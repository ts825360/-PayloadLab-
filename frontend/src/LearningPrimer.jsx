import { PRACTICE_CONTEXT } from './practice-context.js';

export default function LearningPrimer({category,difficulty,onStart}) {
  const info=PRACTICE_CONTEXT[category.id];
  return <section className="learning-primer" aria-label="시작 전 학습">
    <div className="primer-story">
      <span className="eyebrow">{difficulty==='easy'?'FIRST STEPS · EASY':'YOUR MISSION · NORMAL'}</span>
      <h2>어떤 원리인가요?</h2><p>{info.definition}</p>
      <h3>성립 조건</h3><p>{info.conditions}</p>
    </div>
    <div className="primer-map">
      <ol className="concept-flow" aria-label="입력에서 결과까지">{info.flow.map(([title,detail],i)=><li key={title}><span>0{i+1}</span><div><strong>{title}</strong><small>{detail}</small></div></li>)}</ol>
      <div className="primer-goal"><h3>이번 학습 목표</h3><p>{difficulty==='medium'?info.normal:info.goal}</p></div>
      <div className="primer-next"><p>{difficulty==='medium'?'먼저 목표를 보고 시도해보세요. 막히면 Lens의 단서 보기를 선택할 수 있어요.':info.next}</p><button type="button" onClick={onStart}>입력하러 가기 <span aria-hidden="true">↗</span></button></div>
    </div>
  </section>;
}
