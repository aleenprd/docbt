"""Tests for JSON stringification feature to reduce token count."""

import json

import pandas as pd
import pytest

from docbt.ai.llm import LLMProvider
from docbt.server.server import DocbtServer


class TestDfToJsonCompact:
    """Test cases for _df_to_json method with compact parameter."""

    def test_compact_json_reduces_size(self):
        """Test that compact JSON produces smaller output than pretty-printed JSON."""
        server = DocbtServer()

        # Create a sample DataFrame
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "city": ["New York", "Los Angeles", "Chicago"],
            }
        )

        # Generate pretty-printed JSON (default)
        pretty_json = server._df_to_json(df, compact=False)

        # Generate compact JSON
        compact_json = server._df_to_json(df, compact=True)

        # Compact JSON should be smaller
        assert len(compact_json) < len(pretty_json), (
            f"Compact JSON ({len(compact_json)} chars) should be smaller than pretty JSON ({len(pretty_json)} chars)"
        )

        # Both should be valid JSON
        assert json.loads(pretty_json) == json.loads(compact_json), (
            "Both JSON formats should contain the same data"
        )

    def test_compact_json_removes_whitespace(self):
        """Test that compact JSON removes unnecessary whitespace."""
        server = DocbtServer()

        df = pd.DataFrame({"id": [1, 2, 3], "value": [10.5, 20.3, 30.7]})

        compact_json = server._df_to_json(df, compact=True)

        # Compact JSON should not contain multiple consecutive spaces or newlines
        # (except within string values)
        assert "\n" not in compact_json or compact_json.count("\n") < 3, (
            "Compact JSON should minimize newlines"
        )

    @pytest.mark.skipif(
        True, reason="Requires external network access to download tiktoken encodings"
    )
    def test_compact_json_token_reduction(self):
        """Test that compact JSON reduces token count for LLM processing."""
        server = DocbtServer()

        # Create a larger DataFrame for more significant token difference
        df = pd.DataFrame(
            {
                "product_name": ["Widget A", "Widget B", "Widget C", "Widget D", "Widget E"],
                "price": [19.99, 29.99, 39.99, 49.99, 59.99],
                "category": ["Electronics", "Home", "Garden", "Sports", "Books"],
                "in_stock": [True, False, True, True, False],
                "quantity": [100, 0, 50, 200, 0],
            }
        )

        pretty_json = server._df_to_json(df, compact=False)
        compact_json = server._df_to_json(df, compact=True)

        # Count tokens for both formats
        pretty_tokens = LLMProvider.count_tokens(pretty_json)
        compact_tokens = LLMProvider.count_tokens(compact_json)

        # Compact should use fewer tokens
        assert compact_tokens < pretty_tokens, (
            f"Compact JSON should use fewer tokens ({compact_tokens}) than pretty JSON ({pretty_tokens})"
        )

        # Calculate token savings
        token_savings = pretty_tokens - compact_tokens
        savings_percentage = (token_savings / pretty_tokens) * 100

        # Should achieve at least some token reduction
        assert token_savings > 0, (
            f"Should achieve token reduction, saved {token_savings} tokens ({savings_percentage:.1f}%)"
        )

    def test_compact_json_with_datetime(self):
        """Test that compact JSON works correctly with datetime columns."""
        server = DocbtServer()

        df = pd.DataFrame(
            {"date": pd.date_range("2024-01-01", periods=3), "value": [100, 200, 300]}
        )

        compact_json = server._df_to_json(df, compact=True)

        # Should be valid JSON
        data = json.loads(compact_json)
        assert len(data) == 3
        assert all("date" in item and "value" in item for item in data)

    def test_compact_json_empty_dataframe(self):
        """Test that compact JSON handles empty DataFrames correctly."""
        server = DocbtServer()

        df = pd.DataFrame()

        compact_json = server._df_to_json(df, compact=True)
        pretty_json = server._df_to_json(df, compact=False)

        # Both should return valid empty array (may have whitespace variations)
        assert json.loads(compact_json) == []
        assert json.loads(pretty_json) == []

        # Compact should be smaller or equal
        assert len(compact_json) <= len(pretty_json)

    def test_compact_json_preserves_data_integrity(self):
        """Test that compact JSON preserves all data values correctly."""
        server = DocbtServer()

        df = pd.DataFrame(
            {
                "string": ["test", "data", "values"],
                "integer": [1, 2, 3],
                "float": [1.1, 2.2, 3.3],
                "boolean": [True, False, True],
                "nullable": [1, None, 3],
            }
        )

        compact_json = server._df_to_json(df, compact=True)
        pretty_json = server._df_to_json(df, compact=False)

        # Parse both JSONs
        compact_data = json.loads(compact_json)
        pretty_data = json.loads(pretty_json)

        # Data should be identical
        assert compact_data == pretty_data, "Compact and pretty JSON should contain identical data"

    def test_default_behavior_unchanged(self):
        """Test that default behavior (without compact parameter) remains pretty-printed."""
        server = DocbtServer()

        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        # Call without compact parameter (should default to False)
        default_json = server._df_to_json(df)

        # Should contain indentation (newlines and spaces)
        assert "\n" in default_json, "Default behavior should produce pretty-printed JSON"
        assert "  " in default_json or "\t" in default_json, (
            "Default JSON should contain indentation"
        )


class TestCompactJsonInContext:
    """Test that compact JSON is used in LLM context generation."""

    def test_create_enhanced_system_prompt_uses_compact_json(self):
        """Test that _create_enhanced_system_prompt uses compact JSON."""
        server = DocbtServer()

        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        # Mock session state
        import streamlit as st

        if "data_source" not in st.session_state:
            st.session_state["data_source"] = "filesystem"

        system_prompt = "You are a helpful assistant."

        # Generate enhanced prompt
        enhanced_prompt = server._create_enhanced_system_prompt(df, system_prompt, sample_size=3)

        # The prompt should contain JSON data
        assert "```json" in enhanced_prompt

        # Extract the JSON portion from the prompt
        json_start = enhanced_prompt.find("```json") + 7
        json_end = enhanced_prompt.find("```", json_start)
        json_content = enhanced_prompt[json_start:json_end].strip()

        # The JSON should be compact (minimal whitespace between records)
        # Count newlines - compact JSON should have very few
        newline_count = json_content.count("\n")

        # Compact JSON for 3 records should have minimal newlines
        # (Pretty JSON would have many more due to indentation)
        assert newline_count < 10, (
            f"Enhanced system prompt should use compact JSON (found {newline_count} newlines)"
        )


class TestTokenReductionBenefit:
    """Test to demonstrate the token reduction benefit of stringified JSON."""

    def test_realistic_character_savings(self):
        """Test character savings with realistic data sample (no external dependencies)."""
        server = DocbtServer()

        # Create a realistic dataset similar to what might be used in production
        df = pd.DataFrame(
            {
                "customer_id": range(1, 11),
                "name": [f"Customer {i}" for i in range(1, 11)],
                "email": [f"customer{i}@example.com" for i in range(1, 11)],
                "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
                "city": [
                    "New York",
                    "Los Angeles",
                    "Chicago",
                    "Houston",
                    "Phoenix",
                    "Philadelphia",
                    "San Antonio",
                    "San Diego",
                    "Dallas",
                    "San Jose",
                ],
                "purchase_amount": [
                    129.99,
                    249.50,
                    89.99,
                    399.00,
                    159.99,
                    299.00,
                    179.50,
                    449.99,
                    99.99,
                    199.00,
                ],
                "is_active": [True, True, False, True, True, False, True, True, False, True],
            }
        )

        pretty_json = server._df_to_json(df, compact=False)
        compact_json = server._df_to_json(df, compact=True)

        char_savings = len(pretty_json) - len(compact_json)
        savings_percentage = (char_savings / len(pretty_json)) * 100

        print("\nCharacter Reduction Analysis:")
        print(f"  Pretty JSON: {len(pretty_json)} chars")
        print(f"  Compact JSON: {len(compact_json)} chars")
        print(f"  Savings: {char_savings} chars ({savings_percentage:.1f}%)")

        # Verify we achieved meaningful savings
        assert char_savings > 0, "Should achieve character savings"
        assert savings_percentage > 10, (
            f"Should achieve at least 10% character savings, got {savings_percentage:.1f}%"
        )

    @pytest.mark.skipif(
        True, reason="Requires external network access to download tiktoken encodings"
    )
    def test_realistic_token_savings(self):
        """Test token savings with realistic data sample."""
        server = DocbtServer()

        # Create a realistic dataset similar to what might be used in production
        df = pd.DataFrame(
            {
                "customer_id": range(1, 11),
                "name": [f"Customer {i}" for i in range(1, 11)],
                "email": [f"customer{i}@example.com" for i in range(1, 11)],
                "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
                "city": [
                    "New York",
                    "Los Angeles",
                    "Chicago",
                    "Houston",
                    "Phoenix",
                    "Philadelphia",
                    "San Antonio",
                    "San Diego",
                    "Dallas",
                    "San Jose",
                ],
                "purchase_amount": [
                    129.99,
                    249.50,
                    89.99,
                    399.00,
                    159.99,
                    299.00,
                    179.50,
                    449.99,
                    99.99,
                    199.00,
                ],
                "is_active": [True, True, False, True, True, False, True, True, False, True],
            }
        )

        pretty_json = server._df_to_json(df, compact=False)
        compact_json = server._df_to_json(df, compact=True)

        pretty_tokens = LLMProvider.count_tokens(pretty_json)
        compact_tokens = LLMProvider.count_tokens(compact_json)

        token_savings = pretty_tokens - compact_tokens
        savings_percentage = (token_savings / pretty_tokens) * 100

        print("\nToken Reduction Analysis:")
        print(f"  Pretty JSON: {len(pretty_json)} chars, {pretty_tokens} tokens")
        print(f"  Compact JSON: {len(compact_json)} chars, {compact_tokens} tokens")
        print(f"  Savings: {token_savings} tokens ({savings_percentage:.1f}%)")
        print(f"  Character reduction: {len(pretty_json) - len(compact_json)} chars")

        # Verify we achieved meaningful savings
        assert token_savings > 0, "Should achieve token savings"
        assert savings_percentage > 5, (
            f"Should achieve at least 5% token savings, got {savings_percentage:.1f}%"
        )
