import { useState } from "react";
import { API_BASE } from "./api.js";
import { statusLabel } from "./learning-content.js";
import Icon from "./Icon.jsx";
import PracticeSimulation from "./PracticeSimulation.jsx";

function Truth({ value }) {
  return (
    <span className={`truth ${value ? "yes" : "no"}`}>
      {value ? "참" : "거짓"}
    </span>
  );
}
function ConditionNode({ node, row, activeGroup, onGroup }) {
  if (!node.op)
    return (
      <div className="condition-leaf">
        <button
          className={`condition-text ${activeGroup === node.group ? "group-active" : ""}`}
          onClick={() => onGroup(node.group)}
        >
          <span className="mini-label">비교 조건</span>
          <code>{node.text}</code>
        </button>
        <Truth value={node.values[row]} />
      </div>
    );
  return (
    <div className="condition-branch">
      <div className={`condition-operator ${node.values[row] ? "yes" : "no"}`}>
        <strong>{node.op}</strong>
        <span>
          {node.op === "AND" ? "모두 참이어야 해요" : "하나만 참이면 돼요"}
        </span>
        <Truth value={node.values[row]} />
      </div>
      <div className="condition-children">
        {node.children.map((child) => (
          <div className="condition-child" key={child.id}>
            <ConditionNode
              node={child}
              row={row}
              activeGroup={activeGroup}
              onGroup={onGroup}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function DataTable({ table, row, onRow, isSql, error }) {
  return (
    <div className="table-scroll">
      <table className="evidence-table">
        <caption className="sr-only">교육용 데이터와 실제 반환 결과</caption>
        <thead>
          <tr>
            <th>결과</th>
            {table.columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((r, i) => (
            <tr
              key={i}
              className={`${r.matched ? "matched" : ""} ${isSql && row === i ? "inspected" : ""}`}
            >
              <td>
                <button
                  className="row-inspect"
                  disabled={!isSql}
                  onClick={() => onRow(i)}
                  aria-pressed={isSql ? row === i : undefined}
                  aria-label={`${r.cells[1]} 계정 조건 살펴보기`}
                >
                  <span className={`row-match ${r.matched ? "yes" : ""}`}>
                    {error ? "—" : r.matched ? "✓" : "−"}
                  </span>
                  <span>
                    {error ? "미평가" : r.matched ? "반환" : "미반환"}
                  </span>
                </button>
              </td>
              {r.cells.map((v, j) => (
                <td key={j}>
                  <code>{String(v)}</code>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Ownership({ trace }) {
  const r = trace.relations;
  return (
    <div className="ownership-map">
      <div className="relation-top">
        <div className="entity mine">
          <span>로그인 세션</span>
          <strong>사용자 {r.current_user}</strong>
          <small>서버가 알고 있는 나</small>
        </div>
        <div className="relation-link">
          <span>
            {r.owner === null
              ? "대상 없음"
              : r.owner === r.current_user
                ? "소유자 일치"
                : "소유자 불일치"}
          </span>
          <div className="dashed-link" />
        </div>
        <div
          className={`entity ${r.owner === r.current_user ? "mine" : "other"}`}
        >
          <span>주문 {r.requested_id}</span>
          <strong>
            {r.owner === null ? "없는 주문" : `소유자 ${r.owner}`}
          </strong>
          <small>주문에 기록된 실제 주인</small>
        </div>
      </div>
      <div className="ownership-check">
        <span className="connector-stem" />
        <Icon name="shield" />
        <div>
          <strong>
            {r.medium
              ? "요청에 적힌 사용자 번호를 신뢰"
              : "서버의 소유자 확인이 빠져 있어요"}
          </strong>
          <p>
            {r.medium
              ? `전달한 claimed_user_id: ${r.claimed_user ?? "없음"} · 실제 소유자: ${r.owner ?? "없음"}`
              : "주문을 찾은 뒤 로그인 사용자와 대조하는 단계가 없습니다."}
          </p>
        </div>
      </div>
      <div className={`ownership-result ${r.allowed ? "yes" : "no"}`}>
        {r.allowed
          ? "조회 응답에 주문 정보가 포함됩니다."
          : "이 요청에서는 주문 정보가 반환되지 않습니다."}
      </div>
    </div>
  );
}

function HtmlFlow({ trace, labId }) {
  const [live, setLive] = useState(false);
  return (
    <div className="html-flow">
      <div className="html-stages">
        <div>
          <span className="mini-label">SERVER</span>
          <strong>검색어 → HTML 삽입</strong>
          <code>{trace.effective_input || "(빈 입력)"}</code>
        </div>
        <div className="browser-boundary">
          <Icon name="arrow" />
          <span>HTTP 응답</span>
        </div>
        <div>
          <span className="mini-label">BROWSER</span>
          <strong>HTML 구조로 해석</strong>
          <p>태그·본문·스크립트 내용에 따라 동작이 달라져요.</p>
        </div>
      </div>
      <div className="browser-preview-heading">
        <p>
          태그 인식은 실행 성공의 증거가 아닙니다.
          <br />
          실제 화면은 버튼을 눌러 별도로 관찰해보세요.
        </p>
        <button className="secondary-button" onClick={() => setLive(!live)}>
          {live ? "브라우저 결과 닫기" : "브라우저 결과 열기"}
          <Icon name="arrow" size={15} />
        </button>
      </div>
      {live && (
        <iframe
          key={trace.raw_input}
          title="격리된 HTML 실행 결과"
          className="browser-frame"
          sandbox="allow-scripts allow-modals"
          src={`${API_BASE}/labs/${labId}/render?query=${encodeURIComponent(trace.raw_input)}`}
        />
      )}
    </div>
  );
}

export default function ExecutionCanvas({
  trace,
  category,
  labId,
  activeGroup,
  onGroup,
  onDiagnostic,
  history,
  selectedId,
}) {
  const [row, setRow] = useState(0);
  if (category.simulated) return <PracticeSimulation trace={trace} category={category} onDiagnostic={onDiagnostic} history={history} selectedId={selectedId} />;
  if (!trace)
    return (
      <section className="execution-placeholder">
        <div className="placeholder-title">
          <span className="step-number">03</span>
          <h2>입력이 만든 변화를 따라가 보세요</h2>
        </div>
        <div className="placeholder-flow">
          <div>
            <span className="diagram-symbol">↳</span>
            <strong>내 입력</strong>
            <small>어디에 들어갔을까?</small>
          </div>
          <span className="placeholder-connector" />
          <div>
            <span className="diagram-symbol">
              {category.short === "SQL" ? "ƒ" : "⌘"}
            </span>
            <strong>
              {category.short === "SQL"
                ? "조건의 해석"
                : category.short === "HTML"
                  ? "브라우저 해석"
                  : "소유 관계"}
            </strong>
            <small>어떤 의미가 됐을까?</small>
          </div>
          <span className="placeholder-connector" />
          <div>
            <span className="diagram-symbol">≡</span>
            <strong>실제 결과</strong>
            <small>무엇이 달라졌을까?</small>
          </div>
        </div>
        <p>입력을 실행하면 실제 값으로 채워집니다.</p>
      </section>
    );
  const sql = category.id === "sql_injection",
    error = trace.execution.status === "syntax_error";
  if (sql && ["resource_limit", "blocked"].includes(trace.execution.status)) {
    return (
      <section className="panel execution-panel" aria-label="SQL 처리 중단 안내">
        <div className="panel-heading">
          <h2>{trace.lens.title}</h2>
          <span className="result-badge warning">{statusLabel(trace.execution.status)}</span>
        </div>
        <div className="syntax-stop">
          <p>{trace.lens.what}</p>
          <p>{trace.lens.why}</p>
          <strong>다음 관찰</strong>
          <p>{trace.lens.next}</p>
        </div>
      </section>
    );
  }
  return (
    <section className="panel execution-panel">
      <div className="panel-heading">
        <div>
          <span className="step-number">03</span>
          <h2>
            {sql
              ? "조건에서 결과까지"
              : category.id === "idor"
                ? "요청과 소유 관계"
                : "서버에서 브라우저까지"}
          </h2>
        </div>
        <span
          className={`result-badge ${["matched", "exposed", "own"].includes(trace.execution.status) ? "positive" : error ? "warning" : ""}`}
        >
          {statusLabel(trace.execution.status)}
        </span>
      </div>
      <div className="execution-caption">
        <span>{trace.execution.label}</span>
        <p>
          {sql
            ? "문장과 데이터 사이의 관계를 살펴보세요."
            : category.id === "idor"
              ? "요청하는 대상과 권한을 가진 사용자를 구분해보세요."
              : "입력이 HTML로 전달되는 경로를 관찰해보세요."}
        </p>
      </div>
      {sql ? (
        <div className="sql-execution-grid">
          <div className="condition-zone">
            {trace.table?.rows && <label className="account-inspector">관찰할 계정 <select aria-label="조건을 관찰할 계정" value={row} onChange={(event)=>setRow(Number(event.target.value))}>{trace.table.rows.map((item,index)=><option key={index} value={index}>{item.cells[1]}</option>)}</select></label>}
            <div className="zone-title">
              <span className="mini-label">CONDITION MAP</span>
              <span>
                {!error && trace.condition_tree
                  ? `${trace.table.rows[row]?.cells[1]} 계정 기준`
                  : error
                    ? "문법 해석에서 중단"
                    : "해석 범위 확인"}
              </span>
            </div>
            {error ? (
              <div className="syntax-stop">
                <span className="stop-mark">!</span>
                <h3>조회 전에 문법 오류가 발생했어요</h3>
                <p>
                  데이터가 없는 것이 아니라,
                  <br />
                  문장을 실행하지 못한 상태예요.
                </p>
                <code>{trace.execution.error}</code>
              </div>
            ) : trace.condition_tree ? (
              <>
                <ConditionNode
                  node={trace.condition_tree}
                  row={row}
                  activeGroup={activeGroup}
                  onGroup={onGroup}
                />
                <div className="condition-verdict">
                  <Icon
                    name={trace.condition_tree.values[row] ? "check" : "close"}
                    size={17}
                  />
                  <span>
                    이 계정의 전체 조건은{" "}
                    <strong>
                      {trace.condition_tree.values[row] ? "참" : "거짓"}
                    </strong>
                    이에요.
                  </span>
                </div>
                {trace.row_explanations?.[row] && <p className="row-story">{trace.row_explanations[row].explanation}</p>}
                <p className="diagram-footnote">
                  조건 관계를 풀어 쓴 교육용 해설입니다. DB 내부 실행 순서를
                  뜻하지 않아요.
                </p>
              </>
            ) : (
              <div className="unmapped">
                <Icon name="lens" size={26} />
                <h3>이 문장의 상세 해설은 아직 없어요</h3>
                <p>
                  실제 조회 결과는 오른쪽 표에서 확인할 수 있습니다. 알 수 없는
                  조건을 임의로 해석하지 않아요.
                </p>
              </div>
            )}
          </div>
          <div className="data-zone">
            <div className="zone-title">
              <span className="mini-label">USERS TABLE</span>
              <span>교육용 계정 · {trace.execution.count}개 행 반환</span>
            </div>
            <DataTable
              table={trace.table}
              row={row}
              onRow={setRow}
              isSql
              error={error}
            />
            <div className="table-legend">
              <span>
                <i className="legend-dot returned" />
                실제 반환된 행
              </span>
              <span>
                <i className="legend-dot inspected" />
                현재 살펴보는 계정
              </span>
            </div>
            <p className="data-help">
              계정 행을 누르면 해당 계정의 조건 판정으로 바뀝니다.
            </p>
            <div className="query-outcome">
              <span className="mini-label">QUERY RESULT</span>
              <strong>
                {error
                  ? "실행 중단"
                  : trace.execution.count
                    ? `${trace.execution.count}개 계정이 조회됐어요`
                    : "조건을 만족하는 계정이 없어요"}
              </strong>
              <p>
                {error
                  ? "위 문장의 오류와 Lens 단서를 확인해보세요."
                  : trace.execution.count
                    ? "비밀번호를 몰라도 행이 반환된 이유를 조건 그림에서 확인해보세요."
                    : "입력을 바꿨을 때 어떤 조건이 달라질지 예상해보세요."}
              </p>
            </div>
          </div>
        </div>
      ) : category.id === "idor" ? (
        <>
          <Ownership trace={trace} />
          <DataTable
            table={trace.table}
            row={0}
            onRow={() => {}}
            isSql={false}
          />
        </>
      ) : (
        <HtmlFlow trace={trace} labId={labId} />
      )}
    </section>
  );
}
