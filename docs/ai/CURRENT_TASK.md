# Current Task

## Metadata

- Updated At: 2026-09-03
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main` @ `6401ea6`；server `knowledge-pipeline-v1` @ `8710914`（本地提交；未 push）
- Base Commit: 6401ea6

## Objective

IMG-02：spec Approved，实施计划已落盘。server `8710914` 已本地提交 Tasks 1.1–3.3。kids 文档一并提交。未 push、不标 DONE。RENDER-02 未开始。

## Background

LEGEND-01 已在 kids `1598e74` / SHA 记录 `6401ea6`、server `f9baf8f` 本地提交。IMG-02：IMG-01 isolate 主图并存；额外像素键可选；同一 illustration-intent；不经 mapping-lock。RENDER-02 不在本任务。

## Acceptance Criteria

- [x] spec 写入 `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md` 并标为 Approved（操作者审阅通过）
- [x] spec 收录文档地图
- [x] 系统总设计 §11 与路线图指向 IMG-02 本刀
- [x] 显式决定 IMG-01 单主图路径是否并存（并存；`hero.png` = `observe.isolate`）
- [x] 完成条件覆盖：无实例不请图、烧字失败、`learning_place` 不得画成栖息地
- [x] 实施计划落盘
- [x] 不覆盖未提交 `outputs/`
- [x] server 按计划实施并本地提交（`8710914`；未 push）
- [x] 本刀未开始 RENDER-02

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/README.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md`（只改后续消费面交叉引用，若需要）
- `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`
- `docs/superpowers/plans/2026-09-03-multi-view-wordless-assets-implementation-plan.md`

## Out of Scope

- RENDER-02 模块铬
- 改四对象顶层 schema、v1 FACT 键集、KNOW-03 七面 id
- 接图像 API / Skill claim / 生产 OCR
- merge / push / release / 现网
- `outputs/`、server `uv.lock`
- 标 IMG-01 / COMPOSE-01 / LEGEND-01 / API-01 / IMG-02 `DONE`
- 把 rabbit-composite mapping-lock 的 `LEGEND_ROLE_MISSING` 当成 IMG-02 缺陷去放宽图例门禁

## Constraints

- 不 merge/push/release。
- 不覆盖未提交 `outputs/`。
- 不把 server `uv.lock` 纳入提交。
- 不把「视法出齐」写成知识源准入。
- 不标 IMG-02 `DONE`（未生产）。

## Verification Plan

- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`
- `docs/superpowers/plans/2026-09-03-multi-view-wordless-assets-implementation-plan.md`
- `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md`
- `docs/superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md`
- `docs/cognitive-card-os-roadmap.md` § IMG-02
