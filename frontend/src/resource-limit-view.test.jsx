import React from 'react';
import {it,expect,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import ExecutionCanvas from './ExecutionCanvas.jsx';
import {CATEGORIES} from './learning-content.js';

const stopped=(status)=>({category:'sql_injection',execution:{status,count:0,error:'자원 한도',label:'SQLite 제한 상태'},table:null,condition_tree:null,lens:{title:status==='blocked'?'허용된 실습 연산 범위를 확인하세요':'실습 계산 한도에 도달했어요',what:'조회를 중단했습니다.',why:'문법 오류와 다른 상태입니다.',next:'입력 부분 하나를 줄여 다시 시도하세요.'}});

it.each(['resource_limit','blocked'])('renders %s without a table or false empty result',status=>{
 render(<ExecutionCanvas trace={stopped(status)} category={CATEGORIES[0]} onGroup={vi.fn()}/>);
 expect(screen.getByRole('heading',{name:stopped(status).lens.title})).toBeInTheDocument();
 expect(screen.getByText('문법 오류와 다른 상태입니다.')).toBeInTheDocument();
 expect(screen.getByText('입력 부분 하나를 줄여 다시 시도하세요.')).toBeInTheDocument();
 expect(screen.queryByRole('table')).not.toBeInTheDocument();
 expect(screen.queryByText(/0개 행 반환/)).not.toBeInTheDocument();
});

it('returns from limit notice to a normal table after a new successful result',()=>{
 const {rerender}=render(<ExecutionCanvas trace={stopped('resource_limit')} category={CATEGORIES[0]} onGroup={vi.fn()}/>);
 rerender(<ExecutionCanvas category={CATEGORIES[0]} onGroup={vi.fn()} trace={{category:'sql_injection',execution:{status:'matched',count:2,label:'SQLite 실제 조회'},condition_tree:null,table:{columns:['id','username'],rows:[{cells:[1,'admin'],matched:true},{cells:[2,'guest'],matched:true}]}}}/>);
 expect(screen.getByRole('table')).toBeInTheDocument();
 expect(screen.queryByRole('heading',{name:'실습 계산 한도에 도달했어요'})).not.toBeInTheDocument();
});
