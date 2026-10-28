# #42 2차 검증 — 2026-10-28

기준 HEAD `714a7412f6d638a297de33a07e37ff6f2027e720` + 미커밋 #42 모듈·테스트. Windows/Python3.13.2/SQLite3.45.3. production 호출부는 미연결이고 정책 팀 승인 대기 상태를 유지한다.

## 재현 후 수정한 문제 3개

| 입력/조건 | 수정 전 실제 결과 | 수정과 재검증 |
| --- | --- | --- |
| 동일 SQLBudget(vm256)으로 SELECT1을60회 실행 | 쿼리가64 VM callback 간격보다 짧아steps가 누적되지 않고 전부 성공 | 문장 trace callback에서 미보고 잔여 구간64를 선차감. 실제 progress 비용과 함께 누적하는 보수적 상계로 변경. 한도 이후 동일 예산 요청은vm 제한 상태를 유지 |
| authorizer가 users.username 읽기에 SQLITE_IGNORE 반환 | NULL로 바뀐 행을ok로 반환 | SQLITE_OK 이외는DENY로 처리. 일부 수정된 행을 정상 교육 결과로 표시하지 않고blocked·빈 결과 |
| authorizer 자체에서 예외 발생 | SQLite가 막았지만syntax_error로 잘못 분류 | 검사 예외를DENY로 바꿔blocked로 구분. 입력/내부 경로를 반사하지 않음 |

[수정 전 실패 로그:3실패/13통과](evidence/2026-10-28-issue42-second-before.txt). SQLBudget의8192는 이제 정확한 VM 카운터가 아니라 짧은 문장까지 포함하는 보수적 계산 예산이다. 문장당64 여유를 먼저 차감하므로 실제 명령 수보다 일찍 거부할 수 있다. 기존 단위 VM 측정347/요청상계800은 변경 전 측정 근거로 보존하며, 제품 연결 뒤 새 계산 방식의 정상 학습 여유를 다시 측정해야 한다.

cursor 정리 중 문제가 나더라도 connection 정리 finally에 도달하도록 cleanup을 중첩하고, 종료 시 trace/progress/authorizer callback을 해제한다. cleanup 장애 자체를 OS 자원 정리 보장으로 과장하지 않는다.

## 추가 대조와 실제 검사

- 일반 이름 박태성·빈 문자열·Easy OR 성공·Normal 대문자OR필터·대소문자 우회·UNION 총6개 사례의 실제 행을 기존 실행기와 비교.
- Normal 대문자OR제거 사례는 기존에도 문법 오류다. 신규 호환성 테스트가 처음에는 모든 사례를ok로 기대해1개 실패했으며 제품을 바꾸지 않고 기대 상태를syntax_error로 교정했다. [중간 로그](evidence/2026-10-28-issue42-second-normal-expectation.txt). 이 실패를 제품 버그로 세지 않는다.
- 본문 수신 중 연결 종료 시 랩을 실행하거나 응답을 보내지 않는 검사 추가.
- 기존 N-1/N/N+1, 잘못된 타입/JSON/history, SQL 행·셀·결과·문장 크기, authorizer 차단, 연결 종료·복구와 실제loopback HTTP13개를 포함한 **백엔드 전체314개 통과**, 경고 없음.
- 명령: 작업 venv Python `-m pytest backend/tests -q`. [최종 실제 로그](evidence/2026-10-28-issue42-second-after.txt). git diff --check 통과.

## 범위와 다음 단계

팀 정책 승인, 실제 production app/SQL 호출부 연결, 전체 응답 상한, 제품의 자원 제한 학습 설명, main 기준 회귀 및 목표 환경 검증은 미완료다. 현재 테스트 앱의 실제HTTP와 SQL 모듈 검증을 현재 서비스 보호 완료로 쓰지 않는다. 프론트 변경은 없어 재검사하지 않았다. commit/push·#19 PR 변경·#42 체크/종료 없음.
