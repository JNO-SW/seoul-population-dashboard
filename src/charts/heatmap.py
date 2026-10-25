"""
페이지 4: 요일 × 시간 혼잡 패턴 (담당: 김경진)

선택한 장소의 요일(월~일) × 시각(0~23) 히트맵. 혼잡도 / 인구 수 전환.
"""
from typing import List, Optional

import plotly.graph_objects as go

from ..models import Place
from ..repository import PlaceRepository
from .base import BaseChart


class CongestionHeatmapChart(BaseChart):
    title = "요일 × 시간 혼잡 패턴"
    owner = "김경진"

    def __init__(self) -> None:
        self.metric: str = "congestion_score"   # "congestion_score" 또는 "avg_population"

    def controls(self, repo: PlaceRepository) -> None:
        """혼잡도 / 인구 수 전환 버튼을 만들고 self.metric에 저장"""
        raise NotImplementedError

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """place.pivot(self.metric)으로 히트맵 1개를 돌려준다 (x: 0~23시, y: 월~일)"""
        raise NotImplementedError

    def _hover_text(self, place: Place) -> List[List[str]]:
        """7×24 칸마다 마우스를 올렸을 때 보일 글자 (예: "월 18시 / 혼잡도 3.5 / 인구 38,000~42,000명")"""
        raise NotImplementedError

    def _colorscale(self, metric: str) -> list:
        """congestion_score면 CONGESTION_COLORS 4단계, avg_population이면 연한색→진한색 연속 색"""
        raise NotImplementedError
