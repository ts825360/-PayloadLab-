import {it,expect,vi,afterEach} from 'vitest';
import {attemptLab,analyzeLab} from './api.js';

afterEach(()=>vi.unstubAllGlobals());
it.each([attemptLab,analyzeLab])('explains input-size rejection instead of generic failure',async(call)=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:413}));
 await expect(call('sql-injection-easy',{username:'a'})).rejects.toThrow('입력 전체 크기가 실습 요청 한도를 넘었습니다.');
});
it.each([attemptLab,analyzeLab])('explains rejected input type or length',async(call)=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:422}));
 await expect(call('sql-injection-easy',{username:'a'})).rejects.toThrow('입력 형식·길이·값이 실습 허용 범위를 벗어났습니다.');
});
it('explains response cap without exposing server details',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:503,json:async()=>({code:'response_limit',detail:'/private/path'})}));
 await expect(attemptLab('sql-injection-easy',{})).rejects.toThrow('조회 결과가 표시 가능한 크기를 넘었습니다.');
});
it('keeps unrelated server failure generic',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:500,json:async()=>({detail:'/private/path'})}));
 await expect(attemptLab('sql-injection-easy',{})).rejects.toThrow('시도 요청이 실패했습니다');
});
