#!/usr/bin/env python3
"""
Steadwing RCA detection hook (Claude Code `PostToolUse`).

This hook is intentionally PASSIVE. It inspects the result of tool calls (primarily Bash)
for production-style error signals — tracebacks, unhandled exceptions, stack traces — and,
when it finds one, injects a note via `additionalContext` asking the agent to OFFER to run
Steadwing RCA. It never contacts the Steadwing API and never sends anything on its own;
the agent always asks the user first (per the steadwing SKILL.md).

A small debounce (state file) prevents nagging about the same error repeatedly.

Input: Claude Code PostToolUse JSON on stdin.
Output: PostToolUse JSON on stdout (additionalContext) when an error is detected; nothing otherwise.
Exit code is always 0 — this hook must never block tool execution.
"""

import hashlib
import json
import os
import re
import sys
import time

DEBOUNCE_SECONDS = 300  # don't re-surface the same error signature within 5 minutes
MAX_LOG_CHARS = 4000  # cap the snippet we echo back into context

# Strong, production-style error signals. Ordinary failures (plain "exit 1",
# "command not found", a single "error:" line) are deliberately NOT matched here so the
# hook stays quiet for routine command failures.
STRONG_PATTERNS = [
    r"Traceback \(most recent call last\)",          # Python
    r"\bUnhandled (?:promise rejection|exception)\b",  # Node / general
    r"\bpanic:\s",                                    # Go
    r"\bgoroutine \d+ \[",                            # Go stack
    r"^\s*at [\w.$<>]+\([^)]*:\d+:\d+\)",             # JS/TS stack frame
    r"Exception in thread \"",                        # Java
    r"\bcaused by:\s",                                # Java/Kotlin chained
    r"\b[A-Z][A-Za-z0-9]*(?:Error|Exception):",       # SomethingError: / SomethingException:
    r"\bsegmentation fault\b",
    r"\bfatal error:\s",
]
_STRONG_RE = re.compile("|".join(f"(?:{p})" for p in STRONG_PATTERNS), re.MULTILINE)


def _state_path() -> str:
    base = os.environ.get("APPDATA") if os.name == "nt" else os.path.expanduser("~/.steadwing")
    if os.name == "nt" and base:
        base = os.path.join(base, "steadwing")
    return os.path.join(base or os.path.expanduser("~/.steadwing"), ".rca_hook_state.json")


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Prefer common text-bearing fields, then fall back to the whole dict.
        parts = [str(value.get(k, "")) for k in ("stdout", "stderr", "output", "content", "text", "error")]
        joined = "\n".join(p for p in parts if p)
        return joined or json.dumps(value, default=str)
    if isinstance(value, list):
        return "\n".join(_stringify(v) for v in value)
    return str(value)


def _recently_seen(signature: str) -> bool:
    path = _state_path()
    now = time.time()
    seen = {}
    try:
        with open(path) as fh:
            seen = json.load(fh)
    except (OSError, ValueError):
        seen = {}
    # prune old entries
    seen = {k: v for k, v in seen.items() if isinstance(v, (int, float)) and now - v < DEBOUNCE_SECONDS}
    if signature in seen:
        return True
    seen[signature] = now
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(seen, fh)
    except OSError:
        pass  # debounce is best-effort
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = ""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = str(tool_input.get("command", ""))

    output = _stringify(payload.get("tool_response"))
    haystack = f"{command}\n{output}"

    match = _STRONG_RE.search(haystack)
    if not match:
        return 0

    signature = hashlib.sha1(match.group(0).encode("utf-8", "replace")).hexdigest()[:16]
    if _recently_seen(signature):
        return 0

    snippet = output.strip()[:MAX_LOG_CHARS]
    note = (
        "A production-style error was detected in the previous command's output "
        f"(matched: {match.group(0)!r}).\n\n"
        "Per the `steadwing` skill, OFFER to run Root Cause Analysis: ask the user whether "
        "they want you to trigger Steadwing RCA on this error. Only if they confirm, follow the "
        "skill to register (if needed) and POST to /api/mcp/analyze, attaching the relevant source "
        "files referenced in the stack trace. Do NOT send anything without explicit confirmation.\n\n"
        f"Detected error output (truncated):\n{snippet}"
    )

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": note,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # A hook must never crash the session. Fail silent.
        sys.exit(0)
