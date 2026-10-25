"""
차트 공통 규칙 (담당: 이준호)

모든 차트는 BaseChart를 상속하고 controls(), render()를 구현한다.
DashboardApp은 차트 종류와 상관없이 controls(repo) → render(repo, place) 순서로 호출한다.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import plotly.graph_objects as go

from ..models import Place
from ..repository import PlaceRepository

# 혼잡도 색 (모든 차트 공통)
CONGESTION_COLORS = {"여유": "#2E9E5B", "보통": "#E6B820", "약간 붐빔": "#EE8A2E", "붐빔": "#D64545"}
CONGESTION_ORDER = ["여유", "보통", "약간 붐빔", "붐빔"]


class BaseChart(ABC):
    title: str = "차트 제목"
    owner: str = "담당자"

    def controls(self, repo: PlaceRepository) -> None:
        """화면에 조작 버튼(st.selectbox, st.slider 등)을 만들고, 고른 값을 self 속성에 저장한다. 기본: 없음"""

    @abstractmethod
    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """그래프 목록을 돌려준다. place는 사이드바에서 고른 장소(전체 비교 차트는 안 써도 됨)."""

    def summary_cards(self, place: Optional[Place]) -> Dict[str, str]:
        """그래프 위에 띄울 숫자 카드 {"이름": "값"}. 기본: 없음"""
        return {}

    def _apply_theme(self, fig: go.Figure, height: int = 420) -> go.Figure:
        """모든 그래프 공통 스타일. render()에서 돌려주기 전에 꼭 거친다."""
        fig.update_layout(title=self.title, height=height, margin=dict(l=20, r=20, t=50, b=20),
                          font=dict(family="Noto Sans KR, sans-serif"))
        return fig
