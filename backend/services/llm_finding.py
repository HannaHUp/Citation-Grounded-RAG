import anthropic

from backend.models import AnalysisProfile, Chunk, RawFinding


def _get_client():
    # ponytail: module-level factory so tests can monkeypatch _get_client
    return anthropic.Anthropic()


def run_llm(chunks: list, profile: AnalysisProfile, full_text: str) -> list:
    """Profile-agnostic forced tool-call findings runner (ENGINE-01, ENGINE-04, D-04, D-16).

    Sends chunk_id + text only — no start_offset/end_offset in the LLM payload (D-02/ENGINE-02).

    # ponytail: one call with all chunk texts concatenated; per-chunk loop is the upgrade path
    #           when a fixture exceeds ~40k tokens (Pitfall 6)
    """
    client = _get_client()

    # Build prompt: chunk_id + text only (never offsets — D-02)
    chunk_lines = "\n\n".join(
        f"[{chunk.chunk_id}]\n{chunk.text}" for chunk in chunks
    )
    user_message = f"Analyze the following contract text:\n\n{chunk_lines}"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",   # D-16
        max_tokens=4096,
        tools=[{
            "name": "extract_findings",
            "description": profile.tool_description,
            "input_schema": profile.output_schema,
        }],
        tool_choice={"type": "tool", "name": "extract_findings"},
        messages=[{"role": "user", "content": user_message}],
        system=profile.system_prompt,
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")
    return [
        RawFinding(
            finding=f["finding"],
            severity=f["severity"],
            source_chunk_id=f["source_chunk_id"],
            quote=f["quote"],
        )
        for f in tool_block.input["findings"]
    ]
