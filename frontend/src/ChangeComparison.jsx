import { editWindow } from "./compare-inputs.js";
import { statusLabel } from "./learning-content.js";
import Icon from "./Icon.jsx";

function ChangedText({ before, after, side }) {
  const edit = editWindow(before, after),
    value = side === 0 ? before : after,
    end = side === 0 ? edit.beforeEnd : edit.afterEnd;
  return (
    <>
      {value.slice(0, edit.start)}
      {end > edit.start && (
        <mark className="edit-highlight">{value.slice(edit.start, end)}</mark>
      )}
      {value.slice(end) || (!value ? "(빈 입력)" : "")}
    </>
  );
}

export default function ChangeComparison({ history, selected }) {
  const index = history.indexOf(selected),
    previous = history[Math.max(0, index - 1)],
    current = history[Math.max(1, index)];
  if (!selected || index < 0 || !previous || !current)
    return (
      <div className="comparison-empty">
        <Icon name="clock" size={27} />
        <h3>두 번째 시도부터 변화를 비교할 수 있어요</h3>
        <p>입력을 고쳐 실행하면 이 공간에 변경 전후가 함께 나타납니다.</p>
      </div>
    );
  const before = previous.result.learning_trace,
    after = current.result.learning_trace;
  return (
    <section className="change-comparison" aria-label="시도 변화 비교">
      <div className="comparison-intro">
        <span className="eyebrow">CHANGE → EFFECT</span>
        <h2>어떤 수정이 결과를 바꿨을까요?</h2>
        <p>바뀐 글자부터 조립된 문장, 결과까지 연결해보세요.</p>
      </div>
      <div className="comparison-labels">
        <span>
          이전 입력 <b>#{history.indexOf(previous) + 1}</b>
        </span>
        <span>
          비교 입력 <b>#{history.indexOf(current) + 1}</b>
        </span>
      </div>
      <div className="comparison-step-label">
        <span>01</span>입력에서 달라진 부분
      </div>
      <div className="change-pair">
        {[previous, current].map((entry, i) => (
          <pre key={entry.id}>
            <ChangedText
              before={previous.input}
              after={current.input}
              side={i}
            />
            {(previous.claim || current.claim) && (
              <small>소유자 주장 값: {entry.claim || "없음"}</small>
            )}
          </pre>
        ))}
      </div>
      <div className="comparison-step-label">
        <span>02</span>그 수정이 반영된 문장
      </div>
      <div className="change-pair query-pair">
        {[before, after].map((trace, i) => (
          <pre key={i}>
            <ChangedText
              before={before.composition.full}
              after={after.composition.full}
              side={i}
            />
          </pre>
        ))}
      </div>
      <div className="comparison-step-label">
        <span>03</span>실제 결과의 변화
      </div>
      <div className="change-pair result-pair">
        {[before, after].map((trace, i) => (
          <div key={i}>
            <strong>{statusLabel(trace.execution.status)}</strong>
            <span>{trace.execution.label}</span>
            {trace.simulated ? <pre className="comparison-output">{trace.execution.stdout || trace.execution.stderr || '(출력 없음)'}</pre> : trace.category !== "reflected_xss" && (
              <small>{trace.execution.count}개 행 반환</small>
            )}
          </div>
        ))}
      </div>
      <div className="change-summary">
        <Icon name="lens" />
        <p>{after.lens.next}</p>
      </div>
    </section>
  );
}
