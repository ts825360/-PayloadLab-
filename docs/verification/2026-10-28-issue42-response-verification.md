# #42 전체 응답 크기 제한 — 2026-10-28

## 기준과 범위

HEAD `714a7412f6d638a297de33a07e37ff6f2027e720` + 미커밋 #42 파일. 사용자 요청으로 전체 응답 제한 모듈을 추가했다. #6/#24 댓글 재조회 결과 팀 승인 답변은 없으며, production app/main.py·기존 SQL 호출부에는 연결하지 않았다.

## 구현

`backend/app/core/response_limits.py`의 ResponseGuard는 값을 주입받아 analyze/attempt/render의 실제 응답 bytes를 누적한다. Content-Length를 신뢰해 상한 검사를 생략하지 않는다. 최대 버퍼 이상은 복사하기 전에 중단하고 성공 헤더/부분 결과를 내보내지 않는다.

- 초과 시 HTTP503·code=response_limit·고정 안내 JSON. 요청 크기 초과413과 구분하는 검토용 동작이며 최종 팀 정책 미승인.
- 원래 응답 헤더/부분 데이터는 버리고 이미 계산된 CORS/Vary 정보만 보존한다. 정상 버퍼 응답의 Content-Length를 실제 길이에 맞추고 Transfer-Encoding을 제거한다.
- 스트리밍 초과 시 생성 작업을 종료한다. Starlette/AnyIO의 ExceptionGroup 안에 든 초과 예외도 처리하지만 다른 예외는 숨기지 않는다.
- HEAD/204/304의 Content-Length 의미와 관련 없는 경로의 응답을 임의 변경하지 않는다. 현재 수업 경로는 일반 JSON/HTML 응답이다.

이 가드는 이미 상위 핸들러가 할당한 큰 데이터/직렬화 비용까지 막지는 못한다. 실제 SQL 결과 크기 제한과 함께 연결해야 한다. 압축·응답 trailers·파일 zero-copy 같은 새 ASGI 응답 방식은 별도 호환성 검토가 필요하며 검증하지 않았다. 스트림은 제한된 범위에서 전체 버퍼 후 내보내므로 SSE·장시간 스트리밍용 정책이 아니다.

## 실제 검증

- 모듈 검증8개:1023/1024/1025bytes, 잘못된 Content-Length와 실제 누적, CORS 보존/내부 헤더 폐기, 부분 성공 비노출, 스트림 중단·정리, 다른 경로 보존, 관련 없는 예외 비은폐, 고정 오류조차 담지 못하는 정책 거부.
- 정상 응답 헤더 대조를 추가하면서 잘못된 길이 헤더가 그대로 전달되는2개 실패를 확인하고 실제 버퍼 길이로 재계산하도록 수정했다.
- 기존 loopback HTTP 테스트 앱에 입력+응답 가드를 함께 설치했다. production 앱이 아니다. 테스트 전용 응답 probe에서262143/262144/262145bytes →200/200/503 확인.
- 제한 응답 이후 같은 HTTPConnection 객체로 정상 SQL 요청200·성공 판정 복구 확인. 기존 입력HTTP13개도 유지했다.
- 응답8+실제HTTP17=관련25개 통과. 기존 포함 **백엔드326개 통과**, 경고 없음. [전체 로그](evidence/2026-10-28-issue42-response-backend-tests.txt). venv Python `-m pytest backend/tests -q`, git diff --check 통과.

## 다음

팀의 제한값/SQL 허용 연산 검토 후 #19와 분리한 개인 브랜치 범위에서 실제 app 및 SQL resolve/trace/EXPLAIN/상수비교를 연결한다. 새 보수적 VM 계산으로 수업 사례 여유를 재측정하고 제한 상태를 Lens/UI 설명과 연결해야 한다. 정책 팀 승인·제품 보호 완료·main 반영·commit/push·PR·#42 종료는 아직 아니다.
