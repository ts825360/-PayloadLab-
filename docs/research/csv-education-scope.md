# #19 CSV 교육 범위와 현재 실습의 연결 — 2026-10-27

담당: 이수웅(dtd2428), AI 보조. 관련: [#19](https://github.com/ts825360/-PayloadLab-/issues/19), [데이터 안내](../datasets/payloads-all-the-things/README.md).
검토 기준 로컬 커밋: fd106c93c4c37375bcc43aca4249dceea0dbeb12. 이 커밋은 터미널 수정분이며 CSV 후속 문서는 검증 당시 미커밋이었다. 이후 사용자 진행 승인에 따라 이 문서를 포함하는 로컬 커밋으로 보관한다. 실제 SHA는 git log로 확인하며 push는 별도다.

최신 후속 확인: [Git 원문 기준 출처·기존 생성기 재생성2개 검사](../verification/2026-10-27-csv-snapshot-verification.md)가 통과했다. 원문 파일 복구나 작업 폴더 기반7개 검사 전체 통과와는 구분한다.

## 검토 결과

CSV는 입력·문안을 설계할 때 참고하는 문서상 예시137행이다. 현재 프론트/백엔드는 이 CSV를 읽어 자동으로 공격을 판정하거나, 전 행을 실습에 실행하거나, 학습된 AI 모델로 사용하지 않는다. CSV를 추가했다고 현재13개 랩의 해석 범위가 넓어지는 것은 아니다.

교육 범위·라벨 문맥 검토와 Git 보관 원문 대조는 아래 범위에서 마쳤다. **작업 폴더 원문을 사용하는 재생성 검사는 미완료**다. 기존7개 검사 중5개 통과·2개 오류였으며 원문 파일1개의 읽기 실패/부재를 확인했다. 이를 전체 통과로 바꾸지 않는다.

## 유형별 범위

| CSV / 행 수 | 자료가 다루는 범위 | 현재 실습에서 연결할 설명 | 현재 실습 지원으로 단정하지 않을 범위 |
| --- | --- | --- | --- |
| SQL /37 | 공격28·정상8·문맥 미정1. common, MySQL, MSSQL, PostgreSQL, Oracle, SQLite | SQL Easy/Normal의 이름 값·따옴표·OR/AND·주석·고정 비밀번호·Normal 대문자 OR 제거. 실제 SQLite 조회 결과와 지원하는 작은 조건 그림을 구분 | DBMS 전용 함수·버전/스키마 조회·오류 기반/블라인드·UNION 예시 전체를 현재 로그인 과제나 조건 그림이 해석/성공한다는 주장 |
| XSS /33 | 공격24·정상8·문맥 미정1. script 태그·속성 탈출·이벤트 핸들러·URI·필터 변형 | HTML 본문에 검색어를 결합하는 위치, 일반 글자/표시 태그/코드, 소문자 필터 전후, 태그 형태 인식과 실제 미리보기 실행의 구분 | 현재 성공 규칙은 대소문자를 무시한 script 여는/닫는 형태 검사다. 이벤트 속성·javascript URI 등 모든 CSV 공격을 인식/실행 검증하는 탐지기가 아님 |
| CMDi /34 | 공격25·정상8·문맥 미정1. 명령 결합·치환·인자 주입·Bash/Windows/인코딩 변형 | Easy/Normal의 hostname→조립된 ping 문장→경계와 모의 stdout. 호스트 뒤 ; 또는 &&와 whoami/pwd/id 한 개만 모형화. Normal은 ; 포함 시 차단 | CSV의 command1/command2 자리표시자·치환·개행·디코딩·Windows/셸 전용 구문 전체. 실제 셸/프로세스/네트워크 실행 |
| SSRF /33 | 공격24·정상8·문맥 미정1. 메타데이터·루프백·내부/로컬 주소·IPv6·주소 변형 | URL 파싱과 hostname, 루프백용 더미 응답, Normal의 preview.lab.invalid 부분 문자열 정책을 비교 | 실제 DNS·HTTP·리다이렉트·클라우드 메타데이터·내부망 접근·각종 인코딩 주소 전부의 정규화/연결 결과 |
| IDOR / CSV 없음 | 객체번호·소유권 관계의 별도 고정 데이터 | 사용자1042, 주문1042/1043, 소유자1042/2001, Normal claimed_user_id를 실제 관계/응답과 연결 | CSV4개가 IDOR 학습/검증 데이터까지 제공한다는 주장 |
| Linux / CSV 없음 | 명령·옵션·경로 기초 퀴즈 | Easy 목록과 Normal 긴 목록의 고정 답·간략한 가상 출력 | CMDi CSV의 명령 단어를 Linux 퀴즈 공격 라벨이나 실제 OS 오류로 재사용 |
| 권한 / CSV 없음 | 가상 사용자·파일 소유자·허용 도우미의 고정 모형 | student/mentor/root, 읽기 거부, 가상 사용자 변화와 root의 보고서 읽기 목표를 구분 | CSV가 권한 상승 성공·실제 sudo·호스트 파일 접근을 검증한다는 주장. 권한 Normal은 계속 구현 예정 |

이 표는 코드와 문서의 교육 범위를 대조한 결과이며 CSV 전 행의 실제 실행 성공/실패 표가 아니다. CSV를 DB/브라우저/셸/목적지 URL에 일괄 연결하지 않았다.

## 라벨을 Lens 문안으로 옮길 때

- attack101행은 원문 시나리오의 공격 **시도**라는 문서상 라벨이다. 실제 랩 성공 여부나 입력자의 악의를 증명하지 않는다. 현재 모형이 문법 오류·미지원·차단을 반환해도 라벨을 임의로 benign으로 바꾸지 않는다.
- benign32행은 PayloadLab이 별도 작성한 input_context 안의 정상 예시다. 예를 들어 SQL의 O'Reilly는 이름이라는 문맥이고 취약한 쿼리를 깨뜨린다고 자동으로 공격이 되지 않는다. XSS의 표시 태그 예시는 스크립트 실행과 구분한다. CMDi 자료의 whoami는 메모 문자열 문맥이며 모든 입력칸에서 같은 뜻이 아니다.
- uncertain4행은 review_only다. 입력 문자열만으로 문맥·권한·정책이 정해지지 않으므로 이진 정답이나 성공 판정으로 쓰지 않는다.
- ssrf-attack-002와 ssrf-uncertain-001은 같은 http://localhost:80 문자열이다. 전자는 공개 목적지만 허용한다는 시도 문맥, 후자는 정책이 미지정인 문맥이다. 문자열만 보는 분류에서는 충돌하므로 문맥을 보존한다. 이를 검토 없이 중복 삭제하거나 한쪽 라벨로 덮어쓰지 않는다.
- Lens는 CSV 라벨을 화면 결과로 복사하지 않고, 현재 입력 위치·필터/비교·실제 trace·다음 관찰을 설명해야 한다. family_id와 출처/라벨 메타데이터는 향후 학습 분리·누수 검토 대상이며 현재 모델 학습·정확도 검증은 수행하지 않았다.

## 원문·manifest 대조

[검토 스크립트](../verification/scripts/csv_scope_review.py)는 payload를 문자열로만 읽고, CSV14개 컬럼·137개 고유 ID·필수 문맥/라벨 근거·validation_status·라벨별 개수를 대조한다.

| 검증 | 결과와 한계 |
| --- | --- |
|4개 CSV /137행 | SQL37·XSS33·CMDi34·SSRF33, attack101·benign32·uncertain4. 형식·BOM·고유 ID·필수 메타데이터 일치 |
|공격/문맥 미정 출처105건 | Git 보관 원문의 바이트 부분 문자열·SHA-256·줄 번호·고정 commit URL과 manifest 일치 |
|원문10개 | Git 보관 blob의 SHA-256이 manifest와 모두 일치. 현재 작업 폴더에서는9개만 읽기 가능 |
|CSV4개와 manifest | 현재 바이트가 기준 로컬 커밋과 동일. 라벨/내용/위치/해시를 수정하지 않음 |
|validation_status /license | 모든 행의 documentation_reviewed_not_executed·MIT 메타데이터 유지. 이 검사는 실행 유효성이나 법적 판단이 아님 |
|원격 원본 조회 | 이번에는 고정 원문의 로컬/Git 보관본 대조만 수행. 상위 저장소 원격 바이트의 별도 재인증·최신 버전 추적은 하지 않음 |
|기존 데이터 검사7개 |5개 통과·원문 대조/오프라인 재생성2개 오류. 전체 통과 아님 |

[행별 메타데이터·분포·Git 출처 근거·누락 상태](../verification/2026-10-27-csv-scope-audit.json), [감사 요약](../verification/evidence/2026-10-27-csv-scope-audit.txt), [기존 검사 실패 원문](../verification/evidence/2026-10-27-csv-scope-tests.txt).

## 작업 폴더 파일 부재와 남은 확인

기존 검사를 실행할 때 sources/SQL Injection__SQLite Injection.md가 Invalid argument 읽기 오류를 낸 뒤 파일이 없는 상태가 됐다. Get-MpThreatDetection에서 이 경로의 탐지 시각2026-10-27 16:27:32, 조치 상태 변경16:28:13, ActionSuccess=True, ThreatID2147891539를 확인했다. 자세한 조치 유형을 임의로 단정하지 않는다. Git 보관 blob은8703바이트이고 SHA-256은 manifest의 f6bad93117b22ac5575260d55967cb030f2780d8dcb70f5a9a5e16e82f1dbf36과 일치한다.

백신 예외 설정·비활성화·파일 복원은 하지 않았다. 이 파일의 삭제는 이번 작업의 코드 변경으로 취급해 stage/commit하지 않는다. 작업 폴더 원문을 확인할 수 있는 환경이 마련되면 기존7개 검사와 오프라인 재현을 다시 수행해야 한다. 그 전까지 원문/재생성 검증 완료로 체크하지 않는다.

재현:

    python docs/datasets/payloads-all-the-things/test_dataset.py -v
    python docs/verification/scripts/csv_scope_review.py

두 번째 스크립트도 현재는 검사 결과를 저장한 뒤 원문 미확인 상태를 나타내는 exit2로 끝난다. 실패를 숨기거나 파일 부재를 정상 처리하도록 기존 검사를 고치지 않았다.

CSV 교육 범위 검토와 별개로 실제 hover·실기기 터치·200% 확대, 본인·팀 최종 문안 검토, #19 전체 기준 확인은 남는다. 새 PR·main 반영·이슈 종료는 하지 않았다.


## 2차 검증 — 2026-10-27

현재 데이터 바이트와 교육 범위 표를 다시 대조했다. CSV4개·manifest는 기준 커밋과 여전히 동일했고 라벨/문자열을 수정하지 않았다. 원문 파일 부재도 계속 확인돼 기존 전체 검사의2개 오류를 해결된 것으로 기록하지 않는다.

### 검사 기준 보완

1. 출처 검사를 고정 commit 문자열과 줄 번호의 부분 일치에서 **정확한 전체 URL 일치**로 강화했다. GitHub 호스트·상위 저장소 경로·고정 커밋·원문 파일 경로·줄 번호를 함께 검사한다. 파일별 attack_type, ID의 유형/라벨 접두사, 허용 라벨·validation_status·정상 예시의 출처 공란도 확인한다. 실제 CSV에서 출처 불일치가 발견된 것은 아니다.
2. 감사 결과의 상태 의미를 바로잡았다. 원문이 모두 읽힌다는 사실만으로 오프라인 재생성이 완료됐다고 할 수 없으므로 working_copy_source_checks_complete와 working_copy_full_reproduction_complete를 분리했다. 이 스크립트는 재생성을 실행하지 않아 후자는False, offline_regeneration은not_run_by_scope_audit로 기록한다. 현재 전자는9/10 파일만 읽혀False다. 기존 실제 데이터 검사의 재생성 절차는 수정하지 않았다.

### 재검증 결과

- [새 메타데이터 계약 검사](../verification/scripts/test_csv_scope_review.py) **4개 통과**. 실제137행 통과, 출처 URL 변조525건(105행×호스트/경로/커밋/줄 번호/빈 값5종), 정상 예시의 거짓 출처32건, 잘못된 파일 유형137건을 모두 거부했다. 총694개의 반례이며 파일이나 URL 목적지에서 실행하지 않았다. [실행 로그](../verification/evidence/2026-10-27-csv-second-contract-tests.txt).
- 기존 데이터 검사 중 원문 파일에 의존하지 않는 **5개만 선택해 재실행·통과**했다. 전체7개 통과가 아니다. [실행 로그](../verification/evidence/2026-10-27-csv-second-available-tests.txt).
- 강화한 감사 재실행에서137행·Git 원문10개·출처105건·CSV/manifest5파일 불변을 확인했다. 작업 원문은9/10, 전체 재현은 미완료로 보고하고 프로그램은exit2로 종료한다. [재실행 로그](../verification/evidence/2026-10-27-csv-second-audit.txt), [갱신한 JSON](../verification/2026-10-27-csv-scope-audit.json).
- SSRF의 동일 문자열에 서로 다른 라벨이 있는1개 묶음은 입력 문맥이 다른 자료임을 재확인했다. 해당 라벨을 바꾸거나 행을 삭제하지 않았다.
- 원문 복원·보안 설정 변경·CSV 일괄 실행·새 모델 학습·실습 코드 수정은 하지 않았다. 따라서 앱의 이전113개/빌드를 이번에 재실행한 것처럼 세지 않는다.

재현:

    python docs/verification/scripts/test_csv_scope_review.py -v
    python docs/verification/scripts/csv_scope_review.py

이2차 검증 당시에는 미커밋·미push였고 이후 로컬 commit은 상단 승인 상태를 따른다. SQLite 작업 원문 확인·재생성2개 검사, 실제 hover·터치·확대와 본인·팀 최종 검토는 여전히 남아 있다.
