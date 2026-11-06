"""Read a PDF into plain text, one Page per PDF page."""
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import InvalidDocumentError


@dataclass(frozen=True)
class Page:
    text: str
    source: str  # PDF file name, e.g. "leave-policy.pdf"
    page: int    # 1-based page number


def load_pdf(pdf_path: Path) -> list[Page]:
    """Return the pages that contain text. Image-only pages are skipped."""
    try:
        reader = PdfReader(pdf_path)
        pdf_pages = list(reader.pages)
    except (PdfReadError, ValueError) as exc:
        raise InvalidDocumentError(f"Could not read '{pdf_path.name}' as a PDF") from exc

    pages: list[Page] = []
    for number, pdf_page in enumerate(pdf_pages, start=1):
        text = (pdf_page.extract_text() or "").strip()
        if not text:
            logger.warning("No text on {} page {} (scanned image?), skipped", pdf_path.name, number)
            continue
        pages.append(Page(text=text, source=pdf_path.name, page=number))
    return pages
