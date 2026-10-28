"""Test file utilities."""

from pathlib import Path

import pytest

from excel_parser.exceptions import ParserFileNotFoundError
from excel_parser.utils.file_utils import (
    ensure_directory_exists,
    find_files_by_extension,
    format_file_size,
    get_file_extension,
    get_file_size,
    validate_file_exists,
)


class TestFileUtils:
    def test_get_file_extension(self) -> None:
        assert get_file_extension("data.XLSX") == ".xlsx"
        assert get_file_extension(Path("no-ext")) == ""

    def test_validate_file_exists(self, tmp_path: Path) -> None:
        path = tmp_path / "f.txt"
        path.write_text("hi")
        assert validate_file_exists(path) == path
        with pytest.raises(ParserFileNotFoundError):
            validate_file_exists(tmp_path / "missing.txt")
        with pytest.raises(ValueError, match="not a file"):
            validate_file_exists(tmp_path)

    def test_get_file_size(self, tmp_path: Path) -> None:
        path = tmp_path / "f.bin"
        path.write_bytes(b"12345")
        assert get_file_size(path) == 5
        with pytest.raises(ParserFileNotFoundError):
            get_file_size(tmp_path / "missing.bin")

    def test_format_file_size(self) -> None:
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        with pytest.raises(ValueError):
            format_file_size(-1)

    def test_find_files_by_extension_is_sorted(self, tmp_path: Path) -> None:
        (tmp_path / "b.xlsx").write_bytes(b"x")
        (tmp_path / "a.xlsx").write_bytes(b"x")
        (tmp_path / "c.txt").write_text("x")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "d.xlsx").write_bytes(b"x")
        assert find_files_by_extension(tmp_path, [".xlsx"]) == [
            tmp_path / "a.xlsx",
            tmp_path / "b.xlsx",
            tmp_path / "sub" / "d.xlsx",
        ]
        assert find_files_by_extension(tmp_path, [".xlsx"], recursive=False) == [
            tmp_path / "a.xlsx",
            tmp_path / "b.xlsx",
        ]

    def test_find_files_missing_directory(self, tmp_path: Path) -> None:
        with pytest.raises(ParserFileNotFoundError):
            find_files_by_extension(tmp_path / "missing", [".xlsx"])

    def test_ensure_directory_exists(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b"
        assert ensure_directory_exists(nested) == nested
        assert nested.is_dir()
        assert ensure_directory_exists(nested) == nested
