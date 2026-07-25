> **Snapshot notice:** This is a manually curated, secondary project-local snapshot. It may be stale and does not prove current deployment, branch, or runtime permission state.

# Card OS Deployment Ops

- Rollout ID: `019f50b0-b3a7-7670-83bf-6b261faf1f30`
- Date: 2026-07-14
- Last Reviewed: 2026-07-24
- Next Review Due: 2026-08-24

## Outcomes

- Backup assets in `ops/cognitive-card-server/card_os_backup.py` and their tests established atomic, no-replace backup publication. Retention skips invalid timestamp-like directory names rather than failing the entire cleanup run.
- Acceptance assets in `ops/cognitive-card-server/card_os_acceptance.py` and `tests/test_card_os_acceptance.py` refuse redirects, avoid exposing raw tokens, and compensate for post-issue failures by revoking the token by ID and removing written local state.
- Deployment assets, including `ops/cognitive-card-server/install_nginx_include.py` and the Card OS systemd units, received deployment-focused validation alongside the backup and acceptance changes.

## Operational Lesson

Passing syntax or unit checks is not sufficient evidence that a hardened service can read protected `0600` data. At the time of this rollout, the unresolved issue was a runtime permission mismatch between the backup service and protected Card OS data. Re-check the active service identity, file ownership, mode, and runtime access before relying on this snapshot.

## Boundary

Use the current code, tests, deployment runbook, and live runtime checks as authority. This summary records reusable safeguards only; it is not a production-status report.
