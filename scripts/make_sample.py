"""
가짜 데이터 생성 (담당: 이준호) — 결과가 항상 같도록 난수를 쓰지 않는다.
실행: python scripts/make_sample.py
결과: data/sample/raw/sample.csv, data/sample/raw_city/sample.csv, data/sample/place_district.csv

규칙
- 기간: 2026-10-05(월) 0시 ~ 2026-10-18(일) 23시, 1시간 간격 (장소당 336줄)
- 인구 = 기준인구 × 시간대 배율 × 요일 배율, 최소/최대 = 인구 ∓ 500
  시간대 배율: 0~5시 0.4 / 6~10시 0.8 / 11~16시 1.0 / 17~20시 1.4 / 21~23시 0.6
  요일 배율: 평일 1.0, 주말은 관광특구·공원·고궁 1.3, 그 외 0.7
- 혼잡도: 인구/기준인구 < 0.6 여유, < 0.9 보통, < 1.2 약간 붐빔, 그 이상 붐빔
- 연령 비율·남녀 비율은 장소마다 고정, 거주 비율은 밤(22~5시) +5, 나머지 -2.5 (하루 평균 = 기준값)
"""
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "sample"

# 코드, 이름, 분류, 자치구, 기준인구, (10대, 20대, 30대), 거주 비율
PLACES = [
    ("POI001", "샘플_강남역", "발달상권", "강남구", 40000, (5, 35, 30), 10),
    ("POI002", "샘플_홍대", "관광특구", "마포구", 30000, (10, 40, 12), 5),
    ("POI003", "샘플_명동", "관광특구", "중구", 50000, (5, 25, 25), 8),
    ("POI004", "샘플_여의도공원", "공원", "영등포구", 12000, (8, 15, 20), 30),
    ("POI005", "샘플_덕수궁", "고궁·문화유산", "중구", 8000, (6, 14, 12), 3),
    ("POI006", "샘플_잠실", "인구밀집지역", "송파구", 25000, (7, 13, 20), 40),
    ("POI007", "샘플_서울숲", "공원", "성동구", 6000, (5, 10, 10), 25),
    ("POI008", "샘플_가산디지털단지", "발달상권", "금천구", 20000, (2, 18, 30), 15),
]
START = datetime(2026, 10, 5)
HOURS = 14 * 24
WEEKEND_UP = {"관광특구", "공원", "고궁·문화유산"}


def hour_factor(h):
    return 0.4 if h < 6 else 0.8 if h < 11 else 1.0 if h < 17 else 1.4 if h < 21 else 0.6


def level(ratio):
    return "여유" if ratio < 0.6 else "보통" if ratio < 0.9 else "약간 붐빔" if ratio < 1.2 else "붐빔"


def ages(youth):
    rest = 100 - 2 - sum(youth)
    return {"0": 2, "10": youth[0], "20": youth[1], "30": youth[2],
            "40": rest * 0.4, "50": rest * 0.3, "60": rest * 0.2, "70": rest * 0.1}


pop_rows, city_rows = [], []
for code, name, cat, _, base, youth, resident in PLACES:
    a = ages(youth)
    for i in range(HOURS):
        t = START + timedelta(hours=i)
        wd = 1.0 if t.weekday() < 5 else (1.3 if cat in WEEKEND_UP else 0.7)
        ratio = hour_factor(t.hour) * wd
        pop = round(base * ratio)
        res = resident + (5 if (t.hour < 6 or t.hour >= 22) else -2.5)
        pop_rows.append({
            "AREA_NM": name, "AREA_CD": code, "CATEGORY": cat, "PPLTN_TIME": t.strftime("%Y-%m-%d %H:%M"),
            "AREA_CONGEST_LVL": level(ratio), "AREA_PPLTN_MIN": pop - 500, "AREA_PPLTN_MAX": pop + 500,
            "MALE_PPLTN_RATE": 48.0, "FEMALE_PPLTN_RATE": 52.0,
            **{f"PPLTN_RATE_{k}": round(v, 2) for k, v in a.items()},
            "RESNT_PPLTN_RATE": res, "NON_RESNT_PPLTN_RATE": 100 - res, "REPLACE_YN": "N",
            "COLLECTED_AT": t.strftime("%Y-%m-%d %H:%M"),
        })
        road = "원활" if ratio < 0.9 else "서행" if ratio < 1.2 else "정체"
        city_rows.append({
            "AREA_NM": name, "AREA_CD": code, "ROAD_TRAFFIC_IDX": road, "ROAD_TRAFFIC_SPD": round(36 / ratio, 1),
            "PRK_CNT": 3, "PRK_CAPACITY": 900, "PRK_CUR_CNT": round(900 * min(ratio, 1.0) * 0.8),
            "SUB_STN_CNT": 2, "BUS_STN_CNT": 10,
            "SUB_ACML_GTON_PPLTN_MIN": t.hour * 1000, "SUB_ACML_GTON_PPLTN_MAX": t.hour * 1000 + 100,
            "SUB_ACML_GTOFF_PPLTN_MIN": t.hour * 1200, "SUB_ACML_GTOFF_PPLTN_MAX": t.hour * 1200 + 100,
            "BUS_ACML_GTON_PPLTN_MIN": t.hour * 300, "BUS_ACML_GTON_PPLTN_MAX": t.hour * 300 + 100,
            "BUS_ACML_GTOFF_PPLTN_MIN": t.hour * 350, "BUS_ACML_GTOFF_PPLTN_MAX": t.hour * 350 + 100,
            "EVENT_CNT": 2 if cat in WEEKEND_UP else 0, "ACDNT_CNT": 1 if code == "POI001" and t.hour == 18 else 0,
            "COLLECTED_AT": t.strftime("%Y-%m-%d %H:%M"),
        })

for sub in ("raw", "raw_city"):
    (OUT / sub).mkdir(parents=True, exist_ok=True)
pd.DataFrame(pop_rows).to_csv(OUT / "raw" / "sample.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(city_rows).to_csv(OUT / "raw_city" / "sample.csv", index=False, encoding="utf-8-sig")
pd.DataFrame([{"AREA_CD": p[0], "DISTRICT": p[3]} for p in PLACES]).to_csv(
    OUT / "place_district.csv", index=False, encoding="utf-8-sig")
print(f"saved {len(pop_rows)} rows → {OUT}")
