"""
Chunker invariant tests (D-01).
Uses a plain multi-paragraph string — no fixture needed.
"""
from backend.services.chunker import chunk_text


SAMPLE_TEXT = "\n".join([
    "First paragraph with some content here.",
    "Second paragraph that goes on a bit longer.",
    "Third paragraph containing more text for testing purposes.",
    "Fourth paragraph to ensure we have enough content.",
    "Fifth paragraph for good measure in the test suite.",
    "Sixth paragraph to push us over the chunk boundary.",
    "Seventh paragraph with even more words to ensure multiple chunks.",
    "Eighth paragraph so that chunk_text definitely produces more than one chunk.",
])


def test_chunk_invariant():
    """D-01: every chunk satisfies chunk.text == full_text[start_offset:end_offset]."""
    chunks = chunk_text("doc_test", SAMPLE_TEXT, max_chars=100)
    assert len(chunks) > 0, "expected at least one chunk"
    for chunk in chunks:
        assert chunk.text == SAMPLE_TEXT[chunk.start_offset:chunk.end_offset], (
            f"Offset invariant violated at {chunk.chunk_id}: "
            f"chunk.text={chunk.text!r}, "
            f"full_text[{chunk.start_offset}:{chunk.end_offset}]="
            f"{SAMPLE_TEXT[chunk.start_offset:chunk.end_offset]!r}"
        )


def test_chunks_cover_text():
    """Chunks are contiguous and cover the entire full_text."""
    chunks = chunk_text("doc_cov", SAMPLE_TEXT, max_chars=100)
    assert chunks[0].start_offset == 0, "first chunk must start at 0"
    assert chunks[-1].end_offset == len(SAMPLE_TEXT), (
        f"last chunk end_offset {chunks[-1].end_offset} != len(full_text) {len(SAMPLE_TEXT)}"
    )
    # contiguous: each chunk starts where the previous ended
    for prev, curr in zip(chunks, chunks[1:]):
        assert curr.start_offset == prev.end_offset, (
            f"gap between chunks: {prev.chunk_id} ends at {prev.end_offset}, "
            f"{curr.chunk_id} starts at {curr.start_offset}"
        )
