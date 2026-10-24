# Terminal Diagnostic Spike Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Current user preference is inline work on the shared main; do not spawn implementer agents or create a branch without authorization.

실행 상태는 [WORK-STATE의 UX-01](../../WORK-STATE.md)에만 기록한다. 이 문서의 Step은 절차이며 별도 완료표로 관리하지 않는다. 다음 수정 진행 요청에서는 이미 합의한 목표를 다시 묻지 않고 현재 체크포인트부터 재개한다.

**Goal:** 기존 권한 Easy trace를 원문·유니코드 위치가 정확한 진단 데이터로 변환하는 작은 스파이크를 검증한다.

**Architecture:** 기존 API와 성공 판정은 바꾸지 않는다. 프론트 순수 함수가 알려진 permission_denied만 진단하며, 실제 오류 문자열과 없는 문자열의 경계를 확인한다. 이 결과는 다음 세로 시제품의 밑줄·요약·Lens·TUI가 공유할 계약이다.

**Tech Stack:** JavaScript, 기존 Vitest. 새 패키지·서버·실제 셸 없음.

## Global Constraints

- [설계 검토안](../specs/2026-10-24-dual-workspace-design.md)을 사용자가 검토한 뒤 착수한다. 지금 이 문서는 실행 결과가 아니다.
- 13개 랩, API ID와 상태, 권한 Normal 미등록을 보존한다. 모르는 오류는 원인을 지어내지 않는다.
- 원문 문자열을 수정하지 않는다. 범위는 코드포인트이며 view의 선택 키는 labId/attemptId/diagnosticId다.
- 별도 표시가 없는 모든 명령은 저장소 루트에서 실행한다.
- 사용자 요청대로 main에서 작업별 검증·소규모 커밋을 한다. 원격 변경을 확인하고 unrelated dirty changes는 보존한다. 강제 push·공개 배포는 금지한다.
- 이 계획은 첫 진단 계약만 다룬다. 전체 Linux Desktop을 완성했다고 보고할 수 없다. 후속 UI 계획은 이 스파이크의 실제 결과를 반영해 별도 작성한다.

---

### Task 1: 권한 오류 진단 어댑터

**Files:**
- Create: `frontend/src/terminal/diagnostics.js`
- Test: `frontend/src/terminal/diagnostics.test.js`
- Read: `backend/app/labs/practice_extensions.py`, `frontend/src/PracticeSimulation.jsx`

**Interfaces:**
- Consumes: 기존 trace의 `category`, `raw_input`, `execution.status`, `execution.stderr`, `lens.title/why/next`.
- Produces: `terminalDiagnostics(trace): Diagnostic[]`. Diagnostic은 `id`, `category`, `severity`, `title`, `why`, `next`, `targets`를 갖는다. target은 `{source, start, end, unit:'codepoint'}`이다. 현재 스파이크는 stderr의 Permission denied 구절만 표시하며 경로가 틀렸다고 단정하지 않는다.

**Step 1: 아래 실패 테스트를 추가한다.**

```js
import {expect, it} from 'vitest';
import {terminalDiagnostics} from './diagnostics.js';

function denied(stderr='cat: /lab/report.txt: Permission denied\n') {
  return {category:'permissions', raw_input:'cat /lab/report.txt',
    execution:{status:'permission_denied', stderr},
    lens:{title:'읽기 권한을 확인하세요', why:'소유자와 현재 사용자를 비교해요.',
      next:'ls -l /lab/report.txt와 whoami를 관찰하세요.'}};
}

it('marks only the actual stderr phrase and reuses the existing Lens',()=>{
  const trace=denied();
  const [diagnostic]=terminalDiagnostics(trace);
  expect(diagnostic.category).toBe('permission');
  expect(diagnostic.severity).toBe('warning');
  expect(diagnostic.why).toBe(trace.lens.why);
  expect(diagnostic.next).toBe(trace.lens.next);
  const target=diagnostic.targets[0];
  expect(target.source).toBe('stderr');
  expect(target.unit).toBe('codepoint');
  expect(Array.from(trace.execution.stderr).slice(target.start,target.end).join(''))
    .toBe('Permission denied');
  expect(trace.execution.stderr).toBe('cat: /lab/report.txt: Permission denied\n');
});

it('does not confuse UTF-16 offsets with codepoint positions',()=>{
  const trace=denied('🔒 파일: Permission denied\n');
  const [diagnostic]=terminalDiagnostics(trace);
  const target=diagnostic.targets[0];
  expect(target.start).toBe(Array.from('🔒 파일: ').length);
  expect(Array.from(trace.execution.stderr).slice(target.start,target.end).join(''))
    .toBe('Permission denied');
});

it.each([
  null,
  {category:'permissions',execution:{status:'command_ok',stderr:''}},
  {category:'permissions',execution:{status:'unsupported',stderr:'미지원'}},
  {category:'permissions',execution:{status:'permission_denied',stderr:123}},
  {category:'permissions',execution:{status:'permission_denied',stderr:'다른 오류'}},
  {category:'linux_basics',execution:{status:'permission_denied',stderr:'Permission denied'}},
])('does not invent a diagnosis for an unsupported trace %j',(trace)=>{
  expect(terminalDiagnostics(trace)).toEqual([]);
});
```

**Step 2: 실패를 확인한다.**

저장소 루트의 frontend 의존성이 설치된 환경에서:

```powershell
npm --prefix frontend test -- src/terminal/diagnostics.test.js --reporter=dot --maxWorkers=1 --minWorkers=1
```

기대: 진단 모듈이 없어 실패한다. 패키지/환경 오류는 기능 실패와 구분해 먼저 해결한다. Docker에서 파일이 bind mount된 경우 `docker compose exec -T frontend npm test -- src/terminal/diagnostics.test.js --reporter=dot --maxWorkers=1 --minWorkers=1`로 같은 검사를 할 수 있다. 실제 실행에서 기본 워커가 컨테이너 제한으로 EAGAIN을 발생시켜 단일 워커로 한정했다. 모듈 부재 확인 후 빈 함수를 먼저 두어 정상 진단 assertion 실패도 확인한다.

**Step 3: 최소 어댑터를 작성한다.**

```js
export function terminalDiagnostics(trace) {
  if (trace?.category !== 'permissions' ||
      trace.execution?.status !== 'permission_denied') return [];
  const text=trace.execution.stderr;
  if (typeof text !== 'string') return [];
  const phrase='Permission denied';
  const offset=text.indexOf(phrase);
  if (offset < 0) return [];
  const start=Array.from(text.slice(0,offset)).length;
  return [{
    id:'permission-denied', category:'permission', severity:'warning',
    title:trace.lens?.title || '읽기 권한을 확인하세요',
    why:trace.lens?.why || '현재 사용자와 파일의 소유자·읽기 권한을 비교하세요.',
    next:trace.lens?.next || '가상 환경의 사용자와 파일 권한을 관찰하세요.',
    targets:[{source:'stderr', start, end:start+Array.from(phrase).length,
      unit:'codepoint'}],
  }];
}
```

**Step 4: 같은 테스트를 다시 실행해 8개 통과를 확인한다.**

**Step 5: 허용된 환경에서 기존 프론트 테스트 전체와 build를 실행한다. 기존 54개와 신규 8개가 모두 수집되면 62개가 예상된다. 실제 수집 수·결과를 기록하고 숫자만 맞추기 위해 테스트를 삭제하지 않는다.**

```powershell
docker compose exec -T frontend npm test -- --reporter=dot --maxWorkers=2 --minWorkers=1
docker compose exec -T frontend npm run build
```

**Step 6: 변경과 WORK-STATE의 완료 근거·다음 작업을 함께 검토하고 커밋한다.**

```powershell
git diff --check
git add -- frontend/src/terminal/diagnostics.js frontend/src/terminal/diagnostics.test.js docs/WORK-STATE.md
git commit -m "feat: model terminal permission diagnostics with precise ranges"
```

원격 main이 바뀌었으면 먼저 차이를 검토한다. 이 커밋은 진단 계약의 검증일 뿐 화면 구현·브라우저 검증 완료가 아니다. 새 이슈를 만들거나 기존 검증 이슈를 닫지 않는다.

## 스파이크 통과 뒤 후속 계획에 반드시 담을 것

아래는 이번 계획의 미완성 구현 단계가 아니라 **다음 계획의 입력 조건**이다.

1. DiagnosticText가 이 코드포인트 범위를 사용해 밑줄을 그리고 hover/focus 요약을 연다. tooltip은 비상호작용 텍스트이며 trigger 선택이 공통 Lens의 진단 선택으로 연결된다.
2. 권한 Easy 한 화면에서 입력→모의 원문→밑줄→요약→하단 Lens→같은 trace의 권한 TUI를 연결한다. 이 입력면에서 Shift+Enter·IME·여러 줄·스크롤·이모지·확대 정렬을 별도 검증한다.
3. 전체 화면/데스크톱 모드와 로고 복귀를 붙이기 전에 사용자에게 동작을 확인받는다. 범위가 없는 오류는 배지/지원 안내로 처리하며 임의 인자에 밑줄을 긋지 않는다.
4. 다음 계획은 실제 스파이크·브라우저 결과를 반영해 정확한 UI 파일·props·실패 테스트를 정의한다. 기존 App 상태의 무조건 복제와 자유 셸 도입은 하지 않는다.

## 검토·진행 방식

이 계획의 자가 검토: 기존 API를 바꾸지 않는 단일 순수 함수, 원문 보존, 유니코드 범위, 미지원 판정, 명시적 실패/통과 명령을 포함했다. 아직 어느 단계도 실행하지 않았다.

사용자가 설계·순서를 확인하면 이 세션에서 `executing-plans` 방식으로 한 과제씩 수행하는 것을 기본 제안한다. 별도 에이전트 분업이 필요하면 먼저 요청/승인을 받는다.
