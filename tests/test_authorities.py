from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Chunk, DocStore
from backend.services.authority_ingest import AuthorityRecord, write_corpus
from backend.store import doc_store


def test_retrieve_authorities_uses_local_cosine_scores(tmp_path, monkeypatch):
    from backend.services import authorities as service

    write_corpus(
        [
            AuthorityRecord(
                authority_id="merger-case",
                title="Merger Case",
                source_type="case",
                summary_seed="Merger competition summary.",
                quote_seed="substantially lessen competition in a relevant market",
                url="https://example.test/merger",
                source_text="A merger may substantially lessen competition in a relevant market.",
                metadata={},
            ),
            AuthorityRecord(
                authority_id="employment-case",
                title="Employment Case",
                source_type="case",
                summary_seed="Employment summary.",
                quote_seed="employment contract wages and benefits",
                url="https://example.test/employment",
                source_text="This authority concerns an employment contract wages and benefits dispute.",
                metadata={},
            ),
        ],
        tmp_path / "corpus.jsonl",
    )
    monkeypatch.setattr(service, "CORPUS_PATH", tmp_path / "corpus.jsonl")

    results = service.retrieve_authorities(
        document_text="The proposed acquisition may lessen competition.",
        profile_id="contract_antitrust",
        finding="The acquisition substantially lessens competition.",
        quote="substantially lessen competition",
    )

    assert [authority.authority_id for authority in results][:2] == [
        "merger-case",
        "employment-case",
    ]
    assert results[0].raw_score > results[1].raw_score
    assert results[0].relevance == round(results[0].raw_score * 100)
    assert results[0].quote in results[0].source_text
    assert results[0].verified is True


def test_authority_response_keeps_unverified_summary_visible():
    from backend.services.authorities import RetrievedAuthority, authority_response

    authority = RetrievedAuthority(
        authority_id="bad-quote",
        title="Bad Quote",
        source_type="secondary",
        summary="Summary is still visible.",
        relevance=50,
        quote="not in source",
        url="https://example.test/bad",
        source_text="The source text does not contain the requested support.",
        raw_score=0.5,
        verified=False,
    )

    payload = authority_response([authority])[0]

    assert payload["summary"] == "Summary is still visible."
    assert payload["verified"] is False
    assert payload["quote"] == "not in source"


def test_authorities_endpoint_returns_tab_ready_records_for_stored_document():
    client = TestClient(app)
    doc_store.clear()
    doc_store["doc-auth"] = DocStore(
        doc_id="doc-auth",
        full_text=(
            "The merger agreement raises antitrust concerns because it may "
            "substantially lessen competition."
        ),
        chunks=[
            Chunk(
                chunk_id="doc-auth:0",
                text="The merger agreement raises antitrust concerns because it may substantially lessen competition.",
                start_offset=0,
                end_offset=91,
            )
        ],
    )

    response = client.post(
        "/authorities",
        json={"doc_id": "doc-auth", "profile_id": "contract_antitrust"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["authorities"]
    first = payload["authorities"][0]
    assert {
        "authority_id",
        "title",
        "source_type",
        "summary",
        "relevance",
        "quote",
        "verified",
        "url",
    } <= set(first)
    assert isinstance(first["relevance"], int)
    assert 0 <= first["relevance"] <= 100
    assert isinstance(first["verified"], bool)


def test_authorities_endpoint_accepts_finding_specific_lookup():
    client = TestClient(app)
    doc_store.clear()
    doc_store["doc-finding-auth"] = DocStore(
        doc_id="doc-finding-auth",
        full_text="The acquisition may substantially lessen competition.",
        chunks=[
            Chunk(
                chunk_id="doc-finding-auth:0",
                text="The acquisition may substantially lessen competition.",
                start_offset=0,
                end_offset=53,
            )
        ],
    )

    response = client.post(
        "/authorities",
        json={
            "doc_id": "doc-finding-auth",
            "profile_id": "contract_antitrust",
            "finding": "The acquisition may substantially lessen competition.",
            "quote": "substantially lessen competition",
            "source_chunk_id": "doc-finding-auth:0",
        },
    )

    assert response.status_code == 200
    assert response.json()["authorities"]


def test_authorities_endpoint_404_for_missing_document():
    client = TestClient(app)
    doc_store.clear()

    response = client.post(
        "/authorities",
        json={"doc_id": "missing", "profile_id": "contract_antitrust"},
    )

    assert response.status_code == 404
