# #44 취소 수정 재검증 — 송신 대기와 drain 경쟁

2026-10-29 / 이수웅(dtd2428), AI 보조. [직전 2차 검증](2026-10-29-issue44-second-verification.md)의 후속이다. 기본 앱·Compose·운영값·프론트 소스는 변경하지 않았다.

## 1. 재검증 범위와 발견

직전에는 본문 수신 중 ASGI 호출 취소를 수정했다. 이번에는 본문 도착과 취소가 같은 event-loop 차례에 예약될 때, 송신 대기에서 취소될 때, 반복 취소·전송 예외·drain 취소를 추가로 검사했다.

추가 결함2건을 확인했다.

| 문제 | 관찰 | 수정 이유 |
| --- | --- | --- |
| 송신 대기 중 호출 취소 | 이미 send()를 기다리는 작업이 남아 슬롯/drain이 끝나지 않음 | 수신뿐 아니라 취소된 scope의 송신 대기도 정리해야 함 |
| 완료된 작업의 drain 반복 | 본문 도착→취소 순서에서 wait_idle이 계속 반복하며 CPU를 사용 | 이미 완료된 task의 gather가 즉시 반환해 done callback이 실행될 기회를 주지 못함 |

두 번째는 현재 Python3.13.2 환경에서 실제 재현됐다. 프로젝트 Docker의 Python3.12에서 같은 증상까지 시험했다는 뜻은 아니다. 버전 차이를 고려해 콜백 실행 기회를 명시적으로 주도록 보완했다.

## 2. 실패 근거와 진단

- [송신 대기 검사 단독 실패](evidence/2026-10-29-issue44-cancellation-send-before.txt):0.5초 watchdog 내 drain 미완료.
- [본문 경쟁 스택](evidence/2026-10-29-issue44-cancellation-race-stack.txt): 별도 프로세스의5초 진단 watchdog이 asyncio.shield → wait_idle 반복 위치를 저장하고 종료.
- 최초7개 묶음은 이 반복 때문에 완료되지 않았다. 명령줄이 해당 pytest 파일과 일치하는지 확인한 뒤 그 검사 프로세스만 중단했고, 개발 서버를 중단하지 않았다.
- 위0.5초·5초는 검사/진단용 watchdog이며 운영 제한값·HTTP timeout 제안이 아니다.

일반 종료 지연을 곧바로 제품 결함으로 계산하지 않고, 분리 실패와 스택을 남긴 뒤 두 경계를 수정했다.

## 3. 최소 수정

[admission_guard.py](../../backend/app/core/admission_guard.py):

1. 수신 대기와 별도로 송신 Future도 추적한다.
2. 상위 ASGI 호출이 취소되면 그 scope의 수신/송신 대기만 취소한다.
3. disconnected로 정리되는 취소만 처리하고, 일반 전송 예외는 전파한다.
4. 전체 앱 작업이나 실행 중인 sync worker를 취소하지 않는다. 해당 작업의 실제 종료까지 슬롯 유지 규칙은 그대로다.

[admission.py](../../backend/app/core/admission.py)의 wait_idle:

- 소유 작업 gather 뒤 asyncio.sleep(0)으로 event loop에 제어를 돌려준다.
- done callback이 슬롯 반납과 소유 목록 정리를 실행한 뒤 다음 루프에서 종료한다.
- sleep(0)은 운영 대기시간/timeout을 추가한 것이 아니라 콜백에 실행 기회를 주기 위한 처리다.

두 파일의 수정 전 원문은 로컬 outputs/issue44-cancellation-review-before에 보존했다. 숫자 정책이나 API 응답 계약을 바꾸지 않았다.

이미 서버/네트워크에 기록된 바이트를 되돌리는 기능은 아니다. 이번 송신 검사는 아직 완료되지 않은 대기를 취소하고, 취소 뒤 새 응답을 쓰지 않는 경계다.

## 4. 새 검사7개

[검사 파일](../../backend/tests/test_admission_cancellation_review.py), [수정 후 로그](evidence/2026-10-29-issue44-cancellation-after.txt).

- 송신 대기 취소 → 늦은 쓰기 없이 drain·슬롯 정리.
- 취소→본문 도착, 본문 도착→취소의2개 순서 → 모델 처리 시작/응답 없이 정리.
- receive/send 각각의 예상 밖 OSError → 원래 예외 전파·슬롯 반납·상세를 가짜 응답으로 변환하지 않음.
- 반복 caller.cancel() → 중복 반납·대기 잔류 없음.
- wait_idle 호출자 취소 → 이미 허용한 작업을 버리지 않고 실제 종료까지 슬롯 유지.

새7개는 위 parameter 조합을 포함한 pytest 수이며 독립 제품 버그7개라는 뜻이 아니다.

[경쟁 순서 반복20건](evidence/2026-10-29-issue44-cancellation-race-replay.json): 두 순서를 각10회 재생했고 슬롯 잔류/반복이 다시 발생하지 않았다. ASGI event-loop 재생이며 HTTP 부하/사람의 이용량 시험이 아니다. pytest7개나 전체 수에 합산하지 않는다.

## 5. 최종 회귀 결과

- backend 전체433개 통과: [로그](evidence/2026-10-29-issue44-cancellation-backend-tests.txt). #44 관련71개를 포함하며 이번 신규7개도 이 안에 있다.
- 기존 실제 loopback HTTP48건을 다시 수행: [원자료](evidence/2026-10-29-issue44-cancellation-http-observations.json). 응답47건과 응답을 읽기 전 연결 종료1건. 직전48건에 합산하지 않는다.
- root/mount·헤더 변경·429/503·입력422·별칭/HEAD·keepalive 회복·worker 종료까지 슬롯 유지가 기존 검사에서 통과했다.
- 프론트 제품 소스·응답 code/문구는 변경하지 않았다. 직전 관련24개 통과와 이전 전체138개/빌드488은 역사적 근거로 유지하며 이번 재실행으로 표현하지 않는다.
- [최종 환경·소스해시](evidence/2026-10-29-issue44-cancellation-source-hashes.json).

재현: backend에서 python -m pytest tests/test_admission_cancellation_review.py -q 및 python -m pytest -q. HTTP 원자료는 ISSUE44_HTTP_EVIDENCE에 이번 로컬 파일 경로를 지정했을 때만 갱신한다.

## 6. 남은 한계와 다음 행동

- 실제 브라우저·기기·iframe 화면은 이번 검사에 포함하지 않았다.
- 단일 프로세스 검토용이다. 여러 worker의 집계·실제 프록시/원본 포트·학교 NAT·운영 경보/긴급 중지·정책값은 별도다.
- 정해진 요청/입출력 timeout이나 실행 강제 종료를 구현한 것이 아니다. 핸들러가 자체적으로 버린 작업·강제 event-loop/process 종료는 보장하지 않는다.
- 검토 앱 자체 lifespan은 drain을 제공한다. 다른 앱 아래 mount할 때의 상위 lifespan 통합/강제 종료까지 자동 보장하지 않는다.
- 다음 단계는44-04의 프로젝트 근거 기반 빈도·동시 실행·대기열·시간·프록시 정책안 산정이다.
- 이슈 댓글/체크·게시·커밋·푸시·PR·main 반영·종료는 하지 않았다. #19/#42 설명은 #44와 함께 나중에 공유한다.