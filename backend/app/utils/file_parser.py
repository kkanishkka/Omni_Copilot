import io
from typing import Optional


def parse_pdf(content: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        return f"[Error parsing PDF: {e}]"


def parse_docx(content: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text.strip()
    except Exception as e:
        return f"[Error parsing DOCX: {e}]"


def parse_file(content: bytes, filename: str) -> Optional[str]:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(content)
    elif lower.endswith(".docx"):
        return parse_docx(content)
    elif lower.endswith(".txt") or lower.endswith(".md"):
        return content.decode("utf-8", errors="replace")
    else:
        return None
