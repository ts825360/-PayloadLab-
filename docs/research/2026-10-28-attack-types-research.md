# 공격 유형 조사 요약

연결 이슈: #14 SQL Injection · #15 Reflected XSS · #16 IDOR · #17 SSRF · #18 리눅스 명령어 퀴즈
관련 이슈: #2 기획·범위·발표 자료 허브 · #5 초기 보안 유형·난이도·학습 경계 확정

> 공격 유형별 조사 문서 네 개의 핵심만 모은 요약입니다. 자세한 근거, Lens 규칙 후보, 출처는 각 문서를 봅니다.
> 실제 대상 시스템의 민감한 정보는 기록하지 않습니다.

## 결론

- 첫 버전은 SQL Injection, Reflected XSS, IDOR 세 유형을 **기초·중급 2단계**로 다룹니다.
- 공통 학습 목표는 두 가지입니다. "입력 하나가 결과를 어떻게 바꾸는가", 그리고 "방어 코드에서는 왜 막히는가"입니다.
- DreamHack이 "소스 코드를 읽고 직접 풀어 플래그 얻기"라면, PayloadLab은 그 전 단계인 "입력이 어디로 들어가는지 그림으로 보기"를 맡습니다.
- 포함·제외 범위의 최종 결정은 #5에서 확정합니다.

## 유형별 요약

| 유형 | 핵심 원리 | 기초 범위 | 중급 범위 | 방어 핵심 | 대응 DreamHack 문제 | 상세 문서 |
| --- | --- | --- | --- | --- | --- | --- |
| SQL Injection | 입력이 쿼리 문장에 붙어 WHERE 조건이 바뀜 | 따옴표로 문자열 닫기, 주석으로 조건 제거, `OR` 항상 참 | UNION으로 결과 합치기 | Prepared Statement | `simple_sqli`, `simple_sqli_chatgpt` | `2026-10-28-sqli-research.md` |
| Reflected XSS | 입력이 응답 HTML에 실려 브라우저가 코드로 해석 | 태그 해석, `<script>` 실행, `onerror` 이벤트 | 속성값 탈출, 단순 필터 우회 | 출력 위치에 맞는 이스케이프 | `xss-1`, `xss-2` | `2026-10-28-reflected-xss-research.md` |
| IDOR | 서버가 ID만 믿고 소유자 확인을 하지 않음 | URL·요청 본문 ID 변경 (수평 권한 상승) | 관리자 기능 직접 접근 (수직 권한 상승) | 요청마다 세션 사용자와 소유자 비교 | `Access Control 1·2: Dream NAS` | `2026-10-28-idor-research.md` |

## 첫 버전 제외 항목

| 제외 항목 | 이유 | 상세 문서 |
| --- | --- | --- |
| Blind SQLi, Error-based SQLi | 반복 요청·DB별 지식이 필요해 초보 범위를 넘음 | `2026-10-28-sqli-research.md` |
| 쿠키 탈취, 외부 전송, 관리자 봇 | 실제 공격 도구에 가까움 | `2026-10-28-reflected-xss-research.md` |
| Stored·DOM XSS, CSRF | Reflected XSS 위에 쌓이는 개념, 다음 단계 후보 | `2026-10-28-extension-candidates-research.md` |
| SSRF, Command Injection | 임의 URL·명령어 실행 금지 원칙과 충돌 | `2026-10-28-extension-candidates-research.md` |

## 다른 이슈와 맞출 점

- XSS 성공 판정 방식과 실행 격리: #36, #43
- IDOR 입력 화면 형식과 더미 ID 도달성: #8, #35
- Lens 규칙 연결 구조: #32
- SQL 실행 자원 제한: #42

## 상세 문서

- `2026-10-28-sqli-research.md`
- `2026-10-28-reflected-xss-research.md`
- `2026-10-28-idor-research.md`
- `2026-10-28-extension-candidates-research.md`
