import type { VerifiedFinding } from "../types";
import SeverityTag from "./SeverityTag";
import VerifiedBadge from "./VerifiedBadge";

interface Props {
  finding: VerifiedFinding;
  isActive: boolean;
  onClick: (f: VerifiedFinding) => void;
}

export default function FindingCard({ finding, isActive, onClick }: Props) {
  const classes = [
    "finding-card",
    "finding-card--clickable",
    isActive ? "finding-card--active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} onClick={() => onClick(finding)}>
      <div className="finding-card__top">
        <SeverityTag severity={finding.severity} />
        {finding.source_page != null && (
          <span className="finding-card__page">p. {finding.source_page}</span>
        )}
        <VerifiedBadge verified={finding.verified} compact />
      </div>
      <p className="finding-card__statement">{finding.finding}</p>
      {finding.quote && (
        <blockquote className="finding-card__quote">"{finding.quote}"</blockquote>
      )}
      {!finding.verified && (
        <p className="badge-explainer">
          AI flagged this but the exact source could not be confirmed — verify manually.
        </p>
      )}
    </div>
  );
}
