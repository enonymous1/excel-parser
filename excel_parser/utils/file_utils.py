"""File-related utility functions."""

from pathlib import Path

from ..exceptions import ParserFileNotFoundError


def get_file_extension(file_path: str | Path) -> str:
    """Get the file extension from a file path (including the dot)."""
    return Path(file_path).suffix.lower()


def validate_file_exists(file_path: str | Path) -> Path:
    """Validate that a file exists and return a Path object."""
    path = Path(file_path)
    if not path.exists():
        raise ParserFileNotFoundError(f"File not found: {path}", str(path))
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    return path


def get_file_size(file_path: str | Path) -> int:
    """Get the size of a file in bytes."""
    return validate_file_exists(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """Format a file size in human-readable form (e.g. "1.5 MB")."""
    if size_bytes < 0:
        raise ValueError("size_bytes must not be negative")
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    i = 0
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def find_files_by_extension(
    directory: str | Path,
    extensions: list[str],
    recursive: bool = True,
) -> list[Path]:
    """Find files with the given extensions, sorted by path."""
    directory_path = Path(directory)
    if not directory_path.exists():
        raise ParserFileNotFoundError(
            f"Directory not found: {directory_path}", str(directory_path)
        )
    extensions_lower = [ext.lower() for ext in extensions]

    pattern = "**/*" if recursive else "*"
    found = [
        file_path
        for file_path in directory_path.glob(pattern)
        if file_path.is_file() and file_path.suffix.lower() in extensions_lower
    ]
    return sorted(found)


def ensure_directory_exists(directory: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path
