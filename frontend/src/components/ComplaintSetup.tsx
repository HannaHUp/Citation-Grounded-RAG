import type { ComplaintWorkflowResponse } from "../types";
import ComplaintTaskGrid from "./ComplaintTaskGrid";
import RepresentedPartySelector from "./RepresentedPartySelector";

interface Props {
  workflow: ComplaintWorkflowResponse;
  selectedTaskIds: string[];
  selectedPartyIds: string[];
  running: boolean;
  error: string | null;
  onToggleTask: (taskId: string) => void;
  onToggleParty: (partyId: string) => void;
  onRun: () => void;
  onReset: () => void;
  onBackToWorkflows: () => void;
}

export default function ComplaintSetup({
  workflow,
  selectedTaskIds,
  selectedPartyIds,
  running,
  error,
  onToggleTask,
  onToggleParty,
  onRun,
  onReset,
  onBackToWorkflows,
}: Props) {
  const workflowLabel = workflow.workflow_id === "contract" ? "Analyze a Contract" : "Analyze a Complaint";
  const canRun = workflow.fixture_available && selectedTaskIds.length > 0 && (workflow.parties.length === 0 || selectedPartyIds.length > 0);

  return (
    <main className="complaint-setup">
      <button type="button" className="workflow-back-link" onClick={onBackToWorkflows}>
        &larr; {workflowLabel}
      </button>
      <div className="workspace-document-bar">
        <div>
          <p className="workflow-step-kicker">Workflow Setup</p>
          <h1>{workflow.document_name}</h1>
          <p>{workflow.detected_summary}</p>
        </div>
        <button className="btn-secondary" type="button" onClick={onReset}>New document</button>
      </div>
      {!workflow.fixture_available && (
        <p className="limited-mode">
          Fixture mode is active. This upload was extracted normally, but rich Vincent-style {workflow.workflow_id === "contract" ? "contract" : "complaint"} analysis for arbitrary documents requires LLM mode.
        </p>
      )}
      <ComplaintTaskGrid tasks={workflow.tasks} selectedTaskIds={selectedTaskIds} onToggle={onToggleTask} />
      {workflow.parties.length > 0 && (
        <RepresentedPartySelector parties={workflow.parties} selectedPartyIds={selectedPartyIds} onToggle={onToggleParty} />
      )}
      <div className="workspace-actions">
        {error && <p className="error-msg">{error}</p>}
        <button className="btn-primary" type="button" disabled={!canRun || running} onClick={onRun}>
          {running ? "Starting analysis..." : "Start analysis"}
        </button>
      </div>
    </main>
  );
}
