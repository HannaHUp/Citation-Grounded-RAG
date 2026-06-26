interface Props {
  severity: "high" | "medium" | "low";
}

const LABELS: Record<Props["severity"], string> = {
  high: "HIGH",
  medium: "MEDIUM",
  low: "LOW",
};

export default function SeverityTag({ severity }: Props) {
  return (
    <span className={`severity-tag severity-tag--${severity}`}>
      {LABELS[severity]}
    </span>
  );
}
