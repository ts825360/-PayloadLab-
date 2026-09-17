# PayloadLab 웹 보안 학습 콘텐츠 통합 정리

> 기존 `web_hacking_lens_learning.md`와 `PayloadLab_WebSecurity_6_Research.md` 두 문서를 하나로 통합한 버전입니다. 두 문서에서 겹치는 내용은 하나로 합쳤고, `web_hacking_lens_learning.md`에 정의된 **6가지 보안 취약점 분류를 기준**으로 재구성했습니다.

---

## 1. 프로젝트 방향 및 목표

PayloadLab은 웹 보안 지식이 없는 초보자가 웹 해킹을 직접 실습하고, **Lens 기능을 통해 "왜 이 공격이 성공했는지 / 왜 실패했는지"를 쉽게 이해할 수 있도록 하는 것**을 목표로 한다.

단순히 해킹 명령어나 Payload를 보여주는 것이 아니라 다음 흐름을 보여주는 것이 핵심이다.

```text
사용자 입력
    ↓
서버에서 어떻게 처리되는가?
    ↓
어떤 부분이 잘못되었는가?
    ↓
왜 공격이 성공하거나 실패하는가?
    ↓
어떻게 방어하는가?
```

> **핵심 방향**: Payload를 알려주는 사이트가 아니라, Payload가 왜 성공하거나 실패했는지 이해시켜주는 사이트.

Dreamhack의 웹 해킹 학습 구성을 참고하되, 초보자가 이해하기 어려운 고급 우회 기법은 제외하고 **EASY / MEDIUM** 두 단계로 구성한다.

- **EASY**: 취약점이 왜 발생하는지 기본 원리를 이해하는 단계 (공격 성공보다 원리 이해가 목표)
- **MEDIUM**: EASY에서 배운 원리를 이용해 조금 더 복잡한 상황(우회, 추론, 구조 분석 등)을 이해하는 단계

전체 사용자 경험 흐름:

```text
문제 → Payload 입력 → 실행 → 성공/실패/오류 판별
  → Lens 분석 → 왜 성공했는지·실패했는지 설명 → 코드 및 데이터 흐름 시각화
```

---

## 2. 프로젝트 범위 — 6가지 보안 취약점 (기준)

이번 프로젝트는 다음 6개 취약점을 핵심 범위로 한다.

```text
01. SQL Injection
02. XSS (Reflected XSS 중심)
03. IDOR / Access Control
04. JWT / Authentication
05. SSRF
06. Command Injection / Linux Shell
```

각 취약점은 다시 **EASY(기본 원리 이해)** / **MEDIUM(응용 및 복잡한 상황 이해)**로 나눈다.

---

## 3. Lens 설계 공통 규칙

모든 취약점에 동일한 6단계 구조를 적용한다.

```text
① Payload        — 사용자가 무엇을 입력했는가?
② Request         — 입력값이 서버에 어떻게 전달되었는가?
③ Vulnerable Point — 서버의 어느 부분에서 문제가 발생했는가?
④ Interpretation  — 입력값이 무엇으로 해석되었는가?
⑤ Result          — 왜 공격이 성공하거나 실패했는가?
⑥ Solution        — 어떻게 막을 수 있는가?
```

### 설명 방식 원칙

초보자에게는 전문 용어를 먼저 설명하지 않는다.

**나쁜 설명**
> 사용자 입력값이 SQL Query에 Injection되어 DBMS의 논리적 실행 흐름을 변조합니다.

**좋은 설명**
> 원래 이름을 입력해야 하는 칸에 SQL 명령처럼 해석될 수 있는 내용을 입력했습니다. 서버가 이 입력을 단순한 글자로 처리하지 않고 SQL 문장의 일부로 사용하면서 문제가 발생했습니다.

---

## 4. 취약점별 상세 정리

### 4.1 SQL Injection

**개념**: 사용자가 입력한 값이 원래 단순한 데이터로 사용되어야 하지만, SQL 문장의 일부로 해석되어 데이터베이스의 동작에 영향을 주는 취약점.

**주요 하위 유형**: Basic SQL Injection, Authentication Bypass, Boolean-based SQLi, UNION-based SQLi, Blind SQLi, Subquery-based SQLi, Error-based SQLi, Time-based SQLi, SQLi Filter/WAF Bypass, DBMS별 문법 차이(MySQL, SQLite 등)

#### EASY
- **학습 목표**: SQL Injection의 가장 기본적인 원리를 이해한다.
- **초보자가 막히는 부분**
  1. SQL이 무엇인지 모름
  2. 사용자가 입력한 값이 데이터베이스까지 전달된다는 것을 모름
  3. `'`, `OR`, `--` 등의 의미를 모름
  4. 정상적인 입력과 공격 입력의 차이를 이해하지 못함
  5. Payload를 입력했는데 왜 결과가 달라지는지, 실제 SQL Query가 어떻게 바뀌는지 모름
- **Lens에서 보여줄 것**

  ```text
  [사용자 입력] → [웹 서버: 입력값을 SQL Query에 삽입]
     → [생성된 Query ↔ 변경된 Query 비교] → [Database 실행] → [결과: 원래 의도와 다른 데이터 조회]
  ```

- **핵심 설명**: SQL Injection은 해커가 특별한 명령을 실행하는 것이 아니라, 원래 데이터로만 사용되어야 할 입력값이 SQL 문장의 일부로 해석되면서 발생하는 문제입니다.

#### MEDIUM
- **학습 목표**: Blind SQL Injection, UNION 등의 개념을 이해한다.
- **초보자가 막히는 부분**
  1. SQL 문장을 직접 이해해야 함
  2. 결과가 화면에 바로 나오지 않는 경우가 있음
  3. 참/거짓 결과만으로 정보를 추론해야 함
  4. UNION의 컬럼 개념을 이해해야 함
  5. 데이터베이스 구조 및 DBMS별 문법 차이를 어느 정도 알아야 함
  6. SQL 문법 오류와 공격 실패를 구분하지 못함
- **Lens에서 보여줄 것**

  ```text
  입력값 → SQL Query → Query 결과가 직접 표시되지 않음
     → 참/거짓 또는 응답 차이 발생 → 응답을 비교하여 정보 추론
  ```

- **핵심 설명**: EASY에서는 공격 결과를 눈으로 확인했다면, MEDIUM에서는 화면에 정보가 직접 나타나지 않아 서버의 반응 차이를 이용해 정보를 추론해야 합니다.

---

### 4.2 XSS (Reflected XSS 중심)

**개념**: 사용자가 입력한 내용이 단순한 문자로 출력되지 않고 HTML 또는 JavaScript 코드로 해석되어 실행되는 취약점. Reflected XSS, Stored XSS, DOM-based XSS로 구분하여 학습한다.

**주요 하위 유형**: Script Tag, HTML Tag, Event Handler, Attribute Escape, HTML Context, JavaScript Context, HTML Entity Encoding, Filter Bypass, CSP 우회

#### EASY
- **학습 목표**: 입력한 문자열이 웹페이지에서 코드로 실행될 수 있다는 사실을 이해한다.
- **초보자가 막히는 부분**
  1. HTML과 JavaScript의 차이를 모름
  2. 입력한 문자열이 페이지에 다시 출력되는 과정을 모름
  3. `<script>` 같은 태그가 왜 실행되는지 모름 (단순히 `<script>alert(1)</script>`만 넣으면 된다고 생각함)
  4. 서버가 데이터를 저장하는 것과 브라우저가 실행하는 것을 구분하지 못함
  5. Payload가 들어가는 위치(Context, 예: HTML Context vs Attribute Context)의 중요성을 모름
  6. HTML/JavaScript Encoding 때문에 Payload가 실행되지 않는 이유를 모름
- **Lens에서 보여줄 것**

  ```text
  사용자 입력 → 입력 위치(Context) 확인 → 서버가 입력값을 페이지에 출력
     → 브라우저가 HTML로 해석 → JavaScript 실행 → XSS 발생 / 실패 원인
  ```

- **핵심 설명**: 문제는 입력 자체가 아니라, 입력한 내용을 안전하게 처리하지 않고 웹페이지 코드로 해석하게 만든 것입니다.
- **Easy 추천**: 입력값을 넣고 바로 결과 페이지에서 실행되는 **Reflected XSS**가 초보자에게 가장 직관적이므로 우선 사용한다.

#### MEDIUM
- **학습 목표**: Reflected XSS에서 Stored XSS 또는 DOM XSS로 개념을 확장한다.
- **초보자가 막히는 부분**
  1. 입력값이 저장되는 위치를 이해하기 어려움
  2. 공격자와 피해자의 관계를 이해해야 함
  3. 서버가 아니라 브라우저의 JavaScript에서 문제가 발생하는 경우가 있음
  4. HTML/JavaScript/DOM의 관계를 이해해야 함
  5. Reflected XSS와 Stored/DOM XSS를 혼동함
- **Lens에서 보여줄 것 (Stored XSS 예시)**

  ```text
  공격자 입력 → 서버/DB에 저장 → 피해자가 페이지 접속
     → 저장된 입력값 출력 → 브라우저에서 실행
  ```

- **핵심 설명**: Reflected XSS는 입력한 내용이 바로 돌아오는 방식이고, Stored XSS는 입력한 내용이 서버에 저장된 뒤 다른 사용자가 페이지를 볼 때 실행되는 방식입니다.

---

### 4.3 IDOR / Access Control

**개념**: 사용자가 접근할 수 있는 권한을 서버가 제대로 확인하지 않아 다른 사용자의 데이터나 기능에 접근할 수 있는 취약점. Horizontal Privilege Escalation과 Vertical Privilege Escalation을 학습한다.

**주요 하위 유형**: User ID Manipulation, Numeric ID Manipulation, Sequential ID Guessing, Query Parameter Manipulation, Path Parameter Manipulation, POST Parameter Manipulation, JSON Parameter Manipulation, 수평 권한 상승, 수직 권한 상승

#### EASY
- **학습 목표**: "내가 요청한 데이터인지"를 서버가 제대로 확인하지 않으면 문제가 발생한다는 것을 이해한다.
- **초보자가 막히는 부분**
  1. URL의 숫자나 ID가 단순한 값이라고 생각함
  2. 권한 검사가 서버에서 이루어진다는 것을 모름
  3. 로그인(Authentication)과 권한(Authorization)이 같은 개념이라고 생각함
  4. 다른 사용자의 데이터에 접근하는 것이 왜 가능한지 이해하지 못함
  5. GET 요청만 생각하고 POST/JSON/Path 파라미터 변조는 생각하지 못함
- **Lens에서 보여줄 것**

  ```text
  사용자 → 요청 (Path/Query/POST/JSON 등 다양한 경로 가능)
     → 서버가 확인한 권한 (❌ 검증 누락 시) → 데이터 반환
  ```

- **핵심 설명**: 로그인했다고 해서 모든 데이터에 접근할 수 있는 것은 아닙니다. 서버가 "이 사용자가 이 데이터에 접근할 권한이 있는지" 확인해야 합니다.

#### MEDIUM
- **학습 목표**: 수평적 권한 상승과 수직적 권한 상승을 구분한다.
- **초보자가 막히는 부분**: 수평적 권한 상승(같은 수준의 다른 사용자 데이터 접근)과 수직적 권한 상승(일반 사용자가 관리자 기능에 접근)을 헷갈리기 쉬움
- **Lens에서 보여줄 것**

  ```text
  [수평] user A → user B 데이터 접근 → 권한 검사 실패
  [수직] user → admin 기능 요청 → 권한 검사 실패
  ```

- **핵심 설명**: 수평은 같은 수준의 다른 사람에게 접근하는 것이고, 수직은 자신의 권한보다 높은 기능에 접근하는 것입니다.

---

### 4.4 JWT / Authentication

**개념**: 사용자가 로그인한 상태인지 확인하고 어떤 권한을 가지고 있는지 판단하는 인증 및 권한 관리 과정에서 발생하는 문제. 초보자에게는 Cookie, Session, Token 등 기본 인증 흐름을 먼저 설명한 뒤 JWT를 연결하는 것이 좋다.

**주요 하위 유형**: Header Manipulation, Payload Manipulation, Claim Manipulation(role/admin claim 변경), exp/nbf/iat/iss/sub 변조, alg=none, Algorithm Confusion, Signature 검증 우회, JWT Reuse, Authentication Bypass

#### EASY
- **학습 목표**: "로그인 상태를 서버가 어떻게 기억하는가?"를 이해한다.
- **초보자가 막히는 부분**
  1. 로그인하면 서버가 무엇을 기억하는지 모름
  2. Cookie/Session/Token의 차이를 모름
  3. JWT가 단순히 암호화된 문자열이라고 생각함
  4. 인증(Authentication)과 권한(Authorization)을 혼동함
- **Lens에서 보여줄 것**

  ```text
  로그인 → 인증 정보 생성 → Cookie/Token 전달
     → 다음 요청에서 인증 정보 전송 → 서버가 사용자 확인 → 페이지 접근
  ```

- **핵심 설명**: 로그인은 한 번만 하는 것처럼 보이지만, 실제로는 이후 요청에서도 서버가 사용자를 확인할 수 있도록 인증 정보를 주고받습니다.

#### MEDIUM
- **학습 목표**: JWT의 구조(`Header.Payload.Signature`)와 인증 정보 검증 과정을 이해한다.
- **초보자가 막히는 부분**
  1. Header / Payload / Signature / exp / role / 검증 등의 개념을 한 번에 이해하기 어려움
  2. Base64URL Encoding과 암호화를 혼동함
  3. Payload를 수정해도 Signature 검증 때문에 실패할 수 있다는 것을 모름
  4. JWT의 Algorithm과 Signature 검증 과정을 이해하지 못함
- **Lens에서 보여줄 것**

  ```text
  JWT ── Header / Payload / Signature
     → Claim 변경 → 서버가 Token 검증(Signature) → 사용자 확인
     → 권한 확인 → 접근 허용/거부
  ```

- **핵심 설명**: JWT는 로그인 정보를 담아 전달하는 하나의 방법입니다. 중요한 것은 JWT 안에 무엇이 들어 있는지만 보는 것이 아니라 서버가 그 정보를 제대로 검증하는지입니다.

---

### 4.5 SSRF

**개념**: 사용자가 지정한 URL 등을 서버가 대신 요청하도록 만들어 서버가 접근할 수 있는 내부 또는 외부 자원에 요청하게 하는 취약점.

**주요 하위 유형**: Basic SSRF, localhost/127.0.0.1 접근, Private IP, Internal Network/Service, Port Manipulation, IP Representation Bypass, URL Encoding, Double Encoding, Redirect, URL Filter Bypass, IPv4/IPv6 변형

#### EASY
- **학습 목표**: "사용자가 요청하는 것"과 "서버가 대신 요청하는 것"의 차이를 이해한다.
- **초보자가 막히는 부분**
  1. 브라우저가 직접 요청하는 것과 서버가 요청하는 것을 구분하지 못함
  2. URL을 입력했을 뿐인데 왜 서버가 요청하는지 이해하지 못함
  3. localhost / 내부 서버의 개념이 없음
  4. 서버의 네트워크 위치를 생각하지 못함
- **Lens에서 보여줄 것**

  ```text
  사용자 → URL 입력 → 웹 서버 → "사용자가 입력한 URL로 요청"
     → 내부 서버 / 외부 서버 → 응답 반환
  ```

- **핵심 설명**: SSRF는 사용자가 서버에게 "이 주소로 대신 가줘"라고 요청하는 것에서 시작합니다. 서버가 접근할 수 있는 주소라면 사용자가 직접 접근하지 못하는 곳에도 서버가 요청을 보낼 수 있습니다.

#### MEDIUM
- **학습 목표**: 서버가 접근할 수 있는 내부 자원과 URL 검증의 중요성을 이해한다.
- **초보자가 막히는 부분**
  1. localhost가 누구 기준인지 혼동함 (사용자 PC의 localhost ≠ 서버의 localhost)
  2. URL 필터링이 왜 필요한지 이해하지 못함
  3. 외부 요청과 내부 요청의 차이를 이해해야 함
  4. 필터를 우회하는 방법(Encoding, Double Encoding, IP 표현 변형 등)을 생각하기 어려움
- **Lens에서 보여줄 것**

  ```text
  사용자 PC의 localhost ≠ 서버의 localhost

  사용자 → 웹 서버 → localhost 요청 → 서버 자신의 내부 서비스 접근
  ```

- **핵심 설명**: localhost는 항상 "현재 내 컴퓨터"를 의미하는 것이 아닙니다. 서버가 localhost로 요청하면 서버 자신의 localhost에 요청하는 것입니다.

---

### 4.6 Command Injection / Linux Shell

**개념**: 웹 애플리케이션이 사용자의 입력값을 운영체제 명령어에 그대로 포함시키면서 공격자가 의도하지 않은 명령이 실행되는 취약점.

**주요 하위 유형**: Command Separator(`;`), Pipe(`|`), AND(`&&`), OR(`||`), Command Substitution(Backtick, `$()`), Newline, Shell Metacharacter, Whitespace Bypass, Encoding, Filter Bypass, Blind Command Injection

#### EASY
- **학습 목표**: 웹사이트의 입력값이 서버의 Linux 명령어와 연결될 수 있다는 것을 이해한다.
- **초보자가 막히는 부분**
  1. 웹사이트와 Linux가 연결되어 있다는 사실을 모름
  2. 서버에서 프로그램이 실행된다는 개념이 부족함
  3. Linux 명령어 자체가 익숙하지 않음
  4. `;`, `&&`, `|` 같은 명령어 연결 문자의 의미를 모름
- **Lens에서 보여줄 것**

  ```text
  사용자 입력 → 웹 서버 → Linux 명령어 생성 → Shell 실행 → 명령어 실행 → 결과 반환
  ```

- **핵심 설명**: 웹사이트의 입력값이 단순한 문자로 끝나는 것이 아니라 서버에서 실행되는 명령어에 포함되면 문제가 발생할 수 있습니다.

#### MEDIUM
- **학습 목표**: Shell에서 입력값이 어떻게 명령어와 결합되는지 이해한다.
- **초보자가 막히는 부분**
  1. Shell과 프로그램의 차이를 모름
  2. 명령어 연결 문자의 동작을 모름
  3. 입력값이 하나의 명령어가 아니라 여러 명령어로 해석되는 이유를 이해하지 못함
  4. 필터링과 입력 검증의 관계를 이해하기 어려움
  5. Command Injection과 단순 명령어 실행을 혼동함
  6. 결과가 화면에 나타나지 않는 Blind Command Injection 개념
- **Lens에서 보여줄 것**

  ```text
  원래 의도:            ping [사용자 입력]
  공격 입력이 포함된 경우: ping [사용자 입력] → Shell이 입력을 명령어로 해석 → 의도하지 않은 명령 실행
  ```

- **핵심 설명**: 서버가 사용자의 입력을 명령어의 일부로 사용할 때, 입력값이 단순한 데이터가 아니라 새로운 명령으로 해석될 수 있습니다.

---

## 5. 취약점별 한 문장 요약

| 취약점 | 초보자용 한 문장 | 가장 많이 막히는 부분 |
|---|---|---|
| SQL Injection | 입력한 내용이 데이터베이스 명령으로 해석되는 문제 | SQL 구조 + Query가 어떻게 변하는지 |
| XSS | 입력한 내용이 웹페이지의 코드로 실행되는 문제 | Context + Payload가 왜 실행되지 않는지 |
| IDOR | 내 권한으로 다른 사람의 데이터를 볼 수 있는 문제 | 인증과 인가의 차이 + Parameter 변조 |
| JWT / Authentication | 로그인 정보나 권한을 서버가 잘못 확인하거나 믿어서 생기는 문제 | Header/Payload/Signature 구조 + Claim/Signature 검증 |
| SSRF | 서버가 사용자를 대신해서 원하지 않는 곳에 요청하는 문제 | 서버가 대신 요청한다는 개념 + 내부 네트워크 |
| Command Injection | 입력한 내용이 서버의 명령어로 실행되는 문제 | Shell 문법 + Metacharacter + 명령어 연결 |

---

## 6. PayloadLab 설계 시 유의사항

Payload가 단순히 `SUCCESS / FAIL`만 보여주는 것에서 끝나지 않고, **왜 성공했는지 / 왜 실패했는지 / 어느 부분에서 막혔는지**를 보여주는 것이 중요하다.

| 취약점 | Lens가 강조해서 보여줄 것 |
|---|---|
| SQL Injection | 실제 Query가 어떻게 변했는지 |
| XSS | 어떤 Context에 입력되었는지 |
| IDOR | 인증된 사용자와 요청한 리소스의 권한 관계 |
| JWT | Token 구조, Claim 변경, Signature 검증 과정 |
| SSRF | 서버가 어떤 대상에게 요청했는지(요청 흐름) |
| Command Injection | Shell에서 입력값이 어떻게 해석되는지 |

Dreamhack에서 초보자가 문제를 풀며 막히는 부분을 PayloadLab의 Lens가 자동으로 설명해주는 방향으로 설계한다.

---

## 7. 최종 프로젝트 범위 요약

**핵심 목표는 Payload를 많이 외우게 하는 것이 아니라, 사용자가 "내가 입력한 값이 서버에서 어떻게 처리되었기 때문에 문제가 발생했는지"를 Lens를 통해 이해하도록 만드는 것이다.**

```text
01. SQL Injection                    — EASY: 기본 원리 / MEDIUM: Blind·UNION
02. XSS                              — EASY: Reflected 기초 / MEDIUM: Stored·DOM
03. IDOR / Access Control            — EASY: 권한 확인 부재 / MEDIUM: 수평·수직 권한 상승
04. JWT / Authentication             — EASY: 인증 흐름 / MEDIUM: JWT 구조·검증
05. SSRF                             — EASY: 서버 대리 요청 / MEDIUM: 내부 자원·URL 검증
06. Command Injection / Linux Shell  — EASY: 명령어 연결 / MEDIUM: 명령어 결합·필터 우회
```
