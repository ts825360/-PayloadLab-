# 공격 유형 조사: SQL Injection · Reflected XSS · IDOR

· 관련: #2 기획·범위·발표 자료 허브

> 공격 유형별 개념, 초보자 학습 범위, Lens 규칙 후보, 시나리오 근거를 정리합니다.
> 각 유형마다 **출처의 사실**과 **팀의 해석**을 별도 소제목으로 구분합니다.
> 실제 대상 시스템의 민감한 정보(실제 URL, 계정, 내부 주소 등)는 기록하지 않습니다. 예시는 모두 더미 값입니다.

## 요약

- 첫 버전은 SQL Injection, Reflected XSS, IDOR 세 유형을 **기초(1)·중급(2) 2단계**로 다룹니다.
- 각 유형의 공통 학습 목표는 "입력 하나가 결과를 어떻게 바꾸는가"와 "방어 코드에서는 왜 막히는가"입니다.
- 범위 근거는 공식 권고문·보안 자료의 개념 정의와 DreamHack 「웹 해킹 기초」 Path 문제 대조입니다.
- 범위 확정(포함/제외 결정)은 별도 결정 문서 `docs/decisions/`에서 다룹니다. 이 문서는 조사 근거만 남깁니다.

---

## 1. SQL Injection

### 1.1 출처의 사실

- 서버가 사용자 입력을 문자열 연결로 SQL 문장에 붙이면, 입력 속 작은따옴표(`'`)가 문자열을 닫고 그 뒤가 SQL 문법으로 해석된다.
- 근본 방어는 입력과 SQL 문장을 분리하는 매개변수화 쿼리(Prepared Statement)다. 입력 형식 검사(허용 목록), DB 계정 최소 권한, 오류 메시지 비노출은 보조 수단이다.
- DreamHack 「웹 해킹 기초」 Path의 SQL Injection Unit은 SQL Injection과 Blind SQL Injection 개념, 대응 방안을 다루며 실습 문제는 `simple_sqli`(로그인 쿼리 조작)이다. Lab에는 Subquery·Blind·Union 기반 SQLi가 포함된다.
- DreamHack `simple_sqli_chatgpt`는 입력 하나(`userlevel`)를 조작해 WHERE 조건을 바꾸는 구조다.
- DreamHack `error based sql injection`은 결과가 화면에 출력되지 않을 때 DB 오류 메시지로 정보를 얻는 문제이며, MySQL 함수 지식이 필요하다.

### 1.2 팀의 해석

**초보자 학습 범위**

| 단계 | 배울 것 | 예시 입력 (더미) | 난이도 |
| --- | --- | --- | --- |
| 1 | 따옴표로 문자열이 닫히는 원리 | `admin'` | 기초 |
| 2 | 주석으로 뒤 조건 제거 | `admin' -- ` | 기초 |
| 3 | 항상 참인 조건 | `' OR '1'='1` | 기초 |
| 4 | UNION으로 결과 합치기 (열 개수 맞추기) | `' UNION SELECT ...` | 중급 |

- 제외: Blind SQLi, Error-based SQLi, DB별 함수·시스템 테이블 조회. 반복 요청과 DB별 지식이 필요해 "원리 이해"라는 목표를 넘는다고 판단했습니다.

**Lens 규칙 후보**

| 규칙 ID | 감지 조건 | Lens가 보여 줄 설명 |
| --- | --- | --- |
| SQLI-01 | 입력에 `'`가 없음 | 입력이 아직 문자열 안에 갇혀 있어 SQL 문법으로 해석되지 않습니다. |
| SQLI-02 | `'`는 있으나 쿼리 문법 오류 | 따옴표 개수가 맞지 않아 쿼리가 깨진 위치를 표시합니다. |
| SQLI-03 | 문법은 맞지만 `AND pw=...` 조건이 남음 | 비밀번호 조건이 아직 살아 있습니다. 뒤 조건을 없애는 방법(주석)이 필요합니다. |
| SQLI-04 | UNION 사용, 열 개수 불일치 | 앞뒤 SELECT의 열 개수가 같아야 하는 이유를 설명합니다. |
| SQLI-05 | 성공 | 완성된 쿼리를 색으로 구분해 보여 주고, Prepared Statement 버전에서는 같은 입력이 실패하는 비교 화면을 띄웁니다. |

**시나리오 근거**

- 시나리오: 더미 로그인 화면에서 비밀번호 없이 `admin`으로 로그인하기.
- 근거: DreamHack `simple_sqli`·`simple_sqli_chatgpt`가 모두 로그인 조건 우회를 첫 문제로 삼고 있어, 초보자에게 가장 익숙한 형태로 판단했습니다. PayloadLab은 코드를 읽지 않아도 되도록 쿼리 변화를 그림으로 보여 주는 점에서 차별화합니다.

---

## 2. Reflected XSS

### 2.1 출처의 사실

- XSS는 공격자 입력이 웹 페이지에 삽입되어 브라우저에서 스크립트로 실행되는 클라이언트 사이드 취약점이다. 저장형(Stored), 반사형(Reflected), DOM 기반으로 나뉜다.
- 방어의 기본은 출력 위치(HTML 본문, 속성, JavaScript 등)에 맞는 출력 이스케이프다. 템플릿 엔진 자동 이스케이프, 쿠키 `HttpOnly`, CSP(Content Security Policy)가 보조 수단이다.
- DreamHack 「웹 해킹 기초」 Path의 XSS Unit은 XSS 이해와 방어를 다루며, 실습 문제는 `xss-1`, `xss-2`다. 두 문제는 스크립트 실행 후 관리자 봇의 쿠키를 얻는 구조다.

### 2.2 팀의 해석

**초보자 학습 범위**

| 단계 | 배울 것 | 예시 입력 (더미) | 난이도 |
| --- | --- | --- | --- |
| 1 | 입력이 HTML 태그로 해석됨 | `<b>hi</b>` | 기초 |
| 2 | 스크립트 태그 실행 | `<script>alert(1)</script>` | 기초 |
| 3 | 이벤트 속성으로 실행 | `<img src=x onerror=alert(1)>` | 기초 |
| 4 | 속성값 탈출, 단순 필터 우회 | `" onmouseover="alert(1)` | 중급 |

- 첫 버전은 원리가 가장 단순한 반사형만 다룹니다. Stored·DOM XSS는 반사형 위에 쌓이는 개념이라 다음 단계 후보로 둡니다.
- 제외: 쿠키 탈취, 외부 서버로 데이터 전송, 관리자 봇. 실제 공격 도구에 가깝다고 판단했습니다.

**Lens 규칙 후보**

| 규칙 ID | 감지 조건 | Lens가 보여 줄 설명 |
| --- | --- | --- |
| XSS-01 | 입력에 `<`가 없음 | 입력이 일반 글자로만 출력됩니다. 태그를 여는 문자가 필요합니다. |
| XSS-02 | 태그는 해석되나 실행 코드 없음 | 입력이 HTML로 해석된 부분을 강조하고, 실행 가능한 위치가 아직 없다고 알려 줍니다. |
| XSS-03 | `<script>`가 필터에 막힘 | 스크립트 태그 대신 이벤트 속성(`onerror` 등)으로도 실행될 수 있음을 설명합니다. |
| XSS-04 | 속성값 안에 갇힘 | 따옴표로 속성이 닫히는 위치를 표시합니다. |
| XSS-05 | 성공 | 브라우저가 실행 영역으로 바꾼 지점을 보여 주고, 이스케이프 버전에서 `&lt;`로 바뀌어 실행되지 않는 비교 화면을 띄웁니다. |

**시나리오 근거**

- 시나리오: 더미 검색 페이지에서 `alert` 창 띄우기.
- 근거: DreamHack `xss-1`·`xss-2`도 "입력이 페이지에 그대로 실린다"는 반사형 구조에서 출발합니다. 다만 쿠키 탈취 단계는 PayloadLab의 "하지 않을 것"과 충돌하므로, 실행 성공 여부만 판정합니다.
- 안전 메모: 실제 스크립트를 실행하지 않고 "실행되었을 위치"를 판정하는 방식, 또는 샌드박스 iframe 안에서만 실행하는 방식을 시나리오·백엔드 담당(#8), 안전 담당(#6, #12)과 협의해야 합니다.

---

## 3. IDOR (Insecure Direct Object Reference)

### 3.1 출처의 사실

- IDOR는 애플리케이션이 사용자가 보낸 식별자(ID)로 내부 자료에 바로 접근하면서 추가 권한 확인을 하지 않을 때 생기는 접근 제어 결함이다. URL의 숫자 하나만 바꿔 다른 사용자의 자료를 볼 수 있는 경우가 대표적이다. (CISA·호주 ACSC 공동 권고문, 2023)
- 같은 권고문은 IDOR를 수평(같은 권한의 다른 사용자 자료 접근), 수직(더 높은 권한의 자료·기능 접근), 객체 수준, 기능 수준으로 분류한다.
- IDOR는 OWASP Top 10의 Broken Access Control에 속하며, MITRE CWE-639("사용자 제어 키를 통한 권한 우회")로 추적된다.
- ID를 UUID처럼 추측하기 어렵게 바꾸는 것만으로는 막을 수 없다. ID가 다른 경로로 노출되면 취약점은 그대로 남는다. (Wiz)
- DreamHack 「웹 해킹 기초」 Path에는 "IDOR"라는 이름의 문제는 없으며, Access Control Unit의 `Access Control 1: Dream NAS`(수평 권한 상승), `Access Control 2: Dream NAS`(수직 권한 상승)가 대응한다.
- DreamHack `cookie`, `session-basic`은 클라이언트가 보낸 쿠키 값을 서버가 그대로 믿어 관리자로 인식되는 문제다.

### 3.2 팀의 해석

**초보자 학습 범위**

| 단계 | 배울 것 | 예시 입력 (더미) | 난이도 |
| --- | --- | --- | --- |
| 1 | URL 파라미터 ID 변경 (수평 권한 상승) | `student_id=1001` → `1002` | 기초 |
| 2 | 요청 본문 속 숨은 ID 변경 | `user_id=7` → `8` | 기초 |
| 3 | 관리자 기능 직접 접근 (수직 권한 상승) | `/admin/users` 직접 요청 | 중급 |

- IDOR는 "공격 문장"이 아니라 "요청 값 변경"이 핵심입니다. 입력칸 대신 요청 편집 화면(URL·파라미터 수정 칸)이 필요하므로 화면 담당(#7)과 협의가 필요합니다.
- `cookie`·`session-basic`은 "클라이언트가 보낸 값을 믿는다"는 같은 원리이므로, IDOR 설명의 비교 예시로 활용할 수 있습니다.

**Lens 규칙 후보**

| 규칙 ID | 감지 조건 | Lens가 보여 줄 설명 |
| --- | --- | --- |
| IDOR-01 | ID를 바꾸지 않음 | 지금은 내 자료만 보입니다. 요청에 실린 ID 값을 찾아보세요. |
| IDOR-02 | 존재하지 않는 ID로 변경 | 해당 ID의 자료가 없습니다. 다른 사용자의 ID 형식을 추측해 보세요. |
| IDOR-03 | 다른 사용자 자료 조회 성공 | 로그인한 사용자와 조회된 자료 주인이 다르다는 점을 나란히 보여 주고, 서버에 소유자 확인(`WHERE id=? AND owner_id=세션사용자`)이 빠져 있음을 설명합니다. |
| IDOR-04 | 관리자 경로 접근 성공 | 역할(role) 확인이 빠진 위치를 표시합니다. |
| IDOR-05 | 방어 버전 비교 | 같은 요청이 소유자 확인 코드에서 "권한 없음"으로 막히는 화면을 띄웁니다. |

**시나리오 근거**

- 시나리오: 더미 "내 성적 조회" 페이지에서 학번 파라미터를 바꿔 다른 더미 학생 성적 보기.
- 근거: 권고문의 대표 예시(URL ID 변경)와 DreamHack `Access Control 1`의 수평 권한 상승 구조가 같아, 첫 단계로 가장 적합하다고 판단했습니다. 대학생 사용자에게 익숙한 "성적 조회" 맥락을 택했습니다.

---

## 4. 확장 후보 유형 (첫 버전 제외)

### 4.1 출처의 사실

- DreamHack 「웹 해킹 기초」 Path는 XSS, CSRF, SSRF, Access Control, Command Injection, File Vulnerability, SQL Injection, NoSQL Injection, JWT의 9개 Unit으로 구성된다. 확장 후보 관련 문제는 `csrf-1`, `csrf-2`, `web-ssrf`, `command-injection-1`이다.

### 4.2 팀의 해석

| 유형 | 제외 이유 | 다시 검토할 조건 |
| --- | --- | --- |
| Stored / DOM XSS | Reflected XSS 위에 쌓이는 개념 | Reflected XSS 시나리오 완성 후 첫 후보 |
| Blind SQL Injection | 반복 요청이 필요해 초보 범위를 넘음 | SQLi 중급까지 마친 사용자용 심화 과정으로 |
| CSRF | 사이트 2개와 로그인 상태가 필요해 흐름이 복잡함 | XSS 학습 흐름이 안정된 뒤 |
| SSRF | "임의 URL 실행 금지" 원칙과 충돌 | 가짜 내부 서버 응답만 보여 주는 방식이 가능할 때 |
| Command Injection (리눅스 명령어 퀴즈) | 실제 셸 실행은 안전 위험이 큼 | 실행 없이 명령 문자열 해석 결과만 그리는 시뮬레이터로 만들 수 있을 때 |

---

## 5. DreamHack과 PayloadLab의 역할 차이 (팀의 해석)

- DreamHack은 소스 코드를 읽고 직접 공격해 플래그를 얻는 것이 목표이며, Python·Flask 기초를 선수 지식으로 둡니다.
- PayloadLab은 코드를 몰라도 입력이 어디에 들어가 결과를 어떻게 바꾸는지 그림으로 보여 주는 것이 목표입니다.
- 따라서 PayloadLab은 DreamHack 문제를 풀기 전 단계, 또는 풀다 막혔을 때 원리를 확인하는 단계를 맡습니다.



## 출처

- [DreamHack 웹 해킹 기초 Path](https://dreamhack.io/lecture/paths/web-hacking-fundamental) — Unit 구성, 실습 문제 목록- [DreamHack XSS Unit](https://dreamhack.io/lecture/units/webhacking-xss)
- [DreamHack Access Control Unit](https://dreamhack.io/lecture/units/access-control-basic)
- [DreamHack SQL Injection Unit](https://dreamhack.io/lecture/units/webhacking-sql-injection)
- [CISA·호주 ACSC 공동 권고문: Preventing Web Application Access Control Abuse (2023)](https://www.cisa.gov/sites/default/files/2023-07/aa23-208a_joint_csa_preventing_web_application_access_control_abuse.pdf)
- [Wiz: What is IDOR](https://www.wiz.io/ko-kr/academy/application-security/insecure-direct-object-reference-idor)
- [simple_sqli_chatgpt 풀이 (velog)](https://velog.io/@yunaa/Dreamhack-simplesqlichatgpt-SQL-인젝션)
- [error based sql injection 풀이 (velog)](https://velog.io/@yunaa/Dreamhack-error-based-sql-injection)
- [cookie 풀이 (velog)](https://velog.io/@hui_/Dreamhack-cookie-풀이-31ljhv0v)
