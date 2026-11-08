"""Temporary, bounded ingestion of text-based PDF policies.

PDFs are never written to project storage or forwarded to Clocked by this
endpoint. Text is returned to the user for review before any paid analysis.
"""
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PDF_BYTES = 2 * 1024 * 1024
MAX_PDF_PAGES = 12
MAX_PDF_TEXT = 12_000


class PdfInputError(ValueError):
    """Safe, user-facing error for an unsupported PDF."""


def parse_policy_pdf(content: bytes) -> dict:
    if not content or len(content) > MAX_PDF_BYTES:
        raise PdfInputError("PDF must be between 1 byte and 2 MB.")
    if not content.startswith(b"%PDF-"):
        raise PdfInputError("This file is not a valid PDF document.")
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise PdfInputError("Password-protected PDFs are not supported. Export an unlocked copy first.")
        count = len(reader.pages)
        if not 1 <= count <= MAX_PDF_PAGES:
            raise PdfInputError("PDF must contain between 1 and 12 pages.")
        fragments: list[str] = []
        pages: list[dict] = []
        offset = 0
        for i, page in enumerate(reader.pages, start=1):
            # No OCR or image interpretation here: missing text means review.
            fragment = (page.extract_text(extraction_mode="plain") or "").strip()
            if len(fragment) > MAX_PDF_TEXT:
                raise PdfInputError("The PDF contains more than 12,000 characters. Use a shorter policy excerpt.")
            if fragments:
                fragments.append("\n\n")
                offset += 2
            start = offset
            fragments.append(fragment)
            offset += len(fragment)
            pages.append({"page": i, "start": start, "end": offset, "characters": len(fragment)})
            if offset > MAX_PDF_TEXT:
                raise PdfInputError("The PDF contains more than 12,000 characters. Use a shorter policy excerpt.")
        text = "".join(fragments)
        if len(text.strip()) < 20:
            raise PdfInputError("No usable selectable text found. Scanned/image PDFs need OCR and are not supported yet.")
        return {
            "text": text,
            "page_count": count,
            "characters": len(text),
            "pages": pages,
            "source": "temporary_pdf_text_extraction",
            "clocked_calls": 0,
            "note": "Review extracted text before analysis. No Clocked request was made and no PDF was saved to app storage.",
        }
    except PdfInputError:
        raise
    except (PdfReadError, OSError, ValueError, TypeError, KeyError) as exc:
        raise PdfInputError("Could not read this PDF. Try exporting a text-based PDF instead.") from exc