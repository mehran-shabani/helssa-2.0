"""
PDF text extraction utilities.

Extracts text from PDF files with safety limits to prevent
excessive token usage.
"""
from __future__ import annotations

import io

from django.core.files.uploadedfile import UploadedFile

try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    from pdfminer.pdfparser import PDFSyntaxError

    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    PDFSyntaxError = Exception  # Fallback for type hints


def extract_text(
    pdf_file: UploadedFile, max_pages: int = 8, max_chars: int = 8000
) -> str:
    """
    Extract text from a PDF file with safety limits.

    Args:
        pdf_file: Uploaded PDF file.
        max_pages: Maximum number of pages to process.
        max_chars: Maximum number of characters to extract.

    Returns:
        Extracted text, truncated if necessary.
    """
    if not PDF_SUPPORT:
        return "[PDF extraction not available - pdfminer.six not installed]"

    try:
        # Read the file content
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        pdf_stream = io.BytesIO(pdf_bytes)

        # Extract text
        text = pdf_extract_text(pdf_stream, maxpages=max_pages)

        # Truncate if too long
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... truncated for length ...]"

        return text.strip() or "[No text found in PDF]"

    except PDFSyntaxError:
        return "[Invalid or corrupted PDF file]"
    except Exception as e:
        return f"[PDF extraction error: {str(e)}]"
