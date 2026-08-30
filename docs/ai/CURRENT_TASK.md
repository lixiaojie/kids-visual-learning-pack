# Current Task

## Metadata

- Updated At: 2026-08-30
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`；实现在 server `knowledge-pipeline-v1`
- Base Commit: kids `a85a785`；server `knowledge-pipeline-v1` @ `e9bfd22`（基线 `9e0c353`）

## Objective

实现 CONV-01：把已 publish 的 library current（且 Projection family 为显式 `four-card`）映射为现有接合 generation-input，使四卡 executor 能密封同一主题。处理 knowledge-core `source_id` 点号与 FACT `source_id` 不允许点号的映射。不写 Knowledge Core，不扩 PORTAL-01，不 merge server `main`，不现网。

## Background

- BROWSE-01 已提供确认点 1。接合 `assemble_from_knowledge_revision` 已存在，但 FACT 仍需人工拼装。
- Authoring 生成 `src.{topic}.{slug}`（允许点号）；v1 FACT `_SOURCE_ID` 为 `^[a-z][a-z0-9-]{1,63}$`。
- 兔子默认 chosen 是 `chaptered-guide`；four-card 须显式 `projection.family` 后重新 publish，才允许转换。

## Acceptance Criteria

- [x] 显式 four-card 的已 publish current 经 CLI `convert` 写出接合密封，并通过 `validate_joined_generation_input`
- [x] FACT `source_id` 不含点号；knowledge-core 磁盘上的 `source_id` 仍含点号（转换只读）
- [x] 默认 chaptered-guide 兔子 current 拒绝转换（`CONVERTER_FAMILY_NOT_FOUR_CARD`）
- [x] 无 current / unlist 拒绝转换；点号映射碰撞 fail closed
- [x] 仅改 Projection 时 Knowledge Core 摘要不变；接合 lock 可变
- [x] 不新增 SQLite 表、不改四对象 schema、不改 v1 FACT 合同、不生成 production-record 本体（那是 executor 输出）
- [x] 未 merge server `main`；未 push；未现网；未扩 PORTAL-01

## In Scope

Kids 治理：

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（CONV-01 状态与近期顺序）
- `docs/cognitive-card-os-system-design.md`（仅交付阶段第 5 条）
- `docs/superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md`
- `docs/README.md`（仅增加本设计一行）

Server 实现（cognitive-card-server worktree，分支 `knowledge-pipeline-v1`）：

- `source_id` 点号→连字符映射与 FACT 投影
- library current → 接合 generation-input
- CLI `convert`、focused 测试、server README 转换命令
- 不修改 `uv.lock`

## Out of Scope

- PORTAL-01、RENDER-01、QA-01、PUBLISH-01、浏览器会话、公网
- 写出 production-record 本体或跑现网 executor
- 新 Projection family；把分类写入 Knowledge Core（KNOW-01）
- 儿童中文 claim（AGE-01）；本批允许把 `canonical_claim` 同时填入 FACT `cn`/`en`
- merge server `main`；push；deploy；现网
- 改四对象 schema、v1 FACT 合同、ADR-001 packet 契约
- 提交 kids `outputs/`；覆盖用户未提交的无关文档

## Constraints

- 实现只落在 server `knowledge-pipeline-v1`；kids 只更新任务账本、设计、交接与交付阶段一句。
- 只转换 **current** 且 family 为 `four-card`；不从历史 revision 建执行密封。
- 分类 / 地点等 four-card request 由 CLI `--request` 提供，不从 Knowledge Core 发明。
- 不覆盖用户未提交修改；不 add `uv.lock`。

## Verification Plan

- server focused converter + library / browse / HTTP / projection-family / authoring / contract / generation-input / join 回归
- server 仍在 `knowledge-pipeline-v1`，未 merge `main`
- kids：`git diff --check`；`bash scripts/ai/check-handoff.sh`；`bash scripts/ai/check-task-state.sh`；`bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md`
- `docs/cognitive-card-os-roadmap.md`
