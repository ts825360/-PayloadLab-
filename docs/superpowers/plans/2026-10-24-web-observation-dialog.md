# 웹 입력/Lens와 실행 관찰창

기준 main `11c1a40`. 사용자 확인: Linux는 유지한다. 웹 1–4는 넓은 목차와 입력/Lens만 기본 화면에 놓는다. 이전 '처리 흐름을 위에 상시 배치' 해석은 이 요청으로 대체한다. 상태는 WORK-STATE가 관리한다.

1. ObservationStage의 popup 모드를 추가한다. overview는 실제 닫힘이며 DOM/레이아웃에 결과 패널을 남기지 않는다. Enter 실행의 result, Lens 위치 보기의 focus, 기록 비교의 compare에서만 body portal의 dialog를 연다. 분석만으로는 자동으로 열지 않는다.
2. Esc는 기존 닫힘 확인→Enter를 유지한다. X는 확인을 생략하고 즉시 닫는다. 닫힘은 view만 초기화하고 입력·시도·학습 단계를 보존한다. Tab은 dialog 안에 두며 원래 입력/트리거로 초점을 복구한다. 웹 배경의 sidebar/body만 inert로 두어 별도 개념 설명창이 막히지 않게 한다.
3. 닫힌 결과는 Lens 안의 '시도 기록 N' 단추로 다시 연다. 기존 시도 선택/비교 footer는 열린 창에 유지한다. 시작 전 정의/목표는 Lens 학습 안내에 넣어 다른 상시 패널을 만들지 않는다.
4. 새 web-workspace.css를 마지막으로 로드한다. 웹 전용 선택자로 761px 이상에서 목차 260px(중간 폭240px)와 이름을 표시하고, 오른쪽은 composer/lens 두 행으로 만든다. Linux 클래스/스타일은 변경하지 않는다.
5. TDD: 입력 전/분석 중 창 없음 → Enter로 실제 dialog → Esc/Enter 및 X로 DOM 제거 → 입력/초점/기록 보존 → 기록으로 재열기·비교·초점 경계·모바일을 검사한다. 기존 상시 region 전제의 테스트를 새 계약에 맞게 갱신하되 학습/백엔드 검증은 유지한다. 전체96개 기반과 신규 검사·빌드를 순차 실행한다.

파일: App.jsx, ObservationStage.jsx, InputDock.jsx, WorkspaceParts.jsx, main.jsx, web-workspace.css, web-observation.test.jsx 및 영향받는 learning-workspace/unified-workspace 테스트. 백엔드·LinuxDesktop·데이터셋은 수정하지 않는다. 실제 브라우저 제어 비활성화 시 시각 검증은 미실시로 기록한다.
