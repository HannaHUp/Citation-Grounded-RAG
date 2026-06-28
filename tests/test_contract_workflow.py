from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.store import doc_store


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DOCX = ROOT / "tests" / "fixtures" / "sample_contract.docx"


def test_demo_contract_endpoint_loads_fixture_workflow():
    client = TestClient(app)
    doc_store.clear()

    response = client.post("/demo/contract/linkedin-merger")

    assert response.status_code == 200
    body = response.json()
    assert body["doc_id"]
    assert body["document_name"] == "LinkedIn Merger Agreement.docx"
    assert body["workflow_id"] == "contract"
    assert body["detected_doc_type"] == "contract"
    assert body["fixture_available"] is True
    assert "demo fixture content" in body["detected_summary"].lower()
    assert "Microsoft" in body["full_text"]


def test_contract_workflow_returns_vincent_style_tasks():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/contract/linkedin-merger").json()["doc_id"]

    response = client.get(f"/workflow/{doc_id}")

    assert response.status_code == 200
    body = response.json()
    task_titles = {task["title"] for task in body["tasks"]}
    assert {
        "Definitions",
        "Overlaps",
        "Language",
        "Risk Mitigation",
        "Obligations",
        "Strategy",
        "Summarize",
        "Timeline",
        "Compliance Checklist",
        "Antitrust Implications",
        "Fiduciary Duties",
    } <= task_titles
    supported = {task["id"] for task in body["tasks"] if task["fixture_supported"]}
    assert {
        "risk_mitigation",
        "antitrust_implications",
        "fiduciary_duties",
        "obligations",
        "summarize",
    } <= supported


def test_contract_chat_start_returns_structured_initial_answer():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/contract/linkedin-merger").json()["doc_id"]

    response = client.post(
        "/chat/start",
        json={
            "doc_id": doc_id,
            "task_ids": ["risk_mitigation", "antitrust_implications", "fiduciary_duties"],
            "represented_party_ids": ["microsoft"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    message = body["messages"][0]
    assert message["role"] == "assistant"
    assert message["report"]["title"] == "LinkedIn Merger Agreement Contract Analysis"
    assert any(section["heading"] == "Risk Mitigation" for section in message["report"]["sections"])
    assert message["citations"]
    assert all(citation["source_doc_name"] == "LinkedIn Merger Agreement.docx" for citation in message["citations"])


def test_contract_authorities_include_antitrust_and_fiduciary_sources():
    client = TestClient(app)
    doc_store.clear()
    doc_id = client.post("/demo/contract/linkedin-merger").json()["doc_id"]

    antitrust = client.post(
        "/authorities",
        json={
            "doc_id": doc_id,
            "profile_id": "contract_antitrust",
            "finding": "Antitrust Implications",
        },
    )
    fiduciary = client.post(
        "/authorities",
        json={
            "doc_id": doc_id,
            "profile_id": "contract_risk",
            "finding": "Fiduciary Duties",
        },
    )

    assert antitrust.status_code == 200
    assert fiduciary.status_code == 200
    antitrust_titles = {item["title"] for item in antitrust.json()["authorities"]}
    fiduciary_titles = {item["title"] for item in fiduciary.json()["authorities"]}
    assert "Clayton Act Section 7" in antitrust_titles
    assert any("Standard Oil" in title for title in antitrust_titles)
    assert any("Merger Guidelines" in title for title in antitrust_titles)
    assert any("Fiduciary" in title or "Revlon" in title for title in fiduciary_titles)


def test_non_demo_contract_upload_does_not_receive_hardcoded_contract_results():
    client = TestClient(app)
    doc_store.clear()
    upload = client.post(
        "/upload",
        files={"file": ("sample_contract.docx", SAMPLE_DOCX.read_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert upload.status_code == 200

    response = client.post(
        "/analysis/report",
        json={
            "doc_id": upload.json()["doc_id"],
            "task_ids": ["risk_mitigation"],
            "represented_party_ids": ["microsoft"],
        },
    )

    assert response.status_code == 409
    assert "LLM mode" in response.json()["detail"]
