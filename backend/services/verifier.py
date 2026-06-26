from dataclasses import asdict

from backend.models import Chunk, RawFinding, VerifiedFinding


def verify(finding: RawFinding, full_text: str, chunks_by_id: dict[str, Chunk]) -> VerifiedFinding:
    # ponytail: exact match only; add fuzzy normalize when measured ⚠ rate > ~15% (v2, VQ-01)
    base = asdict(finding)
    unverified = VerifiedFinding(**base, verified=False, abs_start=None, abs_end=None)

    if not finding.quote:                                   # find("") == 0 trap (Pitfall 4)
        return unverified

    chunk = chunks_by_id.get(finding.source_chunk_id)
    if chunk is None:                                       # fabricated chunk id (D-06)
        return unverified

    # D-06: search the cited chunk FIRST so a quote that appears multiple times in the
    # document resolves to the clause the model actually grounded in — not the first
    # whole-document occurrence (CR-01). Offsets are absolute via chunk.start_offset.
    local = chunk.text.find(finding.quote)
    if local != -1:
        abs_start = chunk.start_offset + local
        return VerifiedFinding(**base, verified=True, abs_start=abs_start,
                               abs_end=abs_start + len(finding.quote))

    # D-06 fallback: quote not in the cited chunk — try the full document. Only reached
    # when the model mis-attributed the chunk_id; the quote is still verifiably real.
    span = full_text.find(finding.quote)
    if span != -1:
        return VerifiedFinding(**base, verified=True, abs_start=span,
                               abs_end=span + len(finding.quote))

    return unverified


def verify_all(raw_findings: list, full_text: str, chunks_by_id: dict[str, Chunk]) -> list:
    return [verify(f, full_text, chunks_by_id) for f in raw_findings]
