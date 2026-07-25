# Cross-Model Project Documentation Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repository-local, periodically reviewed documentation system that lets any Coding Agent recover project facts, current work, recent progress, historical context, and reusable Card OS experience without relying on one model's private session state.

**Architecture:** Add a thin root context index and one canonical docs map over the existing `docs/ai/` task-state layer. Preserve superseded documents in a dated archive, copy only curated project-relevant memory summaries, and enforce required entrypoints, link validity, and review dates with a read-only Bash checker integrated into the existing Agent state checks.

**Tech Stack:** Markdown, Bash, Git, existing `scripts/ai/` infrastructure, Node.js only for `package.json` validation

## Global Constraints

- Preserve all existing uncommitted user and infrastructure changes; do not reset, clean, force-checkout, or delete unrelated files.
- Do not modify business implementation under `boards/`, `apps/`, `packages/`, `ops/`, `skills/`, or `tests/`.
- Do not modify CI, deployment configuration, production systems, user-level memory, or `outputs/`.
- Keep `docs/ai/HANDOFF.md` as the only dynamic handoff truth; do not add a root `HANDOFF.md`.
- Keep `PROJECT_CONTEXT.md` thin and stable; current work belongs in `docs/ai/CURRENT_TASK.md` and `docs/ai/HANDOFF.md`.
- Archive only documents with explicit replacement evidence; retain history and record replacement pointers.
- Treat repository memory files as curated snapshots; code, tests, and formal repository docs always win on conflict.
- Do not copy global `MEMORY.md`, raw rollout JSONL, credentials, private client configuration, or unrelated-project memory.
- Use task-event updates plus a 31-day review reminder; never auto-copy from user directories.
- Use `apply_patch` for repository file edits and moves.
- Do not commit, push, merge, or create a PR unless the user explicitly authorizes it.

---

## File Map

### New Files

- `PROJECT_CONTEXT.md`: stable root-level project and reading-order index.
- `docs/README.md`: canonical map of current, active, historical, review-needed, archived, and memory documents.
- `docs/archive/README.md`: archive manifest and archive policy.
- `docs/archive/2026-07-24-doc-governance/spec-v1.md`: archived project spec v1.
- `docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md`: archived architecture iteration v1.2.
- `docs/knowledge/codex-memory/README.md`: snapshot semantics, source boundary, and review metadata.
- `docs/knowledge/codex-memory/memory_summary.md`: project-only durable lessons.
- `docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md`: curated Card OS deployment rollout summary.
- `docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md`: curated local Skill installation summary.
- `scripts/ai/check-doc-governance.sh`: read-only required-file, link, archive, and review-date checker.
- `scripts/ai/test-doc-governance.sh`: isolated fixture tests for PASS, FAIL, and WARN behavior.

### Modified Files

- `README.md`: add cross-model collaboration entrypoint.
- `AGENTS.md`: add canonical reading order and documentation governance rules.
- `docs/ai/README.md`: describe the root context, docs map, archive, memory snapshots, and periodic review flow.
- `docs/ai/START_PROMPTS.md`: make recovery and infrastructure prompts include the new entrypoints and governance check.
- `docs/ai/CURRENT_TASK.md`: track implementation progress and final acceptance.
- `docs/ai/HANDOFF.md`: record real changes, checks, known failures, and next action.
- `scripts/ai/check-agent-infra.sh`: require and inspect the new governance files.
- `scripts/ai/check-agent-state.sh`: run the new governance check as a first-class step.
- `package.json`: add `check:doc-governance` and `test:doc-governance`.
- Active Markdown files that still route to archived paths: update only confirmed inbound references.

---

### Task 1: Establish Canonical Navigation and Governance Rules

**Files:**

- Create: `PROJECT_CONTEXT.md`
- Create: `docs/README.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/ai/README.md`
- Modify: `docs/ai/START_PROMPTS.md`

**Interfaces:**

- Consumes: existing module descriptions in `README.md`, `docs/project-structure.md`, `docs/cognitive-card-os-system-design.md`, and `docs/cognitive-card-os-roadmap.md`.
- Produces: canonical recovery order `AGENTS.md → PROJECT_CONTEXT.md → docs/README.md → docs/ai/CURRENT_TASK.md → docs/ai/HANDOFF.md`.
- Produces: document status vocabulary `Canonical Current`, `Active`, `Historical Reference`, `Needs Review`, and `Archived`.

- [ ] **Step 1: Run the navigation precondition and confirm it fails**

Run:

```bash
test -f PROJECT_CONTEXT.md
test -f docs/README.md
```

Expected: both commands exit non-zero because neither canonical index exists yet.

- [ ] **Step 2: Create `PROJECT_CONTEXT.md`**

Use `apply_patch` to create a concise file with these exact sections:

```markdown
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
- Production operations truth: `docs/operations/cognitive-card-server-deployment-2026-07-14.md`.

## Working State

- Current task: `docs/ai/CURRENT_TASK.md`.
- Latest reliable handoff: `docs/ai/HANDOFF.md`.
- Non-Card-OS backlog: `docs/ai/BACKLOG.md`.
- Documentation map and status: `docs/README.md`.
- Long-term decisions: `docs/decisions/`.

## Cross-Model Rule

Do not rely on a previous model's chat history. Recover state from the files above, verify drift against code and tests, preserve unrelated dirty changes, and update the handoff before switching tools.
```

- [ ] **Step 3: Create `docs/README.md` as the canonical documentation map**

Use Markdown links, not plain code paths, for every routed document so the governance checker can validate targets. Include these sections and entries:

```markdown
# Project Documentation Map

- Last Reviewed: 2026-07-24
- Next Review Due: 2026-08-24

Start with [PROJECT_CONTEXT](../PROJECT_CONTEXT.md). This file is the only canonical map of formal project documentation; it does not replace code, tests, task state, or handoff records.

## Canonical Current Docs

| Document | Role | Status |
| --- | --- | --- |
| [Project README](../README.md) | Product purpose, commands, and local entrypoints | Canonical Current |
| [Project Context](../PROJECT_CONTEXT.md) | Thin root index and read order | Canonical Current |
| [Project Structure](project-structure.md) | Repository module layout | Canonical Current |
| [Architecture Iteration v1.3](architecture-iteration-v1.3.md) | Current H5 and mini-program architecture baseline | Canonical Current |
| [Cross-Renderer Decisions](cross-renderer-decisions.md) | Intentional renderer differences and parity decisions | Canonical Current |
| [Card OS System Design](cognitive-card-os-system-design.md) | Normative Card OS architecture entrypoint | Canonical Current |
| [Card OS Roadmap](cognitive-card-os-roadmap.md) | Active Card OS task ledger | Active |
| [Card OS Deployment Runbook](operations/cognitive-card-server-deployment-2026-07-14.md) | Production deployment and operations truth | Canonical Current |

## Current Task and Handoff

| Document | Role | Status |
| --- | --- | --- |
| [Current Task](ai/CURRENT_TASK.md) | Unique current execution scope | Active |
| [Latest Handoff](ai/HANDOFF.md) | Latest verified execution state | Active |
| [Backlog](ai/BACKLOG.md) | Non-Card-OS candidate work | Active |
| [Agent Infrastructure](ai/README.md) | Cross-model collaboration workflow | Canonical Current |
| [Start Prompts](ai/START_PROMPTS.md) | Copy-ready recovery and handoff prompts | Canonical Current |
| [Local Configuration Boundary](ai/LOCAL_CONFIG.md) | Private-data and local-config rules | Canonical Current |

## Active Product and Architecture Docs

| Document | Role | Status |
| --- | --- | --- |
| [Project Spec v2.1](spec-v2.md) | Baseline product and content model used by v1.3 architecture | Active |
| [EdgeOne and Mini-Program Alignment](edgeone-miniprogram-alignment-spec-v1.md) | Cross-channel content alignment specification | Active |
| [Yutou Verse Main Tracking v1.2](yutou-verse-main-tracking-spec-v1.2.md) | Interaction-evidence tracking draft | Needs Review |
| [Kids World Image Generation Handoff](kids-world-image-generation-handoff.md) | Topic-level image generation state | Active |
| [Card OS Asset Migration Inventory](cognitive-card-os-asset-migration-inventory.md) | Historical asset source inventory | Active |

## Active Designs and Plans

### Designs

| Document | Role | Status |
| --- | --- | --- |
| [Mobile Scene Deck Design](superpowers/specs/2026-06-23-mobile-scene-deck-design.md) | Mobile scene deck design | Needs Review |
| [Card OS Pro Subscriber Execution Design](superpowers/specs/2026-07-13-cognitive-card-pro-subscriber-execution-design.md) | Pro-client execution architecture | Approved |
| [Card OS Server Deployment Design](superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md) | Production deployment architecture | Implemented |
| [Card OS Thin Skill Release Design](superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md) | Thin Skill distribution architecture | Approved |
| [Project Documentation Governance Design](superpowers/specs/2026-07-24-project-documentation-governance-design.md) | Cross-model documentation governance | Active |

### Plans

| Document | Role | Status |
| --- | --- | --- |
| [Mobile Scene Deck Implementation](superpowers/plans/2026-06-23-mobile-scene-deck-implementation-plan.md) | Mobile scene deck implementation plan | Needs Review |
| [Card OS Asset Inventory and Dedup](superpowers/plans/2026-07-13-cognitive-card-asset-inventory-dedup-plan.md) | Asset inventory implementation | Needs Review |
| [Card OS Remote API Auth Protocol](superpowers/plans/2026-07-13-cognitive-card-remote-api-auth-protocol-plan.md) | API and authentication implementation | Needs Review |
| [Card OS Subscriber Execution Foundation](superpowers/plans/2026-07-13-cognitive-card-subscriber-execution-foundation-plan.md) | Subscriber-client foundation | Needs Review |
| [Card OS Server Deployment](superpowers/plans/2026-07-14-cognitive-card-server-deployment-plan.md) | Deployment execution plan | Needs Review |
| [Card OS Skill Registry](superpowers/plans/2026-07-15-cognitive-card-skill-registry-plan.md) | Skill registry execution plan | Needs Review |
| [Card OS Thin Client](superpowers/plans/2026-07-15-cognitive-card-thin-client-plan.md) | Thin-client execution plan | Needs Review |
| [Project Documentation Governance Implementation](superpowers/plans/2026-07-24-project-documentation-governance-implementation.md) | Current implementation plan | Active |

## Operations, Compliance, and Decisions

| Document | Role | Status |
| --- | --- | --- |
| [Content IP Risk Register](compliance/content-ip-risk-register.md) | Content and copyright constraints | Canonical Current |
| [WeChat Mini-Program Checklist](compliance/wechat-miniprogram-checklist.md) | Mini-program compliance checklist | Active |
| [ADR Template](decisions/ADR-TEMPLATE.md) | Long-term decision record template | Canonical Current |

## Historical Reference

| Document | Role | Status |
| --- | --- | --- |
| [Kids World Refactor Design](2026-05-11-kids-world-refactor-design.md) | Completed refactor design provenance | Historical Reference |
| [Kids World Refactor Plan](2026-05-11-kids-world-refactor-plan.md) | Completed refactor plan provenance | Historical Reference |
| [Architecture Review v1](architecture-review-v1.md) | Earlier architecture assessment | Historical Reference |
| [Cicada Life Spec v1.1](cicada-life-project-spec-v1.1.md) | Observation-template example | Historical Reference |
| [Cross-Renderer Parity Plan v1](cross-renderer-parity-plan-v1.md) | Earlier parity execution plan | Historical Reference |

Historical reference files remain in place until explicit replacement evidence justifies archival.

## Maintenance

- Update this map whenever a formal Markdown file is added, moved, superseded, or archived.
- Review this map and the memory snapshot every 31 days.
- Run `bash scripts/ai/check-doc-governance.sh` and `bash scripts/ai/check-agent-state.sh`.
```

- [ ] **Step 4: Add the collaboration entrypoint to `README.md`**

Insert after the opening project description:

```markdown
## 跨模型协作入口

新的 Coding Agent 或模型工具先按以下顺序恢复上下文：

1. [工程规则](AGENTS.md)
2. [项目上下文](PROJECT_CONTEXT.md)
3. [文档地图](docs/README.md)
4. [当前任务](docs/ai/CURRENT_TASK.md)
5. [最近交接](docs/ai/HANDOFF.md)

不要依赖上一模型的会话记忆；以仓库代码、测试、正式文档和落盘任务状态为准。
```

- [ ] **Step 5: Add documentation governance to `AGENTS.md`**

Update Required Reading so `PROJECT_CONTEXT.md` and `docs/README.md` appear before task state. Add a `Documentation Governance` section with these normative rules:

```markdown
- `PROJECT_CONTEXT.md` is the stable root index; it must not copy dynamic task progress.
- `docs/README.md` is the only canonical documentation map.
- Update `CURRENT_TASK.md` when starting a task and `HANDOFF.md` at each verified phase, blocker, or model switch.
- Update `PROJECT_CONTEXT.md` and `docs/README.md` when project structure, commands, canonical direction, or formal-document status changes.
- Archive only with explicit replacement evidence and record every move in `docs/archive/README.md`.
- Review the documentation map and project memory snapshot every 31 days.
- Project memory is curated manually; no script may copy global memory automatically.
```

Add `bash scripts/ai/check-doc-governance.sh` to the infrastructure commands and add the new root/index files to the documented repository structure.

- [ ] **Step 6: Update `docs/ai/README.md` and `docs/ai/START_PROMPTS.md`**

In `docs/ai/README.md`:

- Add `PROJECT_CONTEXT.md`, `docs/README.md`, `docs/archive/`, `docs/knowledge/codex-memory/`, and `check-doc-governance.sh` to the responsibility map.
- Replace the recovery flow with the six-step canonical order from `PROJECT_CONTEXT.md`.
- Add the event-driven and 31-day review rules.
- State that memory snapshots are secondary and manually curated.

In `docs/ai/START_PROMPTS.md`:

- Add `PROJECT_CONTEXT.md` and `docs/README.md` to prompts 1, 2, 3, and 5.
- Make prompt 5 run `bash scripts/ai/check-doc-governance.sh`.
- Add a sixth prompt named `## 6. 定期文档治理复核` that checks actual structure, links, archive candidates, snapshot relevance, review dates, and then updates HANDOFF.

- [ ] **Step 7: Verify canonical navigation**

Run:

```bash
test -f PROJECT_CONTEXT.md
test -f docs/README.md
rg -n 'AGENTS\.md.*PROJECT_CONTEXT\.md.*docs/README\.md|PROJECT_CONTEXT\.md|docs/README\.md' README.md AGENTS.md docs/ai/README.md docs/ai/START_PROMPTS.md
git diff --check
```

Expected:

- both `test` commands pass;
- every collaboration entrypoint references the same root-first order;
- no whitespace errors.

- [ ] **Step 8: Review checkpoint**

Inspect only Task 1 files with `git diff -- README.md AGENTS.md PROJECT_CONTEXT.md docs/README.md docs/ai/README.md docs/ai/START_PROMPTS.md`. Do not commit unless the user has explicitly authorized commits.

---

### Task 2: Archive Only Explicitly Superseded Documents

**Files:**

- Create: `docs/archive/README.md`
- Move: `docs/spec-v1.md` → `docs/archive/2026-07-24-doc-governance/spec-v1.md`
- Move: `docs/architecture-iteration-v1.2.md` → `docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md`
- Modify: `docs/README.md`
- Modify: `AGENTS.md`
- Modify: active Markdown files with confirmed inbound references to the two old paths

**Interfaces:**

- Consumes: explicit v1 → v2 and v1.2 → v1.3 replacement evidence.
- Produces: archive manifest rows with original path, archived path, date, reason, and replacement.
- Produces: no active first-read route to an archived version.

- [ ] **Step 1: Capture the pre-move references**

Run:

```bash
rg -n 'docs/spec-v1\.md|spec-v1\.md|docs/architecture-iteration-v1\.2\.md|architecture-iteration-v1\.2\.md' . -g '*.md' -g '!docs/archive/**' -g '!.worktrees/**'
```

Expected: active references are visible, including the current `AGENTS.md` source-of-truth list.

- [ ] **Step 2: Create the archive manifest**

Create `docs/archive/README.md`:

```markdown
# Project Documentation Archive

Archived documents are retained for traceability and are not first-read context. Start with [PROJECT_CONTEXT](../../PROJECT_CONTEXT.md) and the [Documentation Map](../README.md).

## Archive Manifest

| Original Path | Archived Path | Date | Reason | Replacement |
| --- | --- | --- | --- | --- |
| `docs/spec-v1.md` | [spec-v1.md](2026-07-24-doc-governance/spec-v1.md) | 2026-07-24 | Superseded project specification | [spec-v2.md](../spec-v2.md) |
| `docs/architecture-iteration-v1.2.md` | [architecture-iteration-v1.2.md](2026-07-24-doc-governance/architecture-iteration-v1.2.md) | 2026-07-24 | Superseded architecture iteration | [architecture-iteration-v1.3.md](../architecture-iteration-v1.3.md) |

## Policy

- Archive only when replacement evidence is explicit.
- Move files; do not delete history.
- Update active inbound references to the replacement or this manifest.
- Keep unclear historical files in place and mark them `Historical Reference` or `Needs Review` in `docs/README.md`.
```

- [ ] **Step 3: Move the two documents with `apply_patch`**

Use two `*** Move to:` patches so Git preserves content history:

```text
docs/spec-v1.md
→ docs/archive/2026-07-24-doc-governance/spec-v1.md

docs/architecture-iteration-v1.2.md
→ docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md
```

Do not edit the archived contents.

- [ ] **Step 4: Update active references**

In `AGENTS.md`, remove both archived paths from the active Sources of Truth list and retain:

- `docs/spec-v2.md`
- `docs/architecture-iteration-v1.3.md`
- `docs/architecture-review-v1.md`
- `docs/cross-renderer-decisions.md`
- Card OS normative docs and `docs/decisions/`

For every additional active reference reported in Step 1:

- route architecture readers to the replacement;
- route historical provenance readers to `docs/archive/README.md`;
- leave references inside archived files unchanged.

Append this section to `docs/README.md` after the historical-reference section:

```markdown
## Archive

[Archive Manifest](archive/README.md) records every superseded document, its retained location, reason, and replacement. Archived files are never first-read context.
```

- [ ] **Step 5: Verify archive integrity and active routing**

Run:

```bash
test ! -e docs/spec-v1.md
test ! -e docs/architecture-iteration-v1.2.md
test -f docs/archive/2026-07-24-doc-governance/spec-v1.md
test -f docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md
rg -n 'docs/spec-v1\.md|docs/architecture-iteration-v1\.2\.md' . -g '*.md' -g '!docs/archive/**' -g '!.worktrees/**'
git diff --check
```

Expected:

- both old paths are absent;
- both archive files exist;
- the final `rg` has no active first-read references; manifest prose using original paths is excluded by `!docs/archive/**`;
- no whitespace errors.

- [ ] **Step 6: Review checkpoint**

Inspect archive moves and references with `git diff --stat` and `git diff -- AGENTS.md docs/archive docs/README.md`. Do not commit without explicit authorization.

---

### Task 3: Add Curated Project Memory Snapshots

**Files:**

- Create: `docs/knowledge/codex-memory/README.md`
- Create: `docs/knowledge/codex-memory/memory_summary.md`
- Create: `docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md`
- Create: `docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md`
- Modify: `docs/README.md`

**Interfaces:**

- Consumes: curated lessons from the global Card OS deployment and local Skill installation memory summaries.
- Produces: secondary project-local retrieval material with no raw session log, credential, private configuration, or unrelated-project content.
- Produces: metadata keys `Last Reviewed` and `Next Review Due` in `YYYY-MM-DD`.

- [ ] **Step 1: Confirm the snapshot files do not exist**

Run:

```bash
test ! -e docs/knowledge/codex-memory/README.md
test ! -e docs/knowledge/codex-memory/memory_summary.md
```

Expected: both commands pass before snapshot creation.

- [ ] **Step 2: Create the snapshot index**

Create `docs/knowledge/codex-memory/README.md` with:

```markdown
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
```

- [ ] **Step 3: Create `memory_summary.md`**

Include only these durable rules:

```markdown
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
```

- [ ] **Step 4: Create the two curated rollout summaries**

The Card OS deployment summary must contain:

- rollout ID `019f50b0-b3a7-7670-83bf-6b261faf1f30`;
- date `2026-07-14`;
- task outcomes for backup, acceptance, and deployment assets;
- atomic no-replace backup publication;
- redirect refusal and compensating token cleanup;
- the unresolved-at-that-time `0600` runtime permission mismatch;
- repository-relative references only.

The local Skill installation summary must contain:

- rollout ID `019f3a8c-a5ab-7ba0-92f9-019e31593437`;
- date `2026-07-07`;
- archive inspection, `SKILL.md` name validation, destination conflict check, clean copy verification, and restart notice;
- generic `~/` paths only, with no local username.

Both files must start with a snapshot notice and must not include a raw session-log path.

- [ ] **Step 5: Add snapshot routing to `docs/README.md`**

Ensure the `Codex Memory Snapshots` section links the snapshot index and summarizes the two included subjects. Do not list the snapshot as a current implementation or architecture authority.

- [ ] **Step 6: Verify privacy and snapshot boundaries**

Run:

```bash
rg -n '/Users/|rollout_path:|BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9]{20,}' docs/knowledge/codex-memory
rg -n 'Last Reviewed: 2026-07-24|Next Review Due: 2026-08-24|secondary|snapshot|快照' docs/knowledge/codex-memory
git diff --check
```

Expected:

- the first command returns no matches;
- the second command confirms review metadata and snapshot semantics;
- no whitespace errors.

- [ ] **Step 7: Review checkpoint**

Inspect `git diff -- docs/knowledge/codex-memory docs/README.md`. Confirm only the two approved project subjects appear. Do not commit without explicit authorization.

---

### Task 4: Implement and Test the Read-Only Documentation Governance Checker

**Files:**

- Create: `scripts/ai/test-doc-governance.sh`
- Create: `scripts/ai/check-doc-governance.sh`
- Modify: `scripts/ai/check-agent-infra.sh`
- Modify: `scripts/ai/check-agent-state.sh`
- Modify: `package.json`
- Modify: `AGENTS.md`
- Modify: `docs/ai/README.md`

**Interfaces:**

- `check-doc-governance.sh` consumes optional `DOC_GOVERNANCE_ROOT` and `DOC_GOVERNANCE_TODAY`.
- It exits `1` when any required file or routed Markdown target is missing.
- It exits `0` and prints `RESULT: WARN` when `Next Review Due` is earlier than the supplied or current date.
- It exits `0` and prints `RESULT: PASS` when all checks are current.
- It never creates, modifies, moves, or refreshes project files.

- [ ] **Step 1: Write the fixture test first**

Create `scripts/ai/test-doc-governance.sh` with four isolated cases:

```bash
#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CHECKER="$ROOT/scripts/ai/check-doc-governance.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

pass_count=0
fail_count=0

pass() {
  printf 'PASS: %s\n' "$1"
  pass_count=$((pass_count + 1))
}

fail() {
  printf 'FAIL: %s\n' "$1"
  fail_count=$((fail_count + 1))
}

make_fixture() {
  fixture="$1"
  mkdir -p \
    "$fixture/docs/ai" \
    "$fixture/docs/archive/2026-07-24-doc-governance" \
    "$fixture/docs/knowledge/codex-memory/rollout-summaries"

  printf '# Agents\n' > "$fixture/AGENTS.md"
  printf '# Readme\n' > "$fixture/README.md"
  printf '%s\n' \
    '# Context' \
    '' \
    '- Last Reviewed: 2026-07-24' \
    '- Next Review Due: 2026-08-24' \
    '' \
    '[Docs](docs/README.md)' \
    > "$fixture/PROJECT_CONTEXT.md"
  printf '%s\n' \
    '# Docs' \
    '' \
    '- Last Reviewed: 2026-07-24' \
    '- Next Review Due: 2026-08-24' \
    '' \
    '[Task](ai/CURRENT_TASK.md)' \
    > "$fixture/docs/README.md"
  printf '# Task\n' > "$fixture/docs/ai/CURRENT_TASK.md"
  printf '# Handoff\n' > "$fixture/docs/ai/HANDOFF.md"
  printf '# Archive\n\n[Replacement](../spec-v2.md)\n' > "$fixture/docs/archive/README.md"
  printf '# Archived\n' > "$fixture/docs/archive/2026-07-24-doc-governance/spec-v1.md"
  printf '# Archived\n' > "$fixture/docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md"
  printf '# Spec v2\n' > "$fixture/docs/spec-v2.md"
  printf '# Architecture v1.3\n' > "$fixture/docs/architecture-iteration-v1.3.md"
  printf '%s\n' \
    '# Memory' \
    '' \
    '- Last Reviewed: 2026-07-24' \
    '- Next Review Due: 2026-08-24' \
    '' \
    '[Summary](memory_summary.md)' \
    > "$fixture/docs/knowledge/codex-memory/README.md"
  printf '# Summary\n' > "$fixture/docs/knowledge/codex-memory/memory_summary.md"
  printf '# Deployment\n' > "$fixture/docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md"
  printf '# Skill Install\n' > "$fixture/docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md"
}

run_checker() {
  fixture="$1"
  DOC_GOVERNANCE_ROOT="$fixture" \
    DOC_GOVERNANCE_TODAY="2026-07-24" \
    bash "$CHECKER" 2>&1
}

make_fixture "$TMP_ROOT/pass"
out="$(run_checker "$TMP_ROOT/pass")"
rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -q 'RESULT: PASS'; then
  pass "current fixture passes"
else
  fail "current fixture should pass"
fi

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/missing"
rm "$TMP_ROOT/missing/docs/README.md"
out="$(run_checker "$TMP_ROOT/missing")"
rc=$?
if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'missing required file'; then
  pass "missing required file fails"
else
  fail "missing required file should fail"
fi

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/broken"
printf '# Context\n\n[Missing](docs/missing.md)\n' > "$TMP_ROOT/broken/PROJECT_CONTEXT.md"
out="$(run_checker "$TMP_ROOT/broken")"
rc=$?
if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'broken Markdown link'; then
  pass "broken link fails"
else
  fail "broken link should fail"
fi

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/overdue"
printf '%s\n' \
  '# Memory' \
  '' \
  '- Last Reviewed: 2026-06-01' \
  '- Next Review Due: 2026-07-02' \
  '' \
  '[Summary](memory_summary.md)' \
  > "$TMP_ROOT/overdue/docs/knowledge/codex-memory/README.md"
out="$(run_checker "$TMP_ROOT/overdue")"
rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -q 'RESULT: WARN'; then
  pass "overdue review warns"
else
  fail "overdue review should warn without failing"
fi

printf '%s\n' "RESULT: pass=$pass_count fail=$fail_count"
[ "$fail_count" -eq 0 ]
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
bash scripts/ai/test-doc-governance.sh
```

Expected: non-zero exit because `scripts/ai/check-doc-governance.sh` does not exist.

- [ ] **Step 3: Implement the minimal checker**

Create `scripts/ai/check-doc-governance.sh`:

```bash
#!/usr/bin/env bash
set -u

ROOT="${DOC_GOVERNANCE_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
TODAY="${DOC_GOVERNANCE_TODAY:-$(date +%F)}"
cd "$ROOT" || exit 2

fail_count=0
warn_count=0

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; warn_count=$((warn_count + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; fail_count=$((fail_count + 1)); }

REQUIRED_FILES="
AGENTS.md
README.md
PROJECT_CONTEXT.md
docs/README.md
docs/ai/CURRENT_TASK.md
docs/ai/HANDOFF.md
docs/archive/README.md
docs/archive/2026-07-24-doc-governance/spec-v1.md
docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md
docs/spec-v2.md
docs/architecture-iteration-v1.3.md
docs/knowledge/codex-memory/README.md
docs/knowledge/codex-memory/memory_summary.md
docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md
docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md
"

for file in $REQUIRED_FILES; do
  if [ -f "$file" ]; then
    pass "required file exists: $file"
  else
    fail "missing required file: $file"
  fi
done

for superseded_path in \
  docs/spec-v1.md \
  docs/architecture-iteration-v1.2.md; do
  if [ -e "$superseded_path" ]; then
    fail "superseded document remains active: $superseded_path"
  else
    pass "superseded active path absent: $superseded_path"
  fi
done

check_links() {
  source="$1"
  [ -f "$source" ] || return 0
  base="$(dirname "$source")"

  while IFS= read -r match; do
    link="${match#](}"
    link="${link%%#*}"
    case "$link" in
      ""|http://*|https://*|mailto:*|\#*) continue ;;
    esac
    target="$base/$link"
    if [ -e "$target" ]; then
      pass "Markdown link exists: $source -> $link"
    else
      fail "broken Markdown link: $source -> $link"
    fi
  done < <(grep -oE '\]\([^)]+' "$source" || true)
}

for source in \
  README.md \
  PROJECT_CONTEXT.md \
  docs/README.md \
  docs/archive/README.md \
  docs/knowledge/codex-memory/README.md; do
  check_links "$source"
done

valid_iso_date() {
  value="$1"
  if date -j -f "%Y-%m-%d" "$value" "+%Y-%m-%d" >/dev/null 2>&1; then
    return 0
  fi
  date -d "$value" "+%Y-%m-%d" >/dev/null 2>&1
}

check_review_dates() {
  review_file="$1"
  [ -f "$review_file" ] || return 0

  last_reviewed="$(sed -n 's/^- Last Reviewed:[[:space:]]*//p' "$review_file" | head -1)"
  next_review_due="$(sed -n 's/^- Next Review Due:[[:space:]]*//p' "$review_file" | head -1)"

  if ! valid_iso_date "$last_reviewed"; then
    fail "invalid Last Reviewed date in $review_file: $last_reviewed"
  elif [ "$last_reviewed" \> "$TODAY" ]; then
    fail "Last Reviewed is in the future in $review_file: $last_reviewed"
  else
    pass "Last Reviewed date is valid in $review_file: $last_reviewed"
  fi

  if ! valid_iso_date "$next_review_due"; then
    fail "invalid Next Review Due date in $review_file: $next_review_due"
  elif [ "$next_review_due" \< "$last_reviewed" ] || [ "$next_review_due" = "$last_reviewed" ]; then
    fail "Next Review Due must be after Last Reviewed in $review_file"
  elif [ "$TODAY" \> "$next_review_due" ]; then
    warn "documentation review overdue for $review_file since $next_review_due"
  else
    pass "documentation review current for $review_file through $next_review_due"
  fi
}

for review_file in \
  PROJECT_CONTEXT.md \
  docs/README.md \
  docs/knowledge/codex-memory/README.md; do
  check_review_dates "$review_file"
done

echo "------------------------------------------------------------"
if [ "$fail_count" -gt 0 ]; then
  printf 'RESULT: FAIL (%d failure(s), %d warning(s))\n' "$fail_count" "$warn_count"
  exit 1
elif [ "$warn_count" -gt 0 ]; then
  printf 'RESULT: WARN (0 failures, %d warning(s))\n' "$warn_count"
  exit 0
else
  echo "RESULT: PASS"
  exit 0
fi
```

- [ ] **Step 4: Run the fixture tests and verify GREEN**

Run:

```bash
bash scripts/ai/test-doc-governance.sh
```

Expected:

```text
PASS: current fixture passes
PASS: missing required file fails
PASS: broken link fails
PASS: overdue review warns
RESULT: pass=4 fail=0
```

- [ ] **Step 5: Integrate the checker into Agent infrastructure**

Modify `scripts/ai/check-agent-infra.sh`:

- add all canonical indexes, archive manifest, memory index, checker, and fixture test to `REQUIRED_FILES`;
- add heading checks for:
  - `PROJECT_CONTEXT.md`: `# Kids Visual Learning Pack Project Context`, `## Required Read Order`;
  - `docs/README.md`: `# Project Documentation Map`, `## Canonical Current Docs`, `## Archive`;
  - `docs/archive/README.md`: `# Project Documentation Archive`, `## Archive Manifest`;
  - memory README: `# Codex Memory Snapshot`, `## Priority and Freshness`;
- add the new indexes and memory files to the infrastructure scan set;
- add the four curated memory files and the two new scripts to the secret-field mention allowlist, while keeping high-confidence value scanning active.

Modify `scripts/ai/check-agent-state.sh`:

```bash
run_step "check-agent-infra" bash scripts/ai/check-agent-infra.sh
run_step "check-doc-governance" bash scripts/ai/check-doc-governance.sh
run_step "check-task-state" bash scripts/ai/check-task-state.sh
run_step "check-handoff" bash scripts/ai/check-handoff.sh
run_step "git diff --check" git diff --check
```

Update its header comment from four steps to five steps.

- [ ] **Step 6: Add package scripts**

Add immediately after `check:agent-infra`:

```json
"check:doc-governance": "bash scripts/ai/check-doc-governance.sh",
"test:doc-governance": "bash scripts/ai/test-doc-governance.sh",
```

Keep the rest of `package.json` unchanged.

- [ ] **Step 7: Validate package JSON and live repository behavior**

Run:

```bash
node -e 'JSON.parse(require("fs").readFileSync("package.json", "utf8")); console.log("PASS: package.json")'
npm run test:doc-governance
npm run check:doc-governance
bash scripts/ai/check-agent-state.sh
```

Expected:

- package JSON parse prints `PASS: package.json`;
- fixture test reports four passes and zero failures;
- live governance check reports no failures;
- unified Agent state reports no failures; the existing authentication-field-name review warning may remain.

- [ ] **Step 8: Review checkpoint**

Inspect `git diff -- scripts/ai package.json AGENTS.md docs/ai/README.md`. Confirm all scripts are read-only except the test's temporary fixture creation under `mktemp -d`. Do not commit without explicit authorization.

---

### Task 5: Final Consistency Pass and Handoff

**Files:**

- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`
- Modify: `docs/README.md` only if the final inventory exposes a missing or misclassified path

**Interfaces:**

- Consumes: all deliverables from Tasks 1–4.
- Produces: a complete task record and exact next action for another model.

- [ ] **Step 1: Check the complete Markdown inventory**

Run:

```bash
rg --files -g '*.md' -g '!node_modules/**' -g '!.worktrees/**' | sort
rg -n '/Users/|rollout_path:' PROJECT_CONTEXT.md docs/README.md docs/archive docs/knowledge docs/ai/CURRENT_TASK.md docs/ai/HANDOFF.md
```

Expected:

- every project documentation category is routed from `docs/README.md` or intentionally described as a root/client adapter;
- the second command returns no matches in newly governed files.

- [ ] **Step 2: Run the complete verification set**

Run:

```bash
bash scripts/ai/test-doc-governance.sh
bash scripts/ai/check-doc-governance.sh
bash scripts/ai/check-agent-state.sh
bash scripts/ai/check-handoff.sh
git diff --check
git status --short
```

Expected:

- no command returns a failure;
- the known existing secret-field-name scan may produce a non-blocking warning;
- Git status includes only preserved prior work plus this task's documentation and infrastructure files.

- [ ] **Step 3: Update `docs/ai/CURRENT_TASK.md`**

Set:

- `Status: Done`;
- `Updated At: 2026-07-24`;
- every completed acceptance item to `[x]`;
- Current State to actual completed files and checks;
- Next Actions to user review and optional commit authorization;
- Verification Plan results to the commands actually run.

Do not claim a check passed unless its final command output passed.

- [ ] **Step 4: Update `docs/ai/HANDOFF.md` from actual state**

Record:

- current branch and base commit;
- exact changed files from `git status --short`, `git diff --stat`, and known untracked task files;
- archive moves and replacements;
- memory snapshot contents and freshness boundary;
- every verification command with `PASS`, `WARN`, or `FAIL`;
- the existing unrelated `19 !== 18` structure-test issue without claiming it was rerun;
- remaining work;
- Exact Next Action;
- recovery notes and no-commit status.

- [ ] **Step 5: Re-run shutdown checks after HANDOFF changes**

Run:

```bash
bash scripts/ai/check-handoff.sh
bash scripts/ai/check-agent-state.sh
git diff --check
git status --short
```

Expected:

- handoff passes;
- unified state has zero failures;
- no whitespace errors;
- final status is reported to the user.

- [ ] **Step 6: Final review checkpoint**

Review the complete task diff. Do not commit or stage files unless the user explicitly authorizes it.

---

## Final Acceptance Mapping

| Design Requirement | Implemented By |
| --- | --- |
| Stable root context | Task 1 |
| Canonical docs map | Task 1 |
| Cross-model reading order | Task 1 |
| Explicit archive with replacements | Task 2 |
| Curated project memory snapshot | Task 3 |
| Event-driven and 31-day governance | Tasks 1, 3, and 4 |
| Missing-link failure and overdue warning | Task 4 |
| No automatic global-memory sync | Tasks 1, 3, and 4 |
| Final task state and handoff | Task 5 |
| No business-code, CI, deployment, or user-config changes | Global Constraints and every review checkpoint |
