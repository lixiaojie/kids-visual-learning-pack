# Current Task

## Metadata

- Updated At: 2026-09-04
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main` @ `c32d4d2`；server `knowledge-pipeline-v1` @ `4f76aca`
- Base Commit: c32d4d2

## Objective

按计划实施 API-01-R2：同一 dinosaur-entity intent 显式 advance、完整提示词内嵌骨架、authoring 可 Confirm、image_suggestions 进 intent 旁路、return-framework 回到骨架。启用 KNOW-01 `paleontology + entity + fossil-animal`。不写 media-plan。不 merge/push/release。不标 `DONE`。server 已本地提交 `4f76aca`。

## Background

FLOW-01 Approved。操作者批准 R2 spec 并要求实施与 commit。串行 subagent 已跑完计划 Tasks 1–5。server `4f76aca` 已本地提交（不含 `uv.lock`）。

## Acceptance Criteria

- [x] R2 spec Approved `docs/superpowers/specs/2026-09-04-operator-complete-prompt-round-design.md`
- [x] 实施计划落盘 `docs/superpowers/plans/2026-09-04-operator-complete-prompt-round-implementation-plan.md`
- [x] Task 1：fossil-animal enabled + complete 模板 + `expand_complete_prompt`
- [x] Task 2：`parse_complete_reply` + suggestions sidecar
- [x] Task 3：advance / complete reply / return-framework / confirm；cat 路径保持
- [x] Task 4：HTTP/ops HTML；无 token 壳不含提示词
- [x] Task 5：kids 账本；不标 API-01 / API-01-R1 / FLOW-01 `DONE`
- [x] 不写 media-plan library 文件
- [x] 不 merge/push/release、不覆盖 `outputs/`、不提交 `uv.lock`

## In Scope

- server worktree `knowledge-pipeline-v1` under `.worktrees/cognitive-card-server-knowledge-core`（classification registry、compile 模块、ops HTTP/pages、http errors、compile/classification 单测）
- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-04-operator-complete-prompt-round-design.md`
- `docs/superpowers/plans/2026-09-04-operator-complete-prompt-round-implementation-plan.md`

## Out of Scope

- media-plan library 文件、GRAPH / FORM / FREEZE、生图、现网、merge/push/release
- 新 ADR、改四对象 schema、KNOW-04 生产 library
- 其他对象类型模板
- `outputs/`、server `uv.lock`
- 标 IMG-01 / COMPOSE-01 / LEGEND-01 / API-01 / API-01-R1 / IMG-02 / RENDER-02 / FLOW-01 `DONE`
- 修 ops mapping-lock `LEGEND_ROLE_MISSING`
- 回退未提交的 API-01-R1 server 改动

## Constraints

- 不 merge/push/release。未要求不 commit。计划默认不 commit。
- 不覆盖未提交 `outputs/`。不提交 server `uv.lock`。
- 省略 `object_type` 的既有编译路径不得改坏。

## Verification Plan

- server worktree combined focused gate（classification + compile + compile HTTP + ops HTTP + auth）：已跑；新测通过；2 已知 `LEGEND_ROLE_MISSING` 未修
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-04-operator-complete-prompt-round-design.md`
- `docs/superpowers/plans/2026-09-04-operator-complete-prompt-round-implementation-plan.md`
- `docs/superpowers/specs/2026-09-04-operator-framework-prompt-round-design.md`
- `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md`
