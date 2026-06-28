import type {
  UploadResponse,
  AnalyzeResponse,
  AnalysisReport,
  AuthoritiesResponse,
  ChatMessage,
  ChatThread,
  ComplaintWorkflowResponse,
  Perspective,
  VerifiedFinding,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8010";

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

export async function loadDemoComplaint(): Promise<ComplaintWorkflowResponse> {
  const res = await fetch(`${BASE}/demo/complaint/musk-altman`, { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Demo load failed (${res.status})`);
  }
  return res.json() as Promise<ComplaintWorkflowResponse>;
}

export async function loadDemoContract(): Promise<ComplaintWorkflowResponse> {
  const res = await fetch(`${BASE}/demo/contract/linkedin-merger`, { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Demo load failed (${res.status})`);
  }
  return res.json() as Promise<ComplaintWorkflowResponse>;
}

export async function getWorkflow(docId: string): Promise<ComplaintWorkflowResponse> {
  const res = await fetch(`${BASE}/workflow/${docId}`);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Workflow failed (${res.status})`);
  }
  return res.json() as Promise<ComplaintWorkflowResponse>;
}

export async function runAnalysisReport(
  docId: string,
  taskIds: string[],
  representedPartyIds: string[],
): Promise<AnalysisReport> {
  const res = await fetch(`${BASE}/analysis/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      doc_id: docId,
      task_ids: taskIds,
      represented_party_ids: representedPartyIds,
    }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Report failed (${res.status})`);
  }
  return res.json() as Promise<AnalysisReport>;
}

export async function startChat(
  docId: string,
  taskIds: string[],
  representedPartyIds: string[],
): Promise<ChatThread> {
  const res = await fetch(`${BASE}/chat/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      doc_id: docId,
      task_ids: taskIds,
      represented_party_ids: representedPartyIds,
    }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Chat start failed (${res.status})`);
  }
  return res.json() as Promise<ChatThread>;
}

export async function sendChatMessage(threadId: string, message: string): Promise<ChatMessage> {
  const res = await fetch(`${BASE}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, message }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Chat message failed (${res.status})`);
  }
  return res.json() as Promise<ChatMessage>;
}

export async function analyze(
  docId: string,
  profileId: string,
  perspective?: Perspective,
): Promise<AnalyzeResponse> {
  const body: {
    doc_id: string;
    profile_id: string;
    perspective?: Perspective;
  } = { doc_id: docId, profile_id: profileId };

  if (perspective !== undefined) {
    body.perspective = perspective;
  }

  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
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

export async function getComplaintAuthorities(
  docId: string,
  finding?: string,
): Promise<AuthoritiesResponse> {
  const res = await fetch(`${BASE}/authorities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      doc_id: docId,
      profile_id: "complaint_claims",
      finding,
    }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Authorities failed (${res.status})`);
  }
  return res.json() as Promise<AuthoritiesResponse>;
}

export async function getWorkflowAuthorities(
  docId: string,
  workflowId: string,
  finding?: string,
): Promise<AuthoritiesResponse> {
  const res = await fetch(`${BASE}/authorities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      doc_id: docId,
      profile_id: workflowId === "contract" ? "contract_antitrust" : "complaint_claims",
      finding,
    }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Authorities failed (${res.status})`);
  }
  return res.json() as Promise<AuthoritiesResponse>;
}
