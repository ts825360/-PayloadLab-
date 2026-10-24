import {useState} from 'react';
import {
  FloatingPortal, autoUpdate, flip, offset, shift, useDismiss, useFloating,
  useFocus, useHover, useInteractions, useRole,
} from '@floating-ui/react';
import './diagnostic-text.css';

function DiagnosticMark({text, diagnostic, onSelect}) {
  const [open,setOpen]=useState(false);
  const {refs,floatingStyles,context}=useFloating({
    open,onOpenChange:setOpen,whileElementsMounted:autoUpdate,
    middleware:[offset(8),flip(),shift({padding:12})],
  });
  const hover=useHover(context,{move:false});
  const focus=useFocus(context);
  const dismiss=useDismiss(context);
  const role=useRole(context,{role:'tooltip'});
  const {getReferenceProps,getFloatingProps}=useInteractions([hover,focus,dismiss,role]);
  const selectable=typeof onSelect==='function';
  const Anchor=selectable?'button':'span';
  return <>
    <Anchor ref={refs.setReference}
      {...(selectable?{type:'button'}:{tabIndex:0})}
      className="terminal-diagnostic-mark" data-severity={diagnostic.severity}
      data-diagnostic-id={diagnostic.id}
      {...getReferenceProps({
        onClick:()=>{if(selectable)onSelect(diagnostic);},
        onKeyDown:event=>{
          if(event.key==='Escape' && open){
            event.preventDefault();event.stopPropagation();setOpen(false);
          }
        },
      })}>{text}</Anchor>
    {open && <FloatingPortal>
      <div ref={refs.setFloating} style={floatingStyles}
        className="terminal-diagnostic-tooltip" {...getFloatingProps()}>
        <strong>{diagnostic.title}</strong>
        <span>{diagnostic.summary || diagnostic.why}</span>
      </div>
    </FloatingPortal>}
  </>;
}

/** Render raw text with exact codepoint marks. Descriptions live outside the raw node. */
export default function DiagnosticText({text='',source,diagnostics=[],onSelect}) {
  const raw=typeof text==='string'?text:'';
  const characters=Array.from(raw);
  const marks=[];
  for(const diagnostic of Array.isArray(diagnostics)?diagnostics:[]){
    for(const target of Array.isArray(diagnostic?.targets)?diagnostic.targets:[]){
      if(target?.source===source && target.unit==='codepoint' &&
        Number.isInteger(target.start) && Number.isInteger(target.end) &&
        target.start>=0 && target.end>target.start && target.end<=characters.length){
        marks.push({...target,diagnostic});
      }
    }
  }
  marks.sort((a,b)=>a.start-b.start || a.end-b.end);
  const pieces=[];
  let cursor=0;
  for(const mark of marks){
    if(mark.start<cursor)continue;
    pieces.push(characters.slice(cursor,mark.start).join(''));
    pieces.push(<DiagnosticMark key={`${mark.diagnostic.id}-${mark.start}-${mark.end}`}
      text={characters.slice(mark.start,mark.end).join('')}
      diagnostic={mark.diagnostic} onSelect={onSelect}/>);
    cursor=mark.end;
  }
  pieces.push(characters.slice(cursor).join(''));
  return <span className="terminal-diagnostic-text">{pieces}</span>;
}
