import type { AnalysisReport, ReportBlock, ReportCitation, ReportTable } from "../types";
import InlineCitation from "./InlineCitation";

interface Props {
  report: AnalysisReport | null;
  onCitationSelect: (citation: ReportCitation) => void;
}

export default function AnalysisReportView({ report, onCitationSelect }: Props) {
  if (!report) {
    return (
      <div className="analysis-report analysis-report--empty">
        <p>Select fixture-backed tasks and a represented party, then run analysis.</p>
      </div>
    );
  }

  const citations = new Map(report.citations.map((citation) => [citation.id, citation]));

  return (
    <article className="analysis-report">
      <header className="analysis-report__header">
        <h1>{report.title}</h1>
        <p>{report.subtitle}</p>
      </header>
      {report.sections.map((section) => (
        <section key={section.id} className="report-section">
          <h2>{section.heading}</h2>
          {section.blocks.map((block, index) => (
            <ReportBlockView
              key={`${section.id}-${index}`}
              block={block}
              citations={citations}
              onCitationSelect={onCitationSelect}
            />
          ))}
        </section>
      ))}
      {report.tables.map((table) => (
        <ReportTableView
          key={table.id}
          table={table}
          citations={citations}
          onCitationSelect={onCitationSelect}
        />
      ))}
    </article>
  );
}

function ReportBlockView({
  block,
  citations,
  onCitationSelect,
}: {
  block: ReportBlock;
  citations: Map<string, ReportCitation>;
  onCitationSelect: (citation: ReportCitation) => void;
}) {
  const citationNodes = <CitationGroup ids={block.citation_ids ?? []} citations={citations} onCitationSelect={onCitationSelect} />;

  if (block.type === "ordered_list") {
    return (
      <ol className="report-list">
        {(block.items ?? []).map((item) => <li key={item}>{item} {citationNodes}</li>)}
      </ol>
    );
  }
  if (block.type === "bulleted_list") {
    return (
      <ul className="report-list">
        {(block.items ?? []).map((item) => <li key={item}>{item} {citationNodes}</li>)}
      </ul>
    );
  }
  if (block.type === "callout") {
    return <p className="report-callout">{block.text} {citationNodes}</p>;
  }
  return <p>{block.text} {citationNodes}</p>;
}

function ReportTableView({
  table,
  citations,
  onCitationSelect,
}: {
  table: ReportTable;
  citations: Map<string, ReportCitation>;
  onCitationSelect: (citation: ReportCitation) => void;
}) {
  return (
    <section className="report-table-section">
      <h2>{table.title}</h2>
      <div className="report-table-wrap">
        <table className="report-table">
          <thead>
            <tr>{table.columns.map((column) => <th key={column}>{column}</th>)}</tr>
          </thead>
          <tbody>
            {table.rows.map((row, index) => (
              <tr key={index}>
                {table.columns.map((column) => {
                  const value = row[column];
                  return (
                    <td key={column}>
                      {Array.isArray(value)
                        ? <CitationGroup ids={value} citations={citations} onCitationSelect={onCitationSelect} />
                        : value}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CitationGroup({
  ids,
  citations,
  onCitationSelect,
}: {
  ids: string[];
  citations: Map<string, ReportCitation>;
  onCitationSelect: (citation: ReportCitation) => void;
}) {
  return (
    <span className="citation-group">
      {ids.map((id) => {
        const citation = citations.get(id);
        if (!citation) return null;
        return <InlineCitation key={id} citation={citation} onSelect={onCitationSelect} />;
      })}
    </span>
  );
}
