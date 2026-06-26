# Test Fixtures

## Required Files (human-supplied)

### `sample_contract.pdf`
A real contract or legal complaint PDF with a text layer (not scanned/OCR).
The file at this path is the Musk v. Altman complaint (46 pages, text-extractable).
The D-03 round-trip test uses KNOWN_SPANS derived from the actual content of this file.

Note: this PDF's font decomposes ligatures to ASCII (no fi/ffi glyphs), so KNOWN_SPANS
use real strings found in the extracted text (e.g. "FIDUCIARY", "San Francisco").

### `sample_contract.docx`
A real generated DOCX contract (Mutual Services Agreement) containing the words
"office" and "efficient". Used for the DOCX extraction round-trip test.

## Note on KNOWN_SPANS
The KNOWN_SPANS in `tests/test_extraction.py` were derived by running the extraction
against the real fixture files. To update them after replacing a fixture:
1. Run `python -c "import pdfplumber, io; ..."` to extract the new full_text
2. Find 3+ stable spans using `full_text.find(word)`
3. Update KNOWN_SPANS in test_extraction.py
