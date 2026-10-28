# Changelog

All notable changes to this project are documented here.

> Renamed 2026-10-28 from `ss-python-parser` to `excel-parser`
> before publication (package `ss_python_parser` became
> `excel_parser`, CLI `ss-parser` became `excel-parser`). This is
> the only place the old name appears, as a history note.

## 2.0.0 — 2026-10-28

Breaking changes:

- `ExcelParser.parse()` now always returns a `ParseResult` whose `data`
  is a dict mapping sheet name to DataFrame, including for a single
  sheet. v1 returned a bare DataFrame for one sheet and a dict for
  several, forcing every caller to branch. `ParseResult` is now a
  dataclass.
- Packaging is a single `pyproject.toml` (PEP 621). `setup.py` and
  `requirements.txt` are removed. Python 3.8/3.9 support is dropped;
  Python 3.10–3.13 is supported.
- The `.xls` engine changed from xlrd (deprecated in pandas) to
  calamine. xlrd is no longer a dependency.

Added:

- `ExcelWriter` and `ParserFactory.create_writer()` / `register_writer()`.
  Writers are no longer an empty registry.
- CLI `sheets` command, `parse --output` (`.csv`, `.json`, `.xlsx`,
  `.xlsm`), and `parse --rows` for previews.
- `python -m excel_parser` entry point.
- `.xlsb` support as an opt-in extra: `pip install "excel-parser[xlsb]"`.
  Without pyxlsb, parsing a `.xlsb` file raises a `ParseError` naming
  the extra instead of failing inside pandas.
- Real MIT `LICENSE`, GitHub Actions CI (Ubuntu + Windows, Python
  3.10–3.13), `.gitattributes` (LF), and a `CHANGELOG.md`.

Fixed:

- `detect_data_types` no longer divides by zero on empty frames, no
  longer uses a bare `except`, and no longer lets the datetime check
  overwrite a numeric suggestion.
- `get_sheet_names` now closes its `ExcelFile`.
- `analyze` no longer silently analyzes the first sheet when the
  requested sheet is missing or when no sheet is given for a
  multi-sheet file; it errors and lists the available sheets.
- `ExcelParser` now selects the read engine explicitly by extension
  instead of letting pandas guess, and exception chaining (`from`)
  is preserved.
- The custom file-not-found exception is now named
  `ParserFileNotFoundError` so it no longer shadows the builtin
  `FileNotFoundError`. The old name remains as a backwards-compatible
  alias.
- `validate_dataframe` stores dtypes as strings so its result is
  JSON-serializable.
- Ruff-clean codebase; factory format names are case-insensitive and
  accept extensions such as `.xlsx`.

Removed:

- `dev-env.sh` (bash aliases and a `PYTHONPATH` hack). Install the
  package editable (`pip install -e ".[dev]"`) and use the `excel-parser`
  console script instead; commands are in the README.

## 1.0.0 / 0.1.0 (2026-02-18)

- Initial release: `ExcelParser` behind `ParserFactory`, validation
  and type-detection utilities, a `parse` / `analyze` / `formats`
  CLI, examples, and a sample workbook. Writers were declared but
  not implemented.
