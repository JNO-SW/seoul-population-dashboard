"""
대시보드 (담당: 이준호)
실행: streamlit run app.py
"""
from typing import Dict, Optional

import streamlit as st

from src.charts import PAGES
from src.charts.base import BaseChart
from src.models import Place
from src.repository import PlaceRepository, load_repository


class DashboardApp:
    def __init__(self, repo: PlaceRepository, charts: Dict[str, BaseChart]):
        self.repo = repo
        self.charts = charts
        self.place: Optional[Place] = None

    def run(self) -> None:
        self.render_page(self.render_sidebar())

    def render_sidebar(self) -> str:
        st.sidebar.title("서울 인구 대시보드")
        page = st.sidebar.radio("페이지", list(self.charts))
        category = st.sidebar.selectbox("장소 분류", self.repo.categories())
        self.place = self.repo.get(st.sidebar.selectbox("장소", self.repo.names(category)))
        start, end = self.repo.period()
        st.sidebar.caption(f"데이터: {start:%Y.%m.%d} ~ {end:%Y.%m.%d} · 장소 {len(self.repo.all())}곳\n\n"
                           "출처: 서울 열린데이터광장 실시간 인구데이터·도시데이터")
        return page

    def render_page(self, name: str) -> None:
        chart = self.charts[name]
        st.header(name)
        try:
            chart.controls(self.repo)
            cards = chart.summary_cards(self.place)
            if cards:
                for col, (k, v) in zip(st.columns(len(cards)), cards.items()):
                    col.metric(k, v)
            for fig in chart.render(self.repo, self.place):
                st.plotly_chart(fig, width="stretch")
        except NotImplementedError:
            st.info(f"{chart.owner} 담당 페이지: 구현 전")
        st.caption(f"담당: {chart.owner}")


st.set_page_config(page_title="서울 인구 대시보드", layout="wide")


@st.cache_resource
def get_repo() -> PlaceRepository:
    return load_repository()


def get_charts() -> Dict[str, BaseChart]:
    """차트 객체는 접속자마다 따로 만든다 (고른 시각·분류 같은 값이 다른 접속자와 섞이지 않게)"""
    if "charts" not in st.session_state:
        st.session_state.charts = {name: cls() for name, cls in PAGES.items()}
    return st.session_state.charts


DashboardApp(get_repo(), get_charts()).run()
