# #42 실제 화면 연결 검증 — 2026-10-28

브랜치 dtd2428/issue-42-input-sql, main64c9cb1+미커밋 변경. [검사한 파일 해시](evidence/2026-10-28-issue42-ui-source-hashes.json). 기존 #19 브랜치와 기본 app.main.app 정책은 보존했다. #6/#24 재조회 결과 팀 답변 없음.

## 실행 환경과 재현 방법

- `docs/verification/scripts/issue42_review_server.py --acknowledge-unapproved-policy --port 8102`: 측정 제안값을 명시적으로 읽는 loopback 검토 전용 앱. 숫자/함수 허용목록이 팀 승인을 받았다는 뜻이 아니다. localhost 외 host 설정은 제공하지 않는다.
- frontend에서 `pnpm exec vite --config vite.issue42-review.config.js`:127.0.0.1:5174를8102 검토 API로 연결. 기존 기본 Vite설정/8001포트를 바꾸지 않았다.
- 기존 venv Python3.13.2/SQLite3.45.3, 프론트 Vite5.4.21. Codex IAB의 실제 클릭·입력으로 확인. backend 세션46689, frontend 세션38912는 사용자 검토를 위해 실행 중. 서버 종료/재개 시 본인이 만든 세션만 조작한다.

## 발견한 오류와 수정

실제 UI에서 제한 결과는 table=None인데 ExecutionCanvas가 DataTable.columns를 읽어 React가 빈 화면으로 중단됐다. [실제 console 오류](evidence/2026-10-28-issue42-ui-error-before.json). 제한/연산 차단은 조건 불충족의0행 결과가 아니므로 빈 테이블을 꾸미지 않고, SQL 처리 중단 전용 안내를 표시하도록 수정했다.

- 자원 제한/연산 차단에서 table 없이 제목·이유·다음 관찰을 표시.
- 자원 제한 상태 라벨 추가. 정상 조회로 바뀌면 기존 테이블/조건 그림으로 복구.
- API의413·422·response_limit503은 구별된 고정 안내. 서버 detail/내부 경로를 그대로 보여주지 않고, 그 밖의 오류는 기존 일반 실패 문구 유지.
- 새 테스트 JSX의 괄호 오타1개도 첫 검사에서 발견해 교정했다. 이 테스트 작성 오류를 제품 버그로 세지 않는다. [첫 검사 로그](evidence/2026-10-28-issue42-ui-before.txt)에는 해당 collection오류와 기존 일반오류 문구에 대한5개 실패가 있다. 화면 중단 자체는 실제 브라우저로 먼저 재현했다.

## 실제 화면 결과

1. Easy에 작은 재귀SQL 입력 →VM한도에서 중단. [자원 제한 화면](assets/2026-10-28-issue42-resource-limit.png). 문법오류/조건불충족과 다름을 안내, 계정 표/성공 결과 없음.
2. 같은 앱에서 일반 OR 학습 입력 실행 →2개 계정과 조건 그림 복구. [정상 복구 화면](assets/2026-10-28-issue42-recovered-query.png).
3. 시험 authorizer가 허용하지 않은 sqlite_version() 입력 →연산범위 차단 안내. [차단 화면](assets/2026-10-28-issue42-operation-blocked.png). SQLite 버전 함수가 본질적으로 위험하다고 주장하지 않으며 실제 과목 허용목록은 팀에서 결정한다.
4. 수정 후 위 세조작에서 새 console error0개. [기록](evidence/2026-10-28-issue42-ui-errors-after.json). 실제 브라우저 입력/클릭으로 확인했지만 모든 기기/브라우저·터치/확대·전유형 검증은 아니다.

## 자동 검사

- 새 회귀9개:자원/연산차단 렌더, 정상 테이블 복구, API입력·본문·응답 크기 안내와 일반 오류의 detail 비노출.
- 프론트21파일109개 전체 통과. [실제 로그](evidence/2026-10-28-issue42-ui-tests.txt). 명령:`pnpm --dir frontend exec vitest run --maxWorkers=2 --minWorkers=1`.
- 빌드487모듈 성공. [빌드 로그](evidence/2026-10-28-issue42-ui-build.txt). 명령:`pnpm --dir frontend build`.
- 백엔드 실행 모듈은 이번 UI수정에서 바꾸지 않았다. 직전 전체236개/HTTP21통과 근거는 [통합2차검증](2026-10-28-issue42-wiring-second-verification.md)으로 유지하며 이번에 재실행했다고 쓰지 않는다.
- git diff --check 통과.

## 남은 일

팀의 수치·보수적 작업예산 단위·SQL 허용목록 검토, 변경 내용 사용자 검토와 공유, 기본앱 정책 활성화, 운영환경 확인과 최종 PR/main반영이 남는다. #19 main반영 시 공통 코드 재대조 필요. 이번에 기본앱 정책 활성화·commit/push·PR게시·#42 종료는 하지 않았다.
