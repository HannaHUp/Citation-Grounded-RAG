from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.store import doc_store


ROOT = Path(__file__).resolve().parents[1]
DEMO_PDF = ROOT / "musk-v-altman-openai-complaint-sf.pdf"
SAMPLE_PDF = ROOT / "tests" / "fixtures" / "sample_contract.pdf"


def test_demo_complaint_endpoint_loads_fixture_workflow():
    client = TestClient(app)
    doc_store.clear()

    response = client.post("/demo/complaint/musk-altman")

    assert response.status_code == 200
    body = response.json()
    assert body["doc_id"]
    assert body["document_name"] == "musk-v-altman-openai-complaint-sf.pdf"
    assert body["workflow_id"] == "complaint"
    assert body["detected_doc_type"] == "complaint"
    assert body["fixture_available"] is True
    assert "OpenAI" in body["detected_summary"]
    assert {party["name"] for party in body["parties"]} >= {
        "Elon Musk",
        "Samuel Altman",
        "OpenAI, Inc.",
        "Microsoft",
    }
    supported = {task["id"] for task in body["tasks"] if task["fixture_supported"]}
    assert supported >= {
        "claims",
        "parties",
        "key_allegations",
        "contract_formation",
        "fiduciary_duties",
        "matters_like_this",
    }


def test_workflow_returns_demo_parties_and_tasks_for_loaded_demo():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/complaint/musk-altman").json()["doc_id"]

    response = client.get(f"/workflow/{doc_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["doc_id"] == doc_id
    assert len(body["parties"]) >= 13
    assert any(p["name"] == "Gregory Brockman" and p["type"] == "person" for p in body["parties"])
    assert any(t["id"] == "timeline" and t["enabled"] is False for t in body["tasks"])


def test_fixture_mode_rejects_structured_report_for_non_demo_upload():
    client = TestClient(app)
    doc_store.clear()
    upload = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", SAMPLE_PDF.read_bytes(), "application/pdf")},
    )
    assert upload.status_code == 200

    response = client.post(
        "/analysis/report",
        json={
            "doc_id": upload.json()["doc_id"],
            "task_ids": ["claims"],
            "represented_party_ids": ["elon-musk"],
        },
    )

    assert response.status_code == 409
    assert "LLM mode" in response.json()["detail"]


def test_demo_report_returns_structured_sections_tables_and_citations():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/complaint/musk-altman").json()["doc_id"]

    response = client.post(
        "/analysis/report",
        json={
            "doc_id": doc_id,
            "task_ids": ["claims", "contract_formation", "fiduciary_duties"],
            "represented_party_ids": ["elon-musk"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"].startswith("report-")
    assert body["primary_task_ids"] == ["claims", "contract_formation", "fiduciary_duties"]
    assert body["represented_party_ids"] == ["elon-musk"]
    assert any(section["heading"] == "(1) All Claims" for section in body["sections"])
    assert any(table["id"] == "claims-table" for table in body["tables"])
    citation_ids = {
        citation_id
        for section in body["sections"]
        for block in section["blocks"]
        for citation_id in block.get("citation_ids", [])
    }
    assert citation_ids
    assert all(citation["page"] >= 1 and citation["quote"] for citation in body["citations"])


def test_every_demo_report_citation_resolves_to_page_quote_and_offsets():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/complaint/musk-altman").json()["doc_id"]
    report = client.post(
        "/analysis/report",
        json={
            "doc_id": doc_id,
            "task_ids": ["claims", "matters_like_this"],
            "represented_party_ids": ["openai-inc"],
        },
    ).json()

    for citation in report["citations"]:
        response = client.get(f"/citation/{doc_id}/{citation['id']}")
        assert response.status_code == 200
        resolved = response.json()
        assert resolved["id"] == citation["id"]
        assert resolved["source_doc_name"] == "musk-v-altman-openai-complaint-sf.pdf"
        assert resolved["page"] >= 1
        assert resolved["quote"]
        assert isinstance(resolved["abs_start"], int)
        assert isinstance(resolved["abs_end"], int)
        assert resolved["abs_end"] > resolved["abs_start"]


def test_demo_authorities_include_similar_matters_shape():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/complaint/musk-altman").json()["doc_id"]

    response = client.post(
        "/authorities",
        json={
            "doc_id": doc_id,
            "profile_id": "complaint_claims",
            "finding": "Matters Like This",
        },
    )

    assert response.status_code == 200
    authorities = response.json()["authorities"]
    assert any(item["source_type"] == "similar_case" for item in authorities)
    assert all("metadata" in item for item in authorities)


def test_chat_start_returns_initial_assistant_report_message():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/complaint/musk-altman").json()["doc_id"]

    response = client.post(
        "/chat/start",
        json={
            "doc_id": doc_id,
            "task_ids": ["claims", "matters_like_this"],
            "represented_party_ids": ["elon-musk"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"]
    assert body["doc_id"] == doc_id
    assert body["selected_task_ids"] == ["claims", "matters_like_this"]
    assert body["represented_party_ids"] == ["elon-musk"]
    assert len(body["messages"]) == 1
    message = body["messages"][0]
    assert message["role"] == "assistant"
    assert message["report"]["title"] == "Musk v. Altman / OpenAI Complaint Analysis"
    assert message["citations"]


def test_chat_message_returns_fixture_follow_up_or_grounded_limitation():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/complaint/musk-altman").json()["doc_id"]
    thread_id = client.post(
        "/chat/start",
        json={
            "doc_id": doc_id,
            "task_ids": ["claims"],
            "represented_party_ids": ["elon-musk"],
        },
    ).json()["thread_id"]

    supported = client.post(
        "/chat/message",
        json={"thread_id": thread_id, "message": "What are the strongest claims?"},
    )
    unsupported = client.post(
        "/chat/message",
        json={"thread_id": thread_id, "message": "Predict the judge's private thoughts."},
    )

    assert supported.status_code == 200
    assert supported.json()["role"] == "assistant"
    assert "contract" in supported.json()["content"].lower()
    assert supported.json()["citations"]
    assert unsupported.status_code == 200
    assert "fixture mode" in unsupported.json()["content"].lower()


def test_chat_workspace_source_preview_is_citation_triggered_only():
    workspace_source = (ROOT / "frontend" / "src" / "components" / "ComplaintChatWorkspace.tsx").read_text()

    assert "chat-workspace__verification" in workspace_source
    assert "setVerifyingCitation" in workspace_source
    assert "<SourcePreviewPanel" in workspace_source
    assert workspace_source.index("<SourcePreviewPanel") > workspace_source.index("chat-workspace__verification")
    main_column = workspace_source[
        workspace_source.index('<div className="chat-workspace__main">') :
        workspace_source.index('<aside className="chat-workspace__verification">')
    ]
    assert "<SourcePreviewPanel" not in main_column
