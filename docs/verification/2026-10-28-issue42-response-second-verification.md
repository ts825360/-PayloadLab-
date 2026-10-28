# #42 응답 제한 2차 검증 — 2026-10-28

기준 HEAD `714a7412f6d638a297de33a07e37ff6f2027e720` + 미커밋 #42 초안. Windows/Python3.13.2/SQLite3.45.3. production 연결·정책 팀 승인 없음. 커밋·푸시 없음.

## 재현·수정

[수정 전 로그](evidence/2026-10-28-issue42-response-second-before.txt):4실패/9통과. 4실패는 다음3종류 결함이며 연결 종료는 직접 ASGI와 실제 Starlette 스트리밍 두 경로에서 재현했다.

| 조건 | 수정 전 | 수정 후 |
| --- | --- | --- |
| more_body=True인 채 downstream이 종료 | 버퍼의 일부를 완료된200응답으로 변환 | 응답 완료 이벤트를 추적하고 미완료면 내부 오류로 전달. 성공 헤더/일부 데이터 전송 없음 |
| response.start 중복 | 두번째 시작으로 기존 정보를 덮어씀 | 시작/본문/완료 순서를 검사해 잘못된 메시지를 오류로 처리 |
| 클라이언트 http.disconnect를 관측한 뒤 앱 종료 | 버퍼를200으로 전송 시도 | receive를 감싸 연결 종료 관측 시 버퍼를 폐기하고 전송하지 않음. 스트리밍 생성기 finally 정리 확인 |

연결 종료 감지는 앱이 receive에서 실제 disconnect를 관측한 경우다. 네트워크가 끊기는 모든 순간을 미리 감지한다고 주장하지 않는다. 불완전 응답 오류는 사이즈 초과503으로 잘못 분류하지 않고 기존 서버 오류 처리로 전달한다.

테스트용 ASGI Client도 개선했다. 이전에는 요청 본문 전달 직후 http.disconnect를 반환해 살아있는 연결까지 종료한 것으로 모의했다. 이제 실제 종료 시험을 제외한 일반 요청은 연결을 유지하고 Starlette가 완료 시 수신 대기를 취소한다. 실제TCP HTTP 검사는 별도 유지했다.

## 검증

- 응답 모듈17개 통과: 앞선8개+불완전/잘못된 응답 순서3개+직접/Starlette disconnect2개+UTF-8 이모지255/256/257개(1020/1024/1028bytes)3개+초과 예외와 내부 오류가 섞인 ExceptionGroup1개.
- 사이즈 초과에 unrelated 내부 오류가 섞이면 단순 초과로 숨기지 않는지 확인.
- 실제loopback HTTP17개와 기존 입력/SQL/Lens 회귀를 포함한 **백엔드335개 통과**, 경고 없음.
- [최종 실제 로그](evidence/2026-10-28-issue42-response-second-after.txt). 명령: 작업 venv Python `-m pytest backend/tests -q`. git diff --check 통과.

제품 연결·main 기준 재검증·SQL과 학습 설명 통합·정책 팀 승인·commit/push/PR/#42종료는 여전히 미완료다. 테스트 앱의 검증을 현재 제품의 보호 완료라고 표시하지 않는다.
