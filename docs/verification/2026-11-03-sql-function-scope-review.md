# SQL 함수 현황과 검토 방향 — 2026-11-03

## 1. 문제와 결정 출처
이수웅이 전달한 태성님의 직접 테스트 후 검토 방향을 기록한다. 기존 시험 정책을 최종 학습 정책으로 오해하지 않도록 함수별 용도와 실제 적용 위치를 구분한다. 이 문서는 허용 목록이나 제한값을 확정하지 않는다.

## 2. 유지할 학습 동작과 보류 범위
- Lens는 현재 구현 유지. Easy 직접 힌트 강화, 짧은 설명/자세히 보기 분리, UNION 해설 확장을 추가 진행하지 않는다.
- SQL은 정해진 공격 원리를 배우는 범위로 제한하며 일반 SQL 함수 연습장으로 확장하지 않는다.
- 박태성·admin·빈 입력과 잘못된 구문도 관찰 대상이다. 공격문만 통과시키는 입력 필터를 만들지 않는다.
- 최종 지원 범위 밖 연산은 ‘이 실습에서 지원하지 않는 연산’으로 안내하고, 실제 문법 오류·조건 불충족과 구분해야 한다.
- 구체적 함수/연산 목록과 수치 제한은 미확정. 확정 전 기본 서비스 정책 적용 금지.
- #44 요청량·동시 이용 정책은 이번 검토에서 보류. 기존 스파이크를 삭제하거나 기본 서비스에 활성화하지 않는다. 이전 N/A/B 선택 요청은 현재 적용 승인 요청으로 진행하지 않는다.

## 3. 전후 예시 — 이번에는 제품 변경 없음
현재 기본 앱과 기존 검토 앱을 각각 호출해 차이를 확인했다. 아래는 개선 전후가 아니라 적용 위치별 현재 동작이다.

| 입력/상황 | 기본 앱 | 기존 검토 앱 | 이번 결정 |
| --- | --- | --- | --- |
| 박태성·admin·빈 값 | 조건 불충족/0행 설명 | 동일 | 일반 입력도 계속 받는다 |
| admin 뒤 따옴표 하나, OR가 빠진 문장 | syntax_error | 동일 | 문법 오류 설명 유지 |
| OR 참 조건+주석 | 행 반환/성공 | 동일 | 핵심 원리 유지 |
| Normal 대문자 OR 제거/혼합 대소문자 | 변형 후 오류/우회 성공 | 동일 | 원본과 사용값 비교 유지 |
| length/printf/sum을 사용한 작은 UNION | 행 반환 | 행 반환 | 함수 필요성을 검토한 뒤 결정 |
| sqlite_version()을 사용한 UNION | 행 반환 | blocked, operation_blocked | 기존 검토 앱의 차단 사례이며 최종 금지 목록 아님 |
| 상수만 사용하는 UNION | 행 반환 | 행 반환 | UNION 자체와 함수 호출은 별개; 해설 추가 확장은 하지 않음 |

## 4. 구현 위치와 처리 순서
기준 SHA: ba4566352f9f52c79444f70a3a90222f1c00b10c.
- backend/app/main.py: 기본 앱. 제한 middleware/SQL authorizer를 등록하지 않는다.
- backend/app/labs/sql_injection.py: 입력 → Normal 필터 → compose_query → execute_active_sql. 활성 검토 문맥이 없으면 기존 SQLite 실행 경로로 간다.
- backend/app/review_app.py: create_review_app에 수치·sql_authorizer를 명시 주입할 때만 검토 정책 연결.
- docs/verification/scripts/issue42_review_server.py의 review_authorizer: 검토 서버 함수 목록.
- backend/tests/test_sql_limits.py의 authorize: 단위/검토 앱 시험용 함수 목록.
- docs/verification/scripts/issue44_policy_measure.py 내부 authorizer: 기존 측정에 사용한 함수 목록.
- 위 세 목록은 모두 length/printf/sum. backend/app/core/sql_limits.py 자체에는 확정된 함수 목록이 없다.
- backend/app/learning_trace.py의 _stopped_sql_trace: blocked를 operation_blocked로 안내하며 문법 오류와 구분한다. 목록 확정 전 이번 작업으로 문안/코드는 수정하지 않았다.

## 5. 함수별 필요성 — 구현 사실과 검토 의견 구분

| 현재 시험 허용 함수 | 하는 일과 작은 확인 예 | 현재 학습에 필요한가? | 기존 허용/시험 근거 | 검토 의견(미확정) |
| --- | --- | --- | --- | --- |
| length | 문자열 길이. length('abc') = 3 | Easy의 이름/비밀번호·따옴표·OR·주석, Normal 필터 우회에 필수 아님 | 위 3 authorizer에는 있으나 기존 SQL 제한 테스트/측정 스크립트에서 SQL length 호출 시험은 찾지 못함. Python len/bit_length는 SQL 함수가 아님 | 실제 채택할 학습 목표가 없다면 학습 목록에 남길 근거 부족. 이번에 임의 삭제하지 않음 |
| printf | 형식에 맞춘 문자열 생성. printf('%s','abc') = abc | 현행 안내 단계에 필수 아님 | test_total_result_cap_is_separate_from_single_cell에서 여러 행의 긴 문자열을 만들어 전체 결과 bytes 초과 검사 | 제한 기능 검증용 필요와 학습 서비스 허용 필요를 분리해 결정 |
| sum | 여러 행의 숫자 합산. users의 id 1+2 = 3 | 현행 안내 단계에 필수 아님 | 재귀 CTE의 sum(x)으로 VM 예산 중단·공유 예산·연결 정리·복구 시험. #44 과거 측정의 무거운 입력도 사용 | 제한 검증용 정책에서 사용 가능하지만 최종 학습 허용 목록은 별도 결정 |

현행 frontend/src/lesson-catalog.js의 SQL Easy 3단계와 Normal 2단계에는 위 세 함수가 필요하지 않다. 따라서 세 함수가 모두 교육상 필수라서 허용됐다고 설명할 근거는 없다. 함수 제거를 확정하는 것도 이 문서의 역할이 아니다.

SELECT/READ/RECURSIVE는 SQLite authorizer의 동작 분류이며 함수 이름이 아니다. 비교·OR·주석·UNION도 함수가 아니다. 함수 목록만 줄여도 모든 허용 연산 범위가 정해지는 것은 아니며, 특히 RECURSIVE는 재귀 계산량 시험을 위해 허용했던 부분이다. 이들의 최종 범위도 팀 결정 대상이다.

## 6. 이번 확인과 재현
- 스크립트: docs/verification/scripts/issue42_function_inventory.py.
- 원자료: docs/verification/evidence/2026-11-03-sql-function-inventory.json.
- 기준 SHA·Python/SQLite/OS·세 authorizer 파일 해시·각 입력·기대/실제 상태·Lens ID를 기록했다.
- 기본/검토 앱 각각 13건, 총 26건의 로컬 프로세스 내 ASGI 요청이 기대 결과와 일치했다.
- 검토 앱은 기존 시험용 수치를 그대로 사용했다. 새 제한값 산정/승인이나 기본 앱 적용은 하지 않았다.
- 실제 TCP/브라우저/화면/운영 부하 검증은 아니다. 기존 전체 테스트 통과 수를 이번 재실행 결과로 쓰지 않는다.
- 제품 파일을 수정하지 않았다. 기존 Lens·SQL 실행·정책을 재구현하지 않았다.

재현 명령: 프로젝트 backend 의존성이 설치된 Python으로 python docs/verification/scripts/issue42_function_inventory.py.

## 7. 한계와 다음 결정
- 최종 함수 목록·연산 범위·수치 제한은 태성님 검토 후 결정.
- 일반 이름/잘못된 구문 수용과 Lens 설명을 유지하며, 공격문만 받는 설계로 바꾸지 않는다.
- 현재 검토 앱에서 확인한 blocked 안내와 미래의 모든 미지원 구문 판별은 동일하지 않다. 미등록 함수·해석 불가 구문까지 모두 올바르게 분류했다고 주장하지 않는다.
- #44 보류는 구현/검증 완료 승인·이슈 종료·공개 승인과 다르다.
- 최초 정리 단계에서는 로컬 문서와 이슈 댓글로 공유했다. 이후 사용자의 명시적인 커밋·push 승인에 따라 이 문서·재현 스크립트·증거를 기존 개인 브랜치에 공유한다. PR/main 반영과 정책 적용은 포함하지 않는다. 댓글의 미커밋 표현은 게시 당시 상태다.

## 8. 추적
기존 원격 설명:
- https://github.com/ts825360/-PayloadLab-/blob/ba4566352f9f52c79444f70a3a90222f1c00b10c/docs/handoff/README.md
- https://github.com/ts825360/-PayloadLab-/commit/a6beb8aee7de8e24177c5a5052bd0a4b2dba4065
- https://github.com/ts825360/-PayloadLab-/commit/b168c7f6444748dcc6721913b6e49999230d6b1f

관련 이슈: #19, #42, #44, 결정 #6, 공개 전 검증 #24. 새 댓글 실제 URL은 게시 확인 기록에 저장한다. 아직 없는 PR/커밋/문서 원격 URL은 만들지 않는다.

### 게시 확인된 댓글
- #42: https://github.com/ts825360/-PayloadLab-/issues/42#issuecomment-6592398160
- #19: https://github.com/ts825360/-PayloadLab-/issues/19#issuecomment-6592398753
- #44: https://github.com/ts825360/-PayloadLab-/issues/44#issuecomment-6592399407
- #6: https://github.com/ts825360/-PayloadLab-/issues/6#issuecomment-6592400069
- #24: https://github.com/ts825360/-PayloadLab-/issues/24#issuecomment-6592400642
