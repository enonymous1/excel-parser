"""Test the factory functionality."""

from pathlib import Path

import pandas as pd
import pytest

from excel_parser.core.factory import ParserFactory
from excel_parser.core.interfaces import BaseParser
from excel_parser.exceptions import UnsupportedFormatError
from excel_parser.parsers.excel_parser import ExcelParser
from excel_parser.writers.excel_writer import ExcelWriter


@pytest.fixture
def sample_excel_file(tmp_path: Path) -> Path:
    """Create a temporary Excel file for testing."""
    path = tmp_path / "sample.xlsx"
    pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}).to_excel(path, index=False)
    return path


class TestParserFactory:
    def test_create_parser_by_format(self) -> None:
        parser = ParserFactory.create_parser("excel")
        assert isinstance(parser, ExcelParser)

    def test_create_parser_format_is_case_insensitive(self) -> None:
        assert isinstance(ParserFactory.create_parser("Excel"), ExcelParser)
        assert isinstance(ParserFactory.create_parser(" EXCEL "), ExcelParser)

    def test_create_parser_by_extension(self) -> None:
        assert isinstance(ParserFactory.create_parser(".xlsx"), ExcelParser)
        assert isinstance(ParserFactory.create_parser("xls"), ExcelParser)

    def test_create_parser_by_file_path(self, sample_excel_file: Path) -> None:
        parser = ParserFactory.create_parser(file_path=sample_excel_file)
        assert isinstance(parser, ExcelParser)

    def test_create_parser_unsupported_format(self) -> None:
        with pytest.raises(UnsupportedFormatError):
            ParserFactory.create_parser("unsupported_format")

    def test_create_parser_unsupported_extension(self) -> None:
        with pytest.raises(UnsupportedFormatError):
            ParserFactory.create_parser(file_path="test.unsupported")

    def test_create_parser_no_arguments(self) -> None:
        with pytest.raises(ValueError):
            ParserFactory.create_parser()

    def test_get_supported_formats(self) -> None:
        formats = ParserFactory.get_supported_formats()
        assert "parsers" in formats
        assert "writers" in formats
        assert "excel" in formats["parsers"]
        assert "excel" in formats["writers"]
        assert ".xlsx" in formats["parsers"]["excel"]
        assert ".xlsx" in formats["writers"]["excel"]

    def test_create_writer(self, sample_excel_file: Path) -> None:
        assert isinstance(ParserFactory.create_writer("excel"), ExcelWriter)
        assert isinstance(
            ParserFactory.create_writer(file_path="out.xlsx"), ExcelWriter
        )
        with pytest.raises(UnsupportedFormatError):
            ParserFactory.create_writer(file_path="out.csv")
        with pytest.raises(UnsupportedFormatError):
            ParserFactory.create_writer("csv")

    def test_register_parser(self) -> None:
        class DummyParser(BaseParser):
            def parse(self, file_path: object, **kwargs: object) -> object:
                raise NotImplementedError

            def supports_format(self, file_path: object) -> bool:
                return False

            def get_supported_extensions(self) -> list:
                return [".dummy"]

        ParserFactory.register_parser("dummy", DummyParser)
        try:
            assert isinstance(ParserFactory.create_parser("dummy"), DummyParser)
        finally:
            ParserFactory._parsers.pop("dummy", None)

    def test_register_parser_rejects_non_parser(self) -> None:
        with pytest.raises(TypeError):
            ParserFactory.register_parser("bad", object)  # type: ignore[arg-type]

    def test_register_writer_rejects_non_writer(self) -> None:
        with pytest.raises(TypeError):
            ParserFactory.register_writer("bad", object)  # type: ignore[arg-type]

    def test_dummy_parser_isolation(self) -> None:
        # Registering in test_register_parser must not leak into other tests.
        assert "dummy" not in ParserFactory.get_supported_formats()["parsers"]
