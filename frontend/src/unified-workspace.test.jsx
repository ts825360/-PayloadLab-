import React from 'react';
import {render,screen,fireEvent,within,waitFor} from '@testing-library/react';
import {it,expect,beforeEach,vi} from 'vitest';
import App from './App.jsx';
import {CATEGORIES} from './learning-content.js';
import {LensPanel} from './WorkspaceParts.jsx';

const labs=CATEGORIES.flatMap(category=>['easy','medium'].filter(d=>!category.plannedLevels?.includes(d)).map(d=>({id:`${category.id.replaceAll('_','-')}-${d}`})));
beforeEach(()=>{localStorage.clear();vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>labs})));});

it('contains input, fixed Lens, and observation in a single named learning tool',()=>{
  render(<App/>);
  const work=screen.getByRole('region',{name:'통합 학습 작업 공간'});
  expect(work).toContainElement(screen.getByLabelText('사용자 이름'));
  expect(work).toContainElement(screen.getByRole('region',{name:'Lens 설명'}));
  expect(work).toContainElement(screen.getByRole('region',{name:'실습 관찰 화면'}));
  expect(work).toHaveAttribute('data-phase','before-input');
});

it('provides definition, conditions, flow, goal and next action before input in all 13 supported lab combinations',async()=>{
  render(<App/>);
  for(const category of CATEGORIES){
    for(const level of ['easy','medium']){
      if(category.plannedLevels?.includes(level))continue;
      fireEvent.click(screen.getByRole('button',{name:new RegExp(category.label)}));
      fireEvent.click(screen.getByRole('button',{name:level==='easy'?'Easy':'Normal'}));
      const primer=screen.getByRole('region',{name:'시작 전 학습'});
      expect(within(primer).getByRole('heading',{name:'어떤 원리인가요?'})).toBeInTheDocument();
      expect(within(primer).getByRole('heading',{name:'성립 조건'})).toBeInTheDocument();
      expect(within(primer).getByRole('list',{name:'입력에서 결과까지'}).children).toHaveLength(3);
      expect(within(primer).getByRole('heading',{name:'이번 학습 목표'})).toBeInTheDocument();
      expect(within(primer).getByRole('button',{name:'입력하러 가기'})).toBeInTheDocument();
      await waitFor(()=>expect(screen.getByRole('button',{name:'실행하기'})).toBeEnabled());
    }
  }
});

it('uses real task-specific controls rather than only renaming one text box',()=>{
  render(<App/>);
  expect(screen.getByLabelText('실습용 고정 비밀번호')).toBeDisabled();
  fireEvent.click(screen.getByRole('button',{name:/Reflected XSS/}));
  expect(screen.getByRole('region',{name:'교육용 검색 페이지'})).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:/IDOR/}));
  expect(screen.getByRole('button',{name:'본인 주문 1042 선택'})).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'타인 주문 1043 선택'}));
  expect(screen.getByLabelText('주문번호')).toHaveValue('1043');
  expect(fetch.mock.calls.some(([url])=>String(url).endsWith('/attempt'))).toBe(false);
  fireEvent.click(screen.getByRole('button',{name:/SSRF/}));
  expect(screen.getByText('요청 주체: 가상 미리보기 서버')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:/Command Injection/}));
  expect(screen.getByText('서버 연결 진단')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:/권한상승 기초/}));
  expect(screen.getByLabelText('가상 터미널 프롬프트')).toHaveTextContent('student@practice:/lab$');
});

it('puts the current input explanation first without losing the guided lesson',async()=>{
  render(<LensPanel guide={<section aria-label="학습 안내">단계형 안내</section>} trace={{lens:{title:'이름을 비교했어요',what:'admin과 다른 이름이에요.',why:'값을 비교해요',next:'다시 입력해보세요'}}} difficulty="easy" onFocus={()=>{}} onLesson={()=>{}} onRetry={()=>{}}/>);
  expect(screen.getByRole('button',{name:'이번 입력 설명'})).toHaveAttribute('aria-pressed','true');
  expect(screen.getByText('admin과 다른 이름이에요.')).toBeVisible();
  fireEvent.click(screen.getByRole('button',{name:'학습 단계'}));
  expect(screen.getByRole('region',{name:'학습 안내'})).toBeVisible();
  screen.getByRole('region',{name:'Lens 설명'}).focus();
  await waitFor(()=>expect(screen.getByRole('button',{name:'이번 입력 설명'})).toHaveAttribute('aria-pressed','true'));
});
