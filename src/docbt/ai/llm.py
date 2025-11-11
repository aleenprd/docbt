"""LLM provider module for interacting with OpenAI-compatible LLM APIs like LM Studio, Ollama, OpenAI, etc."""

import json
import re
import time

import requests
import streamlit as st
import tiktoken
from jsonschema import ValidationError, validate
from loguru import logger
from openai import OpenAI

EXAMPLE_SUGGESTION = {
    "dataset_description": "This dataset contains measurements of flower petal and sepal dimensions for different species of flowers.",
    "columns": [
        {
            "column_name": "id",
            "column_description": "A unique identifier for each flower measurement.",
            "test_suggestions": ["unique", "not_null"],
            "constraint_suggestions": ["primary_key"],
        },
        {
            "column_name": "sepal_length",
            "column_description": "The length of the sepal of the flower, measured in centimeters.",
            "test_suggestions": ["not_null"],
            "constraint_suggestions": ["not_null"],
        },
        {
            "column_name": "sepal_width",
            "column_description": "The width of the sepal of the flower, measured in centimeters.",
            "test_suggestions": ["not_null"],
            "constraint_suggestions": ["not_null"],
        },
        {
            "column_name": "petal_length",
            "column_description": "The length of the petal of the flower, measured in centimeters.",
            "test_suggestions": ["not_null"],
            "constraint_suggestions": ["not_null"],
        },
        {
            "column_name": "petal_width",
            "column_description": "The width of the petal of the flower, measured in centimeters.",
            "test_suggestions": ["not_null"],
            "constraint_suggestions": ["not_null"],
        },
        {
            "column_name": "species",
            "column_description": "The species of the flower.",
            "test_suggestions": ["accepted_values", "not_null"],
            "constraint_suggestions": ["not_null"],
        },
    ],
}

DEFAULT_SYSTEM_PROMPT = """
You are a helpful AI assistant specialized in data, analytics engineering, SQL, data modelling and dbt (Data Build Tool).
Columns and models can have multiple tests applied to them or none at all. Same for constraints.

## Your Expertise
- Data tests are assertions you make about your models to ensure data quality and integrity. They help catch issues early in the data pipeline.
- We can categorize tests into two main types: column-level tests and model-level tests.
    - Column-level tests validate individual columns.
    - Model-level tests validate the entire dataset or relationships between tables.
- SQL data constraints enforce rules at the database level to maintain data integrity.

### Generic Column-Level Tests:
- **not_null**: Ensures column has no NULL values. Use for primary keys, required fields.
- **unique**: Ensures all values in column are unique. Essential for primary keys, identifiers.
- **accepted_values**: Validates column contains only specified values. Use for: status fields, categorical data, enum-like columns of low cardinality.
- **relationships**: Validates foreign key relationships. Ensures referential integrity between tables. Each value in the column must exist in the referenced table/column.

Always suggest appropriate descriptions, constraints and tests based on column data types, business context, and data quality requirements.
You can only suggest tests from the following list:
- not_null
- unique
- accepted_values
- relationships
"""

DEFAULT_CONSTRAINTS_PROMPT = """
### SQL Constraints
- **not_null**: Column cannot have any NULL values.
- **unique**: All values in the column must be unique.
- **primary_key**: The unique identifier for a record in a table. If this constraint is applied, the column must also be not null and unique. A single column can be a primary key.
- **foreign_key**: Ensures referential integrity by linking to a primary key in another table. This must also be not null.

You can only suggest constraints from the following list:
- not_null
- unique
- primary_key
- foreign_key
"""

BIGQUERY_CONSTRAINTS_PROMPT = """
### SQL Constraints
- **not_null**: Column cannot have any NULL values.
- **primary_key**: The unique identifier for a record in a table. If this constraint is applied, the column must also be not null and unique. A single column can be a primary key.
- **foreign_key**: Ensures referential integrity by linking to a primary key in another table. This must also be not null.

You can only suggest constraints from the following list:
- not_null
- primary_key
- foreign_key
"""

SUGGESTION_PROMPT = """
Based on this sample data, and the associated statistics, your task will be to identify the following:
1. [REQUIRED] A concise description of the dataset in one sentence based on the column names, data types, and values observed.
2. For each column, provide:
    - [REQUIRED] A concise description of the column in one sentence..
    - [OPTIONAL] A suggestion of one or more constraints that could be applied to this column.
    - [OPTIONAL] A suggestion of one or more data tests that could be applied to this column.

You must include the dataset description and column descriptions for all columns withot exception.
If you find constraints appropriate for a column, you must also suggest the related data tests.
If no relevant constraints or tests are applicable, you can respond with an empty list for those fields.

IMPORTANT:
- The data sample itself will always be a very small proportion of the whole dataset and may not contain all possible values or edge cases.
- For example, a column may appear to have only non-null values in the sample, but could contain nulls in the full dataset.
- It is only provided to help you understand the data better.
- Do not extrapolate conclusions from the sample data to the entire dataset.
- Do not reference any specific values from the sample data in your descriptions or any statistics related to the sample data.
"""

SUGGESTIONS_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "llm_suggestions",
        "schema": {
            "type": "object",
            "properties": {
                "dataset_description": {
                    "type": "string",
                    "description": "A concise description of the dataset in one sentence.",
                },
                "columns": {
                    "type": "array",
                    "description": "A list of columns with their descriptions and [optional] constraints and test suggestions.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column_name": {
                                "type": "string",
                                "description": "The name of the column.",
                            },
                            "column_description": {
                                "type": "string",
                                "description": "A concise description of the column in one sentence.",
                            },
                            "test_suggestions": {
                                "type": "array",
                                "description": "A list of suggested data tests for this column, if any.",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "not_null",
                                        "unique",
                                        "accepted_values",
                                        "relationships",
                                    ],
                                },
                            },
                            "constraint_suggestions": {
                                "type": "array",
                                "description": "A list of suggested constraints for this column, if any.",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "not_null",
                                        "unique",
                                        "primary_key",
                                        "foreign_key",
                                    ],
                                },
                            },
                        },
                        "required": [
                            "column_name",
                            "column_description",
                        ],
                    },
                },
            },
            "required": ["dataset_description", "columns"],
        },
    },
}

SUGGESTIONS_RESPONSE_FORMAT_OLLAMA = {
    "type": "object",
    "properties": {
        "dataset_description": {
            "type": "string",
            "description": "A concise description of the dataset in one sentence.",
        },
        "columns": {
            "type": "array",
            "description": "A list of columns with their descriptions and [optional] constraints and test suggestions.",
            "items": {
                "type": "object",
                "properties": {
                    "column_name": {
                        "type": "string",
                        "description": "The name of the column.",
                    },
                    "column_description": {
                        "type": "string",
                        "description": "A concise description of the column in one sentence.",
                    },
                    "test_suggestions": {
                        "type": "array",
                        "description": "A list of suggested data tests for this column, if any.",
                        "items": {
                            "type": "string",
                            "enum": [
                                "not_null",
                                "unique",
                                "accepted_values",
                                "relationships",
                            ],
                        },
                    },
                    "constraint_suggestions": {
                        "type": "array",
                        "description": "A list of suggested constraints for this column, if any.",
                        "items": {
                            "type": "string",
                            "enum": [
                                "not_null",
                                "unique",
                                "primary_key",
                                "foreign_key",
                            ],
                        },
                    },
                },
                "required": [
                    "column_name",
                    "column_description",
                ],
            },
        },
    },
    "required": ["dataset_description", "columns"],
}


class LLMProvider:
    @staticmethod
    def count_tokens(text, model="gpt-4") -> int:
        """Count tokens in text using tiktoken.

        Args:
            text (str): The input text to count tokens for.
            model (str): The model name to use for tokenization.

        Returns:
            int: The number of tokens in the input text.
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for newer models
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))

    @staticmethod
    def parse_chain_of_thought(response: str | dict, provider: str) -> tuple[str | None, str]:
        """Parse chain of thought reasoning from response text.

        Args:
            response (str | dict): The full response text from the LLM.

        Returns:
            tuple[str | None, str]: A tuple containing the extracted reasoning (or None if not found)
                                and the cleaned response text without the reasoning.
        """
        if provider not in ["lmstudio", "openai", "ollama"]:
            raise ValueError("Invalid provider. Must be 'lmstudio', 'openai' or 'ollama'.")

        if provider in ["openai"]:
            raise NotImplementedError("Chain of thought parsing for OpenAI is not implemented yet.")

        if not response:
            logger.error("Empty response text received!")
            return None, None

        cot_patterns = [
            r"<think>(.*?)</think>",  # Explicit think tags (check this first)
            r"<thinking>(.*?)</thinking>",  # Explicit thinking tags
            r"<reasoning>(.*?)</reasoning>",  # Reasoning tags
            r"<thought>(.*?)</thought>",  # Thought tags
            r"<analysis>(.*?)</analysis>",  # Analysis tags
            r"^(.*?)</think>",  # Start of text to </think>
        ]

        if isinstance(response, dict):
            response_content = response.get("content", "").strip()

            for key in ["reasoning_content"]:
                if response.get(key, None) is not None:
                    logger.debug(f"Found explicit {key} field in response.")
                    reasoning = response[key].strip()

                    logger.debug(f"Extracted reasoning from explicit field: {reasoning}")
                    return reasoning, response_content

        elif isinstance(response, str):
            response_content = response.strip()

        # Check for explicit tags in the response text
        for pattern in cot_patterns:
            match = re.search(pattern, response_content, re.DOTALL | re.IGNORECASE)

            # If a match is found, extract the reasoning and clean the response
            if match:
                logger.debug(f"Checking pattern: {pattern}, match found.")
                logger.warning(f"Found chain of thought markers using pattern: {pattern}")
                reasoning = match.group(1).strip()
                logger.debug(f"Extracted reasoning: {reasoning}")

                # Remove the reasoning from the main response
                clean_response = re.sub(
                    pattern, "", response_content, flags=re.DOTALL | re.IGNORECASE
                ).strip()

                return reasoning, clean_response

        # If no explicit tags, it means the model does not provide CoT
        logger.debug("No chain of thought markers found in response.")
        return None, response_content

    @staticmethod
    def parse_stop_sequences(stop_sequences: str) -> list[str] | None:
        """Parse stop sequences from a comma-separated string.

        Args:
            stop_sequences (str): Comma-separated stop sequences.

        Returns:
            list[str] | None: A list of stop sequences or None if input is empty.
        """
        if not stop_sequences:
            return None

        # Split by comma and strip whitespace
        stop_list = [s.strip() for s in stop_sequences.split(",") if s.strip()]

        return stop_list if stop_list else None

    @staticmethod
    def generate_metrics(
        response: dict,
        start_time: float,
        end_time: float,
        params: dict,
        provider: str = "lmstudio",
        endpoint: str = "completions",
    ) -> dict:
        """Generate performance metrics from the LLM response.

        Args:
            response (dict): The full response from the LLM API.
            start_time (float): The start time of the request.
            end_time (float): The end time of the request.
            params (dict): The parameters used for the API call.
            provider (str): The LLM provider ("lmstudio", "openai", or "ollama").
            endpoint (str): The API endpoint used ("completions", "create", or "generate").

        Raises:
            ValueError: If an invalid provider is provided.

        Returns:
            dict: A dictionary containing performance metrics.
        """
        if provider not in ["lmstudio", "openai", "ollama"]:
            raise ValueError("Invalid provider. Must be 'lmstudio', 'openai' or 'ollama'.")

        if endpoint not in ["completions", "create", "generate"]:
            raise ValueError("Invalid endpoint. Must be 'completions', 'create', or 'generate'.")

        if provider == "ollama":
            if endpoint == "completions":
                prompt_tokens = response.get("prompt_eval_count", 0)
                completion_tokens = response.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens
            elif endpoint == "generate":
                raise NotImplementedError(
                    "Metrics generation for Ollama endpoint 'generate' is not implemented yet."
                )
            else:
                raise ValueError(
                    "Invalid endpoint for Ollama. Must be 'completions' or 'generate'."
                )

        elif provider == "lmstudio":
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

        elif provider == "openai":
            if endpoint == "create":
                usage = response.get("usage", {}).__dict__
                prompt_tokens = usage.get("input_tokens", 0)
                completion_tokens = usage.get("output_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
            elif endpoint == "completions":
                usage = response.get("usage", {})
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens

        tokens_per_second = (
            round(
                completion_tokens / (end_time - start_time),
                2,
            )
            if (end_time - start_time) > 0
            else 0
        )

        return {
            "response_time": round(end_time - start_time, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "tokens_per_second": tokens_per_second,
            "model": params.get("model"),
            "max_tokens": params.get("max_tokens"),
            "temperature": params.get("temperature"),
            "top_p": params.get("top_p"),
            "stop": params.get("stop"),
        }

    @staticmethod
    def validate_structured_response(response: str | dict, schema: dict) -> bool:
        """Validate the structured response against the provided JSON schema.

        Args:
            response (str |dict): The structured response from the LLM.
            schema (dict): The JSON schema to validate against.

        Returns:
            bool: True if the response is valid, False otherwise.
        """
        try:
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse response string as JSON: {response}")
                    return False
            validate(instance=response, schema=schema)
            return True
        except ValidationError as e:
            logger.error(f"Structured response validation error: {e}")
            return False

    @staticmethod
    def parse_response(
        response: str,
        start_time: float,
        end_time: float,
        params: dict,
        return_metrics: bool,
        return_chain_of_thought: bool = False,
        provider: str = "lmstudio",
        endpoint: str = "completions",
    ) -> str:
        """Parse the response from the OpenAI-compatible LLM API.

        Args:
            response (str): The raw response from the LLM API.
            start_time (float): The start time of the request.
            end_time (float): The end time of the request.
            params (dict): The parameters used for the API call.
            return_metrics (bool): Whether to return performance metrics.
            return_chain_of_thought (bool): Whether to extract and return chain of thought reasoning.
            provider (str): The LLM provider ("lmstudio", "openai", or "ollama").
            endpoint (str): The API endpoint used ("completions", "create", or "generate").

        Raises:
            ValueError: If an invalid api_version is provided.
            ValueError: If an invalid endpoint is provided.

        Returns:
            str | dict: The cleaned response text, or a dictionary with content and metrics if requested.
        """
        if provider not in ["lmstudio", "openai", "ollama"]:
            raise ValueError("Invalid provider. Must be 'lmstudio', 'openai' or 'ollama'.")

        try:
            if provider == "ollama":
                response_data = response.json()
            elif provider == "lmstudio":
                response_data = response.json()
            elif provider == "openai":
                response_data = response.__dict__
        except AttributeError:
            logger.error("Response is not a valid JSON object.")
            return {"content": "Error: Invalid response format.", "error": True}

        if endpoint not in ["completions", "create", "generate"]:
            raise ValueError("Invalid endpoint. Must be 'completions', 'create', or 'generate'.")

        logger.debug(f"LLM response data: {response_data}")

        try:
            if provider == "lmstudio":
                response_message = response_data["choices"][0]["message"]
            elif provider == "openai":
                if endpoint == "completions":
                    response_message = response_data["choices"][0].message.content
                elif endpoint == "create":
                    output = response_data.get("output")
                    message_block = [o for o in output if o.type == "message"][0]
                    response_message = message_block.content[0].text
            elif provider == "ollama":
                if endpoint == "completions":
                    response_message = response_data["message"]["content"]

        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing response message: {e}")
            return {
                "content": "Error: Unable to parse response message.",
                "error": True,
            }

        logger.debug(f"LLM response message: {response_message}")

        # Always parse chain of thought to clean the response
        if provider == "ollama":
            reasoning, response_content = LLMProvider.parse_chain_of_thought(
                response_message, provider
            )
        elif provider == "openai":
            reasoning, response_content = None, response_message
        elif provider == "lmstudio":
            reasoning, response_content = LLMProvider.parse_chain_of_thought(
                response_message, provider
            )
        logger.debug(f"Cleaned response content: {response_content}")
        logger.debug(f"Extracted reasoning: {reasoning}")

        try:
            if return_metrics:
                result = {"content": response_content}
                result["metrics"] = LLMProvider.generate_metrics(
                    response=response_data,
                    start_time=start_time,
                    end_time=end_time,
                    params=params,
                    provider=provider,
                    endpoint=endpoint,
                )

            else:
                return response_content
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return {"content": "Error: Unable to generate metrics.", "error": True}

        if reasoning and return_chain_of_thought:
            result["reasoning"] = reasoning

        return result

    @staticmethod
    def _build_messages(
        message: str,
        system_prompt: str = None,
        chat_history: tuple[str, str] = None,
    ) -> list[dict]:
        """Build message list with system prompt and chat history.

        Args:
            message (str): The current user message.
            system_prompt (str, optional): System prompt to set context.
            chat_history (tuple[str, str], optional): Previous conversation history.

        Returns:
            list[dict]: List of message dictionaries.
        """
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add chat history
        if chat_history:
            for user_msg, assistant_msg in chat_history:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": assistant_msg})

        # Add current message from user
        messages.append({"role": "user", "content": message})

        return messages

    @staticmethod
    def _make_lmstudio_request(
        server_url: str,
        api_params: dict,
        timeout: int,
    ) -> requests.Response:
        """Make HTTP request to LM Studio API.

        Args:
            server_url (str): Base URL of the LM Studio server.
            api_params (dict): API parameters for the request.
            timeout (int): Request timeout in seconds.

        Returns:
            requests.Response: The API response.
        """
        return requests.post(
            f"{server_url}/v1/chat/completions",
            json=api_params,
            timeout=timeout,
        )

    @staticmethod
    def _make_openai_request(
        client: OpenAI,
        model_name: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop_list: list[str],
        response_format: dict,
        endpoint: str,
    ):
        """Make request to OpenAI API.

        Args:
            client (OpenAI): OpenAI client instance.
            model_name (str): Name of the model to use.
            messages (list[dict]): List of message dictionaries.
            max_tokens (int): Maximum tokens to generate.
            temperature (float): Sampling temperature.
            top_p (float): Nucleus sampling probability.
            stop_list (list[str]): List of stop sequences.
            response_format (dict): Structured output format.
            endpoint (str): API endpoint to use.

        Returns:
            Response object from OpenAI API.
        """
        if endpoint == "completions":
            if "gpt-5" in model_name:
                logger.warning("GPT-5 models do not support temperature/top_p/stop parameters.")
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                    response_format=response_format if response_format else None,
                    reasoning_effort="low",
                )
            else:
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    top_p=top_p,
                    stop=stop_list,
                    response_format=response_format if response_format else None,
                    reasoning_effort="low",
                )
        elif endpoint == "create":
            return client.responses.create(
                model=model_name,
                input=messages,
                reasoning={"effort": "low"},
            )
        elif endpoint == "generate":
            raise NotImplementedError(
                "The 'generate' endpoint (for Ollama) is not implemented yet."
            )

    @staticmethod
    def _make_ollama_request(
        server_url: str,
        api_params: dict,
        timeout: int,
    ) -> requests.Response:
        """Make HTTP request to Ollama API.

        Args:
            server_url (str): Base URL of the Ollama server.
            api_params (dict): API parameters for the request.
            timeout (int): Request timeout in seconds.

        Returns:
            requests.Response: The API response.
        """
        return requests.post(
            f"{server_url}/api/chat/",
            json=api_params,
            timeout=timeout,
        )

    @staticmethod
    def _validate_and_parse_structured_response(
        response: dict,
        response_format: dict,
        provider: str,
    ) -> dict:
        """Validate and parse structured response.

        Args:
            response (dict): Response dictionary with content.
            response_format (dict): Expected response format schema.
            provider (str): LLM provider name.

        Returns:
            dict: Response with parsed content or error.
        """
        if not response_format:
            return response

        # Get schema based on provider
        if provider == "ollama":
            schema = response_format  # Ollama uses the full format as schema
        else:
            schema = response_format["json_schema"][
                "schema"
            ]  # Use full schema, not just properties

        is_valid = LLMProvider.validate_structured_response(
            response=response["content"],
            schema=schema,
        )

        if not is_valid:
            error_msg = "Structured response validation failed."
            logger.error(error_msg)
            st.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Structured response validation succeeded.")
        response["content"] = json.loads(response["content"])
        return response

    @staticmethod
    def chat(
        provider: str,
        model_name: str,
        message: str,
        server_url: str = None,
        api_key: str = None,
        chat_history: tuple[str, str] = None,
        return_metrics: bool = False,
        system_prompt: str = None,
        return_chain_of_thought: bool = False,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: list[str] | None = None,
        response_format: dict = None,
        timeout: int = 60,
        endpoint: str = "completions",
    ) -> str | dict:
        """Unified chat method for all LLM providers.

        Args:
            provider (str): LLM provider ("lmstudio", "openai", or "ollama").
            model_name (str): The name of the model to use.
            message (str): The current user message to send.
            server_url (str, optional): Base URL for lmstudio/ollama servers.
            api_key (str, optional): API key for OpenAI.
            chat_history (tuple[str, str], optional): Previous conversation history.
            return_metrics (bool, optional): Whether to return performance metrics. Defaults to False.
            system_prompt (str, optional): System prompt to set the context.
            return_chain_of_thought (bool, optional): Whether to extract CoT reasoning. Defaults to False.
            max_tokens (int, optional): Maximum tokens to generate. Defaults to 1000.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            top_p (float, optional): Nucleus sampling probability. Defaults to 0.9.
            stop_sequences (list[str] | None, optional): List of stop sequences. Defaults to None.
            response_format (dict, optional): Structured output format. Defaults to {}.
            timeout (int, optional): Request timeout in seconds. Defaults to 60.
            endpoint (str, optional): API endpoint (for OpenAI). Defaults to "completions".

        Returns:
            str | dict: The AI response text, or dict with content and metrics if requested.

        Raises:
            ValueError: If invalid provider or missing required parameters.
        """
        # Validate provider
        if response_format is None:
            response_format = {}
        if provider not in ["lmstudio", "openai", "ollama"]:
            raise ValueError(
                f"Invalid provider '{provider}'. Must be 'lmstudio', 'openai', or 'ollama'."
            )

        # Validate required parameters per provider
        if provider in ["lmstudio", "ollama"] and not server_url:
            raise ValueError(f"server_url is required for {provider}")
        if provider == "openai" and not api_key:
            raise ValueError("api_key is required for openai")

        try:
            # Build messages (common across all providers)
            messages = LLMProvider._build_messages(message, system_prompt, chat_history)

            # Parse stop sequences - handle both string and list inputs
            if stop_sequences:
                if isinstance(stop_sequences, list):
                    stop_list = stop_sequences
                else:
                    stop_list = LLMProvider.parse_stop_sequences(stop_sequences)
            else:
                stop_list = []

            # Get timeout from session state if available
            timeout = st.session_state.get("api_timeout", timeout)

            # Build base API parameters
            api_params = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "stop": stop_list,
            }

            # Start timing
            start_time = time.time()

            # Provider-specific request handling
            if provider == "lmstudio":
                if response_format:
                    api_params["response_format"] = response_format

                response = LLMProvider._make_lmstudio_request(server_url, api_params, timeout)

            elif provider == "openai":
                if endpoint not in ["completions", "create", "generate"]:
                    raise ValueError(
                        "Invalid endpoint. Must be 'completions', 'create', or 'generate'."
                    )

                client = OpenAI(api_key=api_key)
                if response_format:
                    api_params["response_format"] = response_format

                response = LLMProvider._make_openai_request(
                    client,
                    model_name,
                    messages,
                    max_tokens,
                    temperature,
                    top_p,
                    stop_list,
                    response_format,
                    endpoint,
                )

            elif provider == "ollama":
                api_params["stream"] = False
                if response_format:
                    api_params["format"] = response_format

                response = LLMProvider._make_ollama_request(server_url, api_params, timeout)

            # End timing
            end_time = time.time()

            # Parse response (common across all providers)
            parsed_response = LLMProvider.parse_response(
                response,
                start_time,
                end_time,
                api_params,
                return_metrics,
                return_chain_of_thought,
                provider=provider,
                endpoint=endpoint if provider == "openai" else "completions",
            )

            # Validate and parse structured response if needed
            if response_format and isinstance(parsed_response, dict):
                parsed_response = LLMProvider._validate_and_parse_structured_response(
                    parsed_response, response_format, provider
                )

            return parsed_response

        except Exception as e:
            error_msg = f"{provider.capitalize()} API error: {e}"
            logger.error(error_msg)
            st.error(error_msg)
            if provider == "openai":
                raise e
            return None

    @staticmethod
    def chat_with_lmstudio(
        server_url: str,
        model_name: str,
        message: str,
        chat_history: tuple[str, str] = None,
        return_metrics: bool = False,
        system_prompt: str = None,
        return_chain_of_thought: bool = False,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: list[str] | None = None,
        response_format: dict = None,
        timeout: int = 60,
    ) -> str | dict:
        """Send a chat message to LM Studio server with conversation history.

        Args:
            server_url (str): The base URL of the LM Studio server.
            model_name (str): The name of the model to use.
            message (str): The current user message to send.
            chat_history (tuple[str, str], optional): Previous conversation history as a list of (user, assistant) tuples.
            return_metrics (bool, optional): Whether to return performance metrics. Defaults to False.
            system_prompt (str, optional): An optional system prompt to set the context.
            return_chain_of_thought (bool, optional): Whether to extract and return chain of thought reasoning. Defaults to False.
            max_tokens (int, optional): Maximum tokens to generate in the response. Defaults to 1000.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            top_p (float, optional): Nucleus sampling probability. Defaults to 0.9.
            stop_sequences (list[str] | None, optional): List of stop sequences to end generation. Defaults to None.
            response_format (dict, optional): A dictionary defining the structured output format. Defaults to {}.

        Returns:
            str | dict: The AI response text, or a dictionary with content and metrics if requested
        """
        if response_format is None:
            response_format = {}
        return LLMProvider.chat(
            provider="lmstudio",
            model_name=model_name,
            message=message,
            server_url=server_url,
            chat_history=chat_history,
            return_metrics=return_metrics,
            system_prompt=system_prompt,
            return_chain_of_thought=return_chain_of_thought,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            response_format=response_format,
            timeout=timeout,
        )

    @staticmethod
    @staticmethod
    def chat_with_openai(
        api_key: str,
        model_name: str,
        message: str,
        chat_history: tuple[str, str] = None,
        return_metrics: bool = False,
        system_prompt: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: list[str] | None = None,
        response_format: dict = None,
        timeout: int = 60,
        endpoint: str = "completions",
    ) -> str | dict:
        """Send a chat message to OpenAI API with conversation history.

        Args:
            api_key (str): The API key for authentication.
            model_name (str): The name of the model to use.
            message (str): The current user message to send.
            chat_history (tuple[str, str], optional): Previous conversation history as a list of (user, assistant) tuples.
            return_metrics (bool, optional): Whether to return performance metrics. Defaults to False.
            system_prompt (str, optional): An optional system prompt to set the context.
            max_tokens (int, optional): Maximum tokens to generate in the response. Defaults to 1000.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            top_p (float, optional): Nucleus sampling probability. Defaults to 0.9.
            stop_sequences (list[str] | None, optional): List of stop sequences to end generation. Defaults to None.
            response_format (dict, optional): A dictionary defining the structured output format. Defaults to {}.
            timeout (int, optional): Request timeout in seconds. Defaults to 60.
            endpoint (str, optional): The API endpoint to use ("completions", "create", or "generate"). Defaults to "completions".

        Returns:
            str | dict: The AI response text, or a dictionary with content and metrics if requested
        """
        if response_format is None:
            response_format = {}
        return LLMProvider.chat(
            provider="openai",
            model_name=model_name,
            message=message,
            api_key=api_key,
            chat_history=chat_history,
            return_metrics=return_metrics,
            system_prompt=system_prompt,
            return_chain_of_thought=False,  # OpenAI doesn't support this parameter in the original method
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            response_format=response_format,
            timeout=timeout,
            endpoint=endpoint,
        )

    @staticmethod
    @staticmethod
    def chat_with_ollama(
        server_url: str,
        model_name: str,
        message: str,
        chat_history: tuple[str, str] = None,
        return_metrics: bool = False,
        system_prompt: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: list[str] | None = None,
        response_format: dict = None,
        timeout: int = 60,
        return_chain_of_thought: bool = False,
    ) -> str | dict:
        """Send a chat message to Ollama API with conversation history.

        Args:
            server_url (str): The base URL of the Ollama server.
            model_name (str): The name of the model to use.
            message (str): The current user message to send.
            chat_history (tuple[str, str], optional): Previous conversation history as a list of (user, assistant) tuples.
            return_metrics (bool, optional): Whether to return performance metrics. Defaults to False.
            system_prompt (str, optional): An optional system prompt to set the context.
            max_tokens (int, optional): Maximum tokens to generate in the response. Defaults to 1000.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            top_p (float, optional): Nucleus sampling probability. Defaults to 0.9.
            stop_sequences (list[str] | None, optional): List of stop sequences to end generation. Defaults to None.
            response_format (dict, optional): A dictionary defining the structured output format. Defaults to {}.
            return_chain_of_thought (bool, optional): Whether to extract and return chain of thought reasoning. Defaults to False.

        Returns:
            str | dict: The AI response text, or a dictionary with content and metrics if requested
        """
        if response_format is None:
            response_format = {}
        return LLMProvider.chat(
            provider="ollama",
            model_name=model_name,
            message=message,
            server_url=server_url,
            chat_history=chat_history,
            return_metrics=return_metrics,
            system_prompt=system_prompt,
            return_chain_of_thought=return_chain_of_thought,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            response_format=response_format,
            timeout=timeout,
        )
