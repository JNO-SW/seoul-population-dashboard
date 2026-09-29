"""
데이터 관리 (담당: 조장)

CSV 파일을 읽어서 Place 객체들로 만들고, 보관·조회하는 역할.
원본 데이터의 열 이름이 바뀌면 COLUMN_MAP만 고치면 된다.
"""
from typing import Dict, List

import pandas as pd

from .models import Place, PopulationRecord

AGE_GROUPS = ["0", "10", "20", "30", "40", "50", "60", "70"]

# 원본 CSV 열 이름 (서울시 실시간 인구데이터 항목명 기준)
# TODO: 실제 과거 데이터 파일을 받으면 열 이름을 확인하고 맞출 것
COLUMN_MAP = {
    "name": "AREA_NM",
    "code": "AREA_CD",
    "category": "CATEGORY",
    "time": "PPLTN_TIME",
    "congestion_level": "AREA_CONGEST_LVL",
    "population_min": "AREA_PPLTN_MIN",
    "population_max": "AREA_PPLTN_MAX",
    "male_rate": "MALE_PPLTN_RATE",
    "female_rate": "FEMALE_PPLTN_RATE",
    "resident_rate": "RESNT_PPLTN_RATE",
    "non_resident_rate": "NON_RESNT_PPLTN_RATE",
}


class PlaceRepository:
    """모든 Place 객체를 보관하고 조회한다."""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._places: Dict[str, Place] = {}
        self._load()

    # ── 내부: CSV → 객체 ────────────────────────────────
    def _load(self) -> None:
        df = pd.read_csv(self.csv_path)
        df[COLUMN_MAP["time"]] = pd.to_datetime(df[COLUMN_MAP["time"]])

        for _, row in df.iterrows():
            place = self._get_or_create_place(row)
            place.add_record(self._to_record(row))

    def _get_or_create_place(self, row) -> Place:
        name = row[COLUMN_MAP["name"]]
        if name not in self._places:
            self._places[name] = Place(
                name=name,
                code=row[COLUMN_MAP["code"]],
                category=row[COLUMN_MAP["category"]],
            )
        return self._places[name]

    @staticmethod
    def _to_record(row) -> PopulationRecord:
        c = COLUMN_MAP
        return PopulationRecord(
            time=row[c["time"]].to_pydatetime(),
            congestion_level=row[c["congestion_level"]],
            population_min=int(row[c["population_min"]]),
            population_max=int(row[c["population_max"]]),
            male_rate=float(row[c["male_rate"]]),
            female_rate=float(row[c["female_rate"]]),
            age_rates={f"{a}대": float(row[f"PPLTN_RATE_{a}"]) for a in AGE_GROUPS},
            resident_rate=float(row[c["resident_rate"]]),
            non_resident_rate=float(row[c["non_resident_rate"]]),
        )

    # ── 외부에서 쓰는 메서드 ────────────────────────────
    def get(self, name: str) -> Place:
        return self._places[name]

    def all(self) -> List[Place]:
        return list(self._places.values())

    def categories(self) -> List[str]:
        return sorted({p.category for p in self._places.values()})

    def names(self, category: str = None) -> List[str]:
        return sorted(
            p.name for p in self._places.values()
            if category is None or p.category == category
        )

    def by_category(self, category: str) -> List[Place]:
        return [p for p in self._places.values() if p.category == category]
