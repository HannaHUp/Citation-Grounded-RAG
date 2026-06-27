import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models import DocStore
from backend.profiles import get_profile
from backend.services.authorities import authority_response, retrieve_authorities
from backend.services.chunker import chunk_text
from backend.services.extraction import extract_docx_document, extract_pdf_document
from backend.services.llm_finding import classify_doc_type, run_llm
from backend.services.verifier import verify_all
from backend.store import doc_store

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


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
    )
    profile_id = classify_doc_type(full_text[:3000])
    detected_doc_type = "complaint" if profile_id == "complaint_claims" else "contract"
    return {"doc_id": doc_id, "full_text": full_text, "detected_doc_type": detected_doc_type, "profile_id": profile_id}


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


@app.post("/authorities")
async def authorities(req: AuthoritiesRequest):
    doc = doc_store.get(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    authorities = retrieve_authorities(
        doc.full_text,
        req.profile_id,
        finding=req.finding,
        quote=req.quote,
    )
    return {"authorities": authority_response(authorities)}
