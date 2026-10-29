# #44 3단계 — 검토 앱·실제 HTTP·재시도 안내

2026-10-29 / 이수웅(dtd2428), AI 보조. 로컬 미커밋 변경. 기본 app.main.app·Compose는 그대로이며 운영 정책값은 미승인이다.

## 문제와 이번 수정 의도

[2단계 모듈](2026-10-29-issue44-admission-verification.md)은 허용 여부만 판단했다. 이번에는 실제 요청이 모듈을 거치고 거부 이유가 실행 화면·자동 분석 Lens까지 전달되게 연결했다. #42의 입력/SQL/응답 제한도 함께 유지했다.

## 처리 순서와 구현 위치

검토 앱에 admission_controller를 넣은 경우:

    CORS → AdmissionGuard → ResponseGuard → InputGuard → SQLScope → route/모형/trace

| 위치 | 변경·이유 |
| --- | --- |
| [admission_guard.py](../../backend/app/core/admission_guard.py) | ASGI 입구에서 전체/분류/선택적 peer 예산·동시 실행 확인, 고정 거부 응답. IP 헤더는 직접 읽지 않음 |
| [lab_paths.py](../../backend/app/core/lab_paths.py) | 기존 정규화를 relative_path로 추출. #42와 #44가 mount 경로를 같은 방식으로 해석 |
| [review_app.py](../../backend/app/review_app.py) | controller 선택 인자·shutdown drain·Retry-After CORS 노출. 생략하면 기존 #42 방식 유지 |
| 같은 파일 local_review_config | loopback·단일 worker·proxy_headers=False·forwarded_allow_ips 빈 값. Uvicorn이 앱 이전에 임의 XFF로 IP를 바꾸지 않게 |
| [api.js](../../frontend/src/api.js) | 알려진429/503만 안전한 문구로 변환. 기존 #42 안내 보존 |
| [HTTP 검사](../../backend/tests/test_admission_http.py), [화면 검사](../../frontend/src/admission-feedback.test.jsx) | 실제 HTTP 경계와 App/Lens 전달을 각각 검사 |

기존 두 backend 파일 전체 덮어쓰기는 자동 승인 검토가 거부했다. 원문 백업·미커밋 diff 확인·백업과 바이트 일치 확인 후 **최소 패치**로 진행했다. 기존 SQL/Input/Response 로직은 보존했다.

정상 analyze/attempt/render는 해당 분류로, labs 목록·메타데이터·없는 labs 경로·잘못된 메서드는 metadata로 집계한다. 같은 앱을 root와 /api에 mount하면 하나의 controller를 공유한다. /health·/docs·OpenAPI 등 labs 밖 경로와 CORS preflight는 집계 대상 밖이다. 전체 HTTP/DDoS 방어로 설명하지 않는다.

local_review_config를 사용할 때만 위 로컬 서버 설정이 적용된다. 다른 실행 설정·실제 운영 프록시가 자동 보호되는 것은 아니다.

## 전후 응답과 재시도 안내

- 빈도 초과: HTTP429 code=rate_limit, Retry-After 정수 초, Cache-Control:no-store. 실행·분석 화면에는 “요청이 잠시 몰렸습니다. N초 뒤 다시 시도해 주세요.”
- Retry-After가 없거나 비정상이면 고정 “잠시 기다린 뒤” 안내. 양의 정수1~6자리만 화면의 초 단위로 표시한다. 이는 응답 표시 형식 경계이며 운영 제한값이 아니다. HTTP-date 형식도 고정 대기 안내로 처리한다.
- 동시 실행/peer 추적 용량 초과: HTTP503 concurrency_limit 또는 peer_capacity. 완료 시간을 모르므로 Retry-After를 만들어내지 않는다. 화면에는 “실습 서버가 사용 중입니다. 잠시 후 다시 시도해 주세요.”
- render 거부: 요청 입력을 반사하지 않는 고정 안내 HTML. 제한된 입력의 script·표식을 포함하지 않는다.
- 새 입력/정상 재시도: 기존 App/hook 초기화 흐름으로 안내가 지워지고 정상 결과로 복귀한다.
- 서버 내부 detail·경로·HTML은 그대로 출력하지 않는다. 자동 재시도나 버튼 countdown은 추가하지 않았다.
- 초기 fetchLabs의 연결 실패/다시 연결 UI는 기존대로다. 실행·자동분석처럼 초 단위 안내를 전달한 범위와 구분한다.

## 실제 HTTP 관찰과 시험값 근거

[원자료32건](evidence/2026-10-29-issue44-http-observations.json): 응답31건은200=19,429=8,503=2,404=1,405=1. 나머지1건은 응답을 읽기 전에 클라이언트 연결을 닫았다.

| 작은 통제 시험 | 기대/실제 |
| --- | --- |
| 전체 시험 예산2, 정상2회·다음 요청 | 200·200·429, Retry-After=1 |
| 가짜 시계1초 진행 | 다음 정상200으로 복구 |
| root analyze와 /api attempt 뒤 render | 같은 전체 예산이 소진되어 render429 |
| 같은 loopback에서 XFF/Forwarded만 변경 | 같은 peer 예산 사용, 이후429 |
| 같은 peer로 analyze·attempt·render3회 | 시험 허용량3 내 정상, 다음429 |
| 분석 분류 예산 소진 | 분석429 뒤 남은 attempt 예산으로200 |
| script 모양 입력의 render 거부 | 고정 HTML에 script·원문 표식 없음 |
| 목록·잘못된 메서드·없는 labs 경로 | 모두 공통 예산 적용. 검토 앱에 원래 없는 /health는429가 아닌404 |
| 허용 Origin의 preflight | 예산을 소비하지 않으며 제한 응답의 Origin·Retry-After CORS 노출 유지 |
| 동기 probe가 슬롯1개 점유 | 다음503, probe 실제 종료 뒤 정상200 |
| probe 요청의 연결 종료 | 실제 handler 종료 전 슬롯 유지·다음503, 종료 뒤200 |

2/3/1은 경계를 작게 드러내는 시험값이다. 운영 후보값이나 사용자의 실제 학습량 측정이 아니다. loopback·단일 프로세스 시험이며 외부 대상/공개 서버에 부하를 보내지 않았다.

추가 ASGI 검사: 통제된 peer3개로 바꿔도 전체 예산200·200·429, 경로7사례, 호출자 취소 후 늦은 send 차단·실제 작업 종료까지 슬롯 유지. IP 자체 변경은 **ASGI 모의**이며 실제 여러 IP 클라이언트를 연결한 시험은 아니다.

## 실패·수정과 검사 근거

- guard 미구현 import 실패: [로그](evidence/2026-10-29-issue44-http-before.txt).
- 첫 연결3실패/16통과: 검토 앱에 없는 health에200을 기대했고, 시험 probe를 generic route 뒤에 추가해 도달하지 못했다. 제품 버그3개로 세지 않고 검사 기대·라우트 순서를 수정. [당시 로그](evidence/2026-10-29-issue44-http-after.txt).
- 오류 매핑 전 화면9실패/1통과: 하나의 미구현이 여러 전달 경로에서 드러난 결과이며 독립 제품 버그9개로 세지 않는다. [로그](evidence/2026-10-29-issue44-ui-before.txt).
- HTTP·ASGI 연결 검사19개 통과. [로그](evidence/2026-10-29-issue44-http-final.txt).
- backend 전체413개 통과(2단계32·이번19 포함). [로그](evidence/2026-10-29-issue44-http-backend-tests.txt).
- frontend23파일138개 통과(이번10 포함). [로그](evidence/2026-10-29-issue44-http-frontend-tests.txt).
- [빌드 로그](evidence/2026-10-29-issue44-http-frontend-build.txt). 성공 여부·모듈 수는 아래 마감 기록 참조.
- 소스 기준은 HEAD eaa3998526b60ea0109cd1b9a08914336944a806 + 이번 미커밋 변경. 최종 파일해시/환경은 마감 근거에 저장한다.

재현: backend에서 python -m pytest tests/test_admission.py tests/test_admission_http.py -q 및 python -m pytest -q. 프론트에서 pnpm exec vitest run --maxWorkers=2 --minWorkers=1 및 pnpm build.

HTTP 원자료를 갱신하려면 ISSUE44_HTTP_EVIDENCE 환경변수에 로컬 경로를 명시한다. 지정하지 않은 일반 pytest 실행은 JSON을 덮어쓰지 않는다.

## 아직 남은 것

1. 실제 브라우저의 안내·iframe 표시/기기 검증. 이번 화면은 jsdom App 렌더 검사이며 새 스크린샷 근거는 없다.
2. 학습자 수·정상 요청 패턴·목표 환경·지연/용량 목표로 빈도·동시 실행·대기열·시간 후보 산정 및 #6/#24 검토.
3. 느린 본문·실제 HTTP timeout·강제 종료. 슬롯 유지가 작업 강제 종료를 제공하는 것은 아니다.
4. 실제 신뢰 프록시 목록·헤더 덮어쓰기·원본 API 접근 차단을 #12/#24와 연결. 로컬 no-proxy만으로 운영 우회 방지 완료라고 할 수 없다.
5. 다중 worker/인스턴스 공유 집계·실제 학교 NAT·초기 목록 재시도 안내·자동분석 cooldown 검토. 현재 카운터는 프로세스별이다.
6. 운영 경보·비용·긴급 중지 책임, 사용자 문서 검토 후 이슈 댓글·커밋·푸시·PR·팀 검토·main 반영. 이슈 종료나 공개 승인은 하지 않았다.

#19/#42 설명도 사용자 결정대로 #44 작업과 함께 나중에 커밋·푸시한다. 지금 게시하지 않는다.
## 마감 기록

backend413개·frontend23파일138개 통과, 빌드488모듈 성공. [검사 대상 소스해시·환경](evidence/2026-10-29-issue44-http-source-hashes.json). 문서 링크·신규 파일 구문·diff 검사는 최종 저장 뒤 별도로 확인한다. 게시·커밋·푸시는 하지 않았다.
