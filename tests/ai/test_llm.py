"""Tests for LLM provider module."""

import time
from unittest.mock import Mock

import pytest

from docbt.ai.llm import LLMProvider


class TestParseChainOfThought:
    """Test cases for parse_chain_of_thought method."""

    def test_lmstudio_with_think_tags(self):
        """Test parsing with <think> tags for lmstudio provider."""
        response = "<think>Let me analyze this data...</think>Here is the final answer."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Let me analyze this data..."
        assert content == "Here is the final answer."

    def test_lmstudio_with_thinking_tags(self):
        """Test parsing with <thinking> tags for lmstudio provider."""
        response = "<thinking>Considering the options...</thinking>The best choice is A."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Considering the options..."
        assert content == "The best choice is A."

    def test_lmstudio_with_reasoning_tags(self):
        """Test parsing with <reasoning> tags for lmstudio provider."""
        response = "<reasoning>This requires careful thought.</reasoning>Final conclusion."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "This requires careful thought."
        assert content == "Final conclusion."

    def test_lmstudio_with_thought_tags(self):
        """Test parsing with <thought> tags for lmstudio provider."""
        response = "<thought>Breaking down the problem...</thought>Solution follows."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Breaking down the problem..."
        assert content == "Solution follows."

    def test_lmstudio_with_analysis_tags(self):
        """Test parsing with <analysis> tags for lmstudio provider."""
        response = "<analysis>Examining the data points...</analysis>Result is positive."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Examining the data points..."
        assert content == "Result is positive."

    def test_lmstudio_no_cot_markers(self):
        """Test parsing when there are no chain of thought markers for lmstudio."""
        response = "This is just a regular response without any markers."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning is None
        assert content == "This is just a regular response without any markers."

    def test_lmstudio_with_multiline_reasoning(self):
        """Test parsing with multiline reasoning content for lmstudio."""
        response = """<think>
First, let me consider point A.
Then, I need to analyze point B.
Finally, conclusion C follows.
</think>The answer is 42."""
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert "First, let me consider point A" in reasoning
        assert "Then, I need to analyze point B" in reasoning
        assert "Finally, conclusion C follows" in reasoning
        assert content == "The answer is 42."

    def test_lmstudio_case_insensitive_tags(self):
        """Test that tag matching is case insensitive for lmstudio."""
        response = "<THINK>Uppercase tags work too</THINK>Final answer"
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Uppercase tags work too"
        assert content == "Final answer"

    def test_ollama_with_think_tags(self):
        """Test parsing with <think> tags for ollama provider."""
        response = "<think>Let me analyze this data...</think>Here is the final answer."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "ollama")

        assert reasoning == "Let me analyze this data..."
        assert content == "Here is the final answer."

    def test_ollama_no_cot_markers(self):
        """Test parsing when there are no chain of thought markers for ollama."""
        response = "This is just a regular response without any markers."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "ollama")

        assert reasoning is None
        assert content == "This is just a regular response without any markers."

    def test_dict_response_with_reasoning_content_field(self):
        """Test parsing dict response with explicit reasoning_content field."""
        response = {
            "content": "The final answer is 42.",
            "reasoning_content": "Let me think about this problem step by step.",
        }
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Let me think about this problem step by step."
        assert content == "The final answer is 42."

    def test_dict_response_without_reasoning_field(self):
        """Test parsing dict response without reasoning field."""
        response = {"content": "<think>Internal reasoning</think>Final answer"}
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Internal reasoning"
        assert content == "Final answer"

    def test_dict_response_with_empty_content(self):
        """Test parsing dict response with empty content field."""
        response = {"content": ""}
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning is None
        assert content == ""  # Empty string is stripped, not None

    def test_empty_string_response(self):
        """Test parsing empty string response."""
        response = ""
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning is None
        assert content is None

    def test_none_response(self):
        """Test parsing None response."""
        response = None
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning is None
        assert content is None

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        response = "Some response text"

        with pytest.raises(ValueError, match="Invalid provider"):
            LLMProvider.parse_chain_of_thought(response, "invalid_provider")

    def test_openai_provider_not_implemented(self):
        """Test that openai provider raises NotImplementedError."""
        response = "Some response text"

        with pytest.raises(NotImplementedError, match="Chain of thought parsing for OpenAI"):
            LLMProvider.parse_chain_of_thought(response, "openai")

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped from reasoning and content."""
        response = "  <think>  Reasoning with spaces  </think>  Content with spaces  "
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Reasoning with spaces"
        assert content == "Content with spaces"

    def test_multiple_cot_markers_first_match_wins(self):
        """Test that only the first matching pattern is extracted."""
        response = (
            "<think>First reasoning</think><reasoning>Second reasoning</reasoning>Final answer"
        )
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        # Should match the first pattern (<think>)
        assert reasoning == "First reasoning"
        assert "<reasoning>Second reasoning</reasoning>Final answer" in content

    def test_nested_tags_not_supported(self):
        """Test behavior with nested tags (should match outer tags)."""
        response = "<think>Outer <think>inner</think> reasoning</think>Answer"
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        # The regex will match the first closing tag
        assert reasoning == "Outer <think>inner"
        assert "reasoning</think>Answer" in content or content == "Answer"

    def test_special_characters_in_reasoning(self):
        """Test that special characters are preserved in reasoning."""
        response = "<think>Testing with $pecial ch@rs & symbols!</think>Final answer."
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Testing with $pecial ch@rs & symbols!"
        assert content == "Final answer."

    def test_json_like_content_in_response(self):
        """Test parsing when response contains JSON-like content."""
        response = '<think>Analyzing JSON structure</think>{"result": "success", "value": 42}'
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Analyzing JSON structure"
        assert content == '{"result": "success", "value": 42}'

    def test_unicode_characters_in_reasoning(self):
        """Test that unicode characters are handled properly."""
        response = "<think>Pensée en français 🤔</think>Final answer with emoji ✅"
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        assert reasoning == "Pensée en français 🤔"
        assert content == "Final answer with emoji ✅"

    def test_only_closing_tag_no_match(self):
        """Test that only closing tag without opening can still be matched by the pattern."""
        response = "Some text </think> more text"
        reasoning, content = LLMProvider.parse_chain_of_thought(response, "lmstudio")

        # The pattern ^(.*?)</think> will match from start to closing tag
        assert reasoning == "Some text"
        assert content == "more text"


class TestParseStopSequences:
    """Test cases for parse_stop_sequences method."""

    def test_single_stop_sequence(self):
        """Test parsing a single stop sequence."""
        result = LLMProvider.parse_stop_sequences("STOP")

        assert result == ["STOP"]

    def test_multiple_stop_sequences(self):
        """Test parsing multiple comma-separated stop sequences."""
        result = LLMProvider.parse_stop_sequences("STOP, END, TERMINATE")

        assert result == ["STOP", "END", "TERMINATE"]

    def test_stop_sequences_with_extra_whitespace(self):
        """Test that extra whitespace is stripped from sequences."""
        result = LLMProvider.parse_stop_sequences("  STOP  ,  END  ,  TERMINATE  ")

        assert result == ["STOP", "END", "TERMINATE"]

    def test_stop_sequences_no_spaces(self):
        """Test parsing sequences without spaces after commas."""
        result = LLMProvider.parse_stop_sequences("STOP,END,TERMINATE")

        assert result == ["STOP", "END", "TERMINATE"]

    def test_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = LLMProvider.parse_stop_sequences("")

        assert result is None

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = LLMProvider.parse_stop_sequences(None)

        assert result is None

    def test_whitespace_only_returns_none(self):
        """Test that whitespace-only string returns None."""
        result = LLMProvider.parse_stop_sequences("   ")

        assert result is None

    def test_empty_items_filtered_out(self):
        """Test that empty items between commas are filtered out."""
        result = LLMProvider.parse_stop_sequences("STOP,,END,,,TERMINATE")

        assert result == ["STOP", "END", "TERMINATE"]

    def test_all_empty_items_returns_none(self):
        """Test that string with only commas returns None."""
        result = LLMProvider.parse_stop_sequences(",,,")

        assert result is None

    def test_mixed_empty_and_whitespace_items(self):
        """Test filtering of both empty and whitespace-only items."""
        result = LLMProvider.parse_stop_sequences("STOP,  , , END,   ,TERMINATE")

        assert result == ["STOP", "END", "TERMINATE"]

    def test_special_characters_in_sequences(self):
        """Test that special characters are preserved."""
        result = LLMProvider.parse_stop_sequences("<|end|>, ###, [DONE]")

        assert result == ["<|end|>", "###", "[DONE]"]

    def test_newlines_in_sequences(self):
        """Test sequences containing newline characters."""
        result = LLMProvider.parse_stop_sequences("\\n, \\n\\n, STOP")

        assert result == ["\\n", "\\n\\n", "STOP"]

    def test_unicode_characters(self):
        """Test sequences with unicode characters."""
        result = LLMProvider.parse_stop_sequences("STOP, 停止, КОНЕЦ")

        assert result == ["STOP", "停止", "КОНЕЦ"]

    def test_single_comma_only(self):
        """Test input of just a single comma."""
        result = LLMProvider.parse_stop_sequences(",")

        assert result is None

    def test_sequences_with_numbers(self):
        """Test sequences containing numbers."""
        result = LLMProvider.parse_stop_sequences("STOP123, END456, 789")

        assert result == ["STOP123", "END456", "789"]

    def test_sequences_with_punctuation(self):
        """Test sequences with various punctuation marks."""
        result = LLMProvider.parse_stop_sequences("stop!, end?, done.")

        assert result == ["stop!", "end?", "done."]

    def test_very_long_sequence_list(self):
        """Test parsing a long list of sequences."""
        sequences = ", ".join([f"SEQ{i}" for i in range(100)])
        result = LLMProvider.parse_stop_sequences(sequences)

        assert len(result) == 100
        assert result[0] == "SEQ0"
        assert result[99] == "SEQ99"

    def test_single_character_sequences(self):
        """Test single character stop sequences."""
        result = LLMProvider.parse_stop_sequences("a, b, c, d")

        assert result == ["a", "b", "c", "d"]

    def test_mixed_length_sequences(self):
        """Test sequences of varying lengths."""
        result = LLMProvider.parse_stop_sequences("x, STOP, a, TERMINATE NOW")

        assert result == ["x", "STOP", "a", "TERMINATE NOW"]

    def test_sequences_with_tabs(self):
        """Test that tabs are also stripped as whitespace."""
        result = LLMProvider.parse_stop_sequences("\tSTOP\t,\tEND\t,\tDONE\t")

        assert result == ["STOP", "END", "DONE"]


class TestValidateStructuredResponse:
    """Test cases for validate_structured_response method."""

    def test_valid_dict_response(self):
        """Test validation with a valid dict response."""
        response = {"name": "John Doe", "age": 30, "email": "john@example.com"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string"},
            },
            "required": ["name", "age", "email"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_valid_json_string_response(self):
        """Test validation with a valid JSON string response."""
        response = '{"name": "John Doe", "age": 30, "email": "john@example.com"}'
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string"},
            },
            "required": ["name", "age", "email"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_invalid_response_missing_required_field(self):
        """Test validation fails when required field is missing."""
        response = {
            "name": "John Doe",
            "age": 30,
            # missing email
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string"},
            },
            "required": ["name", "age", "email"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is False

    def test_invalid_response_wrong_type(self):
        """Test validation fails when field has wrong type."""
        response = {
            "name": "John Doe",
            "age": "thirty",  # Should be number
            "email": "john@example.com",
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string"},
            },
            "required": ["name", "age", "email"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is False

    def test_invalid_json_string(self):
        """Test validation fails with invalid JSON string."""
        response = '{"name": "John Doe", "age": 30, invalid json'
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is False

    def test_valid_array_response(self):
        """Test validation with array response."""
        response = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "number"}, "name": {"type": "string"}},
                "required": ["id", "name"],
            },
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_valid_nested_object(self):
        """Test validation with nested objects."""
        response = {"user": {"name": "John Doe", "address": {"city": "New York", "zip": "10001"}}}
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {"city": {"type": "string"}, "zip": {"type": "string"}},
                        },
                    },
                }
            },
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_schema_with_enum(self):
        """Test validation with enum constraint."""
        response = {"status": "active", "priority": "high"}
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_invalid_enum_value(self):
        """Test validation fails with invalid enum value."""
        response = {"status": "invalid_status", "priority": "high"}
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is False

    def test_optional_fields(self):
        """Test validation with optional fields."""
        response = {
            "name": "John Doe"
            # age is optional
        }
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_additional_properties_allowed(self):
        """Test validation with additional properties."""
        response = {
            "name": "John Doe",
            "age": 30,
            "extra_field": "extra_value",  # Not in schema
        }
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name", "age"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        # By default, additional properties are allowed
        assert result is True

    def test_empty_object_valid_schema(self):
        """Test validation with empty object when no fields required."""
        response = {}
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_empty_array_valid(self):
        """Test validation with empty array."""
        response = []
        schema = {
            "type": "array",
            "items": {"type": "object", "properties": {"id": {"type": "number"}}},
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_complex_schema_llm_suggestions(self):
        """Test validation with complex schema similar to SUGGESTIONS_RESPONSE_FORMAT."""
        response = {
            "dataset_description": "A dataset of customer information",
            "columns": [
                {
                    "column_name": "customer_id",
                    "column_description": "Unique identifier for customers",
                    "test_suggestions": ["not_null", "unique"],
                    "constraint_suggestions": ["primary_key"],
                }
            ],
        }
        schema = {
            "type": "object",
            "properties": {
                "dataset_description": {"type": "string"},
                "columns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column_name": {"type": "string"},
                            "column_description": {"type": "string"},
                            "test_suggestions": {
                                "type": ["array", "null"],
                                "items": {"type": "string"},
                            },
                            "constraint_suggestions": {
                                "type": ["array", "null"],
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["column_name", "column_description"],
                    },
                },
            },
            "required": ["dataset_description", "columns"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_null_values_in_nullable_fields(self):
        """Test validation with null values in nullable fields."""
        response = {
            "name": "John Doe",
            "age": None,  # Nullable field
        }
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": ["number", "null"]}},
            "required": ["name"],
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_string_with_pattern(self):
        """Test validation with string pattern constraint."""
        response = {"email": "test@example.com"}
        schema = {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                }
            },
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_number_with_constraints(self):
        """Test validation with number constraints (minimum, maximum)."""
        response = {"age": 25}
        schema = {
            "type": "object",
            "properties": {"age": {"type": "number", "minimum": 0, "maximum": 150}},
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_invalid_number_out_of_range(self):
        """Test validation fails when number is out of range."""
        response = {"age": 200}
        schema = {
            "type": "object",
            "properties": {"age": {"type": "number", "minimum": 0, "maximum": 150}},
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is False

    def test_boolean_values(self):
        """Test validation with boolean values."""
        response = {"is_active": True, "is_verified": False}
        schema = {
            "type": "object",
            "properties": {"is_active": {"type": "boolean"}, "is_verified": {"type": "boolean"}},
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True

    def test_multiple_types(self):
        """Test validation with multiple allowed types."""
        response1 = {"value": "string_value"}
        response2 = {"value": 12345}
        response3 = {"value": None}
        schema = {"type": "object", "properties": {"value": {"type": ["string", "number", "null"]}}}

        for response in [response1, response2, response3]:
            result = LLMProvider.validate_structured_response(response, schema)

            assert result is True

    def test_json_string_with_unicode(self):
        """Test validation with JSON string containing unicode."""
        response = '{"name": "José García", "city": "São Paulo"}'
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "city": {"type": "string"}},
        }

        result = LLMProvider.validate_structured_response(response, schema)

        assert result is True


class TestParseResponse:
    """Test cases for parse_response method."""

    def test_lmstudio_response_without_metrics(self):
        """Test parsing LM Studio response without metrics."""
        # Create mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is a test response."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        params = {"model": "test-model", "temperature": 0.7}
        start_time = time.time()
        end_time = start_time + 1.0

        result = LLMProvider.parse_response(
            mock_response, start_time, end_time, params, return_metrics=False, provider="lmstudio"
        )

        assert result == "This is a test response."

    def test_lmstudio_response_with_metrics(self):
        """Test parsing LM Studio response with metrics."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        params = {"model": "test-model", "temperature": 0.7, "max_tokens": 100}
        start_time = time.time()
        end_time = start_time + 2.0

        result = LLMProvider.parse_response(
            mock_response, start_time, end_time, params, return_metrics=True, provider="lmstudio"
        )

        assert isinstance(result, dict)
        assert "content" in result
        assert "metrics" in result
        assert result["content"] == "Test response"
        assert result["metrics"]["prompt_tokens"] == 10
        assert result["metrics"]["completion_tokens"] == 5
        assert result["metrics"]["total_tokens"] == 15

    def test_lmstudio_with_chain_of_thought(self):
        """Test parsing LM Studio response with chain of thought."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "<think>Reasoning here</think>Final answer"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        params = {"model": "test-model"}
        start_time = time.time()
        end_time = start_time + 1.0

        result = LLMProvider.parse_response(
            mock_response,
            start_time,
            end_time,
            params,
            return_metrics=True,
            return_chain_of_thought=True,
            provider="lmstudio",
        )

        assert isinstance(result, dict)
        assert result["content"] == "Final answer"
        assert "reasoning" in result
        assert result["reasoning"] == "Reasoning here"

    def test_ollama_response_without_metrics(self):
        """Test parsing Ollama response without metrics."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Ollama response"},
            "prompt_eval_count": 8,
            "eval_count": 12,
        }

        params = {"model": "llama2"}
        start_time = time.time()
        end_time = start_time + 1.5

        result = LLMProvider.parse_response(
            mock_response,
            start_time,
            end_time,
            params,
            return_metrics=False,
            provider="ollama",
            endpoint="completions",
        )

        assert result == "Ollama response"

    def test_ollama_response_with_metrics(self):
        """Test parsing Ollama response with metrics."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Ollama test"},
            "prompt_eval_count": 8,
            "eval_count": 12,
        }

        params = {"model": "llama2", "temperature": 0.5}
        start_time = time.time()
        end_time = start_time + 2.0

        result = LLMProvider.parse_response(
            mock_response,
            start_time,
            end_time,
            params,
            return_metrics=True,
            provider="ollama",
            endpoint="completions",
        )

        assert isinstance(result, dict)
        assert result["content"] == "Ollama test"
        assert result["metrics"]["prompt_tokens"] == 8
        assert result["metrics"]["completion_tokens"] == 12

    def test_openai_response_completions_endpoint(self):
        """Test parsing OpenAI response from completions endpoint."""
        # Create mock response with nested objects
        mock_message = Mock()
        mock_message.content = "OpenAI response"

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_usage = Mock()
        mock_usage.prompt_tokens = 15
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 35

        mock_response = Mock()
        mock_response.__dict__ = {"choices": [mock_choice], "usage": mock_usage}

        params = {"model": "gpt-4"}
        start_time = time.time()
        end_time = start_time + 1.0

        result = LLMProvider.parse_response(
            mock_response,
            start_time,
            end_time,
            params,
            return_metrics=True,
            provider="openai",
            endpoint="completions",
        )

        assert isinstance(result, dict)
        assert result["content"] == "OpenAI response"
        assert result["metrics"]["prompt_tokens"] == 15
        assert result["metrics"]["completion_tokens"] == 20

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        mock_response = Mock()
        params = {"model": "test"}
        start_time = time.time()
        end_time = start_time + 1.0

        with pytest.raises(ValueError, match="Invalid provider"):
            LLMProvider.parse_response(
                mock_response,
                start_time,
                end_time,
                params,
                return_metrics=False,
                provider="invalid_provider",
            )

    def test_invalid_endpoint_raises_error(self):
        """Test that invalid endpoint raises ValueError."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        params = {"model": "test"}
        start_time = time.time()
        end_time = start_time + 1.0

        with pytest.raises(ValueError, match="Invalid endpoint"):
            LLMProvider.parse_response(
                mock_response,
                start_time,
                end_time,
                params,
                return_metrics=False,
                provider="lmstudio",
                endpoint="invalid_endpoint",
            )

    def test_invalid_response_format_error(self):
        """Test handling of invalid response format (no json method)."""
        mock_response = Mock()
        # Remove json method to simulate AttributeError
        del mock_response.json

        params = {"model": "test"}
        start_time = time.time()
        end_time = start_time + 1.0

        result = LLMProvider.parse_response(
            mock_response, start_time, end_time, params, return_metrics=False, provider="lmstudio"
        )

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] is True
        assert "Invalid response format" in result["content"]

    def test_missing_choices_in_response(self):
        """Test handling when response is missing expected fields."""
        mock_response = Mock()
        mock_response.json.return_value = {}  # Missing 'choices'

        params = {"model": "test"}
        start_time = time.time()
        end_time = start_time + 1.0

        result = LLMProvider.parse_response(
            mock_response, start_time, end_time, params, return_metrics=False, provider="lmstudio"
        )

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] is True
        assert "Unable to parse response message" in result["content"]

    def test_error_generating_metrics(self):
        """Test error handling when metrics generation fails."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test"}}],
            "usage": None,  # This might cause issues in metrics generation
        }

        params = {}  # Missing required params might cause issues
        start_time = time.time()
        end_time = start_time + 1.0

        result = LLMProvider.parse_response(
            mock_response, start_time, end_time, params, return_metrics=True, provider="lmstudio"
        )

        # Should handle the error gracefully
        assert isinstance(result, dict)

    def test_chain_of_thought_only_with_flag(self):
        """Test that reasoning is only included when flag is set."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "<think>Reasoning</think>Answer"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }

        params = {"model": "test"}
        start_time = time.time()
        end_time = start_time + 1.0

        # Without chain_of_thought flag
        result_no_cot = LLMProvider.parse_response(
            mock_response,
            start_time,
            end_time,
            params,
            return_metrics=True,
            return_chain_of_thought=False,
            provider="lmstudio",
        )

        assert "reasoning" not in result_no_cot
        assert result_no_cot["content"] == "Answer"

    def test_openai_no_chain_of_thought_parsing(self):
        """Test that OpenAI responses don't parse chain of thought."""
        mock_message = Mock()
        mock_message.content = "<think>Should not parse</think>Content"

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_usage = Mock()
        mock_usage.prompt_tokens = 5
        mock_usage.completion_tokens = 3
        mock_usage.total_tokens = 8

        mock_response = Mock()
        mock_response.__dict__ = {"choices": [mock_choice], "usage": mock_usage}

        params = {"model": "gpt-4"}
        start_time = time.time()
        end_time = start_time + 1.0

        result = LLMProvider.parse_response(
            mock_response,
            start_time,
            end_time,
            params,
            return_metrics=False,
            provider="openai",
            endpoint="completions",
        )

        # OpenAI should not parse CoT, returns content as-is
        assert result == "<think>Should not parse</think>Content"

    def test_metrics_calculation_accuracy(self):
        """Test that metrics are calculated correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

        params = {
            "model": "test-model",
            "temperature": 0.8,
            "max_tokens": 200,
            "top_p": 0.95,
            "stop": ["STOP"],
        }
        start_time = 0.0
        end_time = 2.0  # 2 second duration

        result = LLMProvider.parse_response(
            mock_response, start_time, end_time, params, return_metrics=True, provider="lmstudio"
        )

        metrics = result["metrics"]
        assert metrics["response_time"] == 2.0
        assert metrics["prompt_tokens"] == 100
        assert metrics["completion_tokens"] == 50
        assert metrics["total_tokens"] == 150
        assert metrics["tokens_per_second"] == 25.0  # 50 tokens / 2 seconds
        assert metrics["model"] == "test-model"
        assert metrics["temperature"] == 0.8
        assert metrics["max_tokens"] == 200
