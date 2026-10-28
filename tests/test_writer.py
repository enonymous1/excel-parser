"""Test the Excel writer and its round-trip through the parser."""

from pathlib import Path

import pandas as pd
import pytest

from excel_parser.core.factory import ParserFactory
from excel_parser.exceptions import ParseError, UnsupportedFormatError
from excel_parser.parsers.excel_parser import ExcelParser
from excel_parser.writers.excel_writer import ExcelWriter


class TestExcelWriter:
    def test_write_and_reparse_dataframe(self, tmp_path: Path) -> None:
        output = tmp_path / "out.xlsx"
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        ExcelWriter().write(df, output)
        result = ExcelParser().parse(output)
        assert list(result.data) == ["Sheet1"]
        pd.testing.assert_frame_equal(result.data["Sheet1"], df)

    def test_write_dict_uses_keys_as_sheets(self, tmp_path: Path) -> None:
        output = tmp_path / "out.xlsx"
        data = {
            "One": pd.DataFrame({"A": [1]}),
            "Two": pd.DataFrame({"B": [2]}),
        }
        ExcelWriter().write(data, output)
        assert ExcelParser().get_sheet_names(output) == ["One", "Two"]

    def test_write_with_sheet_name(self, tmp_path: Path) -> None:
        output = tmp_path / "named.xlsx"
        ExcelWriter().write(pd.DataFrame({"A": [1]}), output, sheet_name="Custom")
        assert ExcelParser().get_sheet_names(output) == ["Custom"]

    def test_write_dict_with_sheet_name_is_error(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="sheet_name"):
            ExcelWriter().write(
                {"One": pd.DataFrame({"A": [1]})}, tmp_path / "o.xlsx", sheet_name="X"
            )

    def test_write_empty_dict_is_error(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="empty"):
            ExcelWriter().write({}, tmp_path / "o.xlsx")

    def test_write_unsupported_format(self, tmp_path: Path) -> None:
        with pytest.raises(UnsupportedFormatError):
            ExcelWriter().write(pd.DataFrame({"A": [1]}), tmp_path / "out.csv")

    def test_write_missing_parent_directory(self, tmp_path: Path) -> None:
        with pytest.raises(ParseError, match="Directory does not exist"):
            ExcelWriter().write(
                pd.DataFrame({"A": [1]}), tmp_path / "nope" / "out.xlsx"
            )

    def test_writer_via_factory(self, tmp_path: Path) -> None:
        writer = ParserFactory.create_writer(file_path="out.xlsx")
        output = tmp_path / "factory.xlsx"
        writer.write(pd.DataFrame({"A": [1]}), output)
        assert output.exists()

    def test_supports_format(self) -> None:
        writer = ExcelWriter()
        assert writer.supports_format("a.xlsx") is True
        assert writer.supports_format("a.xlsm") is True
        assert writer.supports_format("a.xls") is False
