<div align="center">

<h1 style="font-size: 4em; margin-bottom: 0;">d<span style="color: #FF8C00;">oc</span>bt</h1>
<h3 style="margin-top: 0;">Documentation Build Tool</h3>

[![CI](https://github.com/aleenprd/docbt/actions/workflows/ci.yml/badge.svg)](https://github.com/aleenprd/docbt/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/aleenprd/docbt/graph/badge.svg?token=Y8TKKM9YKD)](https://codecov.io/gh/aleenprd/docbt)
[![PyPI version](https://badge.fury.io/py/docbt.svg)](https://pypi.org/project/docbt/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=flat&logo=docker&logoColor=white)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![dbt](https://img.shields.io/badge/dbt-FF694B?style=flat&logo=dbt&logoColor=white)
![Snowflake](https://img.shields.io/badge/snowflake-%2329B5E8.svg?style=flat&logo=snowflake&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)
![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=flat&logo=openai&logoColor=white)
![Dependabot](https://img.shields.io/badge/dependabot-025E8C?style=flat&logo=dependabot&logoColor=white)
![GitHub Copilot](https://img.shields.io/badge/github_copilot-8957E5?style=flat&logo=github-copilot&logoColor=white)


> Generate YAML documentation for dbt models with optional AI assistance. Built with Streamlit for an intuitive and familiar web interface.

</div>

## 📖 Why **d<span style="color: #FF8C00;">oc</span>bt**
**d<span style="color: #FF8C00;">oc</span>bt**  (Doc Build Tool) is utility designed to streamline [dbt](https://www.getdbt.com/product/what-is-dbt) (Data Build Tool) documentation workflows. Connect your data and generate professional YAML documentation ready for your DBT projects. Do this using the assistance provided by the UI and even chat with AI models to 100x your productivity!


### 👔 Target Audience
- **Analytics Engineers**: streamline your dbt workflow and maintain consistent data modelling.
- **Data Engineers**: ensure data quality across your infrastructure through thorough testing.
- **Data Managers**: automate tedious tasks and help your team focus on delivering value.
- **AI Enthusiasts**: Experiment with local LLMs or cloud providers for automation tasks.

### ✨ Key Features
- **🛠️ Non-AI Support**: Generate documentation without requiring AI models.
- **🤖 Multiple LLM Providers**: Choose from [OpenAI's GPT models](https://openai.com/api/), local [Ollama](https://ollama.com/), or [LM Studio.](https://lmstudio.ai/)
- **💬 Interactive Chat**: Ask questions about your data and get specific recommendations.
- **🔧 Developer Mode**: Token metrics, response times, parameters, prompts and debugging information.
- **⚙️ Advanced Configuration**: Fine-tune generation parameters.
- **🧠 Chain of Thought**: View AI reasoning process (when available).
- **📈 Real-time Metrics**: Monitor API usage, token consumption, and performance.
- **🔌 Multiple Data Sources**: Connect to [Snowflake](https://www.snowflake.com/en/), [BigQuery](https://cloud.google.com/bigquery?hl=en), and more for seamless data integration.

### ⏳ More to come
- **More Tests Coverage**: automation of [dbt utils](https://github.com/dbt-labs/dbt-utils), [dbt expectations](https://hub.getdbt.com/metaplane/dbt_expectations/latest/) and [dbt-data-reliability](https://github.com/elementary-data/dbt-data-reliability) packages.
- **Sources**: use docbt to automate [source](https://docs.getdbt.com/reference/source-configs) declaration and documentation.
- **Extra LM providers**: use [Gemini](https://gemini.google.com/), [Grok](https://grok.com/), [Claude](https://claude.ai/l) and others to streamline your work.
- **Extra Data Sources**: connect to [Databricks](https://www.databricks.com/), [PostgreSQL](https://www.postgresql.org/), [Redshift](https://aws.amazon.com/redshift/) and others.
- **One-click analytics**: gain critical insights into your data to better assign tests.

## � Contents

- [📖 Why **docbt**](#-why-docbt)
  - [👔 Target Audience](#-target-audience)
  - [✨ Key Features](#-key-features)
  - [⏳ More to come](#-more-to-come)
- [🚀 Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [📦 Installation](#-installation)
  - [🔧 Building from Source](#-building-from-source)
- [🎯 Usage](#-usage)
  - [Data Tab](#data-tab)
  - [Node Tab](#node-tab)
  - [Columns Tab](#columns-tab)
  - [Sidebar and Config Tab](#sidebar-and-config-tab)
  - [AI Tab](#ai-tab)
  - [Chat Tab](#chat-tab)
- [🔧 Configuration Overview](#-configuration-overview)
  - [Logging Level](#logging-configuration)
  - [LLM Providers](#llm-providers)
  - [Advanced Parameters](#advanced-parameters)
  - [🗄️ Data Providers](#️-data-providers)
- [🐛 Troubleshooting](#-troubleshooting)
- [📝 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)
- [📬 Support](#-support)
- [🤝 Contributing](#-contributing)
- [💰 Sponsoring](#-sponsoring)

## �🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (<i>recommended</i>). [poetry](https://python-poetry.org/) or good old [pip](https://pypi.org/project/pip/) for package management
- Optional: [Ollama](https://ollama.com/download), [LM Studio](https://lmstudio.ai/download), or [OpenAI API](https://openai.com/api/) key for AI assistance
- Optional: [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/) for containerized deployment

### 📦 Installation
We recommend always isolating your code within a [virtual environment](https://www.w3schools.com/python/python_virtualenv.asp) and installing the package in it to avoid dependency issues.

#### Using uv
```bash
# Create a virtual enfironment
uv venv

# Activate your virtual environment
source .venv/bin/activate

# Install package version of your choice
uv add docbt                    # For base package with no data platform
uv add "docbt[snowflake]"       # For adding Snowflake provider
uv add "docbt[bigquery]"        # For adding BigQuery provider
uv add "docbt[all-providers]"   # For adding all available data providers
uv add "docbt[dev]"             # For development

# (alternatively) use uv pip
uv pip install docbt

# Verify installation
docbt --version

# Run the application
docbt run
```

<details>
<summary><b>Using Poetry</b></summary>

```bash
# Initialize or navigate to your project
# If you don't have a pyproject.toml yet
poetry init

# Add docbt to your project
poetry add docbt                    # For base package with no data platform
poetry add "docbt[snowflake]"       # For adding Snowflake provider
poetry add "docbt[bigquery]"        # For adding BigQuery provider
poetry add "docbt[all-providers]"   # For adding all available data providers

# Development dependencies (optional)
poetry add --group dev "docbt[dev]"

# Activate the Poetry shell
poetry shell

# Verify installation
docbt --version

# Run the application
docbt run
```
</details>


<details>
<summary><b>Using pip</b></summary>

```bash
# Create virtual environments
python -m venv env

# Activate it
source env/bin/activate

# Install package version of your choice
pip install docbt                    # For base package with no data platform
pip install "docbt[snowflake]"       # For adding Snowflake provider
pip install "docbt[bigquery]"        # For adding BigQuery provider
pip install "docbt[all-providers]"   # For adding all available data providers
pip install "docbt[dev]"             # For development

# Verify installation
docbt --version

# Run the application
docbt run
```
</details>


### 🔧 Building from Source

Building from source gives you access to the latest development features and allows you to contribute to the project. We recommend using [uv](https://docs.astral.sh/uv/) for faster dependency resolution and installation. This is also what we, the developers, use.

<details>
<summary><b>Using uv (Recommended)</b></summary>

```bash
# Clone the repository
git clone https://github.com/aleenprd/docbt.git
cd docbt

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with all dependencies
uv pip install -e .                    # Base installation
uv pip install -e ".[snowflake]"       # With Snowflake support
uv pip install -e ".[bigquery]"        # With BigQuery support
uv pip install -e ".[all-providers]"   # With all data providers
uv pip install -e ".[dev]"             # With development tools

# Verify installation
docbt --version

# Run the application
docbt run
```

</details>

<details>
<summary><b>Using pip</b></summary>

```bash
# Clone the repository
git clone https://github.com/aleenprd/docbt.git
cd docbt

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install in editable mode
pip install -e .                    # Base installation
pip install -e ".[snowflake]"       # With Snowflake support
pip install -e ".[bigquery]"        # With BigQuery support
pip install -e ".[all-providers]"   # With all data providers
pip install -e ".[dev]"             # With development tools

# Verify installation
docbt --version

# Run the application
docbt run
```

</details>

<details>
<summary><b>Using Poetry</b></summary>

```bash
# Clone the repository
git clone https://github.com/aleenprd/docbt.git
cd docbt

# Install dependencies
poetry install

# Install with extras
poetry install --extras "snowflake bigquery"

# Activate the virtual environment
poetry shell

# Run the application
docbt run
```

</details>

<details>
<summary><b>Using Pipenv</b></summary>

```bash
# Clone the repository
git clone https://github.com/aleenprd/docbt.git
cd docbt

# Install dependencies
pipenv install --dev

# Activate the virtual environment
pipenv shell

# Install in editable mode
pip install -e .

# Run the application
docbt run
```

</details>

<details>
<summary><b>Development Setup</b></summary>

For contributors and developers:

```bash
# Clone and navigate to the repository
git clone https://github.com/aleenprd/docbt.git
cd docbt

# Install with development dependencies (using uv)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pre-commit install

# Run tests
make test

# Run linting and formatting
make lint
make format

# Check code quality
ruff check .
ruff format .

# Run specific test files
pytest tests/server/test_server.py -v
```

</details>

<details>
<summary><b>Verifying Your Installation</b></summary>

After building from source, verify everything works:

```bash
# Check version
docbt --version

# View help
docbt help

# Run the server
docbt run

# Run with custom settings
docbt run --port 8080 --log-level DEBUG
```

</details>

<details>
<summary><b>Using Make (Recommended for Contributors)</b></summary>

If you're contributing to the project, using Make provides the easiest setup experience with automated tasks.

**Prerequisites:**
- Make (usually pre-installed on Linux/macOS)
- Git

```bash
# Clone the repository
git clone https://github.com/aleenprd/docbt.git
cd docbt

# Create virtual environment (Make will use uv automatically)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies with one command
make install

# Create .env file from template (keeps section headers, removes comments)
make env

# Edit .env with your credentials
nano .env  # or your preferred editor

# Install pre-commit hooks (optional but recommended)
make pre-commit

# Verify installation by running tests
make test

# Run the application
docbt run
```

**Common Make commands for development:**
```bash
make help          # Show all available commands
make install       # Install dependencies
make env           # Create .env from .env.example
make test          # Run tests
make test-cov      # Run tests with coverage report
make lint          # Check code quality
make format        # Auto-format code
make check         # Run format check + lint
make ci            # Run all CI checks (format, lint, test)
make pre-commit    # Install pre-commit hooks
```

**For detailed information on all Make commands, see [Make Commands Guide](docs/MAKE.md).**

</details>

<details>
<summary><b>Troubleshooting Build Issues</b></summary>

**Missing Build Tools:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev build-essential

# macOS (requires Homebrew)
brew install python@3.10

# Windows (requires Visual Studio Build Tools)
# Download from: https://visualstudio.microsoft.com/downloads/
```

**Dependency Conflicts:**
```bash
# Clear pip cache
pip cache purge

# Or with uv
uv cache clean

# Reinstall from scratch
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

**Permission Issues:**
```bash
# Don't use sudo with pip/uv in virtual environments
# If you get permission errors, ensure you're in an activated venv
source .venv/bin/activate
```

</details>


## 🎯 Usage
[**View live demo app**](https://docbt-demo.streamlit.app/)

![GIF Demo](docs/img/gif-01.gif)

**d<span style="color: #FF8C00;">oc</span>bt** comes equipped with a command line tool which supports the commands:
- **--version**: prints the version of the package.
- **help**: will print very detailed information about commands and options you can use to run the app.
- **run**: run the Streamlit app with the option to specify host, port, log level.

### Data Tab
Provide the app with data to start working with it
- **Upload**: CSV, JSON from your local storage
- **Data Warehouse**: connect to your data platform like Snowflake or BigQuery
- **Context Integration**: Data automatically included in AI conversations
- **Statistics and EDA**: (coming soon)

[![Data Tab](docs/img/data-tab-02.png)](docs/img/data-tab-02.png)

### Node Tab
Here you can set up the configuration for your node
- **Provide specific config**: customize your config with platform-specific properties
- **Configure node properties**: from materialization to meta-tags
- **Apply node-level data tests**: (coming soon)

[![Node Tab](docs/img/node-tab-01.png)](docs/img/node-tab-01.png)

### Columns Tab
Here you can set up the configuration, documentation and tests for your columns

[![Columns Tab](docs/img/columns-tab-01.png)](docs/img/columns-tab-01.png)

### Sidebar and Config Tab
See the end result of your work in real time
- **Preview Configuration**: Interactive visual representation of generated YAML
- **Real-time Updates**: see changes live as you configure your documentation using the UI
- **AI Suggestions**: use LLMs to generate node and column level descriptions, suggest constraints and data tets

[![Sidebar AI Suggestion](docs/img/ai-suggestions-sidebar-01.png)](docs/img/ai-suggestions-sidebar-01.png)

### AI Tab
Configure your AI provider and settings
- **Choose Provider**: OpenAI, Ollama, or LM Studio
- **Developer Mode**: Enable advanced settings and metrics
- **System Prompt**: Customize AI context and behavior (developer mode)
- **Generation Parameters**: Control temperature, max tokens, top-p, stop sequences, etc.

[![AI Tab](docs/img/ai-tab-01.png)](docs/img/ai-tab-01.png)

### Chat Tab
Interact with your AI assistant with in-context data sample
- Ask questions about DBT best practices or your data in general
- Get recommendations for data modeling and data use cases
- Just have whatever type of conversation you want with your model
- Enable "Chain of Thought" to see AI reasoning

[![Chat Tab](docs/img/chat-tab-01.png)](docs/img/chat-tab-01.png)

## 🔧 Configuration Overview
The behavior of the app can be configured through usage of environment variables. You can find an example [environment](.env.example) in the repo. Usage of `make env` (for developers) will also spawn your own `.env` file to work with. Alternatively, copy the `.env.example` contents into `.env` to make use of docbt's [python-dotenv](https://pypi.org/project/python-dotenv/) feature. Or just export the environment variables/inject them into your environment of choice.

### Logging Configuration

Control the verbosity of docbt's logging output to help with debugging or reduce noise in production.

**Setting Log Level:**

You can configure the logging level in two ways:

1. **CLI Flag** (highest priority):
```bash
docbt run --log-level DEBUG
```

2. **Environment Variable** (used if no CLI flag provided):
```bash
# In .env file
DOCBT_LOG_LEVEL=DEBUG

# Or export directly
export DOCBT_LOG_LEVEL=DEBUG
```

**Available Log Levels:**
- `TRACE` - Most verbose, includes all internal details
- `DEBUG` - Detailed debugging information (useful for troubleshooting)
- `INFO` - General informational messages (default)
- `SUCCESS` - Success messages only
- `WARNING` - Warning messages and above
- `ERROR` - Error messages and above
- `CRITICAL` - Only critical errors

**Examples:**
```bash
# Use DEBUG level for troubleshooting
docbt run --log-level DEBUG

# Use environment variable for persistent configuration
echo "DOCBT_LOG_LEVEL=DEBUG" >> .env
docbt run

# Reduce logging noise in production
docbt run --log-level WARNING
```

**Note:** The CLI flag always takes precedence over the environment variable. If neither is specified, the default level is `INFO`.

### LLM Providers

```bash
# Enable/disable AI usage
DOCBT_USE_AI_DEFAULT=false

# Enable/disable developer more for advanced features
DOCBT_DEVELOPER_MODE_ENABLED=true
DOCBT_SHOW_CHAIN_OF_THOUGHT=true

# You can choose which provider will appear as your default
DOCBT_LLM_PROVIDER_DEFAULT=openai/ollama/lmstudio
```
#### OpenAI
We recommend working with gpt-5 series but you can use the `Fetch Models` button to use whatever OpenAI has to offer.
- **gpt-5-nano**: good for most tasks and very cheap - fails to produce valid structured output with large sample size or too many cols
- **gpt-5-mini**: handles itself better than nano, worse at long context than gpt-5. Good middle-ground.
- **gpt-5**: the best of the gpt-5 series but the most expensive. Use sparingly.

```bash
# Set your API key
export DOCBT_OPENAI_API_KEY="sk-..."

# Or add to .env file
DOCBT_OPENAI_API_KEY=sk-...

# Enable it in the UI
DOCBT_DISPLAY_LLM_PROVIDER_OPENAI=true
```

#### Ollama (OSS)
We recomment using models such as:
- [Qwen3 series](https://ollama.com/library/qwen3) especially in the 4B to 14B range

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull qwen3:4b

# Start server (default: http://localhost:11434)
ollama serve

# Set host and port environment variables
DOCBT_OLLAMA_HOST=localhost
DOCBT_OLLAMA_PORT=11434

# Enable it in the UI
DOCBT_DISPLAY_LLM_PROVIDER_OLLAMA=true
```

#### LM Studio (OSS)
Some models we would recommend are:
- [Qwen3-4b-instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) or the 8B/14B variant
- [Qwen3-4b-thinking-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) or the 8B/14B variant
- [Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B) if your GPU permits

**Note**: some models are incapable of producing valid structured outputs. For example, oddly enough, gpt-oss cannot. Experiment and find out what works for your usecase and hardware. Increasing context window in LM-Studio can troubleshoot bugs, especially with data that has lots of columns.

1. Download from [lmstudio.ai](https://lmstudio.ai/)
2. Browse models and download the ones you want
3. Enable "Local Server" (default: http://localhost:1234) from UI

```bash
# Set host and port environment variables
DOCBT_LMSTUDIO_HOST=localhost
DOCBT_LMSTUDIO_PORT=1234

# Enable it in the UI
DOCBT_DISPLAY_LLM_PROVIDER_LMSTUDIO=true
```

### Advanced Parameters
In Developer Mode, fine-tune AI generation with [inference parameters](https://medium.com/@rafaelcostadealmeida159/llm-inference-understanding-how-models-generate-responses-until-we-force-hallucination-and-how-836d12a5592e)

- **API Timeout**: amount of seconds until API call fails
- **Max Tokens**: Maximum response length (100-4000)
- **Temperature**: Creativity level (0.0-2.0)
   - `0.0`: Deterministic, focused
   - `1.0`: Balanced
   - `2.0`: More creative, random
- **Top P**: Nucleus sampling (0.0-1.0)
- **Stop Sequences**: Custom stop words/phrases

**Note**: gpt-5 series does not support temperature (always 1), top-p and stop sequences.

### 🗄️ Data Providers
You can use different connection methods to connect to the following data

#### Snowflake
[Connect](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect) to Snowflake by means of with password, SSO, MFA or with RSA key.

```bash
# Example: connect with your user and password
DOCBT_SNOWFLAKE_ACCOUNT=your-account-id
DOCBT_SNOWFLAKE_USER=your-username
DOCBT_SNOWFLAKE_PASSWORD=your-password
DOCBT_SNOWFLAKE_WAREHOUSE=your-warehouse
DOCBT_SNOWFLAKE_DATABASE=your-database
DOCBT_SNOWFLAKE_SCHEMA=PUBLIC
DOCBT_SNOWFLAKE_AUTHENTICATOR=snowflake
```


#### BigQuery
Currently, the BigQuery connection only works with credentials JSON method:
- Install [cloud dk](https://cloud.google.com/sdk/docs/install-sdk)
- [Authenticate](https://googleapis.dev/python/google-api-core/latest/auth.html) with JSON credentials

```bash
# Point to your credentials JSON in the environment variables
DOCBT_GOOGLE_APPLICATION_CREDENTIALS=/home/<user>/.config/gcloud/application_default_credentials.json
```

## 🐛 Troubleshooting

### Common Issues

**Streamlit App/General Issues**
Run docbt with debug log level and inspect the logs. If you find any bugs while doing so, please report them. :)

```bash
docbt run --log-level debug
```

**LLM Connection Errors**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Verify LM Studio server
curl http://localhost:1234/v1/models

# Test OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**Docker Issues**
```bash
# View container logs
docker-compose logs docbt

# Check if container is running
docker ps

# Restart container
docker-compose restart docbt
```

See [Docker Guide](docs/DOCKER.md) for more Docker-specific troubleshooting.

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- Inspired by the [DBT](https://www.getdbt.com/) community
- Built with [Streamlit](https://streamlit.io/)
- AI via [OpenAI](https://openai.com/), [Ollama](https://ollama.ai/), and [LM Studio](https://lmstudio.ai/)
- Data via [Snowflake](https://www.snowflake.com/en/), [BigQuery](https://cloud.google.com/bigquery?hl=en)

## 📬 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/docdt/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/docdt/discussions)
- 📧 **Email**: [predaalin2694@gmail.com](mailto:predaalin2694@gmail.com)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

**Quick Start:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run `ruff format .` and `pytest`
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

**CI/CD:** All pull requests are automatically tested with our CI pipeline. See [CI/CD Documentation](docs/CICD.md) for details.

**Development Tools:** We use Make for automation. See [Make Commands Guide](docs/MAKE.md) for all available commands.

## 💰 Sponsoring
If you like what I'm working on and decide to sponsor you can do so via:
- [PayPal](https://paypal.me/aleenprd?country.x=DK&locale.x=en_US)
- [Buy me a coffee](https://www.buymeacoffee.com/cristianali)

---

**Happy documenting!** 🎉 Generate better DBT documentation with AI assistance.
