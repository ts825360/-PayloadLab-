# 공격 유형 조사: SQL Injection

연결 이슈: #14 [자료조사] SQL Injection 입문 학습 시나리오와 Lens 규칙 설계
관련 이슈: #2 기획·범위·발표 자료 허브 · #5 초기 보안 유형·난이도·학습 경계 확정 · #42 API 입력과 SQL 실행의 자원 제한 보완

> SQL Injection의 개념, 초보자 학습 범위, Lens 규칙 후보, 시나리오 근거를 정리합니다.
> **출처의 사실**과 **팀의 해석**을 별도 소제목으로 구분합니다.
> 실제 대상 시스템의 민감한 정보는 기록하지 않습니다. 예시는 모두 더미 값입니다.

## 요약

- 학습 목표: 입력값이 쿼리 문장에 들어가면서 WHERE 조건이 바뀌는 원리를 이해합니다.
- 범위: 기초(따옴표·주석·OR 참 조건)와 중급(UNION) 2단계. Blind·Error-based SQLi는 제외합니다.
- 방어 핵심: 매개변수화 쿼리(Prepared Statement).

---

## 1. 출처의 사실

### 개념

- 서버가 사용자 입력을 문자열 연결로 SQL 문장에 붙이면, 입력 속 작은따옴표(`'`)가 문자열을 닫고 그 뒤가 SQL 문법으로 해석된다.
- 예: `SELECT * FROM users WHERE id='{입력}' AND pw='{입력}'`에 `admin' -- `을 넣으면 비밀번호 조건이 주석 처리된다.

### 방어 개념

- 근본 방어는 입력과 SQL 문장을 분리하는 매개변수화 쿼리(Prepared Statement)다.
- 보조 수단: 입력 형식 검사(허용 목록), DB 계정 최소 권한, 오류 메시지 비노출.
- 특정 문자만 지우는 블랙리스트 필터는 우회되기 쉬워 근본 해결이 아니다.

### DreamHack 관련 문제

- 「웹 해킹 기초」 Path의 SQL Injection Unit은 SQL Injection·Blind SQL Injection 개념과 대응 방안을 다루며, 실습 문제는 `simple_sqli`(로그인 쿼리 조작)다. Lab에는 Subquery·Blind·Union 기반 SQLi가 포함된다.
- `simple_sqli_chatgpt`: 입력 하나(`userlevel`)를 조작해 WHERE 조건을 바꾸는 구조다.
- `error based sql injection`: 결과가 화면에 출력되지 않을 때 DB 오류 메시지로 정보를 얻는 문제이며, MySQL 함수 지식이 필요하다.

## 2. 팀의 해석

### 초보자 학습 범위

| 단계 | 배울 것 | 예시 입력 (더미) | 난이도 |
| --- | --- | --- | --- |
| 1 | 따옴표로 문자열이 닫히는 원리 | `admin'` | 기초 |
| 2 | 주석으로 뒤 조건 제거 | `admin' -- ` | 기초 |
| 3 | 항상 참인 조건 | `' OR '1'='1` | 기초 |
| 4 | UNION으로 결과 합치기 (열 개수 맞추기) | `' UNION SELECT ...` | 중급 |

**제외:** Blind SQLi, Error-based SQLi, DB별 함수·시스템 테이블 조회. 반복 요청과 DB별 지식이 필요해 "원리 이해"라는 목표를 넘는다고 판단했습니다.

### Lens 규칙 후보

| 규칙 ID | 감지 조건 | Lens가 보여 줄 설명 |
| --- | --- | --- |
| SQLI-01 | 입력에 `'`가 없음 | 입력이 아직 문자열 안에 갇혀 있어 SQL 문법으로 해석되지 않습니다. |
| SQLI-02 | `'`는 있으나 쿼리 문법 오류 | 따옴표 개수가 맞지 않아 쿼리가 깨진 위치를 표시합니다. |
| SQLI-03 | 문법은 맞지만 `AND pw=...` 조건이 남음 | 비밀번호 조건이 아직 살아 있습니다. 뒤 조건을 없애는 방법(주석)이 필요합니다. |
| SQLI-04 | UNION 사용, 열 개수 불일치 | 앞뒤 SELECT의 열 개수가 같아야 하는 이유를 설명합니다. |
| SQLI-05 | 성공 | 완성된 쿼리를 색으로 구분해 보여 주고, Prepared Statement 버전에서는 같은 입력이 실패하는 비교 화면을 띄웁니다. |

### 시나리오 근거

- **시나리오:** 더미 로그인 화면에서 비밀번호 없이 `admin`으로 로그인하기.
- **근거:** DreamHack `simple_sqli`와 `simple_sqli_chatgpt`가 모두 로그인 조건 우회로 시작합니다. 그래서 초보자에게 가장 익숙한 형태로 판단했습니다.
- **차별점:** DreamHack은 소스 코드를 읽고 플래그를 얻는 것이 목표입니다. PayloadLab은 코드를 몰라도 쿼리가 어떻게 바뀌는지 그림으로 보여 줍니다.

## 3. 남은 질문

- [ ] UNION 단계를 첫 버전에 넣을지, 확장으로 미룰지 (#5에서 결정)
- [ ] Lens 규칙 SQLI-01~05를 조건 체인으로 어떻게 연결할지 (#32)
- [ ] 방어 개념을 OWASP SQL Injection Prevention Cheat Sheet 원문 링크로 보강

## 출처

- [DreamHack 웹 해킹 기초 Path](https://dreamhack.io/lecture/paths/web-hacking-fundamental)- [DreamHack SQL Injection Unit](https://dreamhack.io/lecture/units/webhacking-sql-injection)
- [simple_sqli_chatgpt 풀이 (velog)](https://velog.io/@yunaa/Dreamhack-simplesqlichatgpt-SQL-인젝션)
- [error based sql injection 풀이 (velog)](https://velog.io/@yunaa/Dreamhack-error-based-sql-injection)
