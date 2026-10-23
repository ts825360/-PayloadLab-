import { useEffect, useRef, useState } from "react";
import { LESSONS, statusLabel } from "./learning-content.js";
import Icon from "./Icon.jsx";
import { editWindow } from "./compare-inputs.js";

export function Composition({
  category,
  trace,
  value,
  claim,
  difficulty,
  activeGroup,
  onGroup,
  onLesson,
}) {
  const [showCode, setShowCode] = useState(false);
  const comp = trace?.composition || {
    prefix: category.prefix,
    value: value || "",
    suffix:
      category.suffix +
      (category.numeric && difficulty === "medium"
        ? `?claimed_user_id=${claim}`
        : ""),
  };
  const focus =
    activeGroup === "focus" ? trace?.lens.focus : comp.ranges?.[activeGroup];
  function marked(text, offset = 0) {
    if (!focus) return text || <span className="slot-label">입력 위치</span>;
    if (focus.end < offset || focus.start > offset + text.length) return text;
    const start = Math.max(0, Math.min(focus.start - offset, text.length)),
      end = Math.max(start, Math.min(focus.end - offset, text.length));
    if (start === end && focus.start !== focus.end) return text;
    return (
      <>
        {text.slice(0, start)}
        {start === end ? (
          <span className="insertion-marker" aria-label="이 위치 확인">
            ┆
          </span>
        ) : (
          <mark
            className={activeGroup === "focus" ? "lens-focus" : "linked-focus"}
          >
            {text.slice(start, end)}
          </mark>
        )}
        {text.slice(end)}
      </>
    );
  }
  function inputSegments() {
    if (!comp.ranges?.logic)
      return (
        <button
          className={`input-code ${activeGroup === "input" ? "group-active" : ""}`}
          onClick={() => onGroup(activeGroup === "input" ? "focus" : "input")}
          aria-label="입력 삽입 위치 강조"
        >
          {marked(comp.value)}
        </button>
      );
    const names = {
      name: "이름 부분 강조",
      logic: "조건 부분 강조",
      comment: "주석 부분 강조",
    };
    const ranges = Object.entries(comp.ranges)
      .filter(([key, range]) => key !== "input" && range.end > range.start)
      .sort((a, b) => a[1].start - b[1].start);
    const elements = [];
    let cursor = 0;
    for (const [key, range] of ranges) {
      if (range.start > cursor)
        elements.push(
          <span className="input-separator" key={`gap-${cursor}`}>
            {marked(comp.value.slice(cursor, range.start), cursor)}
          </span>,
        );
      elements.push(
        <button
          key={key}
          className={`input-code segment-${key} ${activeGroup === key ? "group-active" : ""}`}
          onClick={() => onGroup(key)}
          aria-label={names[key]}
        >
          {marked(comp.value.slice(range.start, range.end), range.start)}
        </button>,
      );
      cursor = range.end;
    }
    if (cursor < comp.value.length)
      elements.push(
        <span className="input-separator" key="tail">
          {marked(comp.value.slice(cursor), cursor)}
        </span>,
      );
    return elements;
  }
  return (
    <section id="composition-panel" className="panel composition-panel">
      <div className="panel-heading">
        <div>
          <span className="step-number">02</span>
          <h2>
            {trace
              ? trace.phase === "analysis"
                ? `분석 중인 ${category.composition}`
                : `실행한 ${category.composition}`
              : `${category.composition} 조립 미리보기`}
          </h2>
        </div>
        <span className={`evidence-tag ${trace ? "live" : ""}`}>
          {trace
            ? trace.phase === "analysis"
              ? "입력 분석 · 조회 전"
              : trace.simulated ? "교육용 모델의 모의 결과" : "서버가 반환한 실제 값"
            : "실행 전 · 입력에 따른 미리보기"}
        </span>
      </div>
      <div className="composition-toolbar">
        <span>
          <i className="legend-dot fixed" />
          고정 코드
        </span>
        <button
          className={activeGroup === "input" ? "selected" : ""}
          onClick={() => onGroup(activeGroup === "input" ? "" : "input")}
        >
          <i className="legend-dot input" />
          사용자 입력
        </button>
        {trace && (
          <button
            className={activeGroup === "focus" ? "selected lens" : ""}
            onClick={() => onGroup(activeGroup === "focus" ? "" : "focus")}
          >
            <i className="legend-dot lens" />
            Lens 확인 위치
          </button>
        )}
        <button
          className="text-button composition-help"
          onClick={() => onLesson(trace?.lens.lesson || category.lesson)}
        >
          <Icon name="book" size={14} />
          문법 알아보기
        </button>
      </div>
      <div className="composition-code">
        <span className="code-gutter">01</span>
        <code>
          <span className="fixed-code">{comp.prefix}</span>
          {inputSegments()}
          <span
            className={`fixed-code ${activeGroup === "password" ? "fixed-selected" : ""} ${comp.suffix_commented ? "commented-code" : ""}`}
          >
            {comp.suffix}
          </span>
        </code>
      </div>
      {comp.suffix_commented && (
        <div className="comment-note">
          <span className="comment-line" />
          회색으로 표시된 뒷부분은 줄 주석에 포함되어 실행에서 제외됐어요.
        </div>
      )}
      <div className="composition-note">
        <span className="input-bracket">↳</span>
        <span>
          {trace && trace.raw_input !== trace.effective_input
            ? "필터를 거쳐 바뀐 값이 문장에 들어갔어요."
            : "파란 부분이 내 입력이 들어간 자리예요."}
        </span>
        {trace?.code && (
          <button
            className="text-button"
            onClick={() => setShowCode(!showCode)}
            aria-expanded={showCode}
          >
            {showCode ? "코드 접기" : "원본 코드 보기"} ↗
          </button>
        )}
      </div>
      {trace && trace.raw_input !== trace.effective_input && (
        <div className="filter-comparison">
          <span>
            원본 <code>{trace.raw_input}</code>
          </span>
          <Icon name="arrow" />
          <span>
            필터 이후 <code>{trace.effective_input}</code>
          </span>
        </div>
      )}
      {showCode && <pre className="source-code">{trace.code}</pre>}
    </section>
  );
}

export function LensPanel({
  trace,
  guide,
  difficulty,
  analysisStatus,
  onFocus,
  onLesson,
  onRetry,
}) {
  const [expanded, setExpanded] = useState(false);
  useEffect(() => setExpanded(false), [trace]);
  const hint = trace?.lens;
  return (
    <section
      className={`panel lens-panel ${trace ? "has-result" : ""}`}
      role="region"
      aria-label="Lens 설명"
      aria-live="polite"
    >
      <div className="panel-heading">
        <div>
          <span className="lens-emblem">
            <Icon name="lens" size={19} />
          </span>
          <h2>Lens</h2>
          <span className="lens-caption">입력을 읽는 작은 단서</span>
        </div>
        <span className="lens-state">
          {trace
            ? trace.phase === "analysis"
              ? "입력 분석"
              : "결과 관찰"
            : analysisStatus === "pending"
              ? "분석 중"
              : "대기 중"}
        </span>
      </div>
      {!hint && !guide ? (
        <div className="lens-waiting">
          <div className="lens-orbit">
            <Icon name="lens" size={27} />
          </div>
          <h3>
            {analysisStatus === "pending"
              ? "입력의 의미를 살펴보고 있어요."
              : "첫 입력이, 배움의 시작."}
          </h3>
          <p>
            입력하면 문장이 어떻게 조립되고,
            <br />
            무엇을 확인하면 좋을지 설명해요.
          </p>
          <span>공격문을 몰라도 시작할 수 있어요.</span>
        </div>
      ) : (
        <div className="lens-body">
          {guide}
          {hint && <div className="lens-result-detail">
          <h3>{hint.title}</h3>
          <p>{hint.what}</p>
          <button className="locate-button" onClick={onFocus}>
            <span>⌖</span>문장에서 해당 위치 보기
            <Icon name="arrow" size={15} />
          </button>
          {difficulty === "easy" || expanded ? (
            <div className="lens-explanation">
              <span>왜 그럴까요?</span>
              <p>{hint.why}</p>
              <span>다음 관찰 지점</span>
              <p>{hint.next}</p>
            </div>
          ) : (
            <button className="text-button" onClick={() => setExpanded(true)}>
              이유와 다음 단서 펼치기 ＋
            </button>
          )}
          <div className="lens-actions">
            <button
              className="text-button"
              onClick={() => onLesson(hint.lesson)}
            >
              <Icon name="book" size={15} />
              필요한 개념 읽기
            </button>
            <button className="text-button" onClick={onRetry}>
              입력 고쳐보기 ↗
            </button>
          </div>
          </div>}
        </div>
      )}
    </section>
  );
}

export function ConceptPanel({ lesson, onClose }) {
  const info = LESSONS[lesson] || LESSONS.strings;
  const closeRef = useRef(null),
    restoreRef = useRef(null);
  useEffect(() => {
    restoreRef.current = document.activeElement;
    closeRef.current?.focus();
    function keys(e) {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const nodes = closeRef.current
          ?.closest('[role="dialog"]')
          ?.querySelectorAll("button");
        if (!nodes?.length) return;
        const first = nodes[0],
          last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", keys);
    return () => {
      document.removeEventListener("keydown", keys);
      restoreRef.current?.focus();
    };
  }, []);
  return (
    <div className="concept-backdrop" onClick={onClose}>
      <section
        className="concept-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="concept-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="concept-top">
          <span className="eyebrow">CONCEPT NOTE</span>
          <button
            ref={closeRef}
            className="icon-button"
            aria-label="개념 노트 닫기"
            onClick={onClose}
          >
            <Icon name="close" />
          </button>
        </div>
        <Icon name="book" size={32} />
        <h2 id="concept-title">{info.title}</h2>
        <p className="concept-lead">{info.lead}</p>
        <pre>{info.example}</pre>
        <p>{info.body}</p>
        <div className="concept-question">
          <span>생각해보기</span>
          <p>{info.question}</p>
        </div>
        <button className="primary-button" onClick={onClose}>
          실습으로 돌아가기
          <Icon name="arrow" />
        </button>
      </section>
    </div>
  );
}

export function HistoryPanel({
  history,
  selected,
  onSelect,
  compare,
  onCompare,
}) {
  const selectedIndex = history.indexOf(selected);
  const previous = history[selectedIndex > 0 ? selectedIndex - 1 : 1];
  const edit =
    previous && selected ? editWindow(previous.input, selected.input) : null;
  return (
    <section className="history-panel">
      <div className="panel-heading">
        <div>
          <Icon name="clock" />
          <h2>시도 기록</h2>
          <span className="count-pill">{history.length}</span>
        </div>
        {history.length >= 2 && (
          <button
            className="text-button"
            onClick={onCompare}
            aria-expanded={compare}
          >
            두 시도 비교
          </button>
        )}
      </div>
      {!history.length ? (
        <p className="empty-history">
          실행하면 이 브라우저에 시도가 쌓여요. 바꾼 부분과 결과를 함께
          돌아보세요.
        </p>
      ) : (
        <>
          <div className="history-list">
            {history.map((a, i) => (
              <button
                key={a.id}
                className={selected?.id === a.id ? "active" : ""}
                onClick={() => onSelect(a)}
              >
                <span className="attempt-number">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <code>{a.input || "(빈 입력)"}</code>
                <span className="history-status">
                  {statusLabel(a.result.learning_trace?.execution.status)}
                </span>
                <Icon name="arrow" size={14} />
              </button>
            ))}
          </div>
          {compare && edit && (
            <div className="attempt-comparison">
              <h3>어떤 수정이 결과를 바꿨을까요?</h3>
              <p>
                선택한 시도와 인접한 시도를 비교해요. 색이 표시된 부분이
                달라졌어요.
              </p>
              <div className="compare-grid">
                {[previous, selected].map((a, i) => {
                  const end = i === 0 ? edit.beforeEnd : edit.afterEnd;
                  return (
                    <div key={i}>
                      <span className="mini-label">
                        {i === 0 ? "이전 입력" : "선택한 입력"}
                      </span>
                      <pre>
                        {a.input.slice(0, edit.start)}
                        {end > edit.start && (
                          <mark className="edit-highlight">
                            {a.input.slice(edit.start, end)}
                          </mark>
                        )}
                        {a.input.slice(end) || (!a.input ? "(빈 입력)" : "")}
                      </pre>
                      {a.claim && <p>claimed_user_id: {a.claim}</p>}
                      <small>
                        {statusLabel(a.result.learning_trace?.execution.status)}
                      </small>
                      <code className="compare-query">
                        {a.result.learning_trace?.composition.full}
                      </code>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
