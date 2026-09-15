# PayloadLab 웹 보안 6가지 조사 정리

## 1. 조사 목적

PayloadLab에서 다룰 웹 보안 범위는 총 6가지이다.

1.  SQL Injection
2.  Reflected XSS
3.  IDOR
4.  JWT
5.  SSRF
6.  Command Injection / Linux Shell

Dreamhack의 웹 해킹 강의 및 워게임을 참고하여 각 취약점에서 초보자가
어떤 부분에서 많이 막히는지 정리한다.

------------------------------------------------------------------------

## 2. SQL Injection

### 주요 유형

-   Basic SQL Injection
-   Authentication Bypass
-   Boolean-based SQLi
-   UNION-based SQLi
-   Blind SQLi
-   Subquery
-   Error-based SQLi
-   Time-based SQLi
-   SQLi Filter / WAF Bypass
-   DBMS별 문법 차이

### 초보자가 막히는 부분

-   SQL 문법 자체가 익숙하지 않음
-   Payload를 외워서 사용하고 왜 동작하는지 모름
-   Payload가 실제 SQL Query를 어떻게 바꾸는지 이해하지 못함
-   MySQL, SQLite 등 DBMS별 문법 차이를 모름
-   SQL 문법 오류와 공격 실패를 구분하지 못함

### PayloadLab에서 보여주면 좋은 것

``` text
입력값
  ↓
생성된 SQL Query
  ↓
변경된 Query
  ↓
DB 실행
  ↓
결과
```

------------------------------------------------------------------------

## 3. Reflected XSS

### 주요 유형

-   Script Tag
-   HTML Tag
-   Event Handler
-   Attribute Escape
-   HTML Context
-   JavaScript Context
-   HTML Entity Encoding
-   Filter Bypass
-   CSP 관련 우회

### 초보자가 막히는 부분

-   XSS를 단순히 `<script>alert(1)</script>`만 넣으면 되는 것으로 생각함
-   Payload가 들어가는 Context의 중요성을 모름
-   HTML Context와 Attribute Context의 차이를 모름
-   HTML/JavaScript Encoding 때문에 Payload가 실행되지 않는 이유를 모름
-   Reflected XSS와 Stored/DOM XSS를 혼동함

### PayloadLab에서 보여주면 좋은 것

``` text
현재 입력 위치(Context)
  ↓
입력값
  ↓
HTML/JS 처리 과정
  ↓
실제 브라우저 결과
  ↓
실패 원인
```

------------------------------------------------------------------------

## 4. IDOR

### 주요 유형

-   User ID Manipulation
-   Numeric ID Manipulation
-   Sequential ID Guessing
-   Query Parameter Manipulation
-   Path Parameter Manipulation
-   POST Parameter Manipulation
-   JSON Parameter Manipulation
-   수평 권한 상승
-   수직 권한 상승

### 초보자가 막히는 부분

-   Authentication(인증)과 Authorization(인가)의 차이를 모름
-   ID만 변경하는 것이 왜 취약점인지 이해하지 못함
-   GET 요청만 생각하고 POST/JSON/Path 등의 변조를 생각하지 못함
-   서버가 요청한 객체에 대한 권한을 확인해야 한다는 것을 모름

### PayloadLab에서 보여주면 좋은 것

``` text
현재 사용자
  ↓
요청한 ID
  ↓
서버가 확인한 권한
  ↓
반환된 데이터
  ↓
권한 검증 여부
```

------------------------------------------------------------------------

## 5. JWT

### 주요 유형

-   Header Manipulation
-   Payload Manipulation
-   Claim Manipulation
-   role/admin Claim 변경
-   exp / nbf / iat / iss / sub 변조
-   alg=none
-   Algorithm Confusion
-   Signature 검증
-   JWT Reuse
-   Authentication Bypass

### 초보자가 막히는 부분

-   JWT를 암호화된 문자열이라고 생각함
-   Header / Payload / Signature 구조를 모름
-   Base64URL Encoding과 암호화를 혼동함
-   Payload를 수정해도 Signature 검증 때문에 실패할 수 있다는 것을 모름
-   JWT의 Algorithm과 Signature 검증 과정을 이해하지 못함

### PayloadLab에서 보여주면 좋은 것

``` text
JWT
├── Header
├── Payload
└── Signature

Claim 변경
  ↓
Signature 검증
  ↓
인증 결과
```

------------------------------------------------------------------------

## 6. SSRF

### 주요 유형

-   Basic SSRF
-   localhost 접근
-   127.0.0.1
-   Private IP
-   Internal Network
-   Internal Service
-   Port Manipulation
-   IP Representation Bypass
-   URL Encoding
-   Double Encoding
-   Redirect
-   URL Filter Bypass
-   IPv4 / IPv6 변형

### 초보자가 막히는 부분

-   서버가 대신 요청한다는 개념을 이해하지 못함
-   localhost / 127.0.0.1의 의미를 모름
-   내부 네트워크와 Private IP 개념이 부족함
-   URL Filter가 왜 필요한지 이해하지 못함
-   필터를 우회하는 방법을 생각하기 어려움

### PayloadLab에서 보여주면 좋은 것

``` text
사용자
  ↓
취약한 웹 서버
  ↓
URL 검증
  ↓
서버의 HTTP 요청
  ↓
내부/외부 대상 서버
```

------------------------------------------------------------------------

## 7. Command Injection / Linux Shell

### 주요 유형

-   Command Separator (`;`)
-   Pipe (`|`)
-   AND (`&&`)
-   OR (`||`)
-   Command Substitution
-   Backtick
-   `$()`
-   Newline
-   Shell Metacharacter
-   Whitespace Bypass
-   Encoding
-   Filter Bypass
-   Blind Command Injection

### 초보자가 막히는 부분

-   Linux Shell 문법이 익숙하지 않음
-   `;`, `|`, `&&`, `||` 등의 차이를 모름
-   사용자 입력이 Shell 명령어와 결합되는 원리를 모름
-   Command Injection과 단순 명령어 실행을 혼동함
-   Shell Metacharacter가 어떤 역할을 하는지 모름

### PayloadLab에서 보여주면 좋은 것

``` text
사용자 입력
  ↓
기존 명령어
  ↓
Shell Parsing
  ↓
추가 명령어 실행
  ↓
실행 결과
```

------------------------------------------------------------------------

# 8. 6개 취약점별 핵심 막힘 지점

  취약점              초보자가 가장 많이 막히는 부분
  ------------------- -------------------------------------------------
  SQL Injection       SQL 구조 + Query가 어떻게 변하는지
  Reflected XSS       Context + Payload가 왜 실행되지 않는지
  IDOR                인증과 인가의 차이 + Parameter 변조
  JWT                 Header/Payload/Signature 구조 + Claim/Signature
  SSRF                서버가 대신 요청한다는 개념 + 내부 네트워크
  Command Injection   Shell 문법 + Metacharacter + 명령어 연결

------------------------------------------------------------------------

# 9. PayloadLab에 적용할 방향

Payload가 단순히 `SUCCESS / FAIL`인지 보여주는 것에서 끝나지 않고,

-   왜 성공했는지
-   왜 실패했는지
-   어느 부분에서 막혔는지

를 보여주는 것이 중요하다.

### SQL Injection

실제 Query가 어떻게 변했는지 보여준다.

### Reflected XSS

어떤 Context에 입력되었는지 보여준다.

### IDOR

인증된 사용자와 요청한 리소스의 권한 관계를 보여준다.

### JWT

Token 구조와 Claim 변경, Signature 검증 과정을 보여준다.

### SSRF

서버가 어떤 대상에게 요청했는지 요청 흐름을 보여준다.

### Command Injection

Shell에서 입력값이 어떻게 해석되는지 보여준다.

------------------------------------------------------------------------

# 10. 핵심 방향

> **Payload를 알려주는 사이트가 아니라, Payload가 왜 성공하거나
> 실패했는지 이해시켜주는 사이트**

Dreamhack에서 초보자가 문제를 풀면서 막히는 부분을 PayloadLab의 Lens가
자동으로 설명해주는 방향으로 설계하는 것이 좋다.

``` text
문제
  ↓
Payload 입력
  ↓
실행
  ↓
성공 / 실패 / 오류 판별
  ↓
Lens 분석
  ↓
왜 성공했는지 / 왜 실패했는지 설명
  ↓
코드 및 데이터 흐름 시각화
```

이렇게 구성하면 단순 Payload 데이터베이스가 아니라 **웹 해킹 입문자가
공격 원리를 이해하도록 돕는 실습형 학습 플랫폼**으로 발전시킬 수 있다.
