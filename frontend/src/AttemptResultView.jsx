import AttemptFlowView from "./AttemptFlowView.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function AttemptResultView({ result, submittedValue, labId, category }) {
  const isLive = category === "reflected_xss";

  return (
    <div>
      <strong className="success-heading">성공! 공격이 통했습니다.</strong>

      {isLive && (
        <div className="live-primary">
          <div className="live-hint">
            아래는 우리 서버가 실제로 돌려준 페이지입니다 — 탭 뒤에 숨기지 않고 바로 보여드립니다. 진짜로 실행됩니다.
          </div>
          <iframe
            className="live-frame"
            sandbox="allow-scripts allow-modals"
            src={`${API_BASE}/labs/${labId}/render?query=${encodeURIComponent(submittedValue)}`}
            title="실제 실행 결과"
          />
          <div className="view-note">아래는 이 실행이 코드의 어느 지점에서 어떻게 만들어졌는지 보여주는 흐름입니다.</div>
        </div>
      )}

      <AttemptFlowView nodes={result.flow_nodes} edges={result.flow_edges} code={result.code_snippet} />
    </div>
  );
}
