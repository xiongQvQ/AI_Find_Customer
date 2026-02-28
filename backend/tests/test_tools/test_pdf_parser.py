"""Tests for tools/pdf_parser.py — parse PDF to Markdown using real pymupdf4llm."""

import os
import tempfile

import pymupdf
import pytest

from tools.pdf_parser import PDFParserTool


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal test PDF with two pages."""
    pdf_path = str(tmp_path / "test.pdf")
    doc = pymupdf.open()

    # Page 1
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Solar Inverter Product Catalog", fontsize=16)
    page1.insert_text((72, 120), "This is a test PDF for the AI Hunter pipeline.")

    # Page 2
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Product Specifications", fontsize=14)
    page2.insert_text((72, 110), "Model: SI-5000")
    page2.insert_text((72, 130), "Power: 5000W")

    doc.save(pdf_path)
    doc.close()
    return pdf_path


class TestPDFParserTool:
    def test_parse_returns_markdown(self, sample_pdf):
        tool = PDFParserTool()
        result = tool.parse(sample_pdf)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Solar Inverter" in result or "Product" in result

    def test_parse_contains_page_content(self, sample_pdf):
        tool = PDFParserTool()
        result = tool.parse(sample_pdf)
        assert "test PDF" in result or "Catalog" in result

    def test_parse_specific_page(self, sample_pdf):
        tool = PDFParserTool()
        result = tool.parse(sample_pdf, pages=[1])
        assert "SI-5000" in result or "Specifications" in result

    def test_get_page_count(self, sample_pdf):
        tool = PDFParserTool()
        count = tool.get_page_count(sample_pdf)
        assert count == 2

    def test_parse_nonexistent_file(self):
        tool = PDFParserTool()
        with pytest.raises(Exception):
            tool.parse("/nonexistent/file.pdf")
