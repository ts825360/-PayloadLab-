import {PRACTICE_CONTEXT} from './practice-context.js';

export default function PracticeEnvironment({category,onInput,trace,children}) {
  const info=PRACTICE_CONTEXT[category.id];
  if (!info) return children;
  return <div className={`practice-environment environment-${category.id}`} role="region" aria-label={info.environment}>
    <div className="environment-identity"><span className="environment-icon">{info.icon}</span><div><strong>{info.environment}</strong><small>{category.simulated?'모의 실습 · 외부 연결 없음':category.id==='reflected_xss'?'HTML 응답 · 선택형 격리 미리보기':'로컬 교육용 데이터'}</small></div>
      {category.id==='idor' && <span className="session-pill">로그인 사용자 1042</span>}
    </div>
    <div className="environment-controls">{children}
      {category.id==='sql_injection' && <label className="fixed-password">비밀번호<input aria-label="실습용 고정 비밀번호" type="password" value="this_is_definitely_wrong" disabled readOnly/><small>서버에서 틀린 값으로 고정 · 이름 조건에 집중해요</small></label>}
    </div>
    {category.id==='idor' && <div className="order-shortcuts"><span>주문 선택</span><button type="button" onClick={()=>onInput('1042')}>본인 주문 1042 선택</button><button type="button" onClick={()=>onInput('1043')}>타인 주문 1043 선택</button><small>선택만 해요. 실행은 직접 합니다.</small></div>}
    {category.id==='ssrf' && <div className="environment-context"><span>요청 주체: 가상 미리보기 서버</span><span>URL 입력 → hostname 확인 → 더미 응답</span></div>}
    {category.id==='command_injection' && <div className="environment-context"><span>서버 연결 진단</span><code>ping -c 1 [호스트]</code><span>실제 ping·셸 실행 없음</span></div>}
    {category.id==='linux_basics' && <div className="environment-context"><span>가상 /lab</span><code>report.txt</code><code>readme.txt</code><span>명령 이름 · 옵션 · 경로</span></div>}
    {category.id==='permissions' && <div className="environment-context"><span>가상 파일 /lab/report.txt</span><code>mentor · -rw-------</code><span>현재 사용자와 파일 소유자를 비교해요</span></div>}
  </div>;
}
