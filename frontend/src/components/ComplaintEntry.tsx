import UploadZone from "./UploadZone";

interface Props {
  loading: boolean;
  error: string | null;
  onUseDemo: () => void;
  onUpload: (file: File) => void;
}

export default function ComplaintEntry({ loading, error, onUseDemo, onUpload }: Props) {
  return (
    <main className="complaint-entry">
      <div className="complaint-entry__inner">
        <div className="complaint-entry__header">
          <p className="workflow-step-kicker">Analyze a Complaint</p>
          <h1>Start with a complaint document</h1>
        </div>
        <div className="complaint-entry__actions">
          <button className="demo-complaint-btn" type="button" onClick={onUseDemo} disabled={loading}>
            <span>Use demo complaint</span>
            <strong>musk-v-altman-openai-complaint-sf.pdf</strong>
          </button>
          <UploadZone onUpload={onUpload} uploading={loading} error={error} />
        </div>
        {error && <p className="error-msg">{error}</p>}
      </div>
    </main>
  );
}
