# Latest Handoff

## Metadata

- Updated At: 2026-09-08
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: becaef3
- Kids HEAD: becaef3
- Server Branch: `knowledge-pipeline-v1` @ `a0c8081`
- Working Tree: kids 干净（`outputs/` 未跟踪）。server `a0c8081` 已本地提交；`uv.lock` 未跟踪。
- Task Status: **In Progress（PUBLISH-02 spec Approved；server `a0c8081` 已本地提交；不标 DONE）。**

## Summary

操作者要求 commit。server `knowledge-pipeline-v1` @ `a0c8081`：`publish_locked_projection`、有 pointer 时封旧一刀发布、HTTP/ops「上架画廊」。kids `becaef3` 记录 spec、计划与 SHA。combined focused 263 ran / 261 ok / 2 FAIL（已知 ops mapping-lock `LEGEND_ROLE_MISSING`）。现网应用仍 `7aaeb2b`。未 merge/push/release。不标 `DONE`。

## Completed

- spec Approved `docs/superpowers/specs/2026-09-07-operator-locked-projection-gallery-publish-design.md`
- 实施计划 `docs/superpowers/plans/2026-09-07-operator-locked-projection-gallery-publish-implementation-plan.md`
- server `a0c8081`：`publish_locked_projection`、有 pointer 时封 `publish_from_artifact` / `artifact-publish`、HTTP/ops「上架画廊」、compose overlay 后 `run_machine_qa` 例外；锁定仍只 `record_review`；发布不再 `record_review`
- Tasks 1–3 审查 PASS；整支审查 Ready to commit；combined focused 263 ran / 261 ok / 2 FAIL（已知 `LEGEND_ROLE_MISSING`）
- kids 账本记录 server `a0c8081`；PUBLISH-02 仍 `IN PROGRESS`

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | spec+plan+账本 | `becaef3` 已本地提交 |
| kids | `outputs/` | 未跟踪；未纳入 |
| server | `knowledge-pipeline-v1` @ `a0c8081` | 已本地提交 |
| server | `uv.lock` | 未跟踪；未纳入 |

## Decisions Made

- 画廊面守 PUBLISH-01：四页 PNG + PDF；compose HTML / 节点 PNG 留在 ops。
- 新 ops「上架画廊」；有 pointer 时 `publish_from_artifact` / `artifact-publish` 409 `PUBLISH_LOCKED_PATH_REQUIRED`。
- 新函数 `publish_locked_projection` 只调 `publish_approved`；不改身份算法；不改 PORTAL。
- compose 例外：overlay 后 `run_machine_qa`；锁定仍只 `record_review`；发布不再 `record_review`。
- 不 merge/push/release。不修 ops mapping-lock `LEGEND_ROLE_MISSING`。
- 不标 IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`。
- 不含 `uv.lock` 与 `outputs/`。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `main` @ `becaef3`；`outputs/` 未跟踪 | 不默认 push；不提交 `outputs/` |
| 知识管线 | `.worktrees/cognitive-card-server-knowledge-core` @ `a0c8081` | 不提交 `uv.lock`；不 merge/push |
| 本机验收 | 文档脚本 + server combined gate 263/261/2 | 未开 8765；现网仍 `7aaeb2b` |

## Verification Results

本回合 commit 前账本已按 `a0c8081` 改写。checker 在 kids 提交后复跑。

| Command / Check | Result | Notes |
| --- | --- | --- |
| `bash scripts/ai/check-task-state.sh` | PASS | 提交前；Status In Progress |
| `bash scripts/ai/check-handoff.sh` | PASS | 提交前；Branch `main`；Base Commit `becaef3` |
| `bash scripts/ai/check-doc-governance.sh` | WARN | 0 failures, 3 warning(s)；仅 Last Reviewed 过期（2026-07-24） |
| `git diff --check` | PASS | 无输出；exit 0 |
| server combined focused gate | 263 ran / 261 ok / 2 FAIL | 已知 ops mapping-lock `LEGEND_ROLE_MISSING`；commit 后未复跑 |

## Known Failures

- ops mapping-lock `LEGEND_ROLE_MISSING` 两测：`test_generate_keeps_current_and_publish_requires_actor`、`test_publish_refuses_stale_work_after_relock`。不要修。
- 文档地图 Last Reviewed 过期 WARN（2026-07-24）。与本次无关。
- 现网应用仍 `7aaeb2b`。与本次无关。

## Risks and Caveats

- IMG-03 对照旧剑龙卡只验收模块种类尚未做。
- 本机 8765 仍未走过恐龙 R1→R2→Confirm→layout→Freeze→请图→compose 锁定→上架。
- ChatGPT 仍在人这边；不接模型 API。
- GET artifact 只读 `media_plan` 布尔；禁止用 `get_layout` 探测 pointer（会建草稿）。
- spec §10「已上架」要 catalog 身份等于本次工作区；计划 Task 3 JS 用 portal GET 200。未在本刀改。

## Remaining Work

- spec §10 ops「已上架」身份比对是整支审查记的 follow-up；未改。
- 不 merge/push/release。不标 `DONE`。

## Exact Next Action

不要 merge/push/release。不要标 IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`。不要纳入 `uv.lock` 或 `outputs/`。

## Recovery Notes

- Spec：`docs/superpowers/specs/2026-09-07-operator-locked-projection-gallery-publish-design.md`
- Plan：`docs/superpowers/plans/2026-09-07-operator-locked-projection-gallery-publish-implementation-plan.md`
- Server worktree：`.worktrees/cognitive-card-server-knowledge-core` `knowledge-pipeline-v1` @ `a0c8081`
- Combined gate（PUBLISH-02）：263 ran / 261 ok / 2 FAIL（已知 ops mapping-lock）
- Whole-branch：Ready to commit；0 Critical；ops「已上架」身份启发式为 follow-up
- Production app still `7aaeb2b`
