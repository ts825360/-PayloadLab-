import {statusLabel} from '../learning-content.js';

export default function TerminalInspector({trace,category}) {
  const executed=trace?.phase!=='analysis' && Boolean(trace?.execution);
  const user=trace?.simulation?.nodes?.find(node=>node.id==='identity')?.value || trace?.terminal?.current_user;
  const files=trace?.terminal?.files || [];
  const result=executed ? statusLabel(trace.execution.status) : '아직 실행하지 않았어요';
  let lines;
  if(category.id==='permissions') {
    lines=[`┌─ USER  ${user || 'student (시작 사용자)'}`,'│',
      ...files.flatMap(file=>[`├─ FILE  ${file.path}`,`│  소유자 ${file.owner}`,`│  권한   ${file.permissions}`,'│']),
      `└─ RESULT  ${result}`];
    if(executed && trace.execution.status==='elevated')lines.push(`   ${user} → ${trace.terminal?.current_user} (가상 사용자)`);
  } else if(category.id==='command_injection') {
    lines=[`┌─ HOST  ${trace?.command_model?.hostname || '호스트 입력'}`,
      `│  경계  ${trace?.command_model?.separator || '호스트 인자'}`,'│',`└─ RESULT  ${result}`];
  } else {
    lines=['┌─ COMMAND  이름 + 옵션 + 경로','│','├─ /lab/',...files.map(file=>`│  └─ ${file.path.split('/').at(-1)}`),'│',`└─ RESULT  ${result}`];
  }
  return <div className="terminal-inspector-content">
    <span className="terminal-section-label">INPUT → PROCESS → RESULT</span>
    <pre className="terminal-tui" aria-label="터미널 처리 흐름">{lines.join('\n')}</pre>
    {trace?.composition?.full && <div className="terminal-composition"><h3>{category.id==='command_injection'?'서버가 조립한 명령':'이번 입력'}</h3><pre aria-label={category.id==='command_injection'?'서버가 조립한 명령':'관찰 중인 입력'}>{trace.composition.full}</pre></div>}
    {trace?.lens?.next && <div className="terminal-next"><h3>다음에 볼 단서</h3><p>{trace.lens.next}</p></div>}
    {!trace && <p className="terminal-next">한 번 실행하면 현재 사용자, 입력의 처리 과정, 결과가 여기에 연결돼요.</p>}
  </div>;
}
