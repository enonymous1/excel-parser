"""Excel file writer implementation."""

from pathlib import Path
from typing import Any

import pandas as pd

from ..core.interfaces import BaseWriter
from ..exceptions import ParseError, ParserError, UnsupportedFormatError


class ExcelWriter(BaseWriter):
    """Writer for Excel files (.xlsx, .xlsm)."""

    SUPPORTED_EXTENSIONS = [".xlsx", ".xlsm"]

    def write(
        self,
        data: pd.DataFrame | dict[str, pd.DataFrame],
        file_path: str | Path,
        sheet_name: str | None = None,
        index: bool = False,
        **kwargs: Any,
    ) -> None:
        """Write data to an Excel file.

        A DataFrame writes to one sheet (``sheet_name`` or ``"Sheet1"``).
        A dict writes one sheet per key. Passing ``sheet_name`` with a
        dict is an error: the dict keys are the sheet names.
        """
        path = Path(file_path)

        if not self.supports_format(path):
            raise UnsupportedFormatError(path.suffix, str(path))

        if isinstance(data, dict):
            if sheet_name is not None:
                raise ValueError(
                    "sheet_name must not be given when data is a dict; "
                    "dict keys are the sheet names"
                )
            if not data:
                raise ValueError("Cannot write an empty dict of DataFrames")
            sheets: dict[str, pd.DataFrame] = data
        else:
            sheets = {sheet_name or "Sheet1": data}

        if path.parent and str(path.parent) not in ("", ".") and not path.parent.exists():
            raise ParseError(f"Directory does not exist: {path.parent}")

        kwargs.pop("index", None)
        try:
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                for name, df in sheets.items():
                    df.to_excel(writer, sheet_name=name, index=index, **kwargs)
        except ParserError:
            raise
        except Exception as exc:
            raise ParseError(f"Failed to write Excel file {path}: {exc}") from exc

    def supports_format(self, file_path: str | Path) -> bool:
        """Check if this writer supports the given file format."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()
