# PayloadLab

> **보안 입문자가 웹 입력의 처리 과정을 관찰하면서, 공격문이 왜 위험하고 어떤 조건에서 성공하거나 실패하는지 이해하도록 돕는 교육용 웹 학습 프로젝트**

PayloadLab은 단순히 공격 문자열을 입력하고 정답 여부만 확인하는 방식에서 벗어나, **입력 → 교육용 처리 과정 → 결과 → Lens 설명·시각화 → 재시도**의 흐름으로 학습하는 것을 목표로 합니다.

> **저장소 구분:** 현재 저장소 [`ts825360/-PayloadLab-`](https://github.com/ts825360/-PayloadLab-)는 **기획·이슈·연구 근거·데이터 초안**을 관리합니다. 실행 코드는 별도의 [`ts825360/payload-lab`](https://github.com/ts825360/payload-lab) 저장소에서 개발된 것으로 문서화되어 있습니다. 이 저장소 자체에는 웹 앱의 실행 코드와 Docker Compose 설정이 없습니다.

## 주요 학습 흐름

1. SQL Injection·Reflected XSS·IDOR 중 학습할 유형을 선택합니다.
2. 실습 난이도를 선택하고 교육용 입력을 작성합니다.
3. 서버가 입력을 어떤 코드·쿼리·권한 확인 문맥에서 처리하는지 확인합니다.
4. Lens가 **어디에서, 무엇이, 왜** 문제가 되었는지 설명합니다.
5. 처리 단계와 결과를 시각적으로 관찰한 뒤 입력을 수정해 재시도합니다.

**Lens**는 공격 문자열을 자동으로 만들어 주는 기능이 아니라, 해당 입력이 교육용 시나리오에서 갖는 의미와 부족한 조건을 설명하는 학습 보조 기능입니다. 공격처럼 보이는 문자열이 곧바로 실제 공격 성공을 의미하지는 않습니다.

## 개발 범위 및 현황

| 구분 | 범위 / 현황 |
| --- | --- |
| 핵심 학습 유형 | SQL Injection, Reflected XSS, IDOR |
| 후속 검토 | SSRF 모의 실습, Command Injection 안전 시나리오, 리눅스 명령어 퀴즈 |
| 설명·시각화 | Lens 피드백, 입력과 교육용 코드·결과의 연결 |
| 공격 입력 참고 자료 | SQLi·XSS·Command Injection·SSRF CSV 4종, 총 137행 |
| 데이터셋 성격 | **문서에서 선별한 공격 시도 101행**, 자체 정상 예시 32행, 문맥 미정 4행. **실행 검증 또는 AI 학습 완료 데이터가 아님** |
| 통합 상태 | 2026-10-23 기록 기준 구현 브랜치 검증과 기본 브랜치 통합은 별개이며, 통합 작업 [#23](https://github.com/ts825360/-PayloadLab-/issues/23)은 진행 중 |

2026-10-23 작성된 [구현 검증 기록](docs/decisions/2026-10-23-implementation-review.md)에 따르면 특정 구현 브랜치 기준 **백엔드 47개, 프론트엔드 25개 테스트**가 통과했습니다. 그러나 해당 문서는 원격 `main`과의 충돌 및 브라우저 화면 직접 검증 미완료를 명시하고 있습니다. **이 결과는 통합·운영 배포 완료를 뜻하지 않습니다.**

## 저장소와 문서 구조

```text
-PayloadLab-/                         # 이 저장소: 기획·근거·협업
├── README.md                          # 프로젝트 소개·시작 안내
├── .github/
│   └── ISSUE_TEMPLATE/               # 이슈 유형별 입력 양식
└── docs/
    ├── README.md                     # 팀 문서 작성 및 관리 규칙
    ├── ISSUE-GUIDE.md                # 이슈·브랜치·PR·검증 운영 가이드
    ├── planning-prompt.md            # 이슈 기획 프롬프트
    ├── planning/                     # 프로젝트 범위 및 역할 분담
    ├── decisions/                    # 설계 판단과 구현 검증 기록
    ├── research/                     # 유형별 연구·조사 문서
    ├── meeting-notes/                # 회의·교수님 보고 자료
    └── datasets/
        └── payloads-all-the-things/
            ├── README.md            # 데이터 목적·레이블·제약
            ├── *.csv                # SQLi·XSS·CMDi·SSRF 입력 사례
            ├── curated_samples.py   # 선별 사례와 메타데이터
            ├── sources/             # 고정 원본 Markdown 발췌
            ├── manifest.json        # 원문 위치·바이트·해시 추적
            ├── build_dataset.py     # 오프라인 CSV 재생성
            ├── test_dataset.py      # 데이터 무결성 검사
            └── LICENSE              # 원본 라이선스 고지
```

위 트리는 **이 문서 저장소의 실제 파일 배치에 근거한 요약**입니다. 구현 저장소의 상세 디렉터리 구조는 코드 접근 및 통합 이후 확인하여 별도로 기록합니다. 향후 모듈 구조 원칙은 신규 `docs/architecture/repository-structure.md` 문서로 분리해 관리하는 것을 제안합니다. **이 경로는 아직 생성되지 않은 설계안**입니다.

## 실행 방법

### 사전 준비

- Git
- Docker 및 Docker Compose 플러그인 (`docker compose` 명령 사용 가능)
- 구현 저장소에 접근할 수 있는 GitHub 권한

> **확인 상태:** 아래 명령과 URL은 현재 기획 저장소의 기존 README 및 2026-10-23 구현 검증 문서에 기재된 내용입니다. 연결된 GitHub 환경에서는 구현 저장소를 조회하지 못해 **최신 구현 브랜치의 실행 성공을 재검증하지 못했습니다.** PR 통합 뒤 구현 저장소 README 및 Compose 설정과 대조해야 합니다.

### 웹 학습 앱 실행 (구현 저장소에서)

```bash
git clone https://github.com/ts825360/payload-lab.git
cd payload-lab
docker compose up --build
```

기존 문서에 기록된 로컬 접근 주소:

| 항목 | 주소 |
| --- | --- |
| 프론트엔드 학습 화면 | http://localhost:5173 |
| 백엔드 실습 API | http://localhost:8001/labs |

컨테이너를 중지하려면 실행한 터미널에서 `Ctrl+C`를 사용하고, 별도 터미널에서 `docker compose down`을 실행합니다. 실제 서비스의 Compose 파일·환경변수·포트 매핑은 통합 후 재확인해야 합니다.

**주의:** 지금 보고 있는 `-PayloadLab-` 문서 저장소에서 `docker compose up`을 실행하는 절차가 아닙니다.

### 공격 입력 자료 재생성·검증 (이 문서 저장소에서)

Python 사용 환경에서 저장소 루트 기준:

```bash
python docs/datasets/payloads-all-the-things/build_dataset.py
python docs/datasets/payloads-all-the-things/test_dataset.py -v
```

이 검증은 CSV 형식, 원문과의 일치, 고정 해시 등을 확인합니다. **공격 유효성·라벨의 교육적 적절성·모델 성능을 검증하지는 않습니다.** CSV에 있는 문자열을 실행 환경에 자동으로 전달하지 않습니다.

## 교육용 안전 원칙

- 승인되지 않은 외부 웹사이트·IP·계정 대상 테스트는 제공하지 않습니다.
- 외부 네트워크 요청과 임의 셸 명령 실행 대신 교육용 시나리오·더미 데이터·모의 결과를 사용합니다.
- 취약한 교육용 실습을 공개 서비스로 배포하기 전에 별도의 안전성 검토가 필요합니다.
- 공격문 자료는 **문자열 데이터**로 취급합니다. CSV를 스프레드시트에서 직접 열면 수식으로 해석될 위험이 있으므로 [데이터 관리 안내](docs/datasets/payloads-all-the-things/README.md)를 먼저 확인하세요.

안전 기준: [#6 시뮬레이션 안전 모델](https://github.com/ts825360/-PayloadLab-/issues/6), [#24 공개 전 점검](https://github.com/ts825360/-PayloadLab-/issues/24).

## 기여·협업

모든 작업은 GitHub Issue에서 계획·근거·검증을 남기고, 별도 작업 브랜치와 Pull Request로 변경을 검토합니다. 외부 자료를 활용한 경우 해당 이슈에 출처를 기록하고, 연구 문서에는 원문 URL·버전·활용 근거를 연결하여 보고서와 논문에서 재사용할 수 있도록 합니다. **출처 기록 세부 운영 규칙은 별도 가이드 개정안으로 검토 중이며 현재 `main` 반영 여부를 확인해야 합니다.**

- [이슈 목록](https://github.com/ts825360/-PayloadLab-/issues)
- [이슈·운영 가이드](docs/ISSUE-GUIDE.md)
- [팀 문서 가이드](docs/README.md)
- [프로젝트 기획안](docs/planning/2026-09-07-project-brief.md)
- [2026-10-23 구현 검증 기록](docs/decisions/2026-10-23-implementation-review.md)
- [공격 입력 데이터·원문·검증 방법](docs/datasets/payloads-all-the-things/README.md)

> 문서·이슈에는 근거가 있는 사실과 미검증·검토 중인 제안을 구분합니다. 최종 지원 범위와 실행 방법은 기본 브랜치 통합 검증 결과에 따라 갱신합니다.
