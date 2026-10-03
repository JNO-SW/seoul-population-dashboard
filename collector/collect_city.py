"""
서울시 실시간 도시데이터 수집기 (담당: 조장)

도시데이터 응답은 장소 하나에 수십~수백 KB라서 원본을 매번 저장하지 않고,
장소·시각별 '요약 숫자'만 data/raw_city/YYYY-MM-DD.csv 에 저장한다.

저장 항목
- 도로소통: 소통 상태, 평균 속도
- 주차장: 주차장 수, 총 주차면, 현재 주차 대수
- 지하철: 역 수, 승하차 인원
- 버스정류소: 정류소 수, 승하차 인원
- 문화행사: 진행 중인 행사 수
- 사고통제: 사고·통제 건수

확인용으로 원본 응답 1개를 data/samples/ 에 한 번만 저장한다.

직접 실행:  SEOUL_CITYDATA_KEY=발급받은키 python collector/collect_city.py
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect import KST, ROOT, load_place_codes  # noqa: E402

API_URL = "http://openapi.seoul.go.kr:8088/{key}/json/citydata/1/5/{area}"
RAW_DIR = Path(os.environ.get("CITY_RAW_DIR", ROOT / "data" / "raw_city"))
SAMPLE_DIR = Path(os.environ.get("SAMPLE_DIR", ROOT / "data" / "samples"))
SIZE_WARN_MB = 5


class ApiError(Exception):
    pass


# ── 응답 안에서 항목 찾기 (항목 위치가 바뀌어도 이름으로 찾음) ──────────
def find_key(obj, key):
    """응답 전체를 뒤져서 key 라는 이름의 첫 값을 돌려준다."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = find_key(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_key(v, key)
            if found is not None:
                return found
    return None


def find_list(obj, key):
    """key 항목을 목록으로 꺼낸다. {key: {key: [...]}} 처럼 한 번 더 감싸진 경우도 처리."""
    value = find_key(obj, key)
    if isinstance(value, dict):
        inner = value.get(key)
        value = inner if isinstance(inner, list) else [value]
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, dict)]


def to_num(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def first_num(obj, *keys):
    for k in keys:
        n = to_num(find_key(obj, k))
        if n is not None:
            return n
    return None


def scalars(d, prefix):
    """dict 안의 단일 값 항목만 접두어를 붙여 꺼낸다 (지하철·버스 승하차 요약용)."""
    if not isinstance(d, dict):
        return {}
    return {f"{prefix}{k}": v for k, v in d.items() if not isinstance(v, (dict, list))}


# ── 요약 ──────────────────────────────────────────────
def summarize(city: dict) -> dict:
    parking = find_list(city, "PRK_STTS")
    subway = find_list(city, "SUB_STTS")
    bus = find_list(city, "BUS_STN_STTS")
    events = find_list(city, "EVENT_STTS")
    accidents = find_list(city, "ACDNT_CNTRL_STTS")

    capacity = [to_num(p.get("CPCTY")) for p in parking]
    parked = [to_num(p.get("CUR_PRK_CNT")) for p in parking]

    row = {
        "AREA_NM": city.get("AREA_NM"),
        "AREA_CD": city.get("AREA_CD"),
        # 도로소통
        "ROAD_TRAFFIC_IDX": find_key(city, "ROAD_TRAFFIC_IDX"),
        "ROAD_TRAFFIC_SPD": first_num(city, "ROAD_TRAFFIC_SPD", "ROAD_TRFFC_SPD"),
        "ROAD_TRAFFIC_TIME": find_key(city, "ROAD_TRFFC_TIME") or find_key(city, "ROAD_TRAFFIC_TIME"),
        # 주차장
        "PRK_CNT": len(parking),
        "PRK_CAPACITY": sum(c for c in capacity if c is not None) if parking else None,
        "PRK_CUR_CNT": sum(p for p in parked if p is not None) if any(p is not None for p in parked) else None,
        # 지하철·버스 (역/정류소 수)
        "SUB_STN_CNT": first_num(city, "SUB_STN_CNT") or len(subway),
        "BUS_STN_CNT": first_num(city, "BUS_STN_CNT") or len(bus),
        # 문화행사·사고통제
        "EVENT_CNT": len(events),
        "ACDNT_CNT": len(accidents),
    }
    # 지하철·버스 승하차 인원 요약 (응답에 있는 요약 항목을 그대로 저장)
    row.update(scalars(find_key(city, "LIVE_SUB_PPLTN"), ""))
    row.update(scalars(find_key(city, "LIVE_BUS_PPLTN"), ""))
    # 역·정류소가 없는 장소는 요약값이 빈칸으로 오므로 목록 개수(0)로 채운다
    for key, items in (("SUB_STN_CNT", subway), ("BUS_STN_CNT", bus)):
        n = to_num(row.get(key))
        row[key] = n if n is not None else len(items)
    return row


# ── 호출·저장 ─────────────────────────────────────────
def fetch_city(key: str, code: str, retries: int = 3) -> dict:
    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.get(API_URL.format(key=key, area=code), timeout=40)
            resp.raise_for_status()
            data = resp.json()
            city = data.get("CITYDATA") or find_key(data, "CITYDATA")
            if not isinstance(city, dict) or "AREA_NM" not in city:
                result = data.get("RESULT", {})
                code_ = result.get("RESULT.CODE") or result.get("CODE")
                msg = result.get("RESULT.MESSAGE") or result.get("MESSAGE")
                raise ApiError(f"{code_} {msg}")
            return city
        except ApiError:
            raise
        except Exception as e:
            last_error = e
            time.sleep(3 * (attempt + 1))
    raise ApiError(f"요청 실패: {last_error}")


def save_sample_once(city: dict) -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    path = SAMPLE_DIR / f"citydata_{city.get('AREA_CD', 'sample')}.json"
    if not any(SAMPLE_DIR.glob("citydata_*.json")):
        path.write_text(json.dumps(city, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"확인용 원본 저장: {path}")


def save(rows: list) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{datetime.now(KST):%Y-%m-%d}.csv"
    new = pd.DataFrame(rows)
    if path.exists():
        new = pd.concat([pd.read_csv(path, dtype=str), new.astype(str)], ignore_index=True)
    new = new.drop_duplicates(subset=["AREA_CD", "COLLECTED_AT"], keep="first")
    new.to_csv(path, index=False, encoding="utf-8-sig")
    size_mb = path.stat().st_size / 1e6
    if size_mb > SIZE_WARN_MB:
        print(f"::warning::도시데이터 하루 파일이 {size_mb:.1f}MB 로 예상보다 큽니다: {path.name}")
    return path


def main() -> int:
    key = os.environ.get("SEOUL_CITYDATA_KEY", "").strip()
    if not key:
        print("SEOUL_CITYDATA_KEY 가 설정되지 않았습니다.")
        return 1

    codes = load_place_codes()
    collected_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    def task(code):
        try:
            city = fetch_city(key, code)
            return code, city, None
        except Exception as e:
            return code, None, str(e)

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(task, codes))

    cities = [c for _, c, _ in results if c]
    errors = [(code, err) for code, _, err in results if err]
    print(f"도시데이터 수집 {len(cities)}곳 / 실패 {len(errors)}곳 ({collected_at})")
    for code, err in errors[:10]:
        print(f"  - {code}: {err}")
    if not cities:
        print("한 곳도 수집하지 못했습니다. 인증키와 호출 한도를 확인하세요.")
        return 1

    save_sample_once(cities[0])
    rows = []
    for city in cities:
        row = summarize(city)
        row["COLLECTED_AT"] = collected_at
        rows.append(row)
    print(f"저장: {save(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
