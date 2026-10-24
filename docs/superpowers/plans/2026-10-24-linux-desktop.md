# 전체 Linux 작업 공간 실행 계획

기준 main `6560bcb`. 기존 이중 작업 공간 설계와 2026-10-24 사용자 재확인에 따라 실행한다. 기존 UX-02~04를 반복하지 않고 실제 화면 전환과 정렬 문제를 우선 해결한다. 상태는 WORK-STATE에서만 관리한다. 이 계획은 현재 세션에서 직접 실행하며 새 에이전트·브랜치·의존성을 추가하지 않는다.

## 결과와 경계

- 5–7번 진입: 웹 레이아웃을 전용 Linux 바탕화면/큰 터미널 창으로 교체한다. 짧은 준비 연출은 건너뛰기 가능하며 내부 유형 전환 때 반복하지 않는다. reduced-motion이면 즉시 열린다.
- 터미널 창: 누적 원문 → 네이티브 명령 입력 → 하단 고정 Lens. 옆 관찰 면은 같은 trace로 ASCII/TUI를 표시한다. 기존 InputDock/GuidedLesson/TerminalInput/TerminalTranscript/API를 재사용한다.
- Easy에서 시작한다. 권한은 현재 Easy의 서버 허용 명령 전체만 처리한다. 기존 SQL/XSS/IDOR/SSRF/CMDi/Linux의 Easy/Normal API와 데이터는 제거하지 않고 권한 Normal 예정 상태를 유지한다. 실제 셸/네트워크는 추가하지 않는다.
- 로고/창 닫기로 마지막 웹 입력·선택 시도·난이도·학습 단계를 복구한다. 터미널 유형별 초안/단계도 메모리에서 분리한다. 늦은 실행 응답은 다른 화면을 덮지 않는다.
- 실행 후 새 프롬프트를 비우되 응답 대기 중 사용자가 새로 쓴 초안은 지우지 않는다. 지난 원문은 기록에 남고 같은 시도의 Lens/관찰로 연결된다.
- Esc는 설명/확대 관찰을 우선 처리한다. 확대 관찰은 기존 확인→Enter로 닫으며 Linux 모드를 임의 종료하지 않는다.

## 1. 웹 입력 정렬 원인 수정

파일: InputDock.jsx, unified-workspace.css, input-shortcuts.test.jsx. 현재 prompt 23px + 중앙 정렬, textarea 첫 줄 12px/21.6px + JS 최소52px가 서로 다른 기준선이다. 프롬프트를 ASCII `>`로 바꾸고 같은 13px/24px 글꼴·상단 정렬·0 내부 패딩으로 통일한다. textarea 높이는 24~96px로 맞춘다. 한 줄/한글/여러 줄/Enter 회귀 검사 후 반영한다.

## 2. 전체 화면 전환·상태 복원

파일: App.jsx, terminal/LinuxDesktop.jsx, terminal/linux-desktop.css, terminal/linux-desktop.test.jsx. App만 API/학습 상태를 소유하며 renderDock(onFocus)로 기존 입력/Lens를 공급한다. LinuxDesktop은 표시·준비 연출·관찰 확대만 소유한다. App의 lab별 스냅샷에는 input/claim/viewId/view/stepIndex/acknowledged/stepAfterAttempt/activeGroup을 저장한다. 웹↔Linux/터미널 내부 전환만 복원하고 기존 웹 유형 전환의 동작은 유지한다.

검사: 5/6/7 진입, 큰 작업 공간/웹 레이아웃 제거, 준비 건너뛰기·내부 재연출 방지·reduced-motion, 로고의 웹 초안/단계 복원, 유형별 초안 분리, 늦은 응답 무시, 입력 대기 중 새 초안 보존. 컴포넌트 테스트에서 먼저 실패를 확인한다.

## 3. 터미널/TUI 연결

파일: terminal/TerminalInspector.jsx·테스트, TerminalTranscript.jsx, InputDock.jsx, WorkspaceParts.jsx. 관찰은 trace의 identity/files/execution/simulation/composition만 읽고 성공/실행을 추측하지 않는다. CMDi는 hostname 입력과 조립된 명령을 구분한다. 서버가 주는 supported_commands를 표시하고 선택은 입력만 채운다. 권한 거부의 밑줄·요약·하단 Lens를 기존 진단으로 연결한다.

검사 명령: `docker compose exec -T frontend npm test -- --reporter=dot --maxWorkers=1 --minWorkers=1 --testTimeout=15000` 이후 `docker compose exec -T frontend npm run build`를 순차 실행한다. 실제 API에서 허용 명령과 미지원 상태를 확인한다. Work 브라우저 제어가 비활성화돼 있으면 시각·IME·확대 검증은 대기로 기록하고 통과를 주장하지 않는다.

참고: 사용자가 제시한 https://www.igloo.inc/ 는 이번 텍스트 조회에서 본문 0줄이며 브라우저 제어도 비활성화되어 현재 전환을 직접 관찰하지 못했다. 사용자와 기존에 합의한 '장면 전체 전환'을 구현 근거로 삼고 Igloo의 실제 효과·코드·에셋을 복제했다고 표현하지 않는다.
