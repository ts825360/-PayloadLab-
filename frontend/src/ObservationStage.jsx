import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import {createPortal} from 'react-dom';
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  autoUpdate,
  flip,
  offset,
  shift,
  size,
  useFloating,
} from "@floating-ui/react";
import { Composition } from "./WorkspaceParts.jsx";
import ExecutionCanvas from "./ExecutionCanvas.jsx";
import ChangeComparison from "./ChangeComparison.jsx";
import Icon from "./Icon.jsx";
import LensCloseConfirmation from "./LensCloseConfirmation.jsx";
import LearningPrimer from './LearningPrimer.jsx';
import {codepointRange} from './text-ranges.js';

function FocusScene({ trace, group }) {
  const reduce = useReducedMotion();
  const comp = trace.composition;
  const range = group === "focus" ? trace.lens.focus : comp.ranges?.[group];
  const focus = codepointRange(comp.value, range);
  const full = comp.full || comp.prefix + comp.value + comp.suffix;
  const start =
    group === "password"
      ? comp.prefix.length + comp.value.length
      : comp.prefix.length +
        Math.max(0, Math.min(focus.start, comp.value.length));
  const end =
    group === "password"
      ? full.length
      : comp.prefix.length +
        Math.max(focus.start, Math.min(focus.end, comp.value.length));
  const left = Array.from(full.slice(0, start)).slice(-24).join(''),
    right = Array.from(full.slice(end)).slice(0, 24).join('');
  const target = full.slice(start, end);
  const targetCharacters = Array.from(target);
  const { refs, floatingStyles } = useFloating({
    placement: "bottom-start",
    strategy: "absolute",
    middleware: [
      offset(16),
      flip({ padding: 12 }),
      shift({ padding: 12 }),
      size({
        padding: 12,
        apply({ availableWidth, elements }) {
          elements.floating.style.maxWidth = `${Math.min(330, Math.max(160, availableWidth))}px`;
        },
      }),
    ],
    whileElementsMounted: autoUpdate,
  });
  const labels = {
    name: "이름 비교에 들어간 값",
    logic: "조건을 연결하고 비교하는 부분",
    comment: "이 지점부터 줄 주석",
    password: "서버가 붙이는 비밀번호 조건",
  };
  return (
    <div className="focus-scene">
      <div className="focus-context">
        <span>전체 문장 속 위치</span>
        <code>
          {full.slice(0, start)}
          <span className="context-selection">
            {full.slice(start, end) || "┆"}
          </span>
          {full.slice(end)}
        </code>
      </div>
      <motion.div
        className="focus-magnifier"
        initial={{ opacity: 0, scale: reduce ? 1 : 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.18 }}
      >
        <div className="magnifier-heading">
          <span>
            <Icon name="lens" size={15} />
            관련 구간 확대
          </span>
          <span>전체 문장은 그대로 유지돼요</span>
        </div>
        <div className="magnified-code">
          <code>
            <span className="magnified-context">
              {start > 24 ? "…" : ""}
              {left}
            </span>
            <mark
              ref={refs.setReference}
              className={`magnified-target ${start === end ? "is-gap" : ""}`}
            >
              {start === end ? (
                <span aria-label="연결이 필요한 위치">┆</span>
              ) : targetCharacters.length > 160 ? (
                targetCharacters.slice(0, 160).join('') + "…"
              ) : (
                target || "입력 위치"
              )}
            </mark>
            <span className="magnified-context">
              {right}
              {end + 24 < full.length ? "…" : ""}
            </span>
          </code>
        </div>
        <div
          ref={refs.setFloating}
          style={floatingStyles}
          className="target-annotation"
          role="note"
        >
          <i />
          <strong>
            {group === "focus"
              ? start === end
                ? "두 조건 사이, 연결이 필요한 자리"
                : trace.lens.title
              : labels[group] || "입력과 연결된 부분"}
          </strong>
          <span>
            {group === "focus"
              ? "주황색 위치와 고정된 Lens 설명을 함께 보세요."
              : "같은 부분이 문장과 조건 그림에서 함께 강조됩니다."}
          </span>
        </div>
      </motion.div>
    </div>
  );
}

export default function ObservationStage({
  category,
  difficulty,
  input,
  claim,
  currentTrace,
  executedTrace,
  stale,
  labId,
  activeGroup,
  onGroup,
  onLesson,
  view,
  onView,
  history,
  selected,
  onSelect,
  onStart,
  onDiagnostic,
  popup = false,
  returnFocusRef,
  integrated = false,
}) {
  const regionRef = useRef(null),
    scrollRef = useRef(null),
    backRef = useRef(null),
    previousView = useRef(view),
    restoreRef = useRef(null);
  const [narrow, setNarrow] = useState(
    () => window.matchMedia?.("(max-width: 760px)").matches || false,
  );
  const [closeRequested, setCloseRequested] = useState(false);
  const cancelClose = useCallback(() => setCloseRequested(false), []);
  const confirmClose = useCallback(() => {
    setCloseRequested(false);
    onView("overview");
  }, [onView]);
  const requestClose = () => {
    if (view !== "overview") setCloseRequested(true);
  };
  useEffect(() => setCloseRequested(false), [view, labId]);
  useLayoutEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [view, activeGroup]);
  useEffect(() => {
    const query = window.matchMedia?.("(max-width: 760px)");
    if (!query) return;
    const update = () => setNarrow(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (view !== "overview" && previousView.current === "overview") {
      restoreRef.current = returnFocusRef?.current || document.activeElement;
    }
    if (view !== "overview") backRef.current?.focus({ preventScroll: true });
    if (view === "overview" && previousView.current !== "overview") {
      if(restoreRef.current?.isConnected && restoreRef.current!==document.body)restoreRef.current.focus({preventScroll:true});
      else onStart?.();
    }
    previousView.current = view;
  }, [view, selected?.id]);
  useEffect(() => {
    function escape(e) {
      if (
        document.querySelector(".concept-dialog, .lens-close-confirmation, .terminal-diagnostic-tooltip") ||
        e.isComposing ||
        e.keyCode === 229
      )
        return;
      if (e.key === "Escape" && view !== "overview") {
        e.preventDefault();
        e.stopPropagation();
        if (!e.repeat) setCloseRequested(true);
      }
      if (e.key === "Tab" && (popup || (narrow && !integrated)) && view !== "overview") {
        const controls = [
          ...regionRef.current.querySelectorAll(
            'button:not(:disabled),a[href],input,textarea,[tabindex="0"]',
          ),
        ].filter(element=>!element.closest('[hidden]'));
        const first = controls[0],
          last = controls.at(-1);
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [view, onView, narrow, integrated, popup]);
  const trace = currentTrace || (!stale ? executedTrace : null);
  const compositionProps = {
    category,
    trace,
    value: input,
    claim,
    difficulty,
    activeGroup,
    onGroup,
    onLesson,
  };
  const resultAvailable = Boolean(executedTrace);
  if(popup && view==='overview')return null;
  const content = (
    <section
      ref={regionRef}
      className={`observation-stage view-${view} ${popup?'web-observation-dialog':''}`}
      aria-label="실습 관찰 화면"
      role={popup || (narrow && !integrated && view !== "overview") ? "dialog" : "region"}
      aria-modal={popup || (narrow && !integrated && view !== "overview") ? true : undefined}
      data-view={view}
    >
      <header className="observation-header">
        <div>
          <span className="stage-dot" />
          <h2>처리 흐름과 결과</h2>
          <span className="stage-state">
            {trace?.phase === "analysis"
              ? "입력 분석"
              : trace
                ? "실행 결과"
                : "입력과 설명이 연결되는 곳"}
          </span>
        </div>
        <div className="stage-controls">
          {!popup && <button
            ref={backRef}
            className="stage-back"
            onClick={requestClose}
            disabled={view === "overview"}
            aria-label="관찰 전체로 돌아가기"
          >
            <Icon name="arrow" size={14} />
            돌아가기
          </button>}
          <button
            className={`stage-tab ${view === (popup?'result':'overview') ? "active" : ""}`}
            onClick={()=>popup?onView('result'):requestClose()}
            disabled={popup && !executedTrace}
          >
            {popup?'실행 결과':'전체'}
          </button>
          <button
            className={`stage-tab ${view === "compare" ? "active" : ""}`}
            disabled={history.length < 2}
            onClick={() => onView("compare")}
          >
            변화 비교
          </button>
          {popup && <button ref={backRef} className="stage-close" type="button" aria-label="처리 흐름과 결과 닫기" onClick={confirmClose}>×</button>}
        </div>
      </header>
      <div ref={scrollRef} className="observation-scroll">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={view}
            className="observation-content"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -3 }}
            transition={{ duration: 0.14 }}
          >
            {view === "compare" ? (
              <ChangeComparison history={history} selected={selected} />
            ) : (
              <>
                {!input && !category.plannedLevels?.includes(difficulty) && <LearningPrimer category={category} difficulty={difficulty} onStart={onStart} />}
                {view==='result' && trace?.composition && <div className="result-query-strip" aria-label="이번 입력이 결합된 문장"><code>{trace.composition.prefix}<mark>{trace.composition.value}</mark>{trace.composition.suffix}</code><button type="button" onClick={()=>onView('focus')}>문장 위치 확대 ↗</button></div>}
                {view === "focus" && (
                  <div className="focus-view">
                    <div className="focus-title">
                      <div>
                        <span className="eyebrow">LENS FOCUS</span>
                        <h2>선택한 부분 자세히 보기</h2>
                      </div>
                      <span>
                        {popup ? '닫으면 입력창과 Lens로 돌아가요.' : narrow && !integrated
                          ? "돌아가기를 누르면 입력을 수정할 수 있어요."
                          : "위 입력창과 아래 Lens가 같은 흐름으로 이어져요."}
                      </span>
                    </div>
                    {trace?.composition ? (
                      <FocusScene trace={trace} group={activeGroup} />
                    ) : (
                      <p className="focus-pending">
                        입력을 분석하면 선택한 위치가 여기에 나타납니다.
                      </p>
                    )}
                  </div>
                )}
                {Boolean(input || executedTrace) && (view === "overview" || !trace?.composition) && (
                  <Composition {...compositionProps} />
                )}
                {trace?.phase === "analysis" && (
                  <div className="analysis-preview-note">
                    <Icon name="lens" size={16} />
                    <span>
                      현재 입력의 문장·문법 분석입니다. 결과는 실행하기를 눌러
                      확인하세요.
                    </span>
                  </div>
                )}
                {stale && (
                  <div className="stale-notice">
                    <Icon name="clock" size={15} />
                    입력이 바뀌었어요. 아래는 이전 실행 결과입니다.
                  </div>
                )}
                {Boolean(input || executedTrace) && <ExecutionCanvas
                  key={selected?.id || labId}
                  trace={executedTrace}
                  category={category}
                  labId={labId}
                  activeGroup={activeGroup}
                  onGroup={onGroup}
                  onDiagnostic={stale ? undefined : onDiagnostic}
                  history={history}
                  selectedId={selected?.id}
                />}
                {!resultAvailable && Boolean(input) && (
                  <div className="observation-tip">
                    Lens에서 확인 위치를 누르면 이 공간이 해당 부분에 초점을
                    맞춥니다.
                  </div>
                )}
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
      <footer className="attempt-strip">
        <div className="attempt-strip-heading">
          <Icon name="clock" size={14} />
          <span>시도 기록</span>
          <b>{history.length}</b>
        </div>
        <div className="attempt-chips">
          {history.map((entry, i) => (
            <button
              key={entry.id}
              aria-label={`시도 ${i + 1} 불러오기`}
              aria-pressed={selected?.id === entry.id}
              onClick={() => onSelect(entry)}
              title={entry.input || "빈 입력"}
            >
              {String(i + 1).padStart(2, "0")}
            </button>
          ))}
        </div>
        {history.length >= 2 ? (
          <button className="text-button" onClick={() => onView("compare")}>
            두 시도 비교 <Icon name="arrow" size={13} />
          </button>
        ) : (
          <span className="strip-hint">실행한 시도를 돌아볼 수 있어요</span>
        )}
      </footer>
      {closeRequested && (
        <LensCloseConfirmation
          onConfirm={confirmClose}
          onCancel={cancelClose}
        />
      )}
    </section>
  );
  return popup?createPortal(<div className="unified-layout web-observation-backdrop">{content}</div>,document.body):content;
}
