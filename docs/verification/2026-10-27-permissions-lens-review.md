# #19 권한 Easy 설명·진단 연결 검토 — 2026-10-27

관련: [#19](https://github.com/ts825360/-PayloadLab-/issues/19), [공통 문안 기준](../research/lens-feedback-template.md), [이전 통합 검토](2026-10-27-lens-narrative-review.md).
담당: 이수웅(dtd2428), AI 보조. 기준: 작업 브랜치의 9b43f5727f4eac693bb37254173d05d2be4c23f9 이후 로컬 변경.
상태: 코드·자동 검사·아래 실제 화면 대조 완료. 본인·팀의 최종 문안 검토는 대기. 검증 당시에는 미커밋·미push였고 이슈 체크나 종료는 하지 않았다. 이후 사용자의 진행 승인으로 이 기록을 포함하는 커밋을 같은 브랜치에 공유한다. 커밋은 git log로, 전송 결과는 원격 브랜치와의 일치로 확인한다.

## 범위와 불변식

기존 가상 권한 모형과 허용 명령을 유지하고, 명령별 입력→기록에서 복원한 가상 사용자→파일·규칙→모의 출력→다음 관찰을 연결했다.
실제 sudo·셸·파일 조회·OS 권한 변경은 추가하지 않았다. 기록은 허용 명령 최대40개·총2000자 범위에서 재생하는 기존 모형이며 실제 인증 세션이 아니다.
도우미 실행만으로 실습을 완료하지 않는다. 기존 목표는 가상 root 상태에서 report.txt를 읽는 것이다.
권한 Normal은 실제 화면과 등록 상태 모두 구현 예정으로 유지한다.

## 기존 문제·개선·확인 결과

| 사례 | 기존 문제 | 개선 설명·표시 | 기대/실제 결과 |
| --- | --- | --- | --- |
| whoami / id / pwd | 어떤 명령에도 report.txt의 거부 이유를 공통 표시 | 해당 명령이 보여준 가상 사용자·그룹 번호·폴더와 실제 stdout 연결. 파일 읽기나 사용자 변경을 했다고 말하지 않음 | student/root, uid/gid, /lab의 고정 모의 출력 |
| ls / ls -l /lab/report.txt | 목록 조회와 파일 내용 읽기 설명이 구분되지 않음 | -l의 역할과 권한·소유자·경로의 간략한 목록을 설명. 파일 내용을 읽은 것이 아니라고 명시 | command_ok, 기존 목록 stdout 유지 |
| student의 cat /lab/report.txt | 오류 원문과 일반 안내만으로 사용자·소유자·권한의 연결이 부족 | student와 소유자 mentor가 다르고 -rw-------(0600)에 다른 사용자 읽기가 없음을 설명. stdout 부재와 stderr의 거부 안내 구분 | permission_denied. 원문 cat: /lab/report.txt: Permission denied 유지 |
| cat /lab/readme.txt | 읽기 가능한 파일에도 report.txt의 거부 이유를 설명 | 실제 대상 readme.txt·소유자 student·-rw-r--r--·virtual lab readme 출력 연결. graph의 파일 정보도 대상에 맞춤 | command_ok. student는 소유자, root는 모형의 root 읽기 규칙으로 통과 |
| sudo -l | 허용 목록 조회와 사용자 전환 구분 부족 | NOPASSWD와 /lab/maintenance가 가상 허용 규칙임을 풀이하고 아직 사용자가 바뀌지 않았다고 설명 | student 유지, 기존 규칙 stdout |
| sudo /lab/maintenance | 항상 같은 일반 설명, 실제 OS 관리자 획득으로 오해 가능 | student→root라는 가상 변화와 아직 파일을 읽지 않았음을 설명. 이미 root이면 root 유지라고 설명 | elevated. 도우미 단독은 실습 목표 미충족 |
| root의 cat /lab/report.txt | root 읽기 성공에도 student 거부 이유가 보임 | 파일 소유자·권한은 그대로이고 모형의 root 규칙으로 training-report를 표시했다고 설명 | command_ok, 실습 목표 충족 |
| exit | Lens가 명령 의미를 설명하지 않고 TUI는 이전 root만 보여줌 | root→student 복귀를 설명하고 TUI에도 표시. 이미 student이면 유지. 실제 프로세스 종료가 아님 | command_ok, 가상 student |
| 빈/미지원 명령·잘못된 history | 권한 거부와 지원 범위 안내가 섞일 수 있음 | 빈 값·허용 목록 밖·기록 미재생을 구분. 실제 Linux 명령의 존재 여부를 단정하지 않음 | unsupported, stdout 없음. 잘못된 기록은 일부만 재생하지 않고 시작 사용자 유지 |
| 실행 전 분석 | 현재 명령의 역할·출력과 구분이 부족 | 이전 기록으로 복원한 사용자만 설명하고 현재 명령은 아직 처리하지 않았음을 명시 | execution=None, 현재 명령으로 root 전환/파일 읽기/exit가 발생하지 않음 |

[9개 대표 사례의 기존/개선 문안·전체 trace·분석 결과](2026-10-27-permissions-review-cases.json).
[재생성 스크립트](scripts/permissions_review_cases.py)는 경로 함수를 직접 호출한다. HTTP나 실제 셸·브라우저 실행 결과가 아니다.

## 실제 화면 대조

로컬 Vite5173/API8001에서 다음 순서로 AI가 화면을 조작했다.

1. whoami → student 출력과 Lens의 현재 사용자 일치.
2. ls -l /lab/report.txt → mentor·-rw-------·경로 목록과 설명 일치.
3. cat /lab/report.txt → 원문 거부와 Lens·TUI의 student/mentor/읽기 권한 원인 일치.
4. cat /lab/readme.txt → 읽기 가능한 파일의 내용과 설명 일치.
5. sudo -l → 규칙만 표시하고 student 유지.
6. sudo /lab/maintenance → 가상 root 전환, whoami → root 확인.
7. cat /lab/report.txt → training-report와 모형의 읽기 허용 설명 확인.
8. exit → Lens의 student 복귀와 TUI의 root→student 표시, whoami → student 확인.
9. 다시 cat /lab/report.txt → 같은 파일이 다시 거부됨.
10. 도우미 입력의 실행 전 분석에서 student 유지·출력 미생성 확인.
11. Normal 선택 시 ‘구현 예정’ 안내·실행 불가 상태 확인.

Permission denied의 밑줄은 현재 시도의 오류 구절을 가리킨다. 입력창에서 실제 Shift+Tab으로 이동해 오류 구절에 키보드 초점을 주었을 때 사용자·소유자·읽기 권한을 설명하는 툴팁이 나타났고 Lens와 TUI의 원인도 일치했다.
처음 프로그램 방식의 초점 이동에서 툴팁이 안 보이는 경우를 조사했고, 기존 useFocus의 키보드 초점 방식으로 다시 확인했다. 진단 UI를 임의로 고치지 않았다.
**실제 마우스 hover·터치·확대 비율별 동작을 이번 검사에서 모두 확인한 것은 아니다.** 기존 진단의 자동 검사와 이 키보드 경로의 실제 대조를 구분한다.

화면: [읽기 거부·밑줄 초점 설명·Lens·TUI](assets/2026-10-27-permissions-denied-lens.png), [가상 root 읽기 성공](assets/2026-10-27-permissions-root-read.png).
확인한 브라우저 경고·오류 로그는 없었다. 실제 초보자 참여 시험·학습 효과는 별도다.

## 자동 검사와 시행착오

- 새 권한 설명 검사26개를 먼저 실행해 실패 확인 후 명령별 설명을 수정했다.
- 기존 모형 검사와 합쳐76개 통과. 최종 백엔드 전체 **224개 통과**.
- exit 후 TUI에 root→student가 없다는 프론트 회귀 검사1개 실패 확인 후 표시 조건을 수정했다. 최종 프론트 **19파일109개 통과**.
- pnpm build **성공, 488모듈**.
- 실제 화면에서 거부 툴팁이 길게 표시되어 사용자·소유자·권한·모의 경계에 집중한 짧은 문구로 교정하고 백엔드 전체를 다시 확인했다.
- 9개 대표 사례의 상태·사용자·실습 목표·실행 전 분석을 대조했다.
- 기존 성공 판정·허용 명령·기록 상한·권한 Normal 등록 여부는 변경하지 않았다.

검사 원문: [백엔드](evidence/2026-10-27-permissions-backend-tests.txt), [프론트](evidence/2026-10-27-permissions-frontend-tests.txt), [빌드](evidence/2026-10-27-permissions-frontend-build.txt).
코드: backend/app/labs/practice_extensions.py, frontend/src/terminal/TerminalInspector.jsx.
회귀 검사: backend/tests/test_permissions_lens_narrative.py, frontend/src/terminal/TerminalInspector.test.jsx.

재현:

    cd backend
    python -m pytest -q
    cd ../frontend
    pnpm test --maxWorkers=1 --minWorkers=1
    pnpm build
    cd ..
    python docs/verification/scripts/permissions_review_cases.py
    git diff --check

## 남은 범위

본인·팀의 문안 최종 검토, 전체13개 학습 흐름과 터미널의 남은 입력/조작 방식 대조, CSV 교육 범위 확인은 남아 있다.
이 기록으로 #19 전체 체크나 종료, 실제 권한상승 검증·공개 보안 승인을 하지 않는다. 사용자의 후속 진행 승인에 따라 이번 변경 commit/push를 진행한다. 본인·팀의 교육 문안 최종 검토 완료를 의미하지 않는다.


## 2차 검증 — 2026-10-27

사용자 요청으로 변경 코드·회귀 검사·실제 화면을 다시 확인했다. 이 검증 시점에는 미커밋·미push였다. 이후 공유 단계의 사용자 승인은 상단 상태에 기록했다.

발견: 앞뒤 공백을 제외해 명령을 처리한다는 안내를 why에 추가했지만, 읽기 거부 분기에서 why를 교체해 안내가 사라졌다. 일반 공백과 전각 공백 U+3000의 회귀 검사2개가 먼저 실패했다. 이 안내를 what의 입력 설명으로 옮겨 원문·공백 제외·처리 명령·거부 이유의 순서가 유지되게 수정했다. 짧은 거부 툴팁과 실행 규칙은 그대로다.

- 최종 백엔드 전체 **226개 통과**. [이번 실행 로그](evidence/2026-10-27-permissions-second-backend-tests.txt).
- TerminalInspector 관련 프론트 **7개 통과**. [이번 실행 로그](evidence/2026-10-27-permissions-second-frontend-tests.txt). 전체109개와 빌드는 위 1차 검증 결과이며 이번에는 프론트 코드가 바뀌지 않아 전체 검사·빌드를 반복하지 않았다.
- 기준 커밋9b43f57과 **1,088개 조합** 대조: 17개 명령(허용13개와 빈 값·미지원·이모지·복합 입력) × 8개 기록 × 4개 공백 형식 × 분석/실행. 출력·사용자·원문/조립문·phase·실행 시 목표 판정 동일. focus 범위와 payload 비변경 확인. 40/41개 기록·잘못된 기록 포함. [결과와 검사 범위](evidence/2026-10-27-permissions-second-matrix.txt). 직접 함수 호출이며 실제 OS 실행 검사가 아니다.
- 실제 화면에서 일반/전각 공백의 거부 설명, readme 읽기 성공, ls /etc 미지원, 도우미 전환, root의 report 읽기, exit의 root→student 표시, 이후 report 재거부를 대조했다.
- 실제 Shift+Tab 초점으로 Permission denied의 짧은 설명과 Lens의 원인 일치를 재확인했다. 확인한 브라우저 경고·오류 로그는 없었다.
- [2차 검증 화면](assets/2026-10-27-permissions-second-review.png). 캡처는 당시 좁은 화면의 보이는 영역이며 오른쪽 관찰 패널 전체 가독성·모든 화면 크기/확대 비율 검증을 의미하지 않는다.

현재 검증한 범위에서 남은 검사 실패는 없다. 실제 마우스 hover·터치·확대별 동작, 본인·팀 최종 검토, 전체13개 흐름·CSV 범위 확인은 별도로 남는다.
