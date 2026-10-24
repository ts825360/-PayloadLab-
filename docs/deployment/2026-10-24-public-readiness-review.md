# 공개 배포 전 1차 코드·의존성 점검

연결: [#24 보안 점검](https://github.com/ts825360/-PayloadLab-/issues/24), [#12 Docker](https://github.com/ts825360/-PayloadLab-/issues/12), [#6 안전 모델](https://github.com/ts825360/-PayloadLab-/issues/6)

기준: `main`의 `5cca64cafc5fd40b1582de4c1f1d0d88eda3b1ba`, 2026-10-24. 코드 수정·공개 배포 없이 소스, 실행 중인 로컬 Docker, 공개 의존성 권고를 조사했다.

## 판단

**현재 개발 구성을 그대로 인터넷에 공개하지 않는다.** 로컬 기능 검증은 통과했지만 공개용 실행 경계와 남용 방지가 부족하다. 현재 포트는 `127.0.0.1`에만 연결되어 있다. 아래 문제는 주로 이 구성을 공개로 전환할 때의 차단 사유이며, 현재 서버가 인터넷에서 공격받았다는 보고가 아니다.

특히 ‘모든 기능이 규칙 기반 시뮬레이션이므로 위협이 없다’는 설명은 현행 코드와 다르다. SQL은 실제 메모리 SQLite 쿼리이며 XSS 결과는 실제 HTML 실행 경로가 있다. SSRF·CMDi·Linux·권한 학습은 제한된 모형이다.

## 확인한 문제와 필요한 조치

| 우선순위 | 확인한 사실·근거 | 공개 전 필요한 조치 |
| --- | --- | --- |
| P1 · 차단 | `routes/labs.py:42–55`, `labs/reflected_xss.py`의 `/render`가 입력을 원본 HTML로 반환한다. 무해한 `document.title` 표식이 HTTP 200으로 반사됐고 CSP가 없었다. UI의 iframe에는 `allow-scripts allow-modals`가 있지만 직접 URL 접근에는 부모 iframe 속성이 적용되지 않는다. | 공개판에서 원본 실행을 끄고 모형으로 설명할지, 별도 실행 origin과 응답 CSP sandbox·리소스 제한을 마련해 유지할지 결정한다. iframe과 직접 URL을 모두 시험한다. |
| P1 · 차단 | `routes/labs.py:25,35`는 일반 dict를 받는다. UI의 `InputDock.jsx:98`은 2,000자 제한이 있지만 SQL·XSS API에 4,096자를 직접 보내면 HTTP 200과 원문 4,096자가 반환됐다. 확장 모형은 같은 길이를 unsupported로 처리한다. 앱의 공통 요청 크기·빈도·동시성 제한은 없다. | 서버에서 필드 타입·길이·JSON 전체 크기를 검증한다. 프록시/API 요청 빈도·동시성·시간 제한을 설계하고 정상 교육 입력은 유지한다. 브라우저 maxLength는 보안 경계가 아니다. |
| P1 · 차단 | `sql_injection.py:56`, `learning_trace.py:140`에서 사용자 조립 SQL을 실제 실행한다. 메모리 DB이지만 VM 명령 수·실행시간·결과량 제한이 없다. 작은 4,096바이트 randomblob 식의 길이를 계산하는 UNION 입력이 실제 행을 반환했다. 무거운 계산이나 대량 결과를 요청한 것은 아니다. | 교육 목표에 맞는 SQL 기능 범위와 계산·행 수·응답 크기 상한, 취소 가능한 실행 격리를 정한다. 메모리 DB와 컨테이너 전체 제한만으로 요청별 계산 비용이 제한되지는 않는다. |
| P1 · 차단 | Docker가 Vite 개발 서버와 Uvicorn reload·소스 bind mount로 동작한다. `/src/App.jsx`가 변환된 소스로 HTTP 200을 반환했다. Vite 5.4.21에 공개 보안 권고가 있다. | 정적 빌드 결과를 운영 웹 서버로 제공하고 개발 서버·reload·개발 mount를 공개 경로에서 제거한다. 의존성 호환 업그레이드와 재검증이 필요하다. |
| P2 · 운영 준비 | 두 컨테이너의 실제 UID가 0, ReadonlyRootfs=false였다. capability 제거·no-new-privileges·CPU/메모리/PID 제한은 적용되어 있으나 아웃바운드 차단·공개 인증/접근 정책·TLS는 현재 구성에 없다. 프론트 API 주소도 localhost이다. | 비-root·쓰기 범위 최소화·필요한 외부 통신만 허용하는 운영 구성을 검토한다. 공개 도메인/API 경로·TLS·오류/로그 정책을 정한다. 익명 공개라면 회원가입 대신에도 요청량 제한과 운영 통제는 필요하다. |

P1은 이 프로젝트의 공개 전 수정 우선순위다. CVSS 평가나 침해 발생 판정이 아니다. XSS의 의도적인 교육용 취약점을 무조건 제거하자는 뜻도 아니며, 학습 실행과 서비스의 신뢰 경계를 분리하자는 판단이다.

## 의존성 조회

실행 중인 컨테이너의 버전을 기준으로 조회했다. 자동 업그레이드·`audit fix`는 하지 않았다.

- `docker compose exec -T frontend npm audit --json`: 취약점 집계 대상 패키지 **6개**(Critical 2, High 1, Moderate 3). 이는 CVE 6개나 실제 악용 가능한 경로 6개라는 뜻이 아니다.
- `npm audit --omit=dev --json`: 현재 registry 기준 **0개**. 하지만 지금은 devDependency인 **Vite 자체를 서비스 서버로 실행**하므로 이 결과만으로 공개 안전성을 주장할 수 없다.
- Vite 5.4.21: 파일 접근·개발 서버 관련 권고. 운영체제와 구성에 따라 영향이 다르며 Windows 전용 경고를 Linux 컨테이너에서 재현됐다고 주장하지 않는다. [Vite 공식 권고 예시](https://github.com/vitejs/vite/security/advisories/GHSA-4w7w-66w2-5vf9).
- Vitest 2.1.9·tinypool 관련 Critical 경고는 테스트 도구 조건을 구분해야 한다. 현재 `vitest run`이며 Vitest UI/API 서버를 공개로 열어 두지 않았다. 따라서 이 수치만으로 현재 웹 앱의 원격 코드 실행이 입증됐다고 해석하지 않는다. [Vitest UI 권고](https://github.com/vitest-dev/vitest/security/advisories/GHSA-5xrq-8626-4rwp).
- Python 설치 패키지 18개의 이름·버전을 [OSV querybatch](https://google.github.io/osv.dev/post-v1-querybatch/)에 조회했다. Starlette **0.38.6**, pip **25.0.1**에서 권고가 반환됐다. GHSA/PYSEC 별칭을 서로 다른 취약점으로 중복 집계하지 않았다.
- Starlette의 form/multipart 파싱, Windows StaticFiles, HTTPEndpoint, URL 재구성 관련 경고는 **현재 라우트의 JSON 처리·HTMLResponse에서 해당 기능을 사용하는지 별도 구분**했다. 이 앱에서 그 경로를 통한 악용은 입증하지 않았다. pip 경고는 주로 설치·빌드 도구 경로다. 의존성 갱신 시 FastAPI와 Starlette 호환 범위를 함께 검토한다. [Starlette multipart 권고](https://github.com/encode/starlette/security/advisories/GHSA-f96h-pmfr-66vw), [Host/URL 권고](https://github.com/Kludex/starlette/security/advisories/GHSA-86qp-5c8j-p5mr).

공개 권고 데이터는 변한다. 위 0개·개수는 조회 시점의 결과이며 안전 보증이 아니다. Python 직접 의존성은 고정되어 있지만 전이 의존성 lock이 없고, 프론트 Dockerfile의 npm install은 저장소 pnpm lockfile과 일치하는 설치를 보장하지 않는다.

## 수행한 검사와 하지 않은 검사

수행:

- 백엔드 pytest **100 passed**, Docker 내부 프론트 Vitest **54 passed**.
- 소량의 로컬 HTTP 검사: XSS 원문 반사·헤더 부재, SQL/XSS 4,096자 수용, SSRF 모형 길이 거절, 작은 SQLite 식 실행, Vite 개발 소스 응답.
- 실제 컨테이너 UID·쓰기 가능 설정과 기존 loopback 바인딩 확인.
- 코드상 실제 subprocess·외부 HTTP/DNS·호스트 파일 실습이 없는 확장 모형과 허용 명령/가상 기록 검사 확인.
- 작업 트리의 제한된 키/토큰 패턴 검색에서 일치 파일을 발견하지 못했다. 전체 비밀정보 탐지나 과거 Git 이력 검사로 간주하지 않는다.

미수행:

- 브라우저 실행·네트워크 관찰: 로컬 브라우저 사용이 비활성화되어 **JS 실행·외부 전송·상위 화면 접근을 직접 재현하지 않았다**. XSS 영향 판단은 응답과 소스 및 웹 표준에 근거한다.
- 부하/DoS 시험, 외부 대상 공격, 데이터셋 자동 실행, 이미지 OS 패키지 전체 스캔, 외부 침투 테스트, TLS/도메인/실제 공개 호스트 검증, 법률 검토.

기능 테스트 통과는 의도한 학습 결과의 근거이며 악의적인 모든 입력을 막았다는 보증이 아니다.

## 제안하는 진행 순서 — 아직 구현 승인 아님

1. 공개판의 XSS 실제 실행 유지 여부와 SQL 실행 상한을 결정한다. 초기 공개는 원본 XSS 실행을 제외하는 안이 관리 부담이 작다. 실제 실행을 유지하면 별도 origin과 응답 정책부터 검증한다.
2. 공통 서버 입력 검증·요청/실행 제한을 추가하고 회귀 검사한다.
3. 의존성 호환 업데이트, 재현 가능한 설치, 운영용 정적 프론트·프록시/API 구성을 만든다.
4. 접근·네트워크·로그·자원 제한과 통제된 브라우저 보안 검사를 수행한다. 그 뒤 제한 공개/일반 공개를 별도 승인한다.

응답 CSP의 sandbox와 iframe 속성의 의미는 [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/sandbox), 정적 빌드 배포는 [Vite](https://vite.dev/guide/static-deploy.html), HTTPS·프로세스·메모리 등 운영 준비는 [FastAPI](https://fastapi.tiangolo.com/deployment/concepts/)를 참고했다. 공식 문서는 판단 근거이지 이 앱에서의 브라우저 검증을 대신하지 않는다.
