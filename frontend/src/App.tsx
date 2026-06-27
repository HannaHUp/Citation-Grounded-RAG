import { useState } from "react";
import { uploadFile, analyze, getAuthorities } from "./api";
import type {
  LegalAuthority,
  Perspective,
  VerifiedFinding,
  WorkflowId,
  WorkflowStep,
} from "./types";
import {
  getTaskByProfileId,
  getWorkflow,
  WORKFLOWS,
  type RunnableProfileId,
} from "./workflows";
import DocViewer from "./components/DocViewer";
import FindingsPanel from "./components/FindingsPanel";
import TaskPicker from "./components/TaskPicker";
import WorkflowPicker from "./components/WorkflowPicker";
import WorkflowUploadStep from "./components/WorkflowUploadStep";

interface Highlight {
  start: number;
  end: number;
}

const DEFAULT_PROFILE_ID: RunnableProfileId = "contract_risk";
const DEFAULT_PERSPECTIVE: Perspective = "neutral";

export default function App() {
  const [step, setStep] = useState<WorkflowStep>("workflow");
  const [workflowId, setWorkflowId] = useState<WorkflowId | null>(null);
  const [fullText, setFullText] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [detectedDocType, setDetectedDocType] = useState<"contract" | "complaint" | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<RunnableProfileId>(DEFAULT_PROFILE_ID);
  const [perspective, setPerspective] = useState<Perspective>(DEFAULT_PERSPECTIVE);
  const [findings, setFindings] = useState<VerifiedFinding[]>([]);
  const [authorities, setAuthorities] = useState<LegalAuthority[]>([]);
  const [highlight, setHighlight] = useState<Highlight | null>(null);
  const [activeFinding, setActiveFinding] = useState<VerifiedFinding | null>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [authoritiesError, setAuthoritiesError] = useState<string | null>(null);
  const [loadingAuthoritiesFor, setLoadingAuthoritiesFor] = useState<string | null>(null);

  const workflow = workflowId === null ? null : getWorkflow(workflowId);
  const selectedTask = getTaskByProfileId(selectedProfileId);

  function handleWorkflowSelect(nextWorkflowId: WorkflowId) {
    const nextWorkflow = getWorkflow(nextWorkflowId);
    setWorkflowId(nextWorkflowId);
    setSelectedProfileId(nextWorkflow.defaultProfileId);
    setPerspective(DEFAULT_PERSPECTIVE);
    setStep("upload");
    clearDocumentState();
  }

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadError(null);
    setDetectedDocType(null);
    try {
      const res = await uploadFile(file);
      const profileId = toRunnableProfileId(res.profile_id);
      setDocId(res.doc_id);
      setFullText(res.full_text);
      setDetectedDocType(res.detected_doc_type);
      setSelectedProfileId(profileId);
      setFindings([]);
      setAuthorities([]);
      setHighlight(null);
      setActiveFinding(null);
      setAnalyzeError(null);
      setStep("tasks");
    } catch (err) {
      setUploadError(parseUploadError(err));
    } finally {
      setUploading(false);
    }
  }

  async function handleAnalyze() {
    if (!docId || !workflow) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    setAuthoritiesError(null);
    setFindings([]);
    setAuthorities([]);
    setHighlight(null);
    setActiveFinding(null);
    try {
      const res = await analyze(
        docId,
        selectedProfileId,
        workflow.requiresPerspective ? perspective : undefined,
      );
      setFindings(res.findings);
      setStep("output");
      // auto-select first verified finding (fallback first) so the right
      // authority pane loads as soon as output opens
      const initial =
        res.findings.find((f) => f.verified) ?? res.findings[0] ?? null;
      if (initial) {
        if (initial.verified && initial.abs_start != null && initial.abs_end != null) {
          setHighlight({ start: initial.abs_start, end: initial.abs_end });
        }
        void loadAuthorities(initial);
      }
    } catch (err) {
      setAnalyzeError(parseAnalyzeError(err));
    } finally {
      setAnalyzing(false);
    }
  }

  function handleProfileSelect(profileId: RunnableProfileId) {
    setSelectedProfileId(profileId);
    setFindings([]);
    setAuthorities([]);
    setHighlight(null);
    setActiveFinding(null);
    setAnalyzeError(null);
    setAuthoritiesError(null);
  }

  function handleFindingClick(f: VerifiedFinding) {
    if (f.verified && f.abs_start != null && f.abs_end != null) {
      setHighlight({ start: f.abs_start, end: f.abs_end });
    }
    // selecting any finding refreshes the right authority pane for it
    void loadAuthorities(f);
  }

  async function loadAuthorities(finding: VerifiedFinding) {
    if (!docId) return;
    setLoadingAuthoritiesFor(finding.source_chunk_id);
    setAuthoritiesError(null);
    setActiveFinding(finding);
    setAuthorities([]);
    try {
      const res = await getAuthorities(docId, selectedProfileId, finding);
      setAuthorities(res.authorities);
    } catch (err) {
      setAuthoritiesError(parseAnalyzeError(err));
    } finally {
      setLoadingAuthoritiesFor(null);
    }
  }

  function clearDocumentState() {
    setFullText(null);
    setDocId(null);
    setDetectedDocType(null);
    setFindings([]);
    setAuthorities([]);
    setHighlight(null);
    setActiveFinding(null);
    setUploadError(null);
    setAnalyzeError(null);
    setAuthoritiesError(null);
    setLoadingAuthoritiesFor(null);
  }

  function renderStep() {
    if (step === "workflow" || workflow === null) {
      return (
        <WorkflowPicker
          workflows={WORKFLOWS}
          onSelectWorkflow={handleWorkflowSelect}
        />
      );
    }

    if (step === "upload") {
      return (
        <WorkflowUploadStep
          workflow={workflow}
          uploading={uploading}
          error={uploadError}
          onUpload={handleUpload}
          onBack={() => {
            setWorkflowId(null);
            setStep("workflow");
          }}
        />
      );
    }

    if (step === "tasks") {
      return (
        <TaskPicker
          workflow={workflow}
          detectedDocType={detectedDocType}
          selectedProfileId={selectedProfileId}
          perspective={perspective}
          analyzing={analyzing}
          analyzeError={analyzeError}
          onSelectProfile={handleProfileSelect}
          onSelectPerspective={setPerspective}
          onRunTask={handleAnalyze}
          onBack={() => setStep("upload")}
        />
      );
    }

    if (fullText === null) {
      return (
        <WorkflowUploadStep
          workflow={workflow}
          uploading={uploading}
          error={uploadError}
          onUpload={handleUpload}
          onBack={() => setStep("workflow")}
        />
      );
    }

    return (
      <>
        <div className="output-toolbar">
          <button type="button" className="btn-secondary" onClick={() => setStep("tasks")}>
            Back to tasks
          </button>
          <span>{workflow.title}</span>
          <span>Task: <strong>{selectedTask.title}</strong></span>
          {detectedDocType !== null && (
            <span>Detected: <strong>{detectedDocType === "contract" ? "Contract" : "Complaint"}</strong></span>
          )}
          {workflow.requiresPerspective && (
            <span>Perspective: <strong>{capitalize(perspective)}</strong></span>
          )}
        </div>
        <main className="app-body app-body--output">
          <section className="doc-pane">
            <DocViewer text={fullText} highlight={highlight} />
          </section>
          <section className="findings-pane">
            <FindingsPanel
              findings={findings}
              authorities={authorities}
              activeFinding={activeFinding}
              hasDocument={true}
              analyzing={analyzing}
              loadingAuthoritiesFor={loadingAuthoritiesFor}
              analyzeError={analyzeError ?? authoritiesError}
              onAnalyze={handleAnalyze}
              onFindingClick={handleFindingClick}
              onAuthorityLookup={loadAuthorities}
              detectedDocType={null}
              selectedProfileId={selectedProfileId}
              onSelectProfile={(id) => handleProfileSelect(toRunnableProfileId(id))}
            />
          </section>
        </main>
      </>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <span>Citation-Grounded RAG</span>
        <WorkflowProgress step={step} />
      </header>
      {renderStep()}
    </div>
  );
}

function parseUploadError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);
  if (/413|too large/i.test(raw)) return "File too large. Maximum size is 20 MB.";
  if (/400|unsupported|type/i.test(raw)) return "Unsupported file type. Please upload a PDF or DOCX.";
  return "Upload failed. Check your connection and try again.";
}

function parseAnalyzeError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);
  if (/404|not found/i.test(raw)) return "Session expired. Please re-upload your document.";
  return "Analysis failed. Try again or upload a different document.";
}

function toRunnableProfileId(profileId: string): RunnableProfileId {
  return profileId === "complaint_claims" ? "complaint_claims" : "contract_risk";
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function WorkflowProgress({ step }: { step: WorkflowStep }) {
  const items: Array<{ id: WorkflowStep; label: string }> = [
    { id: "workflow", label: "Workflow" },
    { id: "upload", label: "Upload" },
    { id: "tasks", label: "Tasks" },
    { id: "output", label: "Output" },
  ];
  const activeIndex = items.findIndex((item) => item.id === step);

  return (
    <nav className="workflow-progress" aria-label="Workflow progress">
      {items.map((item, index) => (
        <span
          key={item.id}
          className={`workflow-progress__item${index <= activeIndex ? " workflow-progress__item--active" : ""}`}
        >
          {item.label}
        </span>
      ))}
    </nav>
  );
}
