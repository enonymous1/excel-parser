"""Factory for creating parsers and writers."""

from pathlib import Path

from ..core.interfaces import BaseParser, BaseWriter
from ..exceptions import UnsupportedFormatError
from ..parsers.excel_parser import ExcelParser
from ..writers.excel_writer import ExcelWriter


class ParserFactory:
    """Factory class for creating appropriate parsers and writers."""

    _parsers: dict[str, type[BaseParser]] = {
        "excel": ExcelParser,
    }

    _writers: dict[str, type[BaseWriter]] = {
        "excel": ExcelWriter,
    }

    @classmethod
    def _normalize_format_type(cls, format_type: str) -> str:
        return format_type.strip().lower().lstrip(".")

    @classmethod
    def _format_for_extension(
        cls, extension: str, registry: dict[str, type]
    ) -> str | None:
        extension = extension.lower()
        for format_type, klass in registry.items():
            if extension in klass().get_supported_extensions():
                return format_type
        return None

    @classmethod
    def create_parser(
        cls,
        format_type: str | None = None,
        file_path: str | Path | None = None,
    ) -> BaseParser:
        """Create a parser for the specified format or file.

        ``format_type`` is case-insensitive and may also be a file
        extension such as ``".xlsx"``. When only ``file_path`` is
        given, the format is detected from its extension.
        """
        if format_type:
            normalized = cls._normalize_format_type(format_type)
            if normalized in cls._parsers:
                return cls._parsers[normalized]()
            detected = cls._format_for_extension(f".{normalized}", cls._parsers)
            if detected is not None:
                return cls._parsers[detected]()
            raise UnsupportedFormatError(
                format_type, str(file_path) if file_path else None
            )

        if file_path:
            path = Path(file_path)
            detected = cls._format_for_extension(path.suffix, cls._parsers)
            if detected is not None:
                return cls._parsers[detected]()
            raise UnsupportedFormatError(
                f"File extension {path.suffix}", str(file_path)
            )

        raise ValueError("Either format_type or file_path must be provided")

    @classmethod
    def create_writer(
        cls,
        format_type: str | None = None,
        file_path: str | Path | None = None,
    ) -> BaseWriter:
        """Create a writer for the specified format or file."""
        if format_type:
            normalized = cls._normalize_format_type(format_type)
            if normalized in cls._writers:
                return cls._writers[normalized]()
            detected = cls._format_for_extension(f".{normalized}", cls._writers)
            if detected is not None:
                return cls._writers[detected]()
            raise UnsupportedFormatError(
                format_type, str(file_path) if file_path else None
            )

        if file_path:
            path = Path(file_path)
            detected = cls._format_for_extension(path.suffix, cls._writers)
            if detected is not None:
                return cls._writers[detected]()
            raise UnsupportedFormatError(
                f"File extension {path.suffix}", str(file_path)
            )

        raise ValueError("Either format_type or file_path must be provided")

    @classmethod
    def register_parser(cls, format_type: str, parser_class: type[BaseParser]) -> None:
        """Register a new parser for a format type."""
        if not (isinstance(parser_class, type) and issubclass(parser_class, BaseParser)):
            raise TypeError("parser_class must be a BaseParser subclass")
        cls._parsers[cls._normalize_format_type(format_type)] = parser_class

    @classmethod
    def register_writer(cls, format_type: str, writer_class: type[BaseWriter]) -> None:
        """Register a new writer for a format type."""
        if not (isinstance(writer_class, type) and issubclass(writer_class, BaseWriter)):
            raise TypeError("writer_class must be a BaseWriter subclass")
        cls._writers[cls._normalize_format_type(format_type)] = writer_class

    @classmethod
    def get_supported_formats(cls) -> dict[str, dict[str, list[str]]]:
        """Get all supported formats for parsing and writing."""
        parsers_info = {
            format_type: parser_class().get_supported_extensions()
            for format_type, parser_class in cls._parsers.items()
        }
        writers_info = {
            format_type: writer_class().get_supported_extensions()
            for format_type, writer_class in cls._writers.items()
        }
        return {"parsers": parsers_info, "writers": writers_info}
