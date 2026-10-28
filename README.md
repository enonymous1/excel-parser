# Excel Parser

A modular Python library for parsing Excel workbooks into pandas DataFrames, with data validation, type detection, rich parse metadata, and a command-line interface.

`parse()` always returns every sheet as a dict of DataFrames, whether you asked for one sheet or all of them, so callers never have to branch on the return type.

## Install

```powershell
pip install .
```

With `.xlsb` support (optional, via pyxlsb):

```powershell
pip install ".[xlsb]"
```

For development:

```powershell
pip install -e ".[dev]"
```

Requires Python 3.10 or newer.

## Quick start

```python
from excel_parser import ParserFactory

parser = ParserFactory.create_parser("excel")
result = parser.parse("sample_data.xlsx")

for sheet_name, df in result.data.items():
    print(sheet_name, df.shape)
    print(df.head())

print(result.metadata)
print(result.warnings)
```

Parse one sheet, by name or by position:

```python
result = parser.parse("sample_data.xlsx", sheet_name="Employees")
employees = result.data["Employees"]

result = parser.parse("sample_data.xlsx", sheet_name=0)
```

Write data back out:

```python
from excel_parser import ExcelWriter

ExcelWriter().write(result.data, "copy.xlsx")
ExcelWriter().write(employees, "employees.xlsx", sheet_name="Employees")
```

## CLI

The install provides `excel-parser`. You can also run `python -m excel_parser`.

```powershell
excel-parser formats
excel-parser sheets report.xlsx
excel-parser parse report.xlsx --preview
excel-parser parse report.xlsx --sheet Sales --preview
excel-parser parse report.xlsx --output report.json
excel-parser parse report.xlsx --sheet Sales --output sales.csv
excel-parser analyze report.xlsx --sheet Employees
```

`parse --output` writes `.csv` (single sheet only, use `--sheet` for multi-sheet files), `.json` (all sheets), or `.xlsx` / `.xlsm`. `analyze` errors instead of guessing when a file has several sheets and no `--sheet` is given, or when the named sheet does not exist.

Exit codes: `0` on success, `1` on a parse or usage error, `2` on an argparse error such as an invalid `--rows` value.

## Formats and engines

| Extension | Read engine | Notes |
| :--- | :--- | :--- |
| `.xlsx`, `.xlsm` | openpyxl | Core dependency |
| `.xls` | calamine | Core dependency; xlrd was dropped in v2.0 (deprecated in pandas) |
| `.xlsb` | pyxlsb | Optional `[xlsb]` extra; without it, parsing raises a `ParseError` naming the extra |

Writers support `.xlsx` and `.xlsm` only.

## API

- `ParserFactory.create_parser(format_type=None, file_path=None)` — format names are case-insensitive and may be extensions (`"Excel"`, `".xlsx"`). With only a file path, the format is detected from the extension.
- `ParserFactory.create_writer(...)` — same lookup for writers.
- `ParserFactory.register_parser(format_type, parser_class)` / `register_writer(...)` — register a `BaseParser` / `BaseWriter` subclass under a new name.
- `ExcelParser.parse(file_path, sheet_name=None, header=0, index_col=None, usecols=None, dtype=None, na_values=None, keep_default_na=True, skiprows=None, nrows=None, engine=None, **kwargs)` — extra keyword arguments are forwarded to `pandas.read_excel`. An explicit `engine` overrides the extension mapping.
- `ExcelParser.get_sheet_names(file_path)` — sheet names without parsing data.
- `ExcelParser.preview(file_path, sheet_name=None, nrows=5)` — first rows of each requested sheet.
- `ParseResult` — dataclass with `data` (dict of DataFrames), `metadata` (file path, size, extension, parser type, engine, sheet names/count, total rows/columns), and `warnings` (empty sheets, all-null columns).
- `validate_dataframe(df, required_columns=None)`, `clean_dataframe(df, ...)`, `detect_data_types(df)` in `excel_parser.utils.validation`.
- `get_file_extension`, `validate_file_exists`, `get_file_size`, `format_file_size`, `find_files_by_extension`, `ensure_directory_exists` in `excel_parser.utils.file_utils`.
- Exceptions in `excel_parser.exceptions`: `ParserError`, `ParseError`, `UnsupportedFormatError`, `ValidationError`, `ParserFileNotFoundError`. The v1 name `FileNotFoundError` remains as an alias for `ParserFileNotFoundError`.

Adding a new parser: implement `BaseParser` in `excel_parser/parsers/`, return a `ParseResult` with dict data and the same metadata keys, register it with `ParserFactory.register_parser()`, and add tests. See `.github/copilot-instructions.md` for the conventions.

## Examples

```powershell
python examples/basic_excel_parsing.py
python examples/advanced_excel_parsing.py
```

Both resolve `sample_data.xlsx` relative to the repository, so they run from any working directory. The sample workbook has two fictional sheets, Employees and Sales.

## Development

```powershell
pytest
ruff check excel_parser tests examples
mypy excel_parser
```

CI runs the same three gates on Ubuntu and Windows, Python 3.10–3.13.

## Migrating from v1

v2 is a breaking release; see [CHANGELOG.md](CHANGELOG.md). The main change: `parse()` data is always a dict. If your v1 code did `df = result.data`, change it to `df = result.data["SheetName"]` or iterate `result.data.items()`. Packaging moved from `setup.py` + `requirements.txt` to a single `pyproject.toml`, and `.xls` now reads via calamine instead of xlrd.

## License

MIT License. See [LICENSE](LICENSE).
