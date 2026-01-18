#!/usr/bin/env python3
"""Claude Code Harness CLI entry point."""

import sys
from pathlib import Path

# Add the orchestration directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from harness.cli import app

if __name__ == "__main__":
    app()
