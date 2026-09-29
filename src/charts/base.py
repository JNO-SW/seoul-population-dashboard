"""
차트 공통 틀 (담당: 조장)

모든 차트 클래스는 BaseChart를 상속하고 render()를 반드시 구현한다.
app.py는 차트 종류를 몰라도 chart.render(place)만 호출하면 된다. (다형성)
"""
from abc import ABC, abstractmethod

import plotly.graph_objects as go

from ..models import Place

# 혼잡도 색상 (모든 차트에서 통일)
CONGESTION_COLORS = {
    "여유": "#2E9E5B",
    "보통": "#E6B820",
    "약간 붐빔": "#EE8A2E",
    "붐빔": "#D64545",
}


class BaseChart(ABC):
    """모든 차트의 부모 클래스"""

    title: str = "차트 제목"
    owner: str = "담당자"

    @abstractmethod
    def render(self, place: Place) -> go.Figure:
        """장소 객체를 받아 Plotly Figure를 돌려준다. 자식 클래스에서 반드시 구현."""

    def _apply_theme(self, fig: go.Figure) -> go.Figure:
        """모든 차트의 공통 스타일"""
        fig.update_layout(
            title=self.title,
            margin=dict(l=20, r=20, t=50, b=20),
            height=360,
            font=dict(family="Noto Sans KR, sans-serif"),
        )
        return fig
