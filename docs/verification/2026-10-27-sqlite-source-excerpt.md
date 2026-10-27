# #19 SQLite 참고 원문 부재 처리 — 2026-10-27

관련: [#19](https://github.com/ts825360/-PayloadLab-/issues/19), [이전 Git 보관본 검증](2026-10-27-csv-snapshot-verification.md).
담당: 이수웅(dtd2428), AI 보조. 기존 원문 보관 기준(공통 main 조상): 23b05593b73f6d9c9556eecd68abad5fbb8f6801.

## 문제와 결과

전체 SQLite 참고 Markdown은 Windows Defender의 Backdoor:PHP/Perhetshell.A!dha 탐지·조치 뒤 작업 폴더에서 없어졌다. Get-MpThreat에서 IsActive=False·DidThreatExecute=False를 확인했다. 문서 안의 예시 탐지와 실제 실행을 구분하며 실제 침해라고 단정하지 않는다.

전체 문서를 복원하거나 보안 설정을 바꾸지 않고, 현재 CSV가 선택한 SQLite 메타데이터 조회문4개만 보관한 발췌본으로 교체했다. 이 파일에는 PHP 백도어 예시를 넣지 않았다. 현재 작업 폴더에서 읽기·일반 데이터 검사·오프라인 재생성이 가능해졌다.

## 보존한 내용과 변경점

- CSV4개의137행·payload·label·source_url·source_commit은 바이트 단위로 그대로다.
- 동일 경로의 SQLite Markdown 머리말에 전체 원문이 아닌 발췌본임을 명시했다. 보관한4개 SQL문은 원래 줄35/43/44/45에 놓았고 나머지 관련 없는 섹션은 생략했다.
- [발췌 출처 근거](../datasets/payloads-all-the-things/sources/SQL%20Injection__SQLite%20Injection.provenance.json)는 전체 원문 SHA-256·기존 Git 커밋·원래4개 바이트/줄 근거·새 발췌본 SHA-256을 연결한다.
- manifest는 새 발췌본의 실제 파일 해시와4개 로컬 바이트 위치로 재생성했다. 원문과 동일한 전체 스냅샷이라고 표시하지 않는다. 다른9개 Markdown·나머지101개 출처 항목은 유지한다.
- 기존 build_dataset.py·curated_samples.py·일반 데이터 검사 코드는 수정하지 않았다. 보호 예외·격리 해제·위협 실행도 수행하지 않았다.

| CSV ID | 원래/현재 발췌 줄 | 유지한 근거 |
| --- | --- | --- |
| sql_injection-attack-025 | 35 | 원래 CSV·출처 URL 유지 |
| sql_injection-attack-026 | 43 | 원래 CSV·출처 URL 유지 |
| sql_injection-attack-027 | 44 | 원래 CSV·출처 URL 유지 |
| sql_injection-attack-028 | 45 | 원래 CSV·출처 URL 유지 |

전체 원문 SHA-256: f6bad93117b22ac5575260d55967cb030f2780d8dcb70f5a9a5e16e82f1dbf36.
발췌본 SHA-256: 6541c1e720b21df687e9ac5e46dbad339884ae794a08ca688fb6e45b38423eb0 / 크기793바이트.

## 검사와 과거 검증의 구분

- **일반 test_dataset.py7개 통과**: 기존에 실패했던 실제 작업 폴더 원문 대조와 오프라인 재생성까지 다시 통과했다. [현재 자료 검사 로그](evidence/2026-10-27-csv-excerpt-dataset-tests.txt).
- **메타데이터/발췌 출처 계약6개 통과**: 137행과697개 잘못된 메타데이터 조건(기존694+발췌 근거 변조3개)을 검사했다. [로그](evidence/2026-10-27-csv-excerpt-contract-tests.txt).
- 현재 감사는10개 작업 파일/105개 현재 출처 위치와, 발췌4개가 원래 Git 원문 문자열·줄 번호와 같음을 확인한다. CSV4개 불변과 manifest 변경 범위를 검사한다. [감사 JSON](2026-10-27-csv-excerpt-audit.json), [감사 로그](evidence/2026-10-27-csv-excerpt-audit.txt).
- **과거 전체 Git 원문 스냅샷7개 검사 통과**: 이 검증은 계속fd106c9의 전체 원문/manifest를 메모리에서 비교한다. 새 발췌본 manifest와 같다고 주장하지 않도록 기대 출력도 Git 기준으로 고정했다. [과거 스냅샷 로그](evidence/2026-10-27-csv-excerpt-archived-tests.txt).

이 문서 이후 상태는 ‘작업 폴더 원문 부재·기존2개 오류’가 해소된 상태다. 이전 문서의 파일 부재/실패 기록은 당시 이력으로 보존한다. 현재는9개 전체 원문 +1개 명시적 발췌본이며 전체 원문10개를 복구한 것이 아니다.

## PR와 완료 판단

사용자가 실제 조작을 전반적으로 정상이라고 보고했으며 세부 기기·확대율·터치 환경은 별도 미기재다. 본인·팀 문안 검토와 main 반영은 PR의 실제 검토 상태에 따라 진행한다. 팀의 승인을 대신하거나 검토 전 #19를 닫지 않는다.


## PR 제출 직전 전체 회귀

백엔드226개, 프론트19파일113개와 빌드488모듈이 이번 변경 후보에서 모두 통과했다. [백엔드](evidence/2026-10-27-pr-backend-tests.txt), [프론트](evidence/2026-10-27-pr-frontend-tests.txt), [빌드](evidence/2026-10-27-pr-frontend-build.txt).

현재 감사·과거 스냅샷 검증의 고정 기준은 공통 main 조상23b0559다. 이후 PR의 merge 방식과 관계없이 원래 자료를 조회할 수 있도록, 데이터 바이트가 같은 개인 브랜치 커밋 대신 공통 조상을 사용한다.

## PR 연결

- 발췌본·검증 커밋: `bd72d45`.
- [PR #48](https://github.com/ts825360/-PayloadLab-/pull/48)에서 팀 검토를 받는다. 실제 승인 전 main 반영·#19 종료하지 않는다.
