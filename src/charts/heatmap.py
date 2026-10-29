"""
페이지 4: 요일 × 시간 혼잡 패턴 (담당: 김경진)

선택한 장소의 요일(월~일) × 시각(0~23) 히트맵. 혼잡도 / 인구 수 전환.
"""
from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..models import Place
from ..repository import PlaceRepository
from .base import BaseChart
from .base import CONGESTION_COLORBAR, CONGESTION_COLORS, CONGESTION_ORDER, CONGESTION_SCALE, PRIMARY


class CongestionHeatmapChart(BaseChart):
    title = "요일 × 시간 혼잡 패턴"
    owner = "김경진"

    def __init__(self) -> None:
        self.metric: str = "congestion_score"   # "congestion_score" 또는 "avg_population"

    def controls(self, repo: PlaceRepository) -> None:
        """혼잡도 / 인구 수 전환 버튼을 만들고 self.metric에 저장"""

        choice = st.radio("보기 기준", ["혼잡도", "인구 수"], key="heatmap_metric")

        if choice == "혼잡도":
            self.metric = "congestion_score"
        else:
            self.metric = "avg_population"

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """place.pivot(self.metric)으로 히트맵 1개를 돌려준다 (x: 0~23시, y: 월~일)"""
        if place is None or not place.records:
            return []
        table = place.pivot(self.metric)
        days = ["월", "화", "수", "목", "금", "토", "일"]
        hours = [f"{h}시" for h in range(24)]
        fig = go.Figure(go.Heatmap(z=table.values, x=hours, y=days,
                                   colorscale=self._colorscale(self.metric),
                                   text=self._hover_text(place), hoverinfo="text"))
        if self.metric == "congestion_score":
            fig.update_traces(zmin=1, zmax=4, colorbar=CONGESTION_COLORBAR)
        else:
            fig.update_traces(colorbar=dict(title=dict(text="명", side="top"), thickness=14, len=0.8))
        fig.update_traces(xgap=1, ygap=1)
        fig.update_yaxes(autorange="reversed")

        label = "혼잡도" if self.metric == "congestion_score" else "평균 인구"
        return [self._apply_theme(fig, height=440, title=f"{place.name} · 요일 × 시간 {label}")]

    def _hover_text(self, place: Place) -> List[List[str]]:
        """7×24 칸마다 마우스를 올렸을 때 보일 글자 (예: "월 18시 / 혼잡도 3.5 / 인구 38,000~42,000명")"""
        score = place.pivot("congestion_score")
        pop = place.pivot("avg_population")
        days = ["월", "화", "수", "목", "금", "토", "일"]
        result = []
        for d in range(7):
            row = []
            for h in range(24):
                s = score.iloc[d, h]
                p = pop.iloc[d, h]
                if pd.isna(s):
                    text = f"{days[d]} {h}시 / 기록 없음"
                else:
                    text = f"{days[d]} {h}시 / 혼잡도 {s:.1f} / 평균 인구 {p:,.0f}명"
                row.append(text)
            result.append(row)
        return result

    def _colorscale(self, metric: str) -> list:
        """congestion_score면 CONGESTION_COLORS 4단계, avg_population이면 연한색→진한색 연속 색"""
        if metric == "congestion_score":
            # 점수 1~4를 색 척도 위치 0~1에 맞춤 (1→0, 2→1/3, 3→2/3, 4→1). 지도와 같은 공통 색
            return CONGESTION_SCALE
        return [[0, "#EEF5F8"], [1, PRIMARY]]
