import { useState } from "react";
import {
  getComplaintAuthorities,
  getWorkflow,
  loadDemoComplaint,
  sendChatMessage,
  startChat,
  uploadFile,
} from "./api";
import ComplaintChatWorkspace from "./components/ComplaintChatWorkspace";
import ComplaintEntry from "./components/ComplaintEntry";
import ComplaintSetup from "./components/ComplaintSetup";
import type {
  ChatMessage,
  ChatThread,
  ComplaintWorkflowResponse,
  LegalAuthority,
  ReportCitation,
} from "./types";

type ComplaintPage = "entry" | "setup" | "workspace";

export default function App() {
  const [page, setPage] = useState<ComplaintPage>("entry");
  const [workflow, setWorkflow] = useState<ComplaintWorkflowResponse | null>(null);
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([]);
  const [selectedPartyIds, setSelectedPartyIds] = useState<string[]>([]);
  const [thread, setThread] = useState<ChatThread | null>(null);
  const [authorities, setAuthorities] = useState<LegalAuthority[]>([]);
  const [activeCitation, setActiveCitation] = useState<ReportCitation | null>(null);

  const [loadingDocument, setLoadingDocument] = useState(false);
  const [running, setRunning] = useState(false);
  const [sending, setSending] = useState(false);
  const [loadingAuthorities, setLoadingAuthorities] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authoritiesError, setAuthoritiesError] = useState<string | null>(null);

  async function handleUseDemo() {
    setLoadingDocument(true);
    setError(null);
    try {
      const nextWorkflow = await loadDemoComplaint();
      applyWorkflow(nextWorkflow);
    } catch (err) {
      setError(parseError(err, "Demo complaint could not be loaded."));
    } finally {
      setLoadingDocument(false);
    }
  }

  async function handleUpload(file: File) {
    setLoadingDocument(true);
    setError(null);
    try {
      const upload = await uploadFile(file);
      const nextWorkflow = await getWorkflow(upload.doc_id);
      applyWorkflow(nextWorkflow);
    } catch (err) {
      setError(parseError(err, "Upload failed. Please use a PDF or DOCX under 20 MB."));
    } finally {
      setLoadingDocument(false);
    }
  }

  function applyWorkflow(nextWorkflow: ComplaintWorkflowResponse) {
    setWorkflow(nextWorkflow);
    setPage("setup");
    setSelectedTaskIds(
      nextWorkflow.tasks
        .filter((task) => task.enabled && task.fixture_supported)
        .slice(0, 3)
        .map((task) => task.id),
    );
    setSelectedPartyIds(
      nextWorkflow.parties
        .filter((party) => party.selected_by_default)
        .map((party) => party.id),
    );
    setThread(null);
    setAuthorities([]);
    setActiveCitation(null);
    setAuthoritiesError(null);
  }

  function toggleTask(taskId: string) {
    setSelectedTaskIds((current) =>
      current.includes(taskId)
        ? current.filter((id) => id !== taskId)
        : [...current, taskId],
    );
    setThread(null);
    setActiveCitation(null);
  }

  function toggleParty(partyId: string) {
    setSelectedPartyIds((current) =>
      current.includes(partyId)
        ? current.filter((id) => id !== partyId)
        : [...current, partyId],
    );
    setThread(null);
    setActiveCitation(null);
  }

  async function handleRunAnalysis() {
    if (!workflow) return;
    setRunning(true);
    setError(null);
    setAuthoritiesError(null);
    try {
      const nextThread = await startChat(workflow.doc_id, selectedTaskIds, selectedPartyIds);
      setThread(nextThread);
      setPage("workspace");
      const firstAssistant = nextThread.messages.find((message) => message.role === "assistant");
      setActiveCitation(firstAssistant?.citations[0] ?? firstAssistant?.report?.citations[0] ?? null);
      void loadAuthorities(workflow.doc_id);
    } catch (err) {
      setError(parseError(err, "Analysis failed. Fixture mode only supports the bundled demo complaint."));
    } finally {
      setRunning(false);
    }
  }

  async function handleSendMessage(message: string) {
    if (!thread) return;
    setSending(true);
    setError(null);
    const userMessage: ChatMessage = {
      id: `client-${Date.now()}`,
      role: "user",
      content: message,
      report: null,
      citations: [],
      created_at: new Date().toISOString(),
    };
    try {
      const assistantMessage = await sendChatMessage(thread.thread_id, message);
      setThread((current) =>
        current
          ? { ...current, messages: [...current.messages, userMessage, assistantMessage] }
          : current,
      );
      setActiveCitation(assistantMessage.citations[0] ?? activeCitation);
    } catch (err) {
      setThread((current) =>
        current
          ? { ...current, messages: [...current.messages, userMessage] }
          : current,
      );
      setError(parseError(err, "Follow-up failed. Fixture mode supports only bundled demo chat examples."));
    } finally {
      setSending(false);
    }
  }

  async function loadAuthorities(docId: string) {
    setLoadingAuthorities(true);
    setAuthoritiesError(null);
    try {
      const response = await getComplaintAuthorities(docId, "Matters Like This");
      setAuthorities(response.authorities);
    } catch (err) {
      setAuthoritiesError(parseError(err, "Legal authorities could not be loaded."));
    } finally {
      setLoadingAuthorities(false);
    }
  }

  function reset() {
    setPage("entry");
    setWorkflow(null);
    setSelectedTaskIds([]);
    setSelectedPartyIds([]);
    setThread(null);
    setAuthorities([]);
    setActiveCitation(null);
    setError(null);
    setAuthoritiesError(null);
  }

  return (
    <div className="app">
      <header className="app-header">
        <span>Citation-Grounded RAG</span>
        <span className="app-header__mode">Analyze a Complaint</span>
      </header>
      {page === "entry" || !workflow ? (
        <ComplaintEntry
          loading={loadingDocument}
          error={error}
          onUseDemo={handleUseDemo}
          onUpload={handleUpload}
        />
      ) : page === "setup" || !thread ? (
        <ComplaintSetup
          workflow={workflow}
          selectedTaskIds={selectedTaskIds}
          selectedPartyIds={selectedPartyIds}
          running={running}
          error={error}
          onToggleTask={toggleTask}
          onToggleParty={toggleParty}
          onRun={handleRunAnalysis}
          onReset={reset}
        />
      ) : (
        <ComplaintChatWorkspace
          workflow={workflow}
          thread={thread}
          authorities={authorities}
          activeCitation={activeCitation}
          loadingAuthorities={loadingAuthorities}
          sending={sending}
          error={error}
          authoritiesError={authoritiesError}
          onCitationSelect={setActiveCitation}
          onBackToSetup={() => setPage("setup")}
          onSendMessage={handleSendMessage}
        />
      )}
    </div>
  );
}

function parseError(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message) {
    try {
      const parsed = JSON.parse(err.message);
      if (typeof parsed.detail === "string") return parsed.detail;
    } catch {
      return err.message;
    }
  }
  return fallback;
}
