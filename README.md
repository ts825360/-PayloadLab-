# PayloadLab

> 보안을 처음 배우는 사람이 입력을 바꿔 보면서 **왜 성공하거나 실패했는지** 이해하는 웹 보안 학습 프로젝트입니다.

## 먼저 알아둘 점

이 저장소는 PayloadLab의 **기획·자료조사·의사결정·팀 협업 문서**를 관리하는 공간입니다. 여기에는 Docker 설정이나 실행 코드가 없으므로, 이 저장소를 내려받은 뒤 `docker compose up`을 실행하면 안 됩니다.

실제 프로토타입 코드는 [payload-lab 구현 저장소](https://github.com/ts825360/payload-lab)에 있습니다.

## 무엇을 만들고 있나요?

보안 입문자는 실습 환경을 설치하는 것부터 어렵고, 예시 문장을 입력해 성공해도 “왜 됐는지” 이해하기 어렵습니다. PayloadLab은 아래 흐름으로 이 문제를 풀려고 합니다.

유형 선택 → 난이도 선택 → 입력 → 결과 확인 → Lens 설명 또는 다이어그램 → 수정해서 다시 시도

**Lens**는 사용자가 입력한 내용이 교육용 코드나 쿼리의 어디에 들어갔는지, 무엇이 부족한지, 왜 필요한지를 알려 주는 돋보기입니다.

자세한 기획은 [프로젝트 한눈에 보기](docs/planning/2026-09-07-project-brief.md)에서 확인할 수 있습니다.

## 현재 단계

현재는 핵심 학습 흐름을 보여 주는 **프로토타입을 확인하고 기획을 구체화하는 단계**입니다.

- 첫 번째 중심 유형: SQL Injection, Reflected XSS, IDOR
- 이후 검토할 후보: SSRF 교육용 모의 시나리오, 리눅스 명령어 빈칸 퀴즈
- 각 유형의 설명 문장, 난이도, 안전 기준, 확장 범위는 팀 이슈에서 계속 검토합니다.

## 프로토타입 실행과 로컬 주소

프로토타입을 실행하려면 [구현 저장소](https://github.com/ts825360/payload-lab)를 내려받은 뒤 그 저장소에서 실행합니다.

```bash
git clone https://github.com/ts825360/payload-lab.git
cd payload-lab
docker compose up --build
```

현재 확인된 로컬 주소는 아래와 같습니다.

| 용도 | 주소 |
| --- | --- |
| 학습 화면 | [http://localhost:5173](http://localhost:5173) |
| 백엔드 API | [http://localhost:8001/labs](http://localhost:8001/labs) |

> 위 주소는 **구현 저장소를 내려받아 Docker를 실행한 현재 컴퓨터에서만** 열립니다. 이 문서 저장소만으로는 실행되지 않습니다.

## 안전 안내

프로토타입에는 보안 학습을 위해 의도적으로 취약한 교육용 처리 흐름이 포함됩니다. 반드시 개인의 로컬 Docker 환경에서만 사용하고, 외부 네트워크나 공개 서버에 배포하지 않습니다. 실제 서비스나 타인의 시스템을 대상으로 입력을 시도해서도 안 됩니다.

프로젝트의 기능별 안전 기준과 공개 전 점검은 [안전 모델 이슈](https://github.com/ts825360/-PayloadLab-/issues/6)와 [공개 전 점검 이슈](https://github.com/ts825360/-PayloadLab-/issues/24)에서 관리합니다.

## 팀은 어떻게 작업하나요?

| 남기는 내용 | 위치 |
| --- | --- |
| 기획서, 자료조사, 결정 기록, 회의 결과 | [docs/](docs/README.md) |
| 의견 제안, 질문, 작업 배정, 진행 상황 | [GitHub Issues](https://github.com/ts825360/-PayloadLab-/issues) |
| 코드·문서·디자인 변경 | Pull Request |

팀은 **격주 수요일**에 열린 이슈와 Pull Request를 함께 검토하고, 토의로 확정한 결과를 `docs/decisions/`와 이슈 댓글에 기록합니다.

새 팀원은 다음 순서로 시작하면 됩니다.

1. [프로젝트 한눈에 보기](docs/planning/2026-09-07-project-brief.md)를 읽습니다.
2. [GitHub 운영 가이드](https://github.com/ts825360/-PayloadLab-/issues/1)를 읽습니다.
3. 본인에게 맡겨진 이슈 하나를 선택하고 댓글에 계획을 남깁니다.

## 주요 문서

- [프로젝트 한눈에 보기](docs/planning/2026-09-07-project-brief.md)
- [역할 분담 초안](docs/planning/2026-09-07-role-assignment.md)
- [주간·격주 진행 보고 기준](docs/meeting-notes/2026-09-07-progress-reporting-workflow.md)
- [기획안 평가와 보완 기록](docs/decisions/2026-09-07-project-review.md)
- [팀 문서 작성 규칙](docs/README.md)
- [이슈 기획 프롬프트](docs/issue-planning-prompt.md)
