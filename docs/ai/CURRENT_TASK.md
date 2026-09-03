# Current Task

## Metadata

- Updated At: 2026-09-03
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main` @ `1598e74`；server `knowledge-pipeline-v1` @ `f9baf8f`（本地提交；未 push）
- Base Commit: 1598e74

## Objective

LEGEND-01：server 已本地提交 `f9baf8f`；kids 文档对齐一并提交。未 push、未生产、不标 DONE。

## Background

投影图例约束编译与四卡映射的认知角色。IMG-02 / RENDER-02 不在本计划内。

## Acceptance Criteria

- [x] 路线图登记 `LEGEND-01`、`IMG-02`、`RENDER-02`
- [x] spec 写入并标为 Approved
- [x] spec 收录文档地图
- [x] 系统总设计 §11 指向新任务
- [x] 操作者审阅书面 spec（「继续」）
- [x] 实施计划落盘
- [x] 不覆盖未提交 `outputs/`
- [x] server 按计划实施并本地提交 `f9baf8f`

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/README.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md`
- `docs/superpowers/plans/2026-09-03-projection-legend-v1-implementation-plan.md`

## Out of Scope

- IMG-02 / RENDER-02 实施
- 改四对象顶层 schema、v1 FACT 键集、KNOW-03 七面 id
- merge / push / release / 现网
- `outputs/`、server `uv.lock`
- 标 IMG-01 / COMPOSE-01 / API-01 `DONE`

## Constraints

- 不 merge/push/release。
- 不覆盖未提交 `outputs/`。
- 不把 server `uv.lock` 纳入提交。

## Verification Plan

- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md`
- `docs/superpowers/plans/2026-09-03-projection-legend-v1-implementation-plan.md`
- `docs/cognitive-card-os-roadmap.md` § LEGEND-01
