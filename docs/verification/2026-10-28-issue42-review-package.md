# #42 공유 전 검토안 — 2026-10-28

## 최신 사용자 결정

이전 이슈별 브랜치 분리 해석을 정정한다. 사용자 요청은 `suwoong(#19,#42,#44)` 한 개인 브랜치 안에 이슈별 커밋을 모으는 것이다. #42코드는 backend14d930d·frontend72949e6로 로컬 저장했고 이 문서/근거를 저장한 뒤 #19를 병합한다. #44코드는 아직 없으며 빈 별도 브랜치는 정리했다. 이번 승인 범위는 로컬 커밋/통합까지만이며 push/PR 게시·이슈 종료는 하지 않는다. #42 종료는 팀장 태성의 최종 검토/보고 후 결정한다.

## 이전 공유 준비 결과

main64c9cb1 기반 개인브랜치 dtd2428/issue-42-input-sql의 미커밋 변경이다. 2026-10-28 원격main도 같은SHA임을 fetch로 확인했다. #6/#24/#42의 검토 요청 이후 다른 팀원 답변은 없고 #19 PR #48은 open·미병합이다.

backend236개/실제HTTP21개, frontend115개·빌드487모듈, SQL60/60과 대표 실제화면 결과를 연결했다. 공유 준비 과정에서는 마지막 backend/frontend 검증 source-hash와 현재 실행파일이 같음을 대조했고 제품 소스 변경이 없으므로 전체 테스트를 불필요하게 다시 돌리지 않았다.

## 검토할 핵심

1. 숫자·8192작업단위의 의미와 SQL허용 목록은 팀 미승인이다.
2. 기본app.main.app에서는 제한을 활성화하지 않았다. 명시적 정책 주입 검토 앱만 활성화한다.
3. 화면에서 자원 제한/연산 차단/입력 거부를 일반 실패와 구분하며 정상 재시도가 가능하다.
4. #19 PR과 공통 learning_trace 등의 위치가 겹친다. #19가 main에 반영되면 재대조한다.
5. 공개 배포·운영 전체보호·#42완료로 체크하지 않는다.

## 제안하는 작은 커밋

- 1: `feat: add policy-injected API and SQL resource guards (#42)` — backend 모듈·라우트/SQL 연결과 관련 검증 코드.
- 2: `fix: preserve actionable resource-limit feedback in the learning UI (#42)` — frontend 안내·복구·검사와 별도 검토용 Vite설정.
- 3: `docs: record resource-limit rationale and verification evidence (#42)` — 산정/회귀/실제화면 근거·문서·원자료·이 상태와 PR초안.

파일별 분류와 내용 해시는 [공유 manifest](evidence/2026-10-28-issue42-share-manifest.json)에 있다. 파일 추가/stage·commit·push는 아직 하지 않았다. 실제 검토한 파일만 사용자 확인 후 명시적으로 stage한다.

## 원격 공유 방식

사용자 확인을 받으면 위 커밋을 본인 계정으로 만들고 본인 브랜치로 push한 뒤 [Draft PR초안](2026-10-28-issue42-pr-draft.md)을 게시해 팀 검토를 요청할 수 있다. Draft는 미완료 제안 검토이며 main반영·기본앱 활성화·#42종료와 구분한다. 부분완료이므로 Refs #42를 사용하고 Closes는 쓰지 않는다.

이전 사용자 지시 '커밋은 마음대로 하지마'를 유지하므로 현재 공유안을 먼저 보여주고 commit/push 여부를 확인받는다. 작업 파일은 지정한 문서/GitHub 저장소에 있고 다른 저장소에서 수정하지 않았다.
