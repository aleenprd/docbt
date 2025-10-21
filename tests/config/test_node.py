"""Tests for node.py module."""

import pandas as pd

from docbt.config.node import (
    generate_column_info,
    generate_number_stats,
    generate_text_stats,
)


class TestGenerateColumnInfo:
    """Test cases for generate_column_info function."""

    def test_basic_dataframe(self):
        """Test with a basic DataFrame containing different data types."""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
                "age": [25, 30, 35, 40, 45],
                "salary": [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
            }
        )

        result = generate_column_info(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4  # 4 columns
        assert list(result.columns) == [
            "Column",
            "Data Type",
            "Non-Null Count",
            "Null Count",
            "Unique Values",
        ]

        # Check column names are present
        assert set(result["Column"]) == {"id", "name", "age", "salary"}

        # Check all non-null counts are 5
        assert all(result["Non-Null Count"] == 5)

        # Check all null counts are 0
        assert all(result["Null Count"] == 0)

    def test_dataframe_with_nulls(self):
        """Test with a DataFrame containing null values."""
        df = pd.DataFrame(
            {
                "col1": [1, 2, None, 4, 5],
                "col2": ["a", None, "c", None, "e"],
                "col3": [1.1, 2.2, 3.3, None, 5.5],
            }
        )

        result = generate_column_info(df)

        # Check non-null counts
        col1_info = result[result["Column"] == "col1"].iloc[0]
        assert col1_info["Non-Null Count"] == 4
        assert col1_info["Null Count"] == 1

        col2_info = result[result["Column"] == "col2"].iloc[0]
        assert col2_info["Non-Null Count"] == 3
        assert col2_info["Null Count"] == 2

        col3_info = result[result["Column"] == "col3"].iloc[0]
        assert col3_info["Non-Null Count"] == 4
        assert col3_info["Null Count"] == 1

    def test_unique_values_count(self):
        """Test unique values counting."""
        df = pd.DataFrame(
            {
                "unique_col": [1, 2, 3, 4, 5],
                "duplicate_col": [1, 1, 2, 2, 3],
                "all_same": [1, 1, 1, 1, 1],
            }
        )

        result = generate_column_info(df)

        unique_info = result[result["Column"] == "unique_col"].iloc[0]
        assert unique_info["Unique Values"] == 5

        dup_info = result[result["Column"] == "duplicate_col"].iloc[0]
        assert dup_info["Unique Values"] == 3

        same_info = result[result["Column"] == "all_same"].iloc[0]
        assert same_info["Unique Values"] == 1

    def test_unique_values_limit_for_object_columns(self):
        """Test that object columns with 100+ unique values show '100+'."""
        # Create a DataFrame with an object column with > 100 unique values
        df = pd.DataFrame(
            {
                "many_values": [f"value_{i}" for i in range(150)],
                "few_values": ["a", "b", "c"] * 50,
            }
        )

        result = generate_column_info(df)

        many_info = result[result["Column"] == "many_values"].iloc[0]
        assert many_info["Unique Values"] == "100+"

        few_info = result[result["Column"] == "few_values"].iloc[0]
        assert few_info["Unique Values"] == 3

    def test_numeric_column_no_limit(self):
        """Test that numeric columns show actual count even if > 100."""
        df = pd.DataFrame(
            {
                "numeric_col": list(range(150)),
            }
        )

        result = generate_column_info(df)

        numeric_info = result[result["Column"] == "numeric_col"].iloc[0]
        assert numeric_info["Unique Values"] == 150

    def test_data_types_displayed(self):
        """Test that data types are correctly displayed."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
                "bool_col": [True, False, True],
            }
        )

        result = generate_column_info(df)

        int_info = result[result["Column"] == "int_col"].iloc[0]
        assert "int" in int_info["Data Type"]

        float_info = result[result["Column"] == "float_col"].iloc[0]
        assert "float" in float_info["Data Type"]

        str_info = result[result["Column"] == "str_col"].iloc[0]
        assert "object" in str_info["Data Type"]

        bool_info = result[result["Column"] == "bool_col"].iloc[0]
        assert "bool" in bool_info["Data Type"]

    def test_empty_dataframe(self):
        """Test with an empty DataFrame."""
        df = pd.DataFrame()

        result = generate_column_info(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_single_column_dataframe(self):
        """Test with a single column DataFrame."""
        df = pd.DataFrame({"single_col": [1, 2, 3, 4, 5]})

        result = generate_column_info(df)

        assert len(result) == 1
        assert result["Column"].iloc[0] == "single_col"


class TestGenerateNumberStats:
    """Test cases for generate_number_stats function."""

    def test_numeric_columns_only(self):
        """Test with DataFrame containing only numeric columns."""
        df = pd.DataFrame(
            {
                "col1": [1, 2, 3, 4, 5],
                "col2": [10.5, 20.5, 30.5, 40.5, 50.5],
                "col3": [100, 200, 300, 400, 500],
            }
        )

        result = generate_number_stats(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 3  # 3 numeric columns
        assert "col1" in result.columns
        assert "col2" in result.columns
        assert "col3" in result.columns

        # Check standard stats are present
        assert "mean" in result.index
        assert "std" in result.index
        assert "min" in result.index
        assert "max" in result.index
        assert "50%" in result.index  # median

    def test_mixed_columns(self):
        """Test with DataFrame containing mixed data types."""
        df = pd.DataFrame(
            {
                "numeric1": [1, 2, 3, 4, 5],
                "text": ["a", "b", "c", "d", "e"],
                "numeric2": [10.5, 20.5, 30.5, 40.5, 50.5],
                "bool": [True, False, True, False, True],
            }
        )

        result = generate_number_stats(df)

        # Should only include numeric columns
        assert len(result.columns) == 2
        assert "numeric1" in result.columns
        assert "numeric2" in result.columns
        assert "text" not in result.columns
        assert "bool" not in result.columns

    def test_no_numeric_columns(self):
        """Test with DataFrame containing no numeric columns."""
        df = pd.DataFrame(
            {
                "text1": ["a", "b", "c"],
                "text2": ["x", "y", "z"],
            }
        )

        result = generate_number_stats(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert len(result.columns) == 0

    def test_with_null_values(self):
        """Test numeric stats with null values."""
        df = pd.DataFrame(
            {
                "col1": [1, 2, None, 4, 5],
                "col2": [10.5, None, 30.5, None, 50.5],
            }
        )

        result = generate_number_stats(df)

        assert isinstance(result, pd.DataFrame)
        assert "col1" in result.columns
        assert "col2" in result.columns

        # Check that stats are calculated (pandas describe handles NaN)
        assert not pd.isna(result["col1"]["mean"])
        assert not pd.isna(result["col2"]["mean"])

    def test_empty_dataframe(self):
        """Test with an empty DataFrame."""
        df = pd.DataFrame()

        result = generate_number_stats(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_integer_and_float_columns(self):
        """Test with both integer and float columns."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3, 4, 5],
                "float_col": [1.1, 2.2, 3.3, 4.4, 5.5],
            }
        )

        result = generate_number_stats(df)

        assert "int_col" in result.columns
        assert "float_col" in result.columns

        # Verify mean calculations
        assert result["int_col"]["mean"] == 3.0
        assert abs(result["float_col"]["mean"] - 3.3) < 0.01


class TestGenerateTextStats:
    """Test cases for generate_text_stats function."""

    def test_text_columns_only(self):
        """Test with DataFrame containing only text columns."""
        df = pd.DataFrame(
            {
                "col1": ["a", "b", "c", "a", "b"],
                "col2": ["x", "y", "z", "x", "x"],
            }
        )

        result = generate_text_stats(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # 2 text columns
        assert list(result.columns) == ["Column", "Unique Values", "Most Frequent", "Frequency"]

        # Check col1 stats
        col1_stats = result[result["Column"] == "col1"].iloc[0]
        assert col1_stats["Unique Values"] == 3
        assert col1_stats["Most Frequent"] in ["a", "b"]  # Both appear twice
        assert col1_stats["Frequency"] == 2

        # Check col2 stats
        col2_stats = result[result["Column"] == "col2"].iloc[0]
        assert col2_stats["Unique Values"] == 3
        assert col2_stats["Most Frequent"] == "x"
        assert col2_stats["Frequency"] == 3

    def test_mixed_columns(self):
        """Test with DataFrame containing mixed data types."""
        df = pd.DataFrame(
            {
                "text": ["a", "b", "c", "a", "b"],
                "numeric": [1, 2, 3, 4, 5],
                "another_text": ["x", "y", "z", "x", "x"],
            }
        )

        result = generate_text_stats(df)

        # Should only include text/object columns
        assert len(result) == 2
        assert set(result["Column"]) == {"text", "another_text"}

    def test_no_text_columns(self):
        """Test with DataFrame containing no text columns."""
        df = pd.DataFrame(
            {
                "numeric1": [1, 2, 3],
                "numeric2": [4.5, 5.5, 6.5],
            }
        )

        result = generate_text_stats(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_single_text_column(self):
        """Test with a single text column."""
        df = pd.DataFrame(
            {
                "text_col": ["apple", "banana", "apple", "cherry", "apple"],
            }
        )

        result = generate_text_stats(df)

        assert len(result) == 1
        stats = result.iloc[0]
        assert stats["Column"] == "text_col"
        assert stats["Unique Values"] == 3
        assert stats["Most Frequent"] == "apple"
        assert stats["Frequency"] == 3

    def test_all_unique_values(self):
        """Test with text column where all values are unique."""
        df = pd.DataFrame(
            {
                "unique_text": ["a", "b", "c", "d", "e"],
            }
        )

        result = generate_text_stats(df)

        stats = result.iloc[0]
        assert stats["Unique Values"] == 5
        assert stats["Most Frequent"] in ["a", "b", "c", "d", "e"]
        assert stats["Frequency"] == 1

    def test_with_null_values(self):
        """Test text stats with null values."""
        df = pd.DataFrame(
            {
                "text_col": ["a", "b", None, "a", None, "a"],
            }
        )

        result = generate_text_stats(df)

        stats = result.iloc[0]
        assert stats["Column"] == "text_col"
        # nunique() excludes NaN by default
        assert stats["Unique Values"] == 2
        assert stats["Most Frequent"] == "a"
        assert stats["Frequency"] == 3

    def test_empty_dataframe(self):
        """Test with an empty DataFrame."""
        df = pd.DataFrame()

        result = generate_text_stats(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_single_value_column(self):
        """Test with column containing only one unique value."""
        df = pd.DataFrame(
            {
                "same_value": ["constant", "constant", "constant"],
            }
        )

        result = generate_text_stats(df)

        stats = result.iloc[0]
        assert stats["Unique Values"] == 1
        assert stats["Most Frequent"] == "constant"
        assert stats["Frequency"] == 3

    def test_empty_strings(self):
        """Test with empty strings in text column."""
        df = pd.DataFrame(
            {
                "text_col": ["", "a", "", "b", ""],
            }
        )

        result = generate_text_stats(df)

        stats = result.iloc[0]
        assert stats["Unique Values"] == 3  # "", "a", "b"
        assert stats["Most Frequent"] == ""
        assert stats["Frequency"] == 3

    def test_mode_with_empty_dataframe_edge_case(self):
        """Test handling of mode when DataFrame is empty or has edge cases."""
        # Create a DataFrame with object column but empty rows
        df = pd.DataFrame({"text_col": pd.Series([], dtype=object)})

        result = generate_text_stats(df)

        # Should handle gracefully
        assert isinstance(result, pd.DataFrame)
        if len(result) > 0:
            stats = result.iloc[0]
            assert stats["Most Frequent"] == "N/A" or pd.isna(stats["Most Frequent"])
            assert stats["Frequency"] == 0

    def test_multiple_modes(self):
        """Test when there are multiple values with the same frequency."""
        df = pd.DataFrame(
            {
                "text_col": ["a", "b", "c", "a", "b", "c"],
            }
        )

        result = generate_text_stats(df)

        stats = result.iloc[0]
        assert stats["Unique Values"] == 3
        # When there are multiple modes, pandas mode() returns the first one
        assert stats["Most Frequent"] in ["a", "b", "c"]
        assert stats["Frequency"] == 2
