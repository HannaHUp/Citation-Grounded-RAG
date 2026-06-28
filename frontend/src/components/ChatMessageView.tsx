import type { ChatMessage, ReportCitation } from "../types";
import AnalysisReportView from "./AnalysisReportView";
import InlineCitation from "./InlineCitation";

interface Props {
  message: ChatMessage;
  onCitationSelect: (citation: ReportCitation) => void;
}

export default function ChatMessageView({ message, onCitationSelect }: Props) {
  return (
    <article className={`chat-message chat-message--${message.role}`}>
      <div className="chat-message__meta">{message.role === "assistant" ? "Assistant" : "You"}</div>
      {message.report ? (
        <AnalysisReportView report={message.report} onCitationSelect={onCitationSelect} />
      ) : (
        <p>{message.content}</p>
      )}
      {!message.report && message.citations.length > 0 && (
        <span className="citation-group">
          {message.citations.map((citation) => (
            <InlineCitation key={citation.id} citation={citation} onSelect={onCitationSelect} />
          ))}
        </span>
      )}
    </article>
  );
}
