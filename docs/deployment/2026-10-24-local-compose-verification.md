# 로컬 Docker 실행·브랜드 파일화 검증

연결: [#7](https://github.com/ts825360/-PayloadLab-/issues/7), [#24](https://github.com/ts825360/-PayloadLab-/issues/24), [통합 학습 공간 결정](../decisions/2026-10-23-unified-workspace.md)

기준: main의 `e10884e` 이후 후속 변경, 2026-10-24. **공개 배포 검증이 아니다.**

## 실행 결과

Docker Desktop Linux 엔진 29.4.3, Compose 5.1.3에서 기존 Compose 파일로 검증했다.

| 검사 | 실제 결과 |
| --- | --- |
| `docker compose up --build -d` | Python 3.12-slim / Node 20-slim 기반 두 이미지 빌드·기동 성공 |
| 기존 포트 충돌 | 이전에 실행한 PayloadLab 로컬 프로세스의 명령과 PID를 확인하고 해당 두 프로세스만 종료해 해결 |
| `docker compose down` → `docker compose up -d` | 해당 프로젝트 컨테이너·네트워크 제거 후 재생성 성공. 이미지·소스는 보존 |
| 컨테이너 내부 Vitest | 12개 파일, **54개 테스트 통과** |
| 컨테이너 내부 Vite build | 종료 코드 0 |
| `python scripts/verify_local_compose.py` | 아래 HTTP 스모크 검사 전부 통과. 재기동 후에도 재실행해 통과 |

스모크 검사는 실행 중인 localhost만 대상으로 하며, 외부 주소의 실제 요청·셸·권한상승을 수행하지 않는다.

- `/health`, 등록된 13개 랩의 정확한 ID 집합
- 13개 `/analyze`에서 결과 실행값이 아직 없다는 계약
- 13개 `/attempt`의 유형별 예상 결과
- 권한 Normal 미등록(404), 가상 helper 이후 더미 보고서 읽기
- 프론트엔드 HTTP 200과 라이트·다크 SVG 응답의 XML/비활성 에셋 형태

## 실제 적용 확인

`docker inspect`의 HostConfig에서 다음 값을 확인했다. 제한의 **적용 확인**이며 부하 적정성·격리 완전성 인증은 아니다.

| 항목 | backend | frontend |
| --- | --- | --- |
| 호스트 바인딩 | `127.0.0.1:8001` | `127.0.0.1:5173` |
| 메모리 | 268435456 bytes (256 MiB) | 805306368 bytes (768 MiB) |
| NanoCpus / PID 상한 | 1000000000 (1 CPU) / 64 | 1000000000 (1 CPU) / 128 |
| 추가 권한 / capability | no-new-privileges / ALL 제거 | no-new-privileges / ALL 제거 |
| 로그 | json-file, 10m × 최대 3개 | json-file, 10m × 최대 3개 |

## 재검증 명령

저장소 루트에서 Docker가 실행 중일 때:

```powershell
docker compose up --build -d
python scripts/verify_local_compose.py
docker compose exec -T frontend npm test -- --reporter=dot --maxWorkers=2 --minWorkers=1
docker compose exec -T frontend npm run build
docker compose ps
```

초기 기동 직후 API 준비가 끝나지 않았다면 `docker compose logs --tail=50 backend frontend`에서 준비 상태를 확인한 뒤 스모크 검사를 실행한다. 스크립트는 기본 포트 8001·5173에서 실행 중인 서비스를 검사하므로 먼저 Compose 프로젝트·포트 소유자를 확인한다.

## 브랜드와 남은 경계

사용자가 기존 문자 브랜드의 파일화를 승인해 라이트·다크 SVG를 공통 에셋으로 추가했다. 웹 UI는 수동 테마 선택, README는 배경 테마에 따라 같은 파일을 사용한다. 좁은 사이드바에서는 같은 SVG의 `p·` 부분만 보이도록 잘라 표시한다. 검토에서 발견된 로고 넘침에 대해 회귀 테스트가 먼저 실패하는 것을 확인하고 CSS를 보완했다. 별도 새 로고를 디자인한 것이 아니다. [브랜드 기록](../branding/README.md).

이번에는 Work 설정에서 로컬 브라우저 사용이 비활성화되어 새 SVG를 웹 화면에서 직접 육안 검증하지 못했다. SVG 응답·구문 및 UI 테마별 경로 테스트는 통과했다. 이전 통합 화면의 브라우저 검증과 이번 Docker/에셋 검증을 구분한다.

외부 PC 접근 차단 실험, XSS의 직접 렌더 경로·CSP·브라우저 외부 요청, 운영 인증·TLS·부하·취약점 점검은 이 검사로 완료되지 않는다. [공개 전 검토 초안](security-review-issue-draft.md)은 유지하고, 공개 배포는 사용자와 별도로 논의한다. 현재 컨테이너는 로컬 실습용으로 켜 둔다.
