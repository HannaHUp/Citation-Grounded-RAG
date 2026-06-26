interface Props {
  verified: boolean;
  compact?: boolean;
}

export default function VerifiedBadge({ verified, compact = false }: Props) {
  if (verified) {
    return <span className="badge badge--verified">✓ Verified</span>;
  }
  return (
    <div>
      <span className="badge badge--unverified">⚠ Unverified</span>
      {!compact && (
        <p className="badge-explainer">
          AI flagged this but the exact source could not be confirmed — verify manually.
        </p>
      )}
    </div>
  );
}
