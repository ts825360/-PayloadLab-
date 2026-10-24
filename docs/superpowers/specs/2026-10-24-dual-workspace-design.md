# 웹·가상 Linux 이중 작업 공간 설계

실행 상태·다음 과제는 [WORK-STATE](../../WORK-STATE.md)를 기준으로 확인한다. 이 문서는 합의한 경험과 기술 검토안을 보존하며 완료 체크를 중복 관리하지 않는다.

연결: [#7 학습 흐름 기록](https://github.com/ts825360/-PayloadLab-/issues/7), [#10 Lens](https://github.com/ts825360/-PayloadLab-/issues/10), [#13 UX 검증](https://github.com/ts825360/-PayloadLab-/issues/13), [#24 공개 안전](https://github.com/ts825360/-PayloadLab-/issues/24)

상태: 2026-10-24 사용자와 합의한 경험을 정리한 **기술 설계 검토안**. 코드 기준 main `63a6114`. 사용자 경험의 방향은 승인됐지만 아래 기술 분리·단계별 실행 계획은 검토 후 착수한다. 이 파일은 구현 완료나 공개 배포 승인이 아니다.

## 목표와 합의한 경험

- 웹 유형 1–4는 목차와 통합 학습 공간을 유지한다. 처리 흐름/결과가 위, 간결한 입력 도구와 고정 Lens가 아래다.
- 5 CMDi·6 Linux·7 권한을 고르면 Linux 바탕화면 위에 큰 터미널 창이 열린 듯한 전용 작업 공간으로 전환한다. OS 전체, 자유 창 이동·앱 설치·실제 셸은 구현하지 않는다.
- 짧고 건너뛸 수 있는 가상 환경 준비 연출을 제공한다. 같은 공간 안에서 유형을 바꿀 때 반복하지 않으며 reduced-motion에서는 즉시 진입한다. 실제 Linux/Metasploit 설치·접속으로 오인하게 표시하지 않는다.
- 로고로 웹 모드에 돌아온다. 페이지 전체 새로고침 없이 마지막 웹 유형·난이도·입력·선택한 시도·학습 단계를 복원한다. 터미널 세 유형도 서로의 입력·기록을 섞지 않는다.
- Enter 실행, Shift+Enter 줄바꿈, IME 보호를 유지한다. Esc는 현재 가장 위에 열린 설명/관찰 레이어를 처리한다. 짧은 툴팁은 닫고, 큰 관찰 장면은 확인 후 Enter로 닫는다. 입력·기록을 삭제하거나 모드를 종료하는 키로 사용하지 않는다.
- 오류 출력은 Linux 관례에 맞춘 **모의 원문**으로 제공하고 교육용 한국어 해설과 분리한다. 지원하지 않는 모형 입력을 실제 Linux의 command not found로 거짓 설명하지 않는다.
- 관련 입력/오류 구절에 밑줄, hover/focus의 짧은 설명, 해당 행의 인라인 설명, 하단 Lens의 자세한 이유/다음 행동을 연결한다. 문법·권한·미지원 상태를 아이콘·말투로도 구분한다.
- ASCII/TUI는 시작 배너뿐 아니라 사용자→소유자/권한→허용/거부를 시각화한다. 기본 명령/오류 텍스트를 복사하면 해설이 원문에 섞이지 않아야 한다. 복잡한 그림은 같은 데이터의 의미 구조와 텍스트 대체 설명을 제공한다.

## 확인한 현행 문제

- `unified-workspace.css`는 composer→processing→lens 순서이며 관찰 영역의 표시를 상시 유지한다. ObservationStage의 overview 복귀가 실제 닫힘으로 느껴지지 않는다.
- InputDock의 JS가 최소 높이 52px을 강제한다. 프롬프트는 23px/39.1px line-height, 입력은 12px/21.6px으로 실제 브라우저에서 확인했다.
- `LensInput.jsx`의 기존 밑줄/hover 코드는 현행 App에서 쓰지 않는다. 전체 입력 폭을 canvas로 재는 방식이어서 정확한 구절·여러 줄·글자 확대를 그대로 해결하지 못한다.
- PracticeEnvironment는 유형별 표지와 같은 textarea를 사용하고, PracticeSimulation은 실행 결과에만 터미널 모양과 별도 주석을 제공한다. 터미널 전체 경험이 아니다.
- 어두운 테마는 비슷한 녹색 면이 많다. 중성의 어두운 배경·입력·관찰·Lens에 밝기/경계의 위계를 설계하고 브랜드 녹색은 선택/강조에 제한한다. 기능/정보 구조는 라이트와 동일하게 유지한다.

## 구현 경계 제안

### 한 학습 엔진, 두 표시 방식

API·랩 ID·성공 판정·GuidedLesson·시도 기록을 공유하고 WebWorkspace와 LinuxDesktop은 표시/입력 방식만 다르게 둔다. 화면 컴포넌트가 각각 API나 권한 상태를 구현하지 않는다. 메모리 상태를 보기별로 보존하고 서버 세션·localStorage 학습 기록을 새로 만들지 않는다.

CMDi는 hostname을 입력하는 진단 콘솔이다. 서버에 조립되는 `ping -c 1 ...`과 결과를 구분해 보여준다. Linux/권한은 command를 입력하는 가상 터미널이다. CMDi를 임의 명령 셸로 오해시키지 않는다.

### 원문·진단·시각화 분리

원문 stdout/stderr는 기존 API가 반환한 문자열을 보존한다. 프론트 어댑터가 **알려진 상태와 실제 문자열 범위만** Diagnostic으로 연결한다. 원인을 알 수 없으면 위치를 추측해 밑줄 긋지 않고 지원 범위 안내를 표시한다.

```text
Diagnostic
  id, category, severity, title, why, next
  targets[]: {source: input|stdout|stderr, start, end, unit: codepoint}
View selection
  labId + attemptId + diagnosticId
```

범위는 원문 코드포인트 인덱스로 정의하고 JS UTF-16 offset과 혼용하지 않는다. 입력을 수정했으면 과거 출력의 진단을 새 입력 위에 표시하지 않는다. 밑줄·짧은 요약·Lens·그림은 같은 diagnostic/시도에서 선택한 정보를 소비한다.

### DOM 기반 학습 터미널 우선

검토한 대안은 (1) 기존 폼의 색만 바꾸기, (2) DOM 텍스트와 기존 입력 기술로 학습 터미널 구성, (3) xterm.js 같은 터미널 에뮬레이터다. (2)를 우선 제안한다. 단어별 설명·키보드 초점·읽기 순서를 통제하기 쉽고 범용 VT/PTY/셸이 현재 목표가 아니기 때문이다. (3)의 기능이 실제로 필요해질 때 별도 스파이크로 검토한다.

출력은 React 텍스트로 렌더링하고 raw HTML/ANSI 제어를 실행하지 않는다. 새 터미널 라이브러리는 도입하지 않는다. 입력 중 밑줄은 단일행/Shift+Enter/스크롤/한글/이모지/200% 확대를 대상으로 작은 편집면 스파이크를 먼저 한다. 직접 구현이 정합성을 만족하지 못하면 코드를 덧대지 말고 편집기 라이브러리 도입을 다시 승인받는다.

Floating UI는 현재 설치된 것을 재사용한다. hover/focus 툴팁에는 요약만 넣는다. '자세히 보기' 같은 상호작용이 필요하면 트리거 클릭으로 선택하거나 별도 popover를 사용한다. 툴팁 안에 임의 버튼을 넣지 않는다.

## 파일 책임 제안

| 경로 | 책임 |
| --- | --- |
| `frontend/src/App.jsx` | 두 모드 선택과 복귀. 기존 시나리오/교재 엔진 연결 |
| `frontend/src/useLearningWorkspace.js` | App에서 필요한 학습 상태/실행 동작을 추출할 경우의 경계. 회귀 테스트 없이 선행 대규모 리팩터링하지 않음 |
| `frontend/src/terminal/diagnostics.js` | 기존 trace→공통 진단 어댑터. 첫 스파이크 대상 |
| `frontend/src/terminal/DiagnosticText.jsx` | 원문 구절 밑줄·focus/hover 요약. 원문과 해설 DOM 구분 |
| `frontend/src/terminal/TerminalInput.jsx` | 프롬프트·IME·단축키·입력 중 진단 정렬 |
| `frontend/src/terminal/TerminalTranscript.jsx` | 시도별 명령/원문 출력과 진단. 화면 기록과 백엔드 history 재생을 분리 |
| `frontend/src/terminal/LinuxDesktop.jsx` | 준비 연출·유형 메뉴·큰 터미널 창·웹 복귀 |
| `frontend/src/terminal/TerminalConceptView.jsx` | trace/선택 진단을 사용하는 ASCII/TUI 그림과 대체 설명 |
| `frontend/src/WorkspaceParts.jsx`, `ObservationStage.jsx` | 공통 Lens/관찰 의미 유지. 선택 진단·확인 닫기 연결 |
| `frontend/src/theme-tokens.css`, `unified-workspace.css`, terminal 전용 CSS | 공통 토큰과 모드별 스타일 책임 분리. 새 덮어쓰기 층 누적 금지 |
| `backend/app/labs/practice_extensions.py` | 현재 판정/안전 경계 유지. 원문 형식/진단 추가가 필요하면 별도 테스트 후 최소 변경 |

새 파일은 제안이며 아직 생성된 실행 코드가 아니다. 구성요소 이름이 같다는 이유로 기존 기능을 무조건 교체하지 않는다.

## 단계와 검증 관문

1. **진단 계약 스파이크:** 권한 Easy의 Permission denied에서 오류 구절과 설명을 정확히 연결한다. 문자열·유니코드·미지원 입력 테스트를 먼저 한다. [실행 계획](../plans/2026-10-24-terminal-diagnostic-spike.md).
2. **권한 Easy 세로 시제품:** 큰 터미널 안에서 입력→실행→원문→밑줄→요약→하단 Lens→권한 TUI→재시도가 완결되는지 검증한다. 배경/부팅 애니메이션보다 이 체인을 먼저 완성한다.
3. **모드 전환/상태 보존:** 5–7 진입·준비 건너뛰기·로고 복귀·재진입·늦은 응답을 검사한다. 빈 화면 또는 다른 유형의 기록이 섞이면 통과하지 않는다.
4. **CMDi/Linux 확장:** 같은 터미널/진단 틀을 사용하되 입력 의미와 학습 내용은 유형별로 유지한다. 기존 Easy/Normal, 권한 Easy/Normal 예정 경계를 보존한다.
5. **웹 화면/다크 테마 복원:** 결과 위·입력/Lens 아래 배치, 간결한 입력, 실제 닫힘과 복귀, 중성 다크 위계를 검증한다. 이전 과도한 CSS 덮어쓰기 원인을 정리한다.
6. **교차 검증:** 기존 전체 테스트·빌드·13개 랩 API 외에 실제 브라우저 hover/focus/touch/IME/Esc/확대·긴 입력·좁은 화면을 검사한다. DOM 통과와 육안/브라우저 검증을 구분한다. #13의 V/W/X/Y/Z와 #22의 관련 항목에 결과를 기록한다.

## 제외 범위와 승인 경계

- 공개 배포, 실제 Linux/Metasploit 설치, SSH/PTY/WebSocket 셸, 외부 ping/HTTP/DNS, 임의 파일/OS 권한 변경은 추가하지 않는다.
- 터미널 디자인은 #24의 입력 제한·DoS·TTL·CSP 문제를 해결한 것으로 간주하지 않는다. UI 개선과 공개 전 보안 작업은 별도다.
- 이번 문서로 새 이슈·종료·브랜치·PR을 만들지 않는다. 사용자 검토 뒤 기존 이슈에 설계 결정과 변경 이유를 연결한다.

## 기술 근거

- [Floating UI Tooltip](https://floating-ui.com/docs/tooltip): hover/focus, 충돌 회피, Esc, 비상호작용 툴팁 규칙을 검토했다. 코드 예제를 그대로 도입한 것은 아니다.
- [xterm.js 문서](https://xtermjs.org/docs/): 범용 터미널 시퀀스·버퍼·파서·장식 인터페이스를 제공하는 대안으로 검토했다. 도입하지 않았다.
- CodeMirror 공식 예제는 이번 조회에서 403으로 열리지 않았다. 확인하지 못한 예제의 지원 범위를 근거로 라이브러리 도입을 확정하지 않았다.
