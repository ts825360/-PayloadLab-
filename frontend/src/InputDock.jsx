import { useLayoutEffect, useRef } from "react";
import Icon from "./Icon.jsx";
import { LensPanel } from "./WorkspaceParts.jsx";
import PracticeEnvironment from './PracticeEnvironment.jsx';
import TerminalInput from './terminal/TerminalInput.jsx';
import {terminalDiagnostics} from './terminal/diagnostics.js';

export default function InputDock({
  category,
  difficulty,
  input,
  claim,
  onInput,
  onClaim,
  onRun,
  busy,
  available,
  planned,
  guide,
  error,
  inputRef,
  lensRef,
  trace,
  analysisStatus,
  onFocus,
  onLesson,
}) {
  const areaRef = useRef(null),
    composing = useRef(false);
  function handleEnter(event) {
    if (
      event.key !== "Enter" ||
      event.shiftKey ||
      event.ctrlKey ||
      event.altKey ||
      event.metaKey
    )
      return;
    if (
      composing.current ||
      event.nativeEvent.isComposing ||
      event.nativeEvent.keyCode === 229
    )
      return;
    event.preventDefault();
    if (!event.repeat && !busy && available)
      event.currentTarget.form.requestSubmit();
  }
  useLayoutEffect(() => {
    const area = areaRef.current;
    if (area) {
      area.style.height = "auto";
      area.style.height = `${Math.min(104, Math.max(52, area.scrollHeight))}px`;
    }
  }, [input]);
  return (
    <div className="input-dock">
      <section className="panel input-panel">
        <div className="panel-heading input-panel-heading">
          <div>
            <span className="step-number">01</span>
            <h2>직접 입력해보세요</h2>
          </div>
          <span className="quiet-badge">
            {category.short} · {difficulty === "easy" ? "Easy" : "Normal"}
          </span>
        </div>
        <p className="scenario environment-description">{category.context}</p>
        {planned ? <div className="planned-panel" role="status"><strong>Normal은 구현 예정</strong><p>현재 제공되는 Easy를 먼저 연습할 수 있어요. 서버 연결 오류가 아닙니다.</p></div> : <form onSubmit={onRun}>
          <PracticeEnvironment category={category} trace={trace} onInput={onInput}>
          <div className="primary-input-control">
          {category.terminal ? <TerminalInput
            value={input} label={category.fieldLabel} placeholder={category.placeholder}
            prompt={trace?.terminal?.prompt} inputRef={inputRef} onChange={onInput}
            onKeyDown={handleEnter}
            onCompositionStart={()=>{composing.current=true;}}
            onCompositionEnd={()=>{composing.current=false;}}
            diagnostics={trace?.raw_input===input ? terminalDiagnostics(trace) : []}
            onDiagnostic={()=>lensRef?.current?.focus({preventScroll:true})}
          /> : <>
          <label htmlFor="payload-input">
            {category.fieldLabel}
            <span>{category.field}</span>
          </label>
          <div className="payload-editor">
            <span className="editor-prompt" aria-hidden="true">
              ›
            </span>
            <textarea
              ref={(el) => {
                areaRef.current = el;
                inputRef.current = el;
              }}
              id="payload-input"
              aria-label={category.fieldLabel}
              value={input}
              onChange={(e) => onInput(e.target.value)}
              onKeyDown={handleEnter}
              onCompositionStart={() => {
                composing.current = true;
              }}
              onCompositionEnd={() => {
                composing.current = false;
              }}
              aria-describedby="payload-shortcuts"
              placeholder={category.placeholder}
              spellCheck={false}
              autoComplete="off"
              rows={1}
              maxLength={2000}
            />
          </div>
          </>}
          </div>
          </PracticeEnvironment>
          {!category.terminal && trace?.lens && input && <div className="inline-diagnostic" aria-label="입력 위치 설명">
            <code>{(() => {
              const text = trace.effective_input ?? input;
              const start = Math.max(0, Math.min(text.length, trace.lens.focus?.start ?? 0));
              const end = Math.max(start, Math.min(text.length, trace.lens.focus?.end ?? text.length));
              return <>{text.slice(0, start)}<mark>{text.slice(start, end) || '┆'}</mark>{text.slice(end)}</>;
            })()}</code><span>↳ {trace.lens.title}</span>
            {trace.raw_input !== trace.effective_input && <small>필터가 적용된 값을 표시합니다. 원본 입력은 위에서 수정할 수 있어요.</small>}
          </div>}
          {category.numeric && difficulty === "medium" && (
            <div className="claim-field">
              <label htmlFor="claim-input">
                소유자 주장 값 <span>claimed_user_id</span>
              </label>
              <input
                id="claim-input"
                aria-label="소유자 주장 값"
                value={claim}
                onChange={(e) => onClaim(e.target.value)}
                inputMode="numeric"
                placeholder="서버에 전달할 사용자 번호"
              />
            </div>
          )}
          <div className="input-footer">
            <span>
              {analysisStatus === "pending"
                ? "Lens가 입력을 살펴보고 있어요."
                : "입력 분석은 자동으로, 실행은 직접."}
              <br />
              <span id="payload-shortcuts">
                Enter 실행 · Shift+Enter 줄바꿈
              </span>
            </span>
            <button
              className="primary-button"
              type="submit"
              disabled={busy || !available}
            >
              <Icon name="play" size={15} />
              {busy ? "실행 중…" : "실행하기"}
            </button>
          </div>
          {error && (
            <p role="alert" className="inline-error">
              {error}
            </p>
          )}
        </form>}
      </section>
      <LensPanel
        panelRef={lensRef}
        trace={trace}
        guide={guide}
        difficulty={difficulty}
        analysisStatus={analysisStatus}
        onFocus={onFocus}
        onLesson={onLesson}
        onRetry={() => inputRef.current?.focus()}
      />
    </div>
  );
}
