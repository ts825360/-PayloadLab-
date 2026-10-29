# #44 2차 검증 — 본문 수신 취소·경로·연결 복구

2026-10-29 / 이수웅(dtd2428), AI 보조. [앞선 연결 검증](2026-10-29-issue44-http-verification.md)의 후속 기록이다. 기본 앱·Compose·운영 정책은 변경하지 않았다.

## 1. 무엇을 다시 확인했나

- root/mount의 경로 별칭·URL 인코딩·HEAD가 공통 상한을 빠져나가지 않는지.
- 잘못된 입력도 요청 예산에 포함하고, 정상 요청·거부·회복이 같은 HTTP 연결에서 유지되는지.
- 본문 수신 중 취소, 이미 실행 중인 worker 취소, 관찰한 disconnect, 예상하지 못한 예외, 앱 수명 종료를 구분해 슬롯/응답이 정리되는지.
- 기존 #19/#42와 App/Lens의 제한 안내를 유지하는지.

이번 핵심 발견은 **ASGI 앱 호출이 본문 수신 대기 중 취소되는 경우**다. 실제 HTTP 연결을 닫은 시험과 ASGI task.cancel() 시험은 서로 다른 근거로 구분한다.

## 2. 발견한 문제와 수정 이유

기존 AdmissionController.run은 실제 worker가 남아 있을 수 있으므로 상위 호출 취소를 소유 작업에 그대로 전파하지 않았다. 이 방식은 실행 중인 계산의 자리를 성급하게 반납하지 않는 데 필요하다.

하지만 AdmissionGuard의 하위 작업이 아직 receive()에서 본문을 기다리는 경우에도 동일하게 보호되어, 상위 ASGI 호출이 취소된 뒤 수신 대기와 슬롯이 남았다. 실행은 시작하지 않았는데 drain이 끝나지 않는 상태를 새 검사로 재현했다.

[수정 전:1실패/4통과](evidence/2026-10-29-issue44-second-before.txt). 검사의0.5초는 멈춤을 탐지하기 위한 watchdog이며 운영 요청 timeout으로 제안한 값이 아니다.

## 3. 어떻게 최소 수정했나

[admission_guard.py](../../backend/app/core/admission_guard.py)의 tracked_receive에만 수신 Future 추적을 추가했다.

1. 각 receive 대기를 추적한다.
2. 상위 ASGI 호출이 취소되면 disconnected를 표시하고, 현재 수신 대기만 취소한다.
3. 해당 대기는 http.disconnect로 마무리해 입력/응답 guard도 연결 종료를 인지하게 한다.
4. 수신 후에도 disconnected를 다시 확인해 늦은 본문을 처리로 넘기지 않는다.
5. 소유한 전체 앱 작업이나 실제 sync worker는 취소하지 않는다. 실행 중인 계산은 여전히 실제 끝날 때 슬롯을 반납한다.
6. 종료된 scope에 대한 늦은 send는 기존대로 버린다.

즉, **취소된 입력 대기는 끝내고 실행 중인 계산은 계속 추적**한다. 실제 작업 종료를 기다리는 기존 #44 의도를 유지한 수정이다. 수정 전 파일은 로컬 outputs/issue44-second-before/admission_guard.py.before에 보존했다.

## 4. 추가 검사와 실제 결과

[신규 수명·오류 검사](../../backend/tests/test_admission_second_review.py):

- 본문 대기 중 caller 취소 → 수신 대기 종료·슬롯0·응답 없음.
- 실제 #42 InputGuard/ResponseGuard까지 있는 검토 앱 → 모델 함수 호출 없이 종료·슬롯0.
- 수신한 http.disconnect → 늦은 send 차단·정상 반납.
- 응답 시작 전/후 RuntimeError → 원래 예외 전파, 가짜 추가 응답 없음, 다음 정상 요청 가능.
- 검토 앱 shutdown → 실제 소유 작업이 끝날 때까지 drain 유지.

[확장 HTTP 검사](../../backend/tests/test_admission_http.py):

- 직접/mount 경로의 뒤 슬래시: 첫307도 예산을 쓰므로 다음 정상 경로는429. 리다이렉트 경로로 예산이 새로 생기지 않음.
- URL 인코딩한 lab ID: 정상200 뒤 공통 상한429.
- 입력 형식 거부422 → 남은 정상200 → 상한429.
- HEAD 제한:429 상태를 유지하며 실제 HTTP 응답 본문은 비어 있음.
- 동일 keep-alive 연결: 정상200 → 본문을 읽기 전에 거부429 → 가짜 시계 보충 후 정상200.

새 HTTP 원자료는 [48건](evidence/2026-10-29-issue44-second-http-observations.json)이다. 응답47건:200=25,429=15,503=2,307=2,422=1,404=1,405=1. 나머지1건은 응답을 읽기 전 연결을 닫았다. 이전32건과 합산하지 않는다. 이번48건은 이전 경로 검사도 재실행한 결과다.

IP 자체 변경은 기존 ASGI 모의, XFF/Forwarded 변경은 실제 loopback HTTP로 재확인했다. 공개 서버·외부 대상 부하나 여러 실제 공인 IP를 사용한 시험이 아니다.

## 5. 자동 검사와 증거

- 수정 직후 기존 범위 포함56개 통과: [로그](evidence/2026-10-29-issue44-second-after.txt).
- 경로/파이프라인 확장 후 #44 관련64개 통과: [로그](evidence/2026-10-29-issue44-second-focused.txt).
- backend 전체426개 통과: [로그](evidence/2026-10-29-issue44-second-backend-tests.txt). 신규 수명6개·이번 확장 HTTP7개를 포함하며 #44 관련64개도 이 안에 포함된다.
- [관련 프론트 재확인 로그](evidence/2026-10-29-issue44-second-frontend-tests.txt): 최종 결과는 아래 마감 기록에서 확인한다.
- 최종 소스 SHA-256·환경·검사 요약은 마감 근거 JSON에 저장한다.

재현: backend에서 python -m pytest tests/test_admission_second_review.py tests/test_admission_http.py tests/test_admission.py -q 및 python -m pytest -q.

원자료 갱신은 ISSUE44_HTTP_EVIDENCE에 이번 파일 경로를 명시한 실행에서만 한다. 프론트는 admission-feedback·api-limit-feedback·api-user-feedback·useInputAnalysis 관련 검사만 재실행한다.

## 6. 그대로 남는 한계

- 실제 브라우저/iframe·실기기·확대·사용자 참여 시험은 이번에 하지 않았다.
- 프론트 소스는 변경하지 않았다. 이전 전체138개/빌드488 성공을 이번에 다시 수행했다고 쓰지 않는다.
- ASGI 취소 뒤 수신 대기 정리는 전체 HTTP 실행/수신 timeout 구현과 다르다. 느린 연결·정책 timeout·강제 loop/프로세스 종료는 남는다.
- 카운터는 단일 프로세스다. 다중 worker/인스턴스의 공유 상한·실제 운영 프록시·원본 포트 차단·학교 NAT 이용량을 완료했다고 판단하지 않는다.
- 후보 수치 산정·#6/#24 정책 결정·기본 앱 활성화·실제 브라우저 검증·운영 책임과 공개 승인은 별도다.
- 이슈 체크·댓글·커밋·푸시·PR·main 반영·종료는 하지 않았다. #19/#42 설명도 #44와 함께 나중에 공유한다.

## 7. 다음 한 단계

현재 기능의 수신 취소 결함을 수정하고 검증했다. 다음은 기존320ms 자동분석 수요·정상 학습 흐름·작은 통제 시험을 근거로, 빈도·동시 실행·대기열·시간·신뢰 프록시 정책안을 산정하는44-04다. 숫자를 임의 확정하거나 기본 앱에 바로 넣지 않는다.
## 마감 기록

관련 프론트4파일24개 통과. 이번 frontend 소스 변경은 없고 이전 전체138개/빌드488은 과거 근거로 유지한다. [최종 소스해시·환경](evidence/2026-10-29-issue44-second-source-hashes.json). backend426개·#44 관련64개 통과, 실제 HTTP48건은 응답47/연결 종료1이다. 문서 링크·구문·공백·hash는 최종 저장 뒤 확인한다.
