import {useCallback,useEffect,useRef,useState} from 'react';
import {useReducedMotion} from 'motion/react';
import {CATEGORIES} from '../learning-content.js';
import LearningPrimer from '../LearningPrimer.jsx';
import LensCloseConfirmation from '../LensCloseConfirmation.jsx';
import TerminalTranscript from './TerminalTranscript.jsx';
import TerminalInspector from './TerminalInspector.jsx';
import './linux-desktop.css';

export const isLinuxCategory=id=>['command_injection','linux_basics','permissions'].includes(id);

export default function LinuxDesktop({category,difficulty,onCategory,onDifficulty,onReturn,
  history,selected,trace,analysisTrace,stale,inputRef,lensRef,onInput,renderDock,
  booting,onBootComplete,connection,onConnect}) {
  const reduce=useReducedMotion();
  const [helpOpen,setHelpOpen]=useState(false),[expanded,setExpanded]=useState(false),[closeRequested,setCloseRequested]=useState(false);
  const inspectorRef=useRef(null),skipRef=useRef(null);
  const closeObservation=useCallback(()=>{setCloseRequested(false);setExpanded(false);inputRef.current?.focus({preventScroll:true});},[inputRef]);
  const cancelClose=useCallback(()=>setCloseRequested(false),[]);
  useEffect(()=>{
    if(!booting)return;
    if(reduce){onBootComplete();return;}
    skipRef.current?.focus();
    const timer=setTimeout(onBootComplete,1050);
    return()=>clearTimeout(timer);
  },[booting,reduce,onBootComplete]);
  useEffect(()=>{if(!booting)inputRef.current?.focus({preventScroll:true});},[booting,category.id,inputRef]);
  useEffect(()=>{setExpanded(false);setCloseRequested(false);},[category.id,difficulty]);
  useEffect(()=>{
    function keys(event){
      if(event.key!=='Escape' || event.isComposing || event.keyCode===229 || event.repeat)return;
      if(document.querySelector('.terminal-diagnostic-tooltip,.concept-dialog,.lens-close-confirmation'))return;
      if(helpOpen){event.preventDefault();setHelpOpen(false);}
      else if(expanded){event.preventDefault();setCloseRequested(true);}
    }
    document.addEventListener('keydown',keys);
    return()=>document.removeEventListener('keydown',keys);
  },[helpOpen,expanded]);
  function openObservation(){setHelpOpen(false);setExpanded(true);requestAnimationFrame(()=>inspectorRef.current?.focus({preventScroll:true}));}
  const metadata=analysisTrace || trace;
  const commands=metadata?.terminal?.supported_commands || metadata?.command_model?.supported_commands || [];
  const displayTrace=selected?.result.learning_trace || trace;
  return <div className="linux-desktop" role="region" aria-label="Linux 실습 데스크톱">
    <header className="linux-desktop-bar">
      <button className="linux-brand" type="button" aria-label="웹 학습 화면으로 돌아가기" onClick={onReturn}><img src="/brand/payloadlab-wordmark-dark.svg" alt="PayloadLab" width="180" height="42"/><span>← 웹 학습</span></button>
      <span className="linux-desktop-name">LINUX WORKSPACE <i/> <span>교육용 모의 환경</span></span>
      <span className="linux-connection">{connection==='ready'?'● 연결됨':connection==='loading'?'◌ 연결 중':'○ 연결 필요'}</span>
    </header>
    <main className="linux-desktop-main">
      <section className="linux-window" id="linux-terminal" role="region" aria-label="교육용 터미널">
        <header className="linux-window-titlebar"><div className="linux-window-dots" aria-hidden="true"><i/><i/><i/></div><span>payloadlab@practice — /lab</span><button type="button" aria-label="터미널 창 닫기" onClick={onReturn}>×</button></header>
        <div className="linux-window-toolbar">
          <nav aria-label="터미널 학습 유형">{CATEGORIES.filter(item=>isLinuxCategory(item.id)).map(item=><button key={item.id} type="button" aria-current={item.id===category.id?'page':undefined} onClick={()=>onCategory(item.id)}><span>{item.short}</span>{item.label}</button>)}</nav>
          <div className="linux-difficulty" role="group" aria-label="난이도 선택">{['easy','medium'].map(level=><button type="button" key={level} aria-pressed={difficulty===level} onClick={()=>onDifficulty(level)}>{level==='easy'?'Easy':'Normal'}</button>)}</div>
          <button className="linux-help-toggle" type="button" aria-expanded={helpOpen} aria-controls="linux-inspector" onClick={()=>setHelpOpen(!helpOpen)}>지원 명령 보기</button>
        </div>
        <section className="linux-window-body" aria-label="통합 학습 작업 공간">
          <div className="linux-terminal-log">
            <div className="linux-terminal-banner"><pre aria-hidden="true">{'┌─ PAYLOAD / LAB ─────────────────────┐\n│  TRY. UNDERSTAND. TRY AGAIN.        │\n└────────────────────────────────────┘'}</pre><span>{category.label} / {difficulty==='easy'?'Easy':'Normal'}</span></div>
            {!history.length && <LearningPrimer category={category} difficulty={difficulty} onStart={()=>inputRef.current?.focus()}/>}
            {connection==='error' && <div role="alert" className="linux-offline">연결을 확인해주세요. 작성 중인 명령은 유지됩니다. <button type="button" onClick={onConnect}>연결 다시 시도</button></div>}
            <TerminalTranscript entries={history} selectedId={selected?.id} onDiagnostic={stale?undefined:()=>lensRef.current?.focus({preventScroll:true})}/>
          </div>
          {renderDock(openObservation)}
          <aside id="linux-inspector" className="linux-inspector" role="region" aria-label="터미널 관찰" tabIndex={-1} ref={inspectorRef} data-expanded={expanded}>
            <header><div><span className="terminal-section-label">OBSERVATION</span><h2>{helpOpen?'지원하는 입력':'지금 무슨 일이 일어났을까요?'}</h2></div><button type="button" onClick={()=>expanded?setCloseRequested(true):openObservation()} aria-label={expanded?'관찰 전체로 돌아가기':'처리 흐름 확대'}>{expanded?'닫기':'↗'}</button></header>
            {stale && <p className="terminal-stale">이전 실행 기준입니다. 새 명령을 실행하면 관찰이 갱신돼요.</p>}
            {helpOpen?<div className="linux-command-help"><p>{category.id==='command_injection'?'입력은 호스트 값입니다. 아래는 구분자 뒤에서 모형화하는 명령입니다.':'이 실습이 해석하는 명령 전체입니다. 선택하면 입력만 채워져요.'}</p>
              {!commands.length && <p>서버에서 지원 목록을 확인하고 있어요.</p>}
              <ul>{commands.map(command=><li key={command}><button type="button" aria-label={`${command} 입력하기`} onClick={()=>{onInput(category.id==='command_injection'?`example.com; ${command}`:command);inputRef.current?.focus();}}><code>{command}</code><span>↙</span></button></li>)}</ul>
            </div>:<TerminalInspector category={category} trace={displayTrace}/>}
          </aside>
        </section>
        <footer className="linux-window-footer"><span>Enter 실행 · Shift+Enter 줄바꿈</span><span>로고를 누르면 웹 학습으로 돌아갑니다 ↖</span></footer>
      </section>
      <span className="linux-desktop-caption">작은 시도를 이어가며, 원리를 발견하는 공간.</span>
    </main>
    {booting && <section className="linux-boot" role="region" aria-label="가상 환경 준비" aria-live="polite"><div><span>PAYLOADLAB / LEARNING SESSION</span><pre>{'[ok] 교육용 명령 규칙 연결\n[ok] 가상 /lab 작업 공간 준비\n[ok] Lens 및 관찰 도구 연결\n\n터미널을 여는 중…'}</pre><button type="button" ref={skipRef} onClick={onBootComplete}>준비 건너뛰기 <span aria-hidden="true">↗</span></button></div></section>}
    {closeRequested && <LensCloseConfirmation className="linux-close-layer" onConfirm={closeObservation} onCancel={cancelClose}/>}
  </div>;
}
