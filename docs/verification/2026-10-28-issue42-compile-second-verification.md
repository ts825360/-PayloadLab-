# #42 EXPLAIN 2차 검증 — 2026-10-28

기준 HEAD `714a7412f6d638a297de33a07e37ff6f2027e720` + 미커밋 #42 파일. Windows/Python3.13.2/SQLite3.45.3. production 연결 및 정책 팀 승인 없음.

## 발견·재현

EXPLAIN 모드에서 SQLite trace/progress만으로 비용을 집계한 것이 부족했다. callback이 발생하지 않는 짧은 반복 분석과 명령 목록 열거가 예산을 소모하지 않았다.

1. 동일256예산으로 SELECT1 컴파일60회를 반복해도 모두 성공.
2. 83개 UNION의 긴 EXPLAIN을128예산으로 읽어도 상한에 걸리지 않음.

[수정 전2실패/25통과](evidence/2026-10-28-issue42-compile-second-before.txt). 단순히 기존338개를 다시 돌린 결과만으로 이 두 경계를 확인했다고 하지 않는다.

## 수정

- compile_only 모드는 준비 비용 한 구간을 명시적으로 먼저 차감한다.
- EXPLAIN 명령 목록의 각 항목을 읽을 때 작업1단위를 추가한다. 계정 행으로 반환하거나 일반 조회128행 제한으로 대신 처리하지 않는다.
- 기존 VM progress/시간/SQL bytes/authorizer/connection 정리 제한을 유지한다.
- SQLBudget 문서에 실제VM명령의 정확한 계수가 아니라 progress 구간·문장 준비 여유·분석 목록 읽기를 합친 보수적 작업 예산이라고 명시했다. 초기 제안의 VM명령8192와 구현 작업단위8192의 의미 차이는 최종 팀 검토 때 확인해야 하며 정책 승인 완료가 아니다.

## 재검증

- 새2개 회귀 검사 포함 백엔드 전체340개 통과, 경고 없음. 실제loopback HTTP17개 포함. [최종 로그](evidence/2026-10-28-issue42-compile-second-after.txt).
- [SQL60사례 대조 재실행](evidence/2026-10-28-issue42-sql-compatibility.json):60/60 기존 결과 일치. attempt 최대1472/8192 유지, analysis 최대730/8192.
- 이전analysis320은 집계 누락이 있던 당시 수치다. 이후 검토에는730을 사용한다. 수업 입력을 막지 않는다는 현재 사례 근거이며 모든 SQL/운영환경 보장이 아니다.
- 함수 canary 미실행, 허용 밖 연산 차단,83행 UNION 보존과 입력/응답 제한 검사를 유지했다.
- 명령: venv Python `docs/verification/scripts/issue42_sql_compatibility.py`, `-m pytest backend/tests -q`. git diff --check 통과.

기존 제품 app/SQL 호출부에는 아직 연결하지 않았다. 실제 서비스 보호 완료·정책 승인·commit/push·PR/main 반영·#42 종료로 기록하지 않는다.
