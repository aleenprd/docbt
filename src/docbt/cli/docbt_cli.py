import os
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

import click
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file (if present)
load_dotenv()

NAME = "docbt"
ASCII_LOGO = r"""
     .___           ___.    __
  __| _/____   ____\_ |___/  |_
 / __ |/  _ \_/ ___\| __ \   __\
/ /_/ (  <_> )  \___| \_\ \  |
\____ |\____/ \___  >___  /__|
      \/           \/    \/
"""


# Try to get version from package metadata first, then fallback to __init__.py
try:
    __version__ = version(NAME)
except PackageNotFoundError:
    try:
        from docbt import __version__
    except ImportError:
        __version__ = "unknown"


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name=NAME)
@click.pass_context
def cli(ctx):
    """
    docbt - Generate dbt configuration files with AI assistance.

    A tool for creating YAML-formatted dbt configuration files with AI-powered
    documentation and test suggestions. Supports multiple data sources and LLM providers.

    Use 'docbt help' for detailed information and examples.
    Use 'docbt run' to start the interactive web interface.
    """
    click.echo(click.style(f"{ASCII_LOGO}\n", fg="cyan"))
    if __version__ != "unknown":
        click.echo(click.style(f"docbt version: {__version__}\n", fg="green"))
    else:
        click.echo(click.style(f"docbt version: {__version__}\n", fg="red"))
    if ctx.invoked_subcommand is None:
        click.echo(cli.get_help(ctx))


@cli.command("help")
def help_command():
    """Show detailed help information and usage examples."""
    ctx = click.Context(cli)

    # Show standard help first
    click.echo(cli.get_help(ctx))

    # Add detailed information
    click.echo("\n" + "=" * 70)
    click.echo(click.style("\n📚 DETAILED INFORMATION\n", fg="cyan", bold=True))

    # About section
    click.echo(click.style("About docbt:", fg="yellow", bold=True))
    click.echo("  docbt is a tool for generating dbt (data build tool) configuration")
    click.echo("  files with AI-powered documentation and testing suggestions.\n")

    # Commands section
    click.echo(click.style("Available Commands:", fg="yellow", bold=True))
    click.echo("  • run      - Launch the interactive Streamlit web interface")
    click.echo("  • help     - Display this detailed help information")
    click.echo("  • --version - Show the installed version of docbt\n")

    # Run command details
    click.echo(click.style("Run Command Options:", fg="yellow", bold=True))
    click.echo("  --port, -p <number>")
    click.echo("      Port number for the web server (default: 8501)")
    click.echo("      Example: docbt run --port 8080\n")

    click.echo("  --host, -h <address>")
    click.echo("      Host address to bind the server (default: localhost)")
    click.echo("      Use '0.0.0.0' to make it accessible from other machines")
    click.echo("      Example: docbt run --host 0.0.0.0\n")

    click.echo("  --log-level, -l <level>")
    click.echo("      Set logging verbosity. Available levels:")
    click.echo("        • TRACE    - Most verbose, includes all details")
    click.echo("        • DEBUG    - Detailed debugging information")
    click.echo("        • INFO     - General informational messages (default)")
    click.echo("        • SUCCESS  - Success messages only")
    click.echo("        • WARNING  - Warning messages and above")
    click.echo("        • ERROR    - Error messages and above")
    click.echo("        • CRITICAL - Only critical errors")
    click.echo("      Example: docbt run --log-level DEBUG\n")

    # Usage examples
    click.echo(click.style("📖 Usage Examples:", fg="yellow", bold=True))
    click.echo("  1. Start with default settings:")
    click.echo("     $ docbt run\n")

    click.echo("  2. Run on a custom port:")
    click.echo("     $ docbt run --port 8080\n")

    click.echo("  3. Make server accessible on network:")
    click.echo("     $ docbt run --host 0.0.0.0 --port 8501\n")

    click.echo("  4. Enable debug logging for troubleshooting:")
    click.echo("     $ docbt run --log-level DEBUG\n")

    click.echo("  5. Combine multiple options:")
    click.echo("     $ docbt run -h 0.0.0.0 -p 8080 -l DEBUG\n")

    # Environment variables
    click.echo(click.style("🔧 Environment Variables:", fg="yellow", bold=True))
    click.echo("  docbt can be configured using environment variables:")
    click.echo("  • DOCBT_USE_AI_DEFAULT          - Enable AI by default (True/False)")
    click.echo("  • DOCBT_LLM_PROVIDER_DEFAULT    - Default LLM provider (lmstudio/ollama/openai)")
    click.echo("  • DOCBT_OPENAI_API_KEY          - OpenAI API key for OpenAI provider")
    click.echo("  • DOCBT_OLLAMA_HOST             - Ollama server host (default: localhost)")
    click.echo("  • DOCBT_OLLAMA_PORT             - Ollama server port (default: 11434)")
    click.echo("  • DOCBT_LMSTUDIO_HOST           - LM Studio server host (default: localhost)")
    click.echo("  • DOCBT_LMSTUDIO_PORT           - LM Studio server port (default: 1234)")
    click.echo(
        "  • DOCBT_DATA_SOURCE_DEFAULT     - Default data source (filesystem/snowflake/bigquery)"
    )
    click.echo("  • DEVELOPER_MODE_ENABLED        - Enable developer mode (True/False)\n")

    # Features
    click.echo(click.style("✨ Key Features:", fg="yellow", bold=True))
    click.echo("  • Generate dbt YAML configuration files")
    click.echo("  • AI-powered table and column descriptions")
    click.echo("  • Automated test and constraint suggestions")
    click.echo("  • Support for multiple data sources (CSV, JSON, Snowflake, BigQuery)")
    click.echo("  • Interactive chat with your data")
    click.echo("  • Multiple LLM provider support (OpenAI, Ollama, LM Studio)\n")

    # Getting started
    click.echo(click.style("🚀 Getting Started:", fg="yellow", bold=True))
    click.echo("  1. Run 'docbt run' to start the web interface")
    click.echo("  2. Configure your LLM provider in the Setup tab")
    click.echo("  3. Upload or connect to your data source")
    click.echo("  4. Generate dbt configuration with AI assistance")
    click.echo("  5. Export your YAML configuration file\n")

    # Support
    click.echo(click.style("📞 Support & Documentation:", fg="yellow", bold=True))
    click.echo("  • GitHub: https://github.com/aleenprd/docbt")
    click.echo("  • Issues: https://github.com/aleenprd/docbt/issues")
    click.echo("  • Documentation: Check the docs/ folder in the repository\n")

    click.echo("=" * 70 + "\n")


@cli.command("run")
@click.option(
    "--port",
    "-p",
    type=int,
    default=8501,
    help="Port to run the server on (default: 8501)",
)
@click.option(
    "--host",
    "-h",
    type=str,
    default="localhost",
    help="Host to bind the server to (default: localhost)",
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=False,
    ),
    default=lambda: os.getenv("DOCBT_LOG_LEVEL", "INFO"),
    help="Set the logging level (default: INFO, or DOCBT_LOG_LEVEL env var)",
)
def run_streamlit_server(port: int, host: str, log_level: str):
    """
    Launch the docbt interactive web interface.

    Starts a Streamlit-based web server where you can:
    - Upload or connect to data sources (CSV, JSON, Snowflake, BigQuery)
    - Configure AI/LLM providers (OpenAI, Ollama, LM Studio)
    - Generate dbt YAML configuration with AI-powered suggestions
    - Chat with your data using natural language
    - Export configuration files for your dbt project

    Examples:
      docbt run                              # Start with defaults
      docbt run --port 8080                  # Use custom port
      docbt run --host 0.0.0.0               # Allow network access
      docbt run --log-level DEBUG            # Enable debug logging
      docbt run -h 0.0.0.0 -p 8080 -l DEBUG  # Combine options
    """
    # Use environment variable if CLI flag not explicitly set to default
    # Priority: CLI flag > Environment variable > Default (INFO)
    final_log_level = log_level.upper()

    # Configure logging level
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level=final_log_level)

    logger.info(f"Logging level set to: {final_log_level}")
    click.echo(f"Spawning Streamlit server at {host}:{port}")

    # Pass log level to server via environment variable
    env = os.environ.copy()
    env["DOCBT_LOG_LEVEL"] = final_log_level

    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        os.path.join(os.path.dirname(__file__), "..", "server", "server.py"),
        f"--server.port={port}",
        f"--server.address={host}",
    ]

    logger.debug(f"Starting Streamlit server with command: {' '.join(streamlit_cmd)}")

    try:
        result = subprocess.run(streamlit_cmd, check=True, env=env)
        logger.info(f"Streamlit server started successfully with return code: {result.returncode}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit server: {e}")
        click.echo(f"Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"Unexpected error: {e}")


if __name__ == "__main__":
    cli()
