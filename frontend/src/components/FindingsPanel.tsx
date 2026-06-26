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
  detectedDocType: "contract" | "complaint" | null;
  selectedProfileId: string;
  onSelectProfile: (id: string) => void;
}

export default function FindingsPanel({
  findings,
  activeFinding,
  hasDocument,
  analyzing,
  analyzeError,
  onAnalyze,
  onFindingClick,
  detectedDocType,
  selectedProfileId,
  onSelectProfile,
}: Props) {
  const sorted = [...findings].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
  );

  const buttonLabel = findings.length > 0 ? "Re-analyze" : "Analyze Document";
  const verifiedCount = findings.filter((f) => f.verified).length;
  const unverifiedCount = findings.length - verifiedCount;

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
      {detectedDocType !== null && (
        <div className="doc-type-control">
          <span className="doc-type-control__label">
            Detected: <strong>{detectedDocType === "contract" ? "Contract" : "Complaint"}</strong>
          </span>
          <div className="doc-type-control__buttons">
            <button
              type="button"
              className={`doc-type-btn${selectedProfileId === "contract_risk" ? " doc-type-btn--active" : ""}`}
              aria-pressed={selectedProfileId === "contract_risk"}
              onClick={() => onSelectProfile("contract_risk")}
            >Contract</button>
            <button
              type="button"
              className={`doc-type-btn${selectedProfileId === "complaint_claims" ? " doc-type-btn--active" : ""}`}
              aria-pressed={selectedProfileId === "complaint_claims"}
              onClick={() => onSelectProfile("complaint_claims")}
            >Complaint</button>
          </div>
        </div>
      )}

      {findings.length > 0 && (
        <div className="findings-legend">
          <div className="findings-legend__row">
            <span className="findings-legend__label">Risk severity:</span>
            <span className="severity-tag severity-tag--high">HIGH</span>
            <span className="severity-tag severity-tag--medium">MEDIUM</span>
            <span className="severity-tag severity-tag--low">LOW</span>
            <span className="findings-legend__hint">
              {selectedProfileId === "complaint_claims"
                ? "strength of the legal claim"
                : "how serious the legal exposure is"}
            </span>
          </div>
          <div className="findings-legend__row">
            <span className="findings-legend__label">Grounding:</span>
            <span className="badge badge--verified">✓ Verified</span>
            <span className="findings-legend__hint">quote matched in source ({verifiedCount})</span>
            <span className="badge badge--unverified">⚠ Unverified</span>
            <span className="findings-legend__hint">could not confirm ({unverifiedCount})</span>
          </div>
        </div>
      )}

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
