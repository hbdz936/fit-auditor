import io
from pypdf import PdfReader
from docx import Document


class UnsupportedFileType(Exception):
    pass


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Best-effort text extraction from a PDF or DOCX resume upload.

    This is intentionally simple: no layout reconstruction, no column
    detection, no OCR for scanned/image-based PDFs. It pulls whatever
    text the file format exposes directly. Output always lands in an
    editable textarea, so imperfect extraction (a misplaced header, a
    skipped line) is a recoverable UX issue, not a hard failure.
    """
    lower = filename.lower()

    if lower.endswith(".pdf"):
        return _extract_pdf(file_bytes)
    elif lower.endswith(".docx"):
        return _extract_docx(file_bytes)
    else:
        raise UnsupportedFileType(f"Unsupported file type: {filename}")


def _extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text).strip()


def _extract_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()