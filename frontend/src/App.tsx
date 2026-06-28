import { useState } from "react";
import {
  getWorkflow,
  getWorkflowAuthorities,
  loadDemoComplaint,
  loadDemoContract,
  sendChatMessage,
  startChat,
  uploadFile,
} from "./api";
import ComplaintChatWorkspace from "./components/ComplaintChatWorkspace";
import ComplaintEntry from "./components/ComplaintEntry";
import ComplaintSetup from "./components/ComplaintSetup";
import WorkflowLauncher from "./components/WorkflowLauncher";
import type {
  ChatMessage,
  ChatThread,
  ComplaintWorkflowResponse,
  LegalAuthority,
  ReportCitation,
  WorkflowId,
} from "./types";
import { WORKFLOWS } from "./workflows";

type AppPage =
  | "launcher"
  | "complaint-entry"
  | "complaint-setup"
  | "complaint-workspace"
  | "contract-entry"
  | "contract-setup"
  | "contract-workspace";

export default function App() {
  const [page, setPage] = useState<AppPage>("launcher");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<WorkflowId | null>(null);
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

  function handleWorkflowSelect(workflowId: WorkflowId) {
    clearComplaintState();
    setSelectedWorkflowId(workflowId);
    setPage(workflowId === "complaint" ? "complaint-entry" : "contract-entry");
  }

  async function handleUseDemo() {
    setLoadingDocument(true);
    setError(null);
    try {
      const nextWorkflow = selectedWorkflowId === "contract"
        ? await loadDemoContract()
        : await loadDemoComplaint();
      applyWorkflow(nextWorkflow);
    } catch (err) {
      setError(parseError(err, "Demo document could not be loaded."));
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
    setSelectedWorkflowId(nextWorkflow.workflow_id === "contract" ? "contract" : "complaint");
    setPage(nextWorkflow.workflow_id === "contract" ? "contract-setup" : "complaint-setup");
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
      setPage(workflow.workflow_id === "contract" ? "contract-workspace" : "complaint-workspace");
      const firstAssistant = nextThread.messages.find((message) => message.role === "assistant");
      setActiveCitation(firstAssistant?.citations[0] ?? firstAssistant?.report?.citations[0] ?? null);
      void loadAuthorities(workflow.doc_id, workflow.workflow_id);
    } catch (err) {
      setError(parseError(err, "Analysis failed. Fixture mode only supports bundled demo documents."));
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

  async function loadAuthorities(docId: string, workflowId: string) {
    setLoadingAuthorities(true);
    setAuthoritiesError(null);
    try {
      const finding = workflowId === "contract" ? "Antitrust Implications" : "Matters Like This";
      const response = await getWorkflowAuthorities(docId, workflowId, finding);
      setAuthorities(response.authorities);
    } catch (err) {
      setAuthoritiesError(parseError(err, "Legal authorities could not be loaded."));
    } finally {
      setLoadingAuthorities(false);
    }
  }

  function reset() {
    setPage("launcher");
    clearComplaintState();
    setSelectedWorkflowId(null);
  }

  function clearComplaintState() {
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
        <span className="app-header__mode">{headerMode(page)}</span>
      </header>
      {page === "launcher" ? (
        <WorkflowLauncher workflows={WORKFLOWS} onSelectWorkflow={handleWorkflowSelect} />
      ) : page === "complaint-entry" || page === "contract-entry" || !workflow ? (
        <ComplaintEntry
          workflowLabel={selectedWorkflowId === "contract" ? "Analyze a Contract" : "Analyze a Complaint"}
          title={selectedWorkflowId === "contract" ? "Start with a contract document" : "Start with a complaint document"}
          demoActionLabel={selectedWorkflowId === "contract" ? "Use demo contract" : "Use demo complaint"}
          demoDocumentName={selectedWorkflowId === "contract" ? "LinkedIn Merger Agreement.docx" : "musk-v-altman-openai-complaint-sf.pdf"}
          loading={loadingDocument}
          error={error}
          onUseDemo={handleUseDemo}
          onUpload={handleUpload}
          onBackToWorkflows={reset}
        />
      ) : page === "complaint-setup" || page === "contract-setup" || !thread ? (
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
          onBackToWorkflows={reset}
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
          onBackToSetup={() => setPage(workflow.workflow_id === "contract" ? "contract-setup" : "complaint-setup")}
          onBackToWorkflows={reset}
          onSendMessage={handleSendMessage}
        />
      )}
    </div>
  );
}

function headerMode(page: AppPage): string {
  if (page.startsWith("contract")) return "Analyze a Contract";
  if (page.startsWith("complaint")) return "Analyze a Complaint";
  return "Workflows";
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
