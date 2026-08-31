# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: 9c39028

## Objective

把 3–4、5–6 的年龄与中文表达做成服务器侧适配；命题、确定性、安全边界不随年龄改写。

## Background

- RUN-01 已在本机 loopback 跑通；server 接线已本地提交 `c55f51b`。
- CONV-01 把 `canonical_claim` 临时写入 FACT `cn`/`en`。AGE-01 用 `age-language-adapter-v1` 替换该临时投影，已本地提交 `4e0ea52`。
- 活 server checkout：`.worktrees/cognitive-card-server-knowledge-core` @ `4e0ea52`。

## Acceptance Criteria

- [x] 带版本的服务器适配器覆盖 `age-3-4`、`age-5-6`；CN 与主年龄同配置；EN 为 `beginner`
- [x] 年龄只改变表达与任务负荷；同一 Knowledge Core 下命题 id、确定性、来源、安全边界跨年龄一致
- [x] 未注册的 canonical claim fail closed（`AGE_EXPRESSION_GAP`），不发明中文
- [x] COPY/描红/口头复述来自同语言知识表达的精确 span；`age-3-4` 抑制正式 COPY
- [x] 不改四对象 schema、不改 v1 FACT 键集、不扩 PORTAL、不 merge、不现网
- [x] focused 适配器 + converter 回归 PASS

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（AGE-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计条目）
- `docs/superpowers/specs/2026-08-31-age-language-adapter-design.md`
- `docs/superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md`（§5.2 临时 cn/en 指向 AGE-01）
- server `knowledge-pipeline-v1`：`age_language` 适配器、converter 接线、focused 测试

## Out of Scope

- 改四对象 schema / v1 FACT 键集 / AUTHOR-05 默认表
- PORTAL-01、RENDER-01、QA-01、PUBLISH-01、KNOW-01、AGE-02（8/10/15）
- 新增 age-3-4 模板族（TMPL-01）；age-3-4 不走 `assemble` / snapshot 模板解析
- 新增 HTTP 端点
- LLM 翻译
- merge `knowledge-pipeline-v1`、push、deploy、现网
- 提交 RUN-01 未提交接线、`uv.lock`、`outputs/`

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 适配器是投影，不是第五个治理对象；不改 Knowledge Core 字节。
- 安全边界原文不随年龄改写。
- 不覆盖 RUN-01 未提交接线（executor、compiled、compiler、knowledge_revision、joined-executor 测试）。

## Verification Plan

- server focused：`tests.test_age_language_adapter` + `tests.test_four_card_converter` 27 项 PASS；pipeline 回归 83 项 PASS
- 完整 suite 561 项，2 项既有 real-uvicorn 502
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/cognitive-card-os-system-design.md` §7
- `docs/superpowers/specs/2026-08-31-age-language-adapter-design.md`
- `docs/cognitive-card-os-roadmap.md` AGE-01
