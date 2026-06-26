import type { VerifiedFinding } from "../types";
import FindingCard from "./FindingCard";

const SEVERITY_ORDER: Record<VerifiedFinding["severity"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

interface Props {
  findings: VerifiedFinding[];
  activeFinding: VerifiedFinding | null;
  hasDocument: boolean;
  analyzing: boolean;
  analyzeError: string | null;
  onAnalyze: () => void;
  onFindingClick: (f: VerifiedFinding) => void;
}

export default function FindingsPanel({
  findings,
  activeFinding,
  hasDocument,
  analyzing,
  analyzeError,
  onAnalyze,
  onFindingClick,
}: Props) {
  const sorted = [...findings].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
  );

  const buttonLabel = findings.length > 0 ? "Re-analyze" : "Analyze Document";

  return (
    <>
      <div className="findings-header">
        <span>Findings</span>
        {hasDocument && (
          <button className="btn-primary" onClick={onAnalyze} disabled={analyzing}>
            {analyzing ? "Analyzing…" : buttonLabel}
          </button>
        )}
      </div>

      <div className="findings-list">
        {analyzeError && <p className="error-msg">{analyzeError}</p>}

        {!hasDocument && (
          <p className="findings-empty">Upload a document to see findings.</p>
        )}

        {hasDocument && !analyzing && findings.length === 0 && !analyzeError && (
          <p className="findings-empty">No findings returned for this document.</p>
        )}

        {sorted.map((f, i) => (
          <FindingCard
            key={i}
            finding={f}
            isActive={f === activeFinding}
            onClick={onFindingClick}
          />
        ))}
      </div>
    </>
  );
}
