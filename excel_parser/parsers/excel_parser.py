"""Excel file parser implementation."""

import importlib.util
from pathlib import Path
from typing import Any

import pandas as pd

from ..core.interfaces import BaseParser, ParseResult
from ..exceptions import (
    ParseError,
    ParserError,
    ParserFileNotFoundError,
    UnsupportedFormatError,
)

SheetSelector = str | int | list[str | int]


def _is_pyxlsb_installed() -> bool:
    return importlib.util.find_spec("pyxlsb") is not None


class ExcelParser(BaseParser):
    """Parser for Excel files (.xlsx, .xls, .xlsm, .xlsb)."""

    SUPPORTED_EXTENSIONS = [".xlsx", ".xls", ".xlsm", ".xlsb"]

    ENGINE_BY_EXTENSION = {
        ".xlsx": "openpyxl",
        ".xlsm": "openpyxl",
        ".xls": "calamine",
        ".xlsb": "pyxlsb",
    }

    def _engine_for(self, file_path: Path, engine: str | None) -> str:
        if engine:
            return engine
        extension = file_path.suffix.lower()
        resolved = self.ENGINE_BY_EXTENSION.get(extension)
        if resolved is None:
            raise UnsupportedFormatError(extension, str(file_path))
        if resolved == "pyxlsb" and not _is_pyxlsb_installed():
            raise ParseError(
                "Parsing .xlsb files requires pyxlsb: "
                'pip install "excel-parser[xlsb]"'
            )
        return resolved

    def parse(
        self,
        file_path: str | Path,
        sheet_name: SheetSelector | None = None,
        header: int | list[int] | None = 0,
        index_col: int | str | list[int | str] | None = None,
        usecols: str | list[str] | list[int] | None = None,
        dtype: dict[str, Any] | None = None,
        na_values: str | list[str] | None = None,
        keep_default_na: bool = True,
        skiprows: int | list[int] | None = None,
        nrows: int | None = None,
        engine: str | None = None,
        **kwargs: Any,
    ) -> ParseResult:
        """Parse an Excel file and return the data.

        ``data`` is always a dict mapping sheet name to DataFrame,
        including when a single sheet was requested.
        """
        path = Path(file_path)

        if not path.exists():
            raise ParserFileNotFoundError(f"File not found: {path}", str(path))

        if not self.supports_format(path):
            raise UnsupportedFormatError(path.suffix, str(path))

        if "engine" in kwargs:
            engine = kwargs.pop("engine")

        try:
            resolved_engine = self._engine_for(path, engine)
            data = pd.read_excel(
                path,
                sheet_name=sheet_name,
                header=header,
                index_col=index_col,
                usecols=usecols,
                dtype=dtype,
                na_values=na_values,
                keep_default_na=keep_default_na,
                skiprows=skiprows,
                nrows=nrows,
                engine=resolved_engine,
                **kwargs,
            )
        except ParserError:
            raise
        except Exception as exc:
            raise ParseError(f"Failed to parse Excel file {path}: {exc}") from exc

        if isinstance(data, dict):
            data_dict: dict[str, pd.DataFrame] = data
        else:
            label = self._sheet_label(path, sheet_name, resolved_engine)
            data_dict = {label: data}

        metadata: dict[str, Any] = {
            "file_path": str(path),
            "file_size": path.stat().st_size,
            "file_extension": path.suffix,
            "parser_type": "excel",
            "engine": resolved_engine,
            "sheet_names": list(data_dict.keys()),
            "sheet_count": len(data_dict),
            "total_rows": sum(len(df) for df in data_dict.values()),
            "total_columns": sum(len(df.columns) for df in data_dict.values()),
        }

        warnings: list[str] = []
        for name, df in data_dict.items():
            if df.empty:
                warnings.append(f"Sheet '{name}' is empty")
            null_columns = df.columns[df.isnull().all()].tolist()
            if null_columns:
                warnings.append(
                    f"Sheet '{name}' has columns with all null values: {null_columns}"
                )

        return ParseResult(data=data_dict, metadata=metadata, warnings=warnings)

    def _sheet_label(
        self,
        path: Path,
        sheet_name: SheetSelector | None,
        engine: str,
    ) -> str:
        if isinstance(sheet_name, str):
            return sheet_name
        if isinstance(sheet_name, int):
            try:
                names = self.get_sheet_names(path)
                return names[sheet_name]
            except (ParserError, IndexError):
                return "Sheet1"
        return "Sheet1"

    def supports_format(self, file_path: str | Path) -> bool:
        """Check if this parser supports the given file format."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

    def get_sheet_names(self, file_path: str | Path) -> list[str]:
        """Get sheet names without parsing the data."""
        path = Path(file_path)

        if not path.exists():
            raise ParserFileNotFoundError(f"File not found: {path}", str(path))

        try:
            resolved_engine = self._engine_for(path, None)
            with pd.ExcelFile(path, engine=resolved_engine) as excel_file:
                return list(excel_file.sheet_names)
        except ParserError:
            raise
        except Exception as exc:
            raise ParseError(
                f"Failed to read sheet names from {path}: {exc}"
            ) from exc

    def preview(
        self,
        file_path: str | Path,
        sheet_name: str | int | None = None,
        nrows: int = 5,
    ) -> ParseResult:
        """Get a preview of the Excel file (first few rows of each sheet)."""
        return self.parse(file_path, sheet_name=sheet_name, nrows=nrows)
