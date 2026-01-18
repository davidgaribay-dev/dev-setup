"""POSIX-compliant exit codes for CLI operations.

Based on BSD sysexits.h conventions (range 64-78 for custom exit codes).
See: https://man.freebsd.org/cgi/man.cgi?query=sysexits
"""

from enum import IntEnum


class ExitCode(IntEnum):
    """Standard exit codes following POSIX/BSD conventions."""

    # Success
    SUCCESS = 0

    # General failure
    FAILURE = 1

    # Command line usage error (bad arguments, flags, etc.)
    USAGE = 64  # EX_USAGE

    # Data format error (invalid input data)
    DATA_ERROR = 65  # EX_DATAERR

    # Cannot open input file
    NO_INPUT = 66  # EX_NOINPUT

    # Service unavailable
    UNAVAILABLE = 69  # EX_UNAVAILABLE

    # Internal software error
    SOFTWARE = 70  # EX_SOFTWARE

    # System error (fork failed, etc.)
    OS_ERROR = 71  # EX_OSERR

    # Cannot create output file
    CANT_CREATE = 73  # EX_CANTCREAT

    # I/O error
    IO_ERROR = 74  # EX_IOERR

    # Temporary failure, user is invited to retry
    TEMP_FAILURE = 75  # EX_TEMPFAIL

    # Permission denied
    NO_PERMISSION = 77  # EX_NOPERM

    # Configuration error
    CONFIG = 78  # EX_CONFIG


class CLIError(Exception):
    """Base exception for CLI errors with associated exit code."""

    exit_code: ExitCode = ExitCode.FAILURE

    def __init__(self, message: str, exit_code: ExitCode | None = None):
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class ConfigurationError(CLIError):
    """Configuration-related errors."""

    exit_code = ExitCode.CONFIG


class UsageError(CLIError):
    """Command line usage errors."""

    exit_code = ExitCode.USAGE


class DataError(CLIError):
    """Invalid input data errors."""

    exit_code = ExitCode.DATA_ERROR


class ServiceUnavailableError(CLIError):
    """External service unavailable errors."""

    exit_code = ExitCode.UNAVAILABLE


class PermissionError(CLIError):
    """Permission denied errors."""

    exit_code = ExitCode.NO_PERMISSION


class TemporaryError(CLIError):
    """Temporary failure, retry may succeed."""

    exit_code = ExitCode.TEMP_FAILURE
