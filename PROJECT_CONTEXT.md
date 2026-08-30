# Kids Visual Learning Pack Project Context

- Last Reviewed: 2026-07-24
- Next Review Due: 2026-08-24

This is a stable repository index. Current task status belongs in `docs/ai/CURRENT_TASK.md`; recent execution state belongs in `docs/ai/HANDOFF.md`.

## Required Read Order

1. `AGENTS.md`
2. `PROJECT_CONTEXT.md`
3. `docs/README.md`
4. `docs/ai/CURRENT_TASK.md`
5. `docs/ai/HANDOFF.md`
6. Task-related code, tests, design docs, ADRs, and runbooks

## Product Boundary

- `boards/kids-world/`: top-level React and TypeScript learning universe.
- `boards/spider-verse/`: standalone static visual story board.
- `boards/paw-patrol/`: Vite, React, and TypeScript task center.
- `packages/kids-content/`: shared typed content package.
- `apps/miniprogram/`: Taro WeChat mini program.
- `ops/`, `skills/cognitive-card-os/`, and `migration/card-os/`: Cognitive Card OS server, thin Skill, release, deployment, and migration assets.

## Canonical Direction

- Product and local development entrypoint: `README.md`.
- Repository structure: `docs/project-structure.md`.
- Current cross-renderer architecture baseline: `docs/architecture-iteration-v1.3.md`.
- Cognitive Card OS normative entrypoint: `docs/cognitive-card-os-system-design.md`.
- Cognitive Card OS active task ledger: `docs/cognitive-card-os-roadmap.md`.
- Cognitive Card OS long-term architecture decision: `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`; one governed Knowledge Core feeds learning design and multiple Projection families, while `four-card` remains the compatible first family.
- Cognitive Card OS workspace roles and live-worktree limits: `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`.
- Cognitive Card OS single-operator main path and deferred multi-user gates: `docs/decisions/ADR-004-single-operator-main-flow.md`.
- Knowledge Core contract semantics: `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md`.
- Production operations truth: `docs/operations/cognitive-card-server-deployment-2026-07-14.md`.

## Working State

- Current task: `docs/ai/CURRENT_TASK.md`.
- Latest reliable handoff: `docs/ai/HANDOFF.md`.
- Non-Card-OS backlog: `docs/ai/BACKLOG.md`.
- Documentation map and status: `docs/README.md`.
- Long-term decisions: `docs/decisions/`.

## Cross-Model Rule

Do not rely on a previous model's chat history. Recover state from the files above, verify drift against code and tests, preserve unrelated dirty changes, and update the handoff before switching tools.
