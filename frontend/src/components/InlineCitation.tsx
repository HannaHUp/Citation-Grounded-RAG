import type { ReportCitation } from "../types";

interface Props {
  citation: ReportCitation;
  onSelect: (citation: ReportCitation) => void;
}

export default function InlineCitation({ citation, onSelect }: Props) {
  return (
    <button className="inline-citation" type="button" onClick={() => onSelect(citation)}>
      {citation.label}
      <span className="inline-citation__tooltip" role="tooltip">
        <strong>{citation.source_doc_name}</strong>
        <span>Page {citation.page}</span>
        <span>{citation.quote}</span>
      </span>
    </button>
  );
}
