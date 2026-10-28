# 공격 유형 조사: IDOR

연결 이슈: #16 [자료조사] IDOR 입문 학습 시나리오와 Lens 규칙 설계
관련 이슈: #2 기획·범위·발표 자료 허브 · #5 초기 보안 유형·난이도·학습 경계 확정 · #35 [검증] IDOR 식별자 규칙 도달성 · #8 공통 실습 시나리오·입력 결과 계약 정리

> IDOR(Insecure Direct Object Reference)의 개념, 초보자 학습 범위, Lens 규칙 후보, 시나리오 근거를 정리합니다.
> **출처의 사실**과 **팀의 해석**을 별도 소제목으로 구분합니다.
> 실제 대상 시스템의 민감한 정보는 기록하지 않습니다. 예시는 모두 더미 값입니다.

## 요약

- 학습 목표: 특별한 문장 없이 ID 값 하나만 바꿔도 남의 자료가 보이며, 그 원인이 서버의 권한 확인 누락이라는 점을 이해합니다.
- 범위: 기초(URL·요청 본문 ID 변경, 수평 권한 상승)와 중급(관리자 기능 접근, 수직 권한 상승) 2단계.
- 방어 핵심: 모든 요청마다 서버가 세션 사용자와 자료 소유자를 비교합니다.

---

## 1. 출처의 사실

### 개념

- IDOR는 애플리케이션이 사용자가 보낸 식별자(ID)로 내부 자료에 바로 접근하면서 추가 권한 확인을 하지 않을 때 생기는 접근 제어 결함이다. (CISA·호주 ACSC 공동 권고문, 2023)
- 대표 예시는 URL의 ID 숫자 하나를 바꿔 다른 사용자의 거래 정보를 보는 경우다. (같은 권고문)
- 권고문은 IDOR를 수평(같은 권한의 다른 사용자 자료 접근), 수직(더 높은 권한의 자료·기능 접근), 객체 수준, 기능 수준으로 분류한다.
- IDOR는 OWASP Top 10의 Broken Access Control에 속하며, MITRE CWE-639("사용자 제어 키를 통한 권한 우회")로 추적된다. (Wiz)

### 방어 개념

- 핵심 방어는 서버가 요청마다 "요청한 사용자가 이 자료에 접근할 권한이 있는가"를 확인하는 것이다.
- ID를 UUID처럼 추측하기 어렵게 바꾸는 것만으로는 막을 수 없다. ID가 다른 경로로 노출되면 취약점은 그대로 남는다. (Wiz)

### DreamHack 관련 문제

- 「웹 해킹 기초」 Path에는 "IDOR"라는 이름의 문제가 없다.
- Access Control Unit의 `Access Control 1: Dream NAS`(수평 권한 상승)와 `Access Control 2: Dream NAS`(수직 권한 상승)가 대응한다.
- `cookie`, `session-basic`은 클라이언트가 보낸 쿠키 값을 서버가 그대로 믿어 관리자로 인식되는 문제다.

## 2. 팀의 해석

### 초보자 학습 범위

| 단계 | 배울 것 | 예시 입력 (더미) | 난이도 |
| --- | --- | --- | --- |
| 1 | URL 파라미터 ID 변경 (수평 권한 상승) | `student_id=1001` → `1002` | 기초 |
| 2 | 요청 본문 속 숨은 ID 변경 | `user_id=7` → `8` | 기초 |
| 3 | 관리자 기능 직접 접근 (수직 권한 상승) | `/admin/users` 직접 요청 | 중급 |

- IDOR는 "공격 문장"이 아니라 "요청 값 변경"이 핵심입니다. 입력칸 대신 요청 편집 화면(URL·파라미터 수정 칸)이 필요할 수 있어, 입력 형식을 #8 공통 시나리오 계약에서 정해야 합니다.
- `cookie`와 `session-basic`도 "클라이언트가 보낸 값을 믿는다"는 같은 원리입니다. 그래서 IDOR 설명의 비교 예시로 활용할 수 있습니다.
- **제외:** ID 패턴 추측 자동화, 인코딩·해시된 ID 분석, Blind IDOR(결과가 보이지 않는 경우). 초보 범위를 넘는다고 판단했습니다.

### Lens 규칙 후보

| 규칙 ID | 감지 조건 | Lens가 보여 줄 설명 |
| --- | --- | --- |
| IDOR-01 | ID를 바꾸지 않음 | 지금은 내 자료만 보입니다. 요청에 실린 ID 값을 찾아보세요. |
| IDOR-02 | 존재하지 않는 ID로 변경 | 해당 ID의 자료가 없습니다. 다른 사용자의 ID 형식을 추측해 보세요. |
| IDOR-03 | 다른 사용자 자료 조회 성공 | 로그인한 사용자와 조회된 자료 주인이 다르다는 점을 나란히 보여 줍니다. 서버에 소유자 확인(`WHERE id=? AND owner_id=세션사용자`)이 빠져 있다고 설명합니다. |
| IDOR-04 | 관리자 경로 접근 성공 | 역할(role) 확인이 빠진 위치를 표시합니다. |
| IDOR-05 | 방어 버전 비교 | 같은 요청이 소유자 확인 코드에서 "권한 없음"으로 막히는 화면을 띄웁니다. |

### 시나리오 근거

- **시나리오:** 더미 "내 성적 조회" 페이지에서 학번 파라미터를 바꿔 다른 더미 학생 성적 보기.
- **근거:** 권고문의 대표 예시(URL ID 변경)와 DreamHack `Access Control 1`의 수평 권한 상승 구조가 같습니다. 그래서 첫 단계로 가장 적합하다고 판단했습니다.
- **맥락 선택:** 대학생 사용자에게 익숙한 "성적 조회" 상황을 택했습니다. 성적·학번은 모두 더미 데이터입니다.


## 출처

- [CISA·호주 ACSC 공동 권고문: Preventing Web Application Access Control Abuse (2023)](https://www.cisa.gov/sites/default/files/2023-07/aa23-208a_joint_csa_preventing_web_application_access_control_abuse.pdf)
- [Wiz: What is IDOR](https://www.wiz.io/ko-kr/academy/application-security/insecure-direct-object-reference-idor)
- [DreamHack 웹 해킹 기초 Path](https://dreamhack.io/lecture/paths/web-hacking-fundamental)- [DreamHack Access Control Unit](https://dreamhack.io/lecture/units/access-control-basic)
- [cookie 풀이 (velog)](https://velog.io/@hui_/Dreamhack-cookie-풀이-31ljhv0v)
