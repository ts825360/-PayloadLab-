import React, { useEffect, useState } from "react";

export default function GuidedLesson({ lesson, stepIndex, onAdvance, onFill, trace, result, acknowledged, onAcknowledge }) {
  const step = lesson?.steps?.[stepIndex];
  const [hintOpen, setHintOpen] = useState(false);
  const [answer, setAnswer] = useState("");
  useEffect(() => {
    setHintOpen(false);
    setAnswer("");
  }, [lesson?.steps, step?.id]);
  if (!lesson) return null;
  const complete = stepIndex >= lesson.steps.length;
  const observed = Boolean(step?.accept(trace, result));
  const correct = !step?.question || answer === step.answer;
  const canAdvance = observed && acknowledged && correct;
  const showSuggestion = lesson.difficulty !== "medium" || hintOpen;
  return <section className="guided-lesson" aria-label="학습 안내">
    <h2>{lesson.title}</h2>
    {complete ? <>
      <h3>이 안내를 마쳤어요</h3>
      <p>관찰과 이해 확인을 마쳤습니다. 입력을 바꾸어 결과를 더 비교해볼 수 있어요.</p>
    </> : <>
      <p>{lesson.summary}</p>
      <p className="guided-progress" aria-label="학습 진행">{stepIndex + 1} / {lesson.steps.length}</p>
      <h3>{step.title}</h3>
      <p>{step.instruction}</p>
      {lesson.difficulty === "medium" && <button type="button" aria-expanded={hintOpen} onClick={() => setHintOpen(!hintOpen)}>{hintOpen ? "단서 접기" : "단서 보기"}</button>}
      {showSuggestion && step.suggestion && <div className="guided-suggestion">
        <code>{step.suggestion}</code>
        <button type="button" onClick={() => onFill(step.suggestion)}>입력 예시 넣기</button>
        <small>입력창만 채워요. 내용을 확인·수정하고 직접 실행하세요.</small>
      </div>}
      {showSuggestion && <p className="guided-observation">{step.observation}</p>}
      <p role="status">{observed ? "이번 실행에서 단계의 관찰 근거를 확인할 수 있어요." : "아직 이 단계의 실행 근거가 없어요. 직접 실행하고 코드와 결과를 비교해보세요. 자유롭게 다른 입력을 시도해도 좋아요."}</p>
      <label className="guided-acknowledgement"><input type="checkbox" checked={Boolean(acknowledged)} onChange={(event) => onAcknowledge(event.target.checked)} />코드와 실행 결과에서 위 내용을 직접 관찰했어요</label>
      {step.question && <fieldset className="guided-question">
        <legend>{step.question}</legend>
        {step.choices.map((item) => <label key={item.value}><input type="radio" name={`lesson-${step.id}`} value={item.value} checked={answer === item.value} onChange={() => setAnswer(item.value)} />{item.label}</label>)}
        {answer && !correct && <p role="status">관찰한 조건과 설명을 다시 비교해보세요. 다른 답을 선택할 수 있어요.</p>}
      </fieldset>}
      <button type="button" disabled={!canAdvance} onClick={onAdvance}>{stepIndex === lesson.steps.length - 1 ? "학습 마치기" : "다음 단계"}</button>
    </>}
  </section>;
}
