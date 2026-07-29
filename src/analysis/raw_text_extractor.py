"""
Stage 3 (wiring) — Raw Text Extraction

Returns TRULY raw text — no whitespace restructuring, no header-spacing
guesses, no character substitutions (the old parse_pdf() pipeline replaces
'|' with 'I', which risks corrupting pipe-separated resume lines like
"Python | React | MySQL"). We bypass that cleanup entirely since Gemini
doesn't need pre-formatted structure and reads messy raw text fine.

Uses the underlying extractors directly:
    - CrossPlatformPDFExtractor.extract_text()  (pdftotext -> PyPDF2 -> OCR fallback chain)
    - extract_text_from_docx()                  (DOCX, assumed already raw — verify below)
"""

from __future__ import annotations
from pathlib import Path

from src.parsing.pdf_parser_improved import CrossPlatformPDFExtractor
from src.parsing.docx_parser import extract_text_from_docx

_pdf_extractor = CrossPlatformPDFExtractor()


def extract_raw_text(file_path: str) -> str:
    # Returns truly raw plain text from a PDF or DOCX resume file
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        raw_text = _pdf_extractor.extract_text(file_path)
    elif suffix == ".docx":
        raw_text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Only .pdf and .docx are supported.")

    if not raw_text or not raw_text.strip():
        raise RuntimeError(f"No text could be extracted from: {file_path}")

    return raw_text


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.analysis.raw_text_extractor <path_to_resume>")
        sys.exit(1)

    text = extract_raw_text(sys.argv[1])
    print(f"\nExtracted {len(text)} characters")
    print("---")
    # print(text[:500])
    print(text)
