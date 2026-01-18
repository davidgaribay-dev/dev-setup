#!/usr/bin/env python3
"""
Rewind Viewer - Claude Code Hook

This hook runs on the Stop event to ingest Claude Code conversation data
into the Rewind API/Neo4j database.

Features:
- Pure Python 3 stdlib (no external dependencies)
- State tracking to avoid duplicate message ingestion
- Incremental processing (only new lines since last run)
- Never blocks Claude Code (returns 0 on any error)

Environment Variables:
- REWIND_API_URL: API endpoint (default: http://localhost:8429)
- REWIND_HOOK_ENABLED: Enable/disable hook (default: true)
- REWIND_HOOK_DEBUG: Enable debug logging (default: false)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

# Configuration
API_URL = os.environ.get("REWIND_API_URL", "http://localhost:8429")
HOOK_ENABLED = os.environ.get("REWIND_HOOK_ENABLED", "true").lower() == "true"
DEBUG = os.environ.get("REWIND_HOOK_DEBUG", "false").lower() == "true"

# State file location
STATE_DIR = Path.home() / ".claude" / "state" / "rewind"
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = STATE_DIR / "hook.log"


def log(message: str, level: str = "INFO") -> None:
    """Log message to file."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception:
        pass  # Never fail on logging


def debug(message: str) -> None:
    """Log debug message if debug mode is enabled."""
    if DEBUG:
        log(message, "DEBUG")


def load_state() -> dict[str, Any]:
    """Load state from file."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
    except Exception as e:
        debug(f"Failed to load state: {e}")
    return {"processed_lines": {}}


def save_state(state: dict[str, Any]) -> None:
    """Save state to file."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        debug(f"Failed to save state: {e}")


def read_transcript(transcript_path: str, start_line: int = 0) -> list[dict[str, Any]]:
    """Read transcript JSONL file from given line number."""
    messages = []
    try:
        with open(transcript_path) as f:
            for i, line in enumerate(f):
                if i < start_line:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except json.JSONDecodeError as e:
                    debug(f"Failed to parse line {i}: {e}")
    except Exception as e:
        log(f"Failed to read transcript: {e}", "ERROR")
    return messages


def filter_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter for valid conversation messages."""
    valid_types = {"user", "assistant"}
    filtered = []
    for msg in messages:
        msg_type = msg.get("type")
        if msg_type in valid_types:
            # Ensure required fields exist
            if msg.get("uuid") and msg.get("sessionId") and msg.get("message"):
                filtered.append(msg)
    return filtered


def extract_project_info(messages: list[dict[str, Any]], cwd: str) -> tuple[str, str]:
    """Extract project ID and path from messages or cwd."""
    # Try to get cwd from first message, fall back to provided cwd
    project_path = cwd
    for msg in messages:
        if msg.get("cwd"):
            project_path = msg["cwd"]
            break

    # Generate project ID from path
    project_id = project_path.replace("/", "-").strip("-")
    if project_id.startswith("home-"):
        # Shorten home directory paths
        parts = project_id.split("-")
        if len(parts) > 2:
            project_id = "-".join(parts[2:])

    return project_id, project_path


def send_to_api(
    project_id: str, project_path: str, conversation_id: str, messages: list[dict[str, Any]]
) -> bool:
    """Send messages to Rewind API batch endpoint."""
    if not messages:
        debug("No messages to send")
        return True

    payload = {
        "projectId": project_id,
        "projectPath": project_path,
        "conversationId": conversation_id,
        "messages": messages,
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        url = f"{API_URL}/api/ingest/batch"
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )

        debug(f"Sending {len(messages)} messages to {url}")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            debug(f"API response: {result}")
            return result.get("success", False)

    except urllib.error.URLError as e:
        log(f"API request failed: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"Unexpected error sending to API: {e}", "ERROR")
        return False


def count_lines(filepath: str) -> int:
    """Count total lines in a file."""
    try:
        with open(filepath) as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main() -> int:
    """Main hook entry point."""
    # Check if hook is enabled
    if not HOOK_ENABLED:
        debug("Hook is disabled")
        return 0

    try:
        # Read hook input from stdin
        input_data = sys.stdin.read()
        if not input_data:
            debug("No input data received")
            return 0

        hook_input = json.loads(input_data)
        debug(f"Hook input: {json.dumps(hook_input, indent=2)}")

        # Extract required fields
        transcript_path = hook_input.get("transcript_path")
        session_id = hook_input.get("session_id")
        cwd = hook_input.get("cwd", "")

        if not transcript_path or not session_id:
            debug("Missing transcript_path or session_id")
            return 0

        # Expand ~ in path
        transcript_path = os.path.expanduser(transcript_path)

        if not os.path.exists(transcript_path):
            debug(f"Transcript file not found: {transcript_path}")
            return 0

        # Load state and get last processed line
        state = load_state()
        processed_lines = state.get("processed_lines", {})
        start_line = processed_lines.get(transcript_path, 0)

        # Get current line count
        total_lines = count_lines(transcript_path)
        if total_lines <= start_line:
            debug(f"No new lines to process (total: {total_lines}, processed: {start_line})")
            return 0

        debug(f"Processing lines {start_line} to {total_lines} from {transcript_path}")

        # Read and filter new messages
        new_messages = read_transcript(transcript_path, start_line)
        filtered_messages = filter_messages(new_messages)

        if not filtered_messages:
            debug("No valid messages to ingest")
            # Still update state to skip these lines next time
            processed_lines[transcript_path] = total_lines
            state["processed_lines"] = processed_lines
            save_state(state)
            return 0

        # Extract project info
        project_id, project_path = extract_project_info(filtered_messages, cwd)
        debug(f"Project: {project_id} at {project_path}")

        # Send to API
        success = send_to_api(project_id, project_path, session_id, filtered_messages)

        if success:
            log(f"Ingested {len(filtered_messages)} messages for session {session_id}")
            # Update state with new line count
            processed_lines[transcript_path] = total_lines
            state["processed_lines"] = processed_lines
            save_state(state)
        else:
            log(f"Failed to ingest messages for session {session_id}", "ERROR")

        return 0

    except json.JSONDecodeError as e:
        debug(f"Failed to parse hook input: {e}")
        return 0
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        return 0  # Never block Claude Code


if __name__ == "__main__":
    sys.exit(main())
