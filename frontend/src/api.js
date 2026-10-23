export const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export async function fetchLabs() {
  const res = await fetch(`${API_BASE}/labs`);
  if (!res.ok) throw new Error("랩 목록을 불러오지 못했습니다");
  return res.json();
}

export async function attemptLab(labId, payload) {
  const res = await fetch(`${API_BASE}/labs/${labId}/attempt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("시도 요청이 실패했습니다");
  return res.json();
}

export async function analyzeLab(labId, payload, signal) {
  const res = await fetch(`${API_BASE}/labs/${labId}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) throw new Error("입력 분석 요청이 실패했습니다");
  return res.json();
}
