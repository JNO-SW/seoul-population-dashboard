"""
페이지 2: 연령 구성 비교 (담당: 이다혜)

10~30대 비율이 높은 장소 상위 N개를 10대·20대·30대 누적 가로 막대로 비교한다.
"""
from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go

from ..models import Place
from ..repository import PlaceRepository
from .base import BaseChart


class YouthChart(BaseChart):
    title = "10~30대 비율이 높은 장소"
    owner = "이다혜"

    def __init__(self) -> None:
        self.category: Optional[str] = None   # None이면 전체 분류
        self.top_n: int = 10

    def controls(self, repo: PlaceRepository) -> None:
        """장소 분류 선택("전체" + repo.categories())과 상위 N 슬라이더(5~30)를 만들고 self에 저장"""
        raise NotImplementedError

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """repo.summary_dataframe(self.category) → _top_n() → 누적 가로 막대 1개를 돌려준다"""
        raise NotImplementedError

    def _top_n(self, df: pd.DataFrame, n: int) -> pd.DataFrame:
        """youth_rate 내림차순 상위 n개 행만 남긴다"""
        raise NotImplementedError
