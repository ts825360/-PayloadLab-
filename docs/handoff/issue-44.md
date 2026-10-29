# #44 — 모이는 요청을 제한하고 취소·복구 경계를 정리하기

2026-10-29 / 이수웅(2284033, GitHub dtd2428), AI 보조. **구현·검토 앱 검증·정책 비교안까지 준비했으며, 최종 정책/운영 적용은 팀 검토 대기다.**

## 1. 문제: 무엇이 부족했나

화면의 실행 중 버튼 차단과 자동분석320ms 대기만으로 여러 탭·직접 API·미리보기 요청을 서버 전체에서 제한할 수 없었다. #42의 입력·SQL·응답 제한은 요청 하나의 범위이므로 여러 요청이 동시에 모이는 문제도 따로 다뤄야 했다.

IP만으로 집계하거나 임의 X-Forwarded-For를 신뢰하면 전체 상한을 우회하거나 학교처럼 같은 IP를 공유하는 정상 사용자들을 한 사람으로 취급할 수 있다. Uvicorn이 앱 이전에 IP를 재해석할 수 있어 앱에서 헤더를 읽지 않는 것만으로 충분하지 않다는 점도 조사했다.

## 2. 의도: 어떤 학습 동작을 지키려 했나

정상 입력·자동 분석·수동 실행·미리보기를 유지하면서 서버가 감당할 요청량과 실행 자리를 제한하려 했다. 거부 시에는 입력 문법 오류나 연결 실패로 뭉뚱그리지 않고 이유와 재시도 방향을 설명한다.

제한 기법과 정책 숫자를 분리했다. 팀이 정할 N(동시 학습 작업공간 수)·빈도·동시성·프록시 조건을 임의 운영값으로 넣지 않고 외부에서 주입하는 검토 앱을 만들었다. 실제 로그인/인증은 새로 만들지 않았다.

## 3. 전후 예시: 같은 상황이 어떻게 달라졌나

| 상황 | 기존 부족한 점 | 개선 동작 — 검토 앱 기준 |
| --- | --- | --- |
| 직접 API 요청 반복 | 화면 버튼 제어를 우회할 수 있음 | 전체·분류·선택적 peer 빈도와 동시 실행을 서버 입구에서 확인 |
| root와 /api 경로 | 경로별로 집계가 나뉠 위험 | 하나의 controller와 공통 경로 해석 사용. 뒤 슬래시·URL 인코딩·HEAD도 검사 |
| 임의 XFF/Forwarded 값 변경 | 앞단 신뢰 설정에 따라 IP가 바뀔 수 있음 | local_review_config는 프록시 재해석을 끔. 헤더만 바꿔 같은 peer 예산을 초기화하지 못함 |
| 빈도 초과 | 일반 연결 실패로 읽힐 수 있음 | 429 rate_limit·정수 Retry-After, 실행/분석 Lens의 안전한 대기 안내 |
| 실행 자리 부족 | 대기열/오래된 요청이 누적될 위험 | 현재 시험은 앱 대기열0·503 즉시 거부. 완료 시각을 몰라 가짜 대기시간을 만들지 않음 |
| XSS render 제한 | 입력을 오류 HTML에 반사하면 다시 실행될 위험 | 입력/태그를 포함하지 않는 고정 안내 HTML |
| 호출 취소/연결 종료 | 일을 버린 것처럼 자리만 반납하거나 대기가 남을 위험 | 실제 실행 중인 worker는 끝날 때까지 추적. 취소된 수신/송신 대기는 정리 |
| 예상 밖 오류·종료 drain | 가짜 추가 응답·슬롯 잔류/반복 위험 | 예외를 전파하고 실제 완료 콜백이 반납하도록 처리. drain에 콜백 실행 기회 제공 |

시험의2회/3회 같은 숫자는 경계를 작게 드러내는 값이다. 기본 서비스가 현재 그 값으로 제한된다는 뜻이 아니다.

## 4. 구현: 어느 파일이 어떤 순서로 처리하나

검토 앱에 controller를 명시했을 때:

    CORS → AdmissionGuard → ResponseGuard → InputGuard → SQLScope → route/모형/trace

| 역할 | 파일·핵심 함수 |
| --- | --- |
| 합계/분류/선택적 peer 토큰과 동시 실행 | [admission.py](../../backend/app/core/admission.py): Rate, AdmissionPolicy, AdmissionController.acquire |
| 취소 뒤 실제 작업 추적·반납·종료 대기 | 같은 파일의 run, wait_idle, lease.release |
| HTTP 분류·429/503·고정 render HTML·입출력 정리 | [admission_guard.py](../../backend/app/core/admission_guard.py): admission_action, AdmissionGuard |
| #42와 공유하는 mount 경로 처리 | [lab_paths.py](../../backend/app/core/lab_paths.py): relative_path, lab_route |
| 선택적 연결·종료 drain·로컬 no-proxy 설정 | [review_app.py](../../backend/app/review_app.py): create_review_app, local_review_config |
| 알려진 안전한 오류만 실행/Lens에 전달 | [api.js](../../frontend/src/api.js), 기존 [App.jsx](../../frontend/src/App.jsx), [useInputAnalysis.js](../../frontend/src/useInputAnalysis.js) |
| 지속 가능한 자동 검사 | backend/tests의 test_admission.py, test_admission_http.py, test_admission_second_review.py, test_admission_cancellation_review.py; frontend/src/admission-feedback.test.jsx |

acquire는 잠금 안에서 모든 예산과 빈자리를 확인한 뒤 함께 차감한다. 거부 시 일부 예산만 소비하지 않는다. peer 상태도 개수 제한을 두고, 소진된 예산이 리셋되지 않도록 활성0·완전 보충 상태만 회수한다.

run은 소유한 작업의 실제 완료 때 슬롯을 돌려준다. 상위 호출 취소는 대기 중인 수신/송신만 정리하며 실제 동기 계산을 성급히 취소하지 않는다. wait_idle은 완료 task를 모은 뒤 event loop에 제어를 돌려줘 완료 콜백이 실행되게 한다.

기본 [main.py](../../backend/app/main.py)는 바꾸지 않았다. create_review_app에서도 controller를 생략하면 #44 제한이 켜지지 않는다. local_review_config의 보장은 그 설정으로 실행한 단일 프로세스 loopback에 한정한다.

## 5. 결정 근거: 왜 그런 숫자·방식인가

[정책 후보와 인원별 계산](../verification/2026-10-29-issue44-policy-proposal.md)에 사실·계산·정책 선택을 나눴다.

- 자동분석320ms의 이론적 한 탭 수요3.125회/초를 위 정수4로 반올림했다.
- analyze/attempt/render 분류별 초당4N·burst N, metadata 초당N·burst N을 검토 후보로 제안했다. 수동 실행/render에 같은 주기를 허용하고 재연결을 초당1회로 보는 것은 정책 선택이다.
- 합계 초당13N·burst4N은 분류 상한의 합계다. 더 엄격한 독립 서비스 상한이라고 설명하지 않는다.
- 동시 실행은 A안2N/B안3N, 분류별N을 비교한다. A안은 응답161ms에도 이전 render와 다음 분석/실행이 겹쳐 거부되는 반례가 있다.
- B안은 응답320ms까지의 가상 모형에서 통과했으나 실제 운영 검증은 아니다. N=4이면12동시로 현재 실제 측정 상단8 밖이다.
- IP별 제한은 기본 미사용을 제안해 학교 NAT를 한 사람으로 보지 않게 했다. 전체·분류 합계는 IP 변경과 별개다.
- 본문/전체 hard timeout은 운영 근거 전 미정이다. 요청 시작 후320ms는 후보 목표이며 실제 deadline 구현이 아니다.

태성님이 N·A/B·여유폭·운영 전제를 결정한다. 개발팀4명이나 사용자 답변을 근거로 운영 인원을 확정하지 않았다. 기존 #42의80ms 등 SQL 후보도 별도 팀 검토가 필요하다.

## 6. 검증: 실제 무엇을 확인했나

| 검증 | 실제 결과·근거 |
| --- | --- |
| 처음 요청/프록시 조사 | [HTTP117건](../verification/2026-10-29-issue44-plan.md). 기존 동작 조사이며 제한 기능 통과 수가 아님 |
| 모듈·HTTP·App 연결 | [연결 기록](../verification/2026-10-29-issue44-http-verification.md). root/mount·헤더·429/503·CORS·재시도 |
| 수신 취소·별칭·HEAD·keepalive | [2차 검증](../verification/2026-10-29-issue44-second-verification.md) |
| 송신 취소·drain 경쟁 | [취소 재검증](../verification/2026-10-29-issue44-cancellation-recheck.md): backend433개(#44 관련71 포함), 실제HTTP48건 재확인, 경쟁 순서20회 |
| 실제 App/Lens 자동 검사 | frontend전체138개/빌드488모듈, 이후 관련24개 통과. 서로 다른 단계의 기록이며 새 브라우저 실사용 증거가 아님 |
| 정책 비용 측정 | admission 포함 [HTTP816건](../verification/evidence/2026-10-29-issue44-policy-with-admission.json):13랩·27단계·경계68사례, 동시1/2/4/8 |
| 정책 가상 재생 | [A안133ms의12시나리오5858입장](../verification/evidence/2026-10-29-issue44-policy-replay.json). 실제HTTP/학습자 용량 시험으로 합산하지 않음 |
| 정책 반례·독립 검산 | [48지연 모형·4대조](../verification/2026-10-29-issue44-policy-second-verification.md). 계산 일치, 2N 가정과 전체상한 분리 검증 보완 |

발견/수정은 실패 검사·스택·정상 재검사에 연결했다. 본문 대기 취소 잔류, 송신 대기 취소 잔류, 완료 콜백 실행 전 drain 반복을 서로 구분했다.

비용 측정은 Windows Python3.13·논리CPU8개에서 별도 서버 프로세스로 수행했다. 최대 프로파일 평균 CPU8.961ms/요청·최대 지연132.51ms를 관측했지만, Compose1CPU/256m이나 최악 입력/운영 p95를 입증하지 않는다. HTTP200 안에도 의도한 SQL resource_limit이 있다.

마감 공유 전 검사 대상 파일이 마지막433개 검사 후보의 해시와 같은지 대조했다. 문서 정리·커밋을 새 테스트 통과로 세지 않는다. backend에서 python -m pytest -q, frontend에서 pnpm exec vitest run 및 pnpm build로 재현할 수 있다.

## 7. 한계: 무엇이 남았나

- 기본 앱의 정책 활성화, 최종 숫자·N·A/B·SQL authorizer는 팀 결정 전이다.
- 실제 Python3.12·1CPU/256m·프록시/원본 포트·다중 worker 공유 집계·학교 NAT 이용량·브라우저/기기/iframe 관찰은 별도다.
- 앱 대기열0은 TCP backlog나 서버 버퍼가0이라는 뜻이 아니다. keepalive5초도 본문/전체 실행 timeout이 아니다.
- 취소 정리는 실행 강제 중단이나 이미 전송한 바이트의 회수가 아니다. 핸들러가 스스로 버린 작업·강제 loop/process 종료까지 보장하지 않는다.
- 카운터는 단일 프로세스다. 여러 worker의 합계를 현재 기능으로 보장하지 않는다.
- health/docs/OpenAPI·CORS preflight는 labs 집계 밖이다. 운영 경보·비용·긴급 중지 책임과 엣지 정책은 #12/#24와 연결한다.
- 자동분석 cooldown·목록 로딩 상세 대기 안내·개인별 공정성은 현재 보장하지 않는다.
- PR·팀 검토·main 반영·#44 종료·공개 승인은 별도다. 코드 공유를 그 완료로 해석하지 않는다.

## 8. 추적: 이슈·커밋·다음 검토

- [#44 상세 진행 보고](https://github.com/ts825360/-PayloadLab-/issues/44#issuecomment-6489536262)
- [#6 정책 선택 요청](https://github.com/ts825360/-PayloadLab-/issues/6#issuecomment-6489536897)
- [#24 운영 잔여 연결](https://github.com/ts825360/-PayloadLab-/issues/24#issuecomment-6489537551)
- 구현 커밋: a6beb8aee7de8e24177c5a5052bd0a4b2dba4065. 같은 개인 브랜치의 문서/근거 커밋과 함께 읽는다.
- 실제 PR은 아직 만들지 않았다. 존재하지 않는 #44 PR 링크를 만들지 않는다.
- 공유 전후 상태·SHA는 [WORK-STATE](../WORK-STATE.md)와 Git 원격을 기준으로 확인한다.

[전체 안내](README.md)에서 #19·#42의 변경 이유도 함께 읽을 수 있다. 다음은 태성/팀의 정책 결정과 선택한 운영 조건의 추가 검증이다.