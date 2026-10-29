# #42 — 수업 입력을 유지하면서 서버 처리 범위 제한하기

> **팀원 검토용 설명 / 2026-10-28**<br>
> 관련: [이슈 #42](https://github.com/ts825360/-PayloadLab-/issues/42) · [전체 안내](README.md)

## 1. 무엇이 문제였나

화면 입력칸의 길이 제한만으로는 API에 직접 보낸 큰 요청을 막을 수 없다. 또한 SQL은 메모리 SQLite라도 실제로 계산하므로 긴 계산·많은 결과·큰 문자열로 자원을 소비할 수 있다. “모든 결과가 규칙 기반이라 실제 실행 위험이 없다”는 설명도 SQL에는 맞지 않는다.

반대로 SQL 수업에 필요한 따옴표나 OR를 모두 금지하면 실습 자체가 성립하지 않는다. 목표는 학습용 입력을 보존하면서 서버가 받아들이고 처리하고 반환하는 양을 제한하는 것이다.

## 2. 왜 이런 구조로 수정했나

제한의 **기법**과 **정책값**을 분리했다. 제한 장치는 먼저 구현·검증하되, 숫자와 SQL 허용 연산은 팀이 검토한 뒤 적용할 수 있도록 외부에서 넣는 구조다.

현재 기본 서비스인 [backend/app/main.py](../../backend/app/main.py)의 app에는 제한 장치를 활성화하지 않았다. [review_app.py](../../backend/app/review_app.py)의 create_review_app에 정책을 명시적으로 넣는 **검토용 앱**에서 연결·시험했다.

따라서 “제한 구현이 없다”도, “기본 서비스 보호가 모두 끝났다”도 현재 상태를 정확히 설명하지 못한다. **검토용 앱 구현·검증 완료, 기본 앱 정책 적용 대기**로 이해하면 된다.

## 3. 무엇을 어떤 방식으로 고쳤나

| 기존 문제 또는 위험 | 수정 방식 | 이렇게 한 이유 |
| --- | --- | --- |
| UI 제한을 우회하는 직접 API 요청 | analyze·attempt·render의 필드 타입·길이·전체 크기·history를 서버에서 검증 | 입력 경로가 달라도 같은 계약을 적용하기 위해 |
| Content-Length만 믿으면 실제 본문과 다를 수 있음 | 실제 수신 청크의 바이트를 누적하고 JSON 해석 전에 검사 | 헤더가 아닌 실제 받은 양을 기준으로 제한하기 위해 |
| 잘못된 JSON·타입·history | 중복 키·잘못된 JSON·허용 밖 필드/값·history 개수/총량 등을 검사. IDOR는 bool을 정수로 받지 않음 | 뜻이 모호한 입력이 각 모형에 다르게 전달되지 않도록 |
| SQL을 자르거나 통째 금지하면 학습 훼손 | 입력을 잘라 실행하지 않고 계산·시간·행·셀·결과 크기로 제한 | 사용자가 쓴 문장의 의미를 바꾸지 않고 처리 범위만 정하기 위해 |
| 한 요청 안에서 여러 SQL이 각각 예산을 새로 받음 | 판정·trace·추가 비교·분석이 요청별 공통 SQL 예산 사용 | 그림 설명을 만드는 추가 계산까지 같은 요청 비용으로 세기 위해 |
| 짧은 SQL·EXPLAIN이 계산 집계에서 빠짐 | 문장별 최소 예약량, progress 점검, EXPLAIN 준비·목록 작업을 함께 집계 | 짧은 문장을 반복하거나 분석 경로를 써서 제한을 비우는 틈을 줄이기 위해 |
| 결과를 모두 만든 뒤 확인하면 이미 너무 큼 | 커서를 순회하며 행·셀·직렬화 크기를 확인하고 엔진 길이 제한도 별도 적용 | 반환 데이터 확대를 단계적으로 멈추기 위해 |
| 제한·차단을 문법 오류나 빈 결과로 오해 | resource_limit·blocked를 별도 상태로 반환하고 성공/표 표시를 정리 | #19의 “왜 0행인가” 설명과 “처리를 끝내지 못함”을 구분하기 위해 |
| authorizer의 IGNORE가 값을 NULL로 바꿀 수 있음 | OK 이외 반환과 authorizer 예외를 차단으로 처리 | 바뀐 값을 정상 SQL 결과처럼 가르치지 않기 위해 |
| 중단 뒤 자원·상태가 남을 수 있음 | finally에서 커서·콜백·연결을 정리하고 요청 context를 초기화 | 다음 정상 요청이 이전 실패에 묶이지 않도록 |
| API 응답 자체가 커질 수 있음 | 응답을 제한 범위에서 보관한 뒤 전송하고 초과 시 고정된 503 response_limit로 대체 | 원래 성공 헤더를 먼저 보내고 나중에 실패하는 상황을 피하기 위해 |
| /api 아래 배치하면 검사 누락 | 공통 경로 해석기로 root_path·실제 경로를 함께 처리 | 직접 경로와 mount된 경로에서 같은 제한을 적용하기 위해 |
| 제한 상태에서 표가 없어 화면 오류 | SQL 중단 전용 패널을 먼저 표시 | table이 없는 응답에 columns를 읽던 오류를 막기 위해 |
| 서버의 입력 거부가 연결 오류로 바뀜 | 알려진 안전한 오류를 LabRequestError로 전달하고 Lens·실행 안내에 표시 | 입력을 고쳐야 하는지 연결을 확인해야 하는지 구분하기 위해 |

입력 거부 413/422, 응답 상한 초과 503, SQL trace의 resource_limit·blocked는 서로 다른 전달 경로다. 모든 SQL 중단이 HTTP 503이라는 뜻은 아니다. 알 수 없는 예외의 내부 경로·상세 내용은 화면에 그대로 출력하지 않는다.

## 4. 제한값을 왜 이렇게 제안했나

아래는 **팀 미승인 후보값**이다. 프로젝트 입력 계약과 측정값에서 계산했고, 여유 배수·시간 배분은 별도의 정책 선택임을 명시했다. “다들 이 값을 쓴다”는 이유로 정한 값이 아니다.

| 항목 | 후보 | 우리 프로젝트에서의 근거 |
| --- | --- | --- |
| 문자열 | 2,000 코드포인트 | 기존 모형·UI 입력 범위를 유지. 한글·이모지를 포함한 긴 입력 관찰도 보존 |
| history | 40개 / 총 2,000자 | 기존 최근 시도·권한 기록 계약 유지. 현재 허용 최장 명령 21자 × 40개 = 840자 |
| JSON 본문 | 32KiB | 2,000개 비BMP 문자의 JSON escape와 최장 history 40개를 합친 25,028바이트를 수용. 다음 2의 거듭제곱 선택 |
| 요청별 SQL 작업 | 8,192단위 | 최초 측정 요청 상계 800에 여유 8배를 둔 6,400보다 큰 다음 2의 거듭제곱. 집계 보정 뒤 시험 최대 시도 1,472·분석 730도 수용 |
| SQL 시간 | 80ms | 자동분석 대기 320ms의 1/4을 SQL 처리 목표 예산으로 배정. 나머지 전송·화면 처리 여유를 의도 |
| SQL 반환 행 | 128행 | 현재 수업 데이터와 2,000자 내 UNION 합성 사례 83행을 수용하는 다음 2의 거듭제곱 |
| 한 셀 | 8KiB | 2,000 코드포인트 × UTF-8 최대 4바이트 = 8,000바이트 수용 |
| SQL 결과 | 32KiB | 현재 3컬럼 한 행의 각 셀이 8,000바이트인 경우와 JSON 구분자를 수용 |
| SQL 문장 / 엔진 값·행 | 8KiB / 32KiB | 입력 UTF-8 최대량에 조립 접두·접미·EXPLAIN을 더해 문장 상한 계산. 엔진의 행 길이는 단일 셀 길이와 구분 |
| 전체 API 응답 | 256KiB | 합성 경계 포함 최대 관측 107,526바이트 × 여유 2배를 수용하는 다음 2의 거듭제곱 |
| IDOR 식별자 | 0 ~ 2^53−1 정수 | 프론트 JavaScript Number의 정확한 정수 표현 범위와 서버 계약을 맞춤 |

8,192는 정확한 SQLite opcode 수가 아니다. 짧은 문장 예약량·progress 구간·EXPLAIN 목록 작업을 합친 **보수적 작업 단위**다. 최초 VM 측정값과 구현 집계값의 의미 차이도 팀 검토 대상이다.

8배·2배·1/4 배분은 측정이 자동으로 증명하는 정답이 아니다. 수업 변형을 얼마나 허용할지와 서비스 반응 목표에 대한 제안이다. 80ms도 OS가 강제로 끊는 절대 시간 상한이 아니다.

Python은 코드포인트, HTML maxLength는 UTF-16 단위를 세므로 이모지 입력에서 UI가 더 엄격할 수 있다. 행·셀·총결과 상한은 동시에 적용되므로 128개의 큰 셀을 모두 반환한다는 보장도 없다.

자세한 계산·원자료·측정 범위: [상한 산정 근거](../verification/2026-10-28-issue42-limit-rationale.md). 고정 main/#19 버전에서 총 916회 경로 함수 직접 호출을 측정했으며 HTTP·동시성 시험과 구분했다.

## 5. 코드는 어디를 보면 되나

| 역할 | 파일·핵심 이름 |
| --- | --- |
| 입력·본문·history 검증 | [request_limits.py](../../backend/app/core/request_limits.py): InputLimits, validate_payload, InputGuard |
| SQL 실행·결과 상한·정리 | [sql_limits.py](../../backend/app/core/sql_limits.py): SQLLimits, SQLBudget, run_bounded_query |
| 한 요청의 SQL 예산·실패 상태 공유 | [sql_context.py](../../backend/app/core/sql_context.py): SQLScopeMiddleware, execute_active_sql |
| 응답 크기·전송 상태 처리 | [response_limits.py](../../backend/app/core/response_limits.py): ResponseGuard |
| mount 경로 공통 해석 | [lab_paths.py](../../backend/app/core/lab_paths.py): lab_route |
| SQL 판정·설명 연결 | [sql_injection.py](../../backend/app/labs/sql_injection.py), [learning_trace.py](../../backend/app/learning_trace.py), [routes/labs.py](../../backend/app/routes/labs.py) |
| 정책을 받는 검토용 앱 | [review_app.py](../../backend/app/review_app.py): create_review_app |
| 안전한 오류 안내 전달 | [api.js](../../frontend/src/api.js), [App.jsx](../../frontend/src/App.jsx), [useInputAnalysis.js](../../frontend/src/useInputAnalysis.js), [InputDock.jsx](../../frontend/src/InputDock.jsx), [WorkspaceParts.jsx](../../frontend/src/WorkspaceParts.jsx) |
| SQL 중단 화면 | [ExecutionCanvas.jsx](../../frontend/src/ExecutionCanvas.jsx), [learning-content.js](../../frontend/src/learning-content.js) |
| backend 검사 | backend/tests의 test_request_limits.py, test_request_limits_http.py, test_sql_limits.py, test_response_limits.py, test_review_app.py |
| frontend 검사 | frontend/src의 api-limit-feedback.test.js, resource-limit-view.test.jsx, api-user-feedback.test.jsx, useInputAnalysis.test.jsx |
| 로컬 검토 실행기 | [issue42_review_server.py](../verification/scripts/issue42_review_server.py), [Vite 검토 설정](../../frontend/vite.issue42-review.config.js) |

실행기는 미승인 정책 인지 옵션을 요구하고 loopback 주소를 사용한다. 시험용 authorizer의 허용 SQL 연산·함수도 최종 정책이 아니다. 기본 서버 실행 설정에 임의로 대입하지 않는다.

## 6. 전후 동작을 예로 설명하면

**너무 큰 직접 요청:** 예전에는 화면 제한과 별개로 서버 공통 크기 검사가 부족했다. 검토용 앱은 실제 받은 바이트를 세어 상한 초과를 413으로 거부한다. 입력을 잘라 다른 문장으로 실행하지 않는다.

**너무 큰 SQL 계산:** 검토용 앱은 요청의 공통 예산으로 중단하고 자원 한도 상태를 설명한다. “조회했더니 0명”이나 “문법이 틀림”으로 표시하지 않는다. 연결 정리 뒤 새 정상 요청이 동작하는지 검사했다.

**IDOR에 9007199254740992 입력:** 후보 식별자 범위를 넘으므로 422다. 자동분석 Lens와 실행 안내에서 입력 형식·길이·값을 확인하라고 보여준다. 1042로 바꾸면 본인 주문의 정상 결과로 돌아오는 것을 실제 화면에서 확인했다.

**응답이 너무 큼:** ResponseGuard는 과도한 성공 응답 대신 고정된 response_limit 안내를 반환한다. 이미 상위 코드가 할당한 모든 메모리를 되돌리거나 전체 프로세스 메모리를 강제 제한하는 기능은 아니다.

## 7. 어떤 검증으로 확인했나

| 검증 범위 | 결과와 근거 |
| --- | --- |
| 길이 경계·타입·JSON·history·직접 요청 | [입력 검증](../verification/2026-10-28-issue42-stage1-verification.md), [실제 HTTP](../verification/2026-10-28-issue42-stage2-http-verification.md). 실제 HTTP 21개는 backend 전체 수에 포함 |
| SQL 예산·취소·연결 정리·정상 재요청 | [2차 검증](../verification/2026-10-28-issue42-second-verification.md), [EXPLAIN 보정](../verification/2026-10-28-issue42-compile-second-verification.md) |
| 기존 SQL 학습 동작 보존 | [고정 60사례 비교](../verification/2026-10-28-issue42-sql-compatibility.md). 모든 SQL 구문의 호환성 보장은 아님 |
| 응답 제한·잘못된 스트림 상태·정리 | [응답 2차 검증](../verification/2026-10-28-issue42-response-second-verification.md) |
| 실제 경로·mount·공통 예산 연결 | [연결 2차 검증](../verification/2026-10-28-issue42-wiring-second-verification.md) |
| SQL 중단 화면·정상 복구 | [화면 검증](../verification/2026-10-28-issue42-ui-verification.md) |
| 입력 거부 전달·Lens 안내·정상 복구 | [화면 2차 검증](../verification/2026-10-28-issue42-ui-second-verification.md). 422는 실제 브라우저, 413/503 화면은 모의 fetch와 실제 App 렌더 검사 |
| #19와 통합한 전체 회귀 | [통합 기록](../verification/2026-10-28-suwoong-integration.md): backend 362·frontend 128·데이터 7 통과, 빌드 488모듈 성공 |

스크린샷은 각 검증 문서에 연결했다. 전체 검사 수에는 기존 검사도 포함된다. 이번 설명 문서 작성 때문에 같은 검사를 새로 수행했다고 주장하지 않는다.

## 8. 남은 결정과 적용 범위

- 팀의 숫자·작업 단위 의미·SQL authorizer 승인과 #6/#24 결정 기록.
- 승인된 정책으로 기본 앱에 연결할지 결정하고, 연결한다면 그 후보를 다시 검증.
- 목표 환경에서 시간·용량·정상 수업 영향 확인. 현재 작은 로컬 시험을 실제 고부하·외부 대상 시험으로 확대 해석하지 않음.
- 이번 개인 브랜치 공유와 별도로 PR·팀 검토·main 반영이 남는다. 실제 전송 상태는 WORK-STATE와 원격 Git으로 확인.
- #42 종료는 팀장 태성의 최종 검토·보고로 결정.

지금 구현은 요청별 입력·SQL·응답 장치다. 요청량 제한·공유 IP·신뢰 프록시 등 앞으로 다룰 작업을 이미 구현한 것으로 설명하지 않는다. 공개 배포 승인이나 전체 서비스 보호 완료를 의미하지 않는다.