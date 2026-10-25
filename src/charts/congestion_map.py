"""
메인 페이지: 서울 혼잡도 지도 (담당: 김재겸)

- 선택한 시각의 혼잡도 지도
  · 장소 단위: 120개 장소 영역을 각자의 혼잡도로 색칠 (기본)
  · 자치구 단위: 자치구별 평균 혼잡도로 색칠 (요약)
- 선택한 장소의 도시데이터 6종 카드

자치구 경계: data/seoul_districts.geojson (southkorea/seoul-maps, 2015 도로명주소 기준)
장소 영역:   data/seoul_places.geojson (열린데이터광장 "서울시 주요 121장소 영역")
장소 → 자치구: data/place_district.csv (장소 영역 중심점이 속한 구)
"""
import json
from typing import Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..models import Place
from ..repository import DATA_DIR, PlaceRepository
from .base import CONGESTION_ORDER, BaseChart

DISTRICT_GEOJSON = DATA_DIR / "seoul_districts.geojson"
PLACE_GEOJSON = DATA_DIR / "seoul_places.geojson"

# 혼잡할수록 진하게 (점수 1~4 고정)
COLOR_SCALE = [[0.0, "#FFF5E6"], [0.33, "#FDC07A"], [0.67, "#F0703C"], [1.0, "#B3241E"]]
COLORBAR = dict(title="혼잡도", tickvals=[1, 2, 3, 4], ticktext=CONGESTION_ORDER)
NO_DATA_COLOR = "#E5E5E5"
BASE_COLOR = "#F4F4F4"
UNITS = ["장소", "자치구"]


class CongestionMapChart(BaseChart):
    title = "서울 혼잡도 지도"
    owner = "김재겸"

    def __init__(self) -> None:
        self.hour: int = 18          # 지도에 표시할 시각 (0~23)
        self.unit: str = "장소"      # 표시 단위: 장소 / 자치구
        self._district_geo: Optional[dict] = None
        self._place_geo: Optional[dict] = None
        self._place_area: Dict[str, float] = {}

    def controls(self, repo: PlaceRepository) -> None:
        """시각 슬라이더(0~23)와 표시 단위를 고르고 self.hour, self.unit에 저장"""
        left, right = st.columns([4, 1])
        self.hour = left.slider("시각", 0, 23, value=self.hour, key="map_hour", format="%d시")
        self.unit = right.radio("표시 단위", UNITS, index=UNITS.index(self.unit), key="map_unit", horizontal=True)

    def render(self, repo: PlaceRepository, place: Optional[Place]) -> List[go.Figure]:
        """선택한 단위(장소/자치구)로 혼잡도를 색칠한 지도 1개를 돌려준다"""
        fig = go.Figure()
        if self.unit == "자치구":
            self._add_district_traces(fig, repo)
        else:
            self._add_place_traces(fig, repo, place)
        fig.update_geos(fitbounds="geojson", visible=False, projection_type="mercator")
        fig = self._apply_theme(fig, height=760)
        fig.update_layout(title=f"{self.title} · {self.unit} 단위 ({self.hour}시 기준)")
        return [fig]

    def summary_cards(self, place: Optional[Place]) -> Dict[str, str]:
        """place.latest_city()로 도시데이터 6종 카드 내용을 만든다
        키: "도로소통", "주차장", "지하철", "버스", "문화행사", "사고통제" """
        city = place.latest_city() if place else None
        if city is None:
            return {}
        # 카드 한 칸에 4~5글자만 보이므로 값은 짧게
        return {
            "도로소통": city.road_idx or "-",                                  # 원활 / 서행 / 정체
            "주차장": f"{city.parking_cnt}곳" if city.parking_cnt else "-",    # 주변 주차장 수
            "지하철": self._ride_text(city.subway_on, city.subway_off),       # 당일 누적 승하차 합
            "버스": self._ride_text(city.bus_on, city.bus_off),
            "문화행사": f"{city.event_cnt}건",
            "사고통제": f"{city.accident_cnt}건",
        }

    def _district_layer(self, repo: PlaceRepository) -> pd.DataFrame:
        """repo.districts()로 자치구별 값 계산. 열: district, avg_congestion, total_population (self.hour 기준)
        그 시각 기록이 없는 구는 avg_congestion, total_population이 NaN"""
        rows = []
        for d in repo.districts():
            score = d.avg_congestion(self.hour)
            rows.append({
                "district": d.name,
                "avg_congestion": score if score > 0 else float("nan"),
                "total_population": d.total_population(self.hour) if score > 0 else float("nan"),
            })
        return pd.DataFrame(rows, columns=["district", "avg_congestion", "total_population"])

    def _place_layer(self, repo: PlaceRepository) -> pd.DataFrame:
        """장소별 값 계산. 열: code, name, category, district, avg_congestion, avg_population (self.hour 기준)
        그 시각 기록이 없는 장소는 빠진다. 영역이 큰 장소부터 정렬 (작은 장소가 위에 그려지도록)"""
        rows = []
        for p in repo.all():
            recs = [r for r in p.records if r.time.hour == self.hour]
            if not recs:
                continue
            rows.append({
                "code": p.code, "name": p.name, "category": p.category, "district": p.district or "-",
                "avg_congestion": sum(r.congestion_score() for r in recs) / len(recs),
                "avg_population": sum(r.avg_population() for r in recs) / len(recs),
            })
        df = pd.DataFrame(rows, columns=["code", "name", "category", "district", "avg_congestion", "avg_population"])
        area = self._place_areas()
        df = df[df["code"].isin(area)]          # 영역 파일에 없는 장소(가짜 데이터 등)는 제외
        return df.assign(area=df["code"].map(area)).sort_values("area", ascending=False).drop(columns="area")

    # ── 지도 레이어 ────────────────────────────────────
    def _add_district_traces(self, fig: go.Figure, repo: PlaceRepository) -> None:
        geo = self._district_geojson()
        df = self._district_layer(repo).dropna(subset=["avg_congestion"])
        # 1) 25개 구 전체를 회색으로 깔기 (장소가 없거나 그 시각 기록이 없는 구)
        fig.add_trace(self._base_districts(geo, NO_DATA_COLOR, "데이터 없음"))
        # 2) 데이터가 있는 구만 혼잡도 점수로 색칠
        fig.add_trace(go.Choropleth(
            geojson=geo, featureidkey="properties.name",
            locations=df["district"], z=df["avg_congestion"], zmin=1, zmax=4,
            colorscale=COLOR_SCALE, colorbar=COLORBAR,
            marker_line_color="white", marker_line_width=1,
            customdata=df[["total_population"]].assign(level=df["avg_congestion"].map(self._level)),
            hovertemplate=("<b>%{location}</b><br>평균 혼잡도 %{z:.2f} (%{customdata[1]})"
                           "<br>평균 인구 합 %{customdata[0]:,.0f}명<extra></extra>"),
        ))

    def _add_place_traces(self, fig: go.Figure, repo: PlaceRepository, place: Optional[Place]) -> None:
        df = self._place_layer(repo)
        geo = self._place_geojson()
        # 1) 자치구 경계를 옅게 깔기 (위치 감 잡기용)
        fig.add_trace(self._base_districts(self._district_geojson(), BASE_COLOR, None))
        # 2) 장소 영역을 혼잡도 점수로 색칠
        fig.add_trace(go.Choropleth(
            geojson=geo, featureidkey="properties.AREA_CD",
            locations=df["code"], z=df["avg_congestion"], zmin=1, zmax=4,
            colorscale=COLOR_SCALE, colorbar=COLORBAR,
            marker_line_color="#666666", marker_line_width=0.5,
            customdata=df[["name", "category", "district", "avg_population"]]
                .assign(level=df["avg_congestion"].map(self._level)),
            hovertemplate=("<b>%{customdata[0]}</b> (%{customdata[1]} · %{customdata[2]})"
                           "<br>평균 혼잡도 %{z:.2f} (%{customdata[4]})"
                           "<br>평균 인구 %{customdata[3]:,.0f}명<extra></extra>"),
        ))
        # 3) 사이드바에서 고른 장소는 굵은 테두리로 강조
        if place is not None and place.code in set(df["code"]):
            fig.add_trace(go.Choropleth(
                geojson=geo, featureidkey="properties.AREA_CD",
                locations=[place.code], z=[0], showscale=False, hoverinfo="skip",
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                marker_line_color="#1F3A93", marker_line_width=3,
            ))

    def _base_districts(self, geo: dict, color: str, hover: Optional[str]) -> go.Choropleth:
        names = [f["properties"]["name"] for f in geo["features"]]
        return go.Choropleth(
            geojson=geo, featureidkey="properties.name", locations=names, z=[0] * len(names),
            colorscale=[[0, color], [1, color]], showscale=False,
            marker_line_color="white" if hover else "#BBBBBB", marker_line_width=1,
            hovertemplate=f"<b>%{{location}}</b><br>{hover}<extra></extra>" if hover else "%{location}<extra></extra>",
        )

    # ── 내부 도우미 ────────────────────────────────────
    def _district_geojson(self) -> dict:
        if self._district_geo is None:
            self._district_geo = json.loads(DISTRICT_GEOJSON.read_text(encoding="utf-8"))
        return self._district_geo

    def _place_geojson(self) -> dict:
        if self._place_geo is None:
            self._place_geo = json.loads(PLACE_GEOJSON.read_text(encoding="utf-8"))
        return self._place_geo

    def _place_areas(self) -> Dict[str, float]:
        """장소 코드 → 영역 넓이 (정렬용, 위경도 단위 그대로)"""
        if not self._place_area:
            for f in self._place_geojson()["features"]:
                ring = f["geometry"]["coordinates"][0]
                a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]))
                self._place_area[f["properties"]["AREA_CD"]] = abs(a) / 2
        return self._place_area

    @staticmethod
    def _level(score: float) -> str:
        """평균 점수(1~4)에 가장 가까운 혼잡도 단계 이름"""
        return CONGESTION_ORDER[min(3, max(0, round(score) - 1))]

    @staticmethod
    def _ride_text(on: Optional[float], off: Optional[float]) -> str:
        """당일 누적 승차 + 하차 합 → "9,450" / "13.4만" (둘 다 없으면 "-")"""
        if on is None and off is None:
            return "-"
        total = (on or 0) + (off or 0)
        return f"{total:,.0f}" if total < 10000 else f"{total / 10000:.1f}만"
