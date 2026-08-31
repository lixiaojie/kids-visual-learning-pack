# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: 823eff4

## Objective

按锁定内容与 RENDER-01 排版产物做机器 QA；全部通过后才进入 `awaiting_review`。人工复核必须记录 actor、决策与审计。不改 Knowledge Core，不扩 PORTAL，不 merge、不现网。

## Background

- RUN-01 / AGE-01 / RENDER-01 / QA-01 已在 `knowledge-pipeline-v1` 本地提交（`c55f51b` / `4e0ea52` / `1ef6edc` / `37a5927`），未 merge、未现网。
- 路线图 QA-01 完成条件：机器 QA 通过后才进入 `awaiting_review`；人工复核有明确 actor、决策和审计记录。
- 抢救来源（ADR-001）：存档 production-record 验证器、双语绑定与 `audit-package` 离线审计为合同候选；其“人工复核”只是本地 receipt，须按服务器权威模型重建，不把客户端 receipt 当成复核。
- 活 server checkout：`.worktrees/cognitive-card-server-knowledge-core` @ `37a5927`。

## Acceptance Criteria

- [x] 机器 QA 消费内容锁与 RENDER-01 输出；复算锁、页序、COPY、来源、未知项、安全、排版摘要与未声明文件
- [x] 任一项机器失败则不得进入 `awaiting_review`
- [x] 人工复核仅在机器通过后可写；必须有非空 actor、`approve`/`reject` 决策，并追加审计事件
- [x] 复核不发布；不改 Knowledge Core 字节
- [x] 不扩 PORTAL、不新增 HTTP、不 merge、不现网
- [x] focused QA 测试 PASS

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（QA-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计条目）
- `docs/superpowers/specs/2026-08-31-strict-qa-human-review-design.md`
- server `knowledge-pipeline-v1`：`four_card_qa` 模块、CLI、focused 测试

## Out of Scope

- 改四对象 schema / v1 FACT 键集 / AUTHOR-05 默认表
- PORTAL-01、PUBLISH-01、KNOW-01、TMPL-01、AGE-02
- 接线 subscriber `JobState` / packet HTTP / SQLite 任务表
- 主观全量视觉观感验收、恐龙 visual vocabulary、package-v5 合入
- 新增 HTTP 端点
- merge `knowledge-pipeline-v1`、push、deploy、现网
- 提交 `uv.lock`、`outputs/`

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- QA 是门禁，不是第五个治理对象；不改 Knowledge Core 字节。
- 安全边界原文不随 QA 改写。
- 不覆盖 server 未跟踪的 `uv.lock`。

## Verification Plan

- server focused：`tests.test_four_card_qa` 12 项 PASS
- pipeline 回归：QA + renderer + AGE + converter + library/browse/HTTP library/joined/authoring 合计 97 项 PASS
- 完整 suite 584 项中 582 PASS；2 项既有 real-uvicorn 502
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/superpowers/specs/2026-08-31-locked-four-card-render-design.md`
- `docs/superpowers/specs/2026-08-31-age-language-adapter-design.md`
- `docs/cognitive-card-os-roadmap.md` QA-01
