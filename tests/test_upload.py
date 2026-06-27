from pathlib import Path

from fastapi.testclient import TestClient

from backend.models import Chunk, DocStore, RawFinding
from backend.main import app
from backend.store import doc_store


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _store_doc(doc_id="doc-perspective"):
    full_text = "Plaintiff alleges the defendants breached fiduciary duties."
    doc_store[doc_id] = DocStore(
        doc_id=doc_id,
        full_text=full_text,
        chunks=[
            Chunk(
                chunk_id=f"{doc_id}:0",
                text=full_text,
                start_offset=0,
                end_offset=len(full_text),
            )
        ],
    )
    return doc_id


def test_upload_fixture_pdf_returns_document_response():
    client = TestClient(app)
    content = (FIXTURE_DIR / "sample_contract.pdf").read_bytes()

    response = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", content, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["doc_id"]
    assert "Superior Court of California" in body["full_text"]
    assert body["detected_doc_type"] in {"contract", "complaint"}
    assert body["profile_id"] in {"contract_risk", "complaint_claims"}


def test_upload_stores_page_spans_and_analyze_returns_source_page(monkeypatch):
    client = TestClient(app)
    doc_store.clear()
    content = (FIXTURE_DIR / "sample_contract.pdf").read_bytes()

    upload_response = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", content, "application/pdf")},
    )
    assert upload_response.status_code == 200
    doc_id = upload_response.json()["doc_id"]
    stored = doc_store[doc_id]
    assert len(stored.page_spans) > 1
    assert stored.page_spans[0].start_offset == 0
    assert stored.page_spans[-1].end_offset == len(stored.full_text)

    def fake_run_llm(chunks, profile, full_text, perspective=None):
        verified_quote = "Superior Court of California"
        verified_chunk = next(chunk for chunk in chunks if verified_quote in chunk.text)
        return [
            RawFinding(
                finding="Verified court caption",
                severity="low",
                source_chunk_id=verified_chunk.chunk_id,
                quote=verified_quote,
            ),
            RawFinding(
                finding="Unverified invented claim",
                severity="medium",
                source_chunk_id=verified_chunk.chunk_id,
                quote="not present in this source document",
            ),
        ]

    monkeypatch.setattr("backend.main.run_llm", fake_run_llm)

    analyze_response = client.post(
        "/analyze",
        json={"doc_id": doc_id, "profile_id": "contract_risk"},
    )

    assert analyze_response.status_code == 200
    findings = analyze_response.json()["findings"]
    assert findings[0]["verified"] is True
    assert findings[0]["source_page"] == 1
    assert findings[1]["verified"] is False
    assert findings[1]["source_page"] is None


def test_analyze_accepts_perspective_and_passes_it_to_run_llm(monkeypatch):
    client = TestClient(app)
    doc_store.clear()
    doc_id = _store_doc()
    captured = {}

    def fake_run_llm(chunks, profile, full_text, perspective=None):
        captured["perspective"] = perspective
        captured["profile_id"] = profile.profile_id
        return [
            RawFinding(
                finding="Plaintiff alleges fiduciary breach",
                severity="high",
                source_chunk_id=chunks[0].chunk_id,
                quote="Plaintiff alleges the defendants breached fiduciary duties.",
            )
        ]

    monkeypatch.setattr("backend.main.run_llm", fake_run_llm)

    response = client.post(
        "/analyze",
        json={
            "doc_id": doc_id,
            "profile_id": "complaint_claims",
            "perspective": "plaintiff",
        },
    )

    assert response.status_code == 200
    assert captured == {"perspective": "plaintiff", "profile_id": "complaint_claims"}


def test_analyze_rejects_unsupported_perspective(monkeypatch):
    client = TestClient(app)
    doc_store.clear()
    doc_id = _store_doc()

    def fake_run_llm(chunks, profile, full_text, perspective=None):
        return [
            RawFinding(
                finding="Plaintiff alleges fiduciary breach",
                severity="high",
                source_chunk_id=chunks[0].chunk_id,
                quote="Plaintiff alleges the defendants breached fiduciary duties.",
            )
        ]

    monkeypatch.setattr("backend.main.run_llm", fake_run_llm)

    response = client.post(
        "/analyze",
        json={
            "doc_id": doc_id,
            "profile_id": "complaint_claims",
            "perspective": "judge",
        },
    )

    assert response.status_code == 422
