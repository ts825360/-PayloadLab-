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
