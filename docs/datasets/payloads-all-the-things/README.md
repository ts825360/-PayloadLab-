# PayloadLab 공격 입력 데이터 초안

연결 이슈: [SQL 조사 #14](https://github.com/ts825360/-PayloadLab-/issues/14), [설명 기준 #19](https://github.com/ts825360/-PayloadLab-/issues/19)

목적은 **입력과 설명을 만들 때 참고할 문서상 예시 모음**입니다. 원본 전체를 변환한 데이터셋이나 학습·평가를 마친 AI 모델이 아닙니다. 원문에서 선별한 공격 시도와 PayloadLab이 별도 작성한 정상 예시를 같은 컬럼으로 저장했습니다. 공격문은 문자열로만 취급했으며 DB·셸·브라우저·목적지 URL에서 **미실행** 상태입니다.

## 파일과 범위

| 파일 | 공격 시도 | 정상 예시 | 문맥 미정 | 합계 |
| --- | ---: | ---: | ---: | ---: |
| `sql_injection.csv` | 28 | 8 | 1 | 37 |
| `xss.csv` | 24 | 8 | 1 | 33 |
| `command_injection.csv` | 25 | 8 | 1 | 34 |
| `ssrf.csv` | 24 | 8 | 1 | 33 |
| 전체 | 101 | 32 | 4 | 137 |

SQL은 common/MySQL/MSSQL/PostgreSQL/Oracle/SQLite 예시를 포함합니다. 우회·변형은 별도 공격 유형이 아니라 `technique`, `variant_type`으로 표현합니다. 현재 서비스는 SQL/XSS/IDOR/SSRF/CMDi/Linux Easy·Normal과 권한 Easy의13개 랩을 제공하지만, 이 CSV는 런타임에 자동 연결되지 않습니다. CSV의 전체 기법이나 모든 DBMS를 실습이 해석·실행한다는 의미가 아닙니다. 유형별 연결과 검증 한계는 [#19 교육 범위 검토](../../research/csv-education-scope.md)를 참조하세요.

자료는 검토 가능한 시작 묶음으로 제한했습니다. 원본의 공격 자동화 도구, 키로거·쿠키 유출, 셸 업로드·리버스 셸, 파괴적 명령과 큰 생성 프로그램은 이 초안에 넣지 않았습니다. 코드 블록 전체를 무조건 공격으로 라벨링하지 않았습니다. 정상 웹 서버 코드·공격 뒤 출력 결과는 수집 대상이 아닙니다. 일부 공격문은 원문에 담긴 템플릿 또는 SQL 코드 조각이며 완성된 공격 입력이 아닐 수 있습니다.

## 공통 컬럼

| 컬럼 | 의미 |
| --- | --- |
| `id` | 유형·라벨·번호로 된 고유 식별자 |
| `payload` | 선택한 원문 부분 문자열 그대로. 공백/대소문자/인코딩/제어문자/줄바꿈 보존 |
| `label` | `attack` / `benign` / `uncertain` |
| `attack_type` | 이 CSV가 다루는 분류 과제: sql_injection / xss / command_injection / ssrf. benign 행의 실제 공격 유형이라는 뜻은 아님 |
| `technique` | 인증 우회·이벤트 핸들러·명령 결합·로컬 주소 등 세부 기법 |
| `target_platform` | DBMS·브라우저·셸·URL 해석 환경. `common`도 모든 엔진 지원을 보증하지 않음 |
| `input_context` | 삽입 위치와 해석 가정. 문자열 자체와 함께 읽어야 하는 라벨 조건 |
| `variant_type` | 원형/대소문자/주석/인코딩/주소/따옴표 변형 등 |
| `family_id` | 같은 템플릿·목적·구문 계열의 관련 예시 묶음. 누수 방지의 최소 단위 |
| `source_url` | 원문 고정 커밋과 줄 번호. 별도 작성 정상 예시는 빈 값 |
| `source_commit` | 수집한 원본 버전. 정상 예시는 빈 값 |
| `label_reason` | 해당 문맥에서 라벨을 붙인 이유와 작성 주체 |
| `validation_status` | 모두 `documentation_reviewed_not_executed`: 문서 대조만 수행, 공격 성공 검증 안 함 |
| `license` | MIT. 아래 고지와 LICENSE를 함께 보존 |

## 라벨을 읽는 방법

- `attack`: 원문의 공격 시나리오에서 사용하는 **시도**입니다. 문법 오류나 플랫폼 불일치로 실패해도 곧바로 정상 입력이 되지 않습니다. 성공을 뜻하지 않습니다.
- `benign`: 작성된 `input_context`에서 일반 입력으로 사용한 자체 예시입니다. `O'Reilly` 때문에 취약 SQL이 깨져도 그 이름을 공격이라고 단정할 수 없습니다. 반대로 다른 문맥에 옮기면 위험할 수 있습니다.
- `uncertain`: 문맥·권한·정책을 모르면 판단할 수 없는 문자열입니다. `review_only`로 관리하고 이진 지도학습에서 제외하거나 팀이 문맥을 명시해 다시 검토해야 합니다.

SSRF의 localhost 주소는 허용된 내부 API라면 정상일 수 있습니다. 여기서는 ‘공개 목적지만 허용한 URL 가져오기 기능에 내부 접근을 시도한다’는 문맥으로 attack 라벨을 붙였습니다. CMDi의 명령 단어도 터미널에 정당하게 입력하면 정상 명령입니다. SQL의 SELECT 자체도 공격이 아닙니다. 따라서 **payload 문자열만으로 보편적인 공격 여부를 판정하는 정답 데이터가 아닙니다.** 같은 문자열이 문맥에 따라 다른 라벨로 존재할 수 있습니다.

## 원문·재현·검증

원본: [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) / 고정 커밋 `3ac27901c711bdf3f5b65a7b1d1820a1f65bd09a` (2026-08-27). 최신 master 자동 추적이 아닙니다.

`sources/`는 대조용 원문 Markdown입니다. 원문 전체 파일에는 CSV에 선별하지 않은 고급 공격 예시도 포함되어 있으므로 참고 자료로만 취급하고 실행하지 않습니다. `curated_samples.py`는 선택한 문자열과 메타데이터이고 `manifest.json`은 원문 SHA-256, 각 입력의 바이트 위치·줄 번호·SHA-256을 기록합니다. `build_dataset.py`는 네트워크와 payload 실행 없이 저장된 원문에 정확히 있는지 확인해 CSV를 재생성합니다. 생성 당시 파일이 없거나 문자열이 달라졌으면 중단합니다. `.gitattributes`는 원문·CSV·manifest의 Git 자동 줄바꿈 변환을 막아 Windows에서도 바이트 근거를 보존합니다.

```powershell
python docs/datasets/payloads-all-the-things/build_dataset.py
python docs/datasets/payloads-all-the-things/test_dataset.py -v
```

테스트는 공통 헤더, ID 중복, 개수, 출처 바이트 동일성, 출처 줄 번호, DBMS 범위, 변형 묶음, Unicode·제어문자·여러 줄 CSV 왕복, 오프라인 재생성 동일성을 확인합니다. 이 검사는 라벨의 교육적 적절성이나 실제 취약점의 유효성까지 검증하지 않습니다.

CSV는 UTF-8 BOM과 표준 quoting을 사용합니다. **Excel에서 더블클릭으로 열지 마세요.** 공격문에는 `=`, `+`, `-`, `@`로 시작하는 문자열 등이 들어갈 수 있어 수식으로 해석될 위험이 있습니다. CSV quoting만으로 수식 해석을 막을 수 없습니다. 원문을 바꾸지 않기 위해 접두 문자를 삽입하지 않았습니다. 코드의 CSV reader 또는 텍스트 편집기로 확인하고, 스프레드시트가 필요하면 모든 열을 텍스트로 지정해 가져오세요. HTML로 렌더링하거나 코드/셸/URL 요청에 그대로 연결하지 않습니다.

## 이후 학습·Lens 적용 전에 할 일

1. 팀원이 각 행의 문맥·라벨·기법을 검토합니다. 미검증 상태를 성공 검증 완료로 바꾸지 않습니다.
2. 실제 정상 입력과 어려운 정상 예시를 보강합니다. 현재는 작은 인공 표본으로 클래스 비율·정확도 주장을 할 수 없습니다.
3. 원문과 비슷한 변형은 `family_id` 단위로 train/validation/test를 분리합니다. 동일 문자열뿐 아니라 거의 같은 변형과 관련 계열도 함께 묶어야 합니다. 현재 family_id는 수동 시작값으로, 교차 파일·의미상 유사 계열까지 추가 점검해야 합니다.
4. `uncertain`과 상충 라벨을 분리합니다. `payload` 단독 모델을 학습하면 문맥이 다른 동일 문자열이 정답 충돌을 일으킬 수 있습니다.
5. `id`, `source_url`, `source_commit`, `label_reason`처럼 라벨을 노출하는 메타데이터를 모델 입력에 넣지 않습니다. 모델 입력과 평가 목표를 먼저 확정합니다.
6. 각 입력의 Easy/Normal 학습 적합성, Lens의 ‘어디서·무엇이·왜’ 설명, 다이어그램 대응을 별도로 작성합니다. CSV를 추가했다고 Lens가 자동으로 이해하지 않습니다.

## 라이선스

원본은 MIT, Copyright (c) 2019 Swissky입니다. [LICENSE](LICENSE)의 원문 고지를 함께 배포합니다. 원본 발췌를 수정하지 않았고 CSV 분류·설명·정상 예시를 추가했습니다. 별도 작성 부분은 Copyright (c) 2026 PayloadLab contributors, MIT로 제공합니다. 라이선스 허용은 임의의 외부 시스템에 공격할 권한을 뜻하지 않습니다.


## 2026-10-27 SQLite 참고 문서 발췌본

Windows Defender가 전체 SQLite 참고 Markdown 안의 PHP 백도어 예시를 탐지해 파일을 조치했다. 보호 설정을 바꾸거나 전체 파일을 복원하는 대신, 현재 CSV가 사용하는 메타데이터 조회문4개만 같은 줄35/43/44/45에 남긴 명시적 발췌본으로 교체했다. `sources/SQL Injection__SQLite Injection.md`의 머리말은 전체 원문이 아님을 밝힌다. 나머지9개 Markdown은 기존 전체 스냅샷이다.

CSV4개의137행·문자열·라벨·source_url·source_commit은 바이트 단위로 유지했다. manifest는 발췌본의 실제 SHA-256과 바이트 위치로 재생성했다. `sources/SQL Injection__SQLite Injection.provenance.json`은 원래 전체 문서 해시·원래4개 바이트/줄 근거·발췌본 해시를 연결한다. 전체 원문과 동일한 파일이라고 주장하지 않는다.

일반 `test_dataset.py`7개를 이 작업 폴더에서 다시 실행할 수 있다. 과거 전체 원문의 Git 스냅샷 재현은 별도 검증이며, 현재 발췌본 manifest 검사는 일반 데이터 검사로 구분한다.
