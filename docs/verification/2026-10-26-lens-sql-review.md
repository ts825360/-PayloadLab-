> 이 문서는 2026-10-26 첫 검토 당시 기록입니다. 이후 수정·검증과 현재 완료 범위는 [2026-10-27 통합 검토](2026-10-27-lens-narrative-review.md)를 기준으로 확인하세요.

# #19 SQL Lens 첫 문안 검토

관련: [#19](https://github.com/ts825360/-PayloadLab-/issues/19), #10, #29, #31, #32.
검토자: 이수웅(`dtd2428`), AI 보조. 검토일: 2026-10-26.
기준: main `23b05593b73f6d9c9556eecd68abad5fbb8f6801`.
작업: `dtd2428/issue-19-lens-sql`의 로컬 미커밋 변경. 사용자가 커밋 전 검토를 요청했으므로 commit/push/PR/main 반영은 진행하지 않았다.

## 요구사항 대조와 이번 범위

사용자가 확인한 첫 보완은 두 건이다. 이미 구현된 일반 이름·오류·필터·성공 설명을 재구현하지 않고, 이름에 포함된 따옴표를 공격 조건으로 오해시키는 안내와 실제 문법 오류를 가리는 안내만 보완한다.

| 확인한 기록 | 이번 작업에 적용한 기준 |
| --- | --- |
| #19 본문·팀장 요청/인계 댓글 | 일반 이름을 잘못된 공격으로 단정하지 않음. 실제 입력→문장→처리→결과와 설명을 대조하고 기존/개선 문안을 기록 |
| #10·#29·#31·#32 | 위치·무엇·이유와 다음 관찰을 제공. 알 수 없는 식을 해석한 것처럼 단정하지 않음. 전체 조건 체인 설계 완료를 주장하지 않음 |
| `planning/2026-10-25-team-handoff.md`, `ISSUE-GUIDE.md` | 본인 브랜치·시작 댓글·검증 근거. 부분 작업은 Refs #19, 전체 완료 전 이슈 유지 |
| `decisions/2026-10-23-unified-workspace.md`, `2026-10-24-issue-completion-review.md` | 기존 API·판정·학습 흐름 유지. 구현·자동 검사·브라우저 검증·교육 효과를 구분 |
| `superpowers/specs/2026-10-24-dual-workspace-design.md` | 원문과 교육용 진단 구분, 미지원 구문 추측 금지. 이번에는 터미널·화면 구조를 수정하지 않음 |
| `datasets/payloads-all-the-things/README.md` | CSV/원문/manifest·라이선스 보존. 자료를 실행기로 일괄 전달하지 않음 |

원격 브랜치 목록을 확인하고 운영 가이드·데이터 관련 브랜치의 문서 스냅샷도 main과 대조했다. 구형 브랜치의 가이드가 최신 인계보다 우선하지 않으며, 주간 보고 브랜치는 발표/보고 기록으로 구분한다. 이번 수정에 과거 브랜치를 병합하거나 다른 작업을 가져오지 않았다.

## 기존 설명과 변경안

| 입력 / 실제 결과 | 기존 문제 | 수정 설명·동작 |
| --- | --- | --- |
| `O''Reilly`, `D''Angelo`, `admin''` / 문법 정상·반환 없음 | 모든 연속 따옴표에 “이름 문자열을 닫지 못했다”, “두 따옴표 사이에 OR를 넣으라”고 안내. 이름을 입력한 사람에게 공격식 구성을 강요 | 온전히 문자열 값인 경우에만 “이름에 따옴표 문자가 포함돼요”. 따옴표 하나를 문자로 읽는다는 설명과 이름·비밀번호 비교 안내를 제공 |
| `admin'' OR 1=1--'` / 실제 SQLite 문법 오류 | 오류 결과가 있는데도 연속 따옴표 설명이 먼저 선택됨 | 실제 오류를 확인한 경우 syntax_error 안내를 먼저 제공. 조립 문장·오류 메시지·문자열 경계를 관찰하도록 안내 |
| `admin''1'='1'--` / 문법 정상·반환 없음 | 기존의 공백 없는 OR 누락 교육 사례 | 이 알려진 비교식 형태에 한해 기존 escaped_quote·OR 안내와 위치 5~7 유지 |
| `admin''' AND 1=0--` / 문법 정상·반환 없음 | 새 이름 안내를 지나치게 넓게 적용하면 복합 식까지 이름으로 오해시킬 수 있음 | 단순 문자열 검사에 맞지 않는 식은 기존 inspect_result로 폴백. 분석에서는 ready_to_try로 실행 전 상태 유지 |

일반 이름용 다음 행동 문안:

> 조립된 SQL의 이름 값과 admin·guest의 이름을 비교하고, 고정된 비밀번호 조건도 함께 확인해보세요.

문법 오류용 다음 행동 문안:

> 문자열의 끝과, 그 뒤 조건이 시작하는 경계를 확인해보세요.

## 실제 경로 함수로 대조한 사례

FastAPI 경로 함수 `attempt_lab`과 `analyze_lab`을 직접 호출했다. 실제 HTTP나 브라우저 검사가 아니다. SQL은 요청별 SQLite 메모리 DB에서 실행하며 분석은 EXPLAIN으로 실행 결과와 구분한다.

| 사례 | 난이도 | 실행 상태 / 반환 행 | 실행 Lens / 분석 Lens |
| --- | --- | --- | --- |
| 박태성 | Easy | empty / 0 | string_value / string_value |
| 빈 입력 | Easy | empty / 0 | string_value / string_value |
| `admin'` | Easy | syntax_error / 0 | syntax_error / syntax_error |
| `admin' '1'='1'--` | Easy | syntax_error / 0 | missing_operator / missing_operator |
| `admin' OR '1'='1'--` | Normal | syntax_error / 0, 대문자 OR 제거 | filter_changed / filter_changed |
| `admin' OR '1'='1'--` | Easy | matched / 2 | success / ready_to_try |
| `O''Reilly` | Easy | empty / 0 | escaped_quote / escaped_quote, OR 삽입 안내 없음 |
| `admin'' OR 1=1--'` | Easy | syntax_error / 0 | syntax_error / syntax_error |
| `admin''1'='1'--` | Easy | empty / 0 | escaped_quote / escaped_quote, 기존 OR 안내 유지 |
| `admin''' AND 1=0--` | Easy | empty / 0 | inspect_result / ready_to_try |

## 검사와 시행착오

환경: Windows, Python 3.13.2, FastAPI 0.115.0, Pydantic 2.9.2, pytest 8.3.3, SQLite 3.45.3. 저장소의 고정 requirements-dev를 격리된 작업 환경에 설치했다. 전이 의존성 전체 lock은 기존 저장소에 없으며 이를 추가하지 않았다.

backend 디렉터리에서:

```text
python -m pytest tests/test_learning_trace.py -q -k "escaped_names or syntax_error_takes"
수정 전: 2 failed, 15 deselected

python -m pytest tests/test_learning_trace.py tests/test_input_analysis.py tests/test_practice_integration.py -q
첫 수정: 1 failed, 24 passed
원인: 기존 공백 없는 OR 누락 사례가 missing_operator로 분류됨.
연속 따옴표와 일반 누락을 분리한 뒤: 25 passed

복합 식을 이름으로 단정하지 않는 경계 사례 추가:
수정 전 1 failed → 단순 문자열에만 이름 설명을 적용

python -m pytest -q
최종: 102 passed in 1.61s
```

신규 검사 함수 2개가 분석/실행, 일반 이름 3개, 복합 식의 미지원 안내, 실제 문법 오류를 검사한다. 기존 OR 누락·SQL 성공·필터·XSS·IDOR·확장 모형 검사도 전체 실행에 포함됐다. CSV·프론트 파일은 변경하지 않았다.

## SQL 실제 브라우저 대조 — 2026-10-26 후속

사용자가 SQL 6개 사례의 화면 대조를 요청해 in-app browser 기본 화면 1280×720에서 확인했다. 로컬 프론트는 고정 pnpm lockfile로 설치했으며 루프백 Vite 5173·FastAPI 8001을 사용했다. 기존 샌드박스 서버는 브라우저에서 연결되지 않아 이번에 시작한 서버만 종료하고 로컬 접근이 가능한 환경에서 재기동했다. 외부 공개·외부 대상 요청은 하지 않았다. 화면의 기존 닫기 동작으로 입력 화면과 결과 dialog를 오가며 검사했으며 뷰포트 override는 사용하지 않았다.

| 사례 | 실제 화면에서 확인한 내용 | 판단과 근거 |
| --- | --- | --- |
| 박태성 / Easy | 입력이 이름 따옴표 안에 표시됨. admin→guest 선택 시 계정명·현재 행·비교 설명이 함께 변경. 이름과 고정 비밀번호 비교가 거짓이며 반환 0개 | 계정별 일반 입력 설명은 이미 동작. [admin 화면](assets/2026-10-26-sql-plain-admin.png), [guest 화면](assets/2026-10-26-sql-plain-guest.png) |
| 빈 입력 / Easy | 빈 이름 값으로 실행 가능. 이름 비교·고정 비밀번호 조건·반환 0개. 이전 박태성 설명을 그대로 사용하지 않음 | [빈 값 결과](assets/2026-10-26-sql-empty.png). 결과 dialog에 시작 전 안내가 함께 보여 실제 결과를 보려면 내부 스크롤이 필요할 수 있음. 빈 입력 안내의 표현 적합성은 추가 검토 대상 |
| `admin'` / Easy | “조회 전에 문법 오류”, SQLite 오류 원문, 계정별 미평가, 실행 중단 표시 | 단순 반환 0개와 구분. [문법 오류](assets/2026-10-26-sql-syntax.png) |
| `admin' '1'='1'--` / Easy | Lens는 빠진 연결 연산자·AND/OR 역할·삽입 위치를 안내. 결과는 문법 오류·미평가로 표시 | 구체적인 누락 설명과 실제 오류 상태가 함께 유지됨. [OR 누락](assets/2026-10-26-sql-missing-or.png) |
| `admin' OR '1'='1'--` / Normal | 입력창에는 OR가 있는 원본 유지. 입력 위치 설명·조립 SQL에는 OR 제거값 표시. Normal 단서를 펼치면 필터 전후 비교 안내. 실제 실행은 문법 오류 | 원본/필터값 구분은 동작. 필터 변화→이번 오류 원인의 이야기 연결은 추가 보완 필요. [필터 Lens](assets/2026-10-26-sql-filter-lens.png), [실행 결과](assets/2026-10-26-sql-filter-result.png) |
| `admin' OR '1'='1'--` / Easy | 반환 2개. guest 선택 시 이름 비교는 거짓, `'1'='1'`은 참, OR 전체는 참이며 guest도 반환 표시 | 그림·행 정합성 확인. 성공 Lens 자체는 여전히 일반적인 결과 안내여서 계정별 문장 보완 후보. [guest 성공](assets/2026-10-26-sql-success-guest.png) |

이전 로컬 수정 두 건도 실제 화면에서 추가 확인했다. `O''Reilly`에는 이름의 따옴표 문자 설명·이름/비밀번호 비교가 표시되고 OR 삽입 안내가 없다([화면](assets/2026-10-26-sql-escaped-name-lens.png)). `admin'' OR 1=1--'`에는 Lens와 결과가 모두 문법 오류로 표시된다([화면](assets/2026-10-26-sql-escaped-syntax.png)).

### 사용자 검토용 추가 문안 제안 — 아직 수정하지 않음

| 항목 | 실제로 본 기존 문구/빈 부분 | 다음 보완 방향 |
| --- | --- | --- |
| 결과 창과 다음 행동 | 입력 화면 Lens가 “오른쪽 계정 행을 눌러”라고 하지만 현재 계정 표는 별도 결과 창 안에 있음 | 실제 버튼 이름을 사용해 “문장에서 해당 위치 보기로 결과 창을 열고, 관찰할 계정을 admin·guest로 바꿔 비교해보세요”처럼 현재 동작에 맞춤 |
| 성공 원인 | Lens는 “실제 SQLite 조회에서 계정 행이 반환됐습니다”, “주석은 모든 성공 입력에 필수인 것은 아닙니다”라고만 설명. guest 화면에 계정별 자연어 설명은 없음 | 지원하는 조건식에 한해 이름 비교·추가 비교·OR·주석·실제 반환을 이어서 설명. 미지원 식에는 성공 사실과 설명 한계만 표시 |
| 필터 변화와 오류 | OR 제거 사실과 실제 문법 오류는 각각 보이나, 연결이 끊겨 다음에 무엇을 볼지 추론해야 함 | 이번 입력의 필터 전후 차이가 어느 연결 위치를 바꿨는지 실제 문장·오류와 연결. 모든 필터 변화가 오류라고 일반화하지 않음 |

브라우저에서 화면 동작과 문안을 대조한 것이며 실제 초보자 참여 시험·학습 효과 검증은 아니다. 이번 후속 단계에서는 실행 코드를 추가로 수정하지 않았다.

## 현재 상태와 남은 일

- SQL 두 건의 로컬 수정·자동 검사 완료. 위 6개 SQL 사례와 수정 두 건의 실제 브라우저 화면 대조 완료. 이해도·실제 초보자 시험은 미실시다.
- 다른 유형의 #19 문안 검토, Easy/Normal 학습 흐름 전체, 터미널 원문/Lens/TUI 대조는 후속 단계다.
- #19 전체 완료·#13/#22 검증 완료·보안 개선·공개 승인을 의미하지 않는다. 이슈 체크박스나 종료 상태를 바꾸지 않았다.
- 시작 댓글: https://github.com/ts825360/-PayloadLab-/issues/19#issuecomment-6412299651
- 사용자 문안·diff 검토 전에는 커밋·push·PR·main 반영을 진행하지 않는다. 아직 공유할 커밋/PR 링크는 없다.
