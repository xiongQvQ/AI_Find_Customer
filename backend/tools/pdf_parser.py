"""PDF parser tool — extract text from PDF files as Markdown using pymupdf4llm."""

from __future__ import annotations

import pymupdf4llm


class PDFParserTool:
    """Parse PDF files and return content as LLM-friendly Markdown.

    Uses pymupdf4llm which preserves structure (headings, tables, lists)
    better than raw text extraction.
    """

    def parse(self, file_path: str, *, pages: list[int] | None = None) -> str:
        """Parse a PDF file and return Markdown content.

        Args:
            file_path: Path to the PDF file.
            pages: Optional list of 0-indexed page numbers to extract.
                   None = all pages.

        Returns:
            Markdown string of the PDF content.

        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: If the PDF cannot be parsed.
        """
        kwargs = {}
        if pages is not None:
            kwargs["pages"] = pages

        md_text = pymupdf4llm.to_markdown(file_path, **kwargs)
        return md_text

    def get_page_count(self, file_path: str) -> int:
        """Return the number of pages in a PDF file."""
        import pymupdf

        doc = pymupdf.open(file_path)
        count = len(doc)
        doc.close()
        return count
