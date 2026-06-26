import io
import pdfplumber
from docx import Document

# ponytail: paragraph layout reconstruction skipped; .chars join is sufficient
# for offset round-trip — revisit only if a fixture fails


def extract_pdf(content: bytes) -> str:
    """Extract full text from PDF bytes preserving char offsets via sorted .chars.

    Uses pdfplumber .chars sorted by (doctop, x0) — document-level Y coordinate
    keeps offsets stable across page boundaries. Do NOT call page.extract_text();
    it normalizes whitespace and corrupts offsets (Pitfall 1).
    """
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        chars = []
        for page in pdf.pages:
            chars.extend(page.chars)  # each char has 'doctop', 'x0', 'text'
    chars.sort(key=lambda c: (c["doctop"], c["x0"]))
    return "".join(c["text"] for c in chars)


def extract_docx(content: bytes) -> str:
    """Extract full text from DOCX bytes with running offset accumulation.

    ponytail: tables/text-boxes skipped (doc.paragraphs only); iterate
    doc.element.body when a table-containing fixture fails round-trip (Pitfall 5).
    """
    doc = Document(io.BytesIO(content))
    full_text = ""
    for para in doc.paragraphs:
        full_text += para.text + "\n"
    return full_text
