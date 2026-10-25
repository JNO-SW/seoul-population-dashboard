"""
[참고용 예시] 시간대별 평균 인구 (평일 vs 주말)

자기 차트를 만들 때 구조를 참고한다. 대시보드 페이지에는 들어가지 않는다.
  1. BaseChart 상속, title / owner 적기
  2. __init__에서 조작 값 기본값 정하기
  3. controls()에서 st 위젯으로 값 받아 self에 저장
  4. render()에서 그래프 만들고 self._apply_theme(fig) 거쳐 리스트로 돌려주기
"""
from typing import List, Optional

import plotly.graph_objects as go
import streamlit as st

from ..models import Place
from ..repository import PlaceRepository
from .base import BaseChart


class HourlyChart(BaseChart):
    title = "시간대별 평균 인구 (평일 vs 주말)"
    owner = "예시"

    def __init__(self) -> None:
        self.show_weekend: bool = True

    def controls(self, repo: PlaceRepository) -> None:
        self.show_weekend = st.checkbox("주말도 보기", value=self.show_weekend, key="hourly_weekend")

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        df = place.to_dataframe()
        hourly = df.groupby(["is_weekend", "hour"])["avg_population"].mean().reset_index()
        fig = go.Figure()
        for is_weekend, label in [(False, "평일"), (True, "주말")]:
            if is_weekend and not self.show_weekend:
                continue
            part = hourly[hourly["is_weekend"] == is_weekend]
            fig.add_trace(go.Scatter(x=part["hour"], y=part["avg_population"], mode="lines+markers", name=label))
        fig.update_xaxes(title="시각", dtick=3)
        fig.update_yaxes(title="평균 인구(명)")
        return [self._apply_theme(fig)]
