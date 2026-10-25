# 서울 인구 대시보드 (seoul-population-dashboard)

서울시 실시간 인구데이터의 특정 기간 기록을 활용해, 서울 주요 장소의 시간대·요일별 인구와 혼잡도를 보여주는 시각화 대시보드입니다. 객체지향프로그래밍 팀 프로젝트.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 이 열립니다.

> 현재 `data/sample.csv`는 **연습용 가짜 데이터**입니다. 실제 데이터를 받으면 교체합니다.

## 폴더 구조

```
app.py                          대시보드 (DashboardApp)                 이준호
src/models.py                   PopulationRecord, CityRecord, Place, District   이준호
src/repository.py               PlaceRepository, load_repository()     이준호
src/charts/base.py              BaseChart (모든 차트의 부모)            이준호
src/charts/__init__.py          페이지 목록                             이준호
src/charts/congestion_map.py    메인: 서울 혼잡도 지도                  김재겸
src/charts/youth.py             연령 구성 비교                          이다혜
src/charts/visitor.py           장소 이용 특성                          장현규
src/charts/heatmap.py           요일 × 시간 혼잡 패턴                   김경진
src/charts/hourly.py            참고용 예시 차트
collector/                      자동 수집 (GitHub Actions)              이준호
data/sample/                    가짜 데이터 (scripts/make_sample.py로 생성)
data/places.xlsx                서울시 주요 121장소 목록
```

## 클래스 구조

```
DashboardApp ──▶ PlaceRepository ◆──▶ District ◆──▶ Place ◆──▶ PopulationRecord, CityRecord
     │
     └──▶ BaseChart «abstract»  controls(repo) → render(repo, place) → [Figure]
              △
   CongestionMapChart · YouthChart · VisitorChart · CongestionHeatmapChart
```

## 팀원 작업 방법

1. 자기 브랜치로 전환 (`feat/map`, `feat/youth`, `feat/visitor`, `feat/heatmap`)
2. main 내용 가져오기 (Update from main / Merge main)
3. 자기 차트 파일의 `raise NotImplementedError` 부분 구현
4. `streamlit run app.py`로 자기 페이지 확인
5. Commit → Push → Pull Request

- 데이터는 `load_repository()`가 알아서 고른다: `data/raw`에 실제 데이터가 있으면 실제, 없으면 `data/sample` 가짜 데이터
- 자기 차트 파일 외에는 수정하지 않는다. 필요한 기능은 톡방에 요청
- 함수 이름·매개변수·반환형은 바꾸지 않는다

## 데이터 수집 (자동)

서울시 실시간 인구데이터 API는 현재 값만 제공하므로, GitHub Actions로 **1시간마다 자동 수집**해서 기간 데이터를 쌓습니다.

- 수집 코드: `collector/collect.py` (인구데이터), `collector/collect_city.py` (도시데이터 요약: 도로소통·주차장·지하철·버스·문화행사·사고통제)
- 자동 실행 설정: `.github/workflows/collect.yml` (매시 7분)
- 저장 위치: **`data` 브랜치**의 `data/raw/` (인구), `data/raw_city/` (도시데이터 요약), 한국 시간 기준 날짜별 CSV
- 장소 목록: `data/places.xlsx` (열린데이터광장 "서울시 주요 121장소 목록") — 장소 분류(관광특구, 공원 등)도 여기서 가져옵니다.

수집된 데이터를 내 컴퓨터로 가져오려면 저장소 폴더에서:

```bash
git fetch origin data
git checkout origin/data -- data/raw data/raw_city
git restore --staged data
```

받은 파일은 `.gitignore`에 등록되어 있어 커밋되지 않습니다.

## 사용 데이터

- 서울시 실시간 인구데이터 (서울 열린데이터광장 OA-21778)
- 서울시 실시간 도시데이터 (서울 열린데이터광장 OA-21285)
