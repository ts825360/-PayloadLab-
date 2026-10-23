import { useEffect, useRef, useState } from "react";

const STATUS_ICON = { passed: "✓", failed: "✕", unknown: "–" };

let measureCanvas;
function measureTextWidth(text, font) {
  measureCanvas = measureCanvas || document.createElement("canvas");
  const ctx = measureCanvas.getContext("2d");
  ctx.font = font;
  return ctx.measureText(text).width;
}

export default function LensInput({ value, onChange, placeholder, failed, lensMessage, lensSteps }) {
  const [hovering, setHovering] = useState(false);
  const inputRef = useRef(null);
  const [mark, setMark] = useState({ left: 0, width: 0 });
  const open = failed && hovering;

  useEffect(() => {
    if (!failed || !inputRef.current) return;
    const el = inputRef.current;
    const cs = getComputedStyle(el);
    const font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    setMark({
      left: parseFloat(cs.paddingLeft) || 0,
      // 실제 입력한 글자 수만큼만 밑줄이 그려지도록 텍스트 폭을 직접 측정
      width: measureTextWidth(value, font),
    });
  }, [value, failed]);

  return (
    <div className="lens-input-wrapper">
      <div className="input-row">
        <input
          ref={inputRef}
          className={failed ? "input-failed" : ""}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
        />
        {failed && (
          <span
            className="underline-mark"
            style={{ left: mark.left, width: mark.width }}
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
          />
        )}
      </div>
      {open && (
        <div className="lens-popover-inline">
          <div className="lens-popover-title">왜 실패했나요?</div>
          <div className="lens-message">{lensMessage}</div>
          {lensSteps && lensSteps.length > 0 && (
            <div className="lens-stepper">
              {lensSteps.map((step, i) => (
                <div className={`lens-step lens-step-${step.status}`} key={i}>
                  <span className="dot">{STATUS_ICON[step.status]}</span>
                  <span className="text">{step.description}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
