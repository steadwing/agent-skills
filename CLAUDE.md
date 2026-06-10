See [AGENTS.md](./AGENTS.md) for the repository guide.

Quick notes for Claude Code specifically:

- The `steadwing` skill can install a `PostToolUse` hook via `skills/steadwing/scripts/install_hook.py`.
  Only offer this once, after the first successful registration, and only in Claude Code.
- The hook is passive — it detects production-style errors and asks before any RCA is triggered.
  Never POST to `/api/mcp/analyze` without explicit user confirmation.
- Credentials live at `~/.steadwing/credentials.json`. On `401`, delete and re-register.
