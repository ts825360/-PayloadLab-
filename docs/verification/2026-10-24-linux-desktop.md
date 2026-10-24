# 전체 Linux 화면 전환과 입력 정렬 검증

2026-10-24, 착수 기준 main `6560bcb`. 사용자가 작은 터미널 입력면과 실제 장면 전환의 차이를 재확인해 UX-06과 UX-09 정렬을 우선 진행했다. 최신 상태는 [WORK-STATE](../WORK-STATE.md), 절차는 [실행 계획](../superpowers/plans/2026-10-24-linux-desktop.md)에 있다.

## 실제 변경

- 5 CMDi·6 Linux·7 권한 선택 시 기존 웹 레이아웃을 LinuxDesktop으로 교체한다. 중성 어두운 바탕화면, 큰 터미널 창, 짧은 준비 연출/건너뛰기, 내부 유형 탭을 추가했다. reduced-motion에서는 준비를 생략한다.
- 창 안에 누적 원문 기록·다음 명령 입력·고정 하단 Lens·ASCII/TUI 관찰 면을 연결했다. 기존 InputDock/GuidedLesson/TerminalInput/TerminalTranscript/API를 재사용하며 새 명령 실행 엔진은 만들지 않았다.
- 권한 관찰은 같은 trace의 실행 전 사용자·파일 소유자/권한·결과를 표시한다. 분석을 실행 성공/실패로 꾸미지 않는다. CMDi는 hostname 입력과 서버가 조립한 명령을 구분한다.
- 로고/닫기로 마지막 웹 유형·난이도·입력·선택 시도·학습 단계를 복구한다. 터미널 유형별 초안도 메모리 스냅샷으로 분리한다. 재접속/영구 학습 기록은 추가하지 않았다.
- 실행한 명령은 기록에 남고 입력은 다음 프롬프트로 비운다. 응답 대기 중 새로 작성한 초안은 지우지 않는다. 이전 모드의 늦은 응답은 무시한다.
- 오류 선택 시 Lens에 초점을 주면서 해당 입력 설명도 연다. 확대 관찰의 Esc는 기존 확인→Enter로 닫으며 Linux 모드를 임의 종료하지 않는다.
- 웹 입력의 기호를 ASCII `>`로 바꾸고 기호/입력을 동일한 13px/24px 줄·상단 정렬에 배치했다. JS 최소 높이 52px과 기호 23px/입력 12px의 불일치를 제거했다. 웹 그리드도 처리/결과 → 입력 → 하단 Lens 순서로 수정했다.

## 자동 검사와 실제 로컬 API

- Red: 5–7 전체 Linux 영역 부재 3개, 기호/최소 높이 회귀 실패, Inspector 미구현을 확인했다.
- Green: 신규 전체 전환 8개·관찰 3개·웹 정렬 1개와 기존 검사. 최초 전체 실행은 94/96이었으며, 실행 후 빈 프롬프트라는 새 계약으로 기존 입력 범위 검사를 조정했다. Lens는 오류 선택 뒤에도 학습 안내가 남을 수 있어 직접 재현 검사를 추가하고 trace별 탭 선택/초점 전환을 수정했다.
- **최종 전체 프론트: 18개 파일·96개 테스트 통과.** 기존 13개 랩의 안내, 지원 Normal과 권한 Normal 예정 상태, 키보드/IME DOM 이벤트, 원문 보존 검사를 유지했다.
- **Vite build: 488개 모듈, 종료 코드 0.** 전체 검사 종료 후 순차 실행했다.
- Docker가 종료되어 첫 Docker 검사는 엔진 연결에 실패했다. 공식 설치된 Docker Desktop을 시작하고 기존 Compose를 `up -d --no-build`로 복구했다. 초기 Red는 호스트의 기존 Node/Vitest로 확인했고 최종 전체 검사/빌드는 실제 Docker에서 수행했다. 자원 제한·포트 공개 설정은 변경하지 않았다.
- 실제 권한 Easy API의 `supported_commands` **13개 전부**를 요청해 모형에서 지원되는 상태로 처리됨을 확인했다: whoami, id, pwd, ls, ls /lab, ls -l /lab, ls /lab/report.txt, ls -l /lab/report.txt, cat /lab/report.txt, cat /lab/readme.txt, sudo -l, sudo /lab/maintenance, exit. 파일 읽기 거부와 가상 관리자 전환은 기대되는 결과이며 미지원 실패로 처리하지 않았다.
- `uname -a`는 모형 미지원 상태를 유지했다. 이것이 실제 Linux에 없는 명령이라는 뜻은 아니다. 프론트와 LinuxDesktop 모듈은 HTTP 200을 확인했다.

검사 명령:

```powershell
docker compose exec -T frontend npm test -- --reporter=dot --maxWorkers=1 --minWorkers=1 --testTimeout=15000
docker compose exec -T frontend npm run build
```

## 아직 확인하지 못한 것

Work 설정의 로컬 브라우저 제어가 비활성화되어 실제 전환 애니메이션·픽셀 기준선·200% 확대·복사·실제 IME 키보드·작은 뷰포트 스크롤은 직접 검증하지 못했다. DOM 검사/빌드/HTTP 200을 육안 확인으로 보고하지 않는다. #13과 관련 기능 검증 이슈를 종료하지 않는다.

사용자가 제시한 Igloo 페이지는 텍스트 도구에 본문이 없어 실제 전환을 관찰했다고 주장하지 않는다. 합의한 '전체 장면 전환'을 구현했으며 해당 사이트의 에셋/코드/효과를 복제하지 않았다.

웹 전반의 다크 테마 재설계·사용자 학습 평가·공개 전 보안 정책/조치는 남아 있다. 실제 셸/설치/외부 네트워크/호스트 권한 변경·공개 배포를 추가하지 않았다.
