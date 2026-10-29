# #19 — 입력에서 결과까지 이해할 수 있는 Lens 설명

> **팀원 검토용 설명 / 2026-10-28**<br>
> 관련: [이슈 #19](https://github.com/ts825360/-PayloadLab-/issues/19) · [전체 안내](README.md)

## 1. 무엇이 문제였나

기존에도 Lens, 조건 그림, 터미널 진단 설명은 있었다. 하지만 “거짓”, “실패”, “인식” 같은 결과와 내 입력 사이의 연결이 부족하거나, 특정 입력에 맞지 않는 공통 안내가 나오는 경우가 있었다.

예를 들어 SQL Easy에 `박태성`을 입력했을 때 “거짓”만 보면 누구와 비교했는지 알기 어렵다. 일반 이름을 입력한 것인지, SQL 문법을 틀렸는지, 공격 목표에 도달하지 못한 것인지도 혼동할 수 있었다.

## 2. 왜 이렇게 수정했나

설명의 순서를 **내 입력 → 서버가 만든 문장/요청 → 실제 비교·처리 → 결과 → 다음 작은 관찰**로 맞췄다. 사용자가 이번 결과를 설명하고 다음 입력을 예상할 수 있게 하는 것이 목적이다.

기존 Lens와 진단 연결을 바탕으로 문안·데이터 연결·상태 표시를 보완했다. Lens 전체를 새로 만든 작업으로 설명하면 안 된다. 실제 실행이 있는 SQL, 태그 판정과 브라우저 실행이 나뉘는 XSS, 모의 출력인 터미널 유형의 차이도 유지했다.

## 3. 어떤 동작으로 달라졌나

아래 문장은 개선 방향을 요약한 설명이다. 화면의 정확한 문구는 선택 행·입력·서버 결과에 따라 달라진다.

| 상황 | 기존 부족한 점 | 개선 후 설명과 동작 |
| --- | --- | --- |
| SQL에 일반 이름 `박태성` | 거짓과 조회 실패의 연결이 부족 | 입력이 이름의 따옴표 안에 들어감 → 선택한 admin 또는 guest와 이름이 다름 → 고정된 틀린 비밀번호도 맞지 않음 → AND 조건을 만족한 행이 없어 0행. 문법 오류로 설명하지 않음 |
| SQL 빈 입력 | 일반 이름 안내로 빈 값의 의미가 모호 | 빈 문자열과 계정 이름을 비교한다는 사실을 설명하고 0행과 연결 |
| SQL 따옴표 오류 | 다른 힌트가 실제 오류를 가릴 수 있음 | 실제 SQLite 문법 오류를 우선 안내. 조건식을 정상 평가했다고 말하지 않음 |
| SQL 알려진 OR 누락 | 오류 위치·역할·실제 결과가 분리 | 확인 가능한 형태에서 빠진 연결 연산자를 설명하면서 실제 문법 오류 상태도 유지 |
| SQL `O''Reilly` | 이름 안의 따옴표에도 OR 삽입을 권할 수 있음 | 따옴표가 포함된 이름 입력과 조건식 구성을 구분. 불필요한 OR 안내 제거 |
| SQL Normal 필터 변형 | 내가 쓴 값과 사용된 값을 혼동 | 원문과 대문자 OR 제거 후 값을 나눠 표시하고, 바뀐 문장과 결과를 연결 |
| SQL Easy의 OR 성공 입력 | 반환된 guest의 이유가 부족 | guest의 이름 비교는 거짓이어도 추가 비교가 참이고 OR로 묶여 반환되는 과정을 선택 행에 맞춰 설명 |
| 지원 범위 밖 SQL | 해석하지 못한 조건의 원인을 추측할 위험 | 실제 반환 사실과 설명 규칙의 한계를 구분. 임의로 OR 원인 등을 만들지 않음 |
| XSS 일반 글자·태그·script | 태그 인식과 실제 실행을 혼동 | 입력이 HTML 어디에 들어가는지 설명하고, 교육용 태그 인식과 브라우저 미리보기의 실행 관찰을 분리 |
| IDOR 본인·타인·없는 주문 | 객체번호와 소유권 관계가 불명확 | 요청 번호·현재 더미 사용자·실제 소유자·반환 결과를 연결. Normal의 요청 소유자 주장을 실제 인증으로 설명하지 않음 |
| SSRF | 문자열 정책과 실제 목적지·통신을 혼동 | URL 파싱 호스트와 신뢰 문자열 검사를 나눠 설명. 출력은 가상 응답이며 실제 DNS/HTTP 조회가 아님 |
| CMDi | 일반 호스트·명령 경계·차단·미지원이 섞임 | hostname이 조립 명령 어디에 붙는지, 구분자와 차단 원인이 무엇인지 설명. stdout/stderr와 모의 실행을 구분 |
| Linux | 퀴즈 불일치를 실제 Linux 문법 오류로 오해 | 명령·옵션·경로와 정해진 학습 목표를 비교. 모형이 모르는 명령을 실제로 존재하지 않는다고 단정하지 않음 |
| 권한 Easy | 명령 종류와 무관하게 같은 거부 설명 | 현재 가상 사용자·파일 소유자·읽기 권한·명령별 출력에 맞춤. sudo 규칙 조회, 가상 사용자 전환, 파일 읽기를 별개로 설명 |

### SQL의 처리 순서

1. 사용자의 원문을 보존하고 Normal에서는 필터 후 값도 구한다.
2. 그 값으로 조립한 SQL과 SQLite의 실제 결과를 얻는다.
3. 지원하는 작은 조건식 범위에서 계정별 비교와 AND/OR 관계를 설명한다.
4. 사용자가 행을 바꾸면 해당 계정의 설명을 보여준다.
5. 문법 오류·0행·성공·설명 미지원은 별도 상태로 안내한다.

조건 설명은 일반 SQL 해석기가 아니다. 실제 조회 결과보다 설명 규칙을 우선해 결과를 만들어내지 않는다.

### 권한·터미널에서 추가로 보완한 부분

`cat /lab/report.txt`가 거부되면 student와 소유자 mentor가 다르고 다른 사용자 읽기 권한이 없다는 원인을 원문 오류·Lens·TUI에 연결한다. `sudo /lab/maintenance` 뒤에는 가상 root 전환을 설명하되, 아직 파일을 읽은 것은 아니므로 실습 완료로 처리하지 않는다. `exit`는 가상 student 복귀를 설명한다.

작은 화면에서는 입력 폭과 Lens 탭 줄바꿈을 보완했다. 긴 초안을 둔 채 화면 크기를 바꿀 때 입력 높이도 따라 조정하도록 보완했다. 실제 OS 권한이나 셸 실행을 추가한 것은 아니다.

13개 실습의 최초 안내와 27단계도 대조했다. Easy는 따라 해 볼 예시·단계, Normal은 목표와 선택적 단서를 중심으로 읽히는지 확인했다. 정상적인 대체 `ls` 입력의 설명·출력을 보완했으며, 권한 Normal은 구현 예정으로 유지했다. 안내 완료와 공격 성공 판정도 구분했다.

## 4. CSV·참고 자료는 왜 손봤나

CSV의 attack 라벨은 교육용 시도 문맥이며 “실습 성공”이나 입력자의 악의를 뜻하지 않는다. 유형별 교육 범위와 모형의 한계를 문서로 설명했다.

Defender 조치로 SQLite 참고 Markdown이 사라져 파일 대조·재생성 검사가 막혔다. 전체 문서를 복원하는 대신 현재 CSV가 사용하는 메타데이터 조회문 4개만 명시적 발췌본으로 보관하고 원래 Git 원문과의 관계를 출처 파일에 남겼다.

CSV 4개·137행의 payload·label·출처 값은 그대로 유지했다. manifest는 새 발췌본 해시·관련 위치를 반영했다. 현재 자료는 **전체 원문 9개 + 발췌본 1개**다. 전체 원문 10개를 복원한 것으로 설명하지 않는다.

## 5. 코드는 어디를 보면 되나

| 역할 | 구현 또는 검증 위치 |
| --- | --- |
| SQL 조건·행별 이야기, XSS·IDOR trace | [learning_trace.py](../../backend/app/learning_trace.py): sql_lens, sql_row_stories, sql_trace, xss_trace, idor_trace |
| SSRF·CMDi·Linux·권한 모형과 설명 | [practice_extensions.py](../../backend/app/labs/practice_extensions.py) |
| 선택 행·조건·결과 표시 | [ExecutionCanvas.jsx](../../frontend/src/ExecutionCanvas.jsx) |
| 공통 문안·개념·단계 | [learning-content.js](../../frontend/src/learning-content.js), [lesson-catalog.js](../../frontend/src/lesson-catalog.js), [GuidedLesson.jsx](../../frontend/src/GuidedLesson.jsx) |
| 터미널 원문 진단·Lens·입력 크기 | [terminal 폴더](../../frontend/src/terminal/): DiagnosticText, diagnostics, TerminalInspector, TerminalInput, linux-desktop.css |
| SQL/XSS/IDOR 회귀 | [test_lens_narrative.py](../../backend/tests/test_lens_narrative.py), [test_learning_trace.py](../../backend/tests/test_learning_trace.py) |
| 다른 유형 회귀 | backend/tests의 test_ssrf_lens_narrative.py, test_cmdi_lens_narrative.py, test_linux_lens_narrative.py, test_permissions_lens_narrative.py |
| 문안 원칙·CSV 교육 범위 | [공통 문안 틀](../research/lens-feedback-template.md), [CSV 교육 범위](../research/csv-education-scope.md) |

## 6. 무엇으로 확인했나

- [기존/개선 문안과 41사례](../verification/2026-10-27-lens-narrative-review.md): SQL 주요 상태, XSS, IDOR, SSRF, CMDi, Linux의 입력·결과·화면 근거.
- [권한 Easy 검토](../verification/2026-10-27-permissions-lens-review.md): 사용자 복원·권한 거부·전환·읽기·exit와 실행 전 분석 구분.
- [13개 안내·27단계](../verification/2026-10-27-learning-flow-review.md): 실제 안내 경로와 진행 조건 대조.
- [작은 화면·터미널 조작](../verification/2026-10-27-terminal-interaction-review.md): 클릭·키보드·창 크기 변경, 입력 폭·초안 보존.
- [SQLite 발췌본 처리](../verification/2026-10-27-sqlite-source-excerpt.md): 파일 부재 해소와 데이터 검사 7개 통과.
- [최신 통합 검사](../verification/2026-10-28-suwoong-integration.md): #19+#42 backend 362·frontend 128·데이터 7 통과, 빌드 성공. 새로 실행한 결과가 아닌 저장된 검사 근거다.

XSS는 별도 미리보기를 열어 로컬 표식 하나의 실제 실행을 관찰했다. 모든 XSS 입력의 실행 보장은 아니다. 사용자의 “다 잘 되는 것 같음” 보고도 보존했지만, 이를 실기기 터치·200% 확대 각각의 통과 근거로 확대하지 않았다.

## 7. 어디까지 끝났고 무엇이 남았나

문안·코드·대표 화면 대조·자동 검사와 원문 파일 부재 처리는 위 근거에 기록되어 있다. #19 구현 공유용 [PR #48](https://github.com/ts825360/-PayloadLab-/pull/48)이 있다.

본인·팀의 최종 문안 검토와 세부 기기·hover·터치·실제 200% 확대 확인 중 기록되지 않은 부분은 구분해서 남겨야 한다. 초보자 참여 시험·학습 효과 검증도 수행하지 않았다. 팀 승인·main 반영·이슈 종료는 이 문서로 완료 처리하지 않는다. PR의 현재 원격 상태는 게시 전에 다시 확인한다.

다른 AI는 [최종 직접 검토표](../verification/2026-10-27-issue19-final-review.md)의 역사적 미완료 표현과 이후 추가 기록을 함께 읽어야 한다. 특히 “SQLite 원문 부재로 기존 검사 2개 미완료”는 후속 발췌본 처리로 해소된 과거 상태다.