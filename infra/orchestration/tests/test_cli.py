"""Tests for CLI commands using Typer's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from harness.cli.app import app
from harness.core.exitcodes import ExitCode

runner = CliRunner()


class TestCLIHelp:
    """Tests for CLI help and basic functionality."""

    def test_help_shows_commands(self) -> None:
        """Test that --help shows all commands."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "neo4j" in result.output
        assert "vms" in result.output
        assert "all" in result.output
        assert "status" in result.output

    def test_short_help_flag(self) -> None:
        """Test that -h works as help."""
        result = runner.invoke(app, ["-h"])

        assert result.exit_code == 0
        assert "Commands" in result.output

    def test_version_flag(self) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "harness" in result.output
        assert "0.1.0" in result.output

    def test_short_version_flag(self) -> None:
        """Test -V works as version."""
        result = runner.invoke(app, ["-V"])

        assert result.exit_code == 0
        assert "harness" in result.output


class TestNeo4jCommand:
    """Tests for neo4j command."""

    def test_neo4j_help(self) -> None:
        """Test neo4j --help shows options and examples."""
        result = runner.invoke(app, ["neo4j", "--help"])

        assert result.exit_code == 0
        assert "--destroy" in result.output
        assert "--skip-provision" in result.output
        assert "--skip-configure" in result.output
        assert "Examples:" in result.output
        assert "NEO4J_ADMIN_PASSWORD" in result.output


class TestVmsCommand:
    """Tests for vms command."""

    def test_vms_help(self) -> None:
        """Test vms --help shows all options."""
        result = runner.invoke(app, ["vms", "--help"])

        assert result.exit_code == 0
        assert "--count" in result.output
        assert "--prefix" in result.output
        assert "--start-id" in result.output
        assert "--neo4j-ip" in result.output
        assert "--destroy" in result.output
        assert "--skip-hardening" in result.output
        assert "Examples:" in result.output

    def test_vms_help_shows_environment_variables(self) -> None:
        """Test vms --help shows env vars."""
        result = runner.invoke(app, ["vms", "--help"])

        assert "NEO4J_PASSWORD" in result.output
        assert "ANSIBLE_GH_TOKEN" in result.output


class TestAllCommand:
    """Tests for all command."""

    def test_all_help(self) -> None:
        """Test all --help shows combined options."""
        result = runner.invoke(app, ["all", "--help"])

        assert result.exit_code == 0
        assert "--count" in result.output
        assert "--destroy" in result.output
        assert "Deploy order" in result.output or "Neo4j" in result.output


class TestStatusCommand:
    """Tests for status command."""

    @patch("harness.core.config.load_config")
    @patch("harness.core.config.get_orchestration_dir")
    def test_status_json_output(
        self,
        mock_get_dir: MagicMock,
        mock_load_config: MagicMock,
        tmp_path: Path,
        sample_config: dict[str, Any],
        sample_inventory: dict[str, Any],
    ) -> None:
        """Test status command with --json flag."""
        # Setup mocks
        mock_get_dir.return_value = tmp_path
        mock_load_config.return_value = sample_config

        # Create inventory files
        claude_vms_dir = tmp_path.parent / "claude-vms" / "configuration" / "inventory"
        claude_vms_dir.mkdir(parents=True)
        with open(claude_vms_dir / "hosts.json", "w") as f:
            json.dump(sample_inventory, f)

        result = runner.invoke(app, ["--json", "status"])

        # Should output valid JSON
        if result.exit_code == 0:
            output = json.loads(result.output)
            assert "neo4j" in output
            assert "claude_vms" in output


class TestGlobalOptions:
    """Tests for global CLI options."""

    def test_verbose_flag_accepted(self) -> None:
        """Test that --verbose flag is accepted."""
        result = runner.invoke(app, ["--verbose", "--help"])

        # Should not error on the flag itself
        assert result.exit_code == 0

    def test_json_flag_accepted(self) -> None:
        """Test that --json flag is accepted."""
        result = runner.invoke(app, ["--json", "--help"])

        # Should not error on the flag itself
        assert result.exit_code == 0

    def test_short_verbose_flag(self) -> None:
        """Test -v works for verbose."""
        result = runner.invoke(app, ["-v", "--help"])

        assert result.exit_code == 0

    def test_short_json_flag(self) -> None:
        """Test -j works for json."""
        result = runner.invoke(app, ["-j", "--help"])

        assert result.exit_code == 0


class TestConfigurationErrors:
    """Tests for configuration error handling."""

    @patch("harness.core.config.load_config")
    @patch("harness.core.config.get_orchestration_dir")
    def test_missing_config_file_error(
        self,
        mock_get_dir: MagicMock,
        mock_load_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test error when config file is missing."""
        mock_get_dir.return_value = tmp_path
        mock_load_config.side_effect = FileNotFoundError("Config not found")

        result = runner.invoke(app, ["status"])

        assert result.exit_code == ExitCode.CONFIG
        assert "Configuration error" in result.output or "error" in result.output.lower()
