import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.models import DocStore
from backend.services.chunker import chunk_text
from backend.services.extraction import extract_docx, extract_pdf
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
    full_text = extract_pdf(content) if ext == ".pdf" else extract_docx(content)
    chunks = chunk_text(doc_id, full_text)
    doc_store[doc_id] = DocStore(doc_id=doc_id, full_text=full_text, chunks=chunks)
    return {"doc_id": doc_id, "full_text": full_text}
