"""Logging utilities using Rich for beautiful console output."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

# Custom theme for consistent styling
custom_theme = Theme(
    {
        "info": "blue",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "header": "magenta bold",
    }
)

console = Console(theme=custom_theme)
error_console = Console(theme=custom_theme, stderr=True)


@dataclass
class OutputBuffer:
    """Collects structured output for JSON mode."""

    events: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] | None = None

    def add_event(self, level: str, message: str, **extra: Any) -> None:
        """Add an event to the buffer."""
        event = {"level": level, "message": message, **extra}
        self.events.append(event)

    def set_result(self, data: dict[str, Any]) -> None:
        """Set the final result data."""
        self.result = data

    def to_dict(self) -> dict[str, Any]:
        """Convert buffer to dictionary."""
        output: dict[str, Any] = {"events": self.events}
        if self.result is not None:
            output["result"] = self.result
        return output

    def to_json(self, indent: int | None = 2) -> str:
        """Convert buffer to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class Logger:
    """Structured logging with Rich formatting and JSON output support."""

    def __init__(
        self,
        console: Console | None = None,
        json_mode: bool = False,
    ):
        """Initialize the logger.

        Args:
            console: Rich console for output.
            json_mode: If True, collect output for JSON instead of printing.
        """
        self._console = console or Console(theme=custom_theme)
        self._error_console = Console(theme=custom_theme, stderr=True)
        self._json_mode = json_mode
        self._buffer = OutputBuffer()

    @property
    def json_mode(self) -> bool:
        """Whether JSON output mode is enabled."""
        return self._json_mode

    @json_mode.setter
    def json_mode(self, value: bool) -> None:
        """Set JSON output mode."""
        self._json_mode = value
        if value:
            self._buffer = OutputBuffer()

    def info(self, message: str, **extra: Any) -> None:
        """Log an informational message."""
        if self._json_mode:
            self._buffer.add_event("info", message, **extra)
        else:
            self._console.print(f"[info][INFO][/info] {message}")

    def success(self, message: str, **extra: Any) -> None:
        """Log a success message."""
        if self._json_mode:
            self._buffer.add_event("success", message, **extra)
        else:
            self._console.print(f"[success][SUCCESS][/success] {message}")

    def warn(self, message: str, **extra: Any) -> None:
        """Log a warning message."""
        if self._json_mode:
            self._buffer.add_event("warning", message, **extra)
        else:
            self._console.print(f"[warning][WARN][/warning] {message}")

    def error(self, message: str, **extra: Any) -> None:
        """Log an error message."""
        if self._json_mode:
            self._buffer.add_event("error", message, **extra)
        else:
            self._error_console.print(f"[error][ERROR][/error] {message}")

    def header(self, title: str) -> None:
        """Display a section header."""
        if self._json_mode:
            self._buffer.add_event("header", title)
        else:
            self._console.print()
            self._console.print(Panel(title, style="header", expand=False))
            self._console.print()

    def step(self, step_num: int, total: int, message: str) -> None:
        """Log a numbered step in a process."""
        if self._json_mode:
            self._buffer.add_event("step", message, step=step_num, total=total)
        else:
            self._console.print(f"[info][{step_num}/{total}][/info] {message}")

    def bullet(self, message: str, indent: int = 2) -> None:
        """Log a bullet point item."""
        if self._json_mode:
            self._buffer.add_event("detail", message)
        else:
            padding = " " * indent
            self._console.print(f"{padding}• {message}")

    def set_result(self, data: dict[str, Any]) -> None:
        """Set structured result data (only used in JSON mode)."""
        self._buffer.set_result(data)

    def flush_json(self) -> None:
        """Flush JSON output to stdout (only in JSON mode)."""
        if self._json_mode:
            print(self._buffer.to_json())
            self._buffer = OutputBuffer()

    def get_buffer(self) -> OutputBuffer:
        """Get the current output buffer."""
        return self._buffer


def print_json(data: Any, indent: int | None = 2) -> None:
    """Print data as formatted JSON to stdout.

    Args:
        data: Data to serialize to JSON.
        indent: Indentation level (None for compact).
    """
    if hasattr(data, "model_dump"):
        # Pydantic model
        data = data.model_dump()
    elif hasattr(data, "__dict__"):
        data = data.__dict__

    print(json.dumps(data, indent=indent, default=str))


# Global logger instance
log = Logger(console)
