"""Test the CLI. main() returns exit codes; it never calls sys.exit."""

import json
from pathlib import Path

import pandas as pd

from excel_parser.cli import main

SAMPLE = Path(__file__).resolve().parent.parent / "sample_data.xlsx"


def _make_workbook(tmp_path: Path) -> Path:
    path = tmp_path / "book.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [28, 35]}).to_excel(
            writer, sheet_name="Employees", index=False
        )
        pd.DataFrame({"Month": ["Jan"], "Total": [100]}).to_excel(
            writer, sheet_name="Sales", index=False
        )
    return path


class TestCli:
    def test_no_command_prints_help(self, capsys: object) -> None:
        assert main([]) == 0
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "excel-parser" in captured.out or "usage" in captured.out.lower()

    def test_formats(self, capsys: object) -> None:
        assert main(["formats"]) == 0
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "excel" in captured.out
        assert ".xlsx" in captured.out

    def test_sheets(self, tmp_path: Path, capsys: object) -> None:
        book = _make_workbook(tmp_path)
        assert main(["sheets", str(book)]) == 0
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert captured.out.splitlines() == ["Employees", "Sales"]

    def test_parse_sample(self, capsys: object) -> None:
        assert main(["parse", str(SAMPLE)]) == 0
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "Employees" in captured.out
        assert "Sales" in captured.out

    def test_parse_preview_single_sheet(self, tmp_path: Path, capsys: object) -> None:
        book = _make_workbook(tmp_path)
        assert main(["parse", str(book), "--sheet", "Employees", "--preview"]) == 0
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "Alice" in captured.out

    def test_parse_missing_file_returns_one(self, capsys: object) -> None:
        assert main(["parse", "no_such_file.xlsx"]) == 1
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "Error" in captured.err

    def test_parse_output_json(self, tmp_path: Path) -> None:
        book = _make_workbook(tmp_path)
        output = tmp_path / "out.json"
        assert main(["parse", str(book), "--output", str(output)]) == 0
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["Employees"][0]["Name"] == "Alice"
        assert payload["Sales"][0]["Total"] == 100

    def test_parse_output_csv_requires_single_sheet(self, tmp_path: Path) -> None:
        book = _make_workbook(tmp_path)
        output = tmp_path / "out.csv"
        assert main(["parse", str(book), "--output", str(output)]) == 1
        assert not output.exists()
        output2 = tmp_path / "one.csv"
        assert (
            main(["parse", str(book), "--sheet", "Employees", "--output", str(output2)])
            == 0
        )
        assert "Alice" in output2.read_text(encoding="utf-8")

    def test_parse_output_xlsx_round_trip(self, tmp_path: Path) -> None:
        book = _make_workbook(tmp_path)
        output = tmp_path / "copy.xlsx"
        assert main(["parse", str(book), "--output", str(output)]) == 0
        assert main(["sheets", str(output)]) == 0

    def test_parse_output_unsupported(self, tmp_path: Path) -> None:
        book = _make_workbook(tmp_path)
        assert main(["parse", str(book), "--output", str(tmp_path / "out.txt")]) == 1

    def test_analyze_single_sheet(self, tmp_path: Path, capsys: object) -> None:
        book = _make_workbook(tmp_path)
        assert main(["analyze", str(book), "--sheet", "Employees"]) == 0
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "Validation" in captured.out
        assert "Age" in captured.out

    def test_analyze_multi_sheet_without_sheet_errors(self, tmp_path: Path) -> None:
        book = _make_workbook(tmp_path)
        assert main(["analyze", str(book)]) == 1

    def test_analyze_missing_sheet_errors(self, tmp_path: Path, capsys: object) -> None:
        book = _make_workbook(tmp_path)
        assert main(["analyze", str(book), "--sheet", "Nope"]) == 1
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "Nope" in captured.err
