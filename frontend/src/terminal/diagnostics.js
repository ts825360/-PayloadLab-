// Ranges use Unicode codepoints, not JavaScript UTF-16 offsets.
// Only known model statuses can produce diagnostics; stderr is never rewritten.
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
