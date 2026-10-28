# #42 SQL 학습 호환성과 새 예산 대조 — 2026-10-28

기준 HEAD `714a7412f6d638a297de33a07e37ff6f2027e720` + 미커밋 #42 모듈. 앞선 main/#19 고정 SHA 측정 corpus의 SQL 입력을 사용했다. 실제 production 라우터 교체가 아니라 신규 실행기를 호출한 독립 시뮬레이션이다. 팀 제한값/authorizer 승인·제품 연결·commit/push 없음.

> 후속 [EXPLAIN 2차 검증](2026-10-28-issue42-compile-second-verification.md)에서 분석 집계 누락을 수정했다. 아래320은 당시 수치이며 현재 원자료의 분석 최대는730이다.

## 변경

입력 중 analyze는 SQLite EXPLAIN으로 컴파일만 한다. 새 제한 모듈에서 이 기능을 명시적으로 지원하지 않으면 SQLite 명령 목록을 계정 반환 행으로 취급해128행/결과 크기 제한에 잘못 걸릴 수 있다.

run_bounded_query에 compile_only 경로를 추가했다. 원래 문장에 EXPLAIN을 붙인 전체 byte길이를 검사하고 authorizer 및 공유 VM/시간 예산을 그대로 적용한다. 명령 목록은 읽고 버리며 계정 행으로 반환하지 않는다. 실제 사용자 함수가 실행되지 않는 canary 검사와 DROP 같은 허용 밖 연산이 여전히 차단되는 검사도 추가했다. 초기3개 신규 검사는 미구현 상태에서 실패했다([로그](evidence/2026-10-28-issue42-compile-before.txt)).

## 실제 대조

[재현 스크립트](scripts/issue42_sql_compatibility.py), [원자료와 요약](evidence/2026-10-28-issue42-sql-compatibility.json).

- 일반 이름/빈 이름/따옴표/필터/OR/UNION/Unicode2000자 등 중복 제거 SQL60사례를 원래 메모리 SQLite 결과와 비교해60/60 일치.
- 각 attempt는 resolve와 trace를 새 연결에서 두 번 실행하고 추가 상수 비교까지 같은 SQLBudget으로 누적했다. 지원 조건식과 관계없이 추가 비교를 실행하므로 실제 경로보다 보수적인 시뮬레이션이다.
- 입력 중 analyze는 별도 요청 예산으로 EXPLAIN 결과를 비교. 실행 행 없음, 함수 canary 실행0회.
- 새 보수적 예산으로 attempt 최대1472/8192, analysis 최대320/8192. UNION83행의 결과도 일치. 초기 VM실측 상계800과 새 문장당64 선차감 계산은 방식이 다르며1472를 새 호환성 기준으로 사용한다. 8192는 약5.6배 여유를 남기는 현재 수업용 제안이고 모든 SQL/미래 수업 호환성 보증이 아니다.
- 새3개 포함 백엔드 전체338개 통과, 경고 없음. 실제 loopback HTTP17개도 포함. [전체 실제 로그](evidence/2026-10-28-issue42-sql-compatibility-tests.txt). git diff --check 통과.

## 미완료

위 authorizer는 대조용 SELECT/READ 정책이다. 프로젝트의 최종 함수/연산 허용 목록이 아니다. 실제 app/SQL resolve/trace/상수비교/EXPLAIN 연결, Lens/UI 제한 상태, main 기준 및 목표환경 회귀, 팀 정책 승인과 PR/main 반영이 필요하다. 기존 제품 호출부와 #19 PR은 바꾸지 않았다.
