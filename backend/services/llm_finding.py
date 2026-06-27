import os

import anthropic

from backend.models import AnalysisProfile, Chunk, RawFinding
from backend.services import stub_findings


def _get_client():
    # ponytail: module-level factory so tests can monkeypatch _get_client
    return anthropic.Anthropic()


def run_llm(
    chunks: list[Chunk],
    profile: AnalysisProfile,
    full_text: str,
    perspective: str | None = None,
) -> list[RawFinding]:
    """Profile-agnostic forced tool-call findings runner (ENGINE-01, ENGINE-04, D-04, D-16).

    Sends chunk_id + text only — no start_offset/end_offset in the LLM payload (D-02/ENGINE-02).

    # ponytail: one call with all chunk texts concatenated; per-chunk loop is the upgrade path
    #           when a fixture exceeds ~40k tokens (Pitfall 6)
    """
    # ponytail: offline demo path — GROUNDING_STUB=1 returns canned findings so the
    # full UI demo runs without a direct Anthropic key. The verify guard still runs
    # FOR REAL against the document, so ✓/⚠ badges are earned, not faked. Remove once
    # a real sk-ant- key (or Bedrock client) is wired. The live path below is unchanged.
    if os.environ.get("GROUNDING_STUB") == "1":
        return stub_findings.findings_for(full_text, chunks)

    client = _get_client()

    # Build prompt: chunk_id + text only (never offsets — D-02)
    chunk_lines = "\n\n".join(
        f"[{chunk.chunk_id}]\n{chunk.text}" for chunk in chunks
    )
    prompt_intro = f"Analyze the following document text:\n\n{chunk_lines}"
    context = _perspective_context(perspective)
    user_message = f"{context}\n\n{prompt_intro}" if context else prompt_intro

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


def _perspective_context(perspective: str | None) -> str:
    if perspective == "plaintiff":
        return (
            "Perspective context: Analyze from the plaintiff's perspective, "
            "emphasizing claims, supporting allegations, requested relief, and plaintiff-side risks."
        )
    if perspective == "defendant":
        return (
            "Perspective context: Analyze from the defendant's perspective, "
            "emphasizing defenses, weaknesses in the claims, exposure, and response strategy."
        )
    if perspective == "neutral":
        return (
            "Perspective context: Analyze from a neutral, balanced perspective, "
            "weighing claims and defenses without favoring either side."
        )
    return ""


_CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "doc_type": {"type": "string", "enum": ["contract", "complaint"]}
    },
    "required": ["doc_type"],
}

_DOC_TYPE_TO_PROFILE = {
    "contract": "contract_risk",
    "complaint": "complaint_claims",
}


def classify_doc_type(prefix: str) -> str:
    """Returns profile_id for the detected document type (D-01/D-02/D-03)."""
    # ponytail: stub classify — keyword heuristic, offline only (D-10)
    if os.environ.get("GROUNDING_STUB") == "1":
        return _classify_doc_type_locally(prefix)

    client = _get_client()
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=64,   # enum response only — much cheaper than findings call
            tools=[{
                "name": "classify_document",
                "description": "Classify the document as a commercial contract or a litigation complaint.",
                "input_schema": _CLASSIFY_SCHEMA,
            }],
            tool_choice={"type": "tool", "name": "classify_document"},
            messages=[{"role": "user", "content": f"Document excerpt:\n\n{prefix}"}],
            system=(
                "You are a legal document classifier. "
                "Return 'contract' for commercial agreements, NDAs, service agreements. "
                "Return 'complaint' for litigation complaints, lawsuits, pleadings, petitions."
            ),
        )
    except Exception:
        return _classify_doc_type_locally(prefix)
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return _DOC_TYPE_TO_PROFILE.get(tool_block.input["doc_type"], "contract_risk")


def _classify_doc_type_locally(prefix: str) -> str:
    text = prefix.lower()
    complaint_terms = ("plaintiff", "defendant", "complaint", "superior court", "cause of action")
    return "complaint_claims" if any(term in text for term in complaint_terms) else "contract_risk"
