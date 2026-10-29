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
# 혼잡도 점수(1~4)를 칠할 때 쓰는 연속 색 (지도·히트맵 공통). zmin=1, zmax=4와 함께 사용
CONGESTION_SCALE = [[i / 3, CONGESTION_COLORS[level]] for i, level in enumerate(CONGESTION_ORDER)]
CONGESTION_COLORBAR = dict(tickvals=[1, 2, 3, 4], ticktext=CONGESTION_ORDER, thickness=14, len=0.8)

# 대시보드 기본 색
PRIMARY = "#0A6B91"        # 기본 (진한 파랑)
PRIMARY_LIGHT = "#8FC1D6"  # 기본 (연한 파랑)
NEUTRAL = "#8C8C8C"        # 보조 (회색)
GRID = "#E6EBEF"           # 격자선
# 장소 분류 색 (분류로 색을 나누는 모든 차트 공통)
CATEGORY_COLORS = {"관광특구": "#0A6B91", "고궁·문화유산": "#8E6BB8", "인구밀집지역": "#D64545",
                   "발달상권": "#EE8A2E", "공원": "#2E9E5B", "미분류": "#8C8C8C"}


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

    def _apply_theme(self, fig: go.Figure, height: int = 420, title: Optional[str] = None) -> go.Figure:
        """모든 그래프 공통 스타일. render()에서 돌려주기 전에 꼭 거친다.
        title을 주면 그 제목을, 없으면 차트 제목(self.title)을 쓴다 (그래프가 여러 개인 페이지용)"""
        fig.update_layout(
            title=dict(text=title or self.title, font=dict(size=17, color="#1F2A33"), x=0, xanchor="left"),
            height=height, margin=dict(l=20, r=20, t=60, b=20),
            font=dict(family="Noto Sans KR, sans-serif", size=13, color="#33414D"),
            paper_bgcolor="white", plot_bgcolor="white",
            hoverlabel=dict(font=dict(family="Noto Sans KR, sans-serif")),
        )
        fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
        fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
        return fig
