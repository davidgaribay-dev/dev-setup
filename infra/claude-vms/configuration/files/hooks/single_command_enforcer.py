#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block Command Chaining

This hook intercepts Bash tool calls and blocks commands that contain
shell chaining operators (&&, ||, ;) or command substitution ($(), ``).

This prevents Claude from running multiple commands in a single call,
giving you granular control to approve each command individually.
"""
import json
import re
import sys


BLOCKED_PATTERNS = [
    # Command chaining operators
    (r'(?<![&|])\s*&&\s*(?![&|])', 'Command chaining with && is not allowed. Run commands separately.'),
    (r'(?<![|])\s*\|\|\s*(?![|])', 'Command chaining with || is not allowed. Run commands separately.'),
    (r'(?<![;])\s*;\s*(?![;])', 'Command chaining with ; is not allowed. Run commands separately.'),

    # Command substitution (potential for hidden command execution)
    (r'\$\([^)]+\)', 'Command substitution $() is not allowed.'),
    (r'`[^`]+`', 'Backtick command substitution is not allowed.'),

    # Process substitution
    (r'<\([^)]+\)', 'Process substitution <() is not allowed.'),
    (r'>\([^)]+\)', 'Process substitution >() is not allowed.'),
]

# Commands that are allowed to use piping (read-only/safe operations)
PIPE_ALLOWED_PREFIXES = [
    'grep',
    'cat',
    'head',
    'tail',
    'wc',
    'sort',
    'uniq',
    'awk',
    'sed',
    'cut',
    'tr',
    'less',
    'more',
    'xargs',
    'find',
]


def validate_command(command: str) -> tuple[bool, str]:
    """
    Validate a bash command for dangerous patterns.

    Returns:
        (is_blocked, reason) - True if command should be blocked
    """
    for pattern, message in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            return True, message

    return False, ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # Invalid JSON, let it pass (fail open for non-Bash tools)
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")

    # Only validate Bash commands
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    is_blocked, reason = validate_command(command)

    if is_blocked:
        # Output JSON with block decision
        result = {
            "decision": "block",
            "reason": reason
        }
        print(json.dumps(result))
        sys.exit(0)

    # Command is allowed - exit cleanly (no output means allow)
    sys.exit(0)


if __name__ == "__main__":
    main()
