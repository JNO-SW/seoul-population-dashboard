"""
서울시 실시간 인구데이터 수집기 (담당: 조장)

GitHub Actions가 1시간마다 실행한다. 장소마다 API를 한 번씩 호출해서
data/raw/YYYY-MM-DD.csv (한국 시간 기준 날짜별 파일) 에 한 줄씩 추가한다.

직접 실행:  SEOUL_API_KEY=발급받은키 python collector/collect.py

장소 목록
- data/places.xlsx (열린데이터광장의 '서울시 주요 121장소 목록.xlsx') 가 있으면 그 목록을 쓴다.
- 없으면 장소 코드 POI001 ~ POI130 을 차례로 시도한다. (없는 코드는 건너뜀)
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
PLACES_FILE = ROOT / "data" / "places.xlsx"
RAW_DIR = Path(os.environ.get("RAW_DIR", ROOT / "data" / "raw"))
KST = timezone(timedelta(hours=9))

API_URL = "http://openapi.seoul.go.kr:8088/{key}/json/citydata_ppltn/1/5/{area}"
FALLBACK_CODES = [f"POI{n:03d}" for n in range(1, 131)]
AGES = ["0", "10", "20", "30", "40", "50", "60", "70"]

# 저장할 열 (API 응답 항목 이름 그대로)
FIELDS = [
    "AREA_NM", "AREA_CD", "PPLTN_TIME",
    "AREA_CONGEST_LVL", "AREA_PPLTN_MIN", "AREA_PPLTN_MAX",
    "MALE_PPLTN_RATE", "FEMALE_PPLTN_RATE",
    *[f"PPLTN_RATE_{a}" for a in AGES],
    "RESNT_PPLTN_RATE", "NON_RESNT_PPLTN_RATE",
    "REPLACE_YN",
]
COLUMNS = FIELDS + ["COLLECTED_AT"]


class ApiError(Exception):
    pass


def load_place_codes() -> list:
    """수집할 장소 코드 목록"""
    if not PLACES_FILE.exists():
        print(f"[안내] {PLACES_FILE.name} 이 없어 POI001~POI130 을 시도합니다.")
        return FALLBACK_CODES

    df = pd.read_excel(PLACES_FILE)
    code_col = next((c for c in df.columns if "CD" in str(c).upper() or "코드" in str(c)), None)
    if code_col is None:
        raise SystemExit(f"{PLACES_FILE.name} 에서 장소 코드 열을 찾지 못했습니다. 열 이름: {list(df.columns)}")
    return df[code_col].dropna().astype(str).str.strip().tolist()


def fetch_area(key: str, code: str, retries: int = 3) -> dict:
    """장소 1곳 조회 → 저장할 한 줄(dict)"""
    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.get(API_URL.format(key=key, area=code), timeout=20)
            resp.raise_for_status()
            return parse_response(resp.json())
        except ApiError:
            raise  # 인증키 오류, 없는 장소 등은 다시 시도해도 같음
        except Exception as e:  # 네트워크 오류 등은 잠시 후 재시도
            last_error = e
            time.sleep(2 * (attempt + 1))
    raise ApiError(f"요청 실패: {last_error}")


def parse_response(data: dict) -> dict:
    """API 응답에서 장소 기록을 찾아 필요한 항목만 뽑는다."""
    record = None
    for value in data.values():
        if isinstance(value, list) and value and isinstance(value[0], dict) and "AREA_NM" in value[0]:
            record = value[0]
            break
    if record is None:
        result = data.get("RESULT", {})
        code = result.get("RESULT.CODE") or result.get("CODE")
        msg = result.get("RESULT.MESSAGE") or result.get("MESSAGE")
        raise ApiError(f"{code} {msg}")
    return {f: record.get(f) for f in FIELDS}


def save(rows: list) -> Path:
    """한국 시간 날짜별 파일에 추가 (같은 장소·같은 시각은 한 번만)"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{datetime.now(KST):%Y-%m-%d}.csv"
    new = pd.DataFrame(rows, columns=COLUMNS)
    if path.exists():
        new = pd.concat([pd.read_csv(path, dtype=str), new.astype(str)], ignore_index=True)
    new = new.drop_duplicates(subset=["AREA_CD", "PPLTN_TIME"], keep="first")
    new.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def main() -> int:
    key = os.environ.get("SEOUL_API_KEY", "").strip()
    if not key:
        print("SEOUL_API_KEY 가 설정되지 않았습니다.")
        return 1

    codes = load_place_codes()
    collected_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    def task(code):
        try:
            row = fetch_area(key, code)
            row["COLLECTED_AT"] = collected_at
            return code, row, None
        except Exception as e:
            return code, None, str(e)

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(task, codes))

    rows = [row for _, row, _ in results if row]
    errors = [(code, err) for code, _, err in results if err]

    print(f"수집 {len(rows)}곳 / 실패 {len(errors)}곳 ({collected_at})")
    for code, err in errors[:10]:
        print(f"  - {code}: {err}")

    if not rows:
        print("한 곳도 수집하지 못했습니다. 인증키와 호출 한도를 확인하세요.")
        return 1

    path = save(rows)
    print(f"저장: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
