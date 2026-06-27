"""
D-03 round-trip gate: char offsets from pdfplumber .chars must satisfy
full_text[start:end] == expected_text for known spans on the real fixture.

KNOWN_SPANS were derived by extracting the real fixture files and finding
stable, unambiguous spans. Update if fixtures change (see fixtures/README.md).
"""
import io
import os
import pytest

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
PDF_PATH = os.path.join(FIXTURE_DIR, "sample_contract.pdf")
DOCX_PATH = os.path.join(FIXTURE_DIR, "sample_contract.docx")

# Spans verified against the real Musk v. Altman complaint PDF fixture.
# Font decomposes ligatures to ASCII so no fi/ffi glyph issues.
# At least one span contains a word historically rendered with ligatures
# in other fonts ("FIDUCIARY" — fi ligature candidate).
KNOWN_SPANS = [
    # (expected_text, start, end)
    ("Superior Court of California", 99, 127),   # 28 chars
    ("San Francisco", 138, 151),                  # 13 chars — city name
    ("FIDUCIARY", 954, 963),                      # 9 chars — ligature-bearing word
]

DOCX_KNOWN_SPAN = ("Agreement", 47, 56)  # from Mutual Services Agreement docx


def test_offset_round_trip():
    """D-03 gate: pdfplumber .chars join round-trips all KNOWN_SPANS."""
    from backend.services.extraction import extract_pdf

    with open(PDF_PATH, "rb") as f:
        content = f.read()
    full_text = extract_pdf(content)

    for expected_text, start, end in KNOWN_SPANS:
        actual = full_text[start:end]
        assert actual == expected_text, (
            f"Offset drift at [{start}:{end}]: "
            f"got {actual!r}, expected {expected_text!r}"
        )


def test_pdf_document_page_spans_cover_full_text_contiguously():
    """Page-aware PDF extraction preserves canonical text and spans every offset."""
    from backend.services.extraction import extract_pdf, extract_pdf_document

    with open(PDF_PATH, "rb") as f:
        content = f.read()

    document = extract_pdf_document(content)
    assert document.full_text == extract_pdf(content)
    assert len(document.page_spans) > 1
    assert document.page_spans[0].start_offset == 0
    assert document.page_spans[-1].end_offset == len(document.full_text)

    page_numbers = [span.page_number for span in document.page_spans]
    assert page_numbers == sorted(page_numbers)

    for prev, curr in zip(document.page_spans, document.page_spans[1:]):
        assert prev.end_offset == curr.start_offset
        assert prev.end_offset > prev.start_offset
    assert document.page_spans[-1].end_offset > document.page_spans[-1].start_offset

    for expected_text, start, end in KNOWN_SPANS:
        assert document.full_text[start:end] == expected_text


def test_full_text_is_char_join():
    """Extraction must use .chars sorted by (doctop, x0), not page.extract_text()."""
    import pdfplumber
    from backend.services.extraction import extract_pdf

    with open(PDF_PATH, "rb") as f:
        content = f.read()
    full_text = extract_pdf(content)

    # Re-derive expected text via the reference implementation
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        chars = []
        for page in pdf.pages:
            chars.extend(page.chars)
    chars.sort(key=lambda c: (c["doctop"], c["x0"]))
    expected = "".join(c["text"] for c in chars)

    assert full_text == expected, (
        f"extract_pdf output differs from sorted-chars join "
        f"(first diff at {next(i for i,(a,b) in enumerate(zip(full_text,expected)) if a!=b)})"
    )


def test_docx_offset_round_trip():
    """DOCX extraction round-trips a known span from the real fixture."""
    from backend.services.extraction import extract_docx

    with open(DOCX_PATH, "rb") as f:
        content = f.read()
    full_text = extract_docx(content)

    expected_text, start, end = DOCX_KNOWN_SPAN
    actual = full_text[start:end]
    assert actual == expected_text, (
        f"DOCX offset drift at [{start}:{end}]: "
        f"got {actual!r}, expected {expected_text!r}"
    )


def test_docx_document_has_page_one_span_covering_full_text():
    """DOCX MVP pagination is explicit: one page-1 span covers full_text."""
    from backend.services.extraction import extract_docx, extract_docx_document

    with open(DOCX_PATH, "rb") as f:
        content = f.read()

    document = extract_docx_document(content)
    assert document.full_text == extract_docx(content)
    assert len(document.page_spans) == 1
    span = document.page_spans[0]
    assert span.page_number == 1
    assert span.start_offset == 0
    assert span.end_offset == len(document.full_text)

    expected_text, start, end = DOCX_KNOWN_SPAN
    assert document.full_text[start:end] == expected_text
