"""Tests for DocbtServer class.

This test suite covers the core business logic and helper methods of the DocbtServer class,
focusing on non-UI logic that can be tested independently of Streamlit.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import requests

from docbt.server.server import DocbtServer


class TestDfToJson:
    """Tests for _df_to_json method."""

    def test_df_to_json_simple_dataframe(self):
        """Test conversion of simple DataFrame with basic types."""
        server = DocbtServer()
        df = pd.DataFrame(
            {"name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35], "score": [95.5, 87.3, 92.1]}
        )

        result = server._df_to_json(df)

        # Should return valid JSON
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 3
        assert parsed[0]["name"] == "Alice"
        assert parsed[0]["age"] == 25
        assert parsed[0]["score"] == 95.5

    def test_df_to_json_timezone_aware_datetime(self):
        """Test conversion of timezone-aware datetime columns."""
        server = DocbtServer()
        df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    ["2023-01-01 10:00:00", "2023-01-02 15:30:00", "2023-01-03 20:45:00"]
                ).tz_localize("UTC"),
                "value": [1, 2, 3],
            }
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Timestamps should be converted to ISO format strings
        assert isinstance(parsed[0]["timestamp"], str)
        assert "T" in parsed[0]["timestamp"]  # ISO format has 'T' separator
        # Should preserve timezone info
        assert parsed[0]["timestamp"].endswith("Z") or "+" in parsed[0]["timestamp"]

    def test_df_to_json_naive_datetime(self):
        """Test conversion of naive datetime columns."""
        server = DocbtServer()
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01"]),
                "value": [10, 20, 30],
            }
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Should convert to ISO format string
        assert isinstance(parsed[0]["date"], str)
        assert "2023-01-01" in parsed[0]["date"]

    def test_df_to_json_timedelta(self):
        """Test conversion of timedelta columns."""
        server = DocbtServer()
        df = pd.DataFrame(
            {"duration": pd.to_timedelta(["1 days", "2 days 3 hours", "5 hours"]), "id": [1, 2, 3]}
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Timedelta should be converted to total seconds
        assert isinstance(parsed[0]["duration"], (int | float))
        assert parsed[0]["duration"] == 86400.0  # 1 day in seconds

    def test_df_to_json_categorical(self):
        """Test conversion of categorical columns."""
        server = DocbtServer()
        df = pd.DataFrame(
            {"category": pd.Categorical(["A", "B", "C", "A", "B"]), "value": [1, 2, 3, 4, 5]}
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Categorical should be converted to string
        assert isinstance(parsed[0]["category"], str)
        assert parsed[0]["category"] == "A"

    def test_df_to_json_period(self):
        """Test conversion of period columns."""
        server = DocbtServer()
        df = pd.DataFrame(
            {"period": pd.period_range("2023-01", periods=3, freq="M"), "value": [100, 200, 300]}
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Period should be converted to string
        assert isinstance(parsed[0]["period"], str)
        assert "2023" in parsed[0]["period"]

    def test_df_to_json_interval(self):
        """Test conversion of interval columns."""
        server = DocbtServer()
        df = pd.DataFrame({"interval": pd.interval_range(start=0, end=3), "value": [1, 2, 3]})

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Interval should be converted to string
        assert isinstance(parsed[0]["interval"], str)

    def test_df_to_json_complex_numbers(self):
        """Test conversion of complex number columns."""
        server = DocbtServer()
        df = pd.DataFrame({"complex": [1 + 2j, 3 + 4j, 5 + 6j], "id": [1, 2, 3]})

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Complex numbers should be converted to string
        assert isinstance(parsed[0]["complex"], str)

    def test_df_to_json_null_values(self):
        """Test handling of null values."""
        server = DocbtServer()
        df = pd.DataFrame(
            {"col1": [1, None, 3], "col2": ["a", None, "c"], "col3": [1.5, np.nan, 3.5]}
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Nulls should be properly handled
        assert parsed[1]["col1"] is None
        assert parsed[1]["col2"] is None
        assert parsed[1]["col3"] is None

    def test_df_to_json_bytes_in_object_column(self):
        """Test conversion of bytes in object columns."""
        server = DocbtServer()
        df = pd.DataFrame({"data": [b"hello", b"world", b"test"], "id": [1, 2, 3]})

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Bytes should be decoded to UTF-8 strings
        assert isinstance(parsed[0]["data"], str)
        assert parsed[0]["data"] == "hello"

    def test_df_to_json_mixed_object_column(self):
        """Test conversion of object columns with mixed types."""
        server = DocbtServer()
        df = pd.DataFrame({"mixed": ["string", 123, None, True], "id": [1, 2, 3, 4]})

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Should handle mixed types
        assert isinstance(result, str)
        assert len(parsed) == 4

    def test_df_to_json_empty_dataframe(self):
        """Test conversion of empty DataFrame."""
        server = DocbtServer()
        df = pd.DataFrame()

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Should return empty array
        assert parsed == []

    def test_df_to_json_single_row(self):
        """Test conversion of single-row DataFrame."""
        server = DocbtServer()
        df = pd.DataFrame({"name": ["Alice"], "age": [25]})

        result = server._df_to_json(df)
        parsed = json.loads(result)

        assert len(parsed) == 1
        assert parsed[0]["name"] == "Alice"
        assert parsed[0]["age"] == 25

    def test_df_to_json_preserves_original_dataframe(self):
        """Test that original DataFrame is not modified."""
        server = DocbtServer()
        df = pd.DataFrame(
            {"date": pd.to_datetime(["2023-01-01"]).tz_localize("UTC"), "value": [100]}
        )

        original_dtype = df["date"].dtype
        _ = server._df_to_json(df)

        # Original DataFrame should remain unchanged
        assert df["date"].dtype == original_dtype

    def test_df_to_json_non_serializable_fallback(self):
        """Test fallback for non-serializable objects."""
        server = DocbtServer()

        # Create DataFrame with custom class that's not JSON serializable
        class CustomObject:
            def __init__(self, value):
                self.value = value

        df = pd.DataFrame({"custom": [CustomObject(1), CustomObject(2)], "id": [1, 2]})

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Should convert to string representation
        assert isinstance(parsed[0]["custom"], str)

    def test_df_to_json_pandas_timestamp_in_object_column(self):
        """Test handling of pandas Timestamp in object columns."""
        server = DocbtServer()
        df = pd.DataFrame(
            {"mixed_dates": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-02-01")], "id": [1, 2]}
        )
        df["mixed_dates"] = df["mixed_dates"].astype(object)

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Should be converted to string
        assert isinstance(parsed[0]["mixed_dates"], str)

    def test_df_to_json_large_dataframe(self):
        """Test conversion of larger DataFrame for performance."""
        server = DocbtServer()
        df = pd.DataFrame(
            {
                "id": range(1000),
                "value": np.random.randn(1000),
                "category": np.random.choice(["A", "B", "C"], 1000),
            }
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # Should handle large DataFrames
        assert len(parsed) == 1000
        assert isinstance(result, str)

    def test_df_to_json_error_handling(self):
        """Test error handling when conversion fails catastrophically."""
        server = DocbtServer()

        # Create a scenario that might cause issues
        # by mocking df.copy() to raise an exception
        with patch.object(pd.DataFrame, "copy", side_effect=Exception("Test error")):
            df = pd.DataFrame({"col": [1, 2, 3]})
            result = server._df_to_json(df)

            # Should return empty array as fallback
            assert result == "[]"

    def test_df_to_json_all_special_types(self):
        """Test DataFrame with multiple special types at once."""
        server = DocbtServer()
        df = pd.DataFrame(
            {
                "datetime": pd.to_datetime(["2023-01-01"]).tz_localize("UTC"),
                "timedelta": pd.to_timedelta(["1 days"]),
                "category": pd.Categorical(["A"]),
                "number": [42],
                "text": ["hello"],
            }
        )

        result = server._df_to_json(df)
        parsed = json.loads(result)

        # All types should be properly converted
        assert isinstance(parsed[0]["datetime"], str)
        assert isinstance(parsed[0]["timedelta"], (int | float))
        assert isinstance(parsed[0]["category"], str)
        assert parsed[0]["number"] == 42
        assert parsed[0]["text"] == "hello"


class TestFetchOpenAIModels:
    """Tests for fetch_openai_models method."""

    def test_fetch_openai_models_success(self):
        """Test successful fetching of OpenAI models."""
        server = DocbtServer()

        # Mock the OpenAI client
        mock_model_1 = Mock()
        mock_model_1.id = "gpt-4-turbo"
        mock_model_2 = Mock()
        mock_model_2.id = "gpt-3.5-turbo"
        mock_model_3 = Mock()
        mock_model_3.id = "gpt-5-nano"
        mock_model_4 = Mock()
        mock_model_4.id = "text-davinci-003"  # Non-GPT model

        mock_response = Mock()
        mock_response.data = [mock_model_1, mock_model_2, mock_model_3, mock_model_4]

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.models.list.return_value = mock_response
            mock_openai.return_value = mock_client

            result = server.fetch_openai_models("test-api-key")

            # Should filter and sort models
            assert isinstance(result, list)
            assert len(result) == 3  # Only GPT models
            assert "gpt-4-turbo" in result
            assert "gpt-3.5-turbo" in result
            assert "gpt-5-nano" in result
            assert "text-davinci-003" not in result

    def test_fetch_openai_models_filters_correctly(self):
        """Test that only chat-compatible models are returned."""
        server = DocbtServer()

        mock_gpt_model = Mock()
        mock_gpt_model.id = "gpt-4"
        mock_non_gpt = Mock()
        mock_non_gpt.id = "whisper-1"
        mock_embedding = Mock()
        mock_embedding.id = "text-embedding-ada-002"

        mock_response = Mock()
        mock_response.data = [mock_gpt_model, mock_non_gpt, mock_embedding]

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.models.list.return_value = mock_response
            mock_openai.return_value = mock_client

            result = server.fetch_openai_models("test-api-key")

            assert "gpt-4" in result
            assert "whisper-1" not in result
            assert "text-embedding-ada-002" not in result

    def test_fetch_openai_models_api_error(self):
        """Test handling of OpenAI API error."""
        server = DocbtServer()

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.models.list.side_effect = Exception("API error")
            mock_openai.return_value = mock_client

            result = server.fetch_openai_models("test-api-key")

            # Should return fallback models
            assert isinstance(result, list)
            assert len(result) > 0
            assert "gpt-5-nano" in result or "gpt-5" in result

    def test_fetch_openai_models_empty_response(self):
        """Test handling of empty model list."""
        server = DocbtServer()

        mock_response = Mock()
        mock_response.data = []

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.models.list.return_value = mock_response
            mock_openai.return_value = mock_client

            result = server.fetch_openai_models("test-api-key")

            assert result == []


class TestFetchOllamaModels:
    """Tests for fetch_ollama_models method."""

    def test_fetch_ollama_models_success(self):
        """Test successful fetching of Ollama models."""
        server = DocbtServer()

        mock_response = Mock()
        mock_response.json.return_value = {
            "models": ["llama2:latest", "mistral:latest", "codellama:latest"]
        }

        with patch("requests.get", return_value=mock_response):
            result = server.fetch_ollama_models("http://localhost:11434")

            assert isinstance(result, list)
            assert len(result) == 3
            assert "llama2:latest" in result
            assert "mistral:latest" in result

    def test_fetch_ollama_models_request_error(self):
        """Test handling of request exception."""
        server = DocbtServer()

        with patch("requests.get", side_effect=requests.RequestException("Connection error")):
            result = server.fetch_ollama_models("http://localhost:11434")

            assert result == []

    def test_fetch_ollama_models_malformed_response(self):
        """Test handling of malformed JSON response."""
        server = DocbtServer()

        mock_response = Mock()
        mock_response.json.return_value = {"wrong_key": []}

        with patch("requests.get", return_value=mock_response):
            result = server.fetch_ollama_models("http://localhost:11434")

            assert result == []

    def test_fetch_ollama_models_empty_list(self):
        """Test handling of empty model list."""
        server = DocbtServer()

        mock_response = Mock()
        mock_response.json.return_value = {"models": []}

        with patch("requests.get", return_value=mock_response):
            result = server.fetch_ollama_models("http://localhost:11434")

            assert result == []


class TestFetchLMStudioModels:
    """Tests for fetch_lmstudio_models method."""

    def test_fetch_lmstudio_models_success(self):
        """Test successful fetching of LM Studio models."""
        server = DocbtServer()

        mock_response = Mock()
        mock_response.json.return_value = {"data": ["model1", "model2", "model3"]}

        with patch("requests.get", return_value=mock_response):
            result = server.fetch_lmstudio_models("http://localhost:1234")

            assert isinstance(result, list)
            assert len(result) == 3
            assert "model1" in result

    def test_fetch_lmstudio_models_request_error(self):
        """Test handling of request exception."""
        server = DocbtServer()

        with patch("requests.get", side_effect=requests.RequestException("Connection error")):
            result = server.fetch_lmstudio_models("http://localhost:1234")

            assert result == []

    def test_fetch_lmstudio_models_no_data_key(self):
        """Test handling of response without 'data' key."""
        server = DocbtServer()

        mock_response = Mock()
        mock_response.json.return_value = {}

        with patch("requests.get", return_value=mock_response):
            result = server.fetch_lmstudio_models("http://localhost:1234")

            assert result == []

    def test_fetch_lmstudio_models_malformed_response(self):
        """Test handling of malformed JSON response."""
        server = DocbtServer()

        mock_response = Mock()
        mock_response.json.return_value = {"wrong_key": []}

        with patch("requests.get", return_value=mock_response):
            result = server.fetch_lmstudio_models("http://localhost:1234")

            assert result == []


class TestSendChatMessage:
    """Tests for send_chat_message method."""

    def test_send_chat_message_llm_disabled(self):
        """Test chat message when LLM is disabled."""
        server = DocbtServer()

        llm_config = {"enabled": False}
        result = server.send_chat_message(llm_config, "Hello")

        assert "not enabled" in result.lower()

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLMProvider")
    def test_send_chat_message_openai(self, mock_llm_provider, mock_st):
        """Test chat message with OpenAI provider."""
        server = DocbtServer()
        mock_st.session_state = {"developer_mode": False}

        llm_config = {
            "enabled": True,
            "provider": "openai",
            "api_key": "test-key",
            "model_name": "gpt-4",
            "system_prompt": "You are a helpful assistant.",
        }

        mock_llm_provider.chat_with_openai.return_value = "AI response"

        result = server.send_chat_message(llm_config, "Hello", [])

        assert result == "AI response"
        mock_llm_provider.chat_with_openai.assert_called_once()

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLMProvider")
    def test_send_chat_message_openai_no_api_key(self, mock_llm_provider, mock_st):
        """Test chat message with OpenAI but missing API key."""
        server = DocbtServer()
        mock_st.session_state = {}

        llm_config = {"enabled": True, "provider": "openai", "model_name": "gpt-4"}

        result = server.send_chat_message(llm_config, "Hello")

        assert "api key is required" in result.lower()

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLMProvider")
    def test_send_chat_message_ollama(self, mock_llm_provider, mock_st):
        """Test chat message with Ollama provider."""
        server = DocbtServer()
        mock_st.session_state = {"developer_mode": False}

        llm_config = {
            "enabled": True,
            "provider": "ollama",
            "server": "http://localhost:11434",
            "model_name": "llama2",
            "system_prompt": "You are helpful.",
        }

        mock_llm_provider.chat_with_ollama.return_value = "Ollama response"

        result = server.send_chat_message(llm_config, "Hello", [])

        assert result == "Ollama response"
        mock_llm_provider.chat_with_ollama.assert_called_once()

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLMProvider")
    def test_send_chat_message_lmstudio(self, mock_llm_provider, mock_st):
        """Test chat message with LM Studio provider."""
        server = DocbtServer()
        mock_st.session_state = {"developer_mode": False}

        llm_config = {
            "enabled": True,
            "provider": "lmstudio",
            "server": "http://localhost:1234",
            "model_name": "local-model",
            "system_prompt": "You are helpful.",
        }

        mock_llm_provider.chat_with_lmstudio.return_value = "LMStudio response"

        result = server.send_chat_message(llm_config, "Hello", [])

        assert result == "LMStudio response"
        mock_llm_provider.chat_with_lmstudio.assert_called_once()

    @patch("docbt.server.server.st")
    def test_send_chat_message_unknown_provider(self, mock_st):
        """Test chat message with unknown provider."""
        server = DocbtServer()
        mock_st.session_state = {}

        llm_config = {"enabled": True, "provider": "unknown"}

        result = server.send_chat_message(llm_config, "Hello")

        assert "unknown" in result.lower()

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLMProvider")
    def test_send_chat_message_with_data_context(self, mock_llm_provider, mock_st):
        """Test chat message with uploaded data context."""
        server = DocbtServer()

        # Mock dataframe in session state
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30], "city": ["NYC", "LA"]})

        # Create a mock session state object that supports both dict-like and attribute access
        mock_session_state = MagicMock()

        # Make get() method work properly
        def mock_get(key, default=None):
            values = {"developer_mode": False, "uploaded_filename": "test.csv"}
            return values.get(key, default)

        mock_session_state.get = mock_get
        mock_session_state.node = df

        # Support "node" in st.session_state check
        mock_session_state.__contains__ = lambda self, key: key in ["node", "uploaded_filename"]

        mock_st.session_state = mock_session_state

        mock_llm_provider.chat_with_openai.return_value = "Response with context"

        llm_config = {
            "enabled": True,
            "provider": "openai",
            "api_key": "test-key",
            "model_name": "gpt-4",
            "system_prompt": "You are a helpful assistant.",
        }

        # Call the method
        server.send_chat_message(llm_config, "Tell me about this data")

        # Verify LLM was called
        mock_llm_provider.chat_with_openai.assert_called_once()

        # Get the actual call arguments
        call_args = mock_llm_provider.chat_with_openai.call_args
        system_prompt_arg = call_args[1]["system_prompt"]

        # Verify data context was added to system prompt
        assert "Data Context" in system_prompt_arg
        assert "test.csv" in system_prompt_arg
        assert "name" in system_prompt_arg
        assert "age" in system_prompt_arg

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLMProvider")
    def test_send_chat_message_developer_mode(self, mock_llm_provider, mock_st):
        """Test chat message returns metrics in developer mode."""
        server = DocbtServer()
        mock_st.session_state = {
            "developer_mode": True,
            "max_tokens": 2000,
            "temperature": 0.8,
            "top_p": 0.9,
            "stop_sequences": "STOP",
        }

        mock_llm_provider.chat_with_openai.return_value = {
            "content": "Response",
            "metrics": {"tokens": 100},
        }

        llm_config = {
            "enabled": True,
            "provider": "openai",
            "api_key": "test-key",
            "model_name": "gpt-4",
            "system_prompt": "You are a helpful assistant.",
        }

        # Call the method
        server.send_chat_message(llm_config, "Hello")

        # Verify return_metrics=True was passed
        call_args = mock_llm_provider.chat_with_openai.call_args
        assert call_args[1]["return_metrics"] is True
        assert call_args[1]["max_tokens"] == 2000
        assert call_args[1]["temperature"] == 0.8


class TestParseRawTags:
    """Tests for parse_raw_tags method."""

    def test_parse_raw_tags_valid(self):
        """Test parsing valid comma-separated tags."""
        server = DocbtServer()

        result = server.parse_raw_tags("tag1, tag2, tag3")

        assert result == ["tag1", "tag2", "tag3"]

    def test_parse_raw_tags_with_extra_spaces(self):
        """Test parsing tags with extra whitespace."""
        server = DocbtServer()

        result = server.parse_raw_tags("  tag1  ,  tag2  ,  tag3  ")

        assert result == ["tag1", "tag2", "tag3"]

    def test_parse_raw_tags_empty_string(self):
        """Test parsing empty string."""
        server = DocbtServer()

        result = server.parse_raw_tags("")

        assert result is None

    def test_parse_raw_tags_none(self):
        """Test parsing None value."""
        server = DocbtServer()

        result = server.parse_raw_tags(None)

        assert result is None

    def test_parse_raw_tags_single_tag(self):
        """Test parsing single tag."""
        server = DocbtServer()

        result = server.parse_raw_tags("single_tag")

        assert result == ["single_tag"]

    def test_parse_raw_tags_empty_items(self):
        """Test parsing with empty items between commas."""
        server = DocbtServer()

        result = server.parse_raw_tags("tag1, , tag2, ,")

        assert result == ["tag1", "tag2"]

    def test_parse_raw_tags_all_empty_items(self):
        """Test parsing with all empty items."""
        server = DocbtServer()

        result = server.parse_raw_tags(", , ,")

        assert result is None


class TestParseRawMetaTags:
    """Tests for parse_raw_meta_tags method."""

    def test_parse_raw_meta_tags_valid(self):
        """Test parsing valid key:value pairs."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags("key1:value1, key2:value2")

        assert result == {"key1": "value1", "key2": "value2"}

    def test_parse_raw_meta_tags_with_spaces(self):
        """Test parsing with extra whitespace."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags("  key1 : value1  ,  key2 : value2  ")

        assert result == {"key1": "value1", "key2": "value2"}

    def test_parse_raw_meta_tags_empty_string(self):
        """Test parsing empty string."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags("")

        assert result is None

    def test_parse_raw_meta_tags_none(self):
        """Test parsing None value."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags(None)

        assert result is None

    def test_parse_raw_meta_tags_single_pair(self):
        """Test parsing single key:value pair."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags("key:value")

        assert result == {"key": "value"}

    def test_parse_raw_meta_tags_value_with_colon(self):
        """Test parsing value containing colon."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags("url:http://example.com")

        assert result == {"url": "http://example.com"}

    def test_parse_raw_meta_tags_invalid_format(self):
        """Test parsing items without colons."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags("key1:value1, invalid, key2:value2")

        # Should only include valid key:value pairs
        assert result == {"key1": "value1", "key2": "value2"}

    def test_parse_raw_meta_tags_all_invalid(self):
        """Test parsing with all invalid items."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags("invalid1, invalid2")

        assert result is None

    def test_parse_raw_meta_tags_empty_after_parse(self):
        """Test when all items are filtered out."""
        server = DocbtServer()

        result = server.parse_raw_meta_tags(", , ,")

        assert result is None


class TestCleanDict:
    """Tests for clean_dict static method."""

    def test_clean_dict_removes_empty_values(self):
        """Test removing None, empty string, and empty dict/list."""
        data = {
            "key1": "value1",
            "key2": None,
            "key3": "",
            "key4": [],
            "key5": {},
            "key6": "value6",
        }

        result = DocbtServer.clean_dict(data)

        assert result == {"key1": "value1", "key6": "value6"}

    def test_clean_dict_with_keep_keys(self):
        """Test keeping specific keys even if empty."""
        data = {"key1": "value1", "key2": None, "key3": "", "important": None}

        result = DocbtServer.clean_dict(data, keep_keys=["important"])

        assert "key1" in result
        assert "important" in result
        assert result["important"] is None
        assert "key2" not in result
        assert "key3" not in result

    def test_clean_dict_nested(self):
        """Test cleaning nested dictionaries."""
        data = {"outer": {"inner1": "value", "inner2": None, "inner3": ""}, "key": "value"}

        result = DocbtServer.clean_dict(data)

        assert result["outer"] == {"inner1": "value"}
        assert result["key"] == "value"

    def test_clean_dict_empty_input(self):
        """Test with empty dictionary."""
        result = DocbtServer.clean_dict({})

        assert result == {}

    def test_clean_dict_all_empty(self):
        """Test when all values are empty."""
        data = {"key1": None, "key2": "", "key3": [], "key4": {}}

        result = DocbtServer.clean_dict(data)

        assert result == {}

    def test_clean_dict_preserves_zero_and_false(self):
        """Test that 0 and False are not removed."""
        data = {"zero": 0, "false": False, "none": None, "empty": ""}

        result = DocbtServer.clean_dict(data)

        assert result == {"zero": 0, "false": False}

    def test_clean_dict_list_of_dicts(self):
        """Test cleaning list containing dictionaries."""
        data = {"items": [{"name": "item1", "value": None}, {"name": "item2", "value": "val2"}]}

        result = DocbtServer.clean_dict(data)

        assert len(result["items"]) == 2
        assert result["items"][0] == {"name": "item1"}
        assert result["items"][1] == {"name": "item2", "value": "val2"}


class TestOrderDict:
    """Tests for _order_dict static method."""

    def test_order_dict_basic(self):
        """Test basic dictionary ordering."""
        data = {"c": 3, "a": 1, "b": 2}
        key_order = ["a", "b", "c"]

        result = DocbtServer._order_dict(data, key_order)

        keys = list(result.keys())
        assert keys == ["a", "b", "c"]

    def test_order_dict_partial_order(self):
        """Test ordering with keys not in order list."""
        data = {"d": 4, "b": 2, "a": 1, "c": 3}
        key_order = ["a", "c"]

        result = DocbtServer._order_dict(data, key_order)

        keys = list(result.keys())
        # 'a' and 'c' should be first in that order
        assert keys[:2] == ["a", "c"]
        # 'd' and 'b' should follow (in original order)
        assert set(keys[2:]) == {"d", "b"}

    def test_order_dict_missing_keys(self):
        """Test ordering when some keys in order list are missing."""
        data = {"a": 1, "c": 3}
        key_order = ["a", "b", "c"]

        result = DocbtServer._order_dict(data, key_order)

        keys = list(result.keys())
        assert keys == ["a", "c"]

    def test_order_dict_empty(self):
        """Test with empty dictionary."""
        result = DocbtServer._order_dict({}, ["a", "b"])

        assert result == {}

    def test_order_dict_empty_order(self):
        """Test with empty order list."""
        data = {"a": 1, "b": 2}

        result = DocbtServer._order_dict(data, [])

        assert result == data


class TestValidateIfChoice:
    """Tests for validate_if_choice static method."""

    @patch("docbt.server.server.st")
    def test_validate_if_choice_valid_formats(self, mock_st):
        """Test valid comparison formats."""
        # Valid formats should return True (or None indicating success)
        result1 = DocbtServer.validate_if_choice("> 1")
        result2 = DocbtServer.validate_if_choice("< 5")
        result3 = DocbtServer.validate_if_choice(">= 10")
        result4 = DocbtServer.validate_if_choice("<= 100")
        result5 = DocbtServer.validate_if_choice("== 42")
        result6 = DocbtServer.validate_if_choice("!= 0")

        # These should not return False (either True or None)
        assert result1 is not False
        assert result2 is not False
        assert result3 is not False
        assert result4 is not False
        assert result5 is not False
        assert result6 is not False

    @patch("docbt.server.server.st")
    def test_validate_if_choice_invalid(self, mock_st):
        """Test invalid choices."""
        # Invalid format should trigger error and return False
        result = DocbtServer.validate_if_choice("invalid")
        assert result is False
        mock_st.error.assert_called()

    @patch("docbt.server.server.st")
    def test_validate_if_choice_empty(self, mock_st):
        """Test empty string."""
        # Empty string should not trigger error (returns None)
        result = DocbtServer.validate_if_choice("")
        assert result is None or result is False

    def test_validate_if_choice_none(self):
        """Test None input."""
        result = DocbtServer.validate_if_choice(None)
        # None should return None (no validation performed)
        assert result is None


class TestArgsAcceptedValues:
    """Tests for args_accepted_values static method."""

    @patch("docbt.server.server.st")
    def test_args_accepted_values_basic(self, mock_st):
        """Test generating accepted values arguments."""
        # Mock the streamlit widgets
        mock_st.text_area.return_value = "val1,val2,val3"
        mock_st.checkbox.return_value = True

        result = DocbtServer.args_accepted_values("status")

        assert isinstance(result, dict)
        assert "values" in result
        assert "quote" in result
        assert isinstance(result["values"], list)

    @patch("docbt.server.server.st")
    def test_args_accepted_values_returns_dict(self, mock_st):
        """Test that result is a dictionary with expected structure."""
        mock_st.text_area.return_value = "a,b,c"
        mock_st.checkbox.return_value = False

        result = DocbtServer.args_accepted_values("test_col")

        assert isinstance(result, dict)
        assert "values" in result
        assert "quote" in result
        assert result["values"] == ["a", "b", "c"]
        assert result["quote"] is False


class TestArgsRelationships:
    """Tests for args_relationships static method."""

    def test_args_relationships_basic(self):
        """Test generating relationships arguments."""
        result = DocbtServer.args_relationships("user_id")

        assert isinstance(result, dict)
        assert "to" in result
        assert "field" in result

    def test_args_relationships_structure(self):
        """Test structure of relationships dictionary."""
        result = DocbtServer.args_relationships("order_id")

        assert "to" in result
        assert "field" in result
        # Should have placeholders or default values
        assert isinstance(result["to"], str)
        assert isinstance(result["field"], str)


class TestArgsGenericTest:
    """Tests for args_generic_test static method."""

    def test_args_generic_test_basic(self):
        """Test generating generic test arguments."""
        result = DocbtServer.args_generic_test("custom_test", "column_name")

        assert isinstance(result, dict)

    def test_args_generic_test_different_tests(self):
        """Test with different test names."""
        result1 = DocbtServer.args_generic_test("test1", "col1")
        result2 = DocbtServer.args_generic_test("test2", "col2")

        assert isinstance(result1, dict)
        assert isinstance(result2, dict)


class TestSetupLLMProvider:
    """Tests for setup_llm_provider method."""

    class SessionStateMock:
        """Mock for st.session_state that supports both dict and attribute access."""

        def __init__(self, initial_data=None):
            self._data = initial_data.copy() if initial_data else {}

        def __getitem__(self, key):
            return self._data[key]

        def __setitem__(self, key, value):
            self._data[key] = value

        def __contains__(self, key):
            return key in self._data

        def get(self, key, default=None):
            return self._data.get(key, default)

        def __getattr__(self, key):
            if key == "_data":
                return object.__getattribute__(self, "_data")
            return self._data.get(key)

        def __setattr__(self, key, value):
            if key == "_data":
                object.__setattr__(self, key, value)
            else:
                self._data[key] = value

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["lmstudio", "ollama", "openai"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "lmstudio")
    def test_setup_llm_provider_initializes_default(self, mock_st):
        """Test that default provider is set when not in session state."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock()
        mock_st.radio.return_value = "lmstudio"

        result = server.setup_llm_provider()

        # Should initialize to default provider
        assert mock_st.session_state["llm_provider"] == "lmstudio"
        assert result == "lmstudio"

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["lmstudio", "ollama", "openai"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "openai")
    def test_setup_llm_provider_uses_existing_selection(self, mock_st):
        """Test that existing provider selection is preserved."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock({"llm_provider": "ollama"})
        mock_st.radio.return_value = "ollama"

        result = server.setup_llm_provider()

        # Should use existing selection
        assert result == "ollama"

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["lmstudio", "ollama"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "openai")
    def test_setup_llm_provider_default_not_available(self, mock_st):
        """Test fallback when default provider is not in available list."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock()
        mock_st.radio.return_value = "lmstudio"

        result = server.setup_llm_provider()

        # Should fall back to first available provider
        assert mock_st.session_state["llm_provider"] == "lmstudio"
        assert result == "lmstudio"

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["ollama", "openai"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "lmstudio")
    def test_setup_llm_provider_current_not_in_list(self, mock_st):
        """Test that current provider is reset if not in available list."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock({"llm_provider": "lmstudio"})  # Not available
        mock_st.radio.return_value = "ollama"

        _ = server.setup_llm_provider()

        # Should reset to first available
        assert mock_st.session_state["llm_provider"] == "ollama"

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", [])
    def test_setup_llm_provider_no_providers_available(self, mock_st):
        """Test error handling when no providers are enabled."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock()

        result = server.setup_llm_provider()

        # Should show error and return None
        assert result is None
        mock_st.error.assert_called_once()
        assert "No LLM providers" in mock_st.error.call_args[0][0]

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["openai"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "openai")
    def test_setup_llm_provider_single_provider(self, mock_st):
        """Test with only one provider available."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock()
        mock_st.radio.return_value = "openai"

        result = server.setup_llm_provider()

        assert result == "openai"
        assert mock_st.session_state["llm_provider"] == "openai"

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["lmstudio", "ollama", "openai"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "ollama")
    def test_setup_llm_provider_radio_called_with_correct_params(self, mock_st):
        """Test that st.radio is called with correct parameters."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock({"llm_provider": "ollama"})
        mock_st.radio.return_value = "openai"

        server.setup_llm_provider()

        # Verify radio was called with correct parameters
        mock_st.radio.assert_called_once()
        call_args = mock_st.radio.call_args

        # Check that options list is passed
        assert call_args[0][1] == ["lmstudio", "ollama", "openai"]

        # Check that index is correct (ollama is at index 1)
        assert call_args[1]["index"] == 1

        # Check horizontal=True
        assert call_args[1]["horizontal"] is True

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["openai", "lmstudio"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "openai")
    def test_setup_llm_provider_returns_selected_value(self, mock_st):
        """Test that the method returns the value from st.radio."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock({"llm_provider": "openai"})
        mock_st.radio.return_value = "lmstudio"  # User selects different provider

        result = server.setup_llm_provider()

        # Should return the new selection from radio
        assert result == "lmstudio"

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["lmstudio", "ollama", "openai"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "lmstudio")
    def test_setup_llm_provider_index_calculation(self, mock_st):
        """Test that the index is correctly calculated for st.radio."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock({"llm_provider": "openai"})
        mock_st.radio.return_value = "openai"

        server.setup_llm_provider()

        # Verify index is correct (openai is at index 2)
        call_args = mock_st.radio.call_args
        assert call_args[1]["index"] == 2

    @patch("docbt.server.server.st")
    @patch("docbt.server.server.LLM_PROVIDERS", ["ollama"])
    @patch("docbt.server.server.DEFAULT_PROVIDER", "ollama")
    def test_setup_llm_provider_help_text_present(self, mock_st):
        """Test that help text is provided to the radio widget."""
        server = DocbtServer()
        mock_st.session_state = self.SessionStateMock()
        mock_st.radio.return_value = "ollama"

        server.setup_llm_provider()

        # Verify help text is present
        call_args = mock_st.radio.call_args
        assert "help" in call_args[1]
        assert len(call_args[1]["help"]) > 0
