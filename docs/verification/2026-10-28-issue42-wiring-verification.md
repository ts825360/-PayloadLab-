# #42 요청별 통합 연결 초안 — 2026-10-28

## 기준과 브랜치

최신 origin/main `64c9cb141108cafa5c6d215fc9eb4981c100b9b7`에서 개인 브랜치 `dtd2428/issue-42-input-sql`을 분리했다. #19 브랜치/PR #48을 수정·커밋·푸시하지 않았다. branch upstream은 origin/main에 잘못 push하지 않도록 해제했다. WORK-STATE의 이전 체크포인트는 stash에 보존한 뒤 main 문서의1절에 현재 체크포인트만 복원했다.

현재 변경은 미커밋이다. [파일 해시](evidence/2026-10-28-issue42-wiring-source-hashes.json)에 기준SHA와 각 실행 파일의SHA256을 저장했다.

## 연결한 범위

- `create_review_app`은 입력·SQL 숫자·authorizer·응답 bytes를 모두 명시적으로 받는다. 기본값으로 정책을 몰래 선택하지 않으며 production `app.main.app`에는 활성화하지 않았다. 다만 기존 SQL/라우터 코드에 opt-in 연결 지점은 추가했다.
- SQLScopeMiddleware는 SQL analyze/attempt별 ContextVar 상태를 만들고 finally에서 초기화한다. 예산은 첫SQL 직전에 만들어 본문 전송 대기를 SQL 시간에 섞지 않는다. FastAPI worker로 복사된 요청 context에서도 같은 요청의 resolve/trace/상수비교가 예산을 공유한다.
- seed/연결은 요청별메모리DB이며 초기화도 예산 안에서 실행한다. 어떤 경로든 실패가 나면 요청에 실패 상태를 보관하고 같은 요청에서 추가 SQL을 반복하지 않는다.
- `sql_injection.py`의 실제 로그인 조회, `learning_trace.py`의 실행/EXPLAIN·상수비교를 opt-in 실행기에 연결했다. context 없는 기본 앱은 기존 경로를 유지한다. 기본 앱이 아직2001자를 허용하고 검토 앱은422로 거부하는 검증으로 미활성 상태를 확인했다.
- 자원 제한/허용 연산 차단/문법 오류를 구분한다. 자원 초과는 실패이고 일부 행/기존 성공 flow를 제거한다. 조회는 이미 성공했지만 trace 계산에서 한도에 걸린 경우에도 success=False로 정정한다.
- Lens는 계산량/시간/행수/셀·결과·문장 bytes 등 알려진 제한 이유를 고정 안내로 설명한다. 원래 SQLite 예외·내부 경로는 반사하지 않는다. 분석 제한은 phase=analysis, execution/table=None이며 analysis_status로 구분한다. 실제UI/브라우저 문안 검토는 아직 하지 않았다.

## 실제 검증

- 통합11개:Easy/Normal·필터 우회, 반환 행 제한, VM중단·정상요청 복구, 분석의 미실행 상태, 연산 차단, 입력 선검사, 소규모 병렬2개 요청의 상태 분리, 기본앱 비활성 유지, resolve성공 뒤trace제한에서 성공값 제거.
- 검토앱을 실제loopback Uvicorn 임시 포트에 띄워 입력 거부→SQL VM중단→정상 조회 복구, 무거운 조회의 분석이 실제 실행하지 않는 것을 확인했다. 테스트 종료 시 서버/소켓을 정리했다.
- 기존17+새2=실제 HTTP19개 포함, main 기준 백엔드 전체225개 통과. [전체 로그](evidence/2026-10-28-issue42-wiring-backend-tests.txt). 앞선340개는 #19기준226+추가114였고, 현재main의 기존100+추가125=225다. #19브랜치의 미병합 검사들을 삭제한 것이 아니다.
- SQL60사례 대조 재실행:60/60, attempt1472·analysis730(8192제안 이내). [원자료](evidence/2026-10-28-issue42-sql-compatibility.json). 독립 실행기 대조와 실제 연결 앱 검사를 구분한다.
- 작업 중 제한 trace 생성 함수의 괄호 오타로 collection이1회 실패해 바로 교정했다. 최종 모든 검사는 통과했다.
- 환경:Windows/Python3.13.2/SQLite3.45.3. 명령:venv Python `-m pytest backend/tests -q`, `docs/verification/scripts/issue42_sql_compatibility.py`. diff --check 통과.

## 남은 일

#6/#24에 팀 승인 답변은 아직 없다. 숫자·작업예산 단위/SQL허용 정책 승인 뒤 기본앱에 적용하고 운영 목표환경·실제UI를 검증해야 한다. #19와 learning_trace.py 등 변경 위치가 겹치므로 #19 main반영 시 다시 통합 대조한다. 현재 범위를 정책 승인·공개 승인·PR/main반영·#42완료로 체크하지 않는다. commit/push 없음.
