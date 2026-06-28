import { useState } from "react";
import type { ChatThread, ComplaintWorkflowResponse, LegalAuthority, ReportCitation } from "../types";
import ChatMessageView from "./ChatMessageView";
import FollowUpComposer from "./FollowUpComposer";
import GroundTruthPanel from "./GroundTruthPanel";
import SourcePreviewPanel from "./SourcePreviewPanel";

interface Props {
  workflow: ComplaintWorkflowResponse;
  thread: ChatThread;
  authorities: LegalAuthority[];
  activeCitation: ReportCitation | null;
  loadingAuthorities: boolean;
  sending: boolean;
  error: string | null;
  authoritiesError: string | null;
  onCitationSelect: (citation: ReportCitation) => void;
  onBackToSetup: () => void;
  onBackToWorkflows: () => void;
  onSendMessage: (message: string) => void;
}

export default function ComplaintChatWorkspace({
  workflow,
  thread,
  authorities,
  activeCitation,
  loadingAuthorities,
  sending,
  error,
  authoritiesError,
  onCitationSelect,
  onBackToSetup,
  onBackToWorkflows,
  onSendMessage,
}: Props) {
  const [verifyingCitation, setVerifyingCitation] = useState<ReportCitation | null>(null);
  const workflowLabel = workflow.workflow_id === "contract" ? "Analyze a Contract" : "Analyze a Complaint";

  function handleCitationSelect(citation: ReportCitation) {
    onCitationSelect(citation);
    setVerifyingCitation(citation);
  }

  return (
    <main className="chat-workspace">
      <header className="chat-workspace__header">
        <div>
          <button type="button" className="workflow-back-link" onClick={onBackToWorkflows}>
            &larr; {workflowLabel}
          </button>
          <p className="workflow-step-kicker">Grounded Chat Workspace</p>
          <h1>{workflow.document_name}</h1>
          <p>
            {thread.selected_task_ids.length} tasks
            {thread.represented_party_ids.length > 0 ? ` · ${thread.represented_party_ids.length} represented parties` : ""}
          </p>
        </div>
        <button className="btn-secondary" type="button" onClick={onBackToSetup}>Back to setup</button>
      </header>
      <section className="chat-workspace__body">
        <div className="chat-workspace__main">
          <div className="chat-transcript">
            {thread.messages.map((message) => (
              <ChatMessageView key={message.id} message={message} onCitationSelect={handleCitationSelect} />
            ))}
            {error && <p className="error-msg">{error}</p>}
          </div>
          <FollowUpComposer sending={sending} onSend={onSendMessage} />
        </div>
        {verifyingCitation ? (
          <aside className="chat-workspace__verification">
            <div className="source-verification__toolbar">
              <div>
                <p className="workflow-step-kicker">Source Verification</p>
                <h2>{verifyingCitation.source_doc_name}</h2>
                <p>Page {verifyingCitation.page}</p>
              </div>
              <button
                className="btn-secondary"
                type="button"
                onClick={() => setVerifyingCitation(null)}
              >
                Back to chat
              </button>
            </div>
            <SourcePreviewPanel text={workflow.full_text} citation={activeCitation ?? verifyingCitation} />
          </aside>
        ) : (
          <GroundTruthPanel
            authorities={authorities}
            loading={loadingAuthorities}
            error={authoritiesError}
          />
        )}
      </section>
    </main>
  );
}
