import {useLayoutEffect,useRef} from 'react';
import DiagnosticText from './DiagnosticText.jsx';
import './terminal-input.css';

export default function TerminalInput({value='',prompt='student@practice:/lab$ ',label,
  placeholder,inputRef,onChange,onKeyDown,onCompositionStart,onCompositionEnd,
  diagnostics=[],onDiagnostic}) {
  const fieldRef=useRef(null),mirrorRef=useRef(null);
  useLayoutEffect(()=>{
    const field=fieldRef.current;
    if(!field)return;
    const resize=()=>{
      field.style.height='auto';
      field.style.height=`${Math.min(144,Math.max(26,field.scrollHeight))}px`;
      if(mirrorRef.current){
        mirrorRef.current.scrollTop=field.scrollTop;
        mirrorRef.current.scrollLeft=field.scrollLeft;
      }
    };
    resize();
    window.addEventListener('resize',resize);
    return ()=>window.removeEventListener('resize',resize);
  },[value]);
  const length=Array.from(value).length;
  const diagnostic=diagnostics.find(item=>item.targets?.some(target=>
    target.source==='input' && target.unit==='codepoint' &&
    Number.isInteger(target.start) && Number.isInteger(target.end) &&
    target.start>=0 && target.end>target.start && target.end<=length));
  return <div className="terminal-input">
    <label htmlFor="payload-input">{label}</label>
    <div className="terminal-input-row">
      <code className="terminal-input-prompt" aria-label="가상 터미널 프롬프트">{prompt}</code>
      <div className="terminal-input-field">
        <div ref={mirrorRef} className="terminal-input-mirror" aria-hidden="true">
          <DiagnosticText text={value} source="input" diagnostics={diagnostics} decorative/>{'\u200b'}
        </div>
        <textarea id="payload-input" aria-label={label} value={value} placeholder={placeholder}
          ref={element=>{fieldRef.current=element;if(inputRef)inputRef.current=element;}}
          onChange={event=>onChange(event.target.value)} onKeyDown={onKeyDown}
          onCompositionStart={onCompositionStart} onCompositionEnd={onCompositionEnd}
          onScroll={event=>{if(mirrorRef.current){
            mirrorRef.current.scrollTop=event.currentTarget.scrollTop;
            mirrorRef.current.scrollLeft=event.currentTarget.scrollLeft;
          }}}
          aria-describedby="payload-shortcuts" spellCheck={false} autoComplete="off"
          autoCapitalize="off" rows={1} maxLength={2000}/>
      </div>
    </div>
    {diagnostic && <div className="terminal-input-note">
      <button type="button" onClick={()=>onDiagnostic?.(diagnostic)}>권한 검사 대상 설명</button>
      <span>{diagnostic.why}</span>
    </div>}
  </div>;
}
