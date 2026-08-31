# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: c5154c3

## Objective

把 ACCEPT-01 兔子端到端跑通：正式输入（兔子、深圳、age-5-6、中英、打印版）经四对象 / library current / 转换 / 确定性锁定 / 四卡 PNG / A4 PDF / 机器 QA / 人工复核 / 不可变 package；本机可查看同一版本。不扩 PORTAL，不要求第二台电脑，不 merge、不现网。

## Background

- PUBLISH-01 已在 `knowledge-pipeline-v1` 本地提交 `7a127b4`。ACCEPT-01 已本地提交 `10b14c8`。
- AUTHOR-02 真实兔子夹具与 AGE-01 登记表覆盖 8 条真实命题；converter 请求含 Shenzhen。
- 本批打印路径用服务器确定性 lock assembler，不调用外部模型。

## Acceptance Criteria

- [x] 正式输入为兔子、深圳、`age-5-6`、双语、`print`；默认 `chaptered-guide` 必须先显式 `four-card` 才转换
- [x] 全链路写出四页 PNG、A4 PDF、QA 批准报告、不可变 package revision；current 指向该 revision
- [x] 本机静态页可打开同一 `content_lock_sha256` 的知识浏览与 package 产物
- [x] 不改 Knowledge Core 字节；不扩 PORTAL、不新增公网 HTTP、不 merge、不现网
- [x] focused accept 测试 PASS

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（ACCEPT-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计/证据条目）
- `docs/superpowers/specs/2026-08-31-rabbit-end-to-end-acceptance-design.md`
- `docs/cognitive-card-os-accept-01-evidence.md`
- server `knowledge-pipeline-v1`：`four_card_lock`、`four_card_accept`、focused 测试

## Out of Scope

- 改四对象 schema / v1 FACT 键集 / AUTHOR-05 默认表
- 完整 `production-record-v1` 生成器、高视觉素材、LLM
- PORTAL-01、KNOW-01、TMPL-01、AGE-02、ACCEPT-02、SKILL-03
- 接线 subscriber `JobState` / 新增公网 HTTP
- 合入 `e78c2fa`、package-v5 客户端、恐龙 visual vocabulary
- merge `knowledge-pipeline-v1`、push、deploy、现网
- 提交 `uv.lock`、`outputs/`

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- Package 与锁定记录都是 Artifact / 投影，不是第五个治理对象。
- 本机 `file://` 或 loopback 查看不等于公网门户。
- 不覆盖 server 未跟踪的 `uv.lock`。
- 不改 AUTHOR-02 真实兔子夹具文件；four-card family 只在运行时覆盖。

## Verification Plan

- server focused：`tests.test_four_card_lock` + `tests.test_four_card_accept` 9 项 PASS
- pipeline 回归：118 项 PASS
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/superpowers/specs/2026-08-31-rabbit-end-to-end-acceptance-design.md`
- `docs/cognitive-card-os-accept-01-evidence.md`
- `docs/cognitive-card-os-roadmap.md` ACCEPT-01
