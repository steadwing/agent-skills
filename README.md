# Steadwing Agent Skills

Official [Agent Skills](https://agentskills.io/) for [Steadwing](https://steadwing.com) — AI-powered
Root Cause Analysis for production incidents.

Install once and your coding agent self-onboards: it registers a Steadwing agent on its own, and is
ready to run RCA on errors — no signup, no API key to paste.

## Install

```bash
npx skills add steadwing/agent-skills
```

Install a specific skill only:

```bash
npx skills add steadwing/agent-skills --skill steadwing
```

The skill activates automatically when relevant. There's nothing to publish to npm and no key to
configure — the `skills` installer reads this repo directly, and the skill registers your agent with
Steadwing the first time it runs.

## What you get

| Skill | Description |
|-------|-------------|
| **steadwing** | Self-registers as a Steadwing agent, triggers AI Root Cause Analysis on error logs/stack traces (attaching relevant source files), optionally installs a hook that watches for production-style errors and offers RCA, and surfaces claim/expiry reminders. |

## How it works

1. **Install** the skill with the command above.
2. **First use** — the skill detects your agent (Claude Code / Cursor / Windsurf), calls
   `POST /api/agents/register` (no auth), and stores the returned API key at
   `~/.steadwing/credentials.json`. It prints a **claim URL** so you can link the agent to your
   Steadwing account (unclaimed agents expire in 3 days).
3. **(Optional) Auto-detection** — in Claude Code, the skill can install a `PostToolUse` hook that
   detects production-style errors (tracebacks, unhandled exceptions, stack traces) and asks whether
   to run RCA. The hook only *detects and asks* — it never sends anything without your confirmation.
4. **Run RCA** — on request (or after you confirm a detected error), the skill calls
   `POST /api/mcp/analyze` with the error log and relevant files, then returns the incident URL to
   track analysis (~1–3 min, runs in the background).

## Skill structure

```
skills/steadwing/
├── SKILL.md                     # agent instructions (entry point)
├── references/
│   └── api-reference.md         # full Steadwing API reference
└── scripts/
    ├── steadwing_rca_hook.py    # passive PostToolUse error-detection hook
    └── install_hook.py          # idempotent installer for the hook
```

## Privacy

The skill sends error logs and any source files you confirm to the Steadwing API
(`https://api.dev.steadwing.com`) for analysis. RCA is only triggered on explicit request or after
you confirm a detected error — never silently.

## License

[MIT](./LICENSE)
