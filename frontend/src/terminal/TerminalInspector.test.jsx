import React from 'react';
import {render,screen} from '@testing-library/react';
import {it,expect} from 'vitest';
import TerminalInspector from './TerminalInspector.jsx';

it('shows a Linux quiz mismatch without implying it listed virtual files',()=>{
  render(<TerminalInspector category={{id:'linux_basics'}} trace={{phase:'result',
    quiz:{tokens:['ls','/lab'],goal_description:'권한 포함 긴 목록',comparison_label:'목표 조건 다름'},
    execution:{status:'quiz_incorrect'},terminal:{files:[{path:'/lab/report.txt'}]}}}/>);
  const diagram=screen.getByLabelText('터미널 처리 흐름');
  for(const text of ['ls | /lab','권한 포함 긴 목록','목표 조건 다름'])expect(diagram).toHaveTextContent(text);
  expect(diagram).not.toHaveTextContent('report.txt');
});

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

it('does not label an unrecognized CMDi input as a valid host argument',()=>{
  render(<TerminalInspector category={{id:'command_injection'}} trace={{phase:'result',
    command_model:{hostname:"example.com'",separator:null},
    lens:{id:'unsupported'},execution:{status:'unsupported'}}}/>);
  const diagram=screen.getByLabelText('터미널 처리 흐름');
  expect(diagram).toHaveTextContent('구조 미판정');
  expect(diagram).toHaveTextContent('지원 범위 밖');
  expect(diagram).not.toHaveTextContent('호스트 인자');
});

it('keeps the first command boundary distinct from the later blocking filter token',()=>{
  render(<TerminalInspector category={{id:'command_injection'}} trace={{phase:'result',
    command_model:{hostname:'example.com',separator:'&&'},
    simulation:{nodes:[{id:'policy',value:'; 발견: 처리 차단'}]},
    lens:{id:'blocked'},execution:{status:'blocked'}}}/>);
  const diagram=screen.getByLabelText('터미널 처리 흐름');
  expect(diagram).toHaveTextContent('경계 &&');
  expect(diagram).toHaveTextContent('필터 ; 발견: 처리 차단');
  expect(diagram).toHaveTextContent('RESULT 처리 차단');
});

it('shows the user change on exit as well as on elevation',()=>{
  render(<TerminalInspector category={{id:'permissions'}} trace={{phase:'result',
    simulation:{nodes:[{id:'identity',value:'root'}]},
    terminal:{current_user:'student',files:[]},execution:{status:'command_ok'}}}/>);
  expect(screen.getByLabelText('터미널 처리 흐름')).toHaveTextContent('root → student');
});
