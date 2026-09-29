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
app.py                  대시보드 메인 화면            (조장)
src/
  models.py             Place, PopulationRecord 클래스 (조장)
  repository.py         CSV → Place 객체 변환·조회     (조장)
  charts/
    base.py             모든 차트의 부모 클래스        (조장)
    hourly.py           [예시] 시간대별 인구 차트      (조원1)
    __init__.py         차트 목록 (새 차트 등록)
data/                   데이터 파일
scripts/make_sample.py  샘플 데이터 생성기
```

## 클래스 설계와 객체 간 상호작용

```
app.py ──▶ PlaceRepository ──(CSV 읽기)──▶ Place 객체 여러 개
                                              └ PopulationRecord 여러 개 (포함 관계)
app.py ──▶ BaseChart «추상»  render(place)
               △ 상속
       HourlyChart, HeatmapChart, ...  (팀원별 차트)
```

1. `PlaceRepository`가 CSV를 읽어 장소별 `Place` 객체를 만든다.
2. 각 `Place`는 시간별 기록인 `PopulationRecord`들을 가진다.
3. `app.py`가 사용자가 고른 장소 객체를 꺼낸다.
4. 모든 차트에 `chart.render(place)`를 똑같이 호출한다 (다형성).
5. 각 차트는 `place.to_dataframe()`으로 데이터를 받아 그래프를 돌려준다.

## 차트 담당 팀원 작업 방법

1. `src/charts/hourly.py`를 복사해서 `src/charts/내차트.py`를 만든다.
2. 클래스 이름, `title`, `owner`를 바꾼다.
3. `render(self, place)` 안에서 `place.to_dataframe()`으로 데이터를 받아 그래프를 만든다.
4. `src/charts/__init__.py`의 `ALL_CHARTS`에 한 줄 추가한다.
5. `streamlit run app.py`로 확인한다.

**규칙**
- 자기 차트 파일만 수정합니다. `models.py`, `repository.py`에 필요한 기능이 있으면 조장에게 요청해 주세요.
- 작업 전에는 항상 **Pull** 먼저.
- 혼잡도 색상은 `base.py`의 `CONGESTION_COLORS`를 사용합니다.

## 사용 데이터

- 서울시 실시간 인구데이터 (서울 열린데이터광장 OA-21778)
