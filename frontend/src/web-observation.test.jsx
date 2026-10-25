import React from 'react';
import {render,screen,fireEvent,waitFor,within} from '@testing-library/react';
import {it,expect,vi,beforeEach} from 'vitest';
import App from './App.jsx';

function trace(value,analysis=false){return {category:'sql_injection',phase:analysis?'analysis':'result',raw_input:value,effective_input:value,
  composition:{prefix:"SELECT * FROM users WHERE username = '",value,suffix:"' AND password = 'wrong'",full:`SELECT * FROM users WHERE username = '${value}' AND password = 'wrong'`},
  execution:analysis?null:{status:'empty',count:0,error:'',label:'SQLite 실제 조회'},
  lens:{title:'입력한 이름을 비교했어요',what:'이름 조건과 비밀번호 조건을 함께 확인해요.',why:'비밀번호가 틀린 값으로 고정됐어요.',next:'따옴표가 만드는 경계를 관찰하세요.',focus:{start:0,end:value.length},lesson:'strings'},
  table:analysis?null:{columns:['id','username'],rows:[{cells:[1,'admin'],matched:false}]},condition_tree:null};}
beforeEach(()=>{
  localStorage.clear();
  vi.stubGlobal('fetch',vi.fn(async(url,options)=>({ok:true,json:async()=>String(url).endsWith('/labs')
    ?[{id:'sql-injection-easy'},{id:'sql-injection-medium'}]
    :String(url).endsWith('/analyze')?trace(JSON.parse(options.body).username,true)
    :{success:false,learning_trace:trace(JSON.parse(options.body).username)}})));
});
async function execute(value='abc'){
  await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  const input=screen.getByLabelText('사용자 이름');
  fireEvent.change(input,{target:{value}});input.focus();
  fireEvent.keyDown(input,{key:'Enter'});
  return {input,dialog:await screen.findByRole('dialog',{name:'실습 관찰 화면'})};
}

it('keeps only input and Lens on the base surface while typing and analyzing',async()=>{
  render(<App/>);
  expect(screen.queryByText('처리 흐름과 결과')).not.toBeInTheDocument();
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  const work=screen.getByRole('region',{name:'통합 학습 작업 공간'});
  expect(work).toContainElement(screen.getByLabelText('사용자 이름'));
  expect(work).toContainElement(screen.getByRole('region',{name:'Lens 설명'}));
  fireEvent.change(screen.getByLabelText('사용자 이름'),{target:{value:'abc'}});
  await screen.findByText('입력한 이름을 비교했어요');
  expect(screen.queryByText('처리 흐름과 결과')).not.toBeInTheDocument();
  expect(fetch.mock.calls.some(([url])=>String(url).endsWith('/attempt'))).toBe(false);
});

it('opens on Enter and really removes the dialog after Escape then Enter',async()=>{
  render(<App/>);
  const {input,dialog}=await execute();
  expect(dialog).toHaveAttribute('aria-modal','true');
  expect(within(dialog).getByRole('heading',{name:'처리 흐름과 결과'})).toBeInTheDocument();
  const close=within(dialog).getByRole('button',{name:'처리 흐름과 결과 닫기'});
  expect(close).toHaveFocus();
  fireEvent.keyDown(close,{key:'Tab',shiftKey:true});
  expect(dialog).toContainElement(document.activeElement);
  fireEvent.keyDown(document,{key:'Escape'});
  expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  fireEvent.keyDown(document,{key:'Enter',repeat:true});
  expect(dialog).toBeInTheDocument();
  fireEvent.keyDown(document,{key:'Enter'});
  expect(dialog).not.toBeInTheDocument();
  expect(screen.queryByText('처리 흐름과 결과')).not.toBeInTheDocument();
  expect(input).toHaveValue('abc');expect(input).toHaveFocus();
});

it('closes immediately with X and can reopen the preserved result from Lens',async()=>{
  render(<App/>);
  const {input,dialog}=await execute("admin'OR'1'='1'--");
  fireEvent.click(within(dialog).getByRole('button',{name:'처리 흐름과 결과 닫기'}));
  expect(dialog).not.toBeInTheDocument();
  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  expect(input).toHaveValue("admin'OR'1'='1'--");
  const history=screen.getByRole('button',{name:'시도 기록 1'});
  history.focus();fireEvent.click(history);
  const reopened=screen.getByRole('dialog',{name:'실습 관찰 화면'});
  expect(within(reopened).getByRole('button',{name:'시도 1 불러오기'})).toBeInTheDocument();
  expect(fetch.mock.calls.filter(([url])=>String(url).endsWith('/attempt'))).toHaveLength(1);
  fireEvent.click(within(reopened).getByRole('button',{name:'처리 흐름과 결과 닫기'}));
  expect(history).toHaveFocus();
});

it('remembers the submitting input before focus is lost while opening the dialog',async()=>{
  const normalFetch=fetch.getMockImplementation();
  let respond;
  fetch.mockImplementation((url,options)=>String(url).endsWith('/attempt')
    ?new Promise(resolve=>{respond=()=>resolve({ok:true,json:async()=>({success:false,learning_trace:trace('abc')})});})
    :normalFetch(url,options));
  render(<App/>);
  await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  const input=screen.getByLabelText('사용자 이름');
  fireEvent.change(input,{target:{value:'abc'}});input.focus();
  fireEvent.keyDown(input,{key:'Enter'});
  await waitFor(()=>expect(respond).toBeTypeOf('function'));
  input.blur();
  respond();
  const dialog=await screen.findByRole('dialog',{name:'실습 관찰 화면'});
  fireEvent.click(within(dialog).getByRole('button',{name:'처리 흐름과 결과 닫기'}));
  expect(input).toHaveFocus();
});
