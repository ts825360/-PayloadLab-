export default function CodeView({ code, activeLine, onHoverLine, onClickLine }) {
  const lines = code.split("\n");
  return (
    <pre className="flow-code">
      <code>
        {lines.map((line, i) => (
          <div
            key={i}
            className={"flow-code-line" + (i === activeLine ? " active" : "")}
            onMouseEnter={() => onHoverLine?.(i)}
            onMouseLeave={() => onHoverLine?.(null)}
            onClick={() => onClickLine?.(i)}
          >
            <span className="flow-code-lineno">{i + 1}</span>
            <span className="flow-code-text">{line || " "}</span>
          </div>
        ))}
      </code>
    </pre>
  );
}
