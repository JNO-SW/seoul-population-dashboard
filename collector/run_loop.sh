#!/usr/bin/env bash
# GitHub Actions 예약 실행은 서버가 붐비면 몇 시간씩 밀리거나 빠진다.
# 그래서 한 번 실행되면 약 5시간 반 동안 매시 7분마다 수집을 반복하고,
# 끝날 때쯤 대기 중이던 다음 실행이 이어받는 방식으로 빈 시간을 줄인다.
set -u
END=$(( $(date +%s) + ${LOOP_SECONDS:-19800} ))

while :; do
  python collector/collect.py;      P=$?
  python collector/collect_city.py; C=$?
  echo "인구데이터 종료코드=$P / 도시데이터 종료코드=$C"

  (
    cd databranch || exit 1
    git add data
    if git diff --cached --quiet; then echo "변경 없음"; exit 0; fi
    git commit -q -m "데이터 수집 $(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M')"
    for i in 1 2 3; do
      git pull -q --rebase origin data && git push -q origin HEAD:data && exit 0
      sleep 5
    done
    echo "::warning::data 브랜치에 저장하지 못했습니다."
  )

  NOW=$(date +%s)
  NEXT=$(( (NOW / 3600 + 1) * 3600 + 420 ))   # 다음 정시 7분
  if [ "$NEXT" -gt "$END" ]; then break; fi
  echo "다음 수집: $(TZ=Asia/Seoul date -d "@$NEXT" '+%H:%M')"
  sleep $(( NEXT - NOW ))
done
