"""
메인 페이지: 서울 혼잡도 지도 (담당: 김재겸)

- 자치구별 평균 혼잡도를 색으로 칠한 지도 (선택한 시각 기준)
- 선택한 장소의 도시데이터 6종 카드
"""
from typing import Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from ..models import Place
from ..repository import PlaceRepository
from .base import BaseChart


class CongestionMapChart(BaseChart):
    title = "서울 자치구별 혼잡도"
    owner = "김재겸"

    def __init__(self) -> None:
        self.hour: int = 18          # 지도에 표시할 시각 (0~23)

    def controls(self, repo: PlaceRepository) -> None:
        """시각 슬라이더(0~23)를 만들고 고른 값을 self.hour에 저장"""
        raise NotImplementedError

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """_district_layer()로 구별 값을 받아 자치구 경계 위에 색칠한 지도 1개를 돌려준다"""
        raise NotImplementedError

    def summary_cards(self, place: Optional[Place]) -> Dict[str, str]:
        """place.latest_city()로 도시데이터 6종 카드 내용을 만든다
        키: "도로소통", "주차장", "지하철", "버스", "문화행사", "사고통제" """
        raise NotImplementedError

    def _district_layer(self, repo: PlaceRepository) -> pd.DataFrame:
        """repo.districts()로 자치구별 값 계산. 열: district, avg_congestion, total_population (self.hour 기준)"""
        raise NotImplementedError
