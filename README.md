# PayloadLab

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/brand/payloadlab-wordmark-dark.svg">
  <img src="frontend/public/brand/payloadlab-wordmark.svg" alt="PayloadLab" width="190" height="44">
</picture>

보안 입문자가 입력이 처리되는 과정을 보며, 취약점이 어떤 조건에서 생기는지 배우는 로컬 웹 학습 앱입니다. 입력을 바꾸고 **입력 → 처리 과정 → 결과 → Lens 설명 → 재시도·비교**를 같은 학습 공간에서 확인합니다.

이 저장소 [`ts825360/-PayloadLab-`](https://github.com/ts825360/-PayloadLab-)가 프론트엔드, 백엔드, Docker 설정, 팀 문서를 함께 관리합니다. 이전 문서의 별도 구현 저장소 안내는 당시의 개발 경위이며, 현재 실행에는 이 저장소를 사용합니다. 과거 검증 기록은 [decisions](docs/decisions/README.md)에 남아 있습니다.

## 무엇을 배울 수 있나요?

검증 범위는 [통합 화면 기록](docs/decisions/2026-10-23-unified-workspace.md#2026-10-24-검증-결과)과 [Docker 후속 실행 기록](docs/deployment/2026-10-24-local-compose-verification.md)을 참고하세요. 백엔드 100개 검사와 Docker 내부 프론트엔드 54개 테스트·빌드·13개 랩 API 검사가 통과했습니다. 공개 배포 안전성 검증과는 구분합니다.

현재 백엔드 등록 기준은 **13개 랩**입니다. 아래 6개 유형은 Easy와 Normal을 각각 제공하고, 권한상승 기초는 Easy만 제공합니다. 화면의 Normal은 API 식별자에서 `medium`으로 표현됩니다.

| 유형 | 난이도 | 실제로 하는 일 |
| --- | --- | --- |
| SQL Injection | Easy / Normal | 매번 새 SQLite 메모리 DB에서 취약한 조회를 실행하고 반환된 행을 관찰 |
| Reflected XSS | Easy / Normal | 입력이 HTML이 되는 과정을 분석하고, 사용자가 결과 열기를 선택하면 격리된 iframe에서 실제 HTML·스크립트를 렌더링 |
| IDOR | Easy / Normal | 고정된 더미 주문·사용자로 객체 번호와 소유자 검사의 차이를 관찰 |
| SSRF | Easy / Normal | URL 문자열과 hostname을 파싱해 가상 목적지·응답을 표시. DNS 조회·HTTP 요청 없음 |
| Command Injection | Easy / Normal | 제한된 토큰·명령 목록으로 경계와 가상 출력을 표시. 셸·ping 실행 없음 |
| Linux 명령어 | Easy / Normal | `ls` 등 명령 토큰을 채점하는 가상 파일 목록 퀴즈. OS 명령 실행 없음 |
| 권한상승 기초 | Easy | 허용된 가상 명령과 사용자·파일 권한을 비교. 실제 sudo·파일·OS 권한 변경 없음. Normal은 구현 예정 |

Lens는 입력의 **어디에서, 무엇이, 왜** 달라졌는지 설명합니다. 규칙과 제한된 교육용 모형에 기반하며, 모든 공격문을 이해하는 AI 판별기나 범용 SQL·HTML·셸 해석기는 아닙니다. XSS의 태그 인식이나 랩의 성공 판정만으로 실제 브라우저 실행이 증명되지는 않습니다.

입력 전에는 정의·성립 조건·처리 단계·학습 목표를 읽고 시작할 수 있습니다. 유형별 로그인·검색·주문 조회·URL·진단·가상 터미널 문맥에서 입력하고, 같은 작업 공간의 처리·결과·Lens를 이어서 관찰합니다. Easy는 단계 안내를, Normal은 목표와 선택형 단서를 제공합니다.

## 처음 실행하기

Git과 Docker Desktop 또는 Docker Engine + Compose 플러그인이 필요합니다. Docker가 실행 중인지 확인한 뒤 저장소를 내려받습니다.

```powershell
git clone https://github.com/ts825360/-PayloadLab-.git
Set-Location -LiteralPath '.\-PayloadLab-'
docker compose up --build
```

이미 내려받았다면 `docker-compose.yml`이 있는 저장소 루트에서 마지막 명령만 실행합니다. 처음에는 이미지 다운로드와 의존성 설치 시간이 필요합니다.

| 용도 | 로컬 주소 |
| --- | --- |
| 학습 화면 | [http://127.0.0.1:5173](http://127.0.0.1:5173) |
| API 상태 확인 | [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health) — 정상 응답 `{"status":"ok"}` |
| 등록된 랩 목록 | [http://127.0.0.1:8001/labs](http://127.0.0.1:8001/labs) |
| 개발용 API 문서 | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |

Compose의 호스트 포트는 `127.0.0.1:5173`과 `127.0.0.1:8001`에 묶습니다. 컨테이너 내부 API 포트는 `8000`입니다. 이 설정은 개인 PC에서 개발하기 위한 것으로, 인터넷 공개 배포 승인을 뜻하지 않습니다.

Compose에는 컨테이너 자원 상한·권한 제한·로그 회전도 설정되어 있습니다. 로컬 Docker 실행과 제한 적용을 확인했으며, 부하 적정성과 공개 전 점검은 별개입니다. 자세한 값과 한계는 [로컬 안전 문서](docs/deployment/local-safety-and-retention.md)에 있습니다.

실행한 터미널에서 `Ctrl+C`로 중지할 수 있습니다. 별도 터미널에서 루트 기준으로 상태·로그·종료를 확인할 수도 있습니다.

```powershell
docker compose ps
docker compose logs --tail=100 -f backend frontend
docker compose down
```

`/health`는 API 응답 여부만 확인합니다. 13개 랩과 에셋은 실행 중인 Compose를 대상으로 `python scripts/verify_local_compose.py`로 추가 검사할 수 있습니다. 현재 Compose는 Vite 개발 서버와 Uvicorn 자동 재시작을 사용하는 로컬 개발 구성입니다. 운영 배포 구성이나 XSS 격리 전체의 검증을 뜻하지 않습니다.

## Docker 없이 개발하기

로컬 개발에는 Node.js 20 계열과 pnpm, Python 3.12 계열을 준비합니다. 실제 의존성은 [frontend/package.json](frontend/package.json), [pnpm-lock.yaml](frontend/pnpm-lock.yaml), [backend/requirements.txt](backend/requirements.txt)에 있습니다.

저장소 루트에서 백엔드를 시작합니다. 필요하면 먼저 본인 환경에 맞는 Python 가상환경을 사용하세요.

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```

다른 터미널에서 프론트엔드를 시작합니다. 로컬 Vite 설정의 `/api` 프록시가 `127.0.0.1:8001`로 연결합니다.

```powershell
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend dev --host 127.0.0.1 --strictPort
```

로컬 개발은 pnpm lockfile을 사용하지만 현재 프론트엔드 Dockerfile은 `npm install`을 사용합니다. 두 설치 경로의 일관성은 [배포 검토 초안](docs/deployment/security-review-issue-draft.md)에서 확인할 항목입니다.

## 검증 명령

백엔드 테스트는 `backend` 디렉터리에서 실행합니다.

```powershell
cd backend
python -m pytest -q
cd ..
```

프론트엔드 테스트·정적 빌드와 데이터 무결성 검사는 루트에서 실행합니다.

```powershell
pnpm --dir frontend test
pnpm --dir frontend build
python docs/datasets/payloads-all-the-things/test_dataset.py -v
```

의도적으로 CSV를 다시 만들 때만 `python docs/datasets/payloads-all-the-things/build_dataset.py`를 실행합니다. 데이터 검사는 형식·원문 바이트·고정 해시를 대조하며 공격 성공·교육적 라벨·AI 모델 성능을 검증하지 않습니다. 원문과 manifest, 라이선스를 함께 보존합니다.

테스트·빌드 통과, 실제 브라우저 화면 확인, Docker 실행, 공개 배포 보안 검토는 서로 다른 검증입니다. 과거 [구현 검증 기록](docs/decisions/2026-10-23-implementation-review.md)의 결과를 최신 실행 결과로 간주하지 않습니다.

## 코드와 문서 위치

| 위치 | 역할 |
| --- | --- |
| `frontend/src/` | React 학습 화면, 단계형 안내, 입력 분석, 실행 결과·시도 비교 |
| `backend/app/` | FastAPI, 랩 등록·판정, Lens·학습 추적, 더미 데이터와 제한된 모형 |
| `backend/tests/`, `frontend/src/*.test.*` | 기능·입력·화면 동작 회귀 검사 |
| `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | 로컬 개발 실행·이미지 빌드 설정 |
| `docs/` | 기획·조사·결정·회의·구조·배포 검토 기록 |
| `docs/datasets/payloads-all-the-things/` | 문자열 참고 자료 137행, 고정 원문, 출처 manifest·검사 코드·라이선스 |
| `.github/ISSUE_TEMPLATE/` | 이슈 작성 양식 |

현재 진입점과 참조 관계, 구형 UI 후보, 생성물의 구분은 [저장소 구조](docs/architecture/repository-structure.md)를 보세요. 기술 스택은 React 18·Vite 5·JavaScript, FastAPI·Pydantic·Python, SQLite, Vitest·Testing Library·pytest, Docker Compose입니다. 현재 런타임에 학습된 AI 모델이나 별도 운영 DB는 없습니다.

## 로컬 실습의 안전 범위

취약한 SQL 구성과 원본 HTML 응답은 학습을 위해 의도적으로 남겨 둔 코드입니다. 실제 개인정보·계정·토큰을 입력하지 말고, 승인되지 않은 외부 사이트·IP·계정을 대상으로 사용하지 마세요. XSS의 선택적 실행은 실제 브라우저 동작이므로 iframe sandbox만으로 네트워크·자원 위험을 모두 해결했다고 볼 수 없습니다. 서버의 SSRF 모형이 외부 요청을 하지 않는 것과 XSS 문서의 브라우저 요청 위험은 별개입니다.

학습 시도는 현재 브라우저 메모리에 최대 40개이며 새로고침하면 초기화됩니다. 테마만 `localStorage`에 남습니다. 서버 세션·영구 학습 기록·DNS 캐시는 구현되어 있지 않습니다. 자세한 근거와 로그·캐시 처리, 공개 전 검증 항목은 [로컬 안전·보관 정책](docs/deployment/local-safety-and-retention.md), [보안 검토 이슈 초안](docs/deployment/security-review-issue-draft.md)을 확인하세요.

공격 입력 CSV는 문자열 참고 자료입니다. 수식으로 해석될 수 있어 Excel에서 더블클릭으로 열지 말고 [데이터 안내](docs/datasets/payloads-all-the-things/README.md)에 따라 다룹니다.

## 팀 문서와 협업

- [이슈 목록](https://github.com/ts825360/-PayloadLab-/issues) · [이슈·운영 가이드](docs/ISSUE-GUIDE.md) · [팀 문서 안내](docs/README.md)
- [기획안](docs/planning/2026-09-07-project-brief.md) · [이번 작업의 승인 범위](docs/decisions/2026-10-23-unified-workspace.md) · [브랜드 원본 확인](docs/branding/README.md)
- [#6 안전 모델](https://github.com/ts825360/-PayloadLab-/issues/6) · [#12](https://github.com/ts825360/-PayloadLab-/issues/12) · [#24 공개 전 점검](https://github.com/ts825360/-PayloadLab-/issues/24)

기본 협업 규칙은 이슈 가이드를 따릅니다. 이번 통합 작업은 사용자가 승인한 `main` 작업 범위를 [결정 기록](docs/decisions/2026-10-23-unified-workspace.md)에 명시했습니다. 새 이슈 등록과 공개 배포는 별도 승인이 필요합니다. 외부 자료는 원문 URL·버전·활용 이유를 남기고 사실·해석·미검증 제안을 구분합니다.
