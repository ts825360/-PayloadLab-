# 보안 검토 이슈 초안 — 등록 전

연결: [#6](https://github.com/ts825360/-PayloadLab-/issues/6), [#12](https://github.com/ts825360/-PayloadLab-/issues/12), [#24](https://github.com/ts825360/-PayloadLab-/issues/24), [이슈 가이드](../ISSUE-GUIDE.md)

상태: 사용자 승인 대기인 로컬 초안. **새 이슈를 등록하지 않았습니다.** 제목 제안은 `🟠 공개 전 XSS 실행과 로컬 배포 안전 경계를 검증한다`, 라벨 제안은 `P1`, `type: idea`, `area: infra`, `needs-spike`입니다. 실제 등록 시 저장소의 기존 라벨 이름을 확인합니다. 아래 세 절이 이슈 본문 초안입니다.

## 문제

- 이 저장소는 SQLi·XSS·IDOR·SSRF·CMDi·Linux의 Easy/Normal과 권한상승 Easy 등 13개 랩을 함께 실행한다. SQL은 실제 메모리 SQLite, XSS는 실제 HTML 렌더링을 포함하지만 나머지 확장 실습은 DNS·HTTP·셸·호스트 파일을 사용하지 않는 제한된 모형이다. 현재 코드 사실과 공개 환경의 안전성 검증을 구분해야 한다.
- `frontend/src/ExecutionCanvas.jsx`의 선택적 XSS iframe은 `allow-scripts allow-modals`를 허용하고, `backend/app/routes/labs.py`의 `/render`는 취약한 원본 HTML을 직접 응답한다. 현재 응답에는 CSP가 없다. iframe 외부 요청·직접 URL 열기·상위 화면/저장소 접근·브라우저 자원 소모를 실제 브라우저에서 확인하지 않았다.
- Compose의 loopback 포트 바인딩은 개인 PC의 인바운드 범위를 줄이는 설정이다. 실제 Docker 버전·방화벽·라우팅, 컨테이너 아웃바운드, 공용 호스트 인증·접근 제어·요청 제한이 검증됐다는 뜻은 아니다. Vite 개발 서버, reload, 소스 bind mount가 있는 현재 구성을 그대로 운영 구성으로 사용할 근거가 없다.
- 현재 두 서비스에는 capability 제거·추가 권한 획득 방지·CPU/메모리/프로세스 상한과 `10m × 최대 3개` 로그 회전이 설정되어 있다. Compose 구문 검사 통과와 실제 컨테이너 적용·부하 적정성·브라우저 자원 제한은 별개의 검증이다.
- `App.jsx`의 시도 기록은 React 메모리 최근 40개, 테마는 localStorage이다. SQLi는 요청별 메모리 DB이며 서버 세션·시도 DB·DNS 캐시는 없다. 기존 기능에 없는 일괄 TTL을 붙이는 대신 실제 URL/접근 로그, 개발·빌드 캐시와 Docker 로그의 수명·용량을 확인해야 한다.
- 프론트엔드 로컬 개발은 pnpm lockfile을 사용하지만 Dockerfile은 `npm install`을 사용한다. 이미지 재현성·의존성 점검 범위를 확정해야 한다.

## 제안

- **먼저 스파이크:** 로컬 격리 환경에서 XSS의 정상 교육용 인라인 실행, 외부 fetch·이미지·스크립트·중첩 frame·폼 요청, `/render` 직접 열기, 반복 모달·계산 부하를 각각 검사한다. 허용되지 않은 외부 대상을 공격하거나 수집한 공격 CSV를 자동 실행하지 않는다. 네트워크 시험에는 통제된 로컬 수신점 또는 브라우저 요청 가로채기를 사용한다.
- XSS 실행 문서의 CSP 응답 헤더·sandbox·별도 origin 선택지를 비교한다. 인라인 교육 동작은 유지하면서 리소스·폼·연결 목적지를 제한하는지 실제 네트워크 관찰로 검증한다. 브라우저 실행과 백엔드 모형의 안전 경계를 각각 기록한다.
- Compose 유효 구성과 실제 published address를 확인하고, 자원·프로세스 상한, 최소 권한·mount, 외부 통신 제한을 기능별로 시험한다. 현재 추가된 로컬 보호 설정이 있다면 그 적용 여부와 남은 위험을 기록한다. 공용 호스트 인증·TLS·프록시·요청 제한·운영 서버는 검증 결과에 따라 별도 구현 범위를 정한다.
- 로그에는 실제 비밀값을 넣지 않고 더미 표식으로 URL·입력의 기록 여부를 조사한다. 기존 로그에는 용량·개수·접근·반출 정책을, 향후 영구 기록에는 목적과 삭제 주체를 정한다. 서버 세션·DNS 캐시가 생기기 전에는 임의의 시간 TTL을 만들지 않는다.
- pnpm lockfile과 이미지 설치 경로의 일관성·스캔 범위를 확인한다. 빌드 문맥에 소스·필수 manifest는 포함하되 `.git`, 로컬 도구 설정·비밀값, node_modules·dist·Python 캐시는 포함하지 않는지 검사한다.
- 이 초안과 후속 이슈 등록은 코드 변경이나 공개 배포를 승인하는 절차가 아니다. 실제 공개는 검증 결과·제한·운영 책임을 팀이 검토한 뒤 별도로 승인한다.

## 검증

- 현재 커밋·환경·명령·관찰 결과를 기능별로 남긴다. DOM 테스트·빌드, Docker 빌드/기동, 브라우저 동작, 공개 전 검토를 분리한다.
- 13개 랩과 권한 Normal 미제공이 유지되고, SSRF의 DNS/HTTP 미실행 및 CMDi·Linux·권한의 실제 셸/파일 미사용이 회귀 검사와 코드 검토에서 확인된다.
- 통제된 시험에서 XSS의 의도한 인라인 실행만 성공하고, 정한 외부 리소스·폼·스크립트 요청이 실패하는 근거가 남는다. iframe과 직접 `/render` 접근을 모두 확인하며, 상위 화면·저장소 접근 및 자원 위험의 결과·한계가 기록된다.
- `docker compose config`, 실제 포트·컨테이너 설정 및 로그를 대조한다. loopback 접근과 외부 PC 차단, 아웃바운드 정책, CPU/메모리/프로세스 상한·비정상 입력의 복구를 각각 확인한다. 실행하지 못한 항목은 미검증으로 남긴다.
- React 기록 40개·새로고침 초기화, 테마의 지속, 서버 영구 기록 부재가 확인된다. 로그·캐시의 보관·삭제 주체 및 필요한 제한을 근거와 함께 결정한다.
- 기능별 검증과 조치 뒤 마지막에 통합 검증을 수행한다. 이슈 완료는 공개 배포 승인이 아니라 **검증 결과·남은 위험·팀 결정이 연결 이슈와 문서에 기록된 상태**로 정의한다.

관련 문서: [현재 구조](../architecture/repository-structure.md), [로컬 안전·보관 정책 및 공식 출처](local-safety-and-retention.md), [통합 작업 승인 범위](../decisions/2026-10-23-unified-workspace.md)

공식 근거는 Docker의 [port publishing](https://docs.docker.com/engine/network/port-publishing/), [Compose services](https://docs.docker.com/reference/compose-file/services/), [logging drivers](https://docs.docker.com/engine/logging/configure/), MDN의 [iframe sandbox](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe), [CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy), SQLite의 [메모리 DB 수명](https://sqlite.org/inmemorydb.html)이다. 포트·격리·리소스 지시문과 상태 수명의 의미를 확인하는 데 사용하며, 이 링크 자체를 PayloadLab 실행 검증으로 보지 않는다.
