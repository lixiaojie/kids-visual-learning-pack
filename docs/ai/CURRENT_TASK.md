# Current Task

## Metadata

- Updated At: 2026-09-07
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main` @ `b022d73`；server `knowledge-pipeline-v1` @ `629144c`
- Base Commit: b022d73

## Objective

实施 IMG-03 + compose 锁定：仅对 frozen 且未 stale 的 `wordless-image` 节点导出无字提示词、人回填 PNG、缺槽不失败；compose 身份一致后以 QA-01 `approve` 锁定投影工作区。不写 PUBLISH-02。不接图像 API。不 merge/push/release。不标 `DONE`。

## Background

操作者结合 [进度核对](a1544cf9-3823-452d-8b5a-8bff28e60d6b) 授权第 4 步。前三步已本地提交：API-01-R1/R2 `4f76aca`，GRAPH/FORM/FREEZE `28ec476`。竖切顺序仍是 R1 → R2 → GRAPH+FORM+FREEZE → **本刀** → PUBLISH-02。SDD Tasks 1–4 已在 server worktree 本地提交 `629144c`；Task 5 只改 kids 账本。compose 锁定走 QA-01 `record_review`。现网应用仍 `7aaeb2b`。不标 `DONE`。

## Acceptance Criteria

- [x] spec 操作者 Approved `docs/superpowers/specs/2026-09-07-operator-frozen-node-illustration-compose-lock-design.md`
- [x] 实施计划落盘 `docs/superpowers/plans/2026-09-07-operator-frozen-node-illustration-compose-lock-implementation-plan.md`
- [x] 无 media-plan pointer 时 IMG-01 / IMG-02 / COMPOSE-01 行为与本刀之前相同
- [x] 有 pointer 时：节点扩词/回填、compose POST、投影锁定均要求 frozen 且 `is_stale=false`
- [x] 缺节点 PNG 不失败；观察卡才 `<img>`；知识卡无插图
- [x] 锁定 = QA-01 `approve`；不调用 `publish_approved`
- [ ] 对照旧剑龙卡只验收模块种类，不对像素
- [ ] 不 merge/push/release、不覆盖 `outputs/`、不提交 `uv.lock`
- [x] 不修 ops mapping-lock `LEGEND_ROLE_MISSING`
- [ ] 不标 IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`

## In Scope

- server worktree `knowledge-pipeline-v1` under `.worktrees/cognitive-card-server-knowledge-core`（illustration 节点槽、compose freeze 门禁、投影锁定、ops HTML、errors、单测）
- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-07-operator-frozen-node-illustration-compose-lock-design.md`
- `docs/superpowers/plans/2026-09-07-operator-frozen-node-illustration-compose-lock-implementation-plan.md`

## Out of Scope

- PUBLISH-02、画廊历史打开/下载、改 PUBLISH-01 身份算法
- OpenAI / 图像 API、Skill claim、canvas 图谱
- 改 `lock_mapping`、改 Confirm current、改四对象 schema
- 打印铬、可交互运行时、新 ADR、KNOW-04 生产 library
- `outputs/`、server `uv.lock`
- 标 IMG-01 / IMG-02 / IMG-03 / COMPOSE-01 / LEGEND-01 / RENDER-02 / API-01 / API-01-R1 / API-01-R2 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`
- 修 ops mapping-lock `LEGEND_ROLE_MISSING`
- merge/push/release

## Constraints

- 不 merge/push/release。不含 `outputs/` 与 `uv.lock`。
- 无 media-plan 的既有 isolate / compose / QA focused 路径不得改坏。
- 复用 `knowledge_layout.plan.is_stale`；禁止另写一套 stale 公式。
- ChatGPT 仍在人的浏览器里。

## Verification Plan

- spec 已 Approved；实施计划已落盘；SDD Tasks 1–5 已本地实施（不 commit）
- server worktree combined focused gate：221 ran / 2 FAIL（已知 ops mapping-lock `LEGEND_ROLE_MISSING`）
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md` §5.3
- `docs/superpowers/specs/2026-09-07-operator-layout-graph-form-freeze-design.md`
- `docs/superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md`
- `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`
- `docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`
- `docs/superpowers/specs/2026-09-04-legend-module-chrome-design.md`
- `docs/superpowers/specs/2026-08-31-strict-qa-human-review-design.md`
