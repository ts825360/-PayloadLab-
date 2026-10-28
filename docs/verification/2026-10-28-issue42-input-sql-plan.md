# #42 착수 조사와 제한값 검토안 — 2026-10-28

작성: 이수웅(dtd2428), AI 보조. 조사 기준 원격 main: `64c9cb141108cafa5c6d215fc9eb4981c100b9b7`.
#42 Assignee dtd2428 확인. #6/#24에는 DEC-02/03 선택값의 최종 승인 기록이 없었다.
#19 PR #48은 별도 검토 중이다. 이 문서는 #42 착수 자료이며 제품 코드·상한 정책은 변경하지 않았다.

## 현재 API 계약과 문제

| 경로/유형 | 현재 필드와 처리 | 현재 상한/문제 |
| --- | --- | --- |
| POST analyze/attempt 공통 | payload: dict, FastAPI에서 JSON 객체로 수신 | 내부 필드 스키마·전체 본문 바이트 상한·추가 필드 상한 없음. JSON 파싱 전 수신 상한도 필요 |
| SQL Easy/Normal | username, 기본 빈 문자열. Normal은 정확한 대문자 OR만 제거 | 문자열 타입·길이 공통 검증 없음. 일부 잘못된 타입은 문자열 연산 오류 가능 |
| XSS Easy/Normal | query, 기본 빈 문자열. Normal은 소문자 script 시작 태그 제거 | 공통 타입·길이 검증 없음 |
| IDOR Easy/Normal | requested_id, claimed_user_id | 정수/범위 공통 검증 없음. bool은 Python int의 하위 타입이므로 별도 거부 필요 |
| SSRF/CMDi/Linux/권한 | target_url/hostname/command 문자열 | 모형 내부 MAX_INPUT=2000 검사와 슬라이싱 존재. API 계층에서 초과 입력을 실행 전에 거부하도록 통일 필요 |
| 권한 history | list[str], 허용 명령을 순서대로 재생 | 최대40개·각2000자·총2000자 및 허용 목록 검사. 실제 인증 상태 아님 |
| GET render | XSS만 지원, dict(request.query_params)로 전달 | JSON 본문이 아님. 디코딩 후 query 길이·UTF-8 바이트 및 중복/미지 필드 정책 별도 필요 |

검토 파일: backend/app/routes/labs.py, backend/app/labs/sql_injection.py, reflected_xss.py, idor.py, practice_extensions.py, backend/app/learning_trace.py.
SQL resolve와 trace에 각각 실제 실행 경로가 있다. sql_tree의 상수 비교도 별도 연결을 만든다. 모든 경로를 공통 제한 실행기로 연결해야 한다.
현재 execute/fetchall은 연산량·실행시간·행·결과 바이트 상한이 없다. SQL 실행 연결은 finally에서 close하지만, sql_tree의 connection context manager는 트랜잭션 처리이므로 명시적 close도 확인해야 한다.

## 후보값 재산정 — 기존 미측정 후보 폐기

사용자 지적에 따라 기존 10만연산/100ms/100행/64KiB 표는 승인안으로 사용하지 않는다. [프로젝트 측정과 값별 산정 이유](2026-10-28-issue42-limit-rationale.md) 및 [요약 JSON](evidence/2026-10-28-issue42-sizing-summary.json)으로 대체한다. 측정 사실과 여유/시간 배분의 정책 선택을 구분했다. 제한값은 제품 미적용·팀 미승인이다.

## 다음 구현과 검증 순서

1. 위 후보를 사용자 확인 후 #6/#24에 팀 검토 요청. 승인 전 고정 정책을 제품에 적용하지 않는다.
2. 최신 main 기반 개인 작업 범위를 분리해 라우트별 엄격한 필드 검증·JSON 수신 바이트 검사·render 쿼리 검증부터 구현한다. 기존 #19 PR에 섞지 않는다.
3. 단일 SQL 실행기에서 authorizer 허용 연산/함수, SQL 길이·셀 길이·VM/시간/행/결과 바이트 상한을 처리한다. 로드 확장·호스트 파일 연결 없이 학습용 SELECT/UNION/주석은 유지한다. 승인된 허용 연산 목록을 별도 표로 확정한다.
4. resolve/trace/상수비교/EXPLAIN을 모두 점검하고 제한 초과를 문법 오류나 조건 불충족으로 설명하지 않는다. 모든 경로에서 cursor/connection close, callback 해제와 다음 정상 요청 복구를 검사한다.
5. 문자열/본문/history 각 N-1/N/N+1, null/bool/list/object·중복/추가 필드·잘못된 JSON·청크 본문과 Unicode를 자동 시험한다. 실제 외부 대상이나 과도한 부하 시험은 하지 않는다.
6. 작은 VM 예산을 주입한 로컬 재귀 쿼리 중단 → 연결 종료 → 새 연결의 SELECT 1 복구 시험부터 한다. 전체 SQL 학습/Lens/Normal 회귀는 구현 후 실행한다.

## 상태와 근거

- 완료: 최신 main 소스 대조, Assignee 확인, #6/#24 결정 기록 대조, API 처리 표와 후보·시험안 작성.
- 미완료: 팀 정책 승인, 제품 수정, 실제 HTTP 경계값 시험, SQL 자원 상한 구현·회귀 검사, commit/push/PR.
- 공식 근거: https://docs.python.org/3.13/library/sqlite3.html 의 set_progress_handler, setlimit, connection context manager. callback 중단은 주기적 VM 점검이며 모든 OS 자원 제한을 대체하지 않는다.

## 작은 로컬 시험 결과

[기법 시험 스크립트](scripts/issue42_sql_budget_spike.py), [실제 결과](evidence/2026-10-28-issue42-sql-budget-spike.json). Python3.13.2/SQLite3.45.3에서 시험용1000 VM연산 예산으로 작은 재귀 조회를 중단하고 연결 종료·새 연결 SELECT1 복구를 확인했다. 제품 API 시험이나100ms 보장은 아니다.
