# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: 16e16f8

## Objective

把 TMPL-01 做成服务器权威模板注册表：相同主路由得到稳定四页骨架；缺口返回 `TEMPLATE_GAP`，不静默套用错误模板。为每个已启用 family 配置至少两个对象夹具。不 merge、不现网。

## Background

- KNOW-01 已在 `knowledge-pipeline-v1` 本地提交 `4083ce7`。分类 `gap` 单元格允许登记，但模板解析仍可能落到 snapshot 受控 fallback。
- Snapshot 已有哺乳动物精确族（3–4 / 5–6）与恐龙 v2，以及 `domain_form_families.json` 的 domain/form 紧凑族。
- ACCEPT-02 依赖本任务：第二个哺乳动物必须解析为同一模板族和固定骨架。

## Acceptance Criteria

- [x] 服务器版本化模板注册表覆盖全部已声明 four-card family（精确族 + 紧凑族），并记录固定四页骨架、槽位、年龄/语言适配、结构指纹与兼容/回滚矩阵
- [x] 相同主路由（domain × form × subtype × age × 语言）得到同一骨架；跨对象夹具每个已启用 family 至少两个对象
- [x] 无注册路由返回 `TEMPLATE_GAP`；次领域/次形态只能激活已声明模块，否则 `INVALID_SECONDARY_MODULE`
- [x] convert 在密封前走注册表；`gap` 分类不再静默套用 generic fallback
- [x] 既有 RUN-01 / KNOW-01 兔子 `--request` 与无 `--request` 路径仍 PASS
- [x] 不扩 PORTAL、不改 v1 FACT 键集、不改 snapshot 字节、不 merge、不现网

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（TMPL-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计条目）
- `docs/superpowers/specs/2026-08-31-template-family-registry-design.md`
- `docs/superpowers/specs/2026-08-31-classification-registry-design.md`（指向 TMPL-01 门禁）
- server `knowledge-pipeline-v1`：`templates` 注册表、resolve、converter 门禁、跨对象夹具、focused 测试

## Out of Scope

- ACCEPT-02 第二个哺乳动物完整试产
- 新增 age-3-4 以外的精确 family.json 到 snapshot
- 改 v1 FACT 键集 / generation-input 密封字段 / AUTHOR-05 默认 Projection 表
- PORTAL-01、AGE-02、SKILL-03
- 接线新公网 HTTP
- merge `knowledge-pipeline-v1`、push、deploy、现网
- 提交 `uv.lock`、`outputs/`
- 修改不可变 core snapshot 字节

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 模板注册表是服务器权威，不是第五个治理对象；不回写 Knowledge Core。
- 受控 fallback 只服务 family 自己的 `subtype_family`（如 `general`），不得把 `animal/bird` 等 gap 单元格悄悄映射到 generic。
- 不覆盖 server 未跟踪的 `uv.lock`。
- 不改 AUTHOR-02 真实来源与命题正文。

## Verification Plan

- server focused：`tests.test_template_registry` + authoring / converter / accept 相关项 PASS
- pipeline 回归：与 KNOW-01 同组 focused 套件 PASS
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/cognitive-card-os-system-design.md` §3.2 / §4.1 / §7.3
- `docs/superpowers/specs/2026-08-31-classification-registry-design.md`
- snapshot `references/template-routing.md` 与 `assets/templates/families/`
