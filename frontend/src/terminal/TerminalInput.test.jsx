import React,{createRef} from 'react';
import {render,screen,fireEvent} from '@testing-library/react';
import {it,expect,vi} from 'vitest';
import TerminalInput from './TerminalInput.jsx';

const value='cat /lab/보고서🔒.txt';
const target={source:'input',unit:'codepoint',start:4,end:Array.from(value).length};
const diagnostic={id:'permission-denied',severity:'warning',title:'파일 권한을 확인해요',
  why:'명령 오타가 아니라 현재 사용자의 읽기 권한 문제예요.',targets:[target]};
function show(overrides={}) {
  const inputRef=createRef(),onChange=vi.fn(),onDiagnostic=vi.fn();
  const props={label:'터미널 명령어',value,prompt:'student@practice:/lab$ ',
    inputRef,onChange,onDiagnostic,diagnostics:[diagnostic],...overrides};
  const view=render(<TerminalInput {...props}/>);
  return {...view,input:screen.getByRole('textbox',{name:'터미널 명령어'}),props};
}

it('keeps the real editable value and ref separate from a hidden decoration',()=>{
  const {input,props,container}=show();
  expect(input).toHaveValue(value);
  expect(props.inputRef.current).toBe(input);
  expect(screen.getAllByRole('textbox')).toHaveLength(1);
  const mirror=container.querySelector('.terminal-input-mirror');
  expect(mirror).toHaveAttribute('aria-hidden','true');
  expect(mirror.querySelector('mark').textContent).toBe('/lab/보고서🔒.txt');
  expect(input).toHaveAttribute('maxlength','2000');
});

it('returns Korean, emoji and newlines without rewriting the command',()=>{
  const {input,props}=show();
  fireEvent.change(input,{target:{value:'cat 한글🔒\nls -l'}});
  expect(props.onChange).toHaveBeenCalledWith('cat 한글🔒\nls -l');
});

it('synchronizes the decoration with native input scrolling',()=>{
  const {input,container}=show();
  input.scrollTop=42;input.scrollLeft=17;
  fireEvent.scroll(input);
  const mirror=container.querySelector('.terminal-input-mirror');
  expect(mirror.scrollTop).toBe(42);
  expect(mirror.scrollLeft).toBe(17);
});

it('connects the exact diagnostic to Lens without interpreting it as a typo',()=>{
  const {props}=show();
  fireEvent.click(screen.getByRole('button',{name:'권한 검사 대상 설명'}));
  expect(props.onDiagnostic).toHaveBeenCalledWith(diagnostic);
  expect(screen.getByText('명령 오타가 아니라 현재 사용자의 읽기 권한 문제예요.')).toBeInTheDocument();
});

it('clears the old underline when the current diagnostics are removed',()=>{
  const {props,rerender,container}=show();
  rerender(<TerminalInput {...props} value="whoami" diagnostics={[]}/>);
  expect(container.querySelector('mark')).not.toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'권한 검사 대상 설명'})).not.toBeInTheDocument();
  expect(screen.getByRole('textbox')).toHaveValue('whoami');
});


it('recalculates capped input height after viewport resize without changing the value',()=>{
  const {input,unmount}=show({value:'긴 입력을 유지한 화면 크기 변경'});
  let contentHeight=208;
  Object.defineProperty(input,'scrollHeight',{configurable:true,get:()=>contentHeight});
  fireEvent(window,new Event('resize'));
  expect(input.style.height).toBe('144px');
  expect(input).toHaveValue('긴 입력을 유지한 화면 크기 변경');
  contentHeight=52;
  fireEvent(window,new Event('resize'));
  expect(input.style.height).toBe('52px');
  const remove=vi.spyOn(window,'removeEventListener');
  unmount();
  expect(remove).toHaveBeenCalledWith('resize',expect.any(Function));
  remove.mockRestore();
});
