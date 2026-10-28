import React from 'react';
import {it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import App from './App.jsx';

afterEach(()=>vi.unstubAllGlobals());
const trace={category:'sql_injection',raw_input:'admin',effective_input:'admin',phase:'analysis',execution:null,table:null,condition_tree:null,composition:{prefix:'SELECT ',value:'admin',suffix:'',full:'SELECT admin'},lens:{id:'string_value',title:'이름 입력',what:'이름을 비교해요.',why:'문자열이에요.',next:'따옴표를 보세요.',focus:{start:0,end:5},lesson:'strings'}};
const result={success:false,learning_trace:{...trace,phase:'result',execution:{status:'empty',count:0,error:'',label:'SQLite 실제 조회'},table:{columns:['id','username'],rows:[{cells:[1,'admin'],matched:false}]}}};
const messages={413:'입력 전체 크기가 실습 요청 한도를 넘었습니다.',422:'입력 형식·길이·값이 실습 허용 범위를 벗어났습니다.',503:'조회 결과가 표시 가능한 크기를 넘었습니다.'};

it.each([413,422,503])('shows actionable %s rejection and allows a subsequent successful request',async(status)=>{
 let attempts=0;
 vi.stubGlobal('fetch',vi.fn(async(url)=>{
  if(String(url).endsWith('/labs'))return {ok:true,json:async()=>[{id:'sql-injection-easy'}]};
  if(String(url).endsWith('/analyze'))return {ok:true,json:async()=>trace};
  if(++attempts===1)return {ok:false,status,json:async()=>({code:'response_limit',detail:'/private/internal'})};
  return {ok:true,json:async()=>result};
 }));
 render(<App/>);
 const input=screen.getByLabelText('사용자 이름');
 fireEvent.change(input,{target:{value:'admin'}});
 const run=await screen.findByRole('button',{name:'실행하기'});
 await vi.waitFor(()=>expect(run).toBeEnabled());
 fireEvent.click(run);
 expect(await screen.findByRole('alert')).toHaveTextContent(messages[status]);
 expect(screen.queryByText(/private\/internal/)).not.toBeInTheDocument();
 fireEvent.click(run);
 expect(await screen.findByRole('table')).toBeInTheDocument();
 expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('shows input-analysis rejection instead of silently returning to waiting guidance',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(url)=>String(url).endsWith('/labs')?{ok:true,json:async()=>[{id:'sql-injection-easy'}]}:{ok:false,status:422}));
 render(<App/>);
 fireEvent.change(screen.getByLabelText('사용자 이름'),{target:{value:'admin'}});
 expect(await screen.findByText(new RegExp(messages[422]))).toBeInTheDocument();
 expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});


it('does not expose an unexpected network error message',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(url)=>{
  if(String(url).endsWith('/labs'))return {ok:true,json:async()=>[{id:'sql-injection-easy'}]};
  if(String(url).endsWith('/analyze'))return {ok:true,json:async()=>trace};
  throw new Error('/private/unexpected-error');
 }));
 render(<App/>);
 fireEvent.change(screen.getByLabelText('사용자 이름'),{target:{value:'admin'}});
 const run=await screen.findByRole('button',{name:'실행하기'});
 await vi.waitFor(()=>expect(run).toBeEnabled());
 fireEvent.click(run);
 expect(await screen.findByRole('alert')).toHaveTextContent('서버 연결을 확인');
 expect(screen.queryByText(/private/)).not.toBeInTheDocument();
});
