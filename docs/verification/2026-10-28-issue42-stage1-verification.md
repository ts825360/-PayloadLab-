# #42 1차 구현·검증 기록 — 2026-10-28

## 버전과 승인 상태

기존 작업 HEAD `714a7412f6d638a297de33a07e37ff6f2027e720`에 미커밋 신규 파일만 추가했다. #19 PR #48에 commit/push하지 않았다. 사용자에게 산정안으로 #42 진행 확인을 받았으나, #42 본문의 팀 검토 조건은 별도로 유지한다.

- [#6 검토 요청](https://github.com/ts825360/-PayloadLab-/issues/6#issuecomment-6462476696)
- [#24 검토 요청](https://github.com/ts825360/-PayloadLab-/issues/24#issuecomment-6462476899)
- [제안값과 측정 근거](2026-10-28-issue42-limit-rationale.md)

## 구현한 범위

- `backend/app/core/request_limits.py`: 숫자 정책을 주입받는 ASGI 입력 가드. 실제 수신 바이트 누적, JSON UTF-8/중복 키/NaN/필드 타입/추가 필드/history 검사, GET render 디코딩 후 길이·중복 검사. 거부 응답에 입력/예외 경로를 반사하지 않으며 초과 입력을 자르지 않는다.
- `backend/app/core/sql_limits.py`: 숫자·authorizer를 주입받는 SQLite 실행기. 여러 실행 사이 공유하는 VM/시간 예산, statement/엔진 행·값/셀/행수/결과 바이트 한도. 초과 시 부분 결과를 성공으로 돌려주지 않는다. cursor/connection 정리와 새 요청 복구를 시험했다.
- 식별자는 JS Number로 만드는 현재 프론트와의 정확한 정수 호환 범위(0~2^53-1)를 테스트 정책으로 명시했다. 최종 팀 정책은 미승인이다.
- 테스트의 SQLite authorizer는 시험용 SELECT/READ/재귀·소수 함수만 허용한다. 이 목록을 실제 교육 정책으로 확정한 것이 아니다.

## 실패 확인과 실제 검사

처음 테스트가 준비되었을 때 모듈 미존재로 실패했고 구현 후 통과했다. TestClient용 httpx가 이 venv에 없어 의존성을 설치하는 대신 자체 ASGI 호출 도우미로 FastAPI 라우터를 호출했다. 따라서 실제 TCP/HTTP 서버 수신 검증이라고 하지 않는다.

- 신규65개 통과: 입력 N-1/N/N+1, JSON 본문32767/32768/32769bytes, Content-Length를 속인 청크 누적 초과, 타입/중복/인코딩, history 개수·총량·허용명령, render, 기존13랩 관련 필드.
- SQL: 정상 SELECT/UNION/주석, VM 중단/공유예산/새 연결 복구, 시간 만료,127/128/129행, 셀 이모지 bytes, 결과/SQL 길이 경계, 파일 ATTACH/확장로드/PRAGMA/DDL 거부, 연결 종료, 예외 문구 비노출.
- 백엔드 전체291개 통과, [실제 로그](evidence/2026-10-28-issue42-backend-tests.txt). 기존226개+신규65개다. 프론트 변경 없음으로 프론트 검사를 다시 실행하지 않았다.
- 환경: Windows, Python3.13.2, SQLite3.45.3. 실행: 해당 venv Python으로 `-m pytest backend/tests -q`.

## 아직 하지 않은 것

**production app/main.py와 기존 SQL 호출부에는 모듈을 연결하지 않았다. 현재 API에 이 정책이 적용되어 보호가 완료됐다는 뜻이 아니다.**

팀 승인 뒤 main 기준 개인 작업 브랜치 범위를 확정하고 (1) 실제 서버 app에 입력 가드 적용, (2) resolve/trace/EXPLAIN/상수비교를 공통 SQL 요청 예산에 연결, (3) 자원 제한 상태를 학습 trace와 UI에 연결, (4) 전체 응답 상한과 실제 HTTP·회귀 검증을 진행한다. source 측정에는 main/PR을 분리했지만 구현 테스트는 현재 #19 head 기반이며 main 연결 뒤 다시 검증해야 한다.

SQL callback은 주기적 점검으로 엄격한 OS 실행시간/메모리 보장이 아니며, 느린 함수/서버 소켓 수신 제한/동시성은 별도 검토한다. #42 체크·완료·PR/main 반영은 아직 하지 않는다. commit/push 없음.
