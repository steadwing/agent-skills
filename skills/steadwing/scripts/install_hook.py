#!/usr/bin/env python3
"""
Install the Steadwing RCA detection hook into Claude Code's user settings.

Registers `steadwing_rca_hook.py` as a `PostToolUse` hook (matcher: Bash) in
`~/.claude/settings.json`. Idempotent: merges into existing settings and will not add a
duplicate entry if the same hook command is already present.

Usage:
    python3 install_hook.py            # install into ~/.claude/settings.json
    python3 install_hook.py --uninstall
    python3 install_hook.py --settings /path/to/settings.json
"""

import argparse
import json
import os
import sys

HOOK_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steadwing_rca_hook.py")
MATCHER = "Bash"


def _default_settings_path() -> str:
    return os.path.join(os.path.expanduser("~"), ".claude", "settings.json")


def _hook_command() -> str:
    # Quote the path so spaces in the home dir are handled.
    return f'python3 "{HOOK_SCRIPT}"'


def _load(path: str) -> dict:
    try:
        with open(path) as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except ValueError:
        print(f"warning: {path} is not valid JSON; refusing to overwrite.", file=sys.stderr)
        sys.exit(1)


def _save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def _command_present(post_tool_use: list, command: str) -> bool:
    for group in post_tool_use:
        if not isinstance(group, dict):
            continue
        for hook in group.get("hooks", []) or []:
            if isinstance(hook, dict) and hook.get("command") == command:
                return True
    return False


def install(path: str) -> None:
    command = _hook_command()
    settings = _load(path)
    hooks = settings.setdefault("hooks", {})
    post_tool_use = hooks.setdefault("PostToolUse", [])

    if _command_present(post_tool_use, command):
        print("Steadwing RCA hook already installed — nothing to do.")
        return

    post_tool_use.append(
        {
            "matcher": MATCHER,
            "hooks": [{"type": "command", "command": command}],
        }
    )
    _save(path, settings)
    print(f"Installed Steadwing RCA detection hook into {path}")
    print("Restart Claude Code (or start a new session) for the hook to take effect.")


def uninstall(path: str) -> None:
    command = _hook_command()
    settings = _load(path)
    post_tool_use = settings.get("hooks", {}).get("PostToolUse", [])
    if not post_tool_use:
        print("No Steadwing RCA hook found — nothing to remove.")
        return

    kept = []
    removed = False
    for group in post_tool_use:
        hooks = [h for h in (group.get("hooks", []) if isinstance(group, dict) else []) if not (
            isinstance(h, dict) and h.get("command") == command
        )]
        if isinstance(group, dict) and len(hooks) != len(group.get("hooks", []) or []):
            removed = True
        if hooks:
            group = {**group, "hooks": hooks} if isinstance(group, dict) else group
            kept.append(group)
        elif not isinstance(group, dict):
            kept.append(group)

    settings["hooks"]["PostToolUse"] = kept
    _save(path, settings)
    print("Removed Steadwing RCA hook." if removed else "No matching Steadwing RCA hook found.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/remove the Steadwing RCA detection hook.")
    parser.add_argument("--uninstall", action="store_true", help="Remove the hook instead of installing.")
    parser.add_argument("--settings", default=_default_settings_path(), help="Path to settings.json.")
    args = parser.parse_args()

    if not os.path.exists(HOOK_SCRIPT):
        print(f"error: hook script not found at {HOOK_SCRIPT}", file=sys.stderr)
        return 1

    if args.uninstall:
        uninstall(args.settings)
    else:
        install(args.settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
