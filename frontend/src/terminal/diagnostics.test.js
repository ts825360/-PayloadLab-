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

it('links the denied file path to the exact input without blaming command spelling',()=>{
  const trace=denied('cat: /lab/보고서🔒.txt: Permission denied\n');
  trace.raw_input='  cat /lab/보고서🔒.txt  ';
  const [diagnostic]=terminalDiagnostics(trace);
  const target=diagnostic.targets.find(target=>target.source==='input');
  expect(target).toBeDefined();
  expect(Array.from(trace.raw_input).slice(target.start,target.end).join('')).toBe('/lab/보고서🔒.txt');
  expect(diagnostic.category).toBe('permission');
});

it('does not underline a different draft or an analysis-only input',()=>{
  const trace=denied();
  trace.raw_input='whoami';
  expect(terminalDiagnostics(trace)[0].targets.some(target=>target.source==='input')).toBe(false);
  expect(terminalDiagnostics({...trace,phase:'analysis',execution:null})).toEqual([]);
  expect(terminalDiagnostics({...trace,phase:'analysis'})).toEqual([]);
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
