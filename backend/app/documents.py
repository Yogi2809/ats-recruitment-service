from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader

from .models import Evidence


def _chunks(source: str, values: list[tuple[str, str]]) -> list[Evidence]:
    prefix = uuid4().hex[:10]
    result = [
        Evidence(f"{prefix}-{index}", source, location, text.strip())
        for index, (location, text) in enumerate(values, start=1)
        if text.strip()
    ]
    if not result:
        raise ValueError("No readable text found. For scanned PDFs, paste the text instead.")
    return result


def extract_paste(text: str) -> list[Evidence]:
    return _chunks("Pasted text", [(f"line {i}", line) for i, line in enumerate(text.splitlines(), 1)])


def extract_document(filename: str, data: bytes) -> list[Evidence]:
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx", ".txt"}:
        raise ValueError("Use a PDF, DOCX, or TXT file.")
    if len(data) > 5 * 1024 * 1024:
        raise ValueError("File exceeds the 5 MB limit.")
    try:
        if extension == ".txt":
            text = data.decode("utf-8-sig")
            values = [(f"line {i}", line) for i, line in enumerate(text.splitlines(), 1)]
        elif extension == ".pdf":
            reader = PdfReader(BytesIO(data))
            values = [(f"page {i}", page.extract_text() or "") for i, page in enumerate(reader.pages, 1)]
        else:
            doc = Document(BytesIO(data))
            values = [(f"paragraph {i}", p.text) for i, p in enumerate(doc.paragraphs, 1)]
            for table_i, table in enumerate(doc.tables, 1):
                for row_i, row in enumerate(table.rows, 1):
                    values.append((f"table {table_i} row {row_i}", " | ".join(cell.text for cell in row.cells)))
    except Exception as exc:
        # Parser exceptions vary by document library and malformed file type.
        raise ValueError("Could not read this document. Try another file or paste its text.") from exc
    return _chunks(filename, values)
