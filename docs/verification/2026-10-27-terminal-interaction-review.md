# #19 터미널 조작·작은 화면 검토 — 2026-10-27

관련: [#19](https://github.com/ts825360/-PayloadLab-/issues/19), [전체13개 흐름](2026-10-27-learning-flow-review.md).
기준 코드: 71c4daa6f600ab176c15f9472e8b3cddaaa1a653 이후 로컬 변경. 담당: 이수웅(dtd2428), AI 보조.

## 결과와 실제 검증 범위

작은 화면 입력 폭과 Lens 탭 줄바꿈 문제를 수정했다. 현재 도구로 가능한 클릭·키보드·4개 viewport 대조와 관련 자동 검사·빌드는 통과했다. **실제 마우스 hover·실기기 터치·브라우저200% 확대는 미검증**이다. 이 항목 전체나 #19 전체를 완료 체크하지 않는다. 검증 시점에는 미커밋·미push였다. 이후 사용자의 요청으로 이 기록을 포함해 로컬 commit하며 push는 하지 않는다.

| 항목 | 실제 화면 | 자동 검사 / 한계 |
| --- | --- | --- |
| 키보드 초점·Escape | 4개 viewport에서 진단 툴팁·원인 확인, Escape 뒤 툴팁 닫힘·터미널 유지 | 기존 Escape 전파 차단 검사 통과 |
| 밑줄 클릭→Lens | student·mentor·읽기 거부 설명 연결 확인 | 같은 진단 객체 선택·원문 보존 검사 통과 |
| 순수 마우스 hover | 미검증 | mouseEnter 표시·mouseLeave 닫힘을 DOM 이벤트 자동 검사로 확인. 실제 마우스 이동 검사가 아님 |
| 실제 터치·길게 누르기 | 미검증 | touch/pointer 이벤트 후 click으로 같은 진단을 1회 선택하는 DOM 검사. 실기기·터치 브라우저 검사가 아님 |
| 실제 브라우저200% 확대 | 미검증 | Control++ 전후 viewport·DPR·visual scale에 변화가 없어 적용되지 않음. Control+0도 보냈으며 확대 성공으로 세지 않음 |
| 작은 화면 | 1280×900, 640×450, 390×844, 320×568 확인 | 640×450를200% 확대의 대체 증거로 쓰지 않음 |

IAB의 제공된 Playwright API에는 hover·touch 입력 메서드가 없고, viewport capability는 크기만 설정한다. 읽기 전용 DOM 평가로 이벤트를 주입하거나 CSS 확대를 실제 브라우저 확대처럼 기록하지 않았다. 실제 입력으로 검증 가능한 항목과 자동 이벤트 모형을 구분한다. 검사 후 viewport override를 reset해 기본 화면 크기로 복원했다.

## 발견·최소 수정

320px 화면에서 프롬프트와 실행 버튼 사이의 실제 입력 폭이 약19.9px였다. cat /lab/report.txt를 입력하면 높이144px 안에서 내용 높이가260px로 감겨, 짧은 명령도 읽기 어려웠다. 작은 화면에서 Lens 선택 버튼의 글자도 세로로 쪼개졌다.

linux-desktop.css의600px 이하 규칙만 보완했다. 터미널의 기존 모바일 줄바꿈을 복원해 프롬프트 다음 줄에 입력이 놓이게 하고, Lens 제목 줄은 줄바꿈을 허용하되 탭 글자는 한 줄로 유지했다. 입력 UI·허용 명령·권한 판정·학습 단계·테마·API는 새로 설계하지 않았다. 320px에서 입력 폭이157.9px로 늘고 같은 짧은 명령이26px 한 줄에 표시됐다.

[수정 전320px 화면](assets/2026-10-27-terminal-narrow-before.png), [수정 후320px 화면](assets/2026-10-27-terminal-narrow-after.png), [390px 진단·입력·Lens](assets/2026-10-27-terminal-mobile-diagnostic.png).

## 실제 측정과 대조

| viewport | 수정 후 입력 폭 | 예시 입력 높이 | 툴팁 위치 | stderr |
| --- | --- | --- | --- | --- |
| 1280×900 | 521.0px | 26px | 화면 안 | 원문 유지 |
| 640×450 | 330.9px | 26px | 화면 안 | 원문 유지 |
| 390×844 | 228.3px | 26px | 화면 안 | 원문 유지 |
| 320×568 | 157.9px | 26px | 화면 안 | 원문 유지 |

네 크기에서 tooltip은 viewport 안에 있고, 페이지 전체의 가로 넘침은 없었다. 원문은 cat: /lab/report.txt: Permission denied 뒤 개행까지 동일했다. 터미널 기록 내부의 스크롤은 별도로 존재하므로 ‘모든 내부 스크롤이 없다’는 뜻은 아니다. 390px 최종 화면에서도 진단 클릭과 키보드 초점 설명이 같은 원인을 가리켰다.

CMDi Easy/Normal과 Linux Easy/Normal은390×844·320×568에서 각각 실제 입력·실행·최신 기록을 확인했다. 총8회 추가 실행 모두 입력 폭228.3/157.9px, 페이지 가로 넘침 없음, 실행 버튼 유지였다. CMDi는 조립 명령과 모의 출력, Linux는 목록·권한/소유자 출력이 유지됐다. 현재 밑줄 진단은 권한의 알려진 Permission denied에만 제공되므로 CMDi/Linux에도 같은 진단 밑줄이 있다고 기록하지 않는다.

[전체 전후 측정·화면 텍스트·추가 실행·확대 시도](evidence/2026-10-27-terminal-interaction-browser.json). 브라우저 경고·오류 로그는 없었다.

## 자동 검사

관련 프론트 **6파일41개 통과**: DiagnosticText9(hover 떠나기·터치 형태 활성화2개 추가), diagnostics10, TerminalInput5, TerminalTranscript5, linux-desktop8, unified-workspace4.
[이번 실행 로그](evidence/2026-10-27-terminal-interaction-tests.txt).

최종 CSS 보완 뒤 빌드 **성공·488모듈**. [이번 빌드 로그](evidence/2026-10-27-terminal-interaction-build.txt).
이전 단계의 전체 프론트110개·백엔드226개를 이번에 다시 실행한 것으로 세지 않는다. 이번에는 백엔드·실행 판정 코드를 변경하지 않았다. 새 CSS의 실제 검증 근거는 위 viewport 측정·화면 대조다.

재현:

    cd frontend
    pnpm test src/terminal/DiagnosticText.test.jsx src/terminal/diagnostics.test.js src/terminal/TerminalInput.test.jsx src/terminal/TerminalTranscript.test.jsx src/terminal/linux-desktop.test.jsx src/unified-workspace.test.jsx --maxWorkers=1 --minWorkers=1
    pnpm build

## 남은 일

실제 마우스 이동으로 hover 표시/이탈, 실기기 터치로 Lens 연결·바깥 누르기·길게 누르기, 실제 브라우저200% 확대에서 입력·툴팁·Lens 재대조가 필요하다. 현재 도구 미지원 항목을 완료로 바꾸지 않았다. CSV 원본·라벨·manifest와 교육 범위, 본인·팀 최종 문안 검토도 별도로 남아 있다. 추가 commit/push는 사용자 요청 뒤 진행한다.


## 2차 검증 — 2026-10-27

화면 크기를 바꾸기 전에 입력을 비우던1차 방식에서 벗어나, 같은 긴 초안을 그대로 둔 축소·복원·경계 폭을 확인했다.

발견: TerminalInput의 자동 높이 계산이 value가 바뀔 때만 실행돼,1280px에서320px로 좁혀도 높이가78px로 남았다. 내용 높이는208px여서 새 폭에 맞춘144px 상한을 쓰지 못했다. 실제 화면에서 재현했고 새 회귀 검사1개도26px/144px 불일치로 먼저 실패했다.

수정: 기존 높이·밑줄 스크롤 동기화 함수를 window resize에도 연결했다. 계산식26~144px는 유지하고 컴포넌트 갱신/해제 때 리스너를 정리한다. 값·명령·입력 길이·실행 기준은 변경하지 않았다. 새 회귀 검사는 폭 변경에 해당하는 내용 높이 변화 후144px 상한,52px로 축소, 값 보존, 리스너 정리를 확인한다.

### 실제 화면 재대조

- 긴 초안을 바꾸지 않고1280→320→1280으로 전환했을 때 입력 높이가78→144→78px로 바뀌었다. 입력과 장식 mirror의 크기가 일치했다.
- 600/601/760/761px 요청 폭도 추가 확인했다. 브라우저가601/761을 실제602/762 CSS px로 반영한 표본은 요청값과 실제 viewport 값을 함께 저장했다. 문서 가로폭은 실제 viewport와 같았고 입력 손실은 없었다.
- 한글·이모지·개행200줄(UTF-16 길이1000) 초안을 실행하지 않고 입력했다. 높이144px 제한과 값 보존, 실제 키보드 스크롤 이후 textarea/mirror scrollTop 일치를 확인했다. 하단 이동 뒤5082.4px, 상단 이동 표본3.2px에서 두 값이 같았다. 스크롤 애니메이션 직후0을 읽은 초기 표본을 실제 이동 완료로 세지 않고 후속 관측을 별도로 기록했다.
- 편집 중 이전 Permission denied는 현재 Lens를 바꾸는 버튼이 아닌 설명용 항목으로 남았다. 키보드 초점으로 이전 오류 툴팁을 확인하고 Enter를 눌러도 현재 초안은 바뀌지 않았다. 기존 stderr도 보존됐다.
- 브라우저 경고·오류 로그는 없었다. 임시 viewport override는 기본값으로 복원했다.

[전후 크기·경계 폭·긴 입력·스크롤 측정](evidence/2026-10-27-terminal-second-browser.json), [좁은 화면의 긴 입력](assets/2026-10-27-terminal-second-resize.png).

최종 프론트 **19파일113개 통과**, 빌드 **성공·488모듈**. [이번 전체 검사](evidence/2026-10-27-terminal-second-tests.txt), [이번 빌드](evidence/2026-10-27-terminal-second-build.txt).
백엔드 코드는 바꾸지 않아 이전226개를 이번에 재실행한 것으로 기록하지 않는다.

현재 수행한 검사에서 남은 실패는 없다. **실제 순수 마우스 hover·실기기 터치·실제200% 확대는 여전히 미검증**이며 이2차 검사로 대체하지 않는다. 이 검증 시점에는 미커밋·미push였으며 이후 사용자 요청으로 로컬 commit한다. push와 사용자·팀 최종 검토는 별도다.
