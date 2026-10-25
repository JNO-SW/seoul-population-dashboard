"""
데이터 모델 (담당: 이준호)

- PopulationRecord : 특정 시각, 한 장소의 인구 기록 1건
- CityRecord       : 특정 시각, 한 장소의 도시 현황 요약 1건
- Place            : 장소 1곳. 기간 동안의 PopulationRecord, CityRecord를 가진다 (포함)
- District         : 자치구 1곳. 그 안의 Place들을 가진다 (포함)

차트 담당은 이 파일을 수정하지 않는다. 필요한 기능은 톡방에 요청한다.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd

CONGESTION_SCORE = {"여유": 1, "보통": 2, "약간 붐빔": 3, "붐빔": 4}
AGE_GROUPS = ["0대", "10대", "20대", "30대", "40대", "50대", "60대", "70대"]


@dataclass
class PopulationRecord:
    """특정 시각, 한 장소의 인구 기록 1건"""

    time: datetime
    congestion_level: str          # 여유 / 보통 / 약간 붐빔 / 붐빔
    population_min: int
    population_max: int
    male_rate: float               # %
    female_rate: float             # %
    age_rates: Dict[str, float]    # {"0대": 0.6, "10대": 3.8, ..., "70대": 3.6}  (%)
    resident_rate: float           # 거주자 비율 %
    non_resident_rate: float       # 방문자(비상주) 비율 %

    def avg_population(self) -> float:
        return (self.population_min + self.population_max) / 2

    def congestion_score(self) -> int:
        """여유 1 / 보통 2 / 약간 붐빔 3 / 붐빔 4"""
        return CONGESTION_SCORE.get(self.congestion_level, 0)

    def is_weekend(self) -> bool:
        return self.time.weekday() >= 5

    def youth_rate(self) -> float:
        """10대 + 20대 + 30대 비율 합 (%)"""
        return sum(self.age_rates.get(a, 0.0) for a in ("10대", "20대", "30대"))


@dataclass
class CityRecord:
    """특정 시각, 한 장소의 도시 현황 요약 1건 (값이 없는 항목은 None)"""

    time: datetime
    road_idx: Optional[str]            # 원활 / 서행 / 정체
    road_speed: Optional[float]        # km/h
    parking_cnt: int                   # 주차장 수
    parking_capacity: Optional[float]  # 총 주차면
    parking_current: Optional[float]   # 현재 주차 대수 (실시간 제공 주차장만)
    subway_on: Optional[float]         # 지하철 당일 누적 승차 인원
    subway_off: Optional[float]        # 지하철 당일 누적 하차 인원
    bus_on: Optional[float]            # 버스 당일 누적 승차 인원
    bus_off: Optional[float]           # 버스 당일 누적 하차 인원
    event_cnt: int                     # 진행 중인 문화행사 수
    accident_cnt: int                  # 사고·통제 건수

    def parking_rate(self) -> Optional[float]:
        """주차 점유율 % (값이 없으면 None)"""
        if not self.parking_capacity or self.parking_current is None:
            return None
        return self.parking_current / self.parking_capacity * 100

    def transit_total(self) -> float:
        """지하철 + 버스 승하차 합계 (없는 값은 0으로 계산)"""
        return sum(v or 0.0 for v in (self.subway_on, self.subway_off, self.bus_on, self.bus_off))


@dataclass
class Place:
    """장소 1곳과 기간 동안의 기록"""

    name: str
    code: str
    category: str                      # 관광특구 / 고궁·문화유산 / 인구밀집지역 / 발달상권 / 공원
    district: Optional[str] = None     # 자치구 (예: "강남구")
    records: List[PopulationRecord] = field(default_factory=list)
    city_records: List[CityRecord] = field(default_factory=list)

    def add_record(self, record: PopulationRecord) -> None:
        self.records.append(record)

    def add_city_record(self, record: CityRecord) -> None:
        self.city_records.append(record)

    # ── 요약값 ─────────────────────────────────────────
    def avg_population(self) -> float:
        """기간 평균 인구"""
        if not self.records:
            return 0.0
        return sum(r.avg_population() for r in self.records) / len(self.records)

    def peak_record(self) -> PopulationRecord:
        return max(self.records, key=lambda r: r.avg_population())

    def crowded_ratio(self) -> float:
        """'붐빔' 이었던 시간 비율 (%)"""
        if not self.records:
            return 0.0
        return sum(r.congestion_level == "붐빔" for r in self.records) / len(self.records) * 100

    def avg_age_distribution(self) -> Dict[str, float]:
        """기간 평균 연령대 비율. {"0대": 2.0, "10대": 5.0, ..., "70대": 2.8}"""
        if not self.records:
            return {a: 0.0 for a in AGE_GROUPS}
        n = len(self.records)
        return {a: sum(r.age_rates.get(a, 0.0) for r in self.records) / n for a in AGE_GROUPS}

    def youth_rate(self) -> float:
        """기간 평균 10~30대 비율 합 (%)"""
        if not self.records:
            return 0.0
        return sum(r.youth_rate() for r in self.records) / len(self.records)

    def avg_visitor_rate(self) -> float:
        """기간 평균 방문자(비상주) 비율 (%)"""
        if not self.records:
            return 0.0
        return sum(r.non_resident_rate for r in self.records) / len(self.records)

    # ── 차트용 표 ──────────────────────────────────────
    def visitor_rate_by_hour(self) -> pd.DataFrame:
        """시간대별 평균 거주·방문 비율. 열: hour(0~23), resident_rate, non_resident_rate"""
        df = self.to_dataframe()
        return (df.groupby("hour")[["resident_rate", "non_resident_rate"]].mean()
                .reindex(range(24)).reset_index())

    def pivot(self, value: str) -> pd.DataFrame:
        """요일(행 0=월 ~ 6=일) × 시각(열 0~23) 평균표. value: "congestion_score" 또는 "avg_population" """
        df = self.to_dataframe()
        return (df.pivot_table(index="weekday", columns="hour", values=value, aggfunc="mean")
                .reindex(index=range(7), columns=range(24)))

    def latest_city(self) -> Optional[CityRecord]:
        """가장 최근 도시데이터 기록 (없으면 None)"""
        return max(self.city_records, key=lambda r: r.time) if self.city_records else None

    def records_between(self, start: date, end: date) -> "Place":
        """start ~ end (날짜, 양끝 포함) 기록만 담은 새 Place"""
        keep = lambda r: start <= r.time.date() <= end
        return Place(self.name, self.code, self.category, self.district,
                     [r for r in self.records if keep(r)], [r for r in self.city_records if keep(r)])

    def to_dataframe(self) -> pd.DataFrame:
        """
        인구 기록 전체를 표로. 열:
        time, hour, weekday(0=월~6=일), is_weekend, congestion_level, congestion_score,
        avg_population, population_min, population_max, male_rate, female_rate,
        resident_rate, non_resident_rate, youth_rate, age_0 ~ age_70
        """
        rows = []
        for r in self.records:
            row = {
                "time": r.time, "hour": r.time.hour, "weekday": r.time.weekday(),
                "is_weekend": r.is_weekend(), "congestion_level": r.congestion_level,
                "congestion_score": r.congestion_score(), "avg_population": r.avg_population(),
                "population_min": r.population_min, "population_max": r.population_max,
                "male_rate": r.male_rate, "female_rate": r.female_rate,
                "resident_rate": r.resident_rate, "non_resident_rate": r.non_resident_rate,
                "youth_rate": r.youth_rate(),
            }
            for a in AGE_GROUPS:
                row[f"age_{a[:-1]}"] = r.age_rates.get(a, 0.0)
            rows.append(row)
        return pd.DataFrame(rows)


@dataclass
class District:
    """자치구 1곳과 그 안의 장소들"""

    name: str
    places: List[Place] = field(default_factory=list)

    def avg_congestion(self, hour: Optional[int] = None) -> float:
        """소속 장소 전체 기록의 평균 혼잡도 점수(1~4). hour를 주면 그 시각 기록만"""
        scores = [r.congestion_score() for p in self.places for r in p.records
                  if hour is None or r.time.hour == hour]
        return sum(scores) / len(scores) if scores else 0.0

    def total_population(self, hour: Optional[int] = None) -> float:
        """소속 장소들의 평균 인구 합. hour를 주면 그 시각 기록만으로 평균"""
        total = 0.0
        for p in self.places:
            vals = [r.avg_population() for r in p.records if hour is None or r.time.hour == hour]
            total += sum(vals) / len(vals) if vals else 0.0
        return total
