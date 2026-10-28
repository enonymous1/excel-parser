"""Test validation and cleaning utilities."""

import json

import pandas as pd

from excel_parser.utils.validation import (
    clean_dataframe,
    detect_data_types,
    validate_dataframe,
)


class TestValidateDataframe:
    def test_empty_dataframe(self) -> None:
        result = validate_dataframe(pd.DataFrame())
        assert result["is_valid"] is True
        assert "DataFrame is empty" in result["warnings"]

    def test_missing_required_columns(self) -> None:
        df = pd.DataFrame({"A": [1, 2]})
        result = validate_dataframe(df, required_columns=["A", "B"])
        assert result["is_valid"] is False
        assert any("B" in error for error in result["errors"])

    def test_duplicate_and_null_columns(self) -> None:
        df = pd.DataFrame([[1, None], [2, None]], columns=["A", "A"])
        result = validate_dataframe(df)
        assert any("Duplicate" in w for w in result["warnings"])
        assert any("all null" in w for w in result["warnings"])

    def test_dtypes_are_json_serializable(self) -> None:
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        result = validate_dataframe(df)
        assert result["info"]["dtypes"]["A"] == "int64"
        assert result["info"]["dtypes"]["B"] in {"object", "str"}
        json.dumps(result["info"])

    def test_memory_usage_is_int(self) -> None:
        result = validate_dataframe(pd.DataFrame({"A": [1]}))
        assert isinstance(result["info"]["memory_usage_bytes"], int)


class TestCleanDataframe:
    def test_drops_empty_rows_and_columns(self) -> None:
        df = pd.DataFrame({"A": [1, None, 3], "B": [None, None, None], "C": [4, None, 6]})
        cleaned = clean_dataframe(df)
        assert list(cleaned.columns) == ["A", "C"]
        assert len(cleaned) == 2

    def test_drop_duplicates_and_fill(self) -> None:
        df = pd.DataFrame({"A": [1, 1, None]})
        cleaned = clean_dataframe(
            df, drop_empty_rows=False, drop_empty_columns=False,
            drop_duplicates=True, fill_na_value=0
        )
        assert cleaned["A"].tolist() == [1, 0]

    def test_original_is_not_mutated(self) -> None:
        df = pd.DataFrame({"A": [1, None]})
        clean_dataframe(df)
        assert df.isnull().sum().sum() == 1


class TestDetectDataTypes:
    def test_empty_dataframe_has_zero_null_percentage(self) -> None:
        assert detect_data_types(pd.DataFrame()) == {}

    def test_empty_column_has_zero_null_percentage(self) -> None:
        result = detect_data_types(pd.DataFrame({"A": pd.Series([], dtype=float)}))
        assert result["A"]["null_percentage"] == 0.0
        assert result["A"]["unique_count"] == 0

    def test_numeric_text_is_detected(self) -> None:
        df = pd.DataFrame({"Amount": ["1,000", "2,500", "3,750", "900"]})
        result = detect_data_types(df)
        assert result["Amount"]["suggested_dtype"] == "numeric"
        assert "numeric" in result["Amount"]["note"]

    def test_date_text_is_detected_and_numeric_is_not_overwritten(self) -> None:
        df = pd.DataFrame(
            {
                "Started": ["2022-01-15", "2020-03-10", "2019-07-22", "2021-11-05"],
                "Age": [28, 35, 42, 31],
            }
        )
        result = detect_data_types(df)
        assert result["Started"]["suggested_dtype"] == "datetime"
        assert result["Age"]["suggested_dtype"] == "int64"

    def test_plain_text_is_not_datetime(self) -> None:
        df = pd.DataFrame({"Name": ["Alice", "Bob", "Charlie", "Diana"]})
        result = detect_data_types(df)
        assert result["Name"]["suggested_dtype"] == result["Name"]["current_dtype"]
        assert "note" not in result["Name"]

    def test_null_percentage(self) -> None:
        df = pd.DataFrame({"A": [1, None, 3, None]})
        assert detect_data_types(df)["A"]["null_percentage"] == 50.0
