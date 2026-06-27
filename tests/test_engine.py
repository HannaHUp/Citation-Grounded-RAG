"""
LLM engine tests — offline, using monkeypatched Anthropic client.

Tests:
- test_run_llm_sends_no_offsets: message payload must not contain start_offset/end_offset
- test_run_llm_prompt_says_document_text: generic prompt must not say contract text
- test_run_llm_adds_perspective_context: plaintiff/defendant/neutral context reaches prompt
- test_engine_has_no_profile_branch: static check for zero if profile_id== branches
"""
import types
import pytest
from backend.models import Chunk, RawFinding
from backend.profiles.complaint_claims import COMPLAINT_CLAIMS
from backend.profiles.contract_risk import CONTRACT_RISK


# ---------------------------------------------------------------------------
# Fake Anthropic client
# ---------------------------------------------------------------------------

def _make_fake_client(captured_calls: list):
    """Returns a fake anthropic.Anthropic()-like object that records calls."""

    class FakeToolUseBlock:
        type = "tool_use"
        input = {"findings": [
            {
                "finding": "Unlimited liability clause",
                "severity": "high",
                "source_chunk_id": "doc:0",
                "quote": "party shall be liable",
            }
        ]}

    class FakeResponse:
        content = [FakeToolUseBlock()]

    class FakeMessages:
        def create(self, **kwargs):
            captured_calls.append(kwargs)
            return FakeResponse()

    class FakeClient:
        messages = FakeMessages()

    return FakeClient()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_run_llm_sends_no_offsets(monkeypatch):
    """The messages payload must not contain start_offset or end_offset (D-02/ENGINE-02)."""
    import backend.services.llm_finding as llm_mod

    calls = []
    monkeypatch.setattr(llm_mod, "_get_client", lambda: _make_fake_client(calls))

    chunks = [
        Chunk(chunk_id="doc:0", text="The party shall be liable for all damages.",
              start_offset=0, end_offset=42),
        Chunk(chunk_id="doc:1", text="Termination requires 30 days notice.",
              start_offset=43, end_offset=79),
    ]

    from backend.services.llm_finding import run_llm
    results = run_llm(chunks, CONTRACT_RISK, "The party shall be liable for all damages.")

    assert len(calls) == 1
    call = calls[0]
    # Serialize the full call to a string and check no offset fields leaked in
    call_str = str(call)
    assert "start_offset" not in call_str, "start_offset must not appear in LLM payload"
    assert "end_offset" not in call_str, "end_offset must not appear in LLM payload"

    # Results are RawFinding instances
    assert len(results) == 1
    assert isinstance(results[0], RawFinding)


def test_run_llm_prompt_says_document_text(monkeypatch):
    """The generic prompt should describe the uploaded source as document text."""
    import backend.services.llm_finding as llm_mod

    calls = []
    monkeypatch.setattr(llm_mod, "_get_client", lambda: _make_fake_client(calls))

    chunks = [
        Chunk(
            chunk_id="doc:0",
            text="The party shall be liable for all damages.",
            start_offset=0,
            end_offset=42,
        ),
    ]

    from backend.services.llm_finding import run_llm

    run_llm(chunks, CONTRACT_RISK, chunks[0].text)

    user_message = calls[0]["messages"][0]["content"]
    assert "Analyze the following document text" in user_message
    assert "Analyze the following contract text" not in user_message


@pytest.mark.parametrize(
    ("perspective", "expected_terms"),
    [
        ("plaintiff", ("plaintiff", "claims")),
        ("defendant", ("defendant", "defenses")),
        ("neutral", ("neutral", "balanced")),
    ],
)
def test_run_llm_adds_perspective_context_without_offsets(
    monkeypatch, perspective, expected_terms
):
    """Perspective framing must reach the user message while offsets stay out."""
    import backend.services.llm_finding as llm_mod

    calls = []
    monkeypatch.setattr(llm_mod, "_get_client", lambda: _make_fake_client(calls))

    chunks = [
        Chunk(
            chunk_id="doc:0",
            text="Plaintiff alleges the defendants breached fiduciary duties.",
            start_offset=0,
            end_offset=61,
        ),
    ]

    from backend.services.llm_finding import run_llm

    run_llm(chunks, COMPLAINT_CLAIMS, chunks[0].text, perspective=perspective)

    call = calls[0]
    user_message = call["messages"][0]["content"]
    lowered = user_message.lower()
    analyze_index = lowered.index("analyze the following document text")
    for term in expected_terms:
        assert term in lowered[:analyze_index]
    assert "start_offset" not in str(call)
    assert "end_offset" not in str(call)


def test_engine_has_no_profile_branch():
    """Static check: llm_finding.py must contain zero if profile_id== branches (ENGINE-04)."""
    import re
    import os

    path = os.path.join(
        os.path.dirname(__file__), "..", "backend", "services", "llm_finding.py"
    )
    with open(path) as f:
        src = f.read()

    matches = re.findall(r"if\s+(profile\.)?profile_id\s*==", src)
    assert matches == [], (
        f"Found {len(matches)} profile_id branch(es) in llm_finding.py — ENGINE-04 violated: {matches}"
    )
