import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

export default function LensCloseConfirmation({ onConfirm, onCancel }) {
  const confirmRef = useRef(null),
    cancelRef = useRef(null),
    restoreFocus = useRef(true);
  function confirm() {
    restoreFocus.current = false;
    onConfirm();
  }
  useEffect(() => {
    const previous = document.activeElement;
    confirmRef.current?.focus();
    function keys(event) {
      if (event.isComposing || event.keyCode === 229) return;
      if (event.key === "Escape" || event.key === "Enter") {
        event.preventDefault();
        event.stopImmediatePropagation();
        if (event.repeat) return;
        if (
          event.key === "Escape" ||
          (document.activeElement === cancelRef.current &&
            event.key === "Enter")
        )
          onCancel();
        else {
          restoreFocus.current = false;
          onConfirm();
        }
      }
      if (event.key === "Tab") {
        event.preventDefault();
        (document.activeElement === confirmRef.current
          ? cancelRef
          : confirmRef
        ).current?.focus();
      }
    }
    document.addEventListener("keydown", keys, true);
    return () => {
      document.removeEventListener("keydown", keys, true);
      if (restoreFocus.current && previous?.isConnected) previous.focus();
    };
  }, [onConfirm, onCancel]);
  return createPortal(
    <div className="lens-close-backdrop">
      <section
        className="lens-close-confirmation"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="lens-close-title"
        aria-describedby="lens-close-description"
      >
        <span className="eyebrow">LENS</span>
        <h2 id="lens-close-title">Lens 관찰창을 닫을까요?</h2>
        <p id="lens-close-description">
          확대·비교 화면만 닫습니다. 입력과 시도 기록은 그대로 유지돼요.
        </p>
        <div className="lens-close-actions">
          <button
            ref={cancelRef}
            type="button"
            className="secondary-button"
            onClick={onCancel}
          >
            계속 보기 <kbd>Esc</kbd>
          </button>
          <button
            ref={confirmRef}
            type="button"
            className="primary-button"
            onClick={confirm}
          >
            닫기 <kbd>Enter</kbd>
          </button>
        </div>
      </section>
    </div>,
    document.body,
  );
}
