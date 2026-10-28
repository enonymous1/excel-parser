"""Custom exceptions for the Excel Parser."""



class ParserError(Exception):
    """Base exception for parser-related errors."""

    def __init__(self, message: str, file_path: str | None = None) -> None:
        self.message = message
        self.file_path = file_path
        super().__init__(self.message)


class UnsupportedFormatError(ParserError):
    """Raised when an unsupported file format is encountered."""

    def __init__(self, format_type: str, file_path: str | None = None) -> None:
        message = f"Unsupported format: {format_type}"
        if file_path:
            message += f" for file: {file_path}"
        super().__init__(message, file_path)


class ParseError(ParserError):
    """Raised when parsing fails."""

    pass


class ValidationError(ParserError):
    """Raised when data validation fails."""

    pass


class ParserFileNotFoundError(ParserError):
    """Raised when the specified file cannot be found."""

    pass


# Backwards-compatible alias for the v1 name. Prefer
# ParserFileNotFoundError in new code; this alias shadows the builtin
# FileNotFoundError when imported explicitly, so do not import it
# unqualified into modules that also need the builtin.
FileNotFoundError = ParserFileNotFoundError
