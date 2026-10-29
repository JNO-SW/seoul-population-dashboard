"""
페이지 3: 장소 이용 특성 (담당: 장현규)

1) 전체 장소: 평균 인구(x) × 방문자 비율(y) 산점도, 색 = 장소 분류
2) 선택 장소: 시간대별 거주·방문 비율 100% 누적 막대
"""
from datetime import date
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..models import Place
from ..repository import PlaceRepository
from .base import CATEGORY_COLORS, PRIMARY, PRIMARY_LIGHT, BaseChart


class VisitorChart(BaseChart):
    title = "장소 이용 특성"
    owner = "장현규"

    def __init__(self) -> None:
        self.category: Optional[str] = None   # None이면 전체 분류
        self.start: Optional[date] = None     # None이면 전체 기간
        self.end: Optional[date] = None

    def controls(self, repo: PlaceRepository) -> None:
        """장소 분류 선택과 기간 선택(시작일·종료일)을 만들고 self에 저장"""
        categories = ["전체"] + repo.categories()
        selected = st.selectbox(
            "비교할 장소 분류", categories,
            index=categories.index(self.category) if self.category in categories else 0,
            key="visitor_category",
        )
        self.category = None if selected == "전체" else selected

        dates = [record.time.date() for place in repo.all() for record in place.records]
        self.start = st.date_input(
            "시작일", value=self.start or min(dates, default=None),
            key="visitor_start",
        )
        self.end = st.date_input(
            "종료일", value=self.end or max(dates, default=None),
            key="visitor_end",
        )
        st.caption("기간은 아래 시간대별 그래프에만 적용됩니다. 위 산점도는 전체 기간 평균입니다.")

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """[_scatter(...), _stacked_by_hour(place)] 2개를 돌려준다 (기간 지정 시 place.records_between 사용)"""
        if self.start is not None and self.end is not None and self.start > self.end:
            st.warning("시작일은 종료일보다 늦을 수 없습니다.")
            return []

        # 산점도는 선택한 날짜와 관계없이 전체 기간 요약을 사용한다.
        figures = [self._apply_theme(self._scatter(repo.summary_dataframe(self.category)), height=480,
                                     title="장소별 평균 인구와 방문자 비율 (전체 기간)")]
        if place is None:
            st.info("시간대별 거주·방문 비율을 보려면 장소를 선택해 주세요.")
            return figures

        if self.start is not None or self.end is not None:
            place = place.records_between(self.start or date.min, self.end or date.max)
        if not place.records:
            st.info("선택한 기간에 해당 장소의 인구 기록이 없습니다.")
            return figures

        figures.append(self._apply_theme(self._stacked_by_hour(place), title=f"{place.name} · 시간대별 거주·방문 비율"))
        return figures

    def _scatter(self, df: pd.DataFrame) -> go.Figure:
        """summary_dataframe 결과로 산점도. x=avg_population, y=visitor_rate, 색=category, 마우스 올리면 name"""
        if df.empty:
            fig = go.Figure()
        else:
            fig = px.scatter(
                df, x="avg_population", y="visitor_rate", color="category",
                hover_name="name", color_discrete_map=CATEGORY_COLORS,
                labels={"avg_population": "평균 인구(명)",
                        "visitor_rate": "방문자 비율(%)", "category": "장소 분류"},
            )
            fig.update_traces(marker=dict(size=10), hovertemplate=(
                "<b>%{hovertext}</b><br>평균 인구: %{x:,.0f}명"
                "<br>방문자 비율: %{y:.1f}%<extra>%{fullData.name}</extra>"
            ))
        fig.update_xaxes(title="평균 인구(명)", rangemode="tozero")
        fig.update_yaxes(title="방문자 비율(%)", range=[0, 100])
        return fig

    def _stacked_by_hour(self, place: Place) -> go.Figure:
        """place.visitor_rate_by_hour()로 0~23시 거주·방문 100% 누적 막대"""
        hourly = place.visitor_rate_by_hour()
        fig = go.Figure()
        for column, label, color in [
            ("resident_rate", "거주자", PRIMARY),
            ("non_resident_rate", "방문자", PRIMARY_LIGHT),
        ]:
            fig.add_trace(go.Bar(
                x=hourly["hour"], y=hourly[column], name=label,
                marker_color=color,
                hovertemplate="%{x}시<br>" + label + ": %{y:.1f}%<extra></extra>",
            ))
        fig.update_layout(barmode="stack", legend_title_text=place.name)
        fig.update_xaxes(title="시각", tickmode="linear", tick0=0, dtick=1,
                         range=[-0.5, 23.5])
        fig.update_yaxes(title="거주·방문 비율(%)", range=[0, 100])
        return fig
