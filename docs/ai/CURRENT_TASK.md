# Current Task

## Metadata

- Updated At: 2026-09-08
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main` @ `94b4a55`；server `knowledge-pipeline-v1` @ `a0c8081`
- Base Commit: 94b4a55

## Objective

实施 PUBLISH-02：已锁定（QA `approved`）的带图投影显式上架本机画廊。新函数 `publish_locked_projection` 只调 `publish_approved`；包形状守 PUBLISH-01；有 media-plan pointer 时封掉旧一刀 `publish_from_artifact` /「批准并上架」。不改身份算法。不改 PORTAL。不接图像 API。不 merge/push/release。不标 `DONE`。

## Background

操作者批准 PUBLISH-02 spec。实施计划已落盘。前四步已本地提交：API-01-R1/R2 `4f76aca`，GRAPH/FORM/FREEZE `28ec476`，IMG-03 `629144c`。竖切顺序仍是 R1 → R2 → GRAPH+FORM+FREEZE → IMG-03 投影锁定 → **本刀**。server `knowledge-pipeline-v1` @ `a0c8081` 已本地提交（`publish_locked_projection`、封旧路、HTTP/ops、单测）。Tasks 1–3 审查 PASS。combined focused 263 ran / 261 ok / 2 FAIL（已知 ops mapping-lock `LEGEND_ROLE_MISSING`）。现网应用仍 `7aaeb2b`。不 merge/push/release。不标 `DONE`。

## Acceptance Criteria

- [x] spec 操作者 Approved `docs/superpowers/specs/2026-09-07-operator-locked-projection-gallery-publish-design.md`
- [x] 实施计划落盘 `docs/superpowers/plans/2026-09-07-operator-locked-projection-gallery-publish-implementation-plan.md`
- [x] 无 media-plan pointer 时 `publish_from_artifact` / `artifact-publish` 与本刀之前相同
- [x] 有 pointer 时：旧一刀发布 409 `PUBLISH_LOCKED_PATH_REQUIRED`；新函数要求 frozen、未 stale、compose 身份一致、已 `approved`
- [x] 成功只调用 `publish_approved`；包内无 compose HTML / 节点 PNG；knowledge library current 指针不变
- [x] 缺节点 PNG 不失败；同身份幂等
- [x] PORTAL-01 下载允白与身份算法不变
- [x] 不 merge/push/release、不覆盖 `outputs/`、不提交 `uv.lock`
- [x] 不修 ops mapping-lock `LEGEND_ROLE_MISSING`
- [x] 不标 IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`

## In Scope

- server worktree `knowledge-pipeline-v1` under `.worktrees/cognitive-card-server-knowledge-core`（`publish_locked_projection`、封旧发布入口、HTTP/ops、单测）
- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-07-operator-locked-projection-gallery-publish-design.md`
- `docs/superpowers/plans/2026-09-07-operator-locked-projection-gallery-publish-implementation-plan.md`

## Out of Scope

- 改 PUBLISH-01 身份算法、改 PORTAL-01 允白/详情 HTML
- 把 compose HTML / 节点 PNG 写入 package
- OpenAI / 图像 API、Skill claim、canvas 图谱
- 改 `lock_mapping`、改 Confirm current、改四对象 schema
- 打印铬、可交互运行时、新 ADR、KNOW-04 生产 library
- `outputs/`、server `uv.lock`
- 标 IMG-01 / IMG-02 / IMG-03 / COMPOSE-01 / LEGEND-01 / RENDER-02 / API-01 / API-01-R1 / API-01-R2 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`
- 修 ops mapping-lock `LEGEND_ROLE_MISSING`
- merge/push/release

## Constraints

- 不 merge/push/release。不含 `outputs/` 与 `uv.lock`。
- 无 media-plan 的既有 `publish_from_artifact` 不得改坏。
- 复用 `knowledge_layout.plan.is_stale`；禁止另写一套 stale 公式。
- 锁定路径继续禁止 `publish_approved`。
- ChatGPT 仍在人的浏览器里。

## Verification Plan

- spec Approved；实施计划已落盘
- server `a0c8081` 已本地提交；审查 PASS；combined focused 263 ran / 261 ok / 2 FAIL（已知 `LEGEND_ROLE_MISSING`）
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md` §5.4
- `docs/superpowers/specs/2026-09-07-operator-frozen-node-illustration-compose-lock-design.md`
- `docs/superpowers/specs/2026-08-31-immutable-package-publish-design.md`
- `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- `docs/superpowers/specs/2026-09-01-operator-mapping-artifact-publish-design.md`
- `docs/superpowers/plans/2026-09-07-operator-locked-projection-gallery-publish-implementation-plan.md`
