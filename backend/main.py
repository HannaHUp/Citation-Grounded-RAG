import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models import ChatMessage, ChatThread, DocStore
from backend.profiles import get_profile
from backend.services.authorities import authority_response, retrieve_authorities
from backend.services.chunker import chunk_text
from backend.services.extraction import extract_docx_document, extract_pdf_document
from backend.services.llm_finding import classify_doc_type, run_llm
from backend.services.verifier import verify_all
from backend.services.workflow_providers import get_workflow_provider, model_dump
from backend.store import doc_store

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
chat_threads: dict[str, ChatThread] = {}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    # Magic-byte validation — trust the bytes, not the declared type (T-01-01)
    if ext == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF")
    if ext == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="File does not appear to be a valid DOCX")

    doc_id = str(uuid.uuid4())
    extracted = extract_pdf_document(content) if ext == ".pdf" else extract_docx_document(content)
    full_text = extracted.full_text
    chunks = chunk_text(doc_id, full_text)
    doc_store[doc_id] = DocStore(
        doc_id=doc_id,
        full_text=full_text,
        chunks=chunks,
        page_spans=extracted.page_spans,
        document_name=file.filename,
    )
    profile_id = classify_doc_type(full_text[:3000])
    detected_doc_type = "complaint" if profile_id == "complaint_claims" else "contract"
    return {"doc_id": doc_id, "full_text": full_text, "detected_doc_type": detected_doc_type, "profile_id": profile_id}


@app.post("/demo/complaint/musk-altman")
async def demo_musk_altman_complaint():
    provider = get_workflow_provider()
    return model_dump(provider.load_demo_complaint())


@app.get("/workflow/{doc_id}")
async def workflow(doc_id: str):
    doc = doc_store.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    provider = get_workflow_provider()
    return model_dump(provider.workflow_for(doc))


class AnalyzeRequest(BaseModel):
    doc_id: str
    profile_id: str = "contract_risk"
    perspective: Literal["plaintiff", "defendant", "neutral"] | None = None
    # No `verified` field — client can never assert verified-ness (VERIFY-02, T-02-01)


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    doc = doc_store.get(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    profile = get_profile(req.profile_id)
    raw = run_llm(doc.chunks, profile, doc.full_text, perspective=req.perspective)
    chunks_by_id = {c.chunk_id: c for c in doc.chunks}
    verified = verify_all(raw, doc.full_text, chunks_by_id, page_spans=doc.page_spans)
    return {"findings": [asdict(f) for f in verified]}


class AuthoritiesRequest(BaseModel):
    doc_id: str
    profile_id: str = "contract_antitrust"
    finding: str | None = None
    quote: str | None = None
    source_chunk_id: str | None = None


class AnalysisReportRequest(BaseModel):
    doc_id: str
    task_ids: list[str]
    represented_party_ids: list[str]


class ChatStartRequest(BaseModel):
    doc_id: str
    task_ids: list[str]
    represented_party_ids: list[str]


class ChatMessageRequest(BaseModel):
    thread_id: str
    message: str


@app.post("/analysis/report")
async def analysis_report(req: AnalysisReportRequest):
    doc = doc_store.get(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    provider = get_workflow_provider()
    return model_dump(provider.run_report(doc, req.task_ids, req.represented_party_ids))


@app.post("/chat/start")
async def chat_start(req: ChatStartRequest):
    doc = doc_store.get(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    provider = get_workflow_provider()
    report = provider.run_report(doc, req.task_ids, req.represented_party_ids)
    thread = ChatThread(
        thread_id=f"thread-{uuid.uuid4().hex}",
        doc_id=req.doc_id,
        selected_task_ids=req.task_ids,
        represented_party_ids=req.represented_party_ids,
        messages=[
            ChatMessage(
                id=f"msg-{uuid.uuid4().hex}",
                role="assistant",
                content=report.subtitle,
                report=report,
                citations=report.citations,
                created_at=datetime.now(UTC).isoformat(),
            )
        ],
    )
    chat_threads[thread.thread_id] = thread
    return model_dump(thread)


@app.post("/chat/message")
async def chat_message(req: ChatMessageRequest):
    thread = chat_threads.get(req.thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    doc = doc_store.get(thread.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    user_message = ChatMessage(
        id=f"msg-{uuid.uuid4().hex}",
        role="user",
        content=req.message,
        report=None,
        citations=[],
        created_at=datetime.now(UTC).isoformat(),
    )
    provider = get_workflow_provider()
    assistant_message = provider.answer_follow_up(doc, req.message)
    thread.messages.extend([user_message, assistant_message])
    return model_dump(assistant_message)


@app.get("/citation/{doc_id}/{citation_id}")
async def citation(doc_id: str, citation_id: str):
    doc = doc_store.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    provider = get_workflow_provider()
    resolved = provider.resolve(doc, citation_id)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Citation not found")
    return model_dump(resolved)


@app.post("/authorities")
async def authorities(req: AuthoritiesRequest):
    doc = doc_store.get(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    provider = get_workflow_provider()
    fixture_authorities = provider.fixture_authorities(doc, req.finding)
    if fixture_authorities is not None:
        return {"authorities": fixture_authorities}
    authorities = retrieve_authorities(
        doc.full_text,
        req.profile_id,
        finding=req.finding,
        quote=req.quote,
    )
    return {"authorities": authority_response(authorities)}
