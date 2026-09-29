"""
가짜 샘플 데이터 생성기 — 실제 데이터를 받기 전 연습용.
실행: python scripts/make_sample.py  →  data/sample.csv 생성
※ 여기서 만든 숫자는 실제 서울시 데이터가 아니다.
"""
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

PLACES = [
    ("강남역", "POI014", "발달상권", 40000, 1.0),
    ("홍대 관광특구", "POI007", "관광특구", 35000, 1.6),
    ("여의도한강공원", "POI086", "공원", 12000, 2.2),
]
START = datetime(2025, 10, 6)  # 월요일부터 1주일
AGES = ["0", "10", "20", "30", "40", "50", "60", "70"]


def level(pop, base):
    r = pop / base
    return "여유" if r < 0.6 else "보통" if r < 0.9 else "약간 붐빔" if r < 1.1 else "붐빔"


rows = []
for name, code, cat, base, weekend_boost in PLACES:
    for h in range(7 * 24):
        t = START + timedelta(hours=h)
        weekend = t.weekday() >= 5
        daily = 0.35 + 0.8 * max(0, math.sin((t.hour - 6) / 16 * math.pi))
        pop = base * daily * (weekend_boost if weekend else 1.0) * random.uniform(0.9, 1.1)
        ages = [random.uniform(1, 4), 6, 30 if cat != "공원" else 18, 24, 15, 11, 8, 4]
        s = sum(ages)
        resident = random.uniform(5, 15) if cat != "공원" else random.uniform(20, 35)
        row = {
            "AREA_NM": name, "AREA_CD": code, "CATEGORY": cat,
            "PPLTN_TIME": t.strftime("%Y-%m-%d %H:%M"),
            "AREA_CONGEST_LVL": level(pop, base),
            "AREA_PPLTN_MIN": int(pop * 0.97), "AREA_PPLTN_MAX": int(pop * 1.03),
            "MALE_PPLTN_RATE": round(m := random.uniform(44, 52), 1),
            "FEMALE_PPLTN_RATE": round(100 - m, 1),
            "RESNT_PPLTN_RATE": round(resident, 1),
            "NON_RESNT_PPLTN_RATE": round(100 - resident, 1),
        }
        row.update({f"PPLTN_RATE_{a}": round(v / s * 100, 1) for a, v in zip(AGES, ages)})
        rows.append(row)

out = Path(__file__).resolve().parent.parent / "data" / "sample.csv"
out.parent.mkdir(exist_ok=True)
pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
print(f"saved {len(rows)} rows → {out}")
