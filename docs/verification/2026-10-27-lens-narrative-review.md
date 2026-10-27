# #19 Lens 문안 개선 통합 검토 — 2026-10-27

작성 대상: 이수웅(GitHub dtd2428)의 로컬 작업. AI 보조로 작성한 검증 기록이며, 본인 설명·최종 검토는 별도다.

관련: [#19](https://github.com/ts825360/-PayloadLab-/issues/19), [#10 위치 안내](https://github.com/ts825360/-PayloadLab-/issues/10), [#46 인계](https://github.com/ts825360/-PayloadLab-/issues/46). 팀장 인계에 명시된 연계 이슈: #14–#18, #29–#32, #36. 이 문서로 해당 이슈의 완료를 주장하지 않는다.

기준 main: 23b05593b73f6d9c9556eecd68abad5fbb8f6801. 2026-10-27 원격 main도 같은 커밋임을 읽기 전용으로 확인했다.
작업 브랜치: dtd2428/issue-19-lens-sql. 작업 위치: 사용자가 지정한 문서/GitHub/-PayloadLab-.
2026-10-27 사용자가 로컬 커밋 진행을 승인해 코드·테스트를 9c90358df363e03123d5e72bf72e52901d7002f0 로 저장했다. 검증 근거는 f8e53b4 문서 커밋으로 기록했다. 기존 코드·문서 커밋은 작업 브랜치에 원격 공유됐으며 공통 기준의 후속 문서 변경도 사용자 승인에 따라 같은 브랜치로 commit/push한다. PR 게시·main 반영은 수행하지 않았다. [PR 본문 초안](2026-10-27-lens-pr-draft.md)을 함께 제공한다.

공통 템플릿과 연결 문서의 후속 수정은 이 파일을 포함하는 문서 커밋으로 기록한다. 실제 공유 상태는 원격 작업 브랜치와 해당 커밋을 대조한다.

## 1. 범위와 완료 수준

| 항목 | 실제 상태 |
| --- | --- |
| 공통 문안 템플릿 | [문안 틀·상태 구분·Easy/Normal·검토 양식](../research/lens-feedback-template.md) 작성 및 기존41사례 AI 대조 완료. 본인·팀 최종 검토 대기 |
| SQL 일반 이름·빈 입력·따옴표 오류·OR 누락·필터 변형·성공 입력 | 코드·자동 검사·화면 대조 완료, 사용자 최종 검토 대기 |
| 참/거짓의 비교 대상·선택 계정·반환 결과 설명 | 지원하는 작은 조건식 범위에서 구현·검사. 일반 SQL 해석기 아님 |
| XSS·IDOR 입력→조립→처리→결과→다음 관찰 | 코드·자동 검사·화면 대조 완료 |
| SSRF·CMDi·Linux Easy/Normal | 설명·흐름도 관련 보완 및 2차 검증 완료 |
| 유형별 비교·입력·기대 결과·테스트·화면 근거 | 이 통합 문서와 아래 연결 자료로 정리 |
| 권한 Easy 설명·진단 연결 | [명령별 설명·28개 새 검사·2차 화면 대조](2026-10-27-permissions-lens-review.md) 완료. 본인·팀 검토 대기. 권한 Normal은 구현 예정 유지 |
| 13개 실습 학습 흐름 | [최초 안내13개·실제27단계·2차 전체 검사](2026-10-27-learning-flow-review.md) 대조와 대체 명령 보완 완료. 대표 안내 경로 검증이며 모든 입력·조작의 통합 검증은 아님 |
| 터미널 작은 화면·조작 | [입력 폭·Lens CSS·resize 높이 보완, 실제 클릭/키보드·크기 변경과 전체113개 검사](2026-10-27-terminal-interaction-review.md). 실제 hover·터치·200% 확대는 미검증 |
| CSV 유형별 교육 범위 | [137행 문맥·유형별 모형 범위 검토](../research/csv-education-scope.md). [Git 원문10개/출처105건·기존 생성기 재현2개 통과](2026-10-27-csv-snapshot-verification.md). 작업 원문1개 부재와 기존 파일 기반2오류는 별도 미해결 |
| 초보자 참여 시험·학습 효과 검증 | 미실시. 자동 검사나 AI의 화면 대조와 구분 |
| commit / push / PR / main 반영 / 이슈 종료 | 코드·테스트·검증 문서 원격 공유. 공통 기준은 9b43f57로 공유. 권한 Easy 후속분은 사용자 승인에 따라 이 기록을 포함하는 커밋으로 공유하며 원격 전송 결과는 git으로 확인한다. PR·main 반영·이슈 종료는 미실시 |

팀장 댓글의 SQL·XSS·IDOR 중심 검토 항목에 대한 구현·검증 근거를 정리했지만, 인계 이슈 #19 전체를 완료했다는 뜻은 아니다. 권한·CSV 잔여 범위와 사용자의 실제 검토가 남아 있으므로 PR은 Refs #19로 연결하고 Closes #19를 사용하지 않는다.

## 2. 비교 문안과 사례

기존 문안은 위 기준 커밋에서 추출했다. 아래 개선 문안은 의미를 요약한 것이며, 정확한 전체 문구·초점 범위·조립 문장·분석/실행 결과는 [41개 고정 사례 JSON](2026-10-27-lens-review-cases.json)에 들어 있다.

### SQL

| 입력 / 사례 ID | 기존 설명·문제 | 개선 설명·동작 | 기대 결과와 실제 확인 |
| --- | --- | --- | --- |
| 박태성 / SQL-01 | 이름이 값이라는 설명과 고정 비밀번호 안내는 있었지만 비교 대상·조회 실패의 연결이 부족 | 입력이 이름의 따옴표 안에 들어감→admin/guest 각각과 다름→비밀번호도 틀림→AND가 거짓→반환 없음. 선택 행을 바꾸면 그 계정 설명으로 바뀜 | empty, 0행. admin/guest 비교와 표 표시 확인 |
| 빈 입력 / SQL-02 | 일반 이름 설명만으로는 빈 값의 처리와 결과가 모호 | 빈 문자열도 이름 값으로 들어가며 어떤 계정과 비교했는지, 문법 오류와 다른 결과임을 설명 | empty, 0행. 이전 이름 설명을 재사용하지 않음 |
| admin 뒤 작은따옴표 / SQL-03 | 실제 오류보다 다른 힌트가 우선하면 조건 불충족과 혼동 | SQLite의 실제 문법 오류를 우선 안내하고 계정 조건을 평가한 것처럼 말하지 않음 | syntax_error. 원문 오류·미평가 확인 |
| admin' '1'='1'-- / SQL-04 | 알려진 OR 누락 진단과 실제 문법 오류가 함께 필요 | 해당 알려진 형태에서 연결 연산자의 위치·역할을 설명하면서 실제 실행 오류 상태 유지 | syntax_error, Lens missing_operator |
| admin' OR '1'='1'--, Normal / SQL-05 | OR 제거와 문법 오류가 따로 설명됨 | 내가 쓴 원문과 서버가 사용한 값을 분리하고, 연결 부분 변경과 이번 오류를 이어서 설명 | syntax_error, 원본 유지·유효 값에서 대문자 OR 제거 |
| 같은 입력, Easy / SQL-06 | 성공 사실만 있고 반환된 guest의 이유가 부족 | 이름 비교가 거짓인 guest도 상수 비교가 참이고 OR로 연결되어 반환되는 과정을 설명 | matched, 2행. guest 선택 시 이름 거짓·상수 참·전체 참 |
| O''Reilly / SQL-07 | 일반 이름의 연속 따옴표에도 OR를 넣으라고 권함 | 따옴표 문자를 포함한 이름으로 읽는 경우와 조건식 구성을 구분 | empty, OR 삽입 안내 없음 |
| admin'' OR 1=1--' / SQL-08 | 연속 따옴표 힌트가 실제 문법 오류를 가림 | 실제 오류를 먼저 안내 | syntax_error |
| admin'-- / SQL-09 | 임의 식에까지 조건 이야기를 만들 위험 | 실제 반환 사실과 설명 규칙의 지원 한계를 분리 | matched, 지원 범위 안내·추측한 OR 설명 없음 |
| 주석 없는 OR 비교 / SQL-10 | 주석이 모든 성공 입력에 필수인 것처럼 오해할 위험 | 뒤 비밀번호 조건의 포함 여부와 AND/OR 관계를 지원 범위 안에서 설명 | matched, 1행. 비밀번호가 모두 주석 처리됐다고 말하지 않음 |

화면: [일반 이름·계정별 비교](assets/2026-10-27-original-repo-review.png), [guest 성공](assets/2026-10-27-sql-guest-story.png), [필터와 오류](assets/2026-10-27-sql-filter-story.png).
추가 6종·따옴표 사례의 당시 캡처는 [SQL 첫 검토 기록](2026-10-26-lens-sql-review.md)에 보존했다. 그 문서의 당시 미완료 표현은 이 통합 문서에서 갱신한 상태를 기준으로 읽는다.

### XSS

| 입력 / 사례 ID | 기존 설명·문제 | 개선 설명·동작 | 기대 결과와 실제 확인 |
| --- | --- | --- | --- |
| hello, &lt;b&gt;hello&lt;/b&gt; / XSS-01~02 | 본문 삽입과 태그 설명은 있었지만 내 입력과 결과 연결이 짧음 | 내 검색어→p 본문에 들어가는 위치→교육용 script 규칙 여부→별도 브라우저 관찰로 연결 | unrecognized. 일반 글자/표시 태그를 실행 실패로 단정하지 않음 |
| &lt;script&gt; / XSS-03 | 미완성 형태와 실제 실행을 혼동할 수 있음 | 태그 규칙의 미충족과 브라우저 실행의 미확인을 구분 | unrecognized |
| &lt;script&gt;&lt;/script&gt; / XSS-04 | 태그 형태가 맞아도 내용이 비면 실행 효과가 없을 수 있음 | 인식 성공을 JavaScript 실행 성공이라고 하지 않음 | recognized, browser_execution_verified=false |
| &lt;script&gt;hello&lt;/script&gt;, Normal / XSS-05 | 소문자 시작 태그 필터 설명이 원문/전달값 이야기와 분리 | 원본과 필터 후 HTML에 들어간 값을 함께 표시 | unrecognized, 필터 변형 확인 |

2026-10-27 로컬 Easy에서 화면 근거를 추가했다. 입력은 script 내부에서 document.body.textContent를 '학습표식'으로 바꾸는 한 문장이다. 결과 버튼을 누르기 전에는 교육용 태그 인식만 표시됐다. 사용 동작과 동일하게 **브라우저 결과 열기**를 누른 뒤 iframe 내부의 '학습표식'을 직접 확인했다. 외부 요청·쿠키 조회·데이터 전송은 넣지 않았다.

[태그 인식 화면](assets/2026-10-27-xss-tag-recognition.png), [명시적으로 연 iframe의 실제 표식](assets/2026-10-27-xss-browser-marker.png).

이 표식 한 사례의 실제 실행 관찰이 모든 XSS 입력의 실행을 증명하지는 않는다. API의 browser_execution_verified=false는 자동 판정이 실행을 증명하지 않는다는 뜻으로 계속 유지한다. 기존 공개 격리 보안 과제 #43을 완료한 것도 아니다.

### IDOR

| 입력 / 사례 ID | 기존 설명·문제 | 개선 설명·동작 | 기대 결과와 실제 확인 |
| --- | --- | --- | --- |
| 주문1042 / IDOR-01 | 현재 사용자·대상 변경의 일반 설명 | 요청1042→교육용 현재 사용자1042→소유자1042→본인 주문 반환 | own, 1개 |
| 주문1043 / IDOR-02 | 타인 주문 반환의 실제 소유자 설명 부족 | 요청1043의 소유자는2001인데 현재 사용자1042에게 반환된 관계를 설명 | exposed, 1개 |
| 주문9999 / IDOR-03 | 권한 차단과 주문 없음이 혼동될 수 있음 | 대상 없음→소유자 비교를 할 주문 없음→반환 없음 | missing, 0개 |
| 주문1043, claimed_user_id=1 / IDOR-04 | 요청의 주장과 실제 인증 세션을 혼동할 위험 | 주장값1과 실제 소유자2001 비교가 다르므로 차단. 고정된 더미 사용자이며 실제 인증 아님 | blocked, 0개 |
| 주문1043, claimed_user_id=2001 / IDOR-05 | 단지 주문번호만 바꿔 성공한 것처럼 오해할 수 있음 | Normal이 요청의 소유자 주장을 믿는 불완전한 검사임을 설명 | exposed, 1개 |

화면: [객체번호·소유자·더미 사용자 관계](assets/2026-10-27-idor-story.png).

### SSRF

| 입력 / 사례 ID | 기존 설명·문제 | 개선 설명·동작 | 기대 결과와 실제 확인 |
| --- | --- | --- | --- |
| https://example.com/news / SSRF-01 | 가상 공개 응답이라는 단정적 표현 | 입력 URL→파싱한 호스트→모형 정책→가상 응답. 실제 공개 여부·안전성은 검사하지 않았다고 설명 | fetched. DNS/HTTP 미요청 |
| http://127.0.0.1/admin, Normal / SSRF-02 | 차단이 실제 연결 실패처럼 보일 수 있음 | 신뢰 문자열이 없어 모형 정책이 차단한 이유를 설명 | blocked, 모의 stdout 없음 |
| 신뢰 문자열@127.0.0.1 / SSRF-03 | 사용자 정보와 목적지 호스트 혼동 | 마지막 @ 앞은 사용자 정보, 뒤는 실제로 파싱한 호스트라는 모형 해석 설명 | fetched, 루프백 가상 응답 |
| 사용자 정보와 신뢰 문자열 경로가 함께 있음 / SSRF-04 | 한 분기만 설명해 경로의 통과 원인이 누락 | 사용자 정보와 경로에 있는 문자열 정책을 함께 설명 | fetched |
| localhost:bad / SSRF-05 | 지원 형식 밖을 정책 차단으로 표시 | 포트 형식 검사와 정책 차단을 구분하고 흐름도도 지원 범위 밖으로 표시 | unsupported |
| 이모지@localhost / SSRF-06 | Python 문자 범위와 JS UTF-16 차이로 강조가 어긋남 | 입력·조립 문장·확대 화면에서 서버의 코드포인트 범위를 변환 | fetched, localhost만 정확히 강조 |
| http://10.0.0.1/admin / SSRF-07 | 루프백이 아니면 공개 목적지로 오해 | 일반 목적지용 가상 응답이며 실제 주소의 공개·안전 판정이 아니라고 명시 | fetched, 일반 목적지 더미 |

화면: [Normal의 입력→정책→호스트→더미](assets/2026-10-27-ssrf-normal-story.png), [이모지 뒤 호스트 강조](assets/2026-10-27-ssrf-second-pass-highlight.png).

### CMDi

| 입력 / 사례 ID | 기존 설명·문제 | 개선 설명·동작 | 기대 결과와 실제 확인 |
| --- | --- | --- | --- |
| example.com / CMD-01 | 호스트 하나를 사용했다는 짧은 안내 | 입력이 ping -c 1 뒤에 붙음→호스트 인자→일반 입력→모의 응답. 공격 목표 미충족을 문법 오류로 설명하지 않음 | command_ok |
| example.com; whoami / CMD-02 | 추가 명령 인식만 설명 | 호스트·구분자·추가 명령을 나누고 고정 webapp 출력과 연결 | injected |
| 같은 입력, Normal / CMD-03 | 필터가 ;를 제거하는 것처럼 읽힐 수 있음 | 입력을 지우는 것이 아니라 전체 처리를 차단. stdout 부재와 stderr의 차단 안내를 구분 | blocked |
| example.com && id, Normal / CMD-04 | &&의 조건과 모형 가정 설명 부족 | 앞 명령 성공 때 이어지는 연결이며 모형은 ping 성공을 가정. 고정 사용자·그룹 번호와 연결 | injected |
| example.com && whoami; pwd, Normal / CMD-05 | 앞의 &&를 차단 원인 ; 대신 강조 | focus는 차단을 일으킨 ;, 흐름도는 첫 명령 경계 &&와 필터 ; 판단을 분리 | blocked |
| example.com; / CMD-06 | 불완전한 조각과 일반 미지원이 같은 안내 | 구분자 뒤의 명령 누락을 짚되 실제 셸의 문법 오류로 단정하지 않음 | unsupported |
| example.com &#124;&#124; whoami / CMD-07 | 지원하지 않는 분기의 실행 결과를 추측할 위험 | 실패 시 연결하는 기호의 역할과 이 모형이 그 분기를 해석하지 않는다는 한계를 설명 | unsupported |

화면: [복합 구분자 차단·stderr·필터 근거](assets/2026-10-27-cmdi-second-pass-blocked.png). 실제 셸·ping·네트워크 실행을 추가하지 않았다.

### Linux

| 입력 / 사례 ID | 기존 설명·문제 | 개선 설명·동작 | 기대 결과와 실제 확인 |
| --- | --- | --- | --- |
| ls, Easy / LINUX-01 | 정답 토큰이라는 일반 안내 | 공백으로 나눈 명령 조각→현재 가상 /lab→이름만 보는 목표→두 파일 이름 | quiz_correct |
| 빈 입력 / LINUX-02 | 목표와 토큰을 다시 보라는 안내 | 비교할 조각이 없음을 설명하고 명령 이름 한 조각부터 관찰 | quiz_incorrect / empty |
| ls -l /lab, Easy / LINUX-03 | 실제 Linux 오류처럼 받아들일 수 있음 | 긴 목록과 이름만 보는 Easy의 정답 범위 차이 설명 | quiz_incorrect / goal_mismatch |
| ls /lab, Normal / LINUX-04 | 어떤 조각이 부족한지 알기 어려움 | -l 옵션의 역할·누락 위치를 설명하고 작은 다음 관찰 제시 | quiz_incorrect / goal_mismatch |
| ls /lab -l, Normal / LINUX-05 | 퀴즈의 고정 순서와 일반 Linux 문법을 혼동 | 이 퀴즈가 정해진 순서와 비교한다는 사실을 설명. 실제 Linux에서 틀린 문법이라고 단정하지 않음 | quiz_incorrect / goal_mismatch |
| pwd, Normal / LINUX-06 | 실제로 없는 명령으로 오해할 수 있음 | 이 퀴즈의 해석 지원 범위 밖이며 명령 존재 여부를 판정하지 않았다고 설명 | quiz_incorrect / unmodeled |
| ls -l /lab, Normal / LINUX-07 | 출력의 각 열과 계정 연결 부족 | 명령·옵션·경로→긴 목록 목표→권한·소유자·경로의 간략한 가상 출력, mentor/student의 파일 연결 | quiz_correct |

Linux의 필요한 개념 버튼이 SQL 설명으로 폴백하던 연결을 고쳤다. 흐름도는 답이 틀렸을 때 파일을 조회한 것처럼 그리는 대신 입력·목표·비교 상태를 보여준다.
화면: [Linux 전용 개념](assets/2026-10-27-linux-concept-review.png).

## 3. 검증 근거와 재현

### 자동 검사 — 원래 저장소에서 재실행

| 검사 | 결과 | 원문 로그 |
| --- | --- | --- |
| backend: python -m pytest -q | 198 passed | [백엔드 로그](evidence/2026-10-27-backend-tests.txt) |
| frontend: pnpm test --maxWorkers=1 --minWorkers=1 | 108 passed / 19 files | [프론트 로그](evidence/2026-10-27-frontend-tests.txt) |
| frontend: pnpm build | 성공 / 488 modules | [빌드 로그](evidence/2026-10-27-frontend-build.txt) |
| 고정 before/after 41사례 추출 | 41개 예상 상태 일치, 분석 execution=None | [JSON](2026-10-27-lens-review-cases.json), [재생성 스크립트](scripts/lens_review_cases.py) |
| git diff --check / 문서 상대 링크 검사 | 통과 | 최종 문서 저장 후 별도 실행 |

새 회귀 검사: backend/tests/test_lens_narrative.py, test_ssrf_lens_narrative.py, test_cmdi_lens_narrative.py, test_linux_lens_narrative.py 및 기존 test_learning_trace.py 보완.
화면 회귀 검사: frontend/src/execution-canvas.test.jsx, input-shortcuts.test.jsx, terminal/TerminalInspector.test.jsx.

재현 방법: 저장소에서 기존 requirements-dev 및 pnpm lockfile에 맞는 의존성을 준비한 후 다음을 실행한다. 사례 추출 스크립트는 기준 커밋의 Python 코드를 읽으므로 로컬 Git 이력이 필요하다.

    cd backend
    python -m pytest -q
    cd ../frontend
    pnpm test --maxWorkers=1 --minWorkers=1
    pnpm build
    cd ..
    python docs/verification/scripts/lens_review_cases.py
    git diff --check

사례 JSON은 FastAPI **경로 함수 직접 호출** 결과다. HTTP·실제 브라우저 실행 결과를 JSON으로 오인하지 않는다. SQL은 메모리 SQLite를 쓰며, XSS의 실제 표식 관찰은 위 별도 화면 검사다.

### 2차 확장 검사 — 당시 실행한 보조 기록

SSRF URL480조합, CMDi 입력2880조합, Linux 입력7392조합과 Linux 실제 HTTP 경계60건은 이전 단계에서 통과했다. 이 수치는 pytest 검사 수에 합산하지 않는다. 당시 일회성 검사 원문 스크립트·로그는 이 문서에 완전히 보존되지 않았으므로, 지속 가능한 회귀 근거는 저장된 검사 파일과 고정41사례를 우선한다.

### 실제 화면 대조

2026-10-26~27 로컬 Vite5173·API8001에서 AI가 직접 화면을 조작했다. SQL 행 변경·필터 전후·오류, XSS 표시/실행 구분, IDOR 관계, SSRF 호스트와 정책, CMDi 차단/미지원/성공, Linux 목표 비교를 확인했다. 첨부 이미지는 그 시점의 화면으로 모든 입력·모바일·확대 비율을 각각 입증하지는 않는다. 유형별 예시와 자동 검사를 함께 읽는다.

2026-10-27 문서 정리 중 XSS 표식 실행을 다시 관찰했으며 확인한 브라우저 경고·오류 로그는 없었다. 실제 초보자 시험·교육 효과·모든 브라우저 호환성은 별도다.

## 4. 남은 일과 제출

- 공통 문안 템플릿의 본인·팀 검토, 권한 Easy의 본인·팀 최종 문안 검토, 터미널의 실제 hover·터치·확대별 조작 검증, CSV 유형별 교육 범위 확인.
- 사용자가 문안과 실제 결과를 읽고 본인 설명으로 검토.
- 사용자가 로컬 커밋을 검토하고 직접 push한 뒤 PR 본문 초안을 실제 검증한 커밋에 맞춰 게시.
- 체크박스는 실제 기준을 확인한 뒤 본인이 체크. 전체 #19 기준 충족 전 이슈를 닫지 않음.
- 본 문서는 공개 배포·XSS 격리·자원 제한 등 별도 보안 과제의 완료나 승인을 의미하지 않음.
