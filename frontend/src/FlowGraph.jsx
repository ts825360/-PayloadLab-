import { useLayoutEffect, useRef, useState } from "react";

function highlightValue(value, needle) {
  if (!needle) return value;
  const idx = value.indexOf(needle);
  if (idx === -1) return value;
  return (
    <>
      {value.slice(0, idx)}
      <mark className="payload-highlight">{needle}</mark>
      {value.slice(idx + needle.length)}
    </>
  );
}

const KIND_LABEL = {
  input: "입력",
  variable: "변수",
  action: "코드 동작",
  query: "생성된 값",
  table: "테이블",
  result: "결과",
};

function MiniTable({ table }) {
  return (
    <table className="flow-mini-table">
      <thead>
        <tr>
          {table.columns.map((c) => (
            <th key={c}>{c}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {table.rows.map((row, i) => (
          <tr key={i} className={table.matched_row_indices.includes(i) ? "matched" : ""}>
            {row.map((cell, j) => (
              <td key={j}>{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function FlowGraph({ nodes, edges, activeLine, activeNodeId, onHoverNode, onClickNode }) {
  const containerRef = useRef(null);
  const nodeRefs = useRef({});
  const [paths, setPaths] = useState([]);

  const activeNodeIds = new Set(
    nodes.filter((n) => n.id === activeNodeId || (activeLine != null && n.code_line === activeLine)).map((n) => n.id)
  );

  useLayoutEffect(() => {
    function recompute() {
      const container = containerRef.current;
      if (!container) return;
      const containerRect = container.getBoundingClientRect();
      const rects = {};
      nodes.forEach((n) => {
        const el = nodeRefs.current[n.id];
        if (!el) return;
        const r = el.getBoundingClientRect();
        rects[n.id] = {
          top: r.top - containerRect.top,
          bottom: r.bottom - containerRect.top,
          right: r.right - containerRect.left,
          centerX: r.left - containerRect.left + r.width / 2,
          centerY: r.top - containerRect.top + r.height / 2,
        };
      });

      const order = nodes.map((n) => n.id);
      const incomingCount = {};
      edges.forEach((e) => {
        incomingCount[e.target] = (incomingCount[e.target] || 0) + 1;
      });

      let lane = 0;
      const newPaths = edges
        .map((e) => {
          const s = rects[e.source];
          const t = rects[e.target];
          if (!s || !t) return null;
          const sIdx = order.indexOf(e.source);
          const tIdx = order.indexOf(e.target);
          const isSimple = tIdx === sIdx + 1 && incomingCount[e.target] === 1;
          const active = activeNodeIds.has(e.source) && activeNodeIds.has(e.target);
          if (isSimple) {
            const x = (s.centerX + t.centerX) / 2;
            return {
              key: `${e.source}->${e.target}`,
              d: `M ${s.centerX} ${s.bottom} L ${x} ${(s.bottom + t.top) / 2} L ${t.centerX} ${t.top}`,
              active,
            };
          }
          lane += 1;
          const laneX = Math.max(s.right, t.right) + 20 + lane * 18;
          return {
            key: `${e.source}->${e.target}`,
            d: `M ${s.right} ${s.centerY} C ${laneX} ${s.centerY}, ${laneX} ${t.centerY}, ${t.right} ${t.centerY}`,
            active,
          };
        })
        .filter(Boolean);
      setPaths(newPaths);
    }
    recompute();
    window.addEventListener("resize", recompute);
    return () => window.removeEventListener("resize", recompute);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, activeLine, activeNodeId]);

  return (
    <div className="flow-graph" ref={containerRef}>
      <svg className="flow-svg">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="flow-arrowhead" />
          </marker>
          <marker id="arrow-active" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="flow-arrowhead active" />
          </marker>
        </defs>
        {paths.map((p) => (
          <path
            key={p.key}
            d={p.d}
            className={"flow-edge" + (p.active ? " active" : "")}
            markerEnd={p.active ? "url(#arrow-active)" : "url(#arrow)"}
          />
        ))}
      </svg>

      <div className="flow-nodes">
        {nodes.map((n) => (
          <div
            key={n.id}
            ref={(el) => (nodeRefs.current[n.id] = el)}
            className={`flow-node flow-node-${n.kind}` + (activeNodeIds.has(n.id) ? " active" : "")}
            onMouseEnter={() => onHoverNode?.(n.id)}
            onMouseLeave={() => onHoverNode?.(null)}
            onClick={() => onClickNode?.(n.id)}
          >
            <div className="flow-node-kind">{KIND_LABEL[n.kind]}</div>
            <div className="flow-node-label">{n.label}</div>
            {n.table ? (
              <MiniTable table={n.table} />
            ) : (
              <div className="flow-node-value">{highlightValue(n.value, n.highlight)}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
