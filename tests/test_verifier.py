"""
Verifier unit tests — RED phase written before verifier.py exists.
Cases per plan 01-02 behavior spec, plus the CR-01 duplicate-quote regression.
"""
import pytest
from backend.models import Chunk, RawFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_TEXT = "The party shall indemnify the other party for all losses."

# Two chunks spanning FULL_TEXT, offsets exact: full_text[start:end] == chunk.text
CHUNKS_BY_ID = {
    "doc:0": Chunk(chunk_id="doc:0", text=FULL_TEXT[:29], start_offset=0, end_offset=29),
    "doc:1": Chunk(chunk_id="doc:1", text=FULL_TEXT[29:], start_offset=29, end_offset=len(FULL_TEXT)),
}


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
    """Quote present in the cited chunk → verified=True with correct absolute offsets."""
    from backend.services.verifier import verify

    quote = "The party shall"  # lives in doc:0 at offset 0
    result = verify(_raw(quote, chunk_id="doc:0"), FULL_TEXT, CHUNKS_BY_ID)

    assert result.verified is True
    assert result.abs_start == FULL_TEXT.index(quote)
    assert result.abs_end == FULL_TEXT.index(quote) + len(quote)
    assert FULL_TEXT[result.abs_start:result.abs_end] == quote


def test_no_match():
    """Quote absent from full_text → verified=False, offsets None."""
    from backend.services.verifier import verify

    result = verify(_raw("this text is not in the document"), FULL_TEXT, CHUNKS_BY_ID)

    assert result.verified is False
    assert result.abs_start is None
    assert result.abs_end is None


def test_empty_quote():
    """Empty quote → verified=False (guards full_text.find('') == 0 trap)."""
    from backend.services.verifier import verify

    result = verify(_raw(""), FULL_TEXT, CHUNKS_BY_ID)

    assert result.verified is False
    assert result.abs_start is None


def test_fabricated_chunk_id():
    """source_chunk_id not in chunks_by_id → verified=False even if quote is present."""
    from backend.services.verifier import verify

    quote = "indemnify the other party"
    assert quote in FULL_TEXT  # precondition: quote would match if chunk_id were valid

    result = verify(_raw(quote, chunk_id="fabricated:999"), FULL_TEXT, CHUNKS_BY_ID)

    assert result.verified is False
    assert result.abs_start is None


def test_duplicate_quote_resolves_to_cited_chunk():
    """CR-01 regression: a quote appearing twice resolves to the CITED chunk's
    occurrence, not the first whole-document occurrence (D-06)."""
    from backend.services.verifier import verify

    # "the party" appears at offset 4 (chunk A) and offset 23 (chunk B).
    full = "the party agrees. Later the party agrees again."
    a_end = 17  # "the party agrees."
    chunks = {
        "c:a": Chunk(chunk_id="c:a", text=full[:a_end], start_offset=0, end_offset=a_end),
        "c:b": Chunk(chunk_id="c:b", text=full[a_end:], start_offset=a_end, end_offset=len(full)),
    }
    quote = "the party"
    first = full.find(quote)               # 0  — the WRONG answer the old code gave
    second = full.find(quote, a_end)       # occurrence inside chunk c:b

    result = verify(_raw(quote, chunk_id="c:b"), full, chunks)

    assert result.verified is True
    assert result.abs_start == second
    assert result.abs_start != first
    assert full[result.abs_start:result.abs_end] == quote


def test_verify_all_preserves_count():
    """verify_all returns one VerifiedFinding per input RawFinding — no filtering."""
    from backend.services.verifier import verify_all

    raws = [
        _raw("The party shall", chunk_id="doc:0"),     # matches in chunk → verified=True
        _raw("this text is not in the document"),      # no match → verified=False
        _raw(""),                                       # empty quote → verified=False
    ]
    results = verify_all(raws, FULL_TEXT, CHUNKS_BY_ID)

    assert len(results) == 3
    assert results[0].verified is True
    assert results[1].verified is False
    assert results[2].verified is False
