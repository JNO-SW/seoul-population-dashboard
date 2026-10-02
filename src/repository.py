"""
데이터 관리 (담당: 조장)

CSV 파일(또는 CSV가 들어 있는 폴더)을 읽어서 Place 객체들로 만들고, 보관·조회하는 역할.
원본 데이터의 열 이름이 바뀌면 COLUMN_MAP만 고치면 된다.
"""
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .models import Place, PopulationRecord

AGE_GROUPS = ["0", "10", "20", "30", "40", "50", "60", "70"]
PLACES_FILE = Path(__file__).resolve().parent.parent / "data" / "places.xlsx"

# 원본 CSV 열 이름 (서울시 실시간 인구데이터 항목명 기준)
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
        df = self._read_csv_files(Path(self.csv_path))
        c = COLUMN_MAP
        df[c["time"]] = pd.to_datetime(df[c["time"]], errors="coerce")
        df = df.dropna(subset=[c["name"], c["time"], c["population_min"], c["population_max"]])
        df = df.drop_duplicates(subset=[c["code"], c["time"]])
        df = self._attach_category(df)

        for _, row in df.iterrows():
            place = self._get_or_create_place(row)
            place.add_record(self._to_record(row))

    @staticmethod
    def _read_csv_files(path: Path) -> pd.DataFrame:
        """파일 하나 또는 폴더 안의 CSV 전체(날짜별 수집 파일)를 하나로 합친다."""
        files = sorted(path.glob("*.csv")) if path.is_dir() else [path]
        if not files:
            raise FileNotFoundError(f"{path} 에 CSV 파일이 없습니다.")
        return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

    @staticmethod
    def _attach_category(df: pd.DataFrame) -> pd.DataFrame:
        """장소 분류 붙이기: places.xlsx(장소 목록) → CSV의 CATEGORY 열 → '미분류' 순"""
        c = COLUMN_MAP
        if PLACES_FILE.exists():
            places = pd.read_excel(PLACES_FILE)
            code_col = next((x for x in places.columns if "CD" in str(x).upper() or "코드" in str(x)), None)
            cat_col = next((x for x in places.columns if "CATEGORY" in str(x).upper() or "카테고리" in str(x) or "분류" in str(x)), None)
            if code_col and cat_col:
                mapping = dict(zip(places[code_col].astype(str).str.strip(), places[cat_col]))
                mapped = df[c["code"]].astype(str).map(mapping)
                if c["category"] in df:
                    mapped = mapped.fillna(df[c["category"]])
                df[c["category"]] = mapped
        if c["category"] not in df:
            df[c["category"]] = "미분류"
        df[c["category"]] = df[c["category"]].fillna("미분류")
        return df

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
