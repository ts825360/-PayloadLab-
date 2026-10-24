import React from 'react';
import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {it,expect,vi,beforeEach} from 'vitest';
import App from './App.jsx';

beforeEach(()=>{
  localStorage.clear();
  vi.stubGlobal('fetch',vi.fn(async url=>({ok:true,json:async()=>String(url).endsWith('/labs')?['sql-injection','reflected-xss','idor','ssrf','command-injection','linux-basics'].flatMap(id=>['easy','medium'].map(d=>({id:`${id}-${d}`}))).concat({id:'permissions-easy'}):{phase:'analysis',category:'permissions',lens:{title:'아직 실행하지 않았어요',what:'명령 분석',focus:{start:0,end:6}}}})));
});

it('starts SQL Easy with an actionable guide rather than an empty Lens slogan',async()=>{
  render(<App/>);
  expect(screen.getByRole('region',{name:'Lens 설명'})).toContainElement(screen.getByRole('region',{name:'학습 안내'}));
  expect(screen.getByRole('button',{name:'입력 예시 넣기'})).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'입력 예시 넣기'}));
  expect(screen.getByLabelText('사용자 이름')).toHaveValue('admin');
  expect(fetch.mock.calls.some(([url])=>String(url).endsWith('/attempt'))).toBe(false);
});

it('distinguishes planned permission Normal from unavailable or failed server connection',async()=>{
  render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:/권한상승 기초/}));
  fireEvent.click(screen.getByRole('button',{name:/Normal/}));
  expect(screen.getByRole('status')).toHaveTextContent('Normal은 구현 예정');
  expect(screen.queryByRole('button',{name:'연결 다시 시도'})).not.toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'실행하기'})).not.toBeInTheDocument();
  expect(screen.getByRole('region',{name:'학습 안내'})).toHaveTextContent('Easy');
});

it('keeps Normal available for every pre-agreed web/command-quiz category',async()=>{
  render(<App/>);
  for(const name of [/SQL Injection/,/Reflected XSS/,/IDOR/,/SSRF/,/Command Injection/,/Linux 명령어/]){
    fireEvent.click(screen.getByRole('button',{name}));
    fireEvent.click(screen.getByRole('button',{name:'Normal'}));
    await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
    expect(screen.queryByText('Normal은 구현 예정')).not.toBeInTheDocument();
  }
});

it('does not let an unsupported permission command poison later virtual history',async()=>{
  fetch.mockImplementation(async(url,options)=>{
    if(String(url).endsWith('/labs'))return {ok:true,json:async()=>[{id:'permissions-easy'}]};
    const payload=JSON.parse(options.body);
    const status=payload.command==='whoami'?'command_ok':'unsupported';
    const trace={category:'permissions',simulated:true,phase:'result',raw_input:payload.command,effective_input:payload.command,composition:{prefix:'',value:payload.command,suffix:'',full:payload.command},lens:{title:'가상 명령 확인',what:'제한된 명령을 처리해요.',why:'가상 연습',next:'whoami',focus:{start:0,end:0}},execution:{status,stdout:status==='command_ok'?'student':'',stderr:status==='unsupported'?'지원하지 않는 명령':'',exit_code:status==='unsupported'?1:0,label:'교육용 모의 실행'},simulation:{nodes:[],edges:[]},terminal:{current_user:'student',prompt:'student@practice:/lab$ ',files:[]}};
    return {ok:true,json:async()=>String(url).endsWith('/analyze')?{...trace,phase:'analysis',execution:null}:{success:false,learning_trace:trace}};
  });
  render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:/권한상승 기초/}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  for(const command of ['not-a-command','whoami']){
    fireEvent.change(screen.getByLabelText('터미널 명령어'),{target:{value:command}});
    fireEvent.click(screen.getByRole('button',{name:'실행하기'}));
    await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  }
  const attempts=fetch.mock.calls.filter(([url])=>String(url).endsWith('/attempt'));
  expect(JSON.parse(attempts[1][1].body).history).toEqual([]);
});

it('connects the current raw error to Lens and keeps old diagnostics local after editing',async()=>{
  const command='cat /lab/report.txt';
  const trace={category:'permissions',simulated:true,phase:'result',raw_input:command,
    composition:{prefix:'',value:command,suffix:'',full:command},
    lens:{title:'읽기 권한을 확인하세요',what:'읽기가 거부됐어요.',
      why:'소유자와 현재 사용자를 비교해요.',next:'whoami',focus:{start:0,end:3}},
    execution:{status:'permission_denied',stdout:'',stderr:'cat: /lab/report.txt: Permission denied\n',exit_code:1},
    simulation:{nodes:[],edges:[]},terminal:{prompt:'student@practice:/lab$ ',files:[]}};
  fetch.mockImplementation(async url=>({ok:true,json:async()=>{
    if(String(url).endsWith('/labs'))return [{id:'permissions-easy'}];
    if(String(url).endsWith('/analyze'))return {...trace,phase:'analysis',execution:null};
    return {success:false,learning_trace:trace};
  }}));
  render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:/권한상승 기초/}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  const input=screen.getByLabelText('터미널 명령어');
  fireEvent.change(input,{target:{value:command}});
  fireEvent.click(screen.getByRole('button',{name:'실행하기'}));
  const mark=await screen.findByRole('button',{name:'Permission denied'});
  expect(input.closest('.terminal-input').querySelector('mark').textContent).toBe('/lab/report.txt');
  fireEvent.mouseEnter(mark);
  await screen.findByRole('tooltip');
  fireEvent.keyDown(document,{key:'Escape'});
  await waitFor(()=>expect(screen.queryByRole('tooltip')).not.toBeInTheDocument());
  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  fireEvent.click(mark);
  expect(screen.getByRole('region',{name:'Lens 설명'})).toHaveFocus();
  input.focus();
  fireEvent.change(input,{target:{value:'whoami'}});
  expect(input.closest('.terminal-input').querySelector('mark')).toBeNull();
  expect(screen.queryByRole('button',{name:'Permission denied'})).not.toBeInTheDocument();
  expect(input).toHaveFocus();
  expect(screen.getByLabelText('터미널 원문 출력')).toHaveTextContent('Permission denied');
});
