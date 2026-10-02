"""
대시보드 메인 화면 (담당: 조장)
실행: streamlit run app.py
"""
import streamlit as st

from src.charts import ALL_CHARTS
from src.repository import PlaceRepository

from pathlib import Path

# 수집한 실제 데이터(data/raw)가 있으면 그걸, 없으면 연습용 샘플을 쓴다.
RAW_DIR = Path("data/raw")
DATA_PATH = str(RAW_DIR) if any(RAW_DIR.glob("*.csv")) else "data/sample.csv"

st.set_page_config(page_title="서울 인구 대시보드", layout="wide")


@st.cache_resource
def load_repository() -> PlaceRepository:
    return PlaceRepository(DATA_PATH)


repo = load_repository()

# ── 사이드바: 필터 ─────────────────────────────────
st.sidebar.title("서울 인구 대시보드")
category = st.sidebar.selectbox("장소 분류", repo.categories())
place_name = st.sidebar.selectbox("장소", repo.names(category))
place = repo.get(place_name)

# ── 상단 요약 카드 ─────────────────────────────────
st.header(place.name)
peak = place.peak_record()
col1, col2, col3 = st.columns(3)
col1.metric("평균 인구", f"{place.avg_population():,.0f}명")
col2.metric("가장 붐빈 시각", peak.time.strftime("%m/%d %H시"))
col3.metric("'붐빔' 시간 비율", f"{place.crowded_ratio():.0f}%")

# ── 팀원 차트: 모두 같은 방식으로 호출 ─────────────
for chart in ALL_CHARTS:
    st.plotly_chart(chart.render(place), width="stretch")
    st.caption(f"담당: {chart.owner}")
