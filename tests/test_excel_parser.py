"""Test the Excel parser functionality."""

from pathlib import Path

import pandas as pd
import pytest

from excel_parser.exceptions import (
    ParseError,
    ParserFileNotFoundError,
    UnsupportedFormatError,
)
from excel_parser.parsers.excel_parser import ExcelParser

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_excel_file(tmp_path: Path) -> Path:
    """Create a temporary single-sheet Excel file."""
    data = {
        "Name": ["Alice", "Bob", "Charlie", "Diana"],
        "Age": [25, 30, 35, 28],
        "City": ["New York", "London", "Paris", "Tokyo"],
        "Salary": [50000, 60000, 70000, 55000],
    }
    path = tmp_path / "sample.xlsx"
    pd.DataFrame(data).to_excel(path, index=False)
    return path


@pytest.fixture
def multi_sheet_excel_file(tmp_path: Path) -> Path:
    """Create a temporary multi-sheet Excel file."""
    path = tmp_path / "multi.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"Product": ["A", "B", "C"], "Price": [10, 20, 30]}).to_excel(
            writer, sheet_name="Products", index=False
        )
        pd.DataFrame({"Customer": ["X", "Y", "Z"], "Orders": [5, 10, 15]}).to_excel(
            writer, sheet_name="Customers", index=False
        )
    return path


class TestExcelParser:
    def test_parser_initialization(self) -> None:
        parser = ExcelParser()
        extensions = parser.get_supported_extensions()
        assert ".xlsx" in extensions
        assert ".xls" in extensions
        assert ".xlsb" in extensions
        # The returned list is a copy; mutating it must not affect the parser.
        extensions.append(".bogus")
        assert ".bogus" not in parser.get_supported_extensions()

    def test_supports_format(self) -> None:
        parser = ExcelParser()
        assert parser.supports_format("test.xlsx") is True
        assert parser.supports_format("test.XLS") is True
        assert parser.supports_format("test.xlsm") is True
        assert parser.supports_format("test.csv") is False
        assert parser.supports_format("test.txt") is False

    def test_parse_always_returns_dict(
        self, sample_excel_file: Path, multi_sheet_excel_file: Path
    ) -> None:
        parser = ExcelParser()

        result = parser.parse(sample_excel_file)
        assert isinstance(result.data, dict)
        assert list(result.data) == ["Sheet1"]

        result = parser.parse(multi_sheet_excel_file)
        assert set(result.data) == {"Products", "Customers"}

        result = parser.parse(multi_sheet_excel_file, sheet_name="Products")
        assert isinstance(result.data, dict)
        assert list(result.data) == ["Products"]
        assert len(result.data["Products"]) == 3

    def test_parse_single_sheet_metadata(self, sample_excel_file: Path) -> None:
        result = ExcelParser().parse(sample_excel_file, sheet_name=0)
        assert result.metadata["sheet_names"] == ["Sheet1"]
        assert result.metadata["sheet_count"] == 1
        assert result.metadata["total_rows"] == 4
        assert result.metadata["total_columns"] == 4
        assert result.metadata["parser_type"] == "excel"
        assert result.metadata["engine"] == "openpyxl"
        assert result.metadata["file_size"] > 0

    def test_parse_multi_sheet_metadata(self, multi_sheet_excel_file: Path) -> None:
        result = ExcelParser().parse(multi_sheet_excel_file)
        assert result.metadata["sheet_names"] == ["Products", "Customers"]
        assert result.metadata["total_rows"] == 6
        assert result.metadata["total_columns"] == 4

    def test_parse_sheet_by_index(self, multi_sheet_excel_file: Path) -> None:
        result = ExcelParser().parse(multi_sheet_excel_file, sheet_name=1)
        assert list(result.data) == ["Customers"]

    def test_parse_specific_sheet_by_list(self, multi_sheet_excel_file: Path) -> None:
        result = ExcelParser().parse(
            multi_sheet_excel_file, sheet_name=["Products", "Customers"]
        )
        assert set(result.data) == {"Products", "Customers"}

    def test_get_sheet_names(self, multi_sheet_excel_file: Path) -> None:
        sheet_names = ExcelParser().get_sheet_names(multi_sheet_excel_file)
        assert sheet_names == ["Products", "Customers"]

    def test_preview(self, sample_excel_file: Path) -> None:
        result = ExcelParser().preview(sample_excel_file, nrows=2)
        df = next(iter(result.data.values()))
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert len(df.columns) == 4

    def test_file_not_found(self) -> None:
        with pytest.raises(ParserFileNotFoundError):
            ExcelParser().parse("non_existent_file.xlsx")
        with pytest.raises(ParserFileNotFoundError):
            ExcelParser().get_sheet_names("non_existent_file.xlsx")

    def test_unsupported_format(self, tmp_path: Path) -> None:
        text_file = tmp_path / "test.txt"
        text_file.write_bytes(b"test content")
        with pytest.raises(UnsupportedFormatError):
            ExcelParser().parse(text_file)

    def test_missing_sheet(self, multi_sheet_excel_file: Path) -> None:
        with pytest.raises(ParseError, match="NoSuchSheet"):
            ExcelParser().parse(multi_sheet_excel_file, sheet_name="NoSuchSheet")

    def test_empty_sheet_warning(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.xlsx"
        with pd.ExcelWriter(path) as writer:
            pd.DataFrame().to_excel(writer, sheet_name="Empty", index=False)
            pd.DataFrame({"A": [1]}).to_excel(writer, sheet_name="Full", index=False)
        result = ExcelParser().parse(path)
        assert any("Empty" in warning and "empty" in warning for warning in result.warnings)

    def test_parse_legacy_xls_fixture(self) -> None:
        xls_file = FIXTURES / "sample_data.xls"
        result = ExcelParser().parse(xls_file)
        assert set(result.data) == {"Employees", "Sales"}
        assert result.metadata["engine"] == "calamine"
        assert len(result.data["Employees"]) == 5
        assert "Alice Johnson" in result.data["Employees"]["Name"].tolist()

    def test_parse_bundled_sample(self) -> None:
        sample = Path(__file__).resolve().parent.parent / "sample_data.xlsx"
        result = ExcelParser().parse(sample)
        assert set(result.data) == {"Employees", "Sales"}
        assert result.metadata["total_rows"] == 10

    def test_xlsb_engine_selection(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The .xlsb path must select the pyxlsb engine, not sniff content."""
        captured: dict = {}

        def fake_read_excel(path: Path, **kwargs: object) -> dict:
            captured.update(kwargs)
            return {"Sheet1": pd.DataFrame({"A": [1]})}

        monkeypatch.setattr(
            "excel_parser.parsers.excel_parser.pd.read_excel", fake_read_excel
        )
        xlsb_file = tmp_path / "data.xlsb"
        xlsb_file.write_bytes(b"fake")
        result = ExcelParser().parse(xlsb_file)
        assert captured["engine"] == "pyxlsb"
        assert list(result.data) == ["Sheet1"]

    def test_xlsb_without_pyxlsb(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "excel_parser.parsers.excel_parser._is_pyxlsb_installed",
            lambda: False,
        )
        xlsb_file = tmp_path / "data.xlsb"
        xlsb_file.write_bytes(b"fake")
        with pytest.raises(ParseError, match=r"excel-parser\[xlsb\]"):
            ExcelParser().parse(xlsb_file)

    def test_corrupt_file_is_parse_error(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.xlsx"
        corrupt.write_bytes(b"not a workbook")
        with pytest.raises(ParseError):
            ExcelParser().parse(corrupt)
