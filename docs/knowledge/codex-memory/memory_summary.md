# Project Memory Summary

## Card OS Deployment

- Use a dedicated worktree and fresh implementer/reviewer gates only when the execution plan or user explicitly calls for subagent-driven work.
- Backup publication must be atomic and no-clobber.
- Retention must skip invalid timestamp-like directory names instead of failing the whole run.
- Acceptance probes must refuse redirects and never expose raw tokens in arguments, output, logs, or stable error messages.
- Revoke by token ID and remove written local state after post-issue failures.
- Syntax tests do not prove a hardened service can read protected `0600` data; validate the runtime permission model.

## Local Skill Installation

- Inspect the archive structure and `SKILL.md` name before copying.
- Stop if the destination already exists unless replacement is explicitly authorized.
- Verify the installed file tree and confirm no `__MACOSX` or `._*` metadata was copied.
- Tell the user to restart Codex after a successful local installation.

## Freshness Boundary

These lessons are reusable patterns, not proof of current branch, deployment, permission, or installed-skill state. Verify current repository and runtime facts before acting.
