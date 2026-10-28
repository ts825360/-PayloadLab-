# #42 테스트 앱 실제 HTTP 검증 — 2026-10-28

기준 작업 HEAD: `714a7412f6d638a297de33a07e37ff6f2027e720` + 미커밋 #42 모듈/테스트. Windows, Python3.13.2, SQLite3.45.3. 팀 검토 요청 이후 #6/#24/#42 댓글을 재조회했으며 팀 승인 답변은 없었다. 제품 app/main.py와 기존 SQL 경로 연결은 하지 않았다.

## 실제 수행

`backend/tests/test_request_limits_http.py`에서 실제 FastAPI 랩 라우터와 입력 가드를 조합한 테스트 앱을 Uvicorn으로 loopback 임시 포트에 띄웠다. Python http.client로 실제 TCP/HTTP를 전송하고 fixture 종료 시 서버 종료·스레드 종료·소켓 정리를 확인했다. 기존5173/8001 개발 서버에는 조작하지 않았다.

- SQL analyze/attempt 한글1999/2000/2001자:200/200/422, 허용된 입력 원문 보존.
- Content-Length 없이 HTTP chunked로32767/32768/32769bytes 전송:200/200/413. 모형 실행 전에 입력 가드가 거부.
- XSS render URL의 이모지1999/2000/2001자: 디코딩 후200/200/422. HTML 수신까지만 확인, 브라우저 실행은 하지 않음.
- 중복JSON키422 후 새 정상 SQL 요청200·성공 판정 복구.

새 실제HTTP13개 통과, 백엔드 전체304개 통과(기존226+앞선 모듈65+HTTP13). [전체 실제 로그](evidence/2026-10-28-issue42-http-backend-tests.txt). 실행: 작업 venv의 Python `-m pytest backend/tests -q`.

첫 HTTP 실행에서는 사용하지 않는 websockets 자동 로딩의 deprecation 경고2개가 있었다. 테스트 서버를HTTP전용 ws='none'으로 설정하고 전체 검사를 다시 실행해304개·경고 없음으로 확인했다. 제품 의존성이나 서버 설정을 변경한 것은 아니다.

## 미완료와 다음 단계

이 결과는 **테스트 앱에서 입력 가드가 실제 HTTP 요청을 처리했다는 근거**다. 현재 서비스의 입력 보호 완료나 SQL 제한이 실제 학습 경로에 연결됐다는 뜻이 아니다. SQL 제한은 앞선 독립 모듈 검사까지다. 전체 응답 상한·공통 SQL 예산/Lens 연결·main 기준 회귀·운영환경 검증도 미완료다.

팀 승인 뒤 개인 작업 범위를 #19 PR과 분리하고 실제 app/SQL 호출부를 연결한다. 무단 제한값 확정·commit/push·PR 게시·이슈 종료는 하지 않았다. [앞선 구현 범위](2026-10-28-issue42-stage1-verification.md), [상한 근거](2026-10-28-issue42-limit-rationale.md).
