import React from 'react';
import {render,screen,fireEvent,waitFor,within} from '@testing-library/react';
import {it,expect,vi,beforeEach} from 'vitest';
import App from '../App.jsx';
import {CATEGORIES} from '../learning-content.js';

const preferences=vi.hoisted(()=>({reduced:false}));
vi.mock('motion/react',async original=>({...await original(),useReducedMotion:()=>preferences.reduced}));

const labs=CATEGORIES.flatMap(category=>['easy','medium'].filter(level=>!category.plannedLevels?.includes(level)).map(level=>({id:`${category.id.replaceAll('_','-')}-${level}`})));
function trace(command='') {
  return {category:'permissions',phase:'result',simulated:true,raw_input:command,effective_input:command,
    composition:{prefix:'',value:command,suffix:'',full:command},
    lens:{title:'읽기 권한을 확인해요',what:'현재 사용자에게 읽기 권한이 없어요.',why:'명령 오타가 아니라 파일 접근 권한의 문제예요.',next:'whoami와 파일 소유자를 비교하세요.',focus:{start:0,end:command.length}},
    execution:{status:'permission_denied',stdout:'',stderr:'cat: /lab/report.txt: Permission denied\n',exit_code:1},
    simulation:{nodes:[{id:'identity',label:'현재 사용자',value:'student'},{id:'result',label:'권한 검사',value:'permission_denied'}]},
    terminal:{current_user:'student',prompt:'student@practice:/lab$ ',supported_commands:['whoami','id','pwd','cat /lab/report.txt','sudo -l'],files:[{path:'/lab/report.txt',owner:'mentor',permissions:'-rw-------'}]}};
}
beforeEach(()=>{
  preferences.reduced=false;
  localStorage.clear();
  vi.stubGlobal('fetch',vi.fn(async(url,options)=>({ok:true,json:async()=>{
    if(String(url).endsWith('/labs'))return labs;
    const command=JSON.parse(options.body).command || '';
    const value=trace(command);
    return String(url).endsWith('/analyze')?{...value,phase:'analysis',execution:null}:{success:false,learning_trace:value};
  }})));
});

it('enters immediately when reduced motion is requested',()=>{
  preferences.reduced=true;
  render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:/권한상승 기초/}));
  expect(screen.getByRole('region',{name:'Linux 실습 데스크톱'})).toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'준비 건너뛰기'})).not.toBeInTheDocument();
});
function enter(name=/권한상승 기초/) {
  fireEvent.click(screen.getByRole('button',{name}));
  const skip=screen.queryByRole('button',{name:'준비 건너뛰기'});
  if(skip)fireEvent.click(skip);
}

it.each([[/Command Injection/,'호스트 이름'],[/Linux 명령어/,'명령어 빈칸'],[/권한상승 기초/,'터미널 명령어']])('opens a full Linux workspace for %s instead of a small web input',async(name,label)=>{
  render(<App/>);enter(name);
  const desktop=screen.queryByRole('region',{name:'Linux 실습 데스크톱'});
  expect(desktop).not.toBeNull();
  const window=within(desktop).getByRole('region',{name:'교육용 터미널'});
  expect(window).toContainElement(screen.getByLabelText(label));
  expect(window).toContainElement(screen.getByRole('region',{name:'Lens 설명'}));
  expect(within(window).getByRole('region',{name:'터미널 기록'})).toBeInTheDocument();
  expect(screen.queryByRole('navigation',{name:'공격 유형'})).not.toBeInTheDocument();
  expect(screen.queryByRole('region',{name:'실습 관찰 화면'})).not.toBeInTheDocument();
  expect(screen.getByRole('button',{name:'Easy'})).toHaveAttribute('aria-pressed','true');
});

it('preserves web and terminal drafts through the logo and does not replay preparation inside Linux',async()=>{
  render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:'Normal'}));
  fireEvent.change(screen.getByLabelText('사용자 이름'),{target:{value:"admin' OR '1'='1'--"}});
  fireEvent.click(screen.getByRole('button',{name:/권한상승 기초/}));
  fireEvent.click(screen.getByRole('button',{name:'준비 건너뛰기'}));
  fireEvent.change(screen.getByLabelText('터미널 명령어'),{target:{value:'whoami'}});
  fireEvent.click(screen.getByRole('button',{name:/Linux 명령어/}));
  expect(screen.queryByRole('button',{name:'준비 건너뛰기'})).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('명령어 빈칸'),{target:{value:'ls'}});
  fireEvent.click(screen.getByRole('button',{name:/권한상승 기초/}));
  expect(screen.getByLabelText('터미널 명령어')).toHaveValue('whoami');
  fireEvent.click(screen.getByRole('button',{name:'웹 학습 화면으로 돌아가기'}));
  expect(screen.getByLabelText('사용자 이름')).toHaveValue("admin' OR '1'='1'--");
  expect(screen.getByRole('button',{name:'Normal'})).toHaveAttribute('aria-pressed','true');
  enter(/권한상승 기초/);
  expect(screen.getByLabelText('터미널 명령어')).toHaveValue('whoami');
  expect(screen.queryByRole('button',{name:'준비 건너뛰기'})).not.toBeInTheDocument();
});

it('runs into the transcript, opens Lens from the raw error, and confirms only observation close',async()=>{
  render(<App/>);enter();
  await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  const input=screen.getByLabelText('터미널 명령어');
  fireEvent.change(input,{target:{value:'cat /lab/report.txt'}});
  fireEvent.keyDown(input,{key:'Enter'});
  const mark=await screen.findByRole('button',{name:'Permission denied'});
  expect(input).toHaveValue('');
  expect(screen.getByLabelText('명령 원문')).toHaveTextContent('cat /lab/report.txt');
  fireEvent.click(mark);
  expect(screen.getByRole('region',{name:'Lens 설명'})).toHaveFocus();
  fireEvent.click(screen.getByRole('button',{name:'처리 흐름 크게 보기'}));
  expect(screen.getByRole('region',{name:'터미널 관찰'})).toHaveAttribute('data-expanded','true');
  fireEvent.keyDown(document,{key:'Escape'});
  expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  fireEvent.keyDown(document,{key:'Enter'});
  expect(screen.getByRole('region',{name:'터미널 관찰'})).toHaveAttribute('data-expanded','false');
  expect(screen.getByRole('region',{name:'Linux 실습 데스크톱'})).toBeInTheDocument();
  expect(input).toHaveFocus();
});

it('fills a server-provided supported command without executing it',async()=>{
  render(<App/>);enter();
  fireEvent.click(screen.getByRole('button',{name:'지원 명령 보기'}));
  const command=await screen.findByRole('button',{name:'sudo -l 입력하기'});
  fireEvent.click(command);
  expect(screen.getByLabelText('터미널 명령어')).toHaveValue('sudo -l');
  expect(fetch.mock.calls.some(([url])=>String(url).endsWith('/attempt'))).toBe(false);
});

it('keeps a new draft written while an attempt is pending and ignores a late response after web return',async()=>{
  let respond;
  const normal=fetch.getMockImplementation();
  fetch.mockImplementation((url,options)=>String(url).endsWith('/attempt')
    ?new Promise(resolve=>{respond=()=>resolve({ok:true,json:async()=>({success:false,learning_trace:trace('cat /lab/report.txt')})});})
    :normal(url,options));
  render(<App/>);enter();
  await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  const input=screen.getByLabelText('터미널 명령어');
  fireEvent.change(input,{target:{value:'cat /lab/report.txt'}});
  fireEvent.keyDown(input,{key:'Enter'});
  fireEvent.change(input,{target:{value:'id'}});
  respond();
  await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
  expect(input).toHaveValue('id');
  fireEvent.keyDown(input,{key:'Enter'});
  fireEvent.click(screen.getByRole('button',{name:'웹 학습 화면으로 돌아가기'}));
  respond();
  await waitFor(()=>expect(screen.getByLabelText('사용자 이름')).toBeInTheDocument());
  expect(screen.queryByText('읽기 권한을 확인해요')).not.toBeInTheDocument();
});
