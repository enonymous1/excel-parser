"""Core interfaces and base classes for the parser framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ParseResult:
    """Container for parse results with metadata.

    ``data`` is always a mapping of sheet name to DataFrame, whether
    one sheet or all sheets were requested. This is a deliberate v2
    breaking change: v1 returned a bare DataFrame for a single sheet
    and a dict otherwise, forcing every caller to branch.
    """

    data: dict[str, pd.DataFrame]
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata."""
        self.metadata[key] = value


class BaseParser(ABC):
    """Abstract base class for all parsers."""

    @abstractmethod
    def parse(self, file_path: str | Path, **kwargs: Any) -> ParseResult:
        """Parse a file and return the data.

        Args:
            file_path: Path to the file to parse.
            **kwargs: Additional parser-specific arguments.

        Returns:
            A ParseResult whose ``data`` maps sheet/format names to DataFrames.

        Raises:
            ParserError: If parsing fails.
        """
        raise NotImplementedError

    @abstractmethod
    def supports_format(self, file_path: str | Path) -> bool:
        """Check if this parser supports the given file format."""
        raise NotImplementedError

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions (e.g. ['.xlsx', '.xls'])."""
        raise NotImplementedError


class BaseWriter(ABC):
    """Abstract base class for all writers."""

    @abstractmethod
    def write(self, data: Any, file_path: str | Path, **kwargs: Any) -> None:
        """Write data to a file.

        Args:
            data: Data to write (a DataFrame or a mapping of names to DataFrames).
            file_path: Path where to write the file.
            **kwargs: Additional writer-specific arguments.

        Raises:
            ParserError: If writing fails.
        """
        raise NotImplementedError

    @abstractmethod
    def supports_format(self, file_path: str | Path) -> bool:
        """Check if this writer supports the given file format."""
        raise NotImplementedError

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for writing."""
        raise NotImplementedError
