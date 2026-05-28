const TS_API = import.meta.env.VITE_TS_API_BASE_URL || "http://localhost:8001";

async function parseResponse(response) {
  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!response.ok) {
    const detail = typeof data === "object" ? data?.detail : data;
    const message = typeof detail === "object" ? JSON.stringify(detail, null, 2) : detail || `API 요청 실패 (${response.status})`;
    throw new Error(message);
  }
  return data;
}

export async function checkTsHealth() {
  const res = await fetch(`${TS_API}/api/ts/health`);
  return parseResponse(res);
}

export async function runTsAgent({ inputFile, uiFile, model }) {
  const fd = new FormData();
  fd.append("input_file", inputFile);
  if (uiFile) fd.append("ui_file", uiFile);
  fd.append("model", model);
  const res = await fetch(`${TS_API}/api/ts/generate`, { method: "POST", body: fd });
  return parseResponse(res);
}

export async function getTsResult() {
  const res = await fetch(`${TS_API}/api/ts/result`);
  return parseResponse(res);
}

export function getTsDocxDownloadUrl() {
  return `${TS_API}/api/ts/download-docx`;
}

export function getTsJsonDownloadUrl() {
  return `${TS_API}/api/ts/download-json`;
}
