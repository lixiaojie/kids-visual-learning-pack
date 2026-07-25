# Codex Memory Snapshot

- Snapshot Type: manually curated project-local copy
- Last Reviewed: 2026-07-24
- Next Review Due: 2026-08-24
- Global Source: `~/.codex/memories/`

## Purpose

This directory preserves reusable project experience so another model can continue without access to one Codex session or hidden global memory.

## Priority and Freshness

1. Current code, tests, and formal repository docs win.
2. `docs/ai/CURRENT_TASK.md` and `docs/ai/HANDOFF.md` describe current execution.
3. These files are secondary snapshots and may be stale.
4. Re-verify branch, paths, runtime permissions, and production state before reuse.

## Included Files

- [Project Memory Summary](memory_summary.md)
- [Card OS Deployment Ops](rollout-summaries/2026-07-11-card-os-deployment-ops.md)
- [Local Cognitive Card OS Skill Install](rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md)

## Refresh Procedure

Review every 31 days and when a completed task produces a reusable lesson not already captured in formal project docs. Copy only curated Markdown, update both dates, run the governance checks, and record the refresh in `docs/ai/HANDOFF.md`.

## Exclusions

Do not copy global `MEMORY.md`, raw rollout logs, credentials, private client configuration, unrelated-project memory, or machine-specific temporary state.
