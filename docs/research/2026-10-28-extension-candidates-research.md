# 공격 유형 조사: 확장 후보 유형 (첫 버전 제외)

연결 이슈: #17 [자료조사] SSRF 입문 학습 범위와 안전한 시뮬레이션 설계 · #18 [기획] 리눅스 명령어 빈칸 퀴즈의 학습 범위와 안전 모델 설계
관련 이슈: #2 기획·범위·발표 자료 허브 · #5 초기 보안 유형·난이도·학습 경계 확정

> 첫 버전(SQL Injection·Reflected XSS·IDOR) 이후 검토할 확장 후보 유형을 정리합니다.
> **출처의 사실**과 **팀의 해석**을 별도 소제목으로 구분합니다.
> 실제 대상 시스템의 민감한 정보는 기록하지 않습니다.

관련 문서:
- `2026-10-28-sqli-research.md`
- `2026-10-28-reflected-xss-research.md`
- `2026-10-28-idor-research.md`

## 1. 출처의 사실

- DreamHack 「웹 해킹 기초」 Path(Tier 1 Easy)는 9개 Unit으로 구성된다: XSS, CSRF, SSRF, Access Control, Command Injection, File Vulnerability, SQL Injection, NoSQL Injection, JWT.
- 확장 후보와 관련된 실습 문제: `csrf-1`, `csrf-2`, `web-ssrf`, `command-injection-1`.
- SSRF는 서버가 사용자가 준 URL로 대신 요청을 보내는 취약점이다.
- Command Injection은 입력이 셸 명령에 붙어 `;`, `&&` 등의 뒤가 별도 명령으로 실행되는 취약점이다.
- CSRF는 다른 사이트가 로그인된 사용자의 브라우저를 통해 요청을 대신 보내게 하는 취약점이다.

## 2. 팀의 해석

| 유형 | 첫 버전 제외 이유 | 다시 검토할 조건 |
| --- | --- | --- |
| Stored / DOM XSS | Reflected XSS 위에 쌓이는 개념 | Reflected XSS 시나리오 완성 후 첫 후보 |
| Blind SQL Injection | 반복 요청이 필요해 초보 범위를 넘음 | SQLi 중급까지 마친 사용자용 심화 과정으로 |
| CSRF | 사이트 2개와 로그인 상태가 필요해 흐름이 복잡함 | XSS 학습 흐름이 안정된 뒤 |
| SSRF | "임의 URL 실행 금지" 원칙과 충돌 | 가짜 내부 서버 응답만 보여 주는 방식이 가능할 때 |
| Command Injection (리눅스 명령어 퀴즈) | 실제 셸 실행은 안전 위험이 큼 | 실행 없이 명령 문자열 해석 결과만 그리는 시뮬레이터로 만들 수 있을 때 |

- 프로젝트 한눈에 보기 문서의 방침대로, SSRF와 리눅스 명령어 퀴즈는 첫 세 유형의 학습 흐름과 설명 품질을 확인한 뒤 진행 여부를 다시 결정합니다.


## 출처

- [DreamHack 웹 해킹 기초 Path](https://dreamhack.io/lecture/paths/web-hacking-fundamental)
