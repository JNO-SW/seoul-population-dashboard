"""
데이터 모델 (담당: 조장)

- PopulationRecord : 특정 시각, 특정 장소의 인구 기록 1건
- Place            : 장소 1곳. 여러 시각의 PopulationRecord를 가지고 있다 (포함 관계)

차트 담당 팀원은 이 파일을 수정하지 않고, Place 객체의 메서드만 가져다 쓴다.
필요한 메서드가 있으면 조장에게 요청한다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import pandas as pd

# 혼잡도 단계 → 숫자 점수 (평균·정렬 계산용)
CONGESTION_SCORE = {"여유": 1, "보통": 2, "약간 붐빔": 3, "붐빔": 4}


@dataclass
class PopulationRecord:
    """특정 시각의 인구 기록 1건"""

    time: datetime
    congestion_level: str          # 여유 / 보통 / 약간 붐빔 / 붐빔
    population_min: int
    population_max: int
    male_rate: float               # 남성 비율(%)
    female_rate: float             # 여성 비율(%)
    age_rates: Dict[str, float]    # {"0대": 1.2, "10대": 5.3, ..., "70대": 4.1}
    resident_rate: float           # 거주자 비율(%)
    non_resident_rate: float       # 방문자 비율(%)

    def avg_population(self) -> float:
        """인구 추정치(최소~최대)의 중간값"""
        return (self.population_min + self.population_max) / 2

    def congestion_score(self) -> int:
        """혼잡도를 1~4 점수로 변환"""
        return CONGESTION_SCORE.get(self.congestion_level, 0)

    def is_weekend(self) -> bool:
        return self.time.weekday() >= 5


@dataclass
class Place:
    """장소 1곳. 기간 동안의 기록(PopulationRecord)들을 가지고 있다."""

    name: str
    code: str
    category: str                  # 관광특구 / 발달상권 / 공원 등
    records: List[PopulationRecord] = field(default_factory=list)

    def add_record(self, record: PopulationRecord) -> None:
        self.records.append(record)

    # ── 요약값 ─────────────────────────────────────────
    def avg_population(self) -> float:
        """전체 기간 평균 인구"""
        if not self.records:
            return 0.0
        return sum(r.avg_population() for r in self.records) / len(self.records)

    def peak_record(self) -> PopulationRecord:
        """가장 붐볐던 시각의 기록"""
        return max(self.records, key=lambda r: r.avg_population())

    def crowded_ratio(self) -> float:
        """'붐빔' 단계였던 시간의 비율(%)"""
        if not self.records:
            return 0.0
        crowded = sum(1 for r in self.records if r.congestion_level == "붐빔")
        return crowded / len(self.records) * 100

    # ── 차트용 데이터 ──────────────────────────────────
    def to_dataframe(self) -> pd.DataFrame:
        """
        이 장소의 기록을 DataFrame으로 변환. 차트 담당 팀원은 주로 이걸 쓴다.

        열: time, hour, weekday, is_weekend, congestion_level, congestion_score,
            avg_population, male_rate, female_rate, resident_rate, non_resident_rate,
            age_0 ~ age_70
        """
        rows = []
        for r in self.records:
            row = {
                "time": r.time,
                "hour": r.time.hour,
                "weekday": r.time.weekday(),  # 0=월 ~ 6=일
                "is_weekend": r.is_weekend(),
                "congestion_level": r.congestion_level,
                "congestion_score": r.congestion_score(),
                "avg_population": r.avg_population(),
                "male_rate": r.male_rate,
                "female_rate": r.female_rate,
                "resident_rate": r.resident_rate,
                "non_resident_rate": r.non_resident_rate,
            }
            for age, rate in r.age_rates.items():
                row[f"age_{age.replace('대', '')}"] = rate
            rows.append(row)
        return pd.DataFrame(rows)
