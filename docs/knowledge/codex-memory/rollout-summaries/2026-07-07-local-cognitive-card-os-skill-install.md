> **Snapshot notice:** This is a manually curated, secondary project-local snapshot. It may be stale and does not prove the currently installed Skill or its destination state.

# Local Cognitive Card OS Skill Install

- Rollout ID: `019f3a8c-a5ab-7ba0-92f9-019e31593437`
- Date: 2026-07-07
- Last Reviewed: 2026-07-24
- Next Review Due: 2026-08-24

## Installation Procedure

1. Inspect the archive structure before copying and confirm the `SKILL.md` `name:` value.
2. Derive the destination from that name under `~/.codex/skills/`.
3. Stop when the destination already exists unless replacement is explicitly authorized.
4. Verify the installed file tree after the copy and confirm that neither `__MACOSX` nor `._*` metadata was installed.
5. Tell the user to restart Codex after a successful installation.

## Boundary

This is a reusable local-install pattern, not evidence that a particular archive, destination, or installed Skill remains current. Inspect the current archive and destination before acting.
