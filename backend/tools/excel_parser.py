"""Excel/CSV parser tool — extract tabular data as Markdown or structured dicts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExcelParserTool:
    """Parse Excel (.xlsx/.xls) and CSV files into structured data.

    Returns data as Markdown tables (for LLM consumption) or as list of dicts.
    """

    SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".tsv"}

    def parse_to_markdown(
        self,
        file_path: str,
        *,
        sheet_name: str | int = 0,
        max_rows: int | None = None,
    ) -> str:
        """Parse a spreadsheet file and return content as a Markdown table.

        Args:
            file_path: Path to the file.
            sheet_name: Sheet name or 0-indexed number (Excel only).
            max_rows: Maximum rows to include. None = all rows.

        Returns:
            Markdown table string.
        """
        df = self._read_file(file_path, sheet_name=sheet_name)
        if max_rows is not None:
            df = df.head(max_rows)
        return df.to_markdown(index=False)

    def parse_to_dicts(
        self,
        file_path: str,
        *,
        sheet_name: str | int = 0,
        max_rows: int | None = None,
    ) -> list[dict]:
        """Parse a spreadsheet file and return rows as list of dicts.

        Args:
            file_path: Path to the file.
            sheet_name: Sheet name or 0-indexed number (Excel only).
            max_rows: Maximum rows to return. None = all rows.

        Returns:
            List of row dicts.
        """
        df = self._read_file(file_path, sheet_name=sheet_name)
        if max_rows is not None:
            df = df.head(max_rows)
        return df.to_dict(orient="records")

    def get_sheet_names(self, file_path: str) -> list[str]:
        """Return sheet names for an Excel file. CSV returns ['Sheet1']."""
        ext = Path(file_path).suffix.lower()
        if ext in {".csv", ".tsv"}:
            return ["Sheet1"]
        xls = pd.ExcelFile(file_path)
        return xls.sheet_names

    def get_row_count(self, file_path: str, *, sheet_name: str | int = 0) -> int:
        """Return the number of data rows (excluding header)."""
        df = self._read_file(file_path, sheet_name=sheet_name)
        return len(df)

    def _read_file(self, file_path: str, *, sheet_name: str | int = 0) -> pd.DataFrame:
        """Read a file into a DataFrame based on extension."""
        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {self.SUPPORTED_EXTENSIONS}")

        if ext == ".csv":
            return pd.read_csv(file_path)
        elif ext == ".tsv":
            return pd.read_csv(file_path, sep="\t")
        else:
            return pd.read_excel(file_path, sheet_name=sheet_name)
