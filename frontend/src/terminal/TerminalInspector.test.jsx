import React from 'react';
import {render,screen} from '@testing-library/react';
import {it,expect} from 'vitest';
import TerminalInspector from './TerminalInspector.jsx';

it('connects actual identity, file metadata and denial without treating it as a typo',()=>{
  render(<TerminalInspector category={{id:'permissions'}} trace={{phase:'result',
    simulation:{nodes:[{id:'identity',value:'student'}]},
    terminal:{current_user:'student',files:[{path:'/lab/report.txt',owner:'mentor',permissions:'-rw-------'}]},
    execution:{status:'permission_denied'},lens:{next:'현재 사용자와 소유자를 비교하세요.'}}}/>);
  const diagram=screen.getByLabelText('터미널 처리 흐름');
  for(const text of ['student','mentor','-rw-------','/lab/report.txt','읽기 권한 없음'])expect(diagram).toHaveTextContent(text);
  expect(screen.getByText('현재 사용자와 소유자를 비교하세요.')).toBeInTheDocument();
});

it('keeps analysis as pending even if metadata contains a current user',()=>{
  render(<TerminalInspector category={{id:'permissions'}} trace={{phase:'analysis',terminal:{current_user:'student',files:[]},execution:null}}/>);
  expect(screen.getByLabelText('터미널 처리 흐름')).toHaveTextContent('아직 실행하지 않았어요');
  expect(screen.queryByText('읽기 권한 없음')).not.toBeInTheDocument();
});

it('shows CMDi composition as text and keeps the input distinct from the command',()=>{
  render(<TerminalInspector category={{id:'command_injection'}} trace={{phase:'result',
    raw_input:'example.com; whoami',composition:{full:'ping -c 1 example.com; whoami'},
    command_model:{hostname:'example.com',separator:';'},execution:{status:'injected'}}}/>);
  expect(screen.getByLabelText('터미널 처리 흐름')).toHaveTextContent('example.com');
  expect(screen.getByLabelText('서버가 조립한 명령')).toHaveTextContent('ping -c 1 example.com; whoami');
});
