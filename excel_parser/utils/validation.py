"""Data validation utilities."""

from typing import Any

import pandas as pd


def validate_dataframe(
    df: pd.DataFrame, required_columns: list[str] | None = None
) -> dict[str, Any]:
    """Validate a DataFrame and return validation results."""
    results: dict[str, Any] = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "info": {},
    }

    results["info"]["shape"] = df.shape
    results["info"]["columns"] = df.columns.tolist()
    # Store dtypes as strings so the result is JSON-serializable.
    results["info"]["dtypes"] = {
        str(col): str(df.iloc[:, i].dtype) for i, col in enumerate(df.columns)
    }

    if df.empty:
        results["warnings"].append("DataFrame is empty")

    if required_columns:
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            results["errors"].append(f"Missing required columns: {sorted(missing_columns)}")
            results["is_valid"] = False

    duplicate_columns = df.columns[df.columns.duplicated()].tolist()
    if duplicate_columns:
        results["warnings"].append(f"Duplicate column names found: {duplicate_columns}")

    null_columns = df.columns[df.isnull().all()].tolist()
    if null_columns:
        results["warnings"].append(f"Columns with all null values: {null_columns}")

    null_rows = df.index[df.isnull().all(axis=1)].tolist()
    if null_rows:
        results["info"]["null_rows_count"] = len(null_rows)
        if len(null_rows) > 10:
            results["warnings"].append(f"Found {len(null_rows)} rows with all null values")

    results["info"]["memory_usage_bytes"] = int(df.memory_usage(deep=True).sum())

    return results


def clean_dataframe(
    df: pd.DataFrame,
    drop_empty_rows: bool = True,
    drop_empty_columns: bool = True,
    drop_duplicates: bool = False,
    fill_na_value: Any | None = None,
) -> pd.DataFrame:
    """Clean a DataFrame by removing empty rows/columns and handling duplicates."""
    df_clean = df.copy()

    if drop_empty_rows:
        df_clean = df_clean.dropna(how="all")

    if drop_empty_columns:
        df_clean = df_clean.dropna(axis=1, how="all")

    if drop_duplicates:
        df_clean = df_clean.drop_duplicates()

    if fill_na_value is not None:
        df_clean = df_clean.fillna(fill_na_value)

    return df_clean


def detect_data_types(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Analyze and suggest data types for DataFrame columns.

    An empty frame yields 0.0 null percentages (no division by zero).
    A numeric suggestion is never overwritten by the datetime check:
    datetime is only considered for non-numeric, string-like columns.
    """
    results: dict[str, dict[str, Any]] = {}
    row_count = len(df)

    for position, column in enumerate(df.columns):
        col_data = df.iloc[:, position]
        non_null = col_data.dropna()

        analysis: dict[str, Any] = {
            "current_dtype": str(col_data.dtype),
            "null_count": int(col_data.isnull().sum()),
            "null_percentage": (
                float(col_data.isnull().sum() / row_count * 100) if row_count else 0.0
            ),
            "unique_count": int(col_data.nunique()),
            "suggested_dtype": str(col_data.dtype),
        }

        if not non_null.empty and pd.api.types.is_string_dtype(col_data.dtype):
            sample = non_null.head(100)
            numeric_count = 0
            for value in sample:
                try:
                    float(str(value).replace(",", ""))
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass

            if sample.size and numeric_count / sample.size > 0.8:
                analysis["suggested_dtype"] = "numeric"
                analysis["note"] = "Appears to contain numeric data stored as text"
            else:
                string_sample = [v for v in sample.head(10) if isinstance(v, str)]
                if string_sample:
                    try:
                        parsed = pd.to_datetime(
                            pd.Series(string_sample), errors="coerce", format="mixed"
                        )
                        if parsed.notna().mean() >= 0.8:
                            analysis["suggested_dtype"] = "datetime"
                            analysis["note"] = "Appears to contain date/time data"
                    except (ValueError, TypeError):
                        pass

        results[str(column)] = analysis

    return results
