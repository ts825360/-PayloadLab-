import { useEffect, useRef, useState } from "react";
import { analyzeLab, LabRequestError } from "./api.js";

export default function useInputAnalysis(lab, payload, enabled) {
  const key = `${lab}:${JSON.stringify(payload)}`;
  const [state, setState] = useState({ key: "", trace: null, status: "idle" });
  const sequence = useRef(0);
  useEffect(() => {
    const id = ++sequence.current;
    if (!enabled) {
      setState({ key, trace: null, status: "idle" });
      return;
    }
    const controller = new AbortController();
    setState({ key, trace: null, status: "pending" });
    const timer = setTimeout(async () => {
      try {
        const trace = await analyzeLab(lab, payload, controller.signal);
        if (id === sequence.current && !controller.signal.aborted)
          setState({ key, trace, status: "ready" });
      } catch (error) {
        if (
          error.name !== "AbortError" &&
          id === sequence.current &&
          !controller.signal.aborted
        )
          setState({ key, trace: null, status: "error", error: error instanceof LabRequestError ? error.message : "입력 분석 결과를 받지 못했습니다. 연결을 확인하고 다시 입력해 주세요." });
      }
    }, 320);
    return () => {
      clearTimeout(timer);
      controller.abort();
      sequence.current++;
    };
  }, [key, enabled]);
  return state.key === key
    ? state
    : { trace: null, status: enabled ? "pending" : "idle" };
}
