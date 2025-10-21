"""Integration tests for LLMProvider chat methods.

Tests the refactored unified chat() method and the provider-specific wrapper methods
to ensure they work correctly with all providers (lmstudio, openai, ollama).
"""

from unittest.mock import Mock, patch

import pytest

from docbt.ai.llm import LLMProvider


class TestUnifiedChatMethod:
    """Test the unified chat() method with different providers."""

    def test_chat_invalid_provider(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Invalid provider"):
            LLMProvider.chat(
                provider="invalid_provider",
                model_name="test-model",
                message="Hello",
            )

    def test_chat_lmstudio_missing_server_url(self):
        """Test that lmstudio without server_url raises ValueError."""
        with pytest.raises(ValueError, match="server_url is required"):
            LLMProvider.chat(
                provider="lmstudio",
                model_name="test-model",
                message="Hello",
            )

    def test_chat_openai_missing_api_key(self):
        """Test that openai without api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key is required"):
            LLMProvider.chat(
                provider="openai",
                model_name="gpt-4",
                message="Hello",
            )

    def test_chat_ollama_missing_server_url(self):
        """Test that ollama without server_url raises ValueError."""
        with pytest.raises(ValueError, match="server_url is required"):
            LLMProvider.chat(
                provider="ollama",
                model_name="llama2",
                message="Hello",
            )

    @patch("docbt.ai.llm.requests.post")
    @patch("docbt.ai.llm.st")
    def test_chat_lmstudio_success(self, mock_st, mock_post):
        """Test successful chat with lmstudio provider."""
        # Mock session state
        mock_st.session_state.get.return_value = 60

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
        mock_post.return_value = mock_response

        result = LLMProvider.chat(
            provider="lmstudio",
            model_name="test-model",
            message="Hello",
            server_url="http://localhost:1234",
        )

        assert result == "Test response"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "http://localhost:1234/v1/chat/completions" in str(call_args)

    @patch("docbt.ai.llm.requests.post")
    @patch("docbt.ai.llm.st")
    def test_chat_lmstudio_with_metrics(self, mock_st, mock_post):
        """Test lmstudio chat with return_metrics=True."""
        mock_st.session_state.get.return_value = 60

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
        mock_post.return_value = mock_response

        result = LLMProvider.chat(
            provider="lmstudio",
            model_name="test-model",
            message="Hello",
            server_url="http://localhost:1234",
            return_metrics=True,
        )

        assert isinstance(result, dict)
        assert result["content"] == "Test response"
        assert "metrics" in result
        assert "response_time" in result["metrics"]
        assert "prompt_tokens" in result["metrics"]
        assert "completion_tokens" in result["metrics"]

    @patch("docbt.ai.llm.OpenAI")
    @patch("docbt.ai.llm.st")
    def test_chat_openai_success(self, mock_st, mock_openai_class):
        """Test successful chat with openai provider."""
        mock_st.session_state.get.return_value = 60

        # Mock OpenAI client and response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_choice = Mock()
        mock_choice.message.content = "OpenAI response"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 25

        mock_client.chat.completions.create.return_value = mock_response

        result = LLMProvider.chat(
            provider="openai",
            model_name="gpt-4",
            message="Hello",
            api_key="test-api-key",
        )

        assert result == "OpenAI response"
        mock_openai_class.assert_called_once_with(api_key="test-api-key")
        mock_client.chat.completions.create.assert_called_once()

    @patch("docbt.ai.llm.OpenAI")
    @patch("docbt.ai.llm.st")
    def test_chat_openai_gpt5_model(self, mock_st, mock_openai_class):
        """Test chat with GPT-5 model (special handling)."""
        mock_st.session_state.get.return_value = 60

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_choice = Mock()
        mock_choice.message.content = "GPT-5 response"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 30

        mock_client.chat.completions.create.return_value = mock_response

        result = LLMProvider.chat(
            provider="openai",
            model_name="gpt-5-turbo",
            message="Hello",
            api_key="test-api-key",
        )

        assert result == "GPT-5 response"
        # Verify that temperature/top_p/stop are not passed for GPT-5
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-5-turbo"
        assert call_kwargs["reasoning_effort"] == "low"

    @patch("docbt.ai.llm.requests.post")
    @patch("docbt.ai.llm.st")
    def test_chat_ollama_success(self, mock_st, mock_post):
        """Test successful chat with ollama provider."""
        mock_st.session_state.get.return_value = 60

        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Ollama response"},
            "prompt_eval_count": 12,
            "eval_count": 18,
        }
        mock_post.return_value = mock_response

        result = LLMProvider.chat(
            provider="ollama",
            model_name="llama2",
            message="Hello",
            server_url="http://localhost:11434",
        )

        assert result == "Ollama response"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "http://localhost:11434/api/chat/" in str(call_args)

    @patch("docbt.ai.llm.requests.post")
    @patch("docbt.ai.llm.st")
    def test_chat_with_system_prompt(self, mock_st, mock_post):
        """Test chat with system prompt."""
        mock_st.session_state.get.return_value = 60

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response with system prompt"}}],
            "usage": {"prompt_tokens": 15, "completion_tokens": 10},
        }
        mock_post.return_value = mock_response

        result = LLMProvider.chat(
            provider="lmstudio",
            model_name="test-model",
            message="Hello",
            server_url="http://localhost:1234",
            system_prompt="You are a helpful assistant.",
        )

        assert result == "Response with system prompt"
        # Check that system prompt was included in messages
        call_kwargs = mock_post.call_args[1]
        messages = call_kwargs["json"]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."

    @patch("docbt.ai.llm.requests.post")
    @patch("docbt.ai.llm.st")
    def test_chat_with_chat_history(self, mock_st, mock_post):
        """Test chat with conversation history."""
        mock_st.session_state.get.return_value = 60

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response with history"}}],
            "usage": {"prompt_tokens": 30, "completion_tokens": 15},
        }
        mock_post.return_value = mock_response

        chat_history = [
            ("Previous user message", "Previous assistant response"),
        ]

        result = LLMProvider.chat(
            provider="lmstudio",
            model_name="test-model",
            message="Hello again",
            server_url="http://localhost:1234",
            chat_history=chat_history,
        )

        assert result == "Response with history"
        # Check that chat history was included
        call_kwargs = mock_post.call_args[1]
        messages = call_kwargs["json"]["messages"]
        assert len(messages) == 3  # 2 history messages + 1 current
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Previous user message"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Previous assistant response"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "Hello again"

    @patch("docbt.ai.llm.requests.post")
    @patch("docbt.ai.llm.st")
    def test_chat_with_stop_sequences(self, mock_st, mock_post):
        """Test chat with stop sequences."""
        mock_st.session_state.get.return_value = 60

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_post.return_value = mock_response

        result = LLMProvider.chat(
            provider="lmstudio",
            model_name="test-model",
            message="Hello",
            server_url="http://localhost:1234",
            stop_sequences=["STOP", "END"],  # Pass as list directly
        )

        assert result == "Response"
        # Check that stop sequences were included correctly
        call_kwargs = mock_post.call_args[1]
        stop_list = call_kwargs["json"]["stop"]
        assert stop_list == ["STOP", "END"]

    @patch("docbt.ai.llm.requests.post")
    @patch("docbt.ai.llm.st")
    def test_chat_with_response_format(self, mock_st, mock_post):
        """Test chat with structured response format."""
        mock_st.session_state.get.return_value = 60

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"name": "John", "age": 30}'}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10},
        }
        mock_post.return_value = mock_response

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "person_schema",
                "schema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                    "required": ["name", "age"],
                },
            },
        }

        result = LLMProvider.chat(
            provider="lmstudio",
            model_name="test-model",
            message="Extract person info",
            server_url="http://localhost:1234",
            response_format=response_format,
            return_metrics=True,
        )

        assert isinstance(result, dict)
        assert isinstance(result["content"], dict)
        assert result["content"]["name"] == "John"
        assert result["content"]["age"] == 30


class TestChatWrapperMethods:
    """Test the provider-specific wrapper methods."""

    @patch("docbt.ai.llm.LLMProvider.chat")
    def test_chat_with_lmstudio_calls_unified_chat(self, mock_chat):
        """Test that chat_with_lmstudio calls the unified chat method."""
        mock_chat.return_value = "Test response"

        result = LLMProvider.chat_with_lmstudio(
            server_url="http://localhost:1234",
            model_name="test-model",
            message="Hello",
            max_tokens=500,
            temperature=0.8,
        )

        assert result == "Test response"
        mock_chat.assert_called_once()
        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs["provider"] == "lmstudio"
        assert call_kwargs["server_url"] == "http://localhost:1234"
        assert call_kwargs["model_name"] == "test-model"
        assert call_kwargs["message"] == "Hello"
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["temperature"] == 0.8

    @patch("docbt.ai.llm.LLMProvider.chat")
    def test_chat_with_openai_calls_unified_chat(self, mock_chat):
        """Test that chat_with_openai calls the unified chat method."""
        mock_chat.return_value = "OpenAI response"

        result = LLMProvider.chat_with_openai(
            api_key="test-key",
            model_name="gpt-4",
            message="Hello",
            endpoint="completions",
        )

        assert result == "OpenAI response"
        mock_chat.assert_called_once()
        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs["provider"] == "openai"
        assert call_kwargs["api_key"] == "test-key"
        assert call_kwargs["model_name"] == "gpt-4"
        assert call_kwargs["endpoint"] == "completions"
        assert call_kwargs["return_chain_of_thought"] is False

    @patch("docbt.ai.llm.LLMProvider.chat")
    def test_chat_with_ollama_calls_unified_chat(self, mock_chat):
        """Test that chat_with_ollama calls the unified chat method."""
        mock_chat.return_value = "Ollama response"

        result = LLMProvider.chat_with_ollama(
            server_url="http://localhost:11434",
            model_name="llama2",
            message="Hello",
            return_chain_of_thought=True,
        )

        assert result == "Ollama response"
        mock_chat.assert_called_once()
        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs["provider"] == "ollama"
        assert call_kwargs["server_url"] == "http://localhost:11434"
        assert call_kwargs["model_name"] == "llama2"
        assert call_kwargs["return_chain_of_thought"] is True


class TestHelperMethods:
    """Test the helper methods used by the unified chat method."""

    def test_build_messages_basic(self):
        """Test basic message building."""
        messages = LLMProvider._build_messages("Hello")

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    def test_build_messages_with_system_prompt(self):
        """Test message building with system prompt."""
        messages = LLMProvider._build_messages(
            "Hello", system_prompt="You are a helpful assistant."
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_build_messages_with_chat_history(self):
        """Test message building with chat history."""
        chat_history = [
            ("First user message", "First assistant response"),
            ("Second user message", "Second assistant response"),
        ]

        messages = LLMProvider._build_messages("Third user message", chat_history=chat_history)

        assert len(messages) == 5
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "First user message"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "First assistant response"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "Second user message"
        assert messages[3]["role"] == "assistant"
        assert messages[3]["content"] == "Second assistant response"
        assert messages[4]["role"] == "user"
        assert messages[4]["content"] == "Third user message"

    def test_build_messages_complete(self):
        """Test message building with all parameters."""
        chat_history = [("Previous", "Response")]

        messages = LLMProvider._build_messages(
            "Current message", system_prompt="System prompt", chat_history=chat_history
        )

        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Previous"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Response"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "Current message"

    @patch("docbt.ai.llm.requests.post")
    def test_make_lmstudio_request(self, mock_post):
        """Test LM Studio request helper."""
        mock_response = Mock()
        mock_post.return_value = mock_response

        api_params = {"model": "test", "messages": []}
        result = LLMProvider._make_lmstudio_request("http://localhost:1234", api_params, 60)

        assert result == mock_response
        mock_post.assert_called_once_with(
            "http://localhost:1234/v1/chat/completions",
            json=api_params,
            timeout=60,
        )

    @patch("docbt.ai.llm.requests.post")
    def test_make_ollama_request(self, mock_post):
        """Test Ollama request helper."""
        mock_response = Mock()
        mock_post.return_value = mock_response

        api_params = {"model": "llama2", "messages": []}
        result = LLMProvider._make_ollama_request("http://localhost:11434", api_params, 60)

        assert result == mock_response
        mock_post.assert_called_once_with(
            "http://localhost:11434/api/chat/",
            json=api_params,
            timeout=60,
        )

    def test_make_openai_request_completions(self):
        """Test OpenAI request helper with completions endpoint."""
        mock_client = Mock()
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        result = LLMProvider._make_openai_request(
            mock_client,
            "gpt-4",
            [{"role": "user", "content": "Hello"}],
            1000,
            0.7,
            0.9,
            [],
            None,
            "completions",
        )

        assert result == mock_response
        mock_client.chat.completions.create.assert_called_once()

    def test_make_openai_request_create_endpoint(self):
        """Test OpenAI request helper with create endpoint."""
        mock_client = Mock()
        mock_response = Mock()
        mock_client.responses.create.return_value = mock_response

        result = LLMProvider._make_openai_request(
            mock_client,
            "gpt-4",
            [{"role": "user", "content": "Hello"}],
            1000,
            0.7,
            0.9,
            [],
            None,
            "create",
        )

        assert result == mock_response
        mock_client.responses.create.assert_called_once()

    def test_validate_and_parse_structured_response_lmstudio(self):
        """Test structured response validation for lmstudio."""
        response = {"content": '{"name": "John", "age": 30}'}
        response_format = {
            "json_schema": {
                "schema": {"properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
            }
        }

        result = LLMProvider._validate_and_parse_structured_response(
            response, response_format, "lmstudio"
        )

        assert isinstance(result["content"], dict)
        assert result["content"]["name"] == "John"
        assert result["content"]["age"] == 30

    def test_validate_and_parse_structured_response_ollama(self):
        """Test structured response validation for ollama."""
        response = {"content": '{"status": "success", "count": 5}'}
        response_format = {
            "properties": {"status": {"type": "string"}, "count": {"type": "integer"}}
        }

        result = LLMProvider._validate_and_parse_structured_response(
            response, response_format, "ollama"
        )

        assert isinstance(result["content"], dict)
        assert result["content"]["status"] == "success"
        assert result["content"]["count"] == 5

    def test_validate_and_parse_structured_response_no_format(self):
        """Test that response is returned unchanged when no format specified."""
        response = {"content": "Plain text response"}

        result = LLMProvider._validate_and_parse_structured_response(response, None, "lmstudio")

        assert result == response
        assert result["content"] == "Plain text response"

    def test_validate_and_parse_structured_response_invalid(self):
        """Test that invalid structured response raises ValueError."""
        response = {"content": '{"name": "John"}'}  # Missing required 'age'
        response_format = {
            "json_schema": {
                "schema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                    "required": ["name", "age"],
                }
            }
        }

        with pytest.raises(ValueError, match="Structured response validation failed"):
            LLMProvider._validate_and_parse_structured_response(
                response, response_format, "lmstudio"
            )
