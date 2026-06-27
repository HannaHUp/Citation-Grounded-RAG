import type { LegalAuthority, VerifiedFinding } from "../types";
import DocViewer from "./DocViewer";
import FindingCard from "./FindingCard";
import LegalAuthoritiesPanel from "./LegalAuthoritiesPanel";

const SEVERITY_ORDER: Record<VerifiedFinding["severity"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

interface Props {
  fullText: string;
  findings: VerifiedFinding[];
  authorities: LegalAuthority[];
  activeFinding: VerifiedFinding | null;
  highlight: { start: number; end: number } | null;
  loadingAuthorities: boolean;
  authoritiesError: string | null;
  onFindingClick: (f: VerifiedFinding) => void;
}

export default function WorkflowOutput({
  fullText,
  findings,
  authorities,
  activeFinding,
  highlight,
  loadingAuthorities,
  authoritiesError,
  onFindingClick,
}: Props) {
  const sorted = [...findings].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
  );
  const verifiedCount = findings.filter((f) => f.verified).length;
  const unverifiedCount = findings.length - verifiedCount;

  return (
    <main className="workflow-output">
      {/* left: document-grounded findings + source preview */}
      <section className="workflow-output__left">
        <div className="workflow-output__pane-title">
          Document-grounded extraction
          <span className="workflow-output__src">
            {findings.length} finding{findings.length === 1 ? "" : "s"}
          </span>
        </div>

        {findings.length > 0 && (
          <div className="workflow-output__legend">
            <span><strong>Severity</strong> = legal exposure</span>
            <span><span className="badge badge--verified">✓</span> grounded in source ({verifiedCount})</span>
            <span><span className="badge badge--unverified">⚠</span> unconfirmed ({unverifiedCount})</span>
            <span className="workflow-output__legend-hint">· click a finding to verify the source &amp; load authorities</span>
          </div>
        )}

        <div className="workflow-output__findings">
          {findings.length === 0 && (
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

        <div className="workflow-output__source">
          <div className="workflow-output__source-title">Source preview</div>
          <DocViewer text={fullText} highlight={highlight} />
        </div>
      </section>

      {/* right: legal authorities for the active finding */}
      <section className="workflow-output__right">
        <div className="workflow-output__pane-title">Legal Authorities</div>
        <div className="workflow-output__authorities">
          {loadingAuthorities && (
            <p className="findings-empty">Finding legal authorities…</p>
          )}
          {!loadingAuthorities && authoritiesError && (
            <p className="error-msg">{authoritiesError}</p>
          )}
          {!loadingAuthorities && !authoritiesError && activeFinding === null && (
            <p className="findings-empty">Select a finding to look up legal authorities.</p>
          )}
          {!loadingAuthorities && !authoritiesError && activeFinding !== null && (
            <LegalAuthoritiesPanel authorities={authorities} />
          )}
        </div>
      </section>
    </main>
  );
}
