from dataclasses import asdict

from backend.models import RawFinding, VerifiedFinding


def verify(finding: RawFinding, full_text: str, known_chunk_ids: set) -> VerifiedFinding:
    # ponytail: exact match only; add fuzzy normalize when measured ⚠ rate > ~15% (v2, VQ-01)
    base = asdict(finding)

    if not finding.quote:                              # find("") == 0 trap (Pitfall 4)
        return VerifiedFinding(**base, verified=False, abs_start=None, abs_end=None)

    if finding.source_chunk_id not in known_chunk_ids:  # fabricated chunk id (D-06)
        return VerifiedFinding(**base, verified=False, abs_start=None, abs_end=None)

    span = full_text.find(finding.quote)
    return VerifiedFinding(
        **base,
        verified=span != -1,
        abs_start=span if span != -1 else None,
        abs_end=(span + len(finding.quote)) if span != -1 else None,
    )


def verify_all(raw_findings: list, full_text: str, known_chunk_ids: set) -> list:
    return [verify(f, full_text, known_chunk_ids) for f in raw_findings]
