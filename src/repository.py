"""
데이터 관리 (담당: 이준호)

수집 CSV를 읽어 Place / District / Record 객체를 만들고 조회 기능을 제공한다.
차트 담당은 load_repository() 로 저장소를 받아 쓰면 된다.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from .models import AGE_GROUPS, CityRecord, District, Place, PopulationRecord

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SAMPLE_DIR = DATA_DIR / "sample"
PLACES_FILE = DATA_DIR / "places.xlsx"            # 장소 분류
DISTRICT_FILE = DATA_DIR / "place_district.csv"   # 장소 → 자치구 (AREA_CD, DISTRICT)


def load_repository() -> "PlaceRepository":
    """실제 수집 데이터(data/raw)가 있으면 그걸, 없으면 가짜 데이터(data/sample)를 읽는다."""
    if any((DATA_DIR / "raw").glob("*.csv")):
        return PlaceRepository(DATA_DIR / "raw", DATA_DIR / "raw_city", DISTRICT_FILE)
    return PlaceRepository(SAMPLE_DIR / "raw", SAMPLE_DIR / "raw_city", SAMPLE_DIR / "place_district.csv")


def _num(v) -> Optional[float]:
    try:
        f = float(v)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


class PlaceRepository:
    """모든 Place와 District를 보관하고 조회한다."""

    def __init__(self, pop_path: Union[str, Path], city_path: Union[str, Path, None] = None,
                 district_path: Union[str, Path, None] = None):
        self.pop_path = Path(pop_path)
        self.city_path = Path(city_path) if city_path else None
        self.district_path = Path(district_path) if district_path else None
        self._places: Dict[str, Place] = {}
        self._districts: Dict[str, District] = {}
        self._load()

    # ── 내부: CSV → 객체 ────────────────────────────────
    @staticmethod
    def _read(path: Path) -> pd.DataFrame:
        files = sorted(path.glob("*.csv")) if path.is_dir() else [path]
        files = [f for f in files if f.exists()]
        return pd.concat([pd.read_csv(f) for f in files], ignore_index=True) if files else pd.DataFrame()

    def _load(self) -> None:
        df = self._read(self.pop_path)
        df["PPLTN_TIME"] = pd.to_datetime(df["PPLTN_TIME"], errors="coerce")
        df = df.dropna(subset=["AREA_NM", "PPLTN_TIME", "AREA_PPLTN_MIN", "AREA_PPLTN_MAX"])
        df = df.drop_duplicates(subset=["AREA_CD", "PPLTN_TIME"])
        categories = self._categories(df)
        districts = self._district_map()

        for row in df.itertuples(index=False):
            r = row._asdict()
            code = str(r["AREA_CD"])
            place = self._places.get(r["AREA_NM"])
            if place is None:
                place = Place(r["AREA_NM"], code, categories.get(code, "미분류"), districts.get(code))
                self._places[place.name] = place
            place.add_record(PopulationRecord(
                time=r["PPLTN_TIME"].to_pydatetime(),
                congestion_level=r["AREA_CONGEST_LVL"],
                population_min=int(r["AREA_PPLTN_MIN"]), population_max=int(r["AREA_PPLTN_MAX"]),
                male_rate=float(r["MALE_PPLTN_RATE"]), female_rate=float(r["FEMALE_PPLTN_RATE"]),
                age_rates={a: float(r[f"PPLTN_RATE_{a[:-1]}"]) for a in AGE_GROUPS},
                resident_rate=float(r["RESNT_PPLTN_RATE"]), non_resident_rate=float(r["NON_RESNT_PPLTN_RATE"]),
            ))

        if self.city_path and self.city_path.exists():
            self._load_city()

        for place in self._places.values():
            if place.district:
                self._districts.setdefault(place.district, District(place.district)).places.append(place)

    def _load_city(self) -> None:
        df = self._read(self.city_path)
        if df.empty:
            return
        by_code = {p.code: p for p in self._places.values()}
        for row in df.itertuples(index=False):
            r = row._asdict()
            place = by_code.get(str(r["AREA_CD"]))
            if place is None:
                continue
            avg = lambda a, b: (None if _num(r.get(a)) is None else (_num(r.get(a)) + (_num(r.get(b)) or _num(r.get(a)))) / 2)
            place.add_city_record(CityRecord(
                time=datetime.strptime(str(r["COLLECTED_AT"]), "%Y-%m-%d %H:%M"),
                road_idx=r.get("ROAD_TRAFFIC_IDX") if isinstance(r.get("ROAD_TRAFFIC_IDX"), str) else None,
                road_speed=_num(r.get("ROAD_TRAFFIC_SPD")),
                parking_cnt=int(_num(r.get("PRK_CNT")) or 0),
                parking_capacity=_num(r.get("PRK_CAPACITY")),
                parking_current=_num(r.get("PRK_CUR_CNT")),
                subway_on=avg("SUB_ACML_GTON_PPLTN_MIN", "SUB_ACML_GTON_PPLTN_MAX"),
                subway_off=avg("SUB_ACML_GTOFF_PPLTN_MIN", "SUB_ACML_GTOFF_PPLTN_MAX"),
                bus_on=avg("BUS_ACML_GTON_PPLTN_MIN", "BUS_ACML_GTON_PPLTN_MAX"),
                bus_off=avg("BUS_ACML_GTOFF_PPLTN_MIN", "BUS_ACML_GTOFF_PPLTN_MAX"),
                event_cnt=int(_num(r.get("EVENT_CNT")) or 0),
                accident_cnt=int(_num(r.get("ACDNT_CNT")) or 0),
            ))

    @staticmethod
    def _categories(df: pd.DataFrame) -> Dict[str, str]:
        if "CATEGORY" in df:                      # 가짜 데이터는 분류가 CSV 안에 있음
            return dict(zip(df["AREA_CD"].astype(str), df["CATEGORY"]))
        if PLACES_FILE.exists():                  # 실제 수집 데이터는 장소 목록 파일에서
            p = pd.read_excel(PLACES_FILE)
            return dict(zip(p["AREA_CD"].astype(str), p["CATEGORY"]))
        return {}

    def _district_map(self) -> Dict[str, str]:
        if self.district_path and self.district_path.exists():
            d = pd.read_csv(self.district_path)
            return dict(zip(d["AREA_CD"].astype(str), d["DISTRICT"]))
        return {}

    # ── 조회 ───────────────────────────────────────────
    def get(self, name: str) -> Place:
        return self._places[name]

    def all(self) -> List[Place]:
        return list(self._places.values())

    def categories(self) -> List[str]:
        return sorted({p.category for p in self._places.values()})

    def names(self, category: Optional[str] = None) -> List[str]:
        return sorted(p.name for p in self._places.values() if category in (None, p.category))

    def by_category(self, category: Optional[str]) -> List[Place]:
        """category가 None이면 전체"""
        return [p for p in self._places.values() if category in (None, p.category)]

    def period(self) -> Tuple[datetime, datetime]:
        """전체 기록의 첫 시각과 마지막 시각"""
        times = [r.time for p in self._places.values() for r in p.records]
        return min(times), max(times)

    def districts(self) -> List[District]:
        return sorted(self._districts.values(), key=lambda d: d.name)

    def summary_dataframe(self, category: Optional[str] = None) -> pd.DataFrame:
        """
        장소당 1줄 요약표 (category가 None이면 전체). 열:
        name, code, category, district, avg_population, visitor_rate, youth_rate, age_0 ~ age_70
        """
        rows = []
        for p in self.by_category(category):
            row = {"name": p.name, "code": p.code, "category": p.category, "district": p.district,
                   "avg_population": p.avg_population(), "visitor_rate": p.avg_visitor_rate(),
                   "youth_rate": p.youth_rate()}
            for a, v in p.avg_age_distribution().items():
                row[f"age_{a[:-1]}"] = v
            rows.append(row)
        return pd.DataFrame(rows)
