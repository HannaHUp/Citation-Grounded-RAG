import type { EnabledWorkflow } from "../workflows";
import UploadZone from "./UploadZone";

interface Props {
  workflow: EnabledWorkflow;
  uploading: boolean;
  error: string | null;
  onUpload: (file: File) => void;
  onBack: () => void;
}

export default function WorkflowUploadStep({
  workflow,
  uploading,
  error,
  onUpload,
  onBack,
}: Props) {
  return (
    <section className="workflow-screen workflow-upload" aria-labelledby="workflow-upload-title">
      <div className="workflow-screen__inner workflow-screen__inner--narrow">
        <button type="button" className="btn-secondary workflow-back" onClick={onBack}>
          Back to workflows
        </button>
        <div className="workflow-step-kicker">Selected workflow</div>
        <h1 id="workflow-upload-title">{workflow.title}</h1>
        <p className="workflow-step-copy">{workflow.description}</p>
        <UploadZone onUpload={onUpload} uploading={uploading} error={error} />
      </div>
    </section>
  );
}
