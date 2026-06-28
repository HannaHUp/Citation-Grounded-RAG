import os
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

from fastapi import HTTPException

from backend.fixtures import linkedin_merger_contract as contract_fixture
from backend.fixtures import musk_v_altman_complaint as musk_fixture
from backend.models import AnalysisReport, ChatMessage, ComplaintWorkflowResponse, DocStore, ReportCitation
from backend.services.chunker import chunk_text
from backend.services.extraction import extract_pdf_document
from backend.store import doc_store


class DocumentWorkflowProvider(Protocol):
    def load_demo_complaint(self) -> ComplaintWorkflowResponse: ...
    def load_demo_contract(self) -> ComplaintWorkflowResponse: ...
    def workflow_for(self, doc: DocStore) -> ComplaintWorkflowResponse: ...


class AnalysisRunner(Protocol):
    def run_report(
        self,
        doc: DocStore,
        task_ids: list[str],
        represented_party_ids: list[str],
    ) -> AnalysisReport: ...

    def answer_follow_up(self, doc: DocStore, message: str) -> ChatMessage: ...


class CitationResolver(Protocol):
    def resolve(self, doc: DocStore, citation_id: str) -> ReportCitation | None: ...


class AuthorityRetriever(Protocol):
    def fixture_authorities(self, doc: DocStore, finding: str | None = None) -> list[dict] | None: ...


class FixtureComplaintProvider(
    DocumentWorkflowProvider,
    AnalysisRunner,
    CitationResolver,
    AuthorityRetriever,
):
    def __init__(self, demo_pdf_path: Path | None = None) -> None:
        self.demo_pdf_path = demo_pdf_path or Path(__file__).resolve().parents[2] / musk_fixture.DOCUMENT_NAME

    def load_demo_complaint(self) -> ComplaintWorkflowResponse:
        if not self.demo_pdf_path.exists():
            raise HTTPException(
                status_code=503,
                detail=f"Demo complaint PDF is not available at {self.demo_pdf_path}",
            )
        doc_id = f"demo-{musk_fixture.FIXTURE_ID}"
        extracted = extract_pdf_document(self.demo_pdf_path.read_bytes())
        doc_store[doc_id] = DocStore(
            doc_id=doc_id,
            full_text=extracted.full_text,
            chunks=chunk_text(doc_id, extracted.full_text),
            page_spans=extracted.page_spans,
            document_name=musk_fixture.DOCUMENT_NAME,
            fixture_id=musk_fixture.FIXTURE_ID,
            detected_doc_type="complaint",
        )
        return musk_fixture.workflow_response(doc_store[doc_id])

    def load_demo_contract(self) -> ComplaintWorkflowResponse:
        doc_id = f"demo-{contract_fixture.FIXTURE_ID}"
        doc_store[doc_id] = DocStore(
            doc_id=doc_id,
            full_text=contract_fixture.DEMO_TEXT,
            chunks=chunk_text(doc_id, contract_fixture.DEMO_TEXT),
            page_spans=contract_fixture.demo_page_spans(),
            document_name=contract_fixture.DOCUMENT_NAME,
            fixture_id=contract_fixture.FIXTURE_ID,
            detected_doc_type="contract",
        )
        return contract_fixture.workflow_response(doc_store[doc_id])

    def workflow_for(self, doc: DocStore) -> ComplaintWorkflowResponse:
        if doc.fixture_id == musk_fixture.FIXTURE_ID:
            return musk_fixture.workflow_response(doc)
        if doc.fixture_id == contract_fixture.FIXTURE_ID:
            return contract_fixture.workflow_response(doc)
        if doc.detected_doc_type == "contract":
            return contract_fixture.limited_workflow_response(doc)
        return musk_fixture.limited_workflow_response(doc)

    def run_report(
        self,
        doc: DocStore,
        task_ids: list[str],
        represented_party_ids: list[str],
    ) -> AnalysisReport:
        if doc.fixture_id == contract_fixture.FIXTURE_ID:
            return contract_fixture.report_for(doc, task_ids, represented_party_ids)
        if doc.fixture_id != musk_fixture.FIXTURE_ID:
            raise HTTPException(
                status_code=409,
                detail=f"Rich Vincent-style {doc.detected_doc_type or 'document'} analysis for arbitrary documents requires LLM mode.",
            )
        return musk_fixture.report_for(doc, task_ids, represented_party_ids)

    def resolve(self, doc: DocStore, citation_id: str) -> ReportCitation | None:
        if doc.fixture_id == contract_fixture.FIXTURE_ID:
            return contract_fixture.citation_for(doc, citation_id)
        if doc.fixture_id == musk_fixture.FIXTURE_ID:
            return musk_fixture.citation_for(doc, citation_id)
        return None

    def answer_follow_up(self, doc: DocStore, message: str) -> ChatMessage:
        if doc.fixture_id == contract_fixture.FIXTURE_ID:
            return contract_fixture.follow_up_answer(doc, message)
        if doc.fixture_id != musk_fixture.FIXTURE_ID:
            raise HTTPException(
                status_code=409,
                detail=f"Rich Vincent-style {doc.detected_doc_type or 'document'} chat for arbitrary documents requires LLM mode.",
            )
        return musk_fixture.follow_up_answer(doc, message)

    def fixture_authorities(self, doc: DocStore, finding: str | None = None) -> list[dict] | None:
        if doc.fixture_id == contract_fixture.FIXTURE_ID:
            return contract_fixture.authorities(finding)
        if doc.fixture_id != musk_fixture.FIXTURE_ID:
            return None
        if finding and "matter" in finding.lower():
            return musk_fixture.authorities()
        return None


class LlmComplaintProvider(FixtureComplaintProvider):
    """Contract-compatible placeholder for future API-backed implementations."""

    def run_report(
        self,
        doc: DocStore,
        task_ids: list[str],
        represented_party_ids: list[str],
    ) -> AnalysisReport:
        raise HTTPException(
            status_code=501,
            detail="LLM workflow provider is configured but not implemented in this demo build.",
        )

    def answer_follow_up(self, doc: DocStore, message: str) -> ChatMessage:
        raise HTTPException(
            status_code=501,
            detail="LLM workflow provider is configured but not implemented in this demo build.",
        )


def get_workflow_provider() -> FixtureComplaintProvider:
    provider = os.getenv("AI_PROVIDER", "fixture").lower()
    if provider == "llm":
        return LlmComplaintProvider()
    return FixtureComplaintProvider()


def model_dump(value) -> dict:
    return asdict(value)
