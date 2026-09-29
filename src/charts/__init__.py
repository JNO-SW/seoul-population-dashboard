"""
차트 목록. 새 차트를 만들면 여기에 한 줄 추가한다.
app.py는 ALL_CHARTS를 순서대로 화면에 그린다.
"""
from .hourly import HourlyChart

ALL_CHARTS = [
    HourlyChart(),
    # HeatmapChart(),    # 조원2
    # CategoryChart(),   # 조원3
    # AgeGenderChart(),  # 조원4
]
