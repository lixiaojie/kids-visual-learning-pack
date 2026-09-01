# Current Task

## Metadata

- Updated At: 2026-09-01
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main`；server `knowledge-pipeline-v1` 只打生产 release，默认不 merge `main`
- Base Commit: 611598e

## Objective

**KNOW-03 知识源** 已在 server `knowledge-pipeline-v1` 提交 `7aaeb2b`（相对 `115377b`）。治理文档已提交 kids `611598e`。不标 DONE：未打生产 release、未 merge server `main`、未 reload、未种子新 library。不实施 WB-02。

## Background

- 用户要求结构覆盖多种可学习对象，并以七个典型主题做兼容验证；格温证明不能把 entity 七面套到虚构角色。
- 已落地：主机 + accuracy kernel + 按 form 的 coverage pack + 按 domain 的 overlay + 闭集 fact_type/axes 与 safety 门。

## Acceptance Criteria

- [x] 独立设计已写入 `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md`（完整知识源 + 插拔升级 + 七主题兼容套件）
- [x] `docs/README.md` 已挂上该设计
- [x] `docs/cognitive-card-os-roadmap.md` 含 KNOW-03 IN PROGRESS；WB-02 为 BACKLOG
- [x] `docs/cognitive-card-os-system-design.md` §11 指向 KNOW-03
- [x] 用户已审查重写后的书面 spec
- [x] 实施计划已写入 `docs/superpowers/plans/2026-09-01-entity-knowledge-coverage-implementation-plan.md`
- [x] 用户已选择执行方式（subagent / inline）且尚未开始 server 代码
- [x] server Task 1.1–3.3 按计划落地；focused 六模块 unittest 含 four_card_accept / age_language_adapter
- [x] Task 4.2：enforced 编译校验闭集 `fact_type` / `semantic_axes`、entity 面轴匹配、safety 类面非空 `safety_scope`（focused 六模块 121 通过）
- [x] 操作者审查并授权 commit；server `7aaeb2b80e591f348c54eb35fb18793e213c5122`
- [x] 未实施 WB-02；未改现网 library / 画廊
- [ ] KNOW-03 标 DONE（须操作者接受：不要求本刀打生产 release）

## In Scope

- server `.worktrees/cognitive-card-server-knowledge-core`：`coverage/` 插件与主机、classification 词表增量、authoring/validator 可选字段、七主题 authoring 夹具与 `tests/test_coverage_*.py`
- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md`
- `docs/superpowers/plans/2026-09-01-entity-knowledge-coverage-implementation-plan.md`
- `docs/superpowers/specs/2026-08-31-four-card-text-mature-projection-design.md`（仅 Parked）

## Out of Scope

- WB-02 / WB-03 / API-01 实现
- 本刀把所有 form pack 都切成 `required`（几何/时效会被误杀）
- 改 v1 FACT 键集、packet 契约
- 生产 library reload、merge server `main`、push、`outputs/`、`uv.lock`

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 兔子过门优先切开现有 Merck/RSPCA 命题。
- 工作区继续按 ADR-003 三角色。

## Verification Plan

- `bash scripts/ai/check-doc-governance.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-agent-state.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md`
- `docs/superpowers/plans/2026-09-01-entity-knowledge-coverage-implementation-plan.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/superpowers/specs/2026-08-31-classification-registry-design.md`
- `docs/superpowers/specs/2026-08-31-template-family-registry-design.md`
