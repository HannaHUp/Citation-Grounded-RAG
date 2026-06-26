"""Offline demo findings (GROUNDING_STUB=1).

Stands in for the Claude findings call when no direct Anthropic key is available.
Quotes were produced against the real fixture text; the verify guard still runs
FOR REAL, so each finding earns its ✓/⚠ by exact string match — nothing is faked.
One finding per document is a deliberate near-miss (paraphrased quote) so the
⚠ unverified path is demonstrated honestly.

# ponytail: canned demo data; delete this module and the GROUNDING_STUB branch
#           in llm_finding.run_llm once a real LLM credential is wired.
"""
from backend.models import RawFinding

_DOCX = [
    ("Payment terms expose the Client to interest accrual on late undisputed invoices at 1.5% per month (~18% annualized).",
     "medium", "Late payments shall accrue interest at 1.5% per month."),
    ("The mutual liability cap excludes indirect, incidental, and consequential damages, sharply limiting recoverable damages.",
     "high", "In no event shall either party be liable for any indirect, incidental, or consequential damages arising out of this Agreement."),
    ("Confidentiality obligations survive only five years post-termination, which may be inadequate for long-lived trade secrets.",
     "medium", "the confidentiality of the other party's Proprietary Information for a period of five (5) years following termination."),
    ("Either party may terminate on 90 days written notice, creating service-continuity risk for the relying party.",
     "medium", "Either party may terminate this Agreement upon ninety (90) days written notice."),
    # Deliberate near-miss: source says "30 (thirty) business days", not "calendar days" → ⚠ unverified.
    ("Undisputed invoices are due within 30 calendar days of receipt, tightening the Client's cash-flow obligations.",
     "low", "shall pay all undisputed invoices within 30 (thirty) calendar days of receipt"),
]

_PDF = [
    ("Musk pleads breach of contract premised on OpenAI's abandonment of its founding non-profit, public-benefit mission.",
     "high", "OpenAI, Inc. is a registered non-profit organization incorporated under the laws of"),
    ("The complaint asserts a breach of fiduciary duty claim against the individual defendants and OpenAI entities.",
     "high", "BREACH OF FIDUCIARY"),
    ("Jurisdiction and venue rest on the County of San Francisco, where most defendants reside or do business.",
     "medium", "the County of San Francisco, State of California."),
    ("Multiple OpenAI entities share a principal place of business at 1960 Bryant Street, relevant to alter-ego and venue theories.",
     "low", "principal place of business at 1960 Bryant Street, San"),
    # Deliberate near-miss: source says "Attorneys for Plaintiff Elon Musk" (no commas) → ⚠ unverified.
    ("Elon Musk is the named plaintiff, represented by Irell & Manella LLP in this action.",
     "medium", "Attorneys for Plaintiff, Elon Musk,"),
]


def _chunk_id_for(quote: str, chunks: list) -> str:
    """Assign each finding to the real chunk that contains its quote (D-06).

    The model would normally cite the chunk it grounded in; the stub recovers
    the same thing by locating the quote. Near-miss quotes (not in any chunk)
    fall back to the first chunk id — they then fail the verify guard on the
    exact-match step, which is the ⚠ path we want to demonstrate.
    """
    for c in chunks:
        if quote and quote in c.text:
            return c.chunk_id
    return chunks[0].chunk_id if chunks else "doc:0"


def _to_findings(rows, chunks):
    return [
        RawFinding(finding=f, severity=s, source_chunk_id=_chunk_id_for(q, chunks), quote=q)
        for (f, s, q) in rows
    ]


def findings_for(full_text: str, chunks: list) -> list:
    """Pick the demo finding set by sniffing which fixture this is."""
    rows = _DOCX if "MUTUAL SERVICES AGREEMENT" in full_text else _PDF
    return _to_findings(rows, chunks)
