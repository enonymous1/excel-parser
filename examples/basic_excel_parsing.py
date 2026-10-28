"""Basic example of using the Excel Parser to read Excel files."""

from pathlib import Path

from excel_parser import ParserFactory
from excel_parser.utils.validation import validate_dataframe

SAMPLE_FILE = Path(__file__).resolve().parent.parent / "sample_data.xlsx"


def main() -> None:
    """Demonstrate basic Excel parsing functionality."""
    if not SAMPLE_FILE.exists():
        print(f"Sample file {SAMPLE_FILE} not found.")
        return

    try:
        parser = ParserFactory.create_parser("excel")
        print(f"Parsing Excel file: {SAMPLE_FILE}")
        result = parser.parse(SAMPLE_FILE)

        print("\n=== File Metadata ===")
        for key, value in result.metadata.items():
            print(f"{key}: {value}")

        if result.warnings:
            print("\n=== Warnings ===")
            for warning in result.warnings:
                print(f"  - {warning}")

        print(f"\n=== Found {len(result.data)} sheets ===")
        for sheet_name, df in result.data.items():
            print(f"\nSheet: {sheet_name}")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("\nFirst 3 rows:")
            print(df.head(3))

            validation_result = validate_dataframe(df)
            if not validation_result["is_valid"]:
                print("Validation errors found:")
                for error in validation_result["errors"]:
                    print(f"   - {error}")
            if validation_result["warnings"]:
                print("Validation warnings:")
                for warning in validation_result["warnings"]:
                    print(f"   - {warning}")
            if validation_result["is_valid"] and not validation_result["warnings"]:
                print("Data validation passed!")
    except Exception as exc:  # noqa: BLE001 - example top level
        print(f"Error parsing file: {exc}")


if __name__ == "__main__":
    main()
