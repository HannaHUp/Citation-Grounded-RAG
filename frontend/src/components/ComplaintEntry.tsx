import UploadZone from "./UploadZone";

interface Props {
  workflowLabel?: string;
  title?: string;
  demoActionLabel?: string;
  demoDocumentName?: string;
  loading: boolean;
  error: string | null;
  onUseDemo: () => void;
  onUpload: (file: File) => void;
  onBackToWorkflows: () => void;
}

export default function ComplaintEntry({
  workflowLabel = "Analyze a Complaint",
  title = "Start with a complaint document",
  demoActionLabel = "Use demo complaint",
  demoDocumentName = "musk-v-altman-openai-complaint-sf.pdf",
  loading,
  error,
  onUseDemo,
  onUpload,
  onBackToWorkflows,
}: Props) {
  return (
    <main className="complaint-entry">
      <div className="complaint-entry__inner">
        <button type="button" className="workflow-back-link" onClick={onBackToWorkflows}>
          &larr; {workflowLabel}
        </button>
        <div className="complaint-entry__header">
          <p className="workflow-step-kicker">{workflowLabel}</p>
          <h1>{title}</h1>
        </div>
        <div className="complaint-entry__actions">
          <button className="demo-complaint-btn" type="button" onClick={onUseDemo} disabled={loading}>
            <span>{demoActionLabel}</span>
            <strong>{demoDocumentName}</strong>
          </button>
          <UploadZone onUpload={onUpload} uploading={loading} error={error} />
        </div>
        {error && <p className="error-msg">{error}</p>}
      </div>
    </main>
  );
}
