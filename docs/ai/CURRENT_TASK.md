# Current Task

## Metadata

- Updated At: 2026-09-09
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main` @ `7bed28f`；server `knowledge-pipeline-v1` @ `7ff8369`
- Base Commit: 7bed28f

## Objective

PACK-01 已在 server `7ff8369` 与 kids `7bed28f` 本地提交。不 merge/push/release、不标 DONE。

## Background

Spec：`docs/superpowers/specs/2026-09-08-operator-pack-layout-dual-gallery-design.md`。
Plan：`docs/superpowers/plans/2026-09-08-operator-pack-layout-dual-gallery-implementation-plan.md`。
执行工位：`.worktrees/cognitive-card-server-knowledge-core`。不得还原该树上已有未提交对照表/compose 补丁。不得动 `uv.lock`。

## Acceptance Criteria

- [x] spec 与计划落盘
- [x] Task 1 catalog / GET draft / PATCH selected
- [x] Task 2 PATCH placement
- [x] Task 3 print sample + lock_pack_layout + compose-lock 409
- [x] Task 4 HTTP + ops pack
- [x] Task 5 numbered package + PORTAL + kids docs
- [ ] 不标 FLOW-01 / PUBLISH-02 / IMG-03 / PACK-01 `DONE`

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/README.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/superpowers/specs/2026-09-08-operator-pack-layout-dual-gallery-design.md`
- `docs/superpowers/plans/2026-09-08-operator-pack-layout-dual-gallery-implementation-plan.md`
- server worktree `.worktrees/cognitive-card-server-knowledge-core` 中计划 File map 所列路径（`knowledge_pack/`、`knowledge_library/store.py`、compose lock gate、publish/portal/ops/http、对应 tests）

## Out of Scope

- OpenAI / 图像 API、Skill claim
- 改四对象 schema；现网 catalog
- merge/push/release；git commit（除非操作者另说）
- `outputs/`、server `uv.lock`、`AGENTS.md`
- 还原 server 树上已有未提交补丁
- 修 ops mapping-lock `LEGEND_ROLE_MISSING`

## Constraints

- 子代理模型：`cursor-grok-4.6-high`（禁止 on-demand / composer-2.5-fast）。
- 不覆盖 `AGENTS.md` 未提交修改。
- 不把 admin token 写入聊天或仓库。

## Verification Plan

- 各任务计划内 unittest
- Task 5 后 combined focused gate
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-08-operator-pack-layout-dual-gallery-design.md`
- `docs/superpowers/plans/2026-09-08-operator-pack-layout-dual-gallery-implementation-plan.md`
