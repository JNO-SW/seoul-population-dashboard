"""
[예시 차트] 시간대별 인구 흐름

차트 담당 팀원은 이 파일을 복사해서 자기 차트를 만들면 된다.
규칙 3가지:
  1. BaseChart를 상속한다
  2. title, owner를 적는다
  3. render(place)에서 Figure를 만들고 self._apply_theme(fig)를 돌려준다
"""
import plotly.graph_objects as go

from ..models import Place
from .base import BaseChart


class HourlyChart(BaseChart):
    title = "시간대별 평균 인구 (평일 vs 주말)"
    owner = "조원1"

    def render(self, place: Place) -> go.Figure:
        df = place.to_dataframe()
        hourly = df.groupby(["is_weekend", "hour"])["avg_population"].mean().reset_index()

        fig = go.Figure()
        for is_weekend, label in [(False, "평일"), (True, "주말")]:
            part = hourly[hourly["is_weekend"] == is_weekend]
            fig.add_trace(go.Scatter(x=part["hour"], y=part["avg_population"],
                                     mode="lines+markers", name=label))
        fig.update_xaxes(title="시각", dtick=3)
        fig.update_yaxes(title="평균 인구(명)")
        return self._apply_theme(fig)
