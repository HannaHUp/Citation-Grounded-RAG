import type { VerifiedFinding } from "../types";
import SeverityTag from "./SeverityTag";
import VerifiedBadge from "./VerifiedBadge";

interface Props {
  finding: VerifiedFinding;
  isActive: boolean;
  onClick: (f: VerifiedFinding) => void;
}

export default function FindingCard({ finding, isActive, onClick }: Props) {
  const clickable = finding.verified && finding.abs_start != null;

  const classes = [
    "finding-card",
    clickable ? "finding-card--verified" : "",
    isActive ? "finding-card--active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={classes}
      onClick={() => {
        if (clickable) onClick(finding);
      }}
    >
      <SeverityTag severity={finding.severity} />
      <p className="finding-card__statement">{finding.finding}</p>
      {finding.quote && (
        <blockquote className="finding-card__quote">"{finding.quote}"</blockquote>
      )}
      <div className="finding-card__footer">
        <VerifiedBadge verified={finding.verified} />
      </div>
    </div>
  );
}
