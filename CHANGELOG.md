# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.8] - 2025-11-12
- Fixed bug where YAML would generate arguments keyword for data tests.

## [0.1.7] - 2025-11-11
- Optimizing json format to work with all providers seamlessly.

## [0.1.6] - 2025-11-11
- Reintroduce caching of Snowflake tables while fixing metadata bug and latency due to re-calling function.

## [0.1.5] - 2025-11-11
- Fixed bug in Snowflake conn where it didn't fetch tables properly

## [0.1.4] - 2025-10-21

## [0.1.3] - 2025-10-21

- Initial release of docbt
- Multi-LLM support (OpenAI, Ollama, LM Studio)
- Interactive chat interface with Streamlit
- Data upload and analysis capabilities
- DBT documentation generation
- Developer mode with advanced settings
- Token usage monitoring
- Chain of Thought reasoning display
- Docker support with multi-stage builds
- Snowflake and BigQuery connectors (optional)
- CI/CD pipeline with GitHub Actions
- Automated testing with pytest on pull requests
- Code quality checks with Ruff
- Docker image builds on pull requests
- Manual release workflow for PyPI and Docker registries
