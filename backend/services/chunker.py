from backend.models import Chunk

# ponytail: paragraph-window split; switch to sentence-boundary only if quotes
# straddle chunk edges at a high rate


def chunk_text(doc_id: str, full_text: str, max_chars: int = 2000) -> list[Chunk]:
    """Split full_text into Chunks with hard offset assert (D-01).

    Prefers splitting at the last newline within the window; falls back to
    the hard window boundary if no newline exists.
    """
    chunks: list[Chunk] = []
    i = 0
    idx = 0
    while i < len(full_text):
        end = min(i + max_chars, len(full_text))
        if end < len(full_text):
            split = full_text.rfind("\n", i, end)
            if split > i:
                end = split + 1  # include the newline in this chunk
        chunk = Chunk(
            chunk_id=f"{doc_id}:{idx}",
            text=full_text[i:end],
            start_offset=i,
            end_offset=end,
        )
        # D-01 invariant — explicit raise, not bare assert, so it survives `python -O`.
        if chunk.text != full_text[chunk.start_offset:chunk.end_offset]:
            raise ValueError(f"Offset invariant violated at chunk {chunk.chunk_id}")
        chunks.append(chunk)
        i = end
        idx += 1
    return chunks
