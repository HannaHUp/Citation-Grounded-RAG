"""
classify_doc_type tests — offline (monkeypatched Anthropic client).

Tests:
- test_stub_complaint: GROUNDING_STUB=1 + "plaintiff" prefix → "complaint_claims", no API call
- test_stub_contract: GROUNDING_STUB=1 + contract prefix → "contract_risk", no API call
- test_live_complaint: live path, fake tool_use block → "complaint_claims", verify call params
- test_profile_registry: complaint_claims profile registered and reuses FINDINGS_SCHEMA
"""
import types
import pytest
from backend.models import FINDINGS_SCHEMA


# ---------------------------------------------------------------------------
# Fake Anthropic client (mirroring test_engine.py _make_fake_client)
# ---------------------------------------------------------------------------

def _make_classify_client(captured_calls: list, doc_type: str = "complaint"):
    """Returns a fake client that returns a classify_document tool_use block."""

    class FakeToolUseBlock:
        type = "tool_use"
        input = {"doc_type": doc_type}

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
# GROUNDING_STUB tests (no API call)
# ---------------------------------------------------------------------------

def test_stub_complaint(monkeypatch):
    """GROUNDING_STUB=1 + 'plaintiff' in prefix → 'complaint_claims', no client call."""
    import backend.services.llm_finding as llm_mod

    monkeypatch.setenv("GROUNDING_STUB", "1")
    # Track whether _get_client is called — it must NOT be
    client_calls = []
    monkeypatch.setattr(llm_mod, "_get_client", lambda: (_ for _ in ()).throw(
        AssertionError("_get_client must not be called on stub path")
    ))

    from backend.services.llm_finding import classify_doc_type
    result = classify_doc_type("In the matter of plaintiff Elon Musk vs. OpenAI")
    assert result == "complaint_claims"


def test_stub_contract(monkeypatch):
    """GROUNDING_STUB=1 + contract prefix (no 'plaintiff') → 'contract_risk', no client call."""
    import backend.services.llm_finding as llm_mod

    monkeypatch.setenv("GROUNDING_STUB", "1")
    monkeypatch.setattr(llm_mod, "_get_client", lambda: (_ for _ in ()).throw(
        AssertionError("_get_client must not be called on stub path")
    ))

    from backend.services.llm_finding import classify_doc_type
    result = classify_doc_type("MUTUAL SERVICES AGREEMENT between Microsoft and LinkedIn")
    assert result == "contract_risk"


# ---------------------------------------------------------------------------
# Live path test (monkeypatched client)
# ---------------------------------------------------------------------------

def test_live_complaint(monkeypatch):
    """Live path: fake tool_use block with doc_type='complaint' → 'complaint_claims'.

    Verifies:
    - exactly one messages.create call
    - max_tokens=64
    - tool name is 'classify_document'
    """
    import backend.services.llm_finding as llm_mod

    # Ensure stub is OFF
    monkeypatch.delenv("GROUNDING_STUB", raising=False)

    calls = []
    monkeypatch.setattr(llm_mod, "_get_client", lambda: _make_classify_client(calls, "complaint"))

    from backend.services.llm_finding import classify_doc_type
    result = classify_doc_type("SUPERIOR COURT - plaintiff alleges defendant violated contract")

    assert result == "complaint_claims"
    assert len(calls) == 1
    call = calls[0]
    assert call["max_tokens"] == 64
    assert call["tools"][0]["name"] == "classify_document"
    assert call["tool_choice"] == {"type": "tool", "name": "classify_document"}
    assert call["model"] == "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# Profile registry test
# ---------------------------------------------------------------------------

def test_profile_registry():
    """complaint_claims registered; output_schema is the same FINDINGS_SCHEMA object (D-04)."""
    from backend.profiles import get_profile

    p = get_profile("complaint_claims")
    assert p.profile_id == "complaint_claims"
    assert p.output_schema is FINDINGS_SCHEMA

    # contract_risk still resolves — registry not broken
    cr = get_profile("contract_risk")
    assert cr.profile_id == "contract_risk"
