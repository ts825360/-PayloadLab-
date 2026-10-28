# #42 UI 안내2차 검증 — 2026-10-28

main64c9cb1 기반 개인브랜치 dtd2428/issue-42-input-sql+미커밋 변경. [파일 해시](evidence/2026-10-28-issue42-ui-second-source-hashes.json). 기본앱 정책 미활성, 커밋/푸시 없음.

## 재현과 수정

API수준의 문구 검사는 통과했지만 화면까지 전달되지 않는2곳을 발견했다.

- App의 실행 catch가 알려진413/422/response_limit503까지 서버 연결 오류로 바꿨다.
- 자동분석 hook이 오류 문구를 버리고 Lens는 대기 안내로 돌아갔다.

[수정 전5실패/2통과](evidence/2026-10-28-issue42-ui-second-before.txt): 실행3상태·App분석1·hook1에서 재현. 이를5개의 독립제품버그로 세지 않는다.

API가 고정한 안전한 문구만 LabRequestError로 구분해 App에 전달한다. 알 수 없는 네트워크/서버 상세 예외는 기존 일반 연결 안내로 유지하며 내부경로를 그대로 출력하지 않는다. hook도 안전한 분석문구를 유지하고 App→InputDock→Lens에 전달한다. Lens는 분석 중단 상태와 문구를 표시하고 입력이 바뀌면 이전 분석오류를 지운다. 실행 재시도 시 기존 alert를 지우고 정상 결과로 복귀한다.

422안내는 숫자의 허용범위도 포함하도록 '입력 형식·길이·값이 실습 허용 범위를 벗어났습니다'로 정정했다. 사용자 값이나 상세 예외를 그대로 반사하지 않는 고정 문구다.

## 실제 화면과 자동검사

- 실제 IAB에서 IDOR 주문번호9007199254740992(2^53)를 입력했다. 검토용 정책의 정확한 JS정수 허용범위를 넘으므로 분석422안내가 Lens에 표시됨. [분석 화면](assets/2026-10-28-issue42-analysis-input-limit.png).
- 실행 버튼에서도 같은 입력범위 안내가 표시되며 연결 오류로 바뀌지 않음. [실행 화면](assets/2026-10-28-issue42-attempt-input-limit.png).
- 1042로 수정 후 본인 주문 표·소유자 연결 복구. [정상 복구](assets/2026-10-28-issue42-idor-recovery.png). 추가console error0개 [기록](evidence/2026-10-28-issue42-ui-second-browser-errors.json).
- 413/503의 실제 브라우저 재현까지 했다는 뜻은 아니다. 그 두 상태는 fetch모의→실제App 렌더→재시도 복구 검사로 대조했고, 실제HTTP 바이트 상한은 앞선 backend검증에 있다.
- 신규6개:App의413/422/503 문구와 정상재시도3개, 분석안내App1개, hook문구유지/새입력초기화1개, 예상밖네트워크예외 비노출1개.
- 프론트22파일115개 전체통과. [최종 로그](evidence/2026-10-28-issue42-ui-second-tests.txt). 명령:`pnpm --dir frontend exec vitest run --maxWorkers=2 --minWorkers=1`.
- 빌드487모듈 성공. [빌드 로그](evidence/2026-10-28-issue42-ui-second-build.txt). git diff --check 통과.
- backend실행 코드는 이번에 바꾸지 않아 전체236개/HTTP21의 직전 근거를 유지하며 재실행으로 기록하지 않는다.

## 미완료

팀의 제한값/작업예산 의미/SQL authorizer 검토, 기본앱 정책활성화·운영환경 검증과 PR/main반영은 여전히 미완료다. 이 결과는 전유형·기기·브라우저·터치/확대 전체검증이 아니다. 검토서버8102/5174는 사용자 확인용으로 유지했다. #19 PR이나 기본정책을 바꾸거나 커밋/푸시하지 않았다.
