# 로컬 실습의 안전 범위와 보관 정책

연결: [#6](https://github.com/ts825360/-PayloadLab-/issues/6), [#12](https://github.com/ts825360/-PayloadLab-/issues/12), [#24](https://github.com/ts825360/-PayloadLab-/issues/24), [승인 범위](../decisions/2026-10-23-unified-workspace.md)

이 문서는 소스에 있는 동작과 배포 전 제안을 구분합니다. 2026-10-24에 Docker 이미지 빌드·컨테이너 기동과 제한 적용을 확인했습니다. [실행 기록](2026-10-24-local-compose-verification.md)을 참고하세요. 외부 PC 접근 차단·공개 서비스 안전성 승인은 별개입니다.

## 현재 실습이 실행하는 것

| 유형 | 확인한 구현 | 안전 경계·한계 |
| --- | --- | --- |
| SQLi | `labs/sql_injection.py`, `learning_trace.py`에서 SQLite `:memory:`를 새로 만들고 더미 계정 시드 사용 | 실제 SQL 엔진 실행. 외부 운영 DB가 아니며 조회 연결은 `finally`에서 닫음. 임의 쿼리의 계산 비용까지 메모리 DB가 제한해 주지는 않음 |
| XSS | `labs/reflected_xss.py`가 입력을 이스케이프 없이 HTML에 삽입. `/render`가 원본 문서를 응답 | 의도적으로 취약함. `ExecutionCanvas.jsx`에서 사용자가 결과를 열면 실제 브라우저가 파싱·실행 |
| IDOR | `labs/idor.py`의 고정 `_CURRENT_USER_ID`, `_ORDERS` | 더미 소유 관계 모형. 실제 인증·서버 세션 없음 |
| SSRF | `practice_extensions.py`의 URL 파싱·IP 문자열 검사·더미 응답 | DNS 조회·HTTP 요청 없음. 문자열 모형을 실제 네트워크 검증 완료라고 해석하지 않음 |
| Command Injection | 호스트·구분자와 허용 명령의 토큰 비교 | 실제 셸·subprocess·ping 실행 없음 |
| Linux·권한상승 | 가상 파일, 명령 퀴즈와 허용 명령 목록. 권한 상태는 요청의 history로 복원 | 호스트 파일 접근·실제 sudo·OS 권한 변경 없음. 범용 터미널 아님 |

현재 확장 모형은 입력 최대 2,000자, 권한 history 최대 40개·총 2,000자와 허용 목록을 검사합니다. 이 제한이 모든 API 요청·SQL·HTML 응답에 공통으로 적용되는 것은 아닙니다. 전체 요청 크기·시간·빈도·동시성 제한은 별도 검증 대상입니다.

## 상태별 수명과 삭제

TTL은 ‘얼마 후 만료되는가’라는 시간 정책입니다. 개수 제한, 새로고침 초기화, 연결 종료와 구분합니다. 현재 기능에 없는 세션·DNS 캐시·임시 작업 큐를 가정해 일괄 타이머를 추가하지 않습니다.

| 상태·위치 | 현재 수명·제한 | 정리 방법 / 필요한 후속 정책 |
| --- | --- | --- |
| 학습 입력·시도·비교, `App.jsx`의 React state | 탭의 현재 앱 인스턴스 메모리. 유형 전체를 합쳐 최근 40개, 시간 TTL 없음 | 새로고침·앱 종료 시 초기화. 브라우저·OS가 메모리를 즉시 안전 삭제함을 보장하는 것은 아님 |
| 테마, `localStorage` 키 `payloadlab-workspace-theme` | 새로고침 뒤에도 유지. 앱이 만료 시간을 두지 않음 | 사이트 저장소 삭제 또는 개발자 도구에서 이 키 제거. 현재 학습 기록은 이 키에 저장하지 않음 |
| SQL 로그인·조회 근거 DB | 요청 처리 중 생성하는 개인 SQLite `:memory:` 연결과 고정 시드 | 조회 연결 종료 시 DB 소멸. 영구 DB·백업·세션 TTL 불필요. 보조 설명의 메모리 연결도 명시적 해제 여부를 유지보수 시 점검 |
| IDOR 고정 더미 데이터 | 코드 상수로 로드 | 사용자별 변경·누적 기록 없음. 실행 중 상태를 주기 삭제할 대상이 아님 |
| 권한 실습 가상 사용자 | 클라이언트 history를 매 요청 새 가상 상태에 재생 | 서버에 사용자 세션 저장 안 함. history 길이·총량·허용 목록 검증 유지 |
| 서버 세션·로그인 토큰 | 현재 기능 없음 | 향후 인증을 추가할 때만 만료·철회·보관 범위를 설계 |
| DNS/SSRF 응답 캐시 | 모형에서 DNS·HTTP를 하지 않으므로 없음 | DNS TTL을 임의로 정할 대상 없음. 실제 요청 도입 시 안전 모델을 새로 검증 |
| 앱 임시 파일·업로드·서버 시도 DB | 현재 코드에 생성·보관 기능 없음 | 업로드·작업 큐 도입 시 생성 주체·삭제 주체·실패 복구를 함께 설계 |
| Uvicorn·Vite 표준 출력 / Docker 로그 | 앱 전용 시간 만료 없음. Compose는 두 서비스에 `json-file`, `max-size: 10m`, `max-file: 3` 설정 | 크기·파일 개수 상한이며 기간 TTL이 아님. 실제 적용·로그 내용·열람·반출 범위를 검증하고 민감 입력·쿼리 문자열의 기록 여부 점검 |
| `node_modules`, Vite 캐시, `dist`, Python/pytest 캐시 | 개발·빌드 산출물. 앱의 학습 상태와 무관 | 재생성 가능. 작업 폴더·Git 이력·원문·manifest와 구분해 필요한 경로만 정리. 자동 시간 삭제 없음 |
| Docker 이미지·빌드 캐시 | Docker가 관리. `compose down`은 이미지·빌드 캐시 전체를 지우는 명령이 아님 | 다른 프로젝트 자산을 포함한 광범위 prune를 기본 절차로 안내하지 않음. 실제 디스크 정책은 운영자가 결정 |

SQL의 `:memory:` 수명은 SQLite의 [In-Memory Databases](https://sqlite.org/inmemorydb.html)를 근거로 해석했습니다. 시간 만료가 아닌 연결 종료에 따른 수명이라는 구분에 사용했습니다.

현재 시도는 클라이언트 메모리에 있어도 XSS 렌더 URL의 `query`는 URL에 포함됩니다. 개발 서버 접근 로그, 브라우저 기록·진단 도구 등에 남는 범위는 실제 환경에서 확인해야 합니다. 비밀번호·개인정보·인증 토큰은 실습에 넣지 않습니다.

## XSS iframe과 CSP 검토

현재 실행 UI는 `sandbox="allow-scripts allow-modals"`를 사용하며 `allow-same-origin`은 부여하지 않습니다. 이는 스크립트·모달을 허용하면서 출처·상위 화면 접근 등에 제한을 남기는 설정입니다. 그러나 iframe 속성만으로 모든 외부 리소스 요청이나 자원 소모가 차단되는 것은 아닙니다. `/render`를 프레임 밖에서 직접 여는 경로도 검토해야 합니다. sandbox 토큰 의미와 직접 열기 한계는 [MDN iframe](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe)의 설명을 근거로 삼았습니다.

현재 `routes/labs.py`의 HTML 응답에는 CSP 응답 헤더가 없습니다. 후속 검증에서 다음을 확인한 뒤 정책을 결정합니다.

- 교육에 필요한 인라인 스크립트 실행과 원치 않는 외부 `fetch`, 이미지·스크립트·frame·폼 목적지 차단을 함께 시험합니다.
- `/render` 직접 열기에도 적용되는 응답 헤더의 CSP sandbox와 별도 실행 origin을 비교합니다. `allow-scripts`와 `allow-same-origin`을 무심코 함께 허용하지 않습니다.
- `default-src`, `connect-src`, `img-src`, `script-src`, `frame-src`, `form-action`, `base-uri` 등의 목적을 구분합니다. 하나의 지시문만으로 모든 경로가 차단된다고 주장하지 않습니다.
- 무한 루프·반복 모달 등 브라우저 CPU·메모리 사용 위험은 서버 컨테이너 자원 제한으로 해결되지 않으므로 별도 검증합니다.

이는 구현 완료 항목이 아닌 [보안 검토 초안](security-review-issue-draft.md)의 검증 제안입니다. 지시문별 역할은 [MDN CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy)를 참고했으며, 프로젝트에 맞는 차단 범위·호환성은 직접 시험해야 합니다.

## 로컬 컨테이너와 공개 전 조건

Compose의 포트는 호스트 loopback `127.0.0.1:8001`과 `127.0.0.1:5173`에 바인딩합니다. 컨테이너 내부 `0.0.0.0` 리스닝과 호스트의 공개 주소는 다릅니다. Docker의 [Port publishing](https://docs.docker.com/engine/network/port-publishing/)을 근거로 호스트 IP가 없는 포트 공개와 구분했습니다. Docker 28.0.0 이전 버전의 localhost 공개 관련 주의사항도 있으므로 실제 버전·방화벽·라우팅을 확인합니다.

loopback 바인딩은 인바운드 접근 범위 설정이며 컨테이너의 아웃바운드 네트워크 차단이 아닙니다. 현재 Compose에는 외부 통신 차단 정책이나 운영 인증·접근 제어가 없습니다. 소스 bind mount, Vite 개발 서버와 Uvicorn reload 설정을 사용하는 개발 구성입니다. API의 CORS 허용 origin은 브라우저 정책이며 인증·비브라우저 요청 차단을 대체하지 않습니다.

현재 Compose에 기록된 로컬 상한은 다음과 같습니다. 실제 컨테이너의 HostConfig에 적용된 값을 확인했지만, 적정 부하에서 충분한지는 별도 검증 대상입니다.

| 설정 | backend | frontend |
| --- | --- | --- |
| CPU | `cpus: 1.0` | `cpus: 1.0` |
| 메모리 | `mem_limit: 256m` | `mem_limit: 768m` |
| 프로세스 수 | `pids_limit: 64` | `pids_limit: 128` |
| 추가 권한 획득 제한 | `no-new-privileges:true` | `no-new-privileges:true` |
| Linux capability | `cap_drop: [ALL]` | `cap_drop: [ALL]` |
| 로그 회전 | 파일당 `10m`, 최대 `3`개 | 파일당 `10m`, 최대 `3`개 |

이 제한은 호스트 브라우저에서 실행하는 XSS의 CPU·메모리에 적용되지 않습니다. 현재 Dockerfile에 별도 비root 실행 사용자는 정의되어 있지 않으며, capability 제거만으로 모든 호스트·커널 위험이 해결되는 것은 아닙니다.

공개 또는 팀 공용 호스트로 옮기기 전에 다음을 기능별로 검증하고 결과를 기록합니다.

1. 포트·라우팅·접근 제어, 실행 origin, TLS·역방향 프록시와 개발 서버 대체 방식을 결정합니다.
2. 브라우저와 컨테이너의 외부 요청 경로를 따로 관찰하고, 필요한 통신만 허용하는 격리 방식을 검증합니다.
3. 요청 크기·시간·빈도·동시성, SQL 비용, 설정된 컨테이너 CPU·메모리·프로세스 상한과 브라우저 자원 위험을 검사합니다. 현재 상한의 적정성은 실제 부하를 측정한 후 재평가합니다.
4. 비밀값·실제 파일·Docker 소켓·과도한 mount가 이미지나 실행 환경에 들어가지 않는지 확인합니다. 실행 사용자·capability·파일시스템 권한도 검토합니다.
5. 실제 Docker 로그의 내용·회전·보관 범위를 확인합니다. 시간 기반 보관이 필요하면 목적·삭제 주체·종료 조건과 함께 별도 결정합니다.

자원 항목의 의미는 [Compose services](https://docs.docker.com/reference/compose-file/services/)의 `cpus`, `mem_limit`, `pids_limit`을 참고합니다. 로그 회전 검토는 Docker의 [logging driver 문서](https://docs.docker.com/engine/logging/configure/)가 기본 드라이버와 회전의 차이를 설명하므로 근거로 사용했습니다. 파일에 설정이 있어도 Docker 실행 검증을 대신하지 않습니다.

## 실행·검증 기록 방법

[README](../../README.md)의 기능 테스트를 먼저 수행하고, Docker 기동·포트 확인·브라우저 네트워크 관찰·직접 렌더 경로를 별도 기록합니다. 기록에는 커밋·명령·결과·실행 환경·남은 위험을 적습니다. 실패나 미검증을 테스트 통과로 대신하지 않습니다. 새 이슈는 [이슈 가이드](../ISSUE-GUIDE.md)에 따라 승인받은 뒤 등록하며, 이 문서 작성으로 새 이슈를 등록하지 않습니다.

`docker compose config --quiet` 구문 검사 외에 후속 [Docker 실행 기록](2026-10-24-local-compose-verification.md)에 이미지 빌드·기동·실제 제한·테스트 결과를 남겼습니다. 공개 전 검증을 대신하지 않습니다.
