# Steadwing API Reference

**Base URL (dev):** `https://api.dev.steadwing.com`

All responses use a standard envelope:

```json
{ "success": true, "message": "...", "data": { ... } }
```

Authenticated endpoints require the API key in a header:

```
X-API-Key: st_xxxxxxxxxxxxxxxx
```

---

## POST `/api/agents/register` — Register an agent (no auth)

Creates a temporary organization, API key, and agent record. The agent is **unclaimed** and
expires in 3 days unless linked to a user account via the claim URL.

**Request**

```json
{ "source": "claude-code" }
```

`source` is one of `claude-code`, `cursor`, `windsurf`, `unknown` (free-form string, max 50 chars).

**Response `201`**

```json
{
  "success": true,
  "message": "Agent registered successfully",
  "data": {
    "agent_id": "uuid",
    "short_id": "agent_a7f3x2",
    "api_key": "st_...",
    "claim_url": "https://dev.steadwing.com/login?claim=<token>",
    "expires_at": "2026-06-12T10:00:00Z",
    "welcome_message": "Steadwing agent registered successfully! ..."
  }
}
```

> `api_key` is shown **only once**. Persist it to the credential file immediately.

`429` is returned if the global registration cap is hit — retry later.

---

## POST `/api/mcp/analyze` — Trigger RCA (auth)

Creates an incident and runs AI Root Cause Analysis in the background. The organization is derived
from the API key.

**Request**

```json
{
  "error_log": "Traceback (most recent call last): ...",
  "files": [
    { "name": "src/billing/service.py", "content": "<contents>" }
  ]
}
```

`files` is optional (`null` or omitted allowed). Each file is `{ "name": string, "content": string }`.

**Response `200`**

```json
{
  "success": true,
  "message": "Incident created and MCP-based analysis started in the background",
  "data": {
    "incident_id": "uuid",
    "incident_url": "https://app.steadwing.com/incident/<id>"
  }
}
```

---

## GET `/api/agents/status` — Agent status (auth)

**Response `200`**

```json
{
  "success": true,
  "message": "Agent status retrieved",
  "data": {
    "agent_id": "uuid",
    "short_id": "agent_a7f3x2",
    "name": null,
    "status": "pending_claim",
    "source": "claude-code",
    "claimed": false,
    "expires_at": "2026-06-12T10:00:00Z",
    "hours_remaining": 70,
    "warning": null,
    "claim_url": "https://dev.steadwing.com/login?claim=<token>"
  }
}
```

`404` if the API key has no associated agent.

---

## Response headers

- `X-Steadwing-Agent-Warning` — present on responses for unclaimed agents nearing expiry
  (< 24h). Contains a human-readable message with the claim URL. Surface it to the user.

## Error handling

- `401` — key revoked or agent expired → delete credentials and re-register.
- `429` — registration cap reached → retry later.
- `5xx` — server error → surface `message`/`details` and let the user retry.
