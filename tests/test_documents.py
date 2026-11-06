from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfWriter
from reportlab.pdfgen import canvas


def test_text_and_paste_keep_locations():
    from backend.app.documents import extract_document, extract_paste

    text = extract_document("resume.txt", b"Python and SQL\nAirflow pipelines")
    pasted = extract_paste("Python\nAWS")
    assert [(e.location, e.text) for e in text] == [
        ("line 1", "Python and SQL"),
        ("line 2", "Airflow pipelines"),
    ]
    assert pasted[1].location == "line 2"


def test_docx_and_pdf_keep_paragraph_or_page():
    from backend.app.documents import extract_document

    document = Document()
    document.add_paragraph("Python data pipelines")
    buffer = BytesIO()
    document.save(buffer)
    docx = extract_document("resume.docx", buffer.getvalue())
    assert docx[0].location == "paragraph 1"
    assert "Python" in docx[0].text

    pdf_bytes = BytesIO()
    pdf = canvas.Canvas(pdf_bytes)
    pdf.drawString(72, 720, "Airflow orchestration")
    pdf.showPage()
    pdf.save()
    pages = extract_document("resume.pdf", pdf_bytes.getvalue())
    assert pages[0].location == "page 1"
    assert "Airflow" in pages[0].text


def test_scan_and_unsupported_type_report_clear_errors():
    from backend.app.documents import extract_document

    pdf_bytes = BytesIO()
    PdfWriter().write(pdf_bytes)
    with pytest.raises(ValueError, match="No readable text"):
        extract_document("scan.pdf", pdf_bytes.getvalue())
    with pytest.raises(ValueError, match="PDF, DOCX, or TXT"):
        extract_document("resume.png", b"not-a-document")
