# #19 Git 원문 기준 출처·재생성 검증 — 2026-10-27

관련: [CSV 교육 범위 검토](../research/csv-education-scope.md), [#19](https://github.com/ts825360/-PayloadLab-/issues/19).
담당: 이수웅(dtd2428), AI 보조. 기준 로컬 커밋: fd106c93c4c37375bcc43aca4249dceea0dbeb12.

사용자 진행 승인에 따라 이 문서와 검증 근거를 포함하는 로컬 commit을 진행한다. 실제 SHA는 git log로 확인하며 push·PR·main 반영·이슈 종료는 하지 않는다. 아래 검사 시점과 후속 저장 단계를 구분한다.

## 결과와 검증 대상

**Git 보관 원문 기준 출처 대조·기존 생성기 재생성 검사2개 통과.** 원문10개 SHA-256·출처105건과, 재생성 CSV4개/manifest의 바이트 동일성을 확인했다. 이는 작업 폴더에서 빠진 원문을 복구하거나 기존 test_dataset.py7개가 모두 통과한 결과가 아니다.

현재 SQLite 원문 파일은 여전히 없고, 보호 기록에는 같은 경로의 탐지·조치 성공과 ThreatStatusID3이 남아 있었다. 조치 종류를 임의로 해석하거나 백신 예외·비활성화·격리 복원은 수행하지 않았다. 파일 삭제도 stage하지 않았다.

## 방법

1. CSV4개·manifest가 기준 커밋과 바이트 단위로 같고, build_dataset.py/curated_samples.py의 소스도 같은지 먼저 검사했다. Python 파일만 Git 작업 트리의 CRLF/LF 차이를 허용했고 데이터·원문·생성 결과는 바이트를 그대로 비교했다.
2. Git에 보관된 원문10개를 메모리에서 읽었다. 원문 Markdown은 디스크에 쓰지 않았다.
3. 기존 생성기 코드는 수정하지 않고, 검증 프로세스 안에서만 ROOT에 읽기 전용 Git 원문 객체를 제공했다. 원래 source_proof 함수로105개 부분 문자열·줄 번호·해시·URL이 manifest/CSV와 같은지 검사했다.
4. 기존 build 함수를 실행해 임시 폴더에 CSV4개와 manifest만 생성했다. 이 함수는 CSV 문자열·문서 메타데이터를 만들 뿐 payload를 DB·브라우저·셸·목적지 URL에서 실행하지 않는다.
5. 임시 폴더의 절대 경로·부모·전용 접두사와 생성 파일5개만 있는지 확인했다. 결과5개를 현재 자료와 비교하고 임시 출력은 정리했다. 저장소 원본·CSV·manifest는 덮어쓰지 않았다.

검증용 ROOT 객체는 이 프로세스 안에만 적용된다. 원래 생성기·기존 데이터 검사·보호 설정·실제 작업 폴더의 파일 상태는 바뀌지 않는다. 같은 이름의 원문을 다른 폴더에 복원해 검사를 우회한 것이 아니다.

## 출력 바이트 대조

| 생성 파일 | 바이트 수 | 현재 자료와 비교 | SHA-256 |
| --- | --- | --- | --- |
| sql_injection.csv | 25192 | 일치 | f177a3229ca2690b7de0d8c0fa9f91711ddb88875889d7095d8acf1df48ec5fd |
| xss.csv | 18880 | 일치 | 8bf06be3c3fef8e6ad81732b9e294405ecf37c927d63bbc85434af5913d6cf6b |
| command_injection.csv | 21989 | 일치 | 7b40f010da721e8774967c304d0b56fcec8b8ee78e055e17daf815ff2cf4ca1f |
| ssrf.csv | 21127 | 일치 | 83880182e6ae43ec10becfeeba3c0fe461541997677bc6b4cd88a688f2555dfe |
| manifest.json | 34739 | 일치 | 08bb0f2b33beca8ab8b1fee3a4ee02bcc2af68098e6677ad79ab98b4c9cd9528 |

[검증 스크립트](scripts/csv_snapshot_verification.py), [검사 로그](evidence/2026-10-27-csv-snapshot-verification.txt), [검증 범위·해시·출력 상태 JSON](2026-10-27-csv-snapshot-verification.json).

## 검사 과정에서 바로잡은 점

첫 사전 검사에서는 Windows 작업 트리의 Python CRLF와 Git LF를 바이트 불일치로 잡았다. Python 소스 비교만 줄바꿈 차이를 허용하도록 고쳤다. [사전 검사 기록](evidence/2026-10-27-csv-snapshot-precheck.txt). CSV·manifest·원문 바이트 비교는 완화하지 않았다.

첫 원문 객체는 문자열 순서로 파일을 정렬해 Windows Path 정렬과 달라 manifest의 sources 순서가 달라졌다. 이를 실제 생성기가 사용하는 현재 호스트 Path 정렬과 같게 고친 뒤, 생성기 변경 없이5개 모두 일치했다. [정렬 어댑터 검출 기록](evidence/2026-10-27-csv-snapshot-adapter-order.txt). 이번 검증은 현재 Windows 환경 기준이며 다른 OS의 정렬까지 독립적으로 검증한 것은 아니다.

## 남아 있는 구분

| 항목 | 상태 |
| --- | --- |
|Git 보관 원문10개/출처105건 | 이번 검사 통과 |
|Git 원문 제공 + 기존 생성기의 CSV/manifest5개 재현 | 이번 검사 통과 |
|기존 작업 폴더 기반 test_dataset.py | 원문 파일 부재로 기존2개 오류는 미해결.7개 전체 통과로 표기하지 않음 |
|백신 예외·원문 복원·격리 해제 | 수행하지 않음 |
|실제 공격 성공·모델 성능·원격 원문 재인증 | 이번 검사 대상 아님 |
|commit/push·PR·main 반영·이슈 종료 | 이번 후속 변경에 수행하지 않음 |

재현:

    python docs/verification/scripts/csv_snapshot_verification.py

CSV 교육 범위·라벨·Git 원문 기반 재현 근거는 마련됐다. 작업 폴더 원문 부재, 실제 hover·실기기 터치·200% 확대, 본인·팀 최종 검토는 별도로 남기고 #19 전체 완료로 처리하지 않는다.


## 2차 검증 — 2026-10-27

정상 자료가 재생성되는지만 다시 확인하는 데서 멈추지 않고, 원문/출력이 틀렸을 때 검증이 실제로 실패하는지 확인했다. 이번 범위에서 새 제품 코드 오류나 데이터 불일치는 발견하지 못했다.

[별도 반례 검사](scripts/test_csv_snapshot_verification.py)를 실행해 **총7개 통과**했다. 이7개는 정상 스냅샷 검사2개 + 새 반례 검사5개이며, 파일이 없는 작업 폴더를 읽는 기존 test_dataset.py7개의 전체 통과가 아니다.

| 의도적으로 바꾼 조건 | 건수 | 실제 결과 |
| --- | ---: | --- |
|메모리 원문 바이트 변경 |10 | SHA 불일치로 거부 |
|원문에 없는 payload 부분 문자열 |105 | 원래 생성기의 source_proof가 거부 |
|메모리 원문 하나 누락 |10 | 누락 출처 조회가 오류로 중단 |
|임시 생성 결과에 바이트 추가 |5 | CSV4개/manifest 각각의 비교가 실패. 실패 후 임시 폴더5개 모두 정리 |
|원문 객체의 상위/절대 경로 요청 |3 | 검증 객체가 거부 |
|합계 |133 | 잘못된 조건을 모두 검출 |

반례는 이 검증 프로세스의 메모리 사본이나 원래 검증기가 만든 임시 CSV/manifest에만 적용했다. 저장소 원문·CSV·manifest를 고친 뒤 되돌리는 방식으로 검사하지 않았다. 정상 스냅샷2개도 같은 실행에서 다시 통과했다.

[이번 실행 로그](evidence/2026-10-27-csv-snapshot-second-controls.txt), [검사 범위·최종 불변 확인 JSON](2026-10-27-csv-snapshot-second-review.json).

마지막으로 CSV4개·manifest는 기준 커밋과 바이트가 같고, 생성기/선별 코드도 Python CRLF/LF만 제외하면 같음을 다시 확인했다. SQLite 원문은 여전히 부재하고 stage된 변경은 없다. 백신 설정 변경·원문 복원·payload 실행·새 commit/push는 하지 않았다.

현재 검사 가능한 Git 보관본 기준의 출처·재생성 근거는 재확인됐다. 실제 작업 폴더 원문 부재와 기존2오류, 실제 hover·터치·200% 확대, 본인·팀 최종 검토는 그대로 남는다.

재현:

    python docs/verification/scripts/test_csv_snapshot_verification.py -v
