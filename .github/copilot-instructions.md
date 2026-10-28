# GitHub Copilot / AI Agents — Project Guide

This file helps AI coding agents become productive when working on this repository. It documents the project's architecture, conventions, workflows, and useful examples you can use to make safe and focused code changes.

## Big picture

- This package (`excel_parser`) is a modular parsing library with four clear layers:
  1. core: base interfaces, the `ParseResult` dataclass, and a `ParserFactory` (see `excel_parser/core/interfaces.py` and `excel_parser/core/factory.py`).
  2. parsers: format-specific implementations (currently `ExcelParser` in `excel_parser/parsers/excel_parser.py`).
  3. writers: format-specific implementations (currently `ExcelWriter` in `excel_parser/writers/excel_writer.py`).
  4. utils: helper functions for file I/O and validation (`excel_parser/utils/`) and the top-level CLI (`excel_parser/cli.py`).

Data flow: callers (CLI, external code, tests) ask `ParserFactory` for a parser by `format_type` or `file_path`. `ParserFactory` returns a `BaseParser` instance. Parsers return a `ParseResult` object with `.data` (always a dict mapping sheet name to DataFrame), `.metadata`, and `.warnings`.

Why this structure: the factory pattern enables adding new formats without changing callers — register new `BaseParser` implementations in `ParserFactory`.

## Key files & responsibilities

- `excel_parser/core/interfaces.py` — defines `BaseParser`, `BaseWriter` and `ParseResult` (behavior and expected return shape).
- `excel_parser/core/factory.py` — `ParserFactory` and registration helpers; format names are case-insensitive and may be extensions.
- `excel_parser/parsers/excel_parser.py` — reference parser implementation. Use this as the baseline pattern to create new parsers. It selects the pandas read engine explicitly by extension (openpyxl / calamine / pyxlsb).
- `excel_parser/writers/excel_writer.py` — reference writer implementation.
- `excel_parser/cli.py` — CLI entrypoint; `main()` returns an exit code and never calls `sys.exit`, so tests can call it directly. Shows how consumers call parsers and how results are displayed.
- `excel_parser/utils/` — validation utilities and file helpers used across parsers/CLI.
- `excel_parser/exceptions.py` — canonical exceptions (`ParserError`, `UnsupportedFormatError`, `ParseError`, `ParserFileNotFoundError`). The v1 name `FileNotFoundError` is a backwards-compatible alias; prefer `ParserFileNotFoundError` in new code.

## Developer workflows & commands

- Install editable: `pip install -e ".[dev]"` (add `,xlsb` for `.xlsb` support: `pip install -e ".[dev,xlsb]"`).
- Run tests (project uses pytest): `python -m pytest tests/ -v`. Tests use `tmp_path` and pandas to write test files; the only committed binary fixtures are `sample_data.xlsx` and `tests/fixtures/sample_data.xls`, both fictional data.
- Lint: `ruff check excel_parser tests examples`
- Static type checks: `mypy excel_parser`
- Run CLI: `python -m excel_parser parse <file>` or `excel-parser parse <file>` once installed.

## Project-specific patterns & conventions

- Parser basics — follow the Excel parser pattern:
  - Implement `BaseParser` methods: `parse`, `supports_format`, `get_supported_extensions`.
  - Return `ParseResult(data, metadata, warnings)` from `parse`, with `data` always a dict, even for a single table.
  - Use `excel_parser/exceptions.py` for consistent error handling. Wrap lower-level failures as `ParseError` with `from exc` so the cause is preserved; re-raise `ParserError` subclasses unwrapped.
  - `ExcelParser` uses `pandas.read_excel()` with an explicit engine and adds metadata (file size, sheet names, counts, engine) — match this metadata format in other parser implementations.
- Factory registration — to add a new parser:
  - Create a new parser in `excel_parser/parsers/` implementing `BaseParser`.
  - Add a mapping to `_parsers` in `ParserFactory`, or call `ParserFactory.register_parser()` at import time from a top-level module.
  - Ensure tests assert `ParserFactory.create_parser(file_path=<file>)` returns the correct parser.
- Writer basics — follow the Excel writer pattern:
  - Implement `BaseWriter.write` accepting a DataFrame (one sheet) or a dict of DataFrames (one sheet per key). Reject a `sheet_name` argument when data is a dict.
- CLI integration — parsers may expose `preview` and `get_sheet_names`; if not present, the CLI falls back to `parse` with `nrows`. CLI helpers return exit codes; only `main()`'s caller turns them into a process exit.
- Tests rely on `tmp_path` and `pandas` to write test files; avoid changing those patterns unless you update tests.
- Packaging is a single `pyproject.toml` (PEP 621, setuptools). Do not reintroduce `setup.py` or `requirements.txt`. Python floor is 3.10.

## Integration points & external dependencies

- Pandas: Excel parsing uses `pandas.read_excel` with an explicit engine. Keep options and semantics intact (kwargs are forwarded). If you add optional arguments in parsers, ensure the CLI and factory remain consistent.
- Engines: openpyxl for `.xlsx`/`.xlsm`, calamine for `.xls`, pyxlsb for `.xlsb` (optional `[xlsb]` extra). Do not reintroduce xlrd; it is deprecated in pandas.
- Writers: `ExcelWriter` uses `pandas.ExcelWriter` with the openpyxl engine and supports `.xlsx`/`.xlsm`.

## Typical tasks for agents — examples

- Add a CSV parser:
  - Create: `excel_parser/parsers/csv_parser.py` implementing `BaseParser`.
  - Implement `parse` using `pandas.read_csv` and convert to `ParseResult` with dict data and metadata similar to `ExcelParser`.
  - Add unit tests in `tests/test_csv_parser.py`.
  - Update `ParserFactory._parsers["csv"] = CSVParser` and add documentation to `README.md`.

- Add a writer:
  - Implement the `BaseWriter` interface, add `excel_parser/writers/<format>_writer.py`, and add it to `ParserFactory._writers`.
  - Add a CLI `--output` extension or command to write files, and add round-trip tests through the parser.

## Common pitfalls & notes

- `ParseResult.data` is always a dict. Do not return a bare DataFrame for a single sheet; that was the v1 behavior and was changed deliberately in v2.
- `ParserFactory.create_parser(file_path=...)` inspects the suffix and iterates `_parsers`; ensure `get_supported_extensions()` returns lowercase extensions with a leading dot.
- Use `ParseResult.metadata` keys as the project expects: `file_path`, `file_size`, `file_extension`, `parser_type`, `engine`, `sheet_names`, `sheet_count`, `total_rows`, `total_columns`.
- `detect_data_types` must not divide by the row count on an empty frame, and a datetime suggestion must never overwrite a numeric one.
- Do not invent new top-level config files; packaging and tool config live in `pyproject.toml` only.
- Keep line endings LF (`.gitattributes` enforces it) and keep the codebase ruff-clean and mypy-clean under the `pyproject.toml` settings.
