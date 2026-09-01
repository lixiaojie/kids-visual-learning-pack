# Current Task

## Metadata

- Updated At: 2026-09-01
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`；server `knowledge-pipeline-v1` @ `5c11880`
- Base Commit: 42b3522

## Objective

实施 **WB-02**：本机操作台选择 Projection family、锁定槽位映射 revision；不抢 knowledge current；不生成 PNG；不现网。

## Background

- 操作者批准 `docs/superpowers/specs/2026-09-01-operator-mapping-scheme-design.md`。
- 旧文字成熟 spec 仍 Parked。
- 现网应用仍为 `7aaeb2b`；画廊仍是 ACCEPT-01。本刀不安装新 release。

## Acceptance Criteria

- [x] 书面 spec 经操作者审查（批准实施）
- [x] 路线图 `WB-02` `DONE`（本机；完成条件对齐 spec §10）
- [x] 写出实施计划
- [x] server：`preview_mapping` / `lock_mapping` / mapping pointer / 安全登记 / ops HTTP+第三块
- [x] focused 测试 PASS（library mapping、safety GAP、ops 既有用例）
- [x] 未打 release、未 reload Nginx、未改画廊、未 merge server `main`、未 push

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-01-operator-mapping-scheme-design.md`
- `docs/superpowers/specs/2026-08-31-four-card-text-mature-projection-design.md`（保持 Parked）
- `docs/superpowers/plans/2026-09-01-operator-mapping-scheme-implementation-plan.md`
- server worktree `.worktrees/cognitive-card-server-knowledge-core` 上 `knowledge-pipeline-v1`：`age_language`、`knowledge_library`、`knowledge_ops`、`http`、对应 `tests/`

## Out of Scope

- CONV-01 / RENDER-01 / QA-01 / PUBLISH-01 / 生图 / 画廊上架（WB-03）
- 改命题（知识源更改）
- API-01、AGE-02
- 新打应用 release、reload Nginx、merge server `main`、push
- `outputs/`、server `uv.lock`
- 改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表

## Constraints

- Card OS 账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- ADR-003：kids 与 server 分开提交；不自动 commit。
- `lock_mapping` 不得调用会移动 current 的 `publish`。
- 不覆盖未提交的 `outputs/`。

## Verification Plan

- 在 server worktree：`python3 -m unittest tests.test_age_safety_expression tests.test_mapping_preview tests.test_knowledge_library_mapping tests.test_http_knowledge_ops tests.test_knowledge_library -v`
- `bash scripts/ai/check-doc-governance.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-01-operator-mapping-scheme-design.md`
- `docs/superpowers/plans/2026-09-01-operator-mapping-scheme-implementation-plan.md`
- `docs/superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md`
- `docs/superpowers/specs/2026-08-30-knowledge-library-revision-current-design.md`
- `docs/superpowers/specs/2026-08-30-projection-family-selection-design.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/cognitive-card-os-roadmap.md`
