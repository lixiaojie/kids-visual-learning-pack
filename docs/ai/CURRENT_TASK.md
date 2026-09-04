# Current Task

## Metadata

- Updated At: 2026-09-04
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main` @ `05dfeaa`；server `knowledge-pipeline-v1` @ `427bf89`（本地提交；未 push）
- Base Commit: 05dfeaa

## Objective

RENDER-02：图例模块铬 spec 已 Approved、实施计划已落盘；kids `05dfeaa`、server `427bf89` 已本地提交。空角色不画假框；清场区无插图；字仍由服务器排；无图 generate 仍可用。不 merge/push/release。不标 IMG-02 / LEGEND-01 / COMPOSE-01 / RENDER-02 `DONE`。

## Background

LEGEND-01 已在 kids `1598e74` / SHA 记录 `6401ea6`、server `f9baf8f` 本地提交。IMG-02 已在 kids `8c7c2d8` / SHA 记录 `4bb276f`、server `8710914` 本地提交。COMPOSE-01 仍只读 `hero.png`；额外 PNG 在 `views/`。旧 Skill 剑龙卡是模块种类标尺，不是整卡烧字合同。兔子 mapping-artifact 观察卡加主图带后 `look` 剩余约 117 px。

## Acceptance Criteria

- [x] spec 写入 `docs/superpowers/specs/2026-09-04-legend-module-chrome-design.md` 并标为 Approved（操作者审阅通过）
- [x] spec 收录文档地图
- [x] 系统总设计 §11 与路线图指向 RENDER-02 本刀
- [x] 显式决定铬画在观察卡、知识卡、或两者（HTML 两卡都画；打印 PNG 不变）
- [x] 完成条件覆盖：空模块不画假框、清场区无插图、既有无图 generate 仍可用
- [x] 三视/剖面/爆炸提示词划归 IMG，不在本刀
- [x] 实施计划落盘
- [x] 不覆盖未提交 `outputs/`
- [x] spec Approved；计划已落盘；kids `05dfeaa`、server `427bf89` 已本地提交
- [x] 不标 IMG-01 / COMPOSE-01 / LEGEND-01 / API-01 / IMG-02 / RENDER-02 `DONE`

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/README.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/superpowers/specs/2026-09-04-legend-module-chrome-design.md`
- `docs/superpowers/plans/2026-09-04-legend-module-chrome-implementation-plan.md`
- `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md`（只改后续消费面交叉引用，若需要）
- `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`（只改后续消费面交叉引用，若需要）
- `docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`（只改后续消费面交叉引用，若需要）

## Out of Scope

- 再改 server 代码（Tasks 1.1–3.2 已提交为 `427bf89`；本刀仅 kids 文档）
- 改四对象顶层 schema、v1 FACT 键集、KNOW-03 七面 id、ACCEPT-01 等分版式
- 用观感倒逼补 Knowledge Core 事实
- 退回整卡烧字；接图像 API / Skill claim / 生产 OCR
- merge / push / release / 现网
- `outputs/`、server `uv.lock`
- 标 IMG-01 / COMPOSE-01 / LEGEND-01 / API-01 / IMG-02 / RENDER-02 `DONE`

## Constraints

- 不 merge/push/release。
- 不覆盖未提交 `outputs/`。
- 不把 server `uv.lock` 纳入提交。
- 不改 ACCEPT-01 等分版式合同。
- 不把「视法出齐 / 模块出齐」写成知识源准入。
- 空角色跳过，禁止为填满画假框。
- 插图不得进入 `record` / `trace` / `copy` / `sources` / `safety` / `confusion` / `uncertain` / `blank`。
- 字由服务器排，不烧进图。
- 不标 RENDER-02 `DONE`（未生产）。

## Verification Plan

- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md`
- `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`
- `docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`
- `docs/superpowers/specs/2026-08-31-locked-four-card-render-design.md`
- `docs/superpowers/specs/2026-09-02-mapping-artifact-weighted-layout-design.md`
- `docs/cognitive-card-os-roadmap.md` § RENDER-02
