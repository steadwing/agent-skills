# Repository guide for AI agents

This repo packages **Agent Skills** for [Steadwing](https://steadwing.com), an AI Root Cause
Analysis platform. The skills let a coding agent self-register with Steadwing and trigger RCA on
production errors.

## Layout

- `skills/<name>/SKILL.md` — the skill manifest and instructions (the entry point an agent reads).
- `skills/<name>/references/` — supporting docs loaded on demand.
- `skills/<name>/scripts/` — helper scripts (e.g. the error-detection hook and its installer).
- `skills.sh.json` — registry/grouping metadata for the `skills` installer.

## Conventions

- `SKILL.md` frontmatter requires `name` and `description`. The `description` must clearly state
  *when* to use the skill — it's how agents decide relevance.
- Keep `SKILL.md` focused; push detail into `references/`.
- Scripts must be dependency-free (Python 3 stdlib only) and cross-platform where feasible.
- The detection hook is **passive**: it surfaces errors and asks; it never calls the Steadwing API
  or sends data without explicit user confirmation.

## Editing a skill

1. Update `skills/<name>/SKILL.md` (and `references/` as needed).
2. If you add a skill, list it in `skills.sh.json` and the README table.
3. Validate JSON and SKILL frontmatter (CI runs `.github/workflows/validate.yml`).
