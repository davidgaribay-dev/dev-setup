"""Application context for dependency injection via Typer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from harness.core.config import Config
from harness.core.logger import Logger, log

if TYPE_CHECKING:
    pass


@dataclass
class AppContext:
    """Shared application context passed through Typer commands.

    This context holds shared state and dependencies that commands need,
    avoiding global state and enabling easier testing.
    """

    config: Config
    logger: Logger = field(default_factory=lambda: log)
    verbose: bool = False
    json_output: bool = False

    def __post_init__(self) -> None:
        """Configure logger based on context settings."""
        self.logger.json_mode = self.json_output

    @classmethod
    def create(
        cls,
        verbose: bool = False,
        json_output: bool = False,
    ) -> AppContext:
        """Create a new application context.

        Args:
            verbose: Enable verbose output.
            json_output: Enable JSON output mode.

        Returns:
            Configured AppContext instance.
        """
        config = Config.from_yaml()
        logger = Logger(json_mode=json_output)

        return cls(
            config=config,
            logger=logger,
            verbose=verbose,
            json_output=json_output,
        )
