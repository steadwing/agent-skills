---
name: steadwing
description: "Use when the user asks to run Root Cause Analysis (RCA), debug a production incident, analyze an error log or stack trace, or trigger Steadwing. Also use when a production-style error (traceback / unhandled exception / stack trace) is surfaced and the user wants automated investigation. Handles agent registration, authentication, optional auto-detection hook setup, and RCA triggering via the Steadwing API."
metadata:
  author: steadwing
  version: "0.1.0"
  homepage: "https://steadwing.com"
---

# Steadwing — AI Root Cause Analysis

Steadwing analyzes production incidents using AI. This skill makes the agent self-onboard
and trigger RCA with zero manual setup. It handles:

1. **Auto-registering** as a Steadwing agent on first use (no signup, no API key to paste)
2. **Triggering RCA** on error logs / stack traces, with relevant source files attached
3. **Optional auto-detection**: installing a Claude Code hook that watches for production-style
   errors and offers to run RCA
4. **Checking status** and surfacing claim/expiry reminders

**Base URL:** `https://api.dev.steadwing.com`
**Auth header:** `X-API-Key: {api_key}` on every authenticated request.

---

## Step 1 — Ensure the agent is registered

Before any authenticated call, check for stored credentials.

### Credential file locations

| OS | Path |
|----|------|
| macOS / Linux | `~/.steadwing/credentials.json` |
| Windows | `%APPDATA%\steadwing\credentials.json` |

### Credential file format

```json
{
    "api_key": "st_...",
    "agent_id": "uuid",
    "short_id": "agent_a7f3x2",
    "base_url": "https://api.dev.steadwing.com",
    "claim_url": "https://dev.steadwing.com/login?claim=<token>",
    "created_at": "2026-06-09T10:00:00Z"
}
```

### If the credential file is missing → register

1. **Detect the agent source** from environment:
   - Claude Code (`CLAUDECODE`/`CLAUDE_CODE*` set, or you are Claude Code) → `"claude-code"`
   - Cursor (`CURSOR_*`) → `"cursor"`
   - Windsurf (`WINDSURF_*`) → `"windsurf"`
   - Otherwise → `"unknown"`
2. `POST https://api.dev.steadwing.com/api/agents/register` with body `{"source": "<detected-source>"}`. **No auth required.**
3. Create the `~/.steadwing/` directory and write `credentials.json` from the response `data`
   (map `data.api_key`, `data.agent_id`, `data.short_id`, `data.claim_url`; set `base_url` to the API base above).
4. On Unix, `chmod 600 ~/.steadwing/credentials.json`.
5. Print the `data.welcome_message` and the `data.claim_url` so the user can link the agent to their account.

> Unclaimed agents expire in **3 days**. Always show the claim URL after registering.

### On any `401` response

The key was revoked or the agent expired. Delete the credential file, re-run registration above,
and tell the user: *"Your Steadwing agent session expired — re-registered with a new key."*

### Expiry warning header

After every authenticated call, check the `X-Steadwing-Agent-Warning` response header. If present,
surface its value prominently — it contains the claim URL and time remaining.

---

## Step 2 — (Optional, recommended) Set up auto-detection

So the agent is "ready to send RCA when an error happens," offer to install the detection hook
**once**, right after the first successful registration:

> *"Want me to watch for production-style errors and offer to run RCA automatically? (Claude Code only)"*

If the user agrees, run the installer from this skill's `scripts/` directory:

```bash
python3 "<this-skill-dir>/scripts/install_hook.py"
```

This registers a **`PostToolUse` hook** in the user's `~/.claude/settings.json`. The hook only
**detects** production-style errors (tracebacks, unhandled exceptions, stack traces) and injects a
note asking you to offer RCA. **It never sends anything on its own** — you always ask the user
first (see Step 3). The installer is idempotent and merges into existing settings.

To remove it later: delete the matching entry under `hooks.PostToolUse` in `~/.claude/settings.json`.

---

## Step 3 — Trigger RCA

Trigger when **any** of these is true:
- The user explicitly asks ("run steadwing", "trigger RCA", "analyze this incident/error").
- The user shares an error log or stack trace and asks why it happened.
- The detection hook surfaced a production-style error **and the user confirms** they want RCA.

**Never auto-send without user confirmation.** When an error is detected by the hook, ask first.

### Call

```
POST https://api.dev.steadwing.com/api/mcp/analyze
X-API-Key: {api_key}
Content-Type: application/json

{
    "error_log": "The full error log or stack trace to analyze",
    "files": [
        {"name": "src/billing/service.py", "content": "<file contents>"}
    ]
}
```

`files` is optional but **strongly improves analysis**. Attach relevant source:
- Read any files named in the stack trace / error (e.g. `src/billing/service.py:45` → read that file).
- Include modules/classes the error references.
- Cap at **5–10 files**, only ones directly relevant — never the whole repo.

### Response

```json
{
    "success": true,
    "data": {
        "incident_id": "uuid",
        "incident_url": "https://app.steadwing.com/incident/<id>"
    }
}
```

Analysis runs in the background (~1–3 min). Tell the user:
*"RCA started — track progress at: {data.incident_url}"*

---

## Step 4 — Check status (optional)

```
GET https://api.dev.steadwing.com/api/agents/status
X-API-Key: {api_key}
```

Returns `claimed`, `status`, `expires_at`, `hours_remaining`, `warning`, `claim_url`. Use it to
remind the user to claim an unclaimed agent before it expires.

---

For the full API reference, see [`references/api-reference.md`](references/api-reference.md).
