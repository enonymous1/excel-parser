"""Command-line interface for Excel Parser.

``main()`` returns an exit code instead of calling ``sys.exit`` so it
can be tested directly. Only the ``__main__`` block and the installed
console script turn that code into a process exit.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .core.factory import ParserFactory
from .core.interfaces import ParseResult
from .exceptions import ParseError, ParserError
from .utils.file_utils import format_file_size, get_file_size
from .utils.validation import detect_data_types, validate_dataframe


def _write_output(result: ParseResult, output: str) -> None:
    output_path = Path(output)
    suffix = output_path.suffix.lower()

    if suffix == ".csv":
        if len(result.data) != 1:
            sheets = ", ".join(result.data)
            raise ParseError(
                f"CSV output requires a single sheet; file has: {sheets}. "
                "Use --sheet to select one."
            )
        df = next(iter(result.data.values()))
        df.to_csv(output_path, index=False)
    elif suffix == ".json":
        payload = {
            name: json.loads(df.to_json(orient="records", date_format="iso"))
            for name, df in result.data.items()
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    elif suffix in (".xlsx", ".xlsm"):
        writer = ParserFactory.create_writer(file_path=output_path)
        writer.write(result.data, output_path)
    else:
        raise ParseError(
            f"Unsupported output format: {suffix} (use .csv, .json, .xlsx, or .xlsm)"
        )


def _print_result(result: ParseResult, file_path: str, preview_only: bool) -> None:
    heading = "Preview of" if preview_only else "Parsed"
    print(f"{heading} {file_path}")
    print("\nFile Information:")
    print(f"   Size: {format_file_size(get_file_size(file_path))}")
    for key, value in result.metadata.items():
        if key != "file_path":
            print(f"   {key.replace('_', ' ').title()}: {value}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"   - {warning}")

    print(f"\nSheets Found: {len(result.data)}")
    for sheet_name, df in result.data.items():
        print(f"\n   Sheet: {sheet_name}")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        if not df.empty:
            print("\n   Data preview:")
            print(df.head(5).to_string(index=False))


def parse_file(
    file_path: str,
    sheet_name: str | None = None,
    preview_only: bool = False,
    rows: int = 5,
    output: str | None = None,
) -> int:
    """Parse a file, display results, and optionally write output."""
    try:
        parser = ParserFactory.create_parser(file_path=file_path)
        if preview_only:
            if hasattr(parser, "preview"):
                result = parser.preview(file_path, sheet_name=sheet_name, nrows=rows)
            else:
                result = parser.parse(file_path, sheet_name=sheet_name, nrows=rows)
        else:
            result = parser.parse(file_path, sheet_name=sheet_name)
        _print_result(result, file_path, preview_only)
        if output:
            _write_output(result, output)
            print(f"\nWrote {output}")
        return 0
    except ParserError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def analyze_file(file_path: str, sheet_name: str | None = None) -> int:
    """Analyze a file and provide detailed information."""
    try:
        parser = ParserFactory.create_parser(file_path=file_path)
        result = parser.parse(file_path, sheet_name=sheet_name)

        if sheet_name is not None and sheet_name not in result.data:
            available = ", ".join(result.data)
            raise ParseError(
                f"Sheet '{sheet_name}' not found. Available sheets: {available}"
            )
        if sheet_name is None and len(result.data) > 1:
            available = ", ".join(result.data)
            raise ParseError(
                f"File has multiple sheets ({available}); use --sheet to select one."
            )

        name, df = next(iter(result.data.items()))
        print(f"Analysis of {file_path} (sheet: {name})")

        validation = validate_dataframe(df)
        print(f"\nValidation: {'Passed' if validation['is_valid'] else 'Failed'}")
        if validation["errors"]:
            print("   Errors:")
            for error in validation["errors"]:
                print(f"   - {error}")
        if validation["warnings"]:
            print("   Warnings:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")

        print("\nData Type Analysis:")
        type_analysis = detect_data_types(df)
        for column, analysis in type_analysis.items():
            print(f"   {column}:")
            print(f"     Current: {analysis['current_dtype']}")
            print(f"     Suggested: {analysis['suggested_dtype']}")
            print(f"     Null %: {analysis['null_percentage']:.1f}%")
            if "note" in analysis:
                print(f"     Note: {analysis['note']}")

        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            print("\nNumeric Statistics:")
            print(df[numeric_cols].describe().round(2).to_string())
        return 0
    except ParserError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def list_sheets(file_path: str) -> int:
    """List the sheet names in a file, one per line."""
    try:
        parser = ParserFactory.create_parser(file_path=file_path)
        if not hasattr(parser, "get_sheet_names"):
            raise ParseError("This parser does not support listing sheet names")
        names: list[str] = parser.get_sheet_names(file_path)
        for name in names:
            print(name)
        return 0
    except ParserError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def list_supported_formats() -> int:
    """List all supported formats."""
    formats = ParserFactory.get_supported_formats()

    print("Supported Formats:")
    print("\nParsers (Read):")
    for format_type, extensions in formats["parsers"].items():
        print(f"   {format_type}: {', '.join(extensions)}")

    print("\nWriters (Write):")
    if formats["writers"]:
        for format_type, extensions in formats["writers"].items():
            print(f"   {format_type}: {', '.join(extensions)}")
    else:
        print("   (Writers not implemented yet)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="excel-parser",
        description="Excel Parser - Parse and analyze Excel files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  excel-parser parse data.xlsx                    # Parse Excel file
  excel-parser parse data.xlsx --sheet Sheet1     # Parse specific sheet
  excel-parser parse data.xlsx --preview          # Show preview only
  excel-parser parse data.xlsx --output out.json  # Parse and export as JSON
  excel-parser analyze data.xlsx                  # Detailed analysis
  excel-parser sheets data.xlsx                   # List sheet names
  excel-parser formats                            # List supported formats
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    parse_parser = subparsers.add_parser("parse", help="Parse a file")
    parse_parser.add_argument("file", help="Path to the file to parse")
    parse_parser.add_argument("--sheet", help="Sheet name (for Excel files)")
    parse_parser.add_argument("--preview", action="store_true", help="Show preview only")
    parse_parser.add_argument(
        "--rows", type=int, default=5, help="Rows to preview (with --preview)"
    )
    parse_parser.add_argument(
        "--output", help="Write parsed data to .csv, .json, .xlsx, or .xlsm"
    )

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a file in detail")
    analyze_parser.add_argument("file", help="Path to the file to analyze")
    analyze_parser.add_argument("--sheet", help="Sheet name (for Excel files)")

    sheets_parser = subparsers.add_parser("sheets", help="List sheet names in a file")
    sheets_parser.add_argument("file", help="Path to the file")

    subparsers.add_parser("formats", help="List supported formats")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "parse":
        if args.rows < 1:
            parser.error("--rows must be at least 1")
        return parse_file(args.file, args.sheet, args.preview, args.rows, args.output)
    if args.command == "analyze":
        return analyze_file(args.file, args.sheet)
    if args.command == "sheets":
        return list_sheets(args.file)
    if args.command == "formats":
        return list_supported_formats()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
