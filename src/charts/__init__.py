"""대시보드 페이지 순서 = PAGES 순서 (담당: 이준호, 수정 금지)"""
from .congestion_map import CongestionMapChart
from .heatmap import CongestionHeatmapChart
from .visitor import VisitorChart
from .youth import YouthChart

PAGES = {
    "메인: 서울 혼잡도 지도": CongestionMapChart,
    "연령 구성 비교": YouthChart,
    "장소 이용 특성": VisitorChart,
    "요일 × 시간 혼잡 패턴": CongestionHeatmapChart,
}
