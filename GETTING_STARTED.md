# Getting Started with Excel Parser

## Overview

Excel Parser is a modular Python library for parsing Excel documents into pandas DataFrames. It is structured so new formats can be added without changing callers: a factory returns a `BaseParser`, and every parser returns a `ParseResult`.

## Project Structure

```
excel-parser/
├── excel_parser/          # Main package
│   ├── __init__.py           # Package exports and __version__
│   ├── __main__.py           # `python -m excel_parser`
│   ├── cli.py                # Command-line interface (excel-parser)
│   ├── exceptions.py         # Custom exceptions
│   ├── core/                 # Interfaces, ParseResult, and factory
│   │   ├── __init__.py
│   │   ├── interfaces.py     # BaseParser, BaseWriter, ParseResult
│   │   └── factory.py        # ParserFactory
│   ├── parsers/              # Format-specific parsers
│   │   ├── __init__.py
│   │   └── excel_parser.py   # Excel parser implementation
│   ├── writers/              # Format-specific writers
│   │   ├── __init__.py
│   │   └── excel_writer.py   # Excel writer implementation
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── file_utils.py     # File operations
│       └── validation.py     # Data validation and type detection
├── tests/                    # Test suite (pytest)
├── examples/                 # Usage examples
├── sample_data.xlsx          # Sample file (fictional Employees/Sales data)
├── pyproject.toml            # Packaging, pytest, ruff, and mypy config
├── README.md                 # Project documentation
└── CHANGELOG.md              # Version history
```

## Key Features

1. **Excel Parsing**: `.xlsx`, `.xls`, `.xlsm`, and `.xlsb` files (`.xlsb` needs the `[xlsb]` extra)
2. **Multi-sheet Support**: Parse single sheets, multiple sheets, or all sheets; the result is always a dict of DataFrames
3. **Flexible Parsing Options**: Custom headers, column selection, row skipping; extra options forward to `pandas.read_excel`
4. **Data Validation**: Built-in validation and data quality checks
5. **Type Detection**: Automatic data type analysis and suggestions
6. **Writers**: Write a DataFrame or a dict of DataFrames back to `.xlsx` / `.xlsm`
7. **Command-line Interface**: `parse`, `analyze`, `sheets`, and `formats` commands, with `--output` export
8. **Extensible Architecture**: Register new parsers and writers with the factory
9. **Rich Metadata**: File size, sheet names, row/column counts, and the read engine used
10. **Error Handling**: Custom exceptions with chained causes; missing files, unsupported formats, and missing sheets are distinct errors

## Quick Start Examples

### Basic Usage

```python
from excel_parser import ParserFactory

parser = ParserFactory.create_parser("excel")
result = parser.parse("sample_data.xlsx")

for sheet_name, df in result.data.items():
    print(f"Sheet: {sheet_name}")
    print(df.head())
```

### Advanced Usage

```python
from excel_parser.parsers.excel_parser import ExcelParser
from excel_parser.utils.validation import validate_dataframe

parser = ExcelParser()
result = parser.parse("sample_data.xlsx", sheet_name="Employees")
df = result.data["Employees"]

validation = validate_dataframe(df)
if validation["is_valid"]:
    print("Data validation passed")
else:
    print("Validation errors:", validation["errors"])
```

### Command Line Usage

```bash
# Parse a file
python -m excel_parser parse sample_data.xlsx

# Parse a specific sheet
python -m excel_parser parse sample_data.xlsx --sheet Employees

# List sheets
python -m excel_parser sheets sample_data.xlsx

# Analyze data quality (single-sheet files, or name a sheet)
python -m excel_parser analyze sample_data.xlsx --sheet Sales

# List supported formats
python -m excel_parser formats
```

## Running the Project

### Set Up Environment

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

On Windows PowerShell, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

### Run Examples

```bash
python examples/basic_excel_parsing.py
python examples/advanced_excel_parsing.py
```

### Run Tests

```bash
python -m pytest tests/ -v
```

### Use the CLI

```bash
python -m excel_parser parse sample_data.xlsx
python -m excel_parser analyze sample_data.xlsx --sheet Employees
```

## Extending the Parser

### Adding a New Parser

1. Create a new parser class in `excel_parser/parsers/`
2. Implement the `BaseParser` interface
3. Register the parser in the factory (or call `ParserFactory.register_parser`)
4. Add tests

Example:

```python
from pathlib import Path
import pandas as pd

from excel_parser.core.interfaces import BaseParser, ParseResult


class CSVParser(BaseParser):
    def parse(self, file_path, **kwargs):
        df = pd.read_csv(file_path, **kwargs)
        return ParseResult(data={"Sheet1": df}, metadata={"parser_type": "csv"})

    def supports_format(self, file_path):
        return Path(file_path).suffix.lower() == ".csv"

    def get_supported_extensions(self):
        return [".csv"]
```

Note: `data` must be a dict, even for single-table formats. Use a fixed key such as `"Sheet1"` or the file stem, and document it.

### Development Tools

The project uses:

- **pytest**: Testing framework
- **ruff**: Linting and import sorting
- **mypy**: Type checking

## Sample Data

The project includes a sample Excel file (`sample_data.xlsx`) with two fictional sheets:

1. **Employees**: Names, departments, ages, salaries, start dates, and status
2. **Sales**: Monthly sales data for different products

A legacy `.xls` version of the same fictional data lives in `tests/fixtures/sample_data.xls` and is used by the test suite.

## Next Steps

1. **Add More Parsers**: CSV, JSON, XML (see the pattern above)
2. **Add Data Transformation**: Built-in data cleaning and transformation helpers
3. **Performance**: Streaming/chunked reads for very large workbooks
4. **Cloud Integration**: Support for cloud storage sources
