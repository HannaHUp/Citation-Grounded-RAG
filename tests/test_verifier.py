"""
Verifier unit tests — RED phase written before verifier.py exists.
Five cases per plan 01-02 behavior spec.
"""
import pytest
from backend.models import RawFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_TEXT = "The party shall indemnify the other party for all losses."
KNOWN_IDS = {"doc:0", "doc:1"}

def _raw(quote, chunk_id="doc:0"):
    return RawFinding(
        finding="Test finding",
        severity="medium",
        source_chunk_id=chunk_id,
        quote=quote,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_exact_match():
    """Quote present in full_text → verified=True with correct offsets."""
    from backend.services.verifier import verify

    quote = "indemnify the other party"
    result = verify(_raw(quote), FULL_TEXT, KNOWN_IDS)

    assert result.verified is True
    assert result.abs_start == FULL_TEXT.index(quote)
    assert result.abs_end == FULL_TEXT.index(quote) + len(quote)
    assert FULL_TEXT[result.abs_start:result.abs_end] == quote


def test_no_match():
    """Quote absent from full_text → verified=False, offsets None."""
    from backend.services.verifier import verify

    result = verify(_raw("this text is not in the document"), FULL_TEXT, KNOWN_IDS)

    assert result.verified is False
    assert result.abs_start is None
    assert result.abs_end is None


def test_empty_quote():
    """Empty quote → verified=False (guards full_text.find('') == 0 trap)."""
    from backend.services.verifier import verify

    result = verify(_raw(""), FULL_TEXT, KNOWN_IDS)

    assert result.verified is False
    assert result.abs_start is None


def test_fabricated_chunk_id():
    """source_chunk_id not in known_chunk_ids → verified=False even if quote is present."""
    from backend.services.verifier import verify

    # The quote IS in the text but the chunk_id is fabricated
    quote = "indemnify the other party"
    assert quote in FULL_TEXT  # precondition: quote would match if chunk_id were valid

    result = verify(_raw(quote, chunk_id="fabricated:999"), FULL_TEXT, KNOWN_IDS)

    assert result.verified is False
    assert result.abs_start is None


def test_verify_all_preserves_count():
    """verify_all returns one VerifiedFinding per input RawFinding — no filtering."""
    from backend.services.verifier import verify_all

    raws = [
        _raw("indemnify the other party"),           # will match → verified=True
        _raw("this text is not in the document"),    # will not match → verified=False
        _raw(""),                                     # empty quote → verified=False
    ]
    results = verify_all(raws, FULL_TEXT, KNOWN_IDS)

    assert len(results) == 3
    assert results[0].verified is True
    assert results[1].verified is False
    assert results[2].verified is False
