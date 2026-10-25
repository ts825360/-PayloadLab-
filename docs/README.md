# PayloadLab 팀 문서

**수정 작업을 재개한다면 [작업 상태](WORK-STATE.md)를 먼저 확인합니다.** 마지막 완료 작업·다음 작업 ID·검사 결과를 한곳에 관리하며, 전체 이슈/채팅을 매번 다시 읽지 않습니다.

**현재 구현 마감 후 팀원은 [작업 인계 안내](planning/2026-10-25-team-handoff.md)와 [#46](https://github.com/ts825360/-PayloadLab-/issues/46)에서 맡을 이슈를 고릅니다.** 해당 이슈의 Assignee로 본인을 지정하고 본인 커밋·PR·검증 결과를 남깁니다.

최종 공개 배포·배포 후 확인·운영/복구 인계는 [#47](https://github.com/ts825360/-PayloadLab-/issues/47)에서 맡습니다. 보안/기능 검증과 사용자 공개 승인 후 진행하며, 현재는 배포 준비·인계 단계입니다.

이 폴더는 팀이 합의한 기획, 자료조사, 의사결정, 회의 기록을 저장하는 공용 공간입니다. 이슈는 **할 일과 논의**, `docs`는 **다시 참고해야 할 근거와 결과물**을 담당합니다.

처음 참여한 팀원은 먼저 [프로젝트 한눈에 보기](planning/2026-09-07-project-brief.md)를 읽고, 맡은 이슈와 관련된 문서만 추가로 읽습니다. 모든 이슈를 처음부터 읽을 필요는 없습니다.

현재 실행 코드는 이 저장소의 `frontend/`와 `backend/`에 함께 있습니다. 시작 명령은 [루트 README](../README.md), 현재 코드의 연결은 [저장소 구조](architecture/repository-structure.md)를 기준으로 확인합니다. 과거 결정·회의 문서의 별도 구현 저장소 설명과 검증 수치는 당시 기록으로 보존합니다.

## 팀 운영 방식

- 모든 기획서·조사 자료·결정 기록·회의 결과는 `docs/`에 저장합니다.
- 의견 제안, 질문, 작업 배정, 진행 상황은 GitHub Issue에서 남깁니다.
- 공통 기준은 `main`입니다. 총괄·AI 보조 작업은 사용자 승인 범위에서 검증 후 main에 커밋하고, 팀원 개인 브랜치의 작업은 Pull Request로 올려 검토합니다. 자세한 기준은 [이슈·운영 가이드](ISSUE-GUIDE.md)를 따릅니다.
- 팀은 **격주 수요일**에 모여 열린 이슈와 Pull Request를 검토하고, 어떤 결과물을 확정할지 토의합니다.
- 확정한 내용은 `docs/decisions/` 문서와 관련 이슈 댓글에 함께 기록합니다.

## 폴더 구조

| 위치 | 저장할 내용 |
| --- | --- |
| `docs/planning/` | 기획 의도, 범위, 사용자 흐름, 발표용 핵심 정리 |
| `docs/research/` | SQL Injection·XSS·IDOR·SSRF 등 유형별 조사 자료와 학습 시나리오 |
| [현재 저장소 구조](architecture/repository-structure.md) | 실행 진입점·API 연결, 구형 UI 검토 후보, 소스·생성물 구분 |
| [로컬 안전·보관 정책](deployment/local-safety-and-retention.md) | 실제 실행/모형 경계, 상태 수명·로그·캐시, 공개 전 검증 |
| [로컬 Docker 실행 기록](deployment/2026-10-24-local-compose-verification.md) | 이미지 빌드·기동·재시작, 13개 랩 API와 컨테이너 제한 적용 확인 |
| [공개 배포 전 1차 점검](deployment/2026-10-24-public-readiness-review.md) | 현재 공개 보류 판단, 실제 코드/응답·의존성 경고, 우선 수정 사항 |
| [A–Z 검증 체크리스트](verification/2026-10-24-release-checklist.md) | 기능·보안·사용자 편의성의 시험 방법·통과 기준·자문 항목과 결과 양식 |
| [이슈 완료 기준 재확인](decisions/2026-10-24-issue-completion-review.md) | 완료로 종료할 항목과 열어 둘 항목의 근거 |
| [보안 검토 이슈 초안](deployment/security-review-issue-draft.md) | 기존 제안과 근거. 현재 팀 작업은 #42~#46 및 #6·#12·#24에서 진행 |
| [브랜드 에셋·승인 기록](branding/README.md) | 승인된 문자 브랜드 SVG와 정식 원본 교체 시 확인할 사항 |
| [공격 입력 데이터 초안](datasets/payloads-all-the-things/README.md) | SQLi·XSS·CMDi·SSRF 공통 CSV, 원문 근거·정상 예시·라벨 검토 기준 |
| `docs/decisions/` | 팀이 확정한 범위, 안전 원칙, UX, 기술 선택의 결정 기록 |
| `docs/meeting-notes/` | 회의 안건, 합의 내용, 다음 행동 |
| `docs/meeting-notes/professor-status-report-template.md` | 교수님께 제출할 한 장짜리 상태 보고 템플릿 |
| `docs/planning-prompt.md` | 이슈 초안을 만들 때 사용하는 공용 프롬프트 |
| `docs/ISSUE-GUIDE.md` | 이슈 작성, 브랜치, Pull Request, 검증 기록의 공용 규칙 |
| `docs/decisions/2026-09-07-project-review.md` | 현재 기획안을 평가하고 보완한 기록 |
| `docs/planning/2026-09-07-role-assignment.md` | 총괄이 역할 댓글을 확인한 뒤 반영하는 역할 분담 현황 |
| `docs/meeting-notes/2026-09-07-progress-reporting-workflow.md` | GitHub 기록으로 교수님 보고를 정리하는 기준 |

## 작성 규칙

1. 파일명은 `YYYY-MM-DD-주제.md` 형식을 사용합니다. 예: `2026-09-07-sqli-learning-scenario.md`
2. 문서 첫 부분에는 연결된 이슈 번호 또는 Pull Request 링크를 적습니다. 연결할 항목이 없다면 `연결 이슈: 없음`으로 표시합니다.
3. 조사 문서에는 출처 링크와, 그 출처를 PayloadLab 학습 시나리오에 적용한 해석을 구분해 적습니다.
4. 결정 문서에는 선택지, 선택한 이유, 제외한 이유, 후속 작업을 짧게 남깁니다.
5. 코드 또는 문서를 변경한 Pull Request에는 변경한 `docs/` 경로를 설명에 적습니다.
6. 다른 팀원이 이미 작성한 문서는 삭제·대체하지 말고, 필요한 경우 새 문서에서 연결하거나 Pull Request로 수정합니다.

## 새 문서를 추가하는 순서

1. 관련 이슈를 열거나 기존 이슈를 찾습니다.
2. 위 폴더 중 문서 성격에 맞는 위치에 Markdown 파일을 만듭니다.
3. 이슈 댓글에 문서 링크와 핵심 결론을 남깁니다.
4. 문서 변경은 브랜치와 Pull Request로 검토한 뒤 반영합니다.

> 이 폴더에는 팀이 재사용할 수 있는 문서만 저장합니다. 계정 정보, API 키, 실제 대상의 취약점 정보, 개인 정보는 기록하지 않습니다.
