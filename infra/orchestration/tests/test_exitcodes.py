"""Tests for exit codes and CLI exceptions."""

from __future__ import annotations

import pytest

from harness.core.exitcodes import (
    CLIError,
    ConfigurationError,
    DataError,
    ExitCode,
    PermissionError,
    ServiceUnavailableError,
    TemporaryError,
    UsageError,
)


class TestExitCode:
    """Tests for ExitCode enum."""

    def test_success_is_zero(self) -> None:
        """Success should be 0."""
        assert ExitCode.SUCCESS == 0

    def test_failure_is_one(self) -> None:
        """General failure should be 1."""
        assert ExitCode.FAILURE == 1

    def test_config_is_78(self) -> None:
        """Config error should be 78 (EX_CONFIG)."""
        assert ExitCode.CONFIG == 78

    def test_usage_is_64(self) -> None:
        """Usage error should be 64 (EX_USAGE)."""
        assert ExitCode.USAGE == 64

    def test_exit_codes_are_in_valid_range(self) -> None:
        """All exit codes should be in valid range (0-255)."""
        for code in ExitCode:
            assert 0 <= code <= 255


class TestCLIError:
    """Tests for CLI exception classes."""

    def test_cli_error_default_exit_code(self) -> None:
        """CLIError should default to FAILURE."""
        error = CLIError("Something went wrong")

        assert error.exit_code == ExitCode.FAILURE
        assert str(error) == "Something went wrong"

    def test_cli_error_custom_exit_code(self) -> None:
        """CLIError should accept custom exit code."""
        error = CLIError("Config issue", exit_code=ExitCode.CONFIG)

        assert error.exit_code == ExitCode.CONFIG

    def test_configuration_error_exit_code(self) -> None:
        """ConfigurationError should have CONFIG exit code."""
        error = ConfigurationError("Invalid config")

        assert error.exit_code == ExitCode.CONFIG

    def test_usage_error_exit_code(self) -> None:
        """UsageError should have USAGE exit code."""
        error = UsageError("Invalid argument")

        assert error.exit_code == ExitCode.USAGE

    def test_data_error_exit_code(self) -> None:
        """DataError should have DATA_ERROR exit code."""
        error = DataError("Invalid data format")

        assert error.exit_code == ExitCode.DATA_ERROR

    def test_service_unavailable_error_exit_code(self) -> None:
        """ServiceUnavailableError should have UNAVAILABLE exit code."""
        error = ServiceUnavailableError("Service down")

        assert error.exit_code == ExitCode.UNAVAILABLE

    def test_permission_error_exit_code(self) -> None:
        """PermissionError should have NO_PERMISSION exit code."""
        error = PermissionError("Access denied")

        assert error.exit_code == ExitCode.NO_PERMISSION

    def test_temporary_error_exit_code(self) -> None:
        """TemporaryError should have TEMP_FAILURE exit code."""
        error = TemporaryError("Try again later")

        assert error.exit_code == ExitCode.TEMP_FAILURE

    def test_exceptions_are_catchable_as_cli_error(self) -> None:
        """All custom exceptions should be catchable as CLIError."""
        exceptions = [
            ConfigurationError("test"),
            UsageError("test"),
            DataError("test"),
            ServiceUnavailableError("test"),
            PermissionError("test"),
            TemporaryError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, CLIError)
