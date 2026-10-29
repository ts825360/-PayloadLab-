export const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export async function fetchLabs() {
  const res = await fetch(`${API_BASE}/labs`);
  if (!res.ok) throw new Error("랩 목록을 불러오지 못했습니다");
  return res.json();
}

export class LabRequestError extends Error {
  constructor(message) {
    super(message);
    this.name = "LabRequestError";
  }
}

async function failureMessage(res, fallback) {
  if (res.status === 413)
    return "입력 전체 크기가 실습 요청 한도를 넘었습니다. 입력을 줄여 다시 시도하세요.";
  if (res.status === 422)
    return "입력 형식·길이·값이 실습 허용 범위를 벗어났습니다. 입력을 확인해 주세요.";
  if (res.status === 429) {
    try {
      const body = await res.json();
      if (body?.code === "rate_limit") {
        const retry = res.headers?.get?.("Retry-After");
        // Reflect only a short, positive integer; never server detail or HTML.
        if (typeof retry === "string" && /^[1-9]\d{0,5}$/.test(retry))
          return `요청이 잠시 몰렸습니다. ${Number(retry)}초 뒤 다시 시도해 주세요.`;
        return "요청이 잠시 몰렸습니다. 잠시 기다린 뒤 다시 시도해 주세요.";
      }
    } catch { /* Unrelated/malformed responses stay generic. */ }
  }
  if (res.status === 503) {
    try {
      const body = await res.json();
      if (body?.code === "response_limit")
        return "조회 결과가 표시 가능한 크기를 넘었습니다. 반환 범위를 줄여 다시 시도하세요.";
      if (["concurrency_limit", "peer_capacity"].includes(body?.code))
        return "실습 서버가 사용 중입니다. 잠시 후 다시 시도해 주세요.";
    } catch { /* Keep malformed or unrelated server errors generic. */ }
  }
  return fallback;
}

async function failureError(res, fallback) {
  const message = await failureMessage(res, fallback);
  return message === fallback ? new Error(fallback) : new LabRequestError(message);
}

export async function attemptLab(labId, payload) {
  const res = await fetch(`${API_BASE}/labs/${labId}/attempt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await failureError(res, "시도 요청이 실패했습니다");
  return res.json();
}

export async function analyzeLab(labId, payload, signal) {
  const res = await fetch(`${API_BASE}/labs/${labId}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) throw await failureError(res, "입력 분석 요청이 실패했습니다");
  return res.json();
}
