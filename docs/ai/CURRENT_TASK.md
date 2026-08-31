# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: 608ef4c

## Objective

按已锁定内容做四卡排版与 A4 PDF。COPY 来自 AGE-01 `copy_plan`；不改 Knowledge Core，不扩 PORTAL，不 merge、不现网。

## Background

- RUN-01 / AGE-01 / RENDER-01 已在 `knowledge-pipeline-v1` 本地提交（`c55f51b` / `4e0ea52` / `1ef6edc`），未 merge、未现网。
- COPY 计划不进 generation-input；generate 不得另写 COPY。RENDER-01 必须调用 `copy_plan`（`source_card` = 知识卡文本来源，`action_card` = 观察卡落位）。
- 抢救来源（ADR-001）：存档分支受治理 renderer 的 A4/Pillow/断行/几何校验/CropBox PDF；不把客户端 workspace lock 或恐龙 family 钉死合入。
- 活 server checkout：`.worktrees/cognitive-card-server-knowledge-core` @ `1ef6edc`。

## Acceptance Criteria

- [x] 渲染器只消费内容锁与锁定卡片文本；不改 Knowledge Core 字节、不发明命题
- [x] 固定四页顺序 CN_OBS → EN_OBS → CN_KNOW → EN_KNOW；文本忠实 A4 300dpi PNG + 四页 PDF
- [x] 观察卡 COPY/描红来自 AGE-01 `copy_plan`，不采用 generate 写入的 COPY；span 可在同语言知识卡还原
- [x] 渲染输入与输出字节均有摘要；内容锁摘要写入报告
- [x] 图像轨可选且不得进入 COPY/描红/来源/安全等清场区；无资产时仍可出文本忠实包
- [x] 不扩 PORTAL、不改四对象 schema、不新增 HTTP、不 merge、不现网
- [x] focused renderer 测试 PASS

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（RENDER-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计条目）
- `docs/superpowers/specs/2026-08-31-locked-four-card-render-design.md`
- server `knowledge-pipeline-v1`：`four_card_render` 模块、CLI、focused 测试

## Out of Scope

- 改四对象 schema / v1 FACT 键集 / AUTHOR-05 默认表
- PORTAL-01、QA-01 全量视觉 QA、PUBLISH-01、KNOW-01、TMPL-01、AGE-02
- 把存档客户端 workspace lock / 恐龙-only family 钉死合入
- 新增 HTTP 端点
- merge `knowledge-pipeline-v1`、push、deploy、现网
- 提交 `uv.lock`、`outputs/`

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 渲染器是投影，不是第五个治理对象；不改 Knowledge Core 字节。
- 安全边界原文不随排版改写。
- 不覆盖 server 未跟踪的 `uv.lock`。

## Verification Plan

- server focused：`tests.test_four_card_render` 11 项 PASS
- AGE-01 / converter 回归：`tests.test_age_language_adapter` + `tests.test_four_card_converter`；与 library/browse/HTTP library/joined/authoring 合计 85 项 PASS
- 完整 suite 572 项，2 项既有 real-uvicorn 502
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/superpowers/specs/2026-08-31-age-language-adapter-design.md`
- `docs/superpowers/specs/2026-08-31-locked-four-card-render-design.md`
- `docs/cognitive-card-os-roadmap.md` RENDER-01
