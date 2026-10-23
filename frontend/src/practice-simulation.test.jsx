import React from 'react';
import {render,screen} from '@testing-library/react';
import {it,expect} from 'vitest';
import PracticeSimulation from './PracticeSimulation.jsx';

it('keeps raw terminal errors and educational notes distinct without executing HTML',()=>{
  render(<PracticeSimulation category={{id:'permissions',terminal:true,label:'권한상승 기초'}} trace={{
    simulated:true,phase:'result',raw_input:'cat /lab/report.txt',
    execution:{status:'permission_denied',stdout:'',stderr:'cat: /lab/report.txt: Permission denied\n',exit_code:1,label:'교육용 모의 실행'},
    lens:{title:'사용자 권한을 확인하세요',what:'현재 사용자에게 읽기 권한이 없어요.'},
    terminal:{prompt:'student@practice:/lab$ ',current_user:'student',files:[{path:'/lab/report.txt',owner:'mentor',permissions:'-rw-------'}]},
    simulation:{nodes:[{id:'user',label:'가상 사용자',value:'student',state:'identity'}],edges:[]}
  }}/>);
  expect(screen.getByLabelText('터미널 원문 출력')).toHaveTextContent('Permission denied');
  expect(screen.getByText('종료 코드 1')).toBeInTheDocument();
  expect(screen.getByLabelText('모의 처리 흐름')).toHaveTextContent('가상 사용자');
  expect(screen.getByText('실제 서버의 파일·권한은 바뀌지 않아요.')).toBeInTheDocument();
});

it('never presents an analysis as a completed terminal command',()=>{
  render(<PracticeSimulation category={{id:'permissions',terminal:true,label:'권한상승 기초'}} trace={{phase:'analysis',execution:null,terminal:{prompt:'student@practice:/lab$ '}}}/>);
  expect(screen.queryByLabelText('터미널 원문 출력')).not.toBeInTheDocument();
  expect(screen.getByText(/실행 전/)).toBeInTheDocument();
});
