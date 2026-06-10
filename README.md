# Steadwing Agent Skills

Official [Agent Skills](https://agentskills.io/) for [Steadwing](https://steadwing.com) — AI-powered
Root Cause Analysis for production incidents.

Install once and your coding agent self-onboards: it registers a Steadwing agent on its own, and is
ready to run RCA on errors — no signup, no API key to paste.

## Install

Works with Claude Code, Cursor, Windsurf, GitHub Copilot, and 18+ other agents — one repo,
every agent. There's nothing to publish to npm and no key to configure: the installer reads this
repo directly, and the skill registers your agent with Steadwing the first time it runs.

### Any agent (recommended)

```bash
npx skills add steadwing/agent-skills
```

The [`skills`](https://skills.sh) CLI auto-detects your agent and installs the skill into its
directory (e.g. `.claude/skills/` for Claude Code, `.cursor/skills/` for Cursor). Useful flags:

```bash
npx skills add steadwing/agent-skills -g                  # global — available in all projects
npx skills add steadwing/agent-skills -a claude-code      # target a specific agent
npx skills add steadwing/agent-skills --skill steadwing   # install just this skill
npx skills add steadwing/agent-skills --copy              # copy instead of symlink
```

> If the skill doesn't appear in Claude Code after install, it's usually a project- vs global-scope
> mismatch — try `-g`, or target it explicitly with `-a claude-code`. Then start a new session
> (agents load skills at session start).

### Claude Code plugin (native)

Claude Code users can also install via the native plugin system, which doesn't depend on the
`skills` CLI:

```bash
claude plugin marketplace add steadwing/agent-skills
claude plugin install steadwing@steadwing-agent-skills
```

The skill activates automatically when relevant — no manual invocation needed.

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

## Repo structure

```
.
├── .claude-plugin/
│   └── marketplace.json         # Claude Code native plugin manifest
├── skills.sh.json               # skills.sh registry/grouping
└── skills/steadwing/
    ├── SKILL.md                 # agent instructions (entry point)
    ├── references/
    │   └── api-reference.md     # full Steadwing API reference
    └── scripts/
        ├── steadwing_rca_hook.py  # passive PostToolUse error-detection hook
        └── install_hook.py        # idempotent installer for the hook
```

## Privacy

The skill sends error logs and any source files you confirm to the Steadwing API
(`https://api.dev.steadwing.com`) for analysis. RCA is only triggered on explicit request or after
you confirm a detected error — never silently.

## License

[MIT](./LICENSE)
