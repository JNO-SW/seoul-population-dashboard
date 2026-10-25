"""
페이지 3: 장소 이용 특성 (담당: 장현규)

1) 전체 장소: 평균 인구(x) × 방문자 비율(y) 산점도, 색 = 장소 분류
2) 선택 장소: 시간대별 거주·방문 비율 100% 누적 막대
"""
from datetime import date
from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go

from ..models import Place
from ..repository import PlaceRepository
from .base import BaseChart


class VisitorChart(BaseChart):
    title = "장소 이용 특성"
    owner = "장현규"

    def __init__(self) -> None:
        self.category: Optional[str] = None   # None이면 전체 분류
        self.start: Optional[date] = None     # None이면 전체 기간
        self.end: Optional[date] = None

    def controls(self, repo: PlaceRepository) -> None:
        """장소 분류 선택과 기간 선택(시작일·종료일)을 만들고 self에 저장"""
        raise NotImplementedError

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """[_scatter(...), _stacked_by_hour(place)] 2개를 돌려준다 (기간 지정 시 place.records_between 사용)"""
        raise NotImplementedError

    def _scatter(self, df: pd.DataFrame) -> go.Figure:
        """summary_dataframe 결과로 산점도. x=avg_population, y=visitor_rate, 색=category, 마우스 올리면 name"""
        raise NotImplementedError

    def _stacked_by_hour(self, place: Place) -> go.Figure:
        """place.visitor_rate_by_hour()로 0~23시 거주·방문 100% 누적 막대"""
        raise NotImplementedError
