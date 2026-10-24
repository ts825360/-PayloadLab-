import { statusLabel } from './learning-content.js';
import DiagnosticText from './terminal/DiagnosticText.jsx';
import { terminalDiagnostics } from './terminal/diagnostics.js';

const starts = {
  permissions: ['현재 사용자', '파일 소유자·권한', '접근 허용 / 거부'],
  linux_basics: ['명령어 빈칸', '명령 + 옵션 + 경로', '가상 목록 출력'],
  command_injection: ['호스트 입력', '명령 경계', '허용한 명령의 모의 출력'],
  ssrf: ['입력 URL', '정책과 실제 hostname', '더미 목적지 응답'],
};

export default function PracticeSimulation({ trace, category, onDiagnostic }) {
  const executed = trace?.phase !== 'analysis' && Boolean(trace?.execution);
  const execution = executed ? trace.execution : null;
  const diagnostics = executed ? terminalDiagnostics(trace) : [];
  const terminal = trace?.terminal;
  const nodes = executed ? trace.simulation?.nodes || [] : [];
  const previousUser = nodes.find((node) => node.id === 'identity')?.value;
  const commandPrompt = previousUser ? `${previousUser}@practice:/lab${previousUser === 'root' ? '#' : '$'} ` : terminal?.prompt || 'student@practice:/lab$ ';
  return <section className="panel practice-simulation" aria-label={`${category.label} 모의 결과`}>
    <div className="panel-heading"><div><span className="step-number">03</span><h2>{category.terminal ? '사용자에서 파일 접근까지' : '입력에서 경계 변화까지'}</h2></div><span className="quiet-badge">교육용 모의 환경</span></div>
    <p className="simulation-boundary">{category.id === 'permissions' ? '실제 서버의 파일·권한은 바뀌지 않아요.' : '실제 네트워크·셸을 실행하지 않고, 정해진 교육용 상황만 보여줘요.'}</p>
    <ol className="simulation-flow" aria-label="모의 처리 흐름">
      {(nodes.length ? nodes : (starts[category.id] || []).map((label, index) => ({id:index,label,value:'실행 후 확인',state:'pending'}))).map((node,index) => <li key={node.id} data-state={node.state}>
        <span className="flow-index">0{index+1}</span><div><strong>{node.label}</strong><code>{node.value}</code></div>
      </li>)}
    </ol>
    {category.id === 'permissions' && terminal?.files?.length > 0 && <div className="virtual-files" aria-label="가상 파일 권한">
      <div className="virtual-identity"><span>현재 가상 사용자</span><strong>{terminal.current_user}</strong><code>{terminal.prompt}</code></div>
      {terminal.files.map((file) => <div className="virtual-file" key={file.path}>
        <strong>{file.path}</strong><span>소유자 <b>{file.owner}</b></span>
        <code title="파일 종류 · 소유자 · 그룹 · 다른 사용자">{file.permissions.slice(0,1)} <mark>{file.permissions.slice(1,4)}</mark> {file.permissions.slice(4,7)} {file.permissions.slice(7,10)}</code>
        <small>소유자 / 그룹 / 다른 사용자 순서 · r 읽기 · w 쓰기 · x 실행</small>
      </div>)}
    </div>}
    {execution ? <div className="terminal-card">
      <div className="terminal-bar"><span>VIRTUAL OUTPUT · {category.short || 'LAB'}</span><span>종료 코드 {execution.exit_code}</span></div>
      <div className="terminal-raw" aria-label="터미널 원문 출력">
        <pre className="terminal-command">{commandPrompt}{trace.raw_input}</pre>
        {execution.stdout && <pre>{execution.stdout}</pre>}
        {execution.stderr && <pre className="terminal-stderr"><DiagnosticText text={execution.stderr} source="stderr" diagnostics={diagnostics} onSelect={onDiagnostic} /></pre>}
        {!execution.stdout && !execution.stderr && <pre>(출력 없음)</pre>}
      </div>
      <div className={`terminal-annotation ${execution.stderr ? 'warning' : ''}`}><span>↳ Lens · {statusLabel(execution.status)}</span><strong>{trace.lens?.title}</strong><p>{trace.lens?.what}</p></div>
    </div> : <div className="simulation-empty"><strong>실행 전 · 먼저 입력을 예상해보세요</strong><p>Enter로 실행하면 원문 출력과 경계가 달라지는 지점을 함께 보여줘요.</p></div>}
    {terminal?.supported_commands && <details className="supported-commands"><summary>이 가상 환경에서 지원하는 명령</summary><p>아래 명령만 해석합니다. 일반 터미널이나 실제 시스템이 아니에요.</p><code>{terminal.supported_commands.join(' · ')}</code></details>}
  </section>;
}
