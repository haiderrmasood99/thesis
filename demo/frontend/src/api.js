const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return response.json();
}

export function fetchOptions() {
  return requestJson("/api/v1/options");
}

export function fetchDailyAdvice(payload) {
  return requestJson("/api/v1/advice/daily", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchSeasonalAdvice(payload) {
  return requestJson("/api/v1/advice/seasonal", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
