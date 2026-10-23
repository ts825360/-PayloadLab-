import { useState } from "react";
import CodeView from "./CodeView.jsx";
import FlowGraph from "./FlowGraph.jsx";

/**
 * 코드와 데이터 흐름 그래프를 한 화면에 나란히 놓고, 마우스를 올리거나
 * 클릭하면 코드 줄 <-> 노드가 양방향으로 서로 강조되게 한다. hover는
 * 지나가면 사라지고, click은 "고정"되어 손을 떼도 유지된다 (다시 클릭하면
 * 해제) -- 설명을 읽는 동안 강조가 사라지지 않게 하기 위함.
 */
export default function AttemptFlowView({ nodes, edges, code }) {
  const [hovered, setHovered] = useState(null); // { line } | { node } | null
  const [pinned, setPinned] = useState(null);

  const active = hovered || pinned;
  const nodesById = Object.fromEntries(nodes.map((n) => [n.id, n]));

  const activeLine =
    active?.line != null ? active.line : active?.node != null ? nodesById[active.node]?.code_line ?? null : null;
  const activeNodeId = active?.node ?? null;

  function togglePin(next) {
    const same =
      pinned && ((pinned.line != null && pinned.line === next.line) || (pinned.node != null && pinned.node === next.node));
    setPinned(same ? null : next);
  }

  return (
    <div className="flow-layout">
      <div className="flow-code-pane">
        <div className="flow-pane-title">취약한 코드</div>
        <CodeView
          code={code}
          activeLine={activeLine}
          onHoverLine={(line) => setHovered(line == null ? null : { line })}
          onClickLine={(line) => togglePin({ line })}
        />
      </div>
      <div className="flow-graph-pane">
        <div className="flow-pane-title">데이터 흐름</div>
        <FlowGraph
          nodes={nodes}
          edges={edges}
          activeLine={activeLine}
          activeNodeId={activeNodeId}
          onHoverNode={(id) => setHovered(id == null ? null : { node: id })}
          onClickNode={(id) => togglePin({ node: id })}
        />
      </div>
    </div>
  );
}
