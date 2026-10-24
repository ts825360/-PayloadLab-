import React from 'react';
import {render,screen,within,fireEvent} from '@testing-library/react';
import {it,expect,vi} from 'vitest';
import TerminalTranscript from './TerminalTranscript.jsx';

function entry(id,overrides={}) {
  return {id,input:'cat /lab/report.txt',result:{learning_trace:{category:'permissions',
    phase:'result',raw_input:'cat /lab/report.txt',
    execution:{status:'permission_denied',stdout:'',stderr:'cat: /lab/report.txt: Permission denied\n',exit_code:1},
    lens:{title:`시도 ${id} 권한 설명`,what:'읽기가 거부됐어요.',why:`시도 ${id}의 사용자 권한을 확인해요.`},
    terminal:{prompt:'student@practice:/lab$ '},simulation:{nodes:[{id:'identity',value:'student'}]},
    ...overrides,
  }}};
}

it('keeps command/output order, exact raw errors and educational notes separate',()=>{
  const first=entry(1);
  const second=entry(2,{raw_input:'whoami',execution:{status:'command_ok',stdout:'student\n',stderr:'',exit_code:0}});
  render(<TerminalTranscript entries={[first,second]} selectedId={2}/>);
  const records=screen.getAllByRole('article');
  expect(records).toHaveLength(2);
  expect(records[0]).toHaveAttribute('data-attempt-id','1');
  expect(records[1]).toHaveAttribute('data-attempt-id','2');
  expect(within(records[0]).getByLabelText('터미널 원문 출력').querySelector('.terminal-stderr').textContent)
    .toBe('cat: /lab/report.txt: Permission denied\n');
  expect(within(records[1]).getByLabelText('터미널 원문 출력')).toHaveTextContent('whoami');
  expect(within(records[1]).getByLabelText('표준 출력').textContent).toBe('student\n');
  expect(within(records[0]).getByLabelText('터미널 원문 출력')).not.toHaveTextContent('읽기가 거부됐어요.');
});

it('uses the user before an elevation command rather than the returned root prompt',()=>{
  const elevated=entry(2,{raw_input:'sudo /lab/maintenance',
    execution:{status:'elevated',stdout:'가상 관리자 셸\n',stderr:'',exit_code:0},
    terminal:{current_user:'root',prompt:'root@practice:/lab# '}});
  render(<TerminalTranscript entries={[elevated]} selectedId={2}/>);
  expect(screen.getByLabelText('명령 원문').textContent).toBe('student@practice:/lab$ sudo /lab/maintenance');
});

it('keeps old diagnoses local and connects only the selected attempt to Lens',async()=>{
  const selected=vi.fn();
  render(<TerminalTranscript entries={[entry(1),entry(2)]} selectedId={2} onDiagnostic={selected}/>);
  const records=screen.getAllByRole('article');
  expect(within(records[0]).queryByRole('button',{name:'Permission denied'})).not.toBeInTheDocument();
  fireEvent.focus(within(records[0]).getByText('Permission denied'));
  expect(await screen.findByRole('tooltip')).toHaveTextContent('시도 1의 사용자 권한');
  fireEvent.click(within(records[1]).getByRole('button',{name:'Permission denied'}));
  expect(selected).toHaveBeenCalledWith(expect.objectContaining({why:'시도 2의 사용자 권한을 확인해요.'}));
});

it('does not turn analysis into a command result or offer stale Lens actions',()=>{
  render(<TerminalTranscript entries={[entry(1),entry(2,{phase:'analysis'})]} selectedId={1}/>);
  expect(screen.getAllByRole('article')).toHaveLength(1);
  expect(screen.queryByRole('button',{name:'Permission denied'})).not.toBeInTheDocument();
});

it('shows untrusted output as text and does not add fabricated terminal errors',()=>{
  const unsupported=entry(1,{raw_input:'unmodeled',execution:{status:'unsupported',stdout:'',stderr:'<img src=x onerror=alert(1)>\n이 모형의 지원 범위 밖입니다.',exit_code:1}});
  render(<TerminalTranscript entries={[unsupported]} selectedId={1} onDiagnostic={()=>{}}/>);
  expect(screen.queryByRole('img')).not.toBeInTheDocument();
  expect(screen.getByLabelText('표준 오류').textContent).toBe(unsupported.result.learning_trace.execution.stderr);
  expect(screen.queryByText(/command not found/)).not.toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'Permission denied'})).not.toBeInTheDocument();
});
