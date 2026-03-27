"""Word document parser tool — extract text from .docx files as Markdown."""

from __future__ import annotations

from pathlib import Path


class DocxParserTool:
    """Parse Word (.docx) files and return content as LLM-friendly Markdown.

    Converts headings, paragraphs, and tables to Markdown format.
    Requires python-docx >= 1.1.0.
    """

    def parse(self, file_path: str) -> str:
        """Parse a .docx file and return Markdown content.

        Args:
            file_path: Path to the .docx file.

        Returns:
            Markdown string of the document content.

        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: If the document cannot be parsed.
        """
        from docx import Document  # lazy import — optional dependency
        from docx.oxml.ns import qn

        doc = Document(file_path)
        lines: list[str] = []

        for block in doc.element.body:
            tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

            if tag == "p":
                # Paragraph
                para_text = "".join(r.text for r in block.iter(qn("w:t")))
                if not para_text.strip():
                    lines.append("")
                    continue
                # Detect heading style
                style_name = ""
                pPr = block.find(qn("w:pPr"))
                if pPr is not None:
                    pStyle = pPr.find(qn("w:pStyle"))
                    if pStyle is not None:
                        style_name = pStyle.get(qn("w:val"), "").lower()

                if "heading1" in style_name or style_name == "title":
                    lines.append(f"# {para_text}")
                elif "heading2" in style_name:
                    lines.append(f"## {para_text}")
                elif "heading3" in style_name:
                    lines.append(f"### {para_text}")
                elif "heading" in style_name:
                    lines.append(f"#### {para_text}")
                else:
                    lines.append(para_text)

            elif tag == "tbl":
                # Table — convert to Markdown table
                rows = block.findall(f".//{qn('w:tr')}")
                if not rows:
                    continue
                md_rows: list[list[str]] = []
                for row in rows:
                    cells = row.findall(f".//{qn('w:tc')}")
                    cell_texts = [
                        " ".join(
                            "".join(r.text for r in cell.iter(qn("w:t"))).split()
                        )
                        for cell in cells
                    ]
                    md_rows.append(cell_texts)

                if md_rows:
                    header = "| " + " | ".join(md_rows[0]) + " |"
                    separator = "| " + " | ".join(["---"] * len(md_rows[0])) + " |"
                    lines.append(header)
                    lines.append(separator)
                    for data_row in md_rows[1:]:
                        # Pad row if fewer cells than header
                        while len(data_row) < len(md_rows[0]):
                            data_row.append("")
                        lines.append("| " + " | ".join(data_row) + " |")
                lines.append("")

        return "\n".join(lines)
