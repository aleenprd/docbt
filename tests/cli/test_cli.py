"""Tests for the docbt CLI."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from docbt.cli.docbt_cli import cli


@pytest.fixture
def runner():
    """Provide a CLI test runner."""
    return CliRunner()


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test that --help flag works."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Commands:" in result.output

    def test_cli_version(self, runner):
        """Test that --version flag works."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_cli_no_args_shows_help(self, runner):
        """Test that running CLI without args shows help."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Commands:" in result.output
        assert "docbt version:" in result.output

    def test_cli_shows_logo(self, runner):
        """Test that CLI shows ASCII logo."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "docbt" in result.output  # Logo should contain "docbt"

    def test_help_command(self, runner):
        """Test the help command."""
        result = runner.invoke(cli, ["help"])
        assert result.exit_code == 0
        assert "Commands:" in result.output


class TestRunCommand:
    """Test the run command."""

    def test_run_help(self, runner):
        """Test run command help."""
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Launch the docbt interactive web interface" in result.output
        assert "--port" in result.output
        assert "--host" in result.output
        assert "--log-level" in result.output

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_default_options(self, mock_subprocess, runner):
        """Test run command with default options."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run"])

        # Check subprocess was called
        assert mock_subprocess.called
        call_args = mock_subprocess.call_args

        # Verify streamlit command was constructed correctly
        cmd = call_args[0][0]
        assert sys.executable in cmd
        assert "-m" in cmd
        assert "streamlit" in cmd
        assert "run" in cmd
        assert "--server.port=8501" in cmd
        assert "--server.address=localhost" in cmd

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_custom_port(self, mock_subprocess, runner):
        """Test run command with custom port."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "--port", "9000"])

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert "--server.port=9000" in cmd

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_custom_host(self, mock_subprocess, runner):
        """Test run command with custom host."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "--host", "0.0.0.0"])

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert "--server.address=0.0.0.0" in cmd

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_custom_log_level(self, mock_subprocess, runner):
        """Test run command with custom log level."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "--log-level", "DEBUG"])

        # Command should succeed
        assert mock_subprocess.called

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_all_custom_options(self, mock_subprocess, runner):
        """Test run command with all custom options."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "--port", "9000", "--host", "0.0.0.0", "--log-level", "ERROR"])

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert "--server.port=9000" in cmd
        assert "--server.address=0.0.0.0" in cmd

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_short_options(self, mock_subprocess, runner):
        """Test run command with short option flags."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "-p", "8080", "-h", "127.0.0.1", "-l", "WARNING"])

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert "--server.port=8080" in cmd
        assert "--server.address=127.0.0.1" in cmd

    def test_run_invalid_log_level(self, runner):
        """Test run command with invalid log level."""
        result = runner.invoke(cli, ["run", "--log-level", "INVALID"])

        # Click should reject invalid choice
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid choice" in result.output.lower()

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_subprocess_error(self, mock_subprocess, runner):
        """Test run command when subprocess fails."""
        from subprocess import CalledProcessError

        mock_subprocess.side_effect = CalledProcessError(1, "streamlit")

        result = runner.invoke(cli, ["run"])

        # Command should handle the error
        assert "Error" in result.output or "Failed" in result.output


class TestCLIValidLogLevels:
    """Test all valid log levels."""

    @pytest.mark.parametrize(
        "log_level",
        ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
    )
    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_valid_log_levels(self, mock_subprocess, runner, log_level):
        """Test that all valid log levels are accepted."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "--log-level", log_level])

        assert mock_subprocess.called

    @pytest.mark.parametrize(
        "log_level",
        ["trace", "debug", "info", "success", "warning", "error", "critical"],
    )
    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_case_insensitive_log_levels(self, mock_subprocess, runner, log_level):
        """Test that log levels are case-insensitive."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "--log-level", log_level])

        assert mock_subprocess.called


class TestCLIEdgeCases:
    """Test edge cases and error conditions."""

    def test_unknown_command(self, runner):
        """Test that unknown commands are rejected."""
        result = runner.invoke(cli, ["unknown-command"])

        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_with_invalid_port_type(self, mock_subprocess, runner):
        """Test run command with invalid port type."""
        result = runner.invoke(cli, ["run", "--port", "not-a-number"])

        # Click should reject invalid integer
        assert result.exit_code != 0

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_with_negative_port(self, mock_subprocess, runner):
        """Test run command with negative port number."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Click allows negative integers, but streamlit will fail
        runner.invoke(cli, ["run", "--port", "-1"])

        # Command should still be constructed (streamlit will handle validation)
        assert mock_subprocess.called

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_run_with_very_large_port(self, mock_subprocess, runner):
        """Test run command with very large port number."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run", "--port", "999999"])

        # Command should still be constructed (streamlit will handle validation)
        assert mock_subprocess.called


class TestCLIIntegration:
    """Integration tests for CLI."""

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_full_command_chain(self, mock_subprocess, runner):
        """Test a full command execution chain."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Test version
        version_result = runner.invoke(cli, ["--version"])
        assert version_result.exit_code == 0

        # Test help
        help_result = runner.invoke(cli, ["--help"])
        assert help_result.exit_code == 0

        # Test run with all options
        runner.invoke(
            cli,
            [
                "run",
                "--port",
                "8888",
                "--host",
                "0.0.0.0",
                "--log-level",
                "DEBUG",
            ],
        )

        assert mock_subprocess.called
        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]
        assert "--server.port=8888" in cmd
        assert "--server.address=0.0.0.0" in cmd

    @patch("docbt.cli.docbt_cli.subprocess.run")
    def test_streamlit_path_construction(self, mock_subprocess, runner):
        """Test that the streamlit server path is constructed correctly."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        runner.invoke(cli, ["run"])

        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]

        # Find the server.py path in the command
        server_py_found = any("server.py" in arg for arg in cmd)
        assert server_py_found, "server.py should be in the streamlit command"

        # Verify it's in the correct directory structure
        server_path = next((arg for arg in cmd if "server.py" in arg), None)
        assert "server" in server_path
        assert "server.py" in server_path
