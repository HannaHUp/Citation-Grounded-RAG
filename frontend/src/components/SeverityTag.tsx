interface Props {
  severity: "high" | "medium" | "low";
}

const LABELS: Record<Props["severity"], string> = {
  high: "HIGH",
  medium: "MEDIUM",
  low: "LOW",
};

// Risk severity = how serious the legal exposure is (LLM-assigned), distinct from
// the ✓/⚠ grounding badge. Tooltip spells it out on hover.
const TOOLTIPS: Record<Props["severity"], string> = {
  high: "High risk — serious legal exposure, review first",
  medium: "Medium risk — worth reviewing",
  low: "Low risk — minor or informational",
};

export default function SeverityTag({ severity }: Props) {
  return (
    <span
      className={`severity-tag severity-tag--${severity}`}
      title={TOOLTIPS[severity]}
    >
      {LABELS[severity]}
    </span>
  );
}
