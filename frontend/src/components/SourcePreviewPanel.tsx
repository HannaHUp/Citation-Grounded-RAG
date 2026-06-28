import type { ReportCitation } from "../types";
import DocViewer from "./DocViewer";

interface Props {
  text: string;
  citation: ReportCitation | null;
}

export default function SourcePreviewPanel({ text, citation }: Props) {
  const highlight =
    citation?.abs_start != null && citation.abs_end != null
      ? { start: citation.abs_start, end: citation.abs_end }
      : null;

  return (
    <section className="source-preview">
      <div className="source-preview__header">
        <h2>Source Preview</h2>
        {citation && <span>{citation.source_doc_name} · p. {citation.page}</span>}
      </div>
      <DocViewer text={text} highlight={highlight} />
    </section>
  );
}
