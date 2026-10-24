import { useEffect, useRef, useState } from "react";
import { MotionConfig } from "motion/react";
import { fetchLabs, attemptLab } from "./api.js";
import { CATEGORIES, labId } from "./learning-content.js";
import Icon from "./Icon.jsx";
import InputDock from "./InputDock.jsx";
import ObservationStage from "./ObservationStage.jsx";
import useInputAnalysis from "./useInputAnalysis.js";
import { ConceptPanel } from "./WorkspaceParts.jsx";
import GuidedLesson from "./GuidedLesson.jsx";
import { getLesson } from "./lesson-catalog.js";
export { CATEGORIES } from "./learning-content.js";

export default function App() {
  const [categoryId, setCategoryId] = useState("sql_injection");
  const [difficulty, setDifficulty] = useState("easy");
  const [input, setInput] = useState(""),
    [claim, setClaim] = useState("");
  const [labs, setLabs] = useState([]),
    [connection, setConnection] = useState("loading");
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [attempts, setAttempts] = useState([]),
    [viewId, setViewId] = useState(null);
  const [view, setView] = useState("overview");
  const [stepIndex, setStepIndex] = useState(0);
  const [acknowledged, setAcknowledged] = useState(false);
  const [stepAfterAttempt, setStepAfterAttempt] = useState(0);
  const [lesson, setLesson] = useState(null),
    [activeGroup, setActiveGroup] = useState("input");
  const [theme, setTheme] = useState(
    () => localStorage.getItem("payloadlab-workspace-theme") || "light",
  );
  const generation = useRef(0),
    nextId = useRef(0),
    inputRef = useRef(null);
  const category = CATEGORIES.find((c) => c.id === categoryId),
    currentLab = labId(categoryId, difficulty);
  const history = attempts.filter((a) => a.lab === currentLab);
  const selected = history.find((a) => a.id === viewId);
  const trace = selected?.result.learning_trace;
  const stale = Boolean(
    selected && (selected.input !== input || selected.claim !== claim),
  );
  const available = labs.some((l) => l.id === currentLab);
  const planned = category.plannedLevels?.includes(difficulty);
  const guideLesson = getLesson(categoryId, difficulty);
  const validId = !category.numeric || /^\d+$/.test(input);
  const payload = {
    [category.field]: category.numeric ? Number(input) : input,
  };
  if (category.numeric && difficulty === "medium" && /^\d+$/.test(claim))
    payload.claimed_user_id = Number(claim);
  if (categoryId === "permissions") payload.history = history
    .filter((entry) => entry.result.learning_trace?.execution?.status !== 'unsupported')
    .map((entry) => entry.input);
  const { trace: analysis, status: analysisStatus } = useInputAnalysis(
    currentLab,
    payload,
    available && Boolean(input) && validId,
  );
  const currentTrace = stale || !trace ? analysis : trace;
  const guideTrace = !stale && selected?.id > stepAfterAttempt ? trace : null;
  function editInput(value) { setInput(value); setAcknowledged(false); }
  function editClaim(value) { setClaim(value); setAcknowledged(false); }

  async function connect() {
    setConnection("loading");
    try {
      setLabs(await fetchLabs());
      setConnection("ready");
    } catch {
      setConnection("error");
    }
  }
  useEffect(() => {
    connect();
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("payloadlab-workspace-theme", theme);
  }, [theme]);
  function changeContext(id, level = difficulty) {
    generation.current++;
    setCategoryId(id);
    setDifficulty(level);
    setInput("");
    setClaim("");
    setViewId(null);
    setView("overview");
    setBusy(false);
    setError("");
    setLesson(null);
    setActiveGroup("input");
    setStepIndex(0);
    setAcknowledged(false);
    setStepAfterAttempt(nextId.current);
  }
  function focusGroup(group = "focus") {
    setActiveGroup(group);
    setView("focus");
  }
  async function run(event) {
    event.preventDefault();
    if (busy || !available) return;
    if (category.numeric && (!input.trim() || !/^\d+$/.test(input))) {
      setError("주문번호는 정수로 입력해주세요.");
      return;
    }
    if (
      category.numeric &&
      difficulty === "medium" &&
      (!claim.trim() || !/^\d+$/.test(claim))
    ) {
      setError("소유자 주장 값은 정수로 입력해주세요.");
      return;
    }
    const version = ++generation.current;
    setBusy(true);
    setError("");
    const submitted = { input, claim, lab: currentLab };
    try {
      const result = await attemptLab(currentLab, payload);
      if (version !== generation.current) return;
      if (!result.learning_trace) {
        setError(
          "실행 해설 데이터가 없습니다. 최신 백엔드가 실행 중인지 확인해주세요.",
        );
        return;
      }
      const entry = { ...submitted, id: ++nextId.current, result };
      setAttempts((prev) => [...prev, entry].slice(-40));
      setViewId(entry.id);
      setAcknowledged(false);
      setActiveGroup("focus");
      setView("result");
    } catch {
      if (version === generation.current)
        setError(
          "실행 결과를 받지 못했어요. 서버 연결을 확인한 뒤 다시 시도해주세요.",
        );
    } finally {
      if (version === generation.current) setBusy(false);
    }
  }
  return (
    <MotionConfig
      reducedMotion="user"
      transition={{ duration: 0.2, ease: [0.22, 0.68, 0, 1] }}
    >
      <div className="workspace-shell focused-workbench unified-layout">
        <a href="#lab-main" className="skip-link">
          실습으로 바로가기
        </a>
        <aside className="workspace-sidebar">
          <a href="#lab-main" className="brand">
            <span className="brand-glyph">
              p<span>·</span>
            </span>
            <span>
              Payload<span className="brand-light">Lab</span>
            </span>
          </a>
          <div className="sidebar-intro">보안의 첫 단계를, 직접.</div>
          <div className="nav-label">LEARNING SPACE</div>
          <nav className="category-nav" aria-label="공격 유형">
            {CATEGORIES.map((c, i) => (
              <button
                key={c.id}
                onClick={() => changeContext(c.id)}
                aria-current={c.id === categoryId ? "page" : undefined}
                className={c.id === categoryId ? "selected" : ""}
              >
                <span className="nav-number">0{i + 1}</span>
                <span>
                  <strong>{c.label}</strong>
                  <small>{c.subtitle}</small>
                </span>
                <span className="nav-chevron">›</span>
              </button>
            ))}
          </nav>
          <div className="sidebar-notes">
            <span className="mini-label">TRY · UNDERSTAND · RETRY</span>
            <p>
              작은 수정을 따라,
              <br />
              이해가 이어지도록.
            </p>
          </div>
          <div className="sidebar-bottom">
            <Icon name="shield" />
            <span>
              교육용 로컬 실습
              <br />
              <small>외부 대상은 사용하지 않아요.</small>
            </span>
          </div>
        </aside>
        <div className="workspace-body">
          <header className="workspace-topbar">
            <div className="breadcrumb">
              학습 공간 <span>/</span>
              <strong>{category.label}</strong>
            </div>
            <select
              className="mobile-category-select"
              aria-label="학습 유형 선택"
              value={categoryId}
              onChange={(e) => changeContext(e.target.value)}
            >
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
            <div className="topbar-actions">
              <span className={`connection-indicator ${connection}`}>
                <i />
                {connection === "ready"
                  ? "실습 서버 연결됨"
                  : connection === "loading"
                    ? "연결 확인 중"
                    : "서버 연결 필요"}
              </span>
              <button
                className="icon-button"
                aria-label={
                  theme === "light" ? "다크 모드로 전환" : "라이트 모드로 전환"
                }
                onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              >
                <Icon name={theme === "light" ? "moon" : "sun"} />
              </button>
            </div>
          </header>
          <main id="lab-main" className="lab-main">
            <section className="lab-heading">
              <div>
                <div className="eyebrow">
                  <span className="eyebrow-line" />
                  WEB SECURITY LAB / 0{CATEGORIES.indexOf(category) + 1}
                </div>
                <h1>{category.title}</h1>
                <p>{category.description}</p>
              </div>
              <div className="difficulty-control">
                <span>학습 난이도</span>
                <div role="group" aria-label="난이도 선택">
                  {["easy", "medium"].map((d) => (
                    <button
                      key={d}
                      className={difficulty === d ? "active" : ""}
                      aria-pressed={difficulty === d}
                      onClick={() => changeContext(categoryId, d)}
                    >
                      {d === "easy" ? "Easy" : "Normal"}
                    </button>
                  ))}
                </div>
                <small>
                  {difficulty === "easy"
                    ? "원리를 따라 알아보기"
                    : "단서를 읽고 적용하기"}
                </small>
              </div>
            </section>
            {(connection === "error" ||
              (connection === "ready" && !available && !planned)) && (
              <div role="alert" className="connection-message">
                {connection === "error"
                  ? "서버 연결을 확인해주세요. 입력은 계속 작성할 수 있어요."
                  : "이 난이도의 실습이 서버 목록에 없습니다."}
                <button onClick={connect}>연결 다시 시도</button>
              </div>
            )}
            <section className="workbench-grid integrated-workspace" aria-label="통합 학습 작업 공간" data-phase={busy ? 'executing' : !input ? 'before-input' : currentTrace?.phase === 'analysis' || stale ? 'analyzing' : trace ? 'result' : 'editing'}>
              <InputDock
                category={category}
                difficulty={difficulty}
                input={input}
                claim={claim}
                onInput={editInput}
                onClaim={editClaim}
                onRun={run}
                busy={busy}
                available={available}
                planned={planned}
                guide={planned ? <section className="guided-lesson" aria-label="학습 안내"><h3>Normal은 다음 단계로 준비합니다</h3><p>권한상승 기초는 Easy에서 사용자·파일 소유자·접근 거부를 먼저 관찰해요. Normal은 구현 예정이며 현재 실행할 수 없어요.</p></section> : <GuidedLesson
                  lesson={guideLesson} stepIndex={stepIndex}
                  trace={guideTrace} result={guideTrace ? selected?.result : null}
                  acknowledged={acknowledged} onAcknowledge={setAcknowledged}
                  onFill={(value) => { editInput(value); inputRef.current?.focus(); }}
                  onAdvance={() => { setStepIndex((n) => n + 1); setAcknowledged(false); setStepAfterAttempt(nextId.current); }}
                />}
                error={error}
                inputRef={inputRef}
                trace={currentTrace}
                analysisStatus={analysisStatus}
                onFocus={() => focusGroup("focus")}
                onLesson={setLesson}
              />
              <ObservationStage
                integrated
                category={category}
                difficulty={difficulty}
                input={input}
                claim={claim}
                currentTrace={currentTrace}
                executedTrace={trace}
                stale={stale}
                labId={currentLab}
                activeGroup={activeGroup}
                onGroup={focusGroup}
                onLesson={setLesson}
                view={view}
                onView={setView}
                history={history}
                selected={selected}
                onSelect={(entry) => {
                  setViewId(entry.id);
                  setInput(entry.input);
                  setClaim(entry.claim);
                  setAcknowledged(false);
                  setView("overview");
                  setActiveGroup("focus");
                }}
                onStart={() => inputRef.current?.focus()}
              />
            </section>
          </main>
        </div>
        {lesson && (
          <ConceptPanel lesson={lesson} onClose={() => setLesson(null)} />
        )}
      </div>
    </MotionConfig>
  );
}
