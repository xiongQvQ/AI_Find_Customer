"""Tests for tools/excel_parser.py — parse Excel/CSV to Markdown and dicts."""

import pytest

from tools.excel_parser import ExcelParserTool


@pytest.fixture
def sample_csv(tmp_path):
    """Create a test CSV file."""
    csv_path = str(tmp_path / "leads.csv")
    with open(csv_path, "w") as f:
        f.write("company,website,industry,country\n")
        f.write("SolarTech,https://solartech.de,Solar,DE\n")
        f.write("PV Dist,https://pvdist.com,Solar,FR\n")
        f.write("GreenCo,https://greenco.uk,Renewable,GB\n")
    return csv_path


@pytest.fixture
def sample_xlsx(tmp_path):
    """Create a test Excel file."""
    import openpyxl

    xlsx_path = str(tmp_path / "leads.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads"
    ws.append(["company", "website", "industry", "country"])
    ws.append(["SolarTech", "https://solartech.de", "Solar", "DE"])
    ws.append(["PV Dist", "https://pvdist.com", "Solar", "FR"])

    ws2 = wb.create_sheet("Summary")
    ws2.append(["metric", "value"])
    ws2.append(["total_leads", 2])

    wb.save(xlsx_path)
    return xlsx_path


@pytest.fixture
def sample_tsv(tmp_path):
    """Create a test TSV file."""
    tsv_path = str(tmp_path / "data.tsv")
    with open(tsv_path, "w") as f:
        f.write("name\tscore\n")
        f.write("Alpha\t0.9\n")
        f.write("Beta\t0.7\n")
    return tsv_path


class TestExcelParserCSV:
    def test_parse_to_markdown(self, sample_csv):
        tool = ExcelParserTool()
        md = tool.parse_to_markdown(sample_csv)
        assert "SolarTech" in md
        assert "PV Dist" in md
        assert "company" in md

    def test_parse_to_dicts(self, sample_csv):
        tool = ExcelParserTool()
        rows = tool.parse_to_dicts(sample_csv)
        assert len(rows) == 3
        assert rows[0]["company"] == "SolarTech"
        assert rows[0]["country"] == "DE"

    def test_parse_max_rows(self, sample_csv):
        tool = ExcelParserTool()
        rows = tool.parse_to_dicts(sample_csv, max_rows=2)
        assert len(rows) == 2

    def test_get_row_count(self, sample_csv):
        tool = ExcelParserTool()
        assert tool.get_row_count(sample_csv) == 3

    def test_get_sheet_names_csv(self, sample_csv):
        tool = ExcelParserTool()
        assert tool.get_sheet_names(sample_csv) == ["Sheet1"]


class TestExcelParserXLSX:
    def test_parse_to_markdown(self, sample_xlsx):
        tool = ExcelParserTool()
        md = tool.parse_to_markdown(sample_xlsx)
        assert "SolarTech" in md

    def test_parse_to_dicts(self, sample_xlsx):
        tool = ExcelParserTool()
        rows = tool.parse_to_dicts(sample_xlsx)
        assert len(rows) == 2
        assert rows[0]["company"] == "SolarTech"

    def test_parse_specific_sheet(self, sample_xlsx):
        tool = ExcelParserTool()
        rows = tool.parse_to_dicts(sample_xlsx, sheet_name="Summary")
        assert len(rows) == 1
        assert rows[0]["metric"] == "total_leads"

    def test_get_sheet_names(self, sample_xlsx):
        tool = ExcelParserTool()
        names = tool.get_sheet_names(sample_xlsx)
        assert "Leads" in names
        assert "Summary" in names

    def test_get_row_count(self, sample_xlsx):
        tool = ExcelParserTool()
        assert tool.get_row_count(sample_xlsx) == 2


class TestExcelParserTSV:
    def test_parse_tsv(self, sample_tsv):
        tool = ExcelParserTool()
        rows = tool.parse_to_dicts(sample_tsv)
        assert len(rows) == 2
        assert rows[0]["name"] == "Alpha"


class TestExcelParserErrors:
    def test_unsupported_extension(self, tmp_path):
        bad_file = str(tmp_path / "data.json")
        with open(bad_file, "w") as f:
            f.write("{}")
        tool = ExcelParserTool()
        with pytest.raises(ValueError, match="Unsupported file type"):
            tool.parse_to_dicts(bad_file)

    def test_nonexistent_file(self):
        tool = ExcelParserTool()
        with pytest.raises(Exception):
            tool.parse_to_dicts("/nonexistent/file.csv")
