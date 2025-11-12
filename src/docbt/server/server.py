"""Streamlit server for docbt application."""

import copy
import json
import os
import re
import sys
from collections import OrderedDict

import openai
import pandas as pd
import requests
import streamlit as st
import yaml
from dotenv import load_dotenv
from loguru import logger

from docbt.ai.llm import (
    BIGQUERY_CONSTRAINTS_PROMPT,
    DEFAULT_CONSTRAINTS_PROMPT,
    DEFAULT_SYSTEM_PROMPT,
    SUGGESTION_PROMPT,
    SUGGESTIONS_RESPONSE_FORMAT,
    SUGGESTIONS_RESPONSE_FORMAT_OLLAMA,
    LLMProvider,
)
from docbt.config.config import DEFAULT_COL_DICT, DEFAULT_MODEL_CONFIG

# Import optional connectors with availability checking
from docbt.providers import BIGQUERY_AVAILABLE, SNOWFLAKE_AVAILABLE

if SNOWFLAKE_AVAILABLE:
    from docbt.providers import ConnSnowflake

if BIGQUERY_AVAILABLE:
    from docbt.providers import ConnBigQuery


# Load environment variables from .env file (if present)
load_dotenv()

# Configure logging based on environment variable
LOG_LEVEL = os.getenv("DOCBT_LOG_LEVEL", "INFO").upper()
logger.remove()  # Remove default handler
logger.add(sys.stderr, level=LOG_LEVEL)
logger.debug(f"Server logging configured with level: {LOG_LEVEL}")


# Configure YAML to preserve order
yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_dict(data.items()))


USE_AI_DEFAULT = os.getenv("DOCBT_USE_AI_DEFAULT", "True").lower() == "true"
MAX_DISPLAY_MESSAGES = int(os.getenv("DOCBT_MAX_DISPLAY_MESSAGES", 30))
CHAT_CONTAINER_HEIGHT = int(os.getenv("DOCBT_CHAT_CONTAINER_HEIGHT", 400))
DEFAULT_PROVIDER = os.getenv("DOCBT_LLM_PROVIDER_DEFAULT", "lmstudio")

# LLM provider options
DISPLAY_LLM_PROVIDER_OPENAI = (
    os.getenv("DOCBT_DISPLAY_LLM_PROVIDER_OPENAI", "True").lower() == "true"
)
DISPLAY_LLM_PROVIDER_OLLAMA = (
    os.getenv("DOCBT_DISPLAY_LLM_PROVIDER_OLLAMA", "True").lower() == "true"
)
DISPLAY_LLM_PROVIDER_LMSTUDIO = (
    os.getenv("DOCBT_DISPLAY_LLM_PROVIDER_LMSTUDIO", "True").lower() == "true"
)
LLM_PROVIDERS = []
for provider in [
    ("lmstudio", DISPLAY_LLM_PROVIDER_LMSTUDIO),
    ("ollama", DISPLAY_LLM_PROVIDER_OLLAMA),
    ("openai", DISPLAY_LLM_PROVIDER_OPENAI),
]:
    if provider[1]:
        LLM_PROVIDERS.append(provider[0])

# Data source options
DATA_SOURCE_DEFAULT = os.getenv("DOCBT_DATA_SOURCE_DEFAULT", "filesystem")
DISPLAY_DATA_SOURCE_FILESYSTEM = (
    os.getenv("DOCBT_DISPLAY_DATA_SOURCE_FILESYSTEM", "True").lower() == "true"
)
# Only show Snowflake/BigQuery options if the dependencies are installed
DISPLAY_DATA_SOURCE_SNOWFLAKE = (
    SNOWFLAKE_AVAILABLE
    and os.getenv("DOCBT_DISPLAY_DATA_SOURCE_SNOWFLAKE", "True").lower() == "true"
)
DISPLAY_DATA_SOURCE_BIGQUERY = (
    BIGQUERY_AVAILABLE and os.getenv("DOCBT_DISPLAY_DATA_SOURCE_BIGQUERY", "True").lower() == "true"
)
DATA_SOURCE_OPTIONS = []
for extra_source in [
    ("filesystem", DISPLAY_DATA_SOURCE_FILESYSTEM),
    ("snowflake", DISPLAY_DATA_SOURCE_SNOWFLAKE),
    ("bigquery", DISPLAY_DATA_SOURCE_BIGQUERY),
]:
    if extra_source[1]:
        DATA_SOURCE_OPTIONS.append(extra_source[0])
DEFAULT_SAMPLE_SIZE = int(os.getenv("DOCBT_DEFAULT_SAMPLE_SIZE", 10))

# LLM model options
FALLBACK_OPENAI_MODELS = [
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-5",
]
MAX_TOKENS = 2048
TEMPERATURE = 0.7
TOP_P = 0.8
EXAMPLE_FILES = """
**CSV Format:**
```
name,age,city
John,25,New York
Jane,30,San Francisco
```

**JSON Format (List of Objects):**
```json
[
    {"name": "John", "age": 25, "city": "New York"},
    {"name": "Jane", "age": 30, "city": "San Francisco"}
]
```

**JSON Format (Single Object):**
```json
{
    "name": "John",
    "age": 25,
    "city": "New York"
}
```
"""
SYSTEM_PROMPT_HEIGHT = 300


class DocbtServer:
    """Streamlit server for docbt application."""

    def _df_to_json(self, df: pd.DataFrame) -> str:
        """Convert a DataFrame to a JSON string with proper handling of complex data types.

        Handles datetime64[ns, UTC], timedelta, period, categorical, and other special pandas types
        to ensure proper JSON serialization without losing data fidelity.

        Args:
            df: DataFrame to convert.

        Returns:
            JSON string representation of the DataFrame.
        """
        logger.debug(f"Converting DataFrame to JSON. Dtypes: {df.dtypes.to_dict()}")

        try:
            # Create a copy to avoid modifying the original DataFrame
            df_copy = df.copy()

            # Handle datetime-like types (including timezone-aware datetime64)
            for col in df_copy.columns:
                dtype = df_copy[col].dtype

                # Handle timezone-aware datetime (e.g., datetime64[ns, UTC])
                if pd.api.types.is_datetime64_any_dtype(dtype):
                    # Convert to ISO format string, preserving timezone info
                    df_copy[col] = df_copy[col].apply(
                        lambda x: x.isoformat() if pd.notna(x) else None
                    )
                    logger.debug(f"Column '{col}' converted from {dtype} to ISO format string")

                # Handle timedelta types
                elif pd.api.types.is_timedelta64_dtype(dtype):
                    # Convert to total seconds for readability
                    df_copy[col] = df_copy[col].apply(
                        lambda x: x.total_seconds() if pd.notna(x) else None
                    )
                    logger.debug(f"Column '{col}' converted from {dtype} to seconds")

                # Handle period types
                elif isinstance(dtype, pd.PeriodDtype):
                    df_copy[col] = df_copy[col].astype(str)
                    logger.debug(f"Column '{col}' converted from {dtype} to string")

                # Handle interval types
                elif isinstance(dtype, pd.IntervalDtype):
                    df_copy[col] = df_copy[col].astype(str)
                    logger.debug(f"Column '{col}' converted from {dtype} to string")

                # Handle categorical types
                elif isinstance(dtype, pd.CategoricalDtype):
                    df_copy[col] = df_copy[col].astype(str)
                    logger.debug(f"Column '{col}' converted from {dtype} to string")

                # Handle complex numbers
                elif pd.api.types.is_complex_dtype(dtype):
                    df_copy[col] = df_copy[col].astype(str)
                    logger.debug(f"Column '{col}' converted from {dtype} to string")

                # Handle object types that might contain non-serializable data
                elif dtype == "object":
                    # Try to identify what's in the object column
                    sample_val = (
                        df_copy[col].dropna().iloc[0] if not df_copy[col].dropna().empty else None
                    )

                    if sample_val is not None:
                        # Handle date objects
                        if isinstance(sample_val, (pd.Timestamp | pd.Timedelta)):
                            df_copy[col] = df_copy[col].astype(str)
                            logger.debug(
                                f"Column '{col}' (object) converted to string (pandas type)"
                            )
                        # Handle bytes
                        elif isinstance(sample_val, bytes):
                            df_copy[col] = df_copy[col].apply(
                                lambda x: (
                                    x.decode("utf-8", errors="replace")
                                    if isinstance(x, bytes)
                                    else x
                                )
                            )
                            logger.debug(f"Column '{col}' (object) decoded from bytes")
                        # Generic fallback for other object types
                        else:
                            try:
                                # Test if the column can be converted to JSON
                                json.dumps(df_copy[col].iloc[0])
                            except (TypeError, ValueError):
                                df_copy[col] = df_copy[col].astype(str)
                                logger.debug(
                                    f"Column '{col}' (object) converted to string (not JSON serializable)"
                                )

            # Convert to JSON with proper handling of NaN/None values
            json_str = df_copy.to_json(
                orient="records", indent=2, date_format="iso", default_handler=str
            )
            logger.debug(f"Successfully converted DataFrame to JSON ({len(json_str)} characters)")
            return json_str

        except Exception as e:
            logger.error(f"Failed to convert DataFrame to JSON: {e}", exc_info=True)
            # Return empty array as fallback
            return "[]"

    def setup_llm_toggle(self) -> bool:
        """Setup the LLM service toggle and return its state."""
        return st.toggle(
            "Use AI",
            USE_AI_DEFAULT,
            help=(
                "The AI/LLM will generate descriptions of the table and its columns. "
                + "For each table column, it can suggest generic DBT tests and constraints."
            ),
        )

    def setup_system_prompt(self, developer_mode: bool = True):
        """Setup system prompt configuration - editable only in developer mode."""
        # Default system prompt with comprehensive DBT testing guidance
        default_prompt = DEFAULT_SYSTEM_PROMPT

        # Get existing system prompt from session state or use default
        if developer_mode:
            current_prompt = st.session_state.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

            with st.expander("📝 System Prompt Configuration", expanded=False):
                system_prompt = st.text_area(
                    "System Prompt",
                    value=current_prompt,
                    height=SYSTEM_PROMPT_HEIGHT,
                    help="Customize the system prompt that will be sent to the LLM to set its behavior and context",
                )

                # Store in session state
                st.session_state.system_prompt = system_prompt

                # Show token count
                token_count = LLMProvider.count_tokens(system_prompt)
                st.caption(f"🔢 Tokens: {token_count}")

                if st.button("🔄 Reset to Default"):
                    # Reset system prompt
                    st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT

                    # Reset LLM provider to default
                    st.session_state.llm_provider = DEFAULT_PROVIDER

                    # Reset fetched OpenAI models
                    if "openai_fetched_models" in st.session_state:
                        del st.session_state.openai_fetched_models

                    # Reset other provider-specific settings
                    if "show_chain_of_thought" in st.session_state:
                        st.session_state.show_chain_of_thought = False

                    st.success("✅ Reset to default settings!")
                    st.rerun()

                if st.button("💾 Save Prompt"):
                    st.success("✅ System prompt saved!")
        else:
            # For non-developers, always use default prompt but store it in session state
            default_prompt = DEFAULT_SYSTEM_PROMPT

            if "system_prompt" not in st.session_state:
                st.session_state.system_prompt = default_prompt

            system_prompt = default_prompt

        return system_prompt

    def setup_developer_mode(self) -> bool:
        """Setup developer mode toggle and advanced settings.

        Returns:
            bool: True if developer mode is enabled, False otherwise.
        """
        defaulth_developer_mode = os.getenv("DEVELOPER_MODE_ENABLED", "True").lower() == "true"
        st.session_state.developer_mode = st.toggle(
            "Developer Mode",
            defaulth_developer_mode,
            help="Enable developer mode to show token metrics, response times, and other debugging information",
        )

        # Show advanced settings if developer mode is enabled
        if st.session_state.developer_mode:
            with st.expander("🔧 Advanced Developer Settings", expanded=False):
                # Chain of thought toggle (available to all users)
                if st.session_state.get("llm_provider") == "openai":
                    st.warning(
                        "🧠 Chain of Thought is not supported with OpenAI models at this time."
                    )
                    show_chain_of_thought = False
                else:
                    show_chain_of_thought = (
                        os.getenv("SHOW_CHAIN_OF_THOUGHT", "True").lower() == "true"
                    )
                    show_chain_of_thought = st.toggle(
                        "🧠 Show Chain of Thought",
                        value=st.session_state.get("show_chain_of_thought", True),
                        help="Display the model's reasoning process when available - for models that support Chain of Thought",
                    )
                # Store in session state
                st.session_state.show_chain_of_thought = show_chain_of_thought

                # Timeout selection
                st.session_state.api_timeout = st.slider(
                    "API Timeout (seconds)",
                    min_value=10,
                    max_value=300,
                    value=60,
                    step=5,
                    help="Maximum time to wait for API responses. Higher values allow for more complex requests but may cause longer waits.",
                    key="api_timeout_slider",
                )

                st.caption(f"⏱️ Current timeout: {st.session_state.api_timeout} seconds")

                if (
                    st.session_state.get("llm_provider") == "openai"
                    and st.session_state.llm_config.get("model_name")
                    and "gpt-5" in st.session_state.llm_config.get("model_name", "")
                ):
                    st.warning("GPT-5 models do not support temperature/top_p/stop parameters.")
                    st.session_state.llm_config.pop("temperature", None)
                    st.session_state.llm_config.pop("top_p", None)
                    st.session_state.llm_config.pop("stop", None)
                    if "max_tokens" not in st.session_state:
                        st.session_state.max_tokens = MAX_TOKENS
                    # Max tokens
                    max_tokens = st.slider(
                        "Max Tokens",
                        min_value=100,
                        max_value=8192,
                        value=st.session_state.max_tokens,
                        step=100,
                        help="Maximum number of tokens to generate in the response",
                        key="max_tokens",
                    )

                else:
                    st.divider()
                    st.subheader("🎛️ Generation Parameters")

                    # Initialize session state for generation parameters
                    if "max_tokens" not in st.session_state:
                        st.session_state.max_tokens = MAX_TOKENS
                    if "temperature" not in st.session_state:
                        st.session_state.temperature = TEMPERATURE
                    if "top_p" not in st.session_state:
                        st.session_state.top_p = TOP_P
                    if "stop_sequences" not in st.session_state:
                        st.session_state.stop_sequences = ""

                    col1, col2 = st.columns(2)

                    with col1:
                        # Max tokens
                        max_tokens = st.slider(
                            "Max Tokens",
                            min_value=100,
                            max_value=8192,
                            value=st.session_state.max_tokens,
                            step=100,
                            help="Maximum number of tokens to generate in the response",
                            key="max_tokens",
                        )

                        # Temperature
                        temperature = st.slider(
                            "Temperature",
                            min_value=0.0,
                            max_value=2.0,
                            value=st.session_state.temperature,
                            step=0.1,
                            help="Controls randomness. Lower values make output more focused and deterministic",
                            key="temperature",
                        )

                    with col2:
                        # Top P
                        top_p = st.slider(
                            "Top P",
                            min_value=0.0,
                            max_value=1.0,
                            value=st.session_state.top_p,
                            step=0.05,
                            help="Nucleus sampling. Lower values make output more focused",
                            key="top_p",
                        )

                        # Stop sequences
                        stop_sequences = st.text_input(
                            "Stop Sequences",
                            value=st.session_state.stop_sequences,
                            placeholder="Enter comma-separated stop sequences",
                            help="Sequences where the model should stop generating (comma-separated)",
                            key="stop_sequences",
                        )

                    # Show current parameter values
                    st.caption(
                        f"🎯 Max Tokens: {max_tokens} | 🌡️ Temperature: {temperature} | 🎪 Top P: {top_p}"
                    )
                    if stop_sequences:
                        stop_list = [s.strip() for s in stop_sequences.split(",") if s.strip()]
                        st.caption(f"🛑 Stop Sequences: {stop_list}")
                    else:
                        st.caption("🛑 Stop Sequences: None")

    def setup_llm_provider(self) -> str:
        """Setup LLM provider selection.

        Returns:
            str: Selected LLM provider.
        """
        # Check if we have any providers available
        if not LLM_PROVIDERS:
            st.error(
                "❌ No LLM providers are enabled. "
                "Please set at least one DOCBT_DISPLAY_LLM_PROVIDER_* environment variable to true."
            )
            return None

        # Initialize session state for provider selection
        if "llm_provider" not in st.session_state:
            # Use default provider if it's in the list, otherwise use the first available
            st.session_state.llm_provider = (
                DEFAULT_PROVIDER if DEFAULT_PROVIDER in LLM_PROVIDERS else LLM_PROVIDERS[0]
            )

        # Ensure current provider is in the available list
        if st.session_state.llm_provider not in LLM_PROVIDERS:
            st.session_state.llm_provider = LLM_PROVIDERS[0]

        provider = st.radio(
            "Choose LLM model provider",
            LLM_PROVIDERS,
            index=LLM_PROVIDERS.index(st.session_state.llm_provider),
            help="Choose between closed and open source providers. Use LLM as a service or self-hosted models.",
            key="llm_provider",
            horizontal=True,
        )

        return provider

    def setup_openai_config(self) -> tuple[str, str]:
        """Configure OpenAI API settings.

        Returns:
            tuple[str, str]: (API key, selected model)
        """
        # Display OpenAI provider information
        st.caption("• Cloud-based AI service")
        st.caption("• Requires internet connection")
        st.caption("• Uses GPT models for high-quality responses")
        st.caption("• Charges per API usage")

        # Help section with links
        with st.expander("📚 OpenAI Help & Resources"):
            st.markdown(
                """
            **Useful Links:**
            - [OpenAI Platform](https://platform.openai.com/) - Main dashboard
            - [API Keys](https://platform.openai.com/account/api-keys) - Get your API key
            - [Documentation](https://platform.openai.com/docs) - API documentation
            - [Pricing](https://openai.com/pricing) - Plan pricing information
            - [API Pricing] (https://platform.openai.com/docs/pricing) - Detailed API pricing
            - [Usage Dashboard](https://platform.openai.com/account/usage) - Monitor your usage

            **Getting Started:**
            1. Sign up at platform.openai.com
            2. Add billing information (required for API access)
            3. Generate an API key
            4. Set usage limits to control costs

            **Model Information:**
            - **gpt-4o**: Latest and most capable model
            - **gpt-4o-mini**: Faster and more cost-effective version
            - **gpt-4-turbo**: Previous generation flagship model
            - **gpt-4**: Original GPT-4 model
            - **gpt-3.5-turbo**: Fast and cost-effective for most tasks
            """
            )

        default_api_key = os.getenv("DOCBT_OPENAI_API_KEY", "")
        openai_api_key = st.text_input(
            "OpenAI API Key",
            value=default_api_key,
            type="password",
            placeholder="sk-...",
            help="Your OpenAI API key. You can get one from https://platform.openai.com/account/api-keys",
        )

        if default_api_key:
            st.info(
                "Using API key from environment variable. The actual key is hidden for security."
            )

        # Initialize session state for fetched models
        if "openai_fetched_models" not in st.session_state:
            st.session_state.openai_fetched_models = None

        # Model selection section
        col1, col2 = st.columns([3, 1])

        with col1:
            # Use fetched models if available, otherwise use default models
            available_models = (
                st.session_state.openai_fetched_models
                if st.session_state.openai_fetched_models
                else FALLBACK_OPENAI_MODELS
            )

            selected_model = st.selectbox(
                "Choose OpenAI Model",
                available_models,
                index=0,  # Default to first model (gpt-4o-mini)
                help="Select the OpenAI model to use. Different models have different capabilities and pricing.",
            )

        with col2:
            # Button to fetch models from API
            if st.button("🔄 Fetch Models", help="Fetch available models from OpenAI API"):
                if openai_api_key:
                    with st.spinner("Fetching available models..."):
                        fetched_models = self.fetch_openai_models(openai_api_key)
                        if fetched_models:
                            st.session_state.openai_fetched_models = fetched_models
                            st.success(f"✅ Fetched {len(fetched_models)} models from OpenAI API")
                            st.rerun()
                        else:
                            st.error(
                                "❌ Could not fetch models from OpenAI API. Please check your API key."
                            )
                else:
                    st.warning("⚠️ Please enter your OpenAI API key first.")

        # Show current model source
        if st.session_state.openai_fetched_models:
            st.info(
                f"📡 Using models fetched from OpenAI API ({len(st.session_state.openai_fetched_models)} models)"
            )
        else:
            st.info("📋 Using default model list (click 'Fetch Models' to get latest from API)")

        return openai_api_key, selected_model

    def fetch_openai_models(self, api_key: str) -> list[str]:
        """Fetch available models from OpenAI API.

        Args:
            api_key (str): OpenAI API key.

        Returns:
            list[str]: List of available model IDs.
        """
        try:
            client = openai.OpenAI(api_key=api_key)
            models_response = client.models.list()

            # Filter for chat completion models and sort by name
            chat_models = []
            for model in models_response.data:
                model_id = model.id
                # Filter for GPT models that support chat completions
                if any(
                    keyword in model_id.lower()
                    for keyword in ["gpt-5", "gpt-4", "gpt-3.5", "gpt-oss"]
                ):
                    chat_models.append(model_id)

            # Sort models with GPT-4 models first, then by name
            chat_models.sort(key=lambda x: (not x.startswith("gpt-4"), x))
            return chat_models

        except Exception as e:
            logger.error(f"Failed to fetch models from OpenAI: {e}")

            # Return fallback models if API call fails
            return FALLBACK_OPENAI_MODELS

    def fetch_ollama_models(self, server_url: str) -> list[str]:
        """Fetch available models from Ollama server."""
        try:
            ollama_models_endpoint = f"{server_url}/api/tags"
            response = requests.get(ollama_models_endpoint, timeout=10)
            response.raise_for_status()
            return response.json()["models"]
        except requests.RequestException as e:
            logger.error(f"Failed to fetch models from Ollama: {e}")
            return []
        except KeyError:
            logger.error("Unexpected response format from Ollama server")
            return []

    def fetch_lmstudio_models(self, server_url: str) -> list[str]:
        """Fetch available models from LM Studio server."""
        try:
            lmstudio_models_endpoint = f"{server_url}/api/v0/models"
            response = requests.get(lmstudio_models_endpoint, timeout=10)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch models from LM Studio: {e}")
            return []
        except KeyError:
            logger.error("Unexpected response format from LM Studio server")
            return []

    def setup_ollama_config(self) -> tuple[str, str, dict]:
        """Configure Ollama server settings."""
        # Display basic provider info even when server is unavailable
        st.caption("• Local AI server running on your machine")
        st.caption("• No internet required after model download")
        st.caption("• Free to use with downloaded models")
        st.caption("• Privacy-focused - data stays local")

        # Get host and port from environment variables with defaults
        default_host = os.getenv("DOCBT_OLLAMA_HOST", "localhost")
        default_port = os.getenv("DOCBT_OLLAMA_PORT", "11434")
        default_server_url = f"http://{default_host}:{default_port}"

        # Always show help section regardless of server availability
        with st.expander("📚 Ollama Help & Resources"):
            st.markdown(
                """
            **Useful Links:**
            - [Ollama Website](https://ollama.ai/) - Official website
            - [Download Ollama](https://ollama.ai/download) - Install for your OS
            - [Model Library](https://ollama.ai/library) - Browse available models
            - [GitHub](https://github.com/ollama/ollama) - Source code and issues
            - [Documentation](https://github.com/ollama/ollama/blob/main/README.md) - Setup guides

            **Getting Started:**
            1. Download and install Ollama for your operating system
            2. Run `ollama serve` to start the server
            3. Pull a model: `ollama pull llama2` or `ollama pull mistral`
            4. The server runs on http://localhost:11434 by default

            **Popular Models to Try:**
            - `llama2` - Meta's Llama 2 model
            - `mistral` - Mistral 7B model
            - `codellama` - Code-focused model
            - `dolphin-mixtral` - Fine-tuned Mixtral model
            """
            )

        server = st.text_input(
            "Ollama server URL",
            value=default_server_url,
            placeholder="http://localhost:11434",
            help=f"URL of your local LLM server (default: {default_server_url}). You can set OLLAMA_HOST and OLLAMA_PORT environment variables to customize defaults.",
        )

        models = self.fetch_ollama_models(server)

        if not models:
            st.error(
                f"Could not fetch models from Ollama server at {server}/api/tags. "
                "Please ensure the server is running and accessible."
            )

            return server, None, None

        llm_model_name = st.selectbox(
            "Choose LLM model",
            [m.get("name") for m in models],
            index=0,
            help="LLM model to use for generating descriptions and suggestions",
        )

        # Find the selected model details
        llm_model = None
        for m in models:
            if m.get("name") == llm_model_name:
                llm_model = m.get("model")
                break

        return server, llm_model_name, llm_model

    def setup_lmstudio_config(self) -> tuple[str, str, dict]:
        """Configure LmStudio server settings."""
        st.caption("• Local AI server with easy model management")
        st.caption("• No internet required after model download")
        st.caption("• Free to use with downloaded models")
        st.caption("• User-friendly interface for model loading")

        # Get host and port from environment variables with defaults
        default_host = os.getenv("DOCBT_LMSTUDIO_HOST", "localhost")
        default_port = os.getenv("DOCBT_LMSTUDIO_PORT", "1234")
        default_server_url = f"http://{default_host}:{default_port}"

        # Always show help section regardless of server availability
        with st.expander("📚 LM Studio Help & Resources"):
            st.markdown(
                """
            **Useful Links:**
            - [LM Studio Website](https://lmstudio.ai/) - Official website
            - [Download LM Studio](https://lmstudio.ai/) - Get the latest version
            - [Documentation](https://lmstudio.ai/docs) - User guides and tutorials
            - [Discord Community](https://discord.gg/aPQfnNkxGC) - Community support
            - [Model Hub](https://huggingface.co/models) - Hugging Face model repository

            **Getting Started:**
            1. Download and install LM Studio from lmstudio.ai
            2. Browse and download models from the built-in model browser
            3. Load a model in the Chat tab
            4. Enable "Local Server" in the settings
            5. The server runs on http://localhost:1234 by default

            **Tips:**
            - Use the model search to find specific models
            - Check system requirements before downloading large models
            - Enable GPU acceleration for better performance
            - Monitor system resources during model inference
            """
            )

        server = st.text_input(
            "LM Studio server URL",
            value=default_server_url,
            placeholder="http://localhost:1234",
            help=f"URL of your LM Studio server (default: {default_server_url}). You can set LMSTUDIO_HOST and LMSTUDIO_PORT environment variables to customize defaults.",
        )

        models = self.fetch_lmstudio_models(server)

        if not models:
            st.error(
                f"Could not fetch models from LM Studio server at {server}/api/v0/models. "
                "Please ensure LM Studio is running with a model loaded and the local server is enabled."
            )
            return server, None, None

        # LM Studio returns models in a different format than Ollama
        model_names = [m.get("id", "Unknown") for m in models]

        if not model_names:
            st.error("No models found. Please load a model in LM Studio first.")

            return server, None, None

        llm_model_name = st.selectbox(
            "Choose LM Studio model",
            model_names,
            index=0,
            help="LM Studio model to use for generating descriptions and suggestions",
        )

        # Find the selected model details
        llm_model = None
        for m in models:
            if m.get("id") == llm_model_name:
                llm_model = m
                break

        return server, llm_model_name, llm_model

    def render_llm_setup(self) -> dict:
        """Render the LLM setup section and return configuration."""
        st.session_state.llm_enabled = self.setup_llm_toggle()

        if not st.session_state.llm_enabled:
            return {"enabled": False}

        # Add developer mode toggle
        self.setup_developer_mode()

        # Add system prompt configuration (developer mode controls editing)
        system_prompt = self.setup_system_prompt(st.session_state.developer_mode)

        llm_provider = self.setup_llm_provider()

        if llm_provider == "openai":
            api_key, model_name = self.setup_openai_config()
            return {
                "enabled": True,
                "provider": "openai",
                "api_key": api_key,
                "model_name": model_name,
                "developer_mode": st.session_state.developer_mode,
                "system_prompt": system_prompt,
            }

        elif llm_provider == "ollama":
            server, model_name, model = self.setup_ollama_config()
            return {
                "enabled": True,
                "provider": "ollama",
                "server": server,
                "model_name": model_name,
                "model": model,
                "developer_mode": st.session_state.developer_mode,
                "system_prompt": system_prompt,
            }

        elif llm_provider == "lmstudio":
            server, model_name, model = self.setup_lmstudio_config()
            return {
                "enabled": True,
                "provider": "lmstudio",
                "server": server,
                "model_name": model_name,
                "model": model,
                "developer_mode": st.session_state.developer_mode,
                "system_prompt": system_prompt,
            }

        return {"enabled": False}

    def send_chat_message(
        self, llm_config: dict, message: str, chat_history: list = None
    ) -> str | dict:
        """Send a chat message to the configured LLM provider with conversation history.

        Args:
            llm_config (dict): LLM configuration dictionary.
            message (str): User's chat message.
            chat_history (list, optional): List of (user_message, assistant_message) tuples
                representing the conversation history. Defaults to None.

        Returns:
            str | dict: LLM response content or a dictionary with content and metrics if in developer
        """
        if not llm_config.get("enabled"):
            return "❌ LLM service is not enabled. Please configure it in the Setup tab."

        provider = llm_config.get("provider")
        system_prompt = llm_config.get("system_prompt")

        # If there's uploaded data, enhance the system prompt (not the message)
        if "node" in st.session_state:
            filename = st.session_state.get("uploaded_filename", "uploaded_data")

            # Get a sample of up to 10 records
            sample_df = st.session_state.node

            # Convert sample to JSON
            try:
                sample_json = self._df_to_json(sample_df)

                # Convert column data types to JSON format
                column_types = {
                    col: str(st.session_state.node[col].dtype)
                    for col in st.session_state.node.columns
                }
                column_types_json = json.dumps(column_types, indent=2)

                # Add data context to the system prompt
                data_context = f"""
                ## Data Context
                You have access to a dataset with the following characteristics:
                - **File**: {filename}
                - **Total Records**: {len(st.session_state.node):,}
                - **Columns**: {len(st.session_state.node.columns)}
                - **Column Names**: {", ".join(st.session_state.node.columns.tolist())}

                **Sample Data:**
                ```json
                {sample_json}
                ```

                **Column Data Types:**
                ```json
                {column_types_json}
                ``

                When the user asks questions, they may be referring to this uploaded dataset.
                Use this context to provide relevant and informed responses.
                """

                # Append data context to system prompt
                system_prompt = (system_prompt or "") + data_context

            except Exception as e:
                logger.error(f"Failed to convert DataFrame sample to JSON: {e}")

                # If JSON conversion fails, just add basic info
                try:
                    # Try to create JSON format for column types even in fallback
                    column_types = {
                        col: str(st.session_state.node[col].dtype)
                        for col in st.session_state.node.columns
                    }
                    column_types_json = json.dumps(column_types, indent=2)

                    data_context = f"""
                    ## Data Context
                    You have access to a dataset: {filename} with {len(st.session_state.node):,} records and {len(st.session_state.node.columns)} columns.
                    Columns: {", ".join(st.session_state.node.columns.tolist())}

                    **Column Data Types:**
                    ```json
                    {column_types_json}
                    ```

                    When the user asks questions, they may be referring to this uploaded dataset.
                    """

                # Final fallback if even basic JSON conversion fails
                except Exception as e:
                    logger.error(f"Failed to create data context: {e}")

                    data_context = f"""
                    ## Data Context
                    You have access to a dataset: {filename} with {len(st.session_state.node):,} records and {len(st.session_state.node.columns)} columns.
                    Columns: {", ".join(st.session_state.node.columns.tolist())}

                    When the user asks questions, they may be referring to this uploaded dataset."""

                    data_context = f"""
                    ## Data Context
                    You have access to a dataset: {filename} with {len(st.session_state.node):,} records and {len(st.session_state.node.columns)} columns.
                    Columns: {", ".join(st.session_state.node.columns.tolist())}

                    When the user asks questions, they may be referring to this uploaded dataset.
                    """

                # Append data context to system prompt
                system_prompt = (system_prompt or "") + data_context

        model_name = llm_config.get("model_name")

        if provider == "openai":
            api_key = llm_config.get("api_key")
            if not api_key:
                return "❌ OpenAI API key is required."
            return LLMProvider.chat_with_openai(
                api_key,
                model_name,
                message,
                chat_history,
                return_metrics=st.session_state.get("developer_mode"),
                system_prompt=system_prompt,
                max_tokens=st.session_state.get("max_tokens", 1000),
                temperature=st.session_state.get("temperature", 0.7),
                top_p=st.session_state.get("top_p", 1.0),
                stop_sequences=st.session_state.get("stop_sequences", None),
            )

        elif provider == "ollama":
            server = llm_config.get("server")
            if not server or not model_name:
                return "❌ Ollama server URL and model name are required."
            return LLMProvider.chat_with_ollama(
                server,
                model_name,
                message,
                chat_history,
                return_metrics=st.session_state.get("developer_mode"),
                system_prompt=system_prompt,
                return_chain_of_thought=True,
                max_tokens=st.session_state.get("max_tokens", 1000),
                temperature=st.session_state.get("temperature", 0.7),
                top_p=st.session_state.get("top_p", 1.0),
                stop_sequences=st.session_state.get("stop_sequences", None),
            )

        elif provider == "lmstudio":
            server = llm_config.get("server")
            if not server or not model_name:
                return "❌ LM Studio server URL and model name are required."
            return LLMProvider.chat_with_lmstudio(
                server,
                model_name,
                message,
                chat_history,
                return_metrics=st.session_state.get("developer_mode"),
                system_prompt=system_prompt,
                return_chain_of_thought=True,
                max_tokens=st.session_state.get("max_tokens", 1000),
                temperature=st.session_state.get("temperature", 0.7),
                top_p=st.session_state.get("top_p", 1.0),
                stop_sequences=st.session_state.get("stop_sequences", None),
            )

        return "❌ Unknown LLM provider."

    def render_ai_tab(self) -> dict:
        """Render the entire AI tab content."""
        st.subheader("📝 LLM Configuration")
        return self.render_llm_setup()

    # **Column Details:**
    # ```json
    # {generate_column_info(df).to_json(orient="records", indent=2)}
    # ```

    # **Statistical Summary of Number Columns:**
    # ```json
    # {generate_number_stats(df)}
    # ```

    # **Summary of Text Columns:**
    # ```json
    # {generate_text_stats(df)}
    # ```

    def _create_enhanced_system_prompt(
        self, df: pd.DataFrame, system_prompt: str, sample_size: int = 10
    ) -> str:
        """Convert a sample of the DataFrame to JSON format for system prompt and return the enhanced prompt."""
        sample_df = df.head(sample_size)

        try:
            sample_json = self._df_to_json(sample_df)
            # Add data context to the system prompt
            data_context = f"""
## Data Context
You have access to the following dataset sample (assume the full dataset has many more records and data values are more diverse):
```json
{sample_json}
```

When the user asks questions, they may be referring to this uploaded dataset.
Use this context to provide relevant and informed responses."""

            base_prompt = system_prompt
            if st.session_state["data_source"] in ["filesystem", "snowflake"]:
                base_prompt = system_prompt + DEFAULT_CONSTRAINTS_PROMPT
            elif st.session_state["data_source"] == "bigquery":
                base_prompt = system_prompt + BIGQUERY_CONSTRAINTS_PROMPT
            else:
                base_prompt = system_prompt + DEFAULT_CONSTRAINTS_PROMPT

            enhanced_system_prompt = base_prompt + data_context

            if st.session_state.get("data_source") in ["snowflake", "bigquery"]:
                enhanced_system_prompt += (
                    f"\nAssume the dataset is stored in {st.session_state.get('data_source')}."
                )

            return enhanced_system_prompt

        except Exception as e:
            st.error(f"Failed to convert prompt enrichment data to JSON: {e}")

    def _caption_chat_metrics(self, metrics: dict) -> None:
        st.caption(
            f"⏱️ {metrics['response_time']}s | "
            f"📝 Prompt: {metrics['prompt_tokens']} | "
            f"💬 Completion: {metrics['completion_tokens']} | "
            f"📊 Total: {metrics['total_tokens']} | "
            f"⚡ {metrics['tokens_per_second']} tok/s | "
            f"🤖 {metrics['model']}"
        )

    def render_chat_tab(self, sample_size: int = 10) -> None:
        """Render the chat interface tab."""
        st.subheader("💬 Chat with your LLM")

        # Check if LLM is configured
        llm_config = st.session_state.get("llm_config", {"enabled": False})

        if not llm_config.get("enabled"):
            st.warning("⚠️ Please configure an LLM provider in the Setup tab first.")
            return

        # Show data context if available
        if "node" in st.session_state:
            st.info("💡 Your questions will automatically include sample data for context.")
        else:
            st.info("💡 Upload data in the **Data** tab to get AI insights about your dataset.")

        # Show system prompt settings
        system_prompt = llm_config.get("system_prompt")
        developer_mode = llm_config.get("developer_mode", False)

        # Create the enhanced system prompt (same logic as in send_chat_message)
        enhanced_system_prompt = system_prompt
        if "node" in st.session_state:
            sample_size = min(sample_size, len(st.session_state.node))
            enhanced_system_prompt = self._create_enhanced_system_prompt(
                st.session_state.node, system_prompt, sample_size
            )

        if developer_mode:
            if enhanced_system_prompt:
                with st.expander("🔧 Active System Prompt", expanded=False):
                    st.markdown(enhanced_system_prompt)
                    token_count = LLMProvider.count_tokens(enhanced_system_prompt)
                    st.caption(f"📊 Tokens: {token_count}")

                    # Show if data context is included
                    if "node" in st.session_state:
                        st.caption("✅ Includes uploaded data context")
                    else:
                        st.caption("ℹ️ No data context (no uploaded file)")
            else:
                st.info("💡 No custom system prompt configured. Using default behavior.")

        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []  # For LLM context (no metrics)
        if "chat_display" not in st.session_state:
            st.session_state.chat_display = []  # For UI display (with metrics if enabled)

        # Chat interface

        # Display chat history in a scrollable container
        # Only show recent messages to keep UI responsive
        max_display_messages = MAX_DISPLAY_MESSAGES
        recent_display = (
            st.session_state.chat_display[-max_display_messages:]
            if len(st.session_state.chat_display) > max_display_messages
            else st.session_state.chat_display
        )

        # Create a container with limited height for chat messages
        chat_container = st.container(
            height=CHAT_CONTAINER_HEIGHT,
            border=True,
        )
        with chat_container:
            if recent_display:
                for _, (user_msg, bot_response_data) in enumerate(recent_display):
                    with st.chat_message("user"):
                        st.write(user_msg)
                    with st.chat_message("assistant"):
                        # Handle both old string format and new dict format
                        if isinstance(bot_response_data, dict):
                            # Display reasoning if available
                            if bot_response_data.get("reasoning") and st.session_state.get(
                                "show_chain_of_thought", False
                            ):
                                with st.expander("🧠 Chain of Thought", expanded=False):
                                    st.markdown(bot_response_data["reasoning"])

                            # Display main response
                            st.write(bot_response_data.get("content", "No response"))

                            # Display metrics if available
                            if bot_response_data.get("metrics") and not bot_response_data.get(
                                "error"
                            ):
                                metrics = bot_response_data["metrics"]
                                self._caption_chat_metrics(metrics)
                        else:
                            # Legacy string format
                            st.write(bot_response_data)
            else:
                st.info("💬 Start a conversation! Type your message below.")

        # Show message count if history is truncated
        if len(st.session_state.chat_display) > max_display_messages:
            st.caption(
                f"📝 Showing last {max_display_messages} messages of {len(st.session_state.chat_display)} total messages"
            )

        # Chat input
        user_input = st.chat_input("Type your message here...")

        if user_input:
            # Send message to LLM with clean history (no metrics/reasoning)
            with st.spinner("🤔 Thinking..."):
                result = self.send_chat_message(
                    llm_config, user_input, st.session_state.chat_history
                )

                # Handle different response formats
                if isinstance(result, dict):
                    # New dict format with potential metrics and reasoning
                    response_content = result.get("content", "No response")

                    # Store clean response for LLM context (no metrics/reasoning)
                    st.session_state.chat_history.append((user_input, response_content))

                    # Store full response data for display
                    st.session_state.chat_display.append((user_input, result))

                elif isinstance(result, tuple):
                    # Legacy tuple format (response, metrics)
                    response, metrics = result
                    response_data = {
                        "content": response,
                        "metrics": metrics if not metrics.get("error") else None,
                        "error": metrics.get("error", False),
                    }

                    # Store clean response for LLM context
                    st.session_state.chat_history.append((user_input, response))

                    # Store response data for display
                    st.session_state.chat_display.append((user_input, response_data))

                else:
                    # Simple string response
                    st.session_state.chat_history.append((user_input, result))
                    st.session_state.chat_display.append((user_input, {"content": result}))

            # Rerun to update the display
            st.rerun()

        # Chat controls
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.chat_display = []
            st.rerun()

        if st.button("💾 Download Chat History"):
            if st.session_state.chat_history:
                chat_text = ""
                for user_msg, bot_msg in st.session_state.chat_history:
                    chat_text += f"User: {user_msg}\n"
                    chat_text += f"Assistant: {bot_msg}\n\n"

                st.download_button(
                    label="Download as TXT",
                    data=chat_text,
                    file_name="chat_history.txt",
                    mime="text/plain",
                )

    def _dataframe_stats(self, df: pd.DataFrame) -> None:
        """Compute and display basic statistics for the DataFrame."""
        if df is not None and not df.empty:
            st.markdown(f"- 📊 **Rows:** {len(df)}")
            st.markdown(f"- 📈 **Columns:** {len(df.columns)}")
            st.markdown(f"- 💾 **Memory Usage:** {df.memory_usage(deep=True).sum():,.0f} bytes")
            st.markdown(f"- 🔢 **Data Types:** {len(df.dtypes.unique())}")

    def _file_stats(self, file) -> None:
        """Display basic file statistics."""
        if file:
            st.markdown(f"- 📄 **File Name:** {file.name}")
            st.markdown(f"- 📁 **File Type:** {file.type}")
            st.markdown(f"- 💾 **File Size:** {file.size:,} bytes")

    def _clear_uploaded_data(self) -> None:
        """Clear uploaded data from session state."""
        logger.debug("🗑️ Clearing uploaded data from session state")
        if "node" in st.session_state:
            del st.session_state.node
        if "uploaded_file" in st.session_state:
            del st.session_state.uploaded_file
        if "configuration" in st.session_state:
            del st.session_state.configuration
        if "yaml_dump" in st.session_state:
            del st.session_state.yaml_dump
        if "ai_suggestion" in st.session_state:
            del st.session_state.ai_suggestion
        logger.info("✅ Data cleared!")
        st.rerun()

    def _load_data_from_upload(self, uploaded_file) -> None:
        if uploaded_file.name.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file)
                logger.debug("✅ CSV file loaded successfully!")
            except Exception as e:
                st.error(f"❌ Error converting CSV to DataFrame: {str(e)}")
                return

        elif uploaded_file.name.endswith(".json"):
            try:
                df = pd.read_json(uploaded_file)
                logger.debug("✅ JSON file loaded successfully!")

            except Exception as e:
                st.error(f"❌ Error converting JSON to DataFrame: {str(e)}")
                st.warning(
                    "💡 Try using a JSON file with a list of objects or a flat dictionary structure"
                )
                return
        else:
            st.error("❌ Unsupported file type. Please upload a CSV or JSON file.")
            return

        return df

    def _preview_dataframe(self, df: pd.DataFrame) -> None:
        """Display data preview options for the DataFrame."""
        if df is None or df.empty:
            st.warning("❌ No data available for preview.")
            return

        st.subheader("📋 Data Preview")
        st.dataframe(df)

    def get_sample_size(self) -> int:
        """Get sample size for data fetching from user input."""
        return st.number_input(
            "Sample Size",
            min_value=1,
            max_value=10000,
            value=DEFAULT_SAMPLE_SIZE,
            step=10,
            help="Number of rows to fetch as a sample from the selected table (max 10k, recommended 10).",
        )

    def get_sample(self) -> bool:
        return st.button(
            "📥 Fetch Data",
            help="Fetch sample data from the selected table.",
        )

    @staticmethod
    @st.cache_data
    def cache_snowflake_dbs(_conn):
        dbs = _conn.list_databases()
        dbs = [db for db in dbs if db not in ["SNOWFLAKE"]]
        return dbs

    @staticmethod
    @st.cache_data
    def cache_snowflake_tables(_conn, _db):
        logger.info(f"Fetching tables for schemas in {_db}")
        schemas = _conn.list_schemas(_db)
        tables = []
        if schemas:
            for schema in schemas:
                if schema not in ["INFORMATION_SCHEMA"]:
                    tables.extend([schema + "." + t for t in _conn.list_tables(_db, schema)])

        return tables

    @staticmethod
    @st.cache_data
    def cache_bigquery_datasets(_conn):
        datasets = _conn.list_datasets()
        return datasets

    @staticmethod
    @st.cache_data
    def cache_bigquery_all_tables(_conn, _datasets):
        tables = []
        for dataset in _datasets:
            dataset_tables = _conn.list_tables(dataset)
            tables.extend([f"{dataset}.{t}" for t in dataset_tables])
        return tables

    @staticmethod
    @st.cache_resource
    def cache_bq_conn():
        if not BIGQUERY_AVAILABLE:
            logger.error("❌ BigQuery dependencies not installed")
            st.error(
                "❌ BigQuery support is not available. Install it with: pip install docbt[bigquery]"
            )
            return None

        try:
            conn = ConnBigQuery()
            return conn
        except Exception as e:
            logger.error(f"❌ BigQuery connection error: {e}")
            st.error(f"❌ BigQuery connection error: {e}")
            st.warning(
                "💡 Please ensure the BigQuery connection is configured correctly and re-run the app."
            )
            return

    def render_bigquery_connection(self) -> None:
        """Render BigQuery connection and data fetching UI.

        Requires ConnBigQuery class from src.docbt.connections.bigquery
        1. Connect to BigQuery using ConnBigQuery.
        2. List available datasets and let user select one.
        3. List tables in the selected dataset.
        4. Let user select a table and sample size.
        5. Fetch sample data and store in session state.
        6. Fetch table schema and metadata.
        7. Store fetched data, schema, and metadata in session state.
        8. Rerun the app to reflect changes.
        9. Display data preview.
        """
        conn = DocbtServer.cache_bq_conn()
        bq_datasets = DocbtServer.cache_bigquery_datasets(conn)
        bq_datasets_choices = ["all"] + bq_datasets
        bq_all_tables = DocbtServer.cache_bigquery_all_tables(conn, bq_datasets)

        st.session_state.bq_dataset = st.selectbox(
            "Select Dataset",
            bq_datasets_choices,
            index=0,
            help="Select the BigQuery dataset to use.",
        )
        if st.session_state.bq_dataset != "all":
            bq_tables_choice = [
                t for t in bq_all_tables if t.startswith(st.session_state.bq_dataset + ".")
            ]
        else:
            bq_tables_choice = bq_all_tables

        st.session_state.bq_table = st.selectbox(
            "Select Table",
            bq_tables_choice,
            index=0,
            help="Select the table to load data from.",
        )

        st.session_state.sample_size = self.get_sample_size()
        get_sample = self.get_sample()

        if get_sample:
            if st.session_state.bq_table:
                project = conn.project
                dataset, _ = st.session_state.bq_table.split(".")

                query = f"SELECT * FROM {st.session_state.bq_table} LIMIT {st.session_state.sample_size}"
                logger.debug(f"Executing query: {query}")
                sample_df = conn.query_data(query)

                fully_qualified_table = f"{project}.{st.session_state.bq_table}"

                table_metadata_query = f"""
                SELECT
                    TABLE_CATALOG,
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE,
                    CREATION_TIME,
                FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
                WHERE CONCAT(TABLE_CATALOG, '.', TABLE_SCHEMA, '.', TABLE_NAME) = '{fully_qualified_table}'
                """
                logger.debug(f"Executing table metadata query: {table_metadata_query}")
                st.session_state.bq_table_info_df = conn.query_data(table_metadata_query)
                logger.debug(st.session_state.bq_table_info_df)

                cols_metadata_query = f"""
                WITH
                IS_COLS AS (
                    SELECT
                        COLUMN_NAME,
                        DATA_TYPE,
                        CASE WHEN(IS_NULLABLE) = 'YES' THEN TRUE ELSE FALSE END AS IS_NULLABLE
                    FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
                    WHERE CONCAT(TABLE_CATALOG, '.', TABLE_SCHEMA, '.', TABLE_NAME) = '{fully_qualified_table}'
                ),
                IS_FIELD_PATHS AS (
                    SELECT
                        COLUMN_NAME,
                        DESCRIPTION
                    FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
                    WHERE CONCAT(TABLE_CATALOG, '.', TABLE_SCHEMA, '.', TABLE_NAME) = '{fully_qualified_table}'
                ),
                TABLE_CONSTRAINTS AS (
                    SELECT
                        CONSTRAINT_NAME,
                        CONSTRAINT_TYPE
                    FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS`
                    WHERE CONCAT(TABLE_CATALOG, '.', TABLE_SCHEMA, '.', TABLE_NAME) = '{fully_qualified_table}'
                ),
                CONSTRAINT_COL_USAGE AS (
                    SELECT
                        COLUMN_NAME,
                        CONSTRAINT_NAME
                    FROM `{project}.{dataset}.INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE`
                ),
                CONSTRAINTS AS (
                    SELECT
                        B.COLUMN_NAME,
                        A.CONSTRAINT_TYPE
                    FROM TABLE_CONSTRAINTS A
                    INNER JOIN CONSTRAINT_COL_USAGE B
                    USING (CONSTRAINT_NAME)
                )
                SELECT
                    A.COLUMN_NAME,
                    A.DATA_TYPE,
                    A.IS_NULLABLE,
                    B.DESCRIPTION,
                    C.CONSTRAINT_TYPE
                FROM IS_COLS A
                INNER JOIN IS_FIELD_PATHS B
                    USING (COLUMN_NAME)
                LEFT JOIN CONSTRAINTS C
                    USING (COLUMN_NAME)
                """
                logger.debug(f"Executing columns metadata query: {cols_metadata_query}")
                st.session_state.bq_cols_df = conn.query_data(cols_metadata_query)
                logger.debug(st.session_state.bq_cols_df)

                if sample_df is not None and not sample_df.empty:
                    logger.debug("✅ Sample data fetched successfully!")
                    st.session_state.node = sample_df

                    st.session_state["configuration"]["models"][0] = (
                        self.create_default_configuration()
                    )

                    st.session_state["configuration"]["models"][0]["columns"] = (
                        self.create_default_column_dict()
                    )

                    st.rerun()
                else:
                    warning_txt = "❌  No data returned from the query."
                    logger.warning(warning_txt)
                    st.error(warning_txt)

        if "node" in st.session_state:
            self.render_preview()

    @staticmethod
    @st.cache_resource
    def cache_snowflake_conn():
        if not SNOWFLAKE_AVAILABLE:
            logger.error("❌ Snowflake dependencies not installed")
            st.error(
                "❌ Snowflake support is not available. "
                "Install it with: pip install docbt[snowflake]"
            )
            return None

        try:
            conn = ConnSnowflake()
            return conn
        except Exception as e:
            logger.error(f"❌ Snowflake connection error: {e}")
            st.error(f"❌ Snowflake connection error: {e}")
            st.warning(
                "💡 Please ensure the Snowflake connection is configured correctly and re-run the app."
            )
            return

    @staticmethod
    @st.cache_data
    def cache_snowflake_warehouses(_conn):
        wh_query = """
        SHOW WAREHOUSES ->>
        SELECT
            "name" AS wh_name,
            "type" AS wh_type,
            "size" AS wh_size
        FROM $1
        """
        logger.debug(f"Executing warehouse query: {wh_query}")
        sf_wh_df = _conn.query_data(wh_query)
        sf_wh_df = sf_wh_df[~sf_wh_df["WH_NAME"].str.startswith("SYSTEM$")]
        return sf_wh_df

    def render_snowflake_connection(self) -> None:
        """Render Snowflake connection and data fetching UI.

        Requires ConnSnowflake class from src.docbt.connections.snowflake
        1. Connect to Snowflake using ConnSnowflake.
        2. List available databases and let user select one.
        3. List schemas and tables in the selected database.
        4. Let user select a table and sample size.
        5. Fetch sample data and store in session state.
        6. Fetch table schema and metadata.
        7. Store fetched data, schema, and metadata in session state.
        8. Rerun the app to reflect changes.
        9. Display data preview.
        """
        conn = DocbtServer.cache_snowflake_conn()
        dbs = DocbtServer.cache_snowflake_dbs(conn)
        st.session_state.sf_wh_df = DocbtServer.cache_snowflake_warehouses(conn)

        st.session_state.sf_db = st.selectbox(
            "Select Database",
            dbs,
            index=0,
            help="Select the Snowflake database to use.",
            on_change=lambda: DocbtServer.cache_snowflake_tables.clear(),
        )

        st.session_state.sf_tables = DocbtServer.cache_snowflake_tables(
            conn, st.session_state.sf_db
        )

        st.session_state.sf_table = st.selectbox(
            "Select Table",
            st.session_state.sf_tables,
            index=0,
            help="Select the table to load data from.",
        )

        st.session_state.sample_size = self.get_sample_size()
        get_sample = self.get_sample()

        if get_sample:
            if st.session_state.sf_table:
                fully_qualified_table = f"{st.session_state.sf_db}.{st.session_state.sf_table}"

                select_query = (
                    f"SELECT * FROM {fully_qualified_table} LIMIT {st.session_state.sample_size}"
                )
                logger.debug(f"Executing select query: {select_query}")
                sample_df = conn.query_data(select_query)

                table_metadata_query = f"""
                SELECT
                    TABLE_CATALOG AS DATABASE,
                    TABLE_SCHEMA AS SCHEMA,
                    TABLE_NAME,
                    COMMENT AS DESCRIPTION,
                    TABLE_TYPE,
                    CASE WHEN IS_TRANSIENT = 'NO' THEN FALSE ELSE TRUE END AS IS_TRANSIENT,
                    CASE WHEN IS_DYNAMIC = 'NO' THEN FALSE ELSE TRUE END AS IS_DYNAMIC,
                    CASE WHEN IS_HYBRID = 'NO' THEN FALSE ELSE TRUE END AS IS_HYBRID,
                    CASE WHEN AUTO_CLUSTERING_ON = 'NO' THEN FALSE ELSE TRUE END AS AUTO_CLUSTERING_ON,
                    ROW_COUNT,
                    BYTES,
                    RETENTION_TIME,
                    CREATED,
                    LAST_ALTERED,
                    LAST_DDL,
                    LAST_DDL_BY
                FROM {st.session_state.sf_db}.INFORMATION_SCHEMA.TABLES
                WHERE CONCAT_WS('.', TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME) = '{fully_qualified_table}'
                """
                logger.debug(f"Executing table metadata query: {table_metadata_query}")
                st.session_state.sf_table_info_df = conn.query_data(table_metadata_query)

                cols_metadata_query = f"""
                    DESCRIBE TABLE {fully_qualified_table} ->>
                    SELECT
                        "name" AS COL_NAME,
                        "comment" AS DESCRIPTION,
                        "type" AS DATA_TYPE,
                        CASE WHEN "null?" = 'Y' THEN TRUE ELSE FALSE END AS CONSTR_NULL,
                        CASE WHEN "primary key" = 'Y' THEN TRUE ELSE FALSE END AS CONSTR_PK,
                        CASE WHEN "unique key" = 'Y' THEN TRUE ELSE FALSE END AS CONSTR_UNIQUE,
                    FROM $1
                    WHERE "kind" = 'COLUMN'
                    """
                logger.debug(f"Executing columns metadata query: {cols_metadata_query}")
                st.session_state.sf_cols_df = conn.query_data(cols_metadata_query)
                logger.debug(st.session_state.sf_cols_df)

                if (
                    sample_df is not None
                    and not sample_df.empty
                    and st.session_state.sf_cols_df is not None
                    and not st.session_state.sf_cols_df.empty
                ):
                    logger.debug("✅ Sample data fetched successfully!")
                    st.session_state.node = sample_df
                    st.session_state["configuration"]["models"][0] = (
                        self.create_default_configuration()
                    )

                    st.session_state["configuration"]["models"][0]["columns"] = (
                        self.create_default_column_dict()
                    )

                    st.rerun()
                else:
                    warning_txt = "❌  No data returned from the query."
                    logger.warning(warning_txt)
                    st.error(warning_txt)

        if "node" in st.session_state:
            self.render_preview()

    def render_preview(self):
        if st.button("🗑️ Clear Data", help="Clear all uploaded data"):
            self._clear_uploaded_data()

        df = st.session_state.get("node", None)

        if df is not None and not df.empty:
            if (
                st.session_state.get("data_source") == "snowflake"
                and st.session_state.get("sf_table_info_df") is not None
            ):
                st.subheader("🔍 Metadata ")
                st.dataframe(st.session_state.sf_table_info_df)

            self._preview_dataframe(df)

    def render_file_upload(self) -> None:
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["csv", "json"],
            help="Upload a CSV or JSON file containing your data model",
        )

        with st.expander("📚 Supported File Formats", expanded=False):
            st.markdown(EXAMPLE_FILES)

        # Store DataFrame and filename in the session state
        st.session_state.sample_size = self.get_sample_size()
        get_sample = self.get_sample()

        if get_sample:
            df = self._load_data_from_upload(uploaded_file)

            if df is not None and (not df.empty if isinstance(df, pd.DataFrame) else True):
                st.session_state.uploaded_file = uploaded_file

                st.session_state.node = df.head(st.session_state.sample_size)
                st.session_state["configuration"]["models"][0]["columns"] = (
                    self.create_default_column_dict()
                )
                st.rerun()

        if "node" in st.session_state:
            self.render_preview()

    def render_data_tab(self):
        st.subheader("📊 Data Loading")

        # The user can choose betweem uploading a file or connecting to a database
        data_source_options = DATA_SOURCE_OPTIONS
        default_index = (
            data_source_options.index(DATA_SOURCE_DEFAULT)
            if DATA_SOURCE_DEFAULT in data_source_options
            else 0
        )

        st.session_state.data_source = st.radio(
            "Select Data Source",
            data_source_options,
            index=default_index,
            horizontal=True,
            help="Choose to upload a local file or connect to a cloud database.",
        )

        if st.session_state["data_source"] == "filesystem":
            self.render_file_upload()

        elif st.session_state["data_source"] == "snowflake":
            self.render_snowflake_connection()

        elif st.session_state["data_source"] == "bigquery":
            self.render_bigquery_connection()

    def parse_raw_tags(self, tags: str) -> list[str] | None:
        """Check and parse comma-separated tags string into a list."""
        if tags:
            tag_list = [tag.strip().replace(" ", "_") for tag in tags.split(",") if tag.strip()]
            return tag_list if tag_list else None
        return None

    def parse_raw_meta_tags(self, meta_tags: str) -> dict | None:
        """Check and parse comma-separated meta tags string into a dictionary."""
        if meta_tags:
            meta_dict = {}
            for item in meta_tags.split(","):
                if ":" in item:
                    key, value = item.split(":", 1)
                    key = key.strip().replace(" ", "_")
                    value = value.strip().replace(" ", "_")
                    meta_dict[key] = value
            return meta_dict if meta_dict else None
        return None

    def render_node_tab(self) -> None:
        """Render the node tab content."""

        if st.session_state.get("node") is not None:
            st.subheader("🗂️ Node Configuration")

            if st.session_state["data_source"] != "filesystem":
                with st.expander(
                    f"{st.session_state['data_source']} specific configuration",
                    expanded=False,
                ):
                    if st.session_state["data_source"] == "snowflake":
                        transient = st.checkbox(
                            "Transient Table",
                            value=st.session_state.configuration["models"][0]["config"].get(
                                "transient", True
                            ),
                            help="Whether to create the table as a [transient table](https://docs.snowflake.com/en/user-guide/tables-temp-transient) (if supported by the data warehouse).",
                        )
                        automatic_clustering = st.checkbox(
                            "Automatic Clustering",
                            value=st.session_state.configuration["models"][0]["config"].get(
                                "automatic_clustering", False
                            ),
                            help="Whether to enable [automatic clustering](https://docs.snowflake.com/en/user-guide/tables-auto-reclustering) on the table (if supported by the data warehouse).",
                        )
                        copy_grants = st.checkbox(
                            "Copy Grants",
                            value=st.session_state.configuration["models"][0]["config"].get(
                                "copy_grants", False
                            ),
                            help="Whether to copy grants from the source table to the target table during [cloning](https://docs.snowflake.com/en/user-guide/object-clone).",
                        )
                        cluster_by_cols = [None] + st.session_state["node"].columns.tolist()
                        cluster_by = st.multiselect(
                            "Cluster By",
                            options=cluster_by_cols,
                            default=st.session_state.configuration["models"][0]["config"].get(
                                "cluster_by", None
                            ),
                            help="String or comma-separated list of columns to [cluster](https://docs.snowflake.com/en/user-guide/tables-clustering-keys) by.",
                            placeholder="e.g., column1, column2",
                        )

                        # Fetch and display available warehouses
                        wh_options = st.session_state.sf_wh_df["WH_NAME"].tolist()
                        wh_info = st.session_state.sf_wh_df[
                            st.session_state.sf_wh_df["WH_NAME"].isin(wh_options)
                        ].to_dict(orient="records")

                        wh_help_text = "**Available Snowflake [Warehouses](https://docs.snowflake.com/en/user-guide/warehouses):**\n\n"
                        for wh in wh_info:
                            wh_help_text += f"- **{wh['WH_NAME']}** (Type: {wh['WH_TYPE']}, Size: {wh['WH_SIZE']})\n"

                        wh_options = [None] + wh_options  # Add None option at the beginning
                        snowflake_warehouse = st.selectbox(
                            "Snowflake Warehouse",
                            options=wh_options,
                            index=0,
                            help=wh_help_text,
                        )

                        st.session_state.configuration["models"][0]["config"]["transient"] = (
                            transient
                        )
                        st.session_state.configuration["models"][0]["config"][
                            "automatic_clustering"
                        ] = automatic_clustering
                        st.session_state.configuration["models"][0]["config"]["copy_grants"] = (
                            copy_grants
                        )
                        st.session_state.configuration["models"][0]["config"][
                            "snowflake_warehouse"
                        ] = snowflake_warehouse
                        st.session_state.configuration["models"][0]["config"]["cluster_by"] = (
                            cluster_by
                        )

                    elif st.session_state["data_source"] == "bigquery":
                        cluster_by_cols = [None] + st.session_state["node"].columns.tolist()
                        cluster_by = st.multiselect(
                            "Cluster By",
                            options=cluster_by_cols,
                            default=st.session_state.configuration["models"][0]["config"].get(
                                "cluster_by", None
                            ),
                            help="String or comma-separated list of columns to [cluster](https://cloud.google.com/bigquery/docs/clustered-tables) by.",
                            placeholder="e.g., column1, column2",
                        )
                        st.session_state.configuration["models"][0]["config"]["cluster_by"] = (
                            cluster_by
                        )

                        partition_by_col = st.selectbox(
                            "Partition By",
                            options=[None] + st.session_state["node"].columns.tolist(),
                            index=0,
                            help="Column to [partition](https://cloud.google.com/bigquery/docs/partitioned-tables) by.",
                        )

                        partition_by = None

                        if partition_by_col is not None:
                            data_type = None
                            for c in st.session_state["configuration"]["models"][0]["columns"]:
                                if c["name"] == partition_by_col:
                                    data_type = c["data_type"]
                                    break

                            if not data_type:
                                st.error(
                                    f"⚠️ Unable to determine data type for the selected partition column '{partition_by_col}'. Please ensure the column exists in the model."
                                )
                                raise ValueError("Partition column data type not found.")

                            partition_type = None
                            if data_type not in [
                                "DATE",
                                "TIMESTAMP",
                                "DATETIME",
                                "INT64",
                            ]:
                                st.error(
                                    f"⚠️ The selected partition column '{partition_by_col}' has data type '{data_type}', which may not be suitable for partitioning in BigQuery. "
                                    "Consider using a column with DATE, TIMESTAMP, DATETIME, or INT64 data type."
                                )
                            else:
                                if data_type in ["DATE", "TIMESTAMP", "DATETIME"]:
                                    partition_type = "date_or_timestamp"
                                else:
                                    partition_type = "integer_range"

                            if partition_type == "integer_range":
                                if (
                                    st.session_state.configuration["models"][0]["config"].get(
                                        "partition_by"
                                    )
                                    is not None
                                ):
                                    if (
                                        st.session_state.configuration["models"][0]["config"]
                                        .get("partition_by")
                                        .get("range")
                                        is not None
                                    ):
                                        if (
                                            st.session_state.configuration["models"][0]["config"][
                                                "partition_by"
                                            ]["range"].get("start")
                                            is not None
                                        ):
                                            default_integer_range_start = (
                                                st.session_state.configuration["models"][0][
                                                    "config"
                                                ]["partition_by"]["range"].get("start", 0)
                                            )

                                        if (
                                            st.session_state.configuration["models"][0]["config"][
                                                "partition_by"
                                            ]["range"].get("end")
                                            is not None
                                        ):
                                            default_integer_range_end = (
                                                st.session_state.configuration["models"][0][
                                                    "config"
                                                ]["partition_by"]["range"].get("end", 100)
                                            )

                                        if (
                                            st.session_state.configuration["models"][0]["config"][
                                                "partition_by"
                                            ]["range"].get("interval")
                                            is not None
                                        ):
                                            default_integer_range_interval = (
                                                st.session_state.configuration["models"][0][
                                                    "config"
                                                ]["partition_by"]["range"].get("interval", 10)
                                            )
                                else:
                                    default_integer_range_start = 0
                                    default_integer_range_end = 100
                                    default_integer_range_interval = 10

                                if default_integer_range_start >= default_integer_range_end:
                                    st.error(
                                        "⚠️ The 'Integer Range Start' must be less than the 'Integer Range End'. Please adjust the values accordingly."
                                    )
                                    partition_by = None

                                else:
                                    integer_range_start = st.number_input(
                                        "Integer Range Start",
                                        value=default_integer_range_start,
                                        help="Start value for integer range partitioning.",
                                    )

                                    integer_range_end = st.number_input(
                                        "Integer Range End",
                                        value=default_integer_range_end,
                                        help="End value for integer range partitioning.",
                                    )

                                    integer_range_interval = st.number_input(
                                        "Integer Range Interval",
                                        value=default_integer_range_interval,
                                        help="Interval for integer range partitioning.",
                                    )

                                    if integer_range_start >= integer_range_end:
                                        st.error(
                                            "⚠️ The 'Integer Range Start' must be less than the 'Integer Range End'. Please adjust the values accordingly."
                                        )
                                        partition_by = None
                                    else:
                                        partition_by = {
                                            "field": partition_by_col,
                                            "data_type": data_type,
                                            "range": {
                                                "start": integer_range_start,
                                                "end": integer_range_end,
                                                "interval": integer_range_interval,
                                            },
                                        }
                            elif partition_type == "date_or_timestamp":
                                if (
                                    st.session_state.configuration["models"][0]["config"].get(
                                        "partition_by"
                                    )
                                    is not None
                                ):
                                    granularity_options = [
                                        "hour",
                                        "day",
                                        "month",
                                        "year",
                                    ]
                                    granularity = st.selectbox(
                                        "Partition Granularity",
                                        options=granularity_options,
                                        index=1,
                                        help="Granularity for date or timestamp partitioning.",
                                    )
                                    time_ingestion_partitioning = st.checkbox(
                                        "Ingestion Time Partitioning",
                                        value=st.session_state.configuration["models"][0]["config"][
                                            "partition_by"
                                        ].get("time_ingestion_partitioning", False),
                                        help=(
                                            "If set to true, the table will be partitioned based on the ingestion time. "
                                            + "This option is only applicable for date or timestamp partitioning."
                                        ),
                                    )

                                partition_by = {
                                    "field": partition_by_col,
                                    "data_type": data_type,
                                    "granularity": granularity,
                                    "time_ingestion_partitioning": time_ingestion_partitioning,
                                }

                        st.session_state.configuration["models"][0]["config"]["partition_by"] = (
                            partition_by
                        )

                        if (
                            st.session_state.configuration["models"][0]["config"]["partition_by"]
                            is not None
                        ):
                            require_partition_filter = st.checkbox(
                                "Require Partition Filter",
                                value=st.session_state.configuration["models"][0]["config"].get(
                                    "require_partition_filter", False
                                ),
                                help=(
                                    "If set to true, anyone querying this model must specify a partition filter, "
                                    + "otherwise their query will fail. This is recommended for very large tables. "
                                    + "Note that this will affect other dbt models or tests that try to select from this model, too."
                                ),
                            )
                            st.session_state.configuration["models"][0]["config"][
                                "require_partition_filter"
                            ] = require_partition_filter

                            if partition_type == "date_or_timestamp":
                                partition_expiration_days = st.number_input(
                                    "Partition Expiration Days",
                                    min_value=0,
                                    value=st.session_state.configuration["models"][0]["config"].get(
                                        "partition_expiration_days", 0
                                    ),
                                    help=(
                                        "If set for date- or timestamp-type partitions, the partition will expire that many days after the date it represents. "
                                        + "E.g. A partition representing `2021-01-01`, set to expire after 7 days, will no longer be queryable as of `2021-01-08`. "
                                        + "A value of 0 means the partition never expires."
                                    ),
                                    placeholder=("e.g., 30 for 30 days, 0 for never"),
                                )
                                if partition_expiration_days == 0:
                                    partition_expiration_days = None
                                st.session_state.configuration["models"][0]["config"][
                                    "partition_expiration_days"
                                ] = partition_expiration_days
                        else:
                            st.session_state.configuration["models"][0]["config"][
                                "require_partition_filter"
                            ] = None

                        # labels = st.text_area(
                        #     "Labels",
                        #     value=st.session_state.configuration["models"][0]["config"]["labels"] or None,
                        #     placeholder="e.g., key1:value1, key2:value2",
                        #     help=(
                        #         "Comma-separated list of key:value pairs to set as [labels](https://cloud.google.com/bigquery/docs/labels-intro) on the table."
                        #         + "BigQuery table and view tags can be created by supplying an empty string for the label value. E.g., `key1:, key2:value2`"
                        #     ),
                        # )
                        # resource_tags = st.text_area(
                        #     "Resource Tags",
                        #     value=",".join(
                        #         f"{k}:{v}"
                        #         for k, v in st.session_state.configuration["models"][0][
                        #             "config"
                        #         ].get("resource_tags", {}).items()
                        #     ),
                        #     placeholder="e.g., key1:value1, key2:value2",
                        #     help=(
                        #         "Comma-separated list of key:value pairs to set as [resource tags](https://cloud.google.com/bigquery/docs/resource-tags) on the table."
                        #         + "BigQuery table and view tags can be created by supplying an empty string for the tag value. E.g., `key1:, key2:value2`"
                        #     ),
                        # )

            node_enabled = st.checkbox(
                "Enable Node",
                value=True,
                help="Whether the node is [enabled](https://docs.getdbt.com/reference/resource-configs/enabled). If unchecked, the node will be disabled in dbt configuration.",
            )

            node_contract_enforced = st.checkbox(
                "Enforce Contract",
                value=False,
                help="Whether to enforce the [contract](https://docs.getdbt.com/docs/mesh/govern/model-contracts) for the node.",
            )
            if node_contract_enforced is True:
                node_contract_enforced_alias_types = st.checkbox(
                    "Contract Alias Types",
                    value=False,
                    help="Whether to enforce contract alias types for the node.",
                )

            st.session_state["node_type"] = st.selectbox(
                "Select Node Type",
                ["model", "snapshot"],
                index=0,
                help="""Type of dbt node to configure:
                [model](https://docs.getdbt.com/docs/build/snapshots)
                or [snapshot](https://docs.getdbt.com/docs/build/snapshots)""",
            )

            node_name = st.text_input(
                "Node Name",
                value=st.session_state.configuration["models"][0]["name"] or None,
                placeholder="e.g., my_model",
                help="Name of the dbt node as it will be used by dbt configuration.",
            )

            node_description = st.text_area(
                "Node Description",
                help="Description of the node as it will be used by dbt configuration.",
                placeholder=(
                    "A concise description of what the node is or is not. "
                    "And any other notes from the developer. "
                    "All the cool kids do it. And so should you! ;)"
                ),
                value=st.session_state.configuration["models"][0]["description"] or None,
            )

            node_database = st.text_input(
                "Node Database",
                value=None,
                placeholder="e.g., my_database",
                help="Database of the node.",
            )

            node_schema = st.text_input(
                "Node Schema",
                value=None,
                placeholder="e.g., public",
                help="[Schema](https://docs.getdbt.com/reference/resource-configs/schema) of the node.",
            )

            if st.session_state["node_type"] in ["model", "snapshot"]:
                materializations = [
                    "table",
                    "view",
                    "incremental",
                    "ephemeral",
                    "materialized_view",
                ]
                if st.session_state["data_source"] == "snowflake":
                    materializations.remove("materialized_view")
                    materializations.append("dynamic_table")

                if st.session_state["node_type"] == "snapshot":
                    materializations = ["table"]

                cfg_materialization = st.session_state.configuration["models"][0]["config"].get(
                    "materialized", "table"
                )
                node_materialization = st.selectbox(
                    "Materialization",
                    materializations,
                    index=(
                        materializations.index(cfg_materialization)
                        if cfg_materialization in materializations
                        else 0
                    ),
                    help="[Materialization](https://docs.getdbt.com/docs/build/materializations) strategy for the dbt model. ",
                )

                if (
                    node_materialization == "view"
                    and st.session_state["data_source"] == "snowflake"
                ):
                    secure_view = st.checkbox(
                        "Secure View",
                        value=st.session_state.configuration["models"][0]["config"].get(
                            "secure_view", False
                        ),
                        help="Whether to enable as Snowflake [secure view](https://docs.snowflake.com/en/user-guide/views-secure).",
                    )
                    st.session_state.configuration["models"][0]["config"]["secure_view"] = (
                        secure_view
                    )

                if node_materialization == "incremental":
                    unique_keys_options = st.session_state["node"].columns.tolist()
                    node_unique_key = st.multiselect(
                        "Unique Key",
                        options=unique_keys_options,
                        default=unique_keys_options[0],
                        help="[Unique key](https://docs.getdbt.com/reference/resource-configs/unique_key) for incremental models. For composite keys, provide comma-separated column names.",
                    )
                    if len(node_unique_key) == 1:
                        node_unique_key = node_unique_key[0]

                    incremental_strategies = ["merge"]
                    if st.session_state["data_source"] == "snowflake":
                        incremental_strategies.append("append")
                        incremental_strategies.append("insert_overwrite")
                        incremental_strategies.append("delete+insert")
                        incremental_strategies.append("microbatch")
                    if st.session_state["data_source"] == "bigquery":
                        incremental_strategies.append("microbatch")
                        incremental_strategies.append("insert_overwrite")

                    node_incremental_strategy = st.selectbox(
                        "Incremental Strategy",
                        incremental_strategies,
                        index=0,
                        help="[Incremental strategy](https://docs.getdbt.com/docs/build/incremental-strategy) for the dbt model.",
                    )

                    if node_incremental_strategy == "merge":
                        node_merge_update_columns = st.text_input(
                            "Merge Update Columns",
                            value=None,
                            placeholder="e.g., col1, col2",
                            help="Comma-separated list of columns to update in the target table when using the merge strategy.",
                        )

                        node_merge_merge_exclude_columns = st.text_input(
                            "Merge Exclude Columns",
                            value=None,
                            placeholder="e.g., col1, col2",
                            help="Comma-separated list of columns to exclude from the merge operation when using the merge strategy.",
                        )

                if node_materialization in ["materialized_view", "dynamic_table"]:
                    on_configuration_change = st.selectbox(
                        "On Configuration Change",
                        options=["apply", "continue", "fail"],
                        help="[Setting](https://docs.getdbt.com/reference/resource-configs/on_configuration_change) for materialized views/dynamic tables only.",
                        index=0,
                    )
                    st.session_state.configuration["models"][0]["config"][
                        "on_configuration_change"
                    ] = on_configuration_change

                if st.session_state["node_type"] == "snapshot":
                    hard_deletes = st.selectbox(
                        "Hard Deletes",
                        options=["ignore", "invalidate", "new_record"],
                        help="[Hard Deletes](https://docs.getdbt.com/reference/resource-configs/hard-deletes) option for the snapshot.",
                    )
                    st.session_state.configuration["models"][0]["config"]["hard_deletes"] = (
                        hard_deletes
                    )

                    unique_keys_options = st.session_state["node"].columns.tolist()
                    node_unique_key = st.multiselect(
                        "Unique Key",
                        options=unique_keys_options,
                        default=unique_keys_options[0],
                        help="[Unique Key](https://docs.getdbt.com/docs/build/snapshots#unique-key) for the snapshot.",
                    )
                    if len(node_unique_key) == 1:
                        node_unique_key = node_unique_key[0]
                    st.session_state.configuration["models"][0]["config"]["unique_key"] = (
                        node_unique_key
                    )

                    strategy = st.selectbox(
                        "Strategy",
                        options=["timestamp", "check"],
                        index=0,
                        help="[Strategy](https://docs.getdbt.com/docs/build/snapshots#strategy) for the snapshot.",
                    )
                    st.session_state.configuration["models"][0]["config"]["strategy"] = strategy

                    if strategy == "timestamp":
                        # TODO: only date/time/integer columns
                        updated_at = st.selectbox(
                            "Updated At",
                            options=unique_keys_options,
                            index=0,
                            help="[Updated At](https://docs.getdbt.com/docs/build/snapshots#updated-at) column for the snapshot.",
                        )
                        st.session_state.configuration["models"][0]["config"]["updated_at"] = (
                            updated_at
                        )

                    elif strategy == "check":
                        check_cols_options = ["all"] + st.session_state["node"].columns.tolist()
                        check_cols = st.multiselect(
                            "Check Columns",
                            options=check_cols_options,
                            default="all",
                            help="[Check Columns](https://docs.getdbt.com/docs/build/snapshots#check-columns) for the snapshot.",
                        )
                        if "all" in check_cols:
                            check_cols = "all"
                        st.session_state.configuration["models"][0]["config"]["check_cols"] = (
                            check_cols
                        )

                    st.session_state.configuration["models"][0]["config"][
                        "incremental_strategy"
                    ] = None

                else:
                    st.session_state.configuration["models"][0]["config"]["unique_key"] = None
                    st.session_state.configuration["models"][0]["config"]["updated_at"] = None
                    st.session_state.configuration["models"][0]["config"]["check_cols"] = None
                    st.session_state.configuration["models"][0]["config"]["strategy"] = None
                    st.session_state.configuration["models"][0]["config"]["hard_deletes"] = None
                    st.session_state.configuration["models"][0]["config"]["check_cols"] = None

                node_pre_hook = st.text_area(
                    "Pre-hook SQL",
                    help="[SQL](https://docs.getdbt.com/reference/resource-configs/pre-hook-post-hook) to run before the node is built.",
                    placeholder="e.g., alter external table {{ source('sys', 'customers').render() }} refresh",
                    value=None,
                    height=25,
                )

                node_post_hook = st.text_area(
                    "Post-hook SQL",
                    help="[SQL](https://docs.getdbt.com/reference/resource-configs/pre-hook-post-hook) to run after the node is built.",
                    placeholder="e.g., unload ('select from {{ this }}') to 's3:/bucket_name/{{ this }}",
                    value=None,
                    height=25,
                )

                node_alias = st.text_input(
                    "Node Alias (optional)",
                    value=None,
                    placeholder="e.g., my_model_alias",
                    help="[Alias](https://docs.getdbt.com/reference/resource-configs/alias) for the node, if different from the name.",
                )

            node_tags = st.text_input(
                "Node Tags",
                help="Comma-separated [tags](https://docs.getdbt.com/reference/resource-configs/tags) for the node.",
                placeholder="e.g., pii, financial, etc.",
                value=None,
            )

            node_meta_tags = st.text_input(
                "Node Meta Tags",
                help="Comma-separated [meta](https://docs.getdbt.com/reference/resource-configs/meta) tags for the node.",
                placeholder="e.g., source:api, owner:team, etc.",
                value=None,
            )
            if node_meta_tags and not self.parse_raw_meta_tags(node_meta_tags):
                st.error("❌ Meta tags must be in key:value format, separated by commas.")

            st.session_state.configuration["models"][0]["name"] = node_name
            st.session_state.configuration["models"][0]["description"] = node_description
            st.session_state.configuration["models"][0]["config"]["database"] = node_database
            st.session_state.configuration["models"][0]["config"]["schema"] = node_schema

            if st.session_state["node_type"] in ["model", "snapshot"]:
                st.session_state.configuration["models"][0]["enabled"] = node_enabled

                st.session_state.configuration["models"][0]["config"]["materialized"] = (
                    node_materialization
                )

                if node_materialization == "incremental":
                    if node_unique_key:
                        # Convert comma-separated string to a list of column names
                        st.session_state.configuration["models"][0]["config"]["unique_key"] = (
                            node_unique_key
                        )

                    if node_incremental_strategy:
                        st.session_state.configuration["models"][0]["config"][
                            "incremental_strategy"
                        ] = node_incremental_strategy

                        if node_incremental_strategy == "merge":
                            if node_merge_update_columns:
                                st.session_state.configuration["models"][0]["config"][
                                    "merge_update_columns"
                                ] = [
                                    col.strip()
                                    for col in node_merge_update_columns.split(",")
                                    if col.strip()
                                ]

                            if node_merge_merge_exclude_columns:
                                st.session_state.configuration["models"][0]["config"][
                                    "merge_exclude_columns"
                                ] = [
                                    col.strip()
                                    for col in node_merge_merge_exclude_columns.split(",")
                                    if col.strip()
                                ]

                st.session_state.configuration["models"][0]["config"]["contract"]["enforced"] = (
                    node_contract_enforced
                )

                if node_contract_enforced is True:
                    st.session_state.configuration["models"][0]["config"]["contract"][
                        "alias_types"
                    ] = node_contract_enforced_alias_types
                st.session_state.configuration["models"][0]["config"]["alias"] = node_alias

            if node_tags:
                st.session_state.configuration["models"][0]["config"]["tags"] = self.parse_raw_tags(
                    node_tags
                )
            if node_meta_tags:
                st.session_state.configuration["models"][0]["config"]["meta"] = (
                    self.parse_raw_meta_tags(node_meta_tags)
                )

            st.session_state.configuration["models"][0]["pre_hook"] = node_pre_hook
            st.session_state.configuration["models"][0]["post_hook"] = node_post_hook

            # st.subheader("🗂️ Data Tests")
            # TODO: Certain tests support the optional group_by_columns argument to provide more granularity in performing tests.
            # This feature is currently available for the following data tests:
            # equal_rowcount
            # fewer_rows_than
            # recency
            # at_least_one
            # not_constant
            # sequential_values
            # not_null_proportion

            # node_data_tests = st.multiselect(
            #     "Select [generic data tests](https://github.com/dbt-labs/dbt-utils?tab=readme-ov-file#generic-test) to apply to the node",
            #     options=[
            #         "equal_rowcount",
            #         "fewer_rows_than",
            #         "equality",
            #         "expression_is_true",
            #         "recency",
            #         "at_least_one",
            #         "not_constant",
            #         "not_empty_string",
            #         "cardinality_equality",
            #         "not_null_proportion",
            #         "not_accepted_values",
            #         "relationships_where",
            #         "mutually_exclusive_ranges",
            #         "sequential_values",
            #         "unique_combination_of_columns",
            #         "accepted_range",
            #     ],
            # )

        else:
            st.warning("⚠️ Please upload a dataset in the Data tab to enable node configuration.")

    @staticmethod
    def clean_dict(data, keep_keys=None):
        """
        Recursively remove keys with empty or null-like values from a dictionary.

        Args:
            data (dict): The dictionary to clean.
            keep_keys (list): Keys to keep even if their values are null/empty.

        Returns:
            dict: A cleaned dictionary.
        """
        if keep_keys is None:
            keep_keys = []

        if not isinstance(data, dict):
            return data

        cleaned = {}
        for key, value in data.items():
            if isinstance(value, dict):
                value = DocbtServer.clean_dict(value, keep_keys)
            elif isinstance(value, list):
                value = [
                    DocbtServer.clean_dict(v, keep_keys) if isinstance(v, dict) else v
                    for v in value
                ]
                value = [v for v in value if v not in (None, "", {}, [])]

            # check emptiness
            if key in keep_keys or value not in (None, "", {}, []):
                cleaned[key] = value

        return cleaned

    def create_default_configuration(self) -> dict:
        default_node_configuration = {}
        # copy.deepcopy(st.session_state["configuration"]["models"][0])
        """Create a default configuration structure."""
        for key in [
            "name",
            "description",
            "tags",
            "meta",
            "data_tests",
            "constraints",
            "pre_hook",
            "post_hook",
        ]:
            default_node_configuration[key] = None
        default_node_configuration["enabled"] = True
        default_node_configuration["config"] = {
            "database": None,
            "schema": None,
            "tags": None,
            "meta": None,
            "materialized": "table",
            "contract": {
                "enforced": False,
            },
        }

        info_df = pd.DataFrame()

        if st.session_state["data_source"] == "snowflake":
            if st.session_state.get("sf_table_info_df") is not None:
                st.session_state.sf_table_info_df.columns = [
                    col.lower() for col in st.session_state.sf_table_info_df.columns
                ]
                info_df = st.session_state.sf_table_info_df.copy().to_dict(orient="records")[0]

                default_node_configuration["name"] = info_df["table_name"]
                default_node_configuration["description"] = info_df["description"]

                if info_df["table_type"] == "VIEW":
                    default_node_configuration["config"]["materialized"] = "view"

                elif info_df["is_dynamic"] is True:
                    default_node_configuration["config"]["materialized"] = "dynamic_table"

                else:
                    default_node_configuration["config"]["materialized"] = "table"

            snowflake_configs = {
                "transient": info_df["is_transient"] or True,
                "snowflake_warehouse": None,
                "cluster_by": None,
                "automatic_clustering": info_df["auto_clustering_on"] or False,
                "copy_grants": True,
                "row_access_policys": None,
            }

            for config_key, default_value in snowflake_configs.items():
                default_node_configuration["config"][config_key] = default_value

        elif st.session_state["data_source"] == "bigquery":
            if st.session_state.get("bq_table_info_df") is not None:
                st.session_state.bq_table_info_df.columns = [
                    col.lower() for col in st.session_state.bq_table_info_df.columns
                ]
                info_df = st.session_state.bq_table_info_df.copy().to_dict(orient="records")[0]

                default_node_configuration["name"] = info_df["table_name"]

                if info_df["table_type"] == "VIEW":
                    default_node_configuration["config"]["materialized"] = "view"

                else:
                    default_node_configuration["config"]["materialized"] = "table"

            bigquery_configs = {
                "partition_by": None,
                "cluster_by": None,
                # "require_partition_filter": None,
                # "labels": None,
                # "resource_tags": None,
                # "partition_expiration_days": None,
            }

            for config_key, default_value in bigquery_configs.items():
                default_node_configuration["config"][config_key] = default_value

        return default_node_configuration

    def create_default_column_dict(self) -> dict:
        """Create a default column dictionary structure.

        If data source schema information is available, populate the default
        structure with relevant details.

        Returns:
            dict: A default column dictionary.
        """
        data_source = st.session_state["data_source"]
        schema = None

        columns_section = [
            copy.deepcopy(DEFAULT_COL_DICT) for _ in range(len(st.session_state.node.columns))
        ]

        if data_source == "snowflake":
            # Update columns_section with Snowflake schema details
            schema = st.session_state.sf_cols_df.to_dict(orient="records")

        elif data_source == "bigquery":
            # Update columns_section with BigQuery schema details
            schema = st.session_state.bq_cols_df.to_dict(orient="records")

        for i, col in enumerate(st.session_state.node.columns):
            columns_section[i]["name"] = col

            if schema:
                if data_source == "snowflake":
                    for scol in schema:
                        if columns_section[i]["name"] == scol["COL_NAME"]:
                            columns_section[i]["description"] = scol["DESCRIPTION"]
                            columns_section[i]["data_type"] = scol["DATA_TYPE"]

                            constraints = []
                            if scol["CONSTR_NULL"] is True:
                                constraints.append({"type": "not_null"})
                            if scol["CONSTR_PK"] is True:
                                constraints.append({"type": "primary_key"})
                            if scol["CONSTR_UNIQUE"] is True:
                                constraints.append({"type": "unique"})

                            columns_section[i]["constraints"] = constraints if constraints else None
                            break  # Exit inner loop once a match is found
                elif data_source == "bigquery":
                    for scol in schema:
                        if columns_section[i]["name"] == scol["COLUMN_NAME"]:
                            columns_section[i]["description"] = scol["DESCRIPTION"]
                            columns_section[i]["data_type"] = scol["DATA_TYPE"]

                            constraints = []
                            if scol["IS_NULLABLE"] is True:
                                constraints.append({"type": "not_null"})
                            # BigQuery does not have direct PK/Unique constraints in the same way as Snowflake
                            # Additional logic can be added here if needed

                            if scol["CONSTRAINT_TYPE"] is not None:
                                constraints.append(
                                    {"type": scol["CONSTRAINT_TYPE"].lower().replace(" ", "_")}
                                )

                            columns_section[i]["constraints"] = constraints if constraints else None
                            break  # Exit inner loop once a match is found

        return columns_section

    def render_columns_tab(self) -> None:
        """Render the columns tab content."""
        st.subheader("🗂️ Columns Configuration")

        pk_counter = 0

        if (
            st.session_state.get("node") is not None
            and st.session_state.get("configuration") is not None
        ):
            st.markdown("Define description, basic attributes, constraints and tests.")

            i = 0
            for col in st.session_state["configuration"]["models"][0]["columns"]:
                colname = col["name"]

                with st.expander(colname.upper(), expanded=False):
                    col_desc = st.text_area(
                        "Description",
                        help="Description of the column as it will be used by dbt configuration.",
                        placeholder=(
                            "A concise description of what the column is or is not. "
                            "And any other notes from the developer. "
                            "All the cool kids do it. And so should you! ;)"
                        ),
                        value=st.session_state["configuration"]["models"][0]["columns"][i][
                            "description"
                        ]
                        or None,
                        key=f"{col}_desc",
                    )

                    col_dtype_placeholder = "e.g., integer, string, timestamp, etc."
                    col_dtype = st.text_input(
                        "Data Type",
                        help="Data type of the column.",
                        placeholder=col_dtype_placeholder,
                        value=st.session_state["configuration"]["models"][0]["columns"][i][
                            "data_type"
                        ]
                        or None,
                        key=f"{colname}_dtype",
                    )

                    col_tags = st.text_input(
                        "Tags",
                        help="Comma-separated tags for the column.",
                        placeholder="e.g., pii, financial, etc.",
                        value=None,
                        key=f"{colname}_tags",
                    )

                    col_meta_tags = st.text_input(
                        "Meta Tags",
                        help="Comma-separated meta tags for the column.",
                        placeholder="e.g., source:api, owner:team, etc.",
                        value=None,
                        key=f"{colname}_meta_tags",
                    )

                    if st.session_state["configuration"]["models"][0]["columns"][i]["constraints"]:
                        col_constraints_value = [
                            c["type"]
                            for c in st.session_state["configuration"]["models"][0]["columns"][i][
                                "constraints"
                            ]
                        ]
                        for cc in col_constraints_value:
                            if cc not in [
                                "not_null",
                                "unique",
                                "primary_key",
                                "foreign_key",
                            ]:
                                col_constraints_value.remove(cc)
                                logger.warning(
                                    f"⚠️  Unsupported constraint '{cc}' found in column '{colname}' and removed."
                                )
                    else:
                        col_constraints_value = None

                    col_constraints = st.multiselect(
                        "Constraints",
                        options=["not_null", "unique", "primary_key", "foreign_key"],
                        help="Select constraints for the column.",
                        key=f"{colname}_constraints",
                        default=col_constraints_value,
                    )
                    st.session_state.configuration["models"][0]["columns"][i]["constraints"] = [
                        {"type": c} for c in col_constraints
                    ]

                    for constraint in col_constraints:
                        if constraint == "primary_key":
                            pk_counter += 1
                            if pk_counter > 1:
                                st.error("⚠️ Only one primary key is allowed per model.")

                        if constraint == "foreign_key":
                            fk_expression = st.text_input(
                                key=f"{colname}_fk_expression",
                                label="Foreign Key Expression",
                                value=None,
                                max_chars=128,
                                type="default",
                                help="Expression to be used with FK constraint. Max 128 characters long.",
                                placeholder="OTHER_MODEL_SCHEMA.OTHER_MODEL_NAME (OTHER_MODEL_COLUMN)",
                                disabled=False,
                                label_visibility="visible",
                            )
                            # Check if foreign_key constraint is selected and there's a valid expression
                            if "foreign_key" in col_constraints and fk_expression:
                                # Find the foreign_key constraint and add the expression
                                for constraint in st.session_state.configuration["models"][0][
                                    "columns"
                                ][i]["constraints"]:
                                    if constraint["type"] == "foreign_key":
                                        constraint["expression"] = fk_expression
                                        break
                        else:
                            pass

                    if st.session_state["configuration"]["models"][0]["columns"][i]["data_tests"]:
                        col_data_tests_value = []
                        for c in st.session_state["configuration"]["models"][0]["columns"][i][
                            "data_tests"
                        ]:
                            if isinstance(c, str):
                                col_data_tests_value.append(c)
                            elif isinstance(c, dict):
                                col_data_tests_value.extend(c.keys())
                    else:
                        col_data_tests_value = None

                    col_data_tests = st.multiselect(
                        "Data Tests",
                        options=[
                            "not_null",
                            "unique",
                            "distinct",
                            "accepted_values",
                            "relationships",
                        ],
                        help="Select data tests for the column.",
                        key=f"{colname}_data_tests",
                        default=col_data_tests_value,
                    )

                    st.session_state.configuration["models"][0]["columns"][i]["data_tests"] = (
                        col_data_tests
                    )

                    if col_data_tests:
                        for test in col_data_tests:
                            DocbtServer.configure_test(
                                colname,
                                test,
                                st.session_state.configuration["models"][0]["columns"],
                                i,
                            )

                    st.session_state.configuration["models"][0]["columns"][i]["data_type"] = (
                        col_dtype
                    )

                    st.session_state.configuration["models"][0]["columns"][i]["description"] = (
                        col_desc
                    )

                    st.session_state.configuration["models"][0]["columns"][i]["tags"] = (
                        self.parse_raw_tags(col_tags)
                    )

                    st.session_state.configuration["models"][0]["columns"][i]["meta"] = (
                        self.parse_raw_meta_tags(col_meta_tags)
                    )

                i += 1

        else:
            st.warning("⚠️ No node selected.")

    @staticmethod
    def args_accepted_values(colname: str) -> list:
        """Get accepted values for the accepted_values test."""
        accepted_values = (
            st.text_area(
                "*Accepted_values* list",
                key=f"{colname}_accepted_values",
                max_chars=256,
                help="Configuration for accepted_values test. Add a list of values.",
                placeholder="value1,value2",
                value="",
            )
            .replace(" ", "")
            .split(",")
        )
        if accepted_values == [""]:
            st.warning("⚠️ Please provide at least one accepted value.")
        quote_values = st.checkbox(
            "Quote accepted_values",
            value=True,
            key=f"{colname}_accepted_values_quote",
            help="Whether to quote the accepted values in the test configuration.",
        )
        return {"values": accepted_values, "quote": quote_values}

    @staticmethod
    def args_relationships(colname: str) -> dict:
        """Get arguments for relationships test."""
        related_model = st.text_input(
            "Related model",
            key=f"{colname}_relationships_model",
            max_chars=128,
            type="default",
            help="Configuration for relationships test. Add the related model in the format: schema.model",
            placeholder="schema.model",
            value="",
        )
        related_column = st.text_input(
            "Related column",
            key=f"{colname}_relationships_column",
            max_chars=128,
            type="default",
            help="Configuration for relationships test. Add the related column name.",
            placeholder="column_name",
            value="",
        )
        if not related_model or not related_column:
            st.warning("⚠️ Please provide both related model and related column.")
        return {"to": related_model, "field": related_column}

    @staticmethod
    def args_generic_test(testname: str, colname: str) -> dict:
        """Get accepted arguments for generic tests."""
        if testname == "accepted_values":
            return DocbtServer.args_accepted_values(colname)
        elif testname == "relationships":
            return DocbtServer.args_relationships(colname)
        else:
            return {}

    @staticmethod
    def configure_test(colname: str, testname: str, columns_section: list[dict], i: int) -> None:
        """Configure a specific data test for a column."""
        with st.expander(
            f"*{testname}* config",
        ):
            args = DocbtServer.args_generic_test(testname, colname)

            enable_conf = st.checkbox(
                "config",
                value=False,
                key=f"{colname}_{testname}_enable",
            )

            where = st.text_input(
                "where",
                key=f"{colname}_{testname}_where",
                value=None,
                max_chars=128,
                type="default",
                help=f"Configuration for {testname} test. Add a where condition.",
                placeholder="where clause",
            )

            severity_choice = st.radio(
                key=f"{colname}_{testname}_severity",
                label="severity",
                options=["warn", "error"],
                index=1,
            )

            warn_if_choice = st.text_input(
                key=f"{colname}_{testname}_warn_if",
                label="warn_if",
                placeholder="e.g., > 1 or < 2 or >= 3",
                value=None,
            )
            valid_warn_if_choice = DocbtServer.validate_if_choice(warn_if_choice)

            error_if_choice = st.text_input(
                key=f"{colname}_{testname}_error_if",
                label="error_if",
                placeholder="e.g., > 1 or < 2 or >= 3",
                value=None,
            )
            valid_error_if_choice = DocbtServer.validate_if_choice(error_if_choice)

            config = {
                "where": where,
                "severity": severity_choice,
                "warn_if": (warn_if_choice if valid_warn_if_choice is not False else None),
                "error_if": (error_if_choice if valid_error_if_choice is not False else None),
            }

            for idx, test in enumerate(columns_section[i]["data_tests"]):
                if (isinstance(test, str) and test == testname) or (
                    isinstance(test, dict) and testname in test
                ):
                    columns_section[i]["data_tests"][idx] = {
                        testname: {
                            **args,
                            "config": config if enable_conf else {},
                        }
                    }
                    break

    @staticmethod
    def validate_if_choice(choice: str) -> bool:
        """Validate choice like e.g., > 1 or < 2 or >= 3, etc."""
        pattern = r"^(>=|<=|>|<|==|!=)\s*\d+$"
        if choice:
            if not bool(re.match(pattern, choice.strip())):
                st.error(
                    "❌ Invalid format. Please use one of the following formats: > 1, < 2, >= 3, <= 4, == 5, != 6"
                )
                return False

    @staticmethod
    def _order_dict(d: dict, key_order: list) -> dict:
        """Reorder dictionary keys according to specified order."""
        ordered = OrderedDict()
        for key in key_order:
            if key in d:
                ordered[key] = d[key]
        for key, value in d.items():
            if key not in ordered:
                ordered[key] = value
        return ordered

    def _create_ordered_yaml(self, data: dict, type: str = "model") -> dict:
        """Create YAML with a specific key order for better readability."""

        # Define the desired order for top-level YAML keys
        top_level_key_order = [
            "version",
            f"{type}s",
        ]

        if type == "model":
            node_key_order = [
                "name",
                "description",
                "enabled",
                "config",
                "data_tests",
                "pre_hook",
                "post_hook",
                "tags",
                "meta",
                # "transient",
                "constraints",
                "columns",
            ]
            model_config_key_order = [
                "materialized",
                "database",
                "schema",
                "alias",
                "unique_key",
                "incremental_strategy",
                "merge_update_columns",
                "merge_exclude_columns",
                "contract",
                "tags",
                "meta",
            ]

            column_key_order = [
                "name",
                "description",
                "data_type",
                "constraints",
                "tags",
                "meta",
                "data_tests",
            ]

        else:
            raise ValueError("Unsupported type. Supported types are 'model', 'source', 'snapshot'.")

        # Process the data structure
        if isinstance(data, dict):
            ordered_data = OrderedDict()

            # Order top-level keys first (version, models/sources/snapshots)
            for key in top_level_key_order:
                if key in data:
                    ordered_data[key] = data[key]

            # Process models/sources/snapshots with their specific ordering
            for key in ["models", "sources", "snapshots"]:
                if key in data and key not in ordered_data:
                    if key == "models" and isinstance(data[key], list):
                        ordered_models = []
                        for model in data[key]:
                            ordered_model = self._order_dict(model, node_key_order)

                            # Order config section if it exists
                            if "config" in ordered_model:
                                ordered_model["config"] = self._order_dict(
                                    ordered_model["config"], model_config_key_order
                                )

                            # Order columns if they exist
                            if "columns" in ordered_model and isinstance(
                                ordered_model["columns"], list
                            ):
                                ordered_columns = []
                                for column in ordered_model["columns"]:
                                    ordered_columns.append(
                                        self._order_dict(column, column_key_order)
                                    )
                                ordered_model["columns"] = ordered_columns

                            ordered_models.append(ordered_model)
                        ordered_data[key] = ordered_models
                    else:
                        ordered_data[key] = data[key]

            # Add any remaining keys that weren't in the predefined orders
            for key, value in data.items():
                if key not in ordered_data:
                    ordered_data[key] = value

            return ordered_data

        return data

    def render_config(self) -> None:
        st.markdown("### 🧾 Generated dbt Configuration")
        if st.session_state.get("llm_enabled") is True:
            enhanced_prompt = self._create_enhanced_system_prompt(
                st.session_state.node,
                DEFAULT_SYSTEM_PROMPT,
                st.session_state.get("sample_size", DEFAULT_SAMPLE_SIZE),
            )
            suggestion_prompt = enhanced_prompt + SUGGESTION_PROMPT
            ai_suggestion_button = st.button(
                "AI Suggestions",
                help="Generate dataset description, column descriptions, constraints and data tests using AI.",
            )

            if ai_suggestion_button:
                st.session_state.ai_not_found_cols = []

                with st.spinner("🤔 Thinking..."):
                    if st.session_state.llm_provider == "lmstudio":
                        st.session_state.ai_suggestion = LLMProvider.chat_with_lmstudio(
                            server_url=st.session_state["llm_config"]["server"],
                            model_name=st.session_state["llm_config"]["model_name"],
                            message=suggestion_prompt,
                            system_prompt=DEFAULT_SYSTEM_PROMPT,
                            return_metrics=st.session_state.get("developer_mode"),
                            return_chain_of_thought=True,
                            max_tokens=st.session_state.get("max_tokens", 2048),
                            temperature=st.session_state.get("temperature", 0.7),
                            top_p=st.session_state.get("top_p", 1.0),
                            stop_sequences=st.session_state.get("stop_sequences", None),
                            response_format=SUGGESTIONS_RESPONSE_FORMAT,
                            timeout=st.session_state.get("timeout", 120),
                        )

                    elif st.session_state.llm_provider == "openai":
                        st.session_state.ai_suggestion = LLMProvider.chat_with_openai(
                            api_key=st.session_state["llm_config"]["api_key"],
                            model_name=st.session_state["llm_config"]["model_name"],
                            message=suggestion_prompt,
                            system_prompt=DEFAULT_SYSTEM_PROMPT,
                            return_metrics=st.session_state.get("developer_mode"),
                            max_tokens=st.session_state.get("max_tokens", 2048),
                            temperature=st.session_state.get("temperature", 0.7),
                            top_p=st.session_state.get("top_p", 1.0),
                            stop_sequences=st.session_state.get("stop_sequences", None),
                            response_format=SUGGESTIONS_RESPONSE_FORMAT,
                            timeout=st.session_state.get("timeout", 120),
                        )

                    elif st.session_state.llm_provider == "ollama":
                        st.session_state.ai_suggestion = LLMProvider.chat_with_ollama(
                            server_url=st.session_state["llm_config"]["server"],
                            model_name=st.session_state["llm_config"]["model_name"],
                            message=suggestion_prompt,
                            system_prompt=DEFAULT_SYSTEM_PROMPT,
                            return_metrics=st.session_state.get("developer_mode"),
                            return_chain_of_thought=True,
                            max_tokens=st.session_state.get("max_tokens", 2048),
                            temperature=st.session_state.get("temperature", 0.7),
                            top_p=st.session_state.get("top_p", 1.0),
                            stop_sequences=st.session_state.get("stop_sequences", None),
                            response_format=SUGGESTIONS_RESPONSE_FORMAT_OLLAMA,
                            timeout=st.session_state.get("timeout", 120),
                        )

                if not st.session_state.ai_suggestion:
                    st.error("❌ Couldn't properly process the AI response or the request.")

                else:
                    st.session_state.configuration["models"][0]["description"] = st.session_state[
                        "ai_suggestion"
                    ]["content"]["dataset_description"]
                    suggestion_columns = st.session_state["ai_suggestion"]["content"]["columns"]

                    suggested_cols_dict = {}
                    for col in suggestion_columns:
                        col_name = col.pop("column_name", None)
                        if col_name:
                            suggested_cols_dict[col_name] = col

                    for col in st.session_state.configuration["models"][0]["columns"]:
                        if col["name"] in suggested_cols_dict.keys():
                            col["description"] = suggested_cols_dict[col["name"]].get(
                                "column_description", col.get("description")
                            )

                            # Check if constraint_suggestions exists and is not None
                            constraint_suggestions = suggested_cols_dict[col["name"]].get(
                                "constraint_suggestions"
                            )
                            if constraint_suggestions:
                                col["constraints"] = [{"type": c} for c in constraint_suggestions]

                            # Check if test_suggestions exists and is not None
                            test_suggestions = suggested_cols_dict[col["name"]].get(
                                "test_suggestions"
                            )
                            if test_suggestions:
                                col["data_tests"] = test_suggestions
                        else:
                            st.session_state.ai_not_found_cols.append(col["name"])
                            logger.warning(f"Column {col['name']} not found in AI suggestions.")

                    st.rerun()

        if st.session_state.get("ai_suggestion") is not None:
            if st.session_state["ai_suggestion"].get("metrics") and not st.session_state[
                "ai_suggestion"
            ].get("error"):
                metrics = st.session_state["ai_suggestion"]["metrics"]
                self._caption_chat_metrics(metrics)

        if st.session_state.get("ai_not_found_cols") not in (None, []):
            warning_txt = ", ".join(st.session_state["ai_not_found_cols"])
            st.warning(
                f"⚠️ The following columns were not found in the AI suggestions and were left unchanged: {warning_txt}."
                + " This might due to context length limitations of the LLM. Try increasing context length or picking a larger model."
            )

        yaml_conf = st.session_state.configuration
        if st.session_state["node_type"] == "snapshot":
            # The models key must be renamed to snapshots for snapshot nodes
            yaml_conf = copy.deepcopy(st.session_state.configuration)
            yaml_conf["snapshots"] = yaml_conf.pop("models", None)

        st.code(
            yaml.dump(
                self._create_ordered_yaml(
                    DocbtServer.clean_dict(
                        yaml_conf,
                        keep_keys=[
                            "name",
                            "not_null",
                            "unique",
                            "distinct",
                            "accepted_values",
                            "relationships",
                        ],
                    )
                ),
                sort_keys=False,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
            ),
            language="yaml",
            line_numbers=False,
        )

    def render_config_tab(self) -> None:
        if st.session_state.get("node") is not None:
            self.render_config()
        else:
            st.warning("⚠️ No node selected.")

    def render_sidebar(self) -> None:
        if st.session_state.get("node") is not None:
            with st.sidebar:
                self.render_config()

    def run(self) -> None:
        """Main application entry point."""
        st.set_page_config(layout="wide")

        st.markdown("# d<span style='color: orange;'>oc</span>bt", unsafe_allow_html=True)

        tab_data, tab_node, tab_columns, tab_config, tab_ai, tab_chat = st.tabs(
            ["Data", "Node", "Columns", "Config", "AI", "Chat"]
        )

        st.session_state.configuration = DEFAULT_MODEL_CONFIG.copy()

        with tab_data:
            self.render_data_tab()

        with tab_node:
            self.render_node_tab()

        with tab_columns:
            self.render_columns_tab()

        with tab_config:
            self.render_config_tab()

        with tab_ai:
            llm_config = self.render_ai_tab()
            st.session_state.llm_config = llm_config

        with tab_chat:
            self.render_chat_tab()

        self.render_sidebar()


if __name__ == "__main__":
    server = DocbtServer()
    server.run()
