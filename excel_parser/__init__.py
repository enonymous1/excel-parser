"""
Excel Parser - A modular file parsing library.

This package provides a flexible framework for parsing Excel
documents into pandas DataFrames, with validation, type detection,
and a command-line interface.
"""

from .core.factory import ParserFactory
from .core.interfaces import BaseParser, BaseWriter, ParseResult
from .exceptions import (
    ParseError,
    ParserError,
    ParserFileNotFoundError,
    UnsupportedFormatError,
    ValidationError,
)
from .parsers.excel_parser import ExcelParser
from .writers.excel_writer import ExcelWriter

__version__ = "2.0.0"
__all__ = [
    "ParserFactory",
    "BaseParser",
    "BaseWriter",
    "ParseResult",
    "ExcelParser",
    "ExcelWriter",
    "ParserError",
    "ParseError",
    "ParserFileNotFoundError",
    "UnsupportedFormatError",
    "ValidationError",
]
