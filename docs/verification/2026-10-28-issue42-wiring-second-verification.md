# #42 통합 연결2차 검증 — 2026-10-28

개인 브랜치 dtd2428/issue-42-input-sql, main기준 `64c9cb141108cafa5c6d215fc9eb4981c100b9b7`+미커밋 변경. Windows/Python3.13.2/SQLite3.45.3. [검사한 소스해시](evidence/2026-10-28-issue42-wiring-second-source-hashes.json).

## 재현한 공통 원인

앱을 `/api`로 mount하면 Starlette 라우터는 root_path를 제외한 경로로 처리하지만, 제한 모듈은 `/api/labs/...` 전체 path를 정규식과 비교했다. 동일 원인으로3개 보호가 빠지는 것을 각각 재현했다.

| 입력/경로 | 수정 전 | 기대·수정 후 |
| --- | --- | --- |
| /api SQL analyze에2001자 | 200 | 입력가드422 |
| /api SQL attempt에 시험정책이 금지한 sqlite_version() | 성공True | successFalse·blocked |
| /api render2000자·시험응답cap1024bytes | 200 | 응답가드503·response_limit |

[수정 전3실패/11통과](evidence/2026-10-28-issue42-wiring-second-before.txt). 외부 서버 공격이나 파일 접근을 하지 않았으며 기본앱에 정책이 적용됐다는 증거가 아니다.

## 수정

공통 lab_paths.lab_route에서 ASGI root_path와 일치하는 경로 세그먼트 접두사만 제거한다. 입력·SQL context·응답 가드가 같은 경로 해석을 사용한다. 이미 접두사가 제거된 ASGI path도 유지하며 `/api2`에서 `/api`를 잘못 떼지 않는다. 임의 경로 normalize나 새 라우트를 추가하지 않는다.

## 재검증

- 루트/접두사 포함/이미 제거/중첩 mount/비슷한 prefix/앱 루트 등6개 경로 경계 확인.
- 앞선 통합11개+재현3개+경로6개+추가 실제HTTP2개=통합22개 통과.
- 실제Uvicorn 테스트 앱을 `/api`, `/limited-api`, 루트에 각각 mount하여 입력거부→SQL연산차단→정상조회 복구와 응답503을 실제TCP HTTP로 확인. 종료 시 서버/소켓 정리.
- 실제HTTP21개 포함 main기준 백엔드 전체236개 통과, 경고 없음. [최종 실제 로그](evidence/2026-10-28-issue42-wiring-second-after.txt). 명령:venv Python `-m pytest backend/tests -q`, git diff --check 통과.
- 요청별 예산/실패 상태 분리·trace중단 뒤 성공 정정·SQL단위/기존학습 회귀도 전체 검사에 포함. SQL실행기 자체는 이번 수정에서 변경하지 않아 별도60사례 재측정은 반복하지 않았다.

## 남은 상태

기본app.main.app의 정책은 비활성이고 팀 수치/authorizer 승인은 대기다. 검토앱의 통합 경로 검증 결과를 실제 운영환경·브라우저·공개승인으로 확대하지 않는다. #19브랜치/PR 수정 없음. 커밋·푸시·PR/main반영·#42 종료 없음.
