import {useLayoutEffect,useRef} from 'react';
import {statusLabel} from '../learning-content.js';
import DiagnosticText from './DiagnosticText.jsx';
import {terminalDiagnostics} from './diagnostics.js';
import './terminal-transcript.css';

function promptBefore(trace) {
  const user=trace.simulation?.nodes?.find(node=>node.id==='identity')?.value;
  return user ? `${user}@practice:/lab${user==='root'?'#':'$'} `
    : trace.terminal?.prompt || 'student@practice:/lab$ ';
}

export default function TerminalTranscript({entries=[],selectedId,onDiagnostic}) {
  const listRef=useRef(null),selectedRef=useRef(null);
  const completed=entries.filter(entry=>{
    const trace=entry.result?.learning_trace;
    return trace?.phase!=='analysis' && Boolean(trace?.execution);
  });
  const lastId=completed.at(-1)?.id;
  useLayoutEffect(()=>{
    if(listRef.current && selectedRef.current)
      listRef.current.scrollTop=selectedRef.current.offsetTop;
  },[selectedId,lastId]);
  return <section className="terminal-card terminal-transcript" aria-label="터미널 기록">
    <header className="terminal-bar"><span>VIRTUAL TERMINAL</span><span>교육용 모의 출력 · {completed.length}회</span></header>
    <div className="terminal-transcript-entries" ref={listRef} tabIndex={0} aria-label="터미널 기록 스크롤">
      {completed.map((entry,index)=>{
        const trace=entry.result.learning_trace,execution=trace.execution;
        const current=entry.id===selectedId;
        return <article key={entry.id} data-attempt-id={entry.id} data-selected={current}
          ref={current?selectedRef:undefined} aria-label={`터미널 시도 ${index+1}`}>
          <div className="terminal-entry-status"><span>시도 {index+1}{current?' · 선택한 시도':''}</span><span>종료 코드 {execution.exit_code}</span></div>
          <div className="terminal-raw" aria-label="터미널 원문 출력">
            <pre className="terminal-command" aria-label="명령 원문">{promptBefore(trace)}{trace.raw_input ?? entry.input}</pre>
            {execution.stdout && <pre aria-label="표준 출력">{execution.stdout}</pre>}
            {execution.stderr && <pre className="terminal-stderr" aria-label="표준 오류"><DiagnosticText
              text={execution.stderr} source="stderr" diagnostics={terminalDiagnostics(trace)}
              onSelect={current?onDiagnostic:undefined}/></pre>}
            {!execution.stdout && !execution.stderr && <pre>(출력 없음)</pre>}
          </div>
          <div className={`terminal-annotation ${execution.stderr?'warning':''}`}>
            <span>↳ Lens · {statusLabel(execution.status)}</span>
            <strong>{trace.lens?.title}</strong>{current && <p>{trace.lens?.what}</p>}
          </div>
        </article>;
      })}
      {!completed.length && <p className="terminal-transcript-empty">실행한 명령이 여기에 쌓여요.</p>}
    </div>
  </section>;
}
