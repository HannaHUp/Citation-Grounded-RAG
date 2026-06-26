import type { UploadResponse, AnalyzeResponse, AuthoritiesResponse, VerifiedFinding } from "./types";

const BASE = "http://localhost:8010";

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

export async function analyze(docId: string, profileId: string): Promise<AnalyzeResponse> {
  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, profile_id: profileId }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Analyze failed (${res.status})`);
  }
  return res.json() as Promise<AnalyzeResponse>;
}

export async function getAuthorities(
  docId: string,
  profileId: string,
  finding?: VerifiedFinding,
): Promise<AuthoritiesResponse> {
  const res = await fetch(`${BASE}/authorities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      doc_id: docId,
      profile_id: profileId,
      finding: finding?.finding,
      quote: finding?.quote,
      source_chunk_id: finding?.source_chunk_id,
    }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Authorities failed (${res.status})`);
  }
  return res.json() as Promise<AuthoritiesResponse>;
}
