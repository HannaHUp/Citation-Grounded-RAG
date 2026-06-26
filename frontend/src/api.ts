import type { UploadResponse, AnalyzeResponse } from "./types";

const BASE = "http://localhost:8000";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Upload failed (${res.status})`);
  }
  return res.json() as Promise<UploadResponse>;
}

export async function analyze(docId: string): Promise<AnalyzeResponse> {
  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, profile_id: "contract_risk" }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Analyze failed (${res.status})`);
  }
  return res.json() as Promise<AnalyzeResponse>;
}
