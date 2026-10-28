"""Advanced example showing various Excel parsing options."""

import tempfile
from pathlib import Path

from excel_parser.parsers.excel_parser import ExcelParser
from excel_parser.utils.validation import (
    clean_dataframe,
    detect_data_types,
)
from excel_parser.writers.excel_writer import ExcelWriter

SAMPLE_FILE = Path(__file__).resolve().parent.parent / "sample_data.xlsx"


def demonstrate_sheet_operations(file_path: Path) -> None:
    """Demonstrate various sheet operations."""
    print("=== Sheet Operations ===")

    parser = ExcelParser()

    try:
        sheet_names = parser.get_sheet_names(file_path)
        print(f"Available sheets: {sheet_names}")
    except Exception as exc:  # noqa: BLE001 - example top level
        print(f"Could not read sheet names: {exc}")
        return

    if sheet_names:
        first_sheet = sheet_names[0]
        print(f"\nParsing specific sheet: {first_sheet}")
        result = parser.parse(file_path, sheet_name=first_sheet)
        print(f"Shape: {result.data[first_sheet].shape}")

    if len(sheet_names) > 1:
        sheets_to_parse = sheet_names[:2]
        print(f"\nParsing multiple sheets: {sheets_to_parse}")
        result = parser.parse(file_path, sheet_name=sheets_to_parse)
        for sheet_name, df in result.data.items():
            print(f"Sheet '{sheet_name}': {df.shape}")


def demonstrate_parsing_options(file_path: Path) -> None:
    """Demonstrate various parsing options."""
    print("\n=== Parsing Options ===")

    parser = ExcelParser()

    print("Getting preview (first 3 rows):")
    preview_result = parser.preview(file_path, nrows=3)
    for sheet_name, df in preview_result.data.items():
        print(f"Sheet '{sheet_name}' preview:")
        print(df)

    print("\nParsing with header on row 2 (index 1):")
    try:
        result = parser.parse(file_path, header=1, nrows=5)
        first_sheet_data = next(iter(result.data.values()))
        print(f"Columns: {list(first_sheet_data.columns)}")
        print(f"Shape: {first_sheet_data.shape}")
    except Exception as exc:  # noqa: BLE001 - example top level
        print(f"Error with custom header: {exc}")

    print("\nParsing only first 3 columns:")
    try:
        result = parser.parse(file_path, usecols=[0, 1, 2], nrows=5)
        first_sheet_data = next(iter(result.data.values()))
        print(f"Columns: {list(first_sheet_data.columns)}")
        print(f"Shape: {first_sheet_data.shape}")
    except Exception as exc:  # noqa: BLE001 - example top level
        print(f"Error with specific columns: {exc}")


def demonstrate_data_analysis(file_path: Path) -> None:
    """Demonstrate data analysis capabilities."""
    print("\n=== Data Analysis ===")

    parser = ExcelParser()
    result = parser.parse(file_path)

    sheet_name, df = next(iter(result.data.items()))
    print(f"Analyzing sheet: {sheet_name}")

    print("\n--- Data Type Analysis ---")
    type_analysis = detect_data_types(df)
    for column, analysis in type_analysis.items():
        print(f"Column '{column}':")
        print(f"  Current type: {analysis['current_dtype']}")
        print(f"  Suggested type: {analysis['suggested_dtype']}")
        print(f"  Null percentage: {analysis['null_percentage']:.1f}%")
        if "note" in analysis:
            print(f"  Note: {analysis['note']}")
        print()

    print("--- Data Cleaning ---")
    original_shape = df.shape
    cleaned_df = clean_dataframe(
        df,
        drop_empty_rows=True,
        drop_empty_columns=True,
        drop_duplicates=True,
    )
    print(f"Original shape: {original_shape}")
    print(f"After cleaning: {cleaned_df.shape}")

    numeric_columns = cleaned_df.select_dtypes(include=["number"]).columns
    if len(numeric_columns) > 0:
        print("\n--- Statistics for Numeric Columns ---")
        print(cleaned_df[numeric_columns].describe())


def demonstrate_writer(file_path: Path) -> None:
    """Demonstrate writing parsed data back to a workbook."""
    print("\n=== Writing ===")
    parser = ExcelParser()
    result = parser.parse(file_path, sheet_name="Employees")
    with tempfile.TemporaryDirectory() as tmp_dir:
        output = Path(tmp_dir) / "employees_copy.xlsx"
        ExcelWriter().write(result.data, output)
        round_tripped = parser.parse(output)
        print(f"Wrote {output.name}; re-read sheets: {list(round_tripped.data)}")


def main() -> None:
    """Demonstrate advanced Excel parsing features."""
    if not SAMPLE_FILE.exists():
        print(f"Sample file {SAMPLE_FILE} not found.")
        return

    try:
        demonstrate_sheet_operations(SAMPLE_FILE)
        demonstrate_parsing_options(SAMPLE_FILE)
        demonstrate_data_analysis(SAMPLE_FILE)
        demonstrate_writer(SAMPLE_FILE)
    except Exception as exc:  # noqa: BLE001 - example top level
        print(f"Error in demonstration: {exc}")


if __name__ == "__main__":
    main()
