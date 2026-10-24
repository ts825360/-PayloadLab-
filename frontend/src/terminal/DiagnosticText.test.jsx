import React from 'react';
import {fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import {expect, it, vi} from 'vitest';
import DiagnosticText from './DiagnosticText.jsx';

const text='🔒 cat: /lab/report.txt: Permission denied\n';
const start=Array.from('🔒 cat: /lab/report.txt: ').length;
const diagnostic={id:'permission-denied',severity:'warning',title:'읽기 권한이 없어요',
  why:'명령 오타가 아니라 현재 사용자의 권한 문제예요.',next:'소유자와 현재 사용자를 비교하세요.',
  targets:[{source:'stderr',start,end:start+17,unit:'codepoint'}]};

function show(props={}) {
  return render(<pre aria-label="원문"><DiagnosticText text={text} source="stderr"
    diagnostics={[diagnostic]} onSelect={()=>{}} {...props}/></pre>);
}

it('marks exactly the codepoint range while preserving the entire raw text',()=>{
  show();
  expect(screen.getByRole('button',{name:'Permission denied'})).toHaveAttribute('data-severity','warning');
  expect(screen.getByLabelText('원문').textContent).toBe(text);
});

it('opens a short noninteractive explanation on hover',async()=>{
  show();
  fireEvent.mouseEnter(screen.getByRole('button',{name:'Permission denied'}));
  const tooltip=await screen.findByRole('tooltip');
  expect(tooltip).toHaveTextContent('읽기 권한이 없어요');
  expect(tooltip).toHaveTextContent('명령 오타가 아니라');
  expect(within(tooltip).queryByRole('button')).not.toBeInTheDocument();
  expect(screen.getByLabelText('원문').textContent).toBe(text);
});

it('supports keyboard focus and consumes Escape without closing an outer view',async()=>{
  const outer=vi.fn();
  const view=render(<div onKeyDown={outer}><DiagnosticText text={text} source="stderr"
    diagnostics={[diagnostic]} onSelect={()=>{}}/></div>);
  const mark=screen.getByRole('button',{name:'Permission denied'});
  fireEvent.focus(mark);
  await screen.findByRole('tooltip');
  fireEvent.keyDown(mark,{key:'Escape'});
  await waitFor(()=>expect(screen.queryByRole('tooltip')).not.toBeInTheDocument());
  expect(outer).not.toHaveBeenCalled();
  view.unmount();
});

it('selects the same diagnostic for the existing Lens',()=>{
  const selected=vi.fn();
  show({onSelect:selected});
  fireEvent.click(screen.getByRole('button',{name:'Permission denied'}));
  expect(selected).toHaveBeenCalledWith(diagnostic);
});

it('ignores malformed, out-of-bounds and other-source ranges',()=>{
  show({diagnostics:[{...diagnostic,targets:[
    {source:'stderr',start:-1,end:2,unit:'codepoint'},
    {source:'stderr',start:0,end:9999,unit:'codepoint'},
    {source:'stderr',start:0,end:2,unit:'utf16'},
    {source:'input',start:0,end:2,unit:'codepoint'},
  ]}]});
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  expect(screen.getByLabelText('원문').textContent).toBe(text);
});

it('renders untrusted output only as text',()=>{
  show({text:'<img src=x onerror=alert(1)>',diagnostics:[]});
  expect(screen.queryByRole('img')).not.toBeInTheDocument();
  expect(screen.getByLabelText('원문').textContent).toBe('<img src=x onerror=alert(1)>');
});

it('can explain older output without offering a misleading current-Lens action',async()=>{
  show({onSelect:undefined});
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  fireEvent.focus(screen.getByText('Permission denied'));
  expect(await screen.findByRole('tooltip')).toHaveTextContent('읽기 권한이 없어요');
});
