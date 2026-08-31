# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: 8c7048c

## Objective

把 KNOW-01 做成服务器权威分类注册表：`domain × form × subtype` 覆盖矩阵可机器校验；authoring 走受控分类并写入 Knowledge Scope；four-card convert / accept 不再依赖手填完整 `--request`。不阻塞已完成的 RUN-01，不 merge、不现网。

## Background

- ACCEPT-01 已在 `knowledge-pipeline-v1` 本地提交 `10b14c8`。分类此前只存在于四卡 `normalized_request` 和 core snapshot 内存档分类规范。
- AUTHOR-05 证明三次试产都没有 authoring 分类键；CONV-01 用 CLI `--request` 补 mammal 路由，直到本任务。
- 活 server 尖端现为 `.worktrees/cognitive-card-server-knowledge-core` @ `4083ce7`。

## Acceptance Criteria

- [x] 服务器版本化注册表覆盖全部受控 domain / form，且每个 domain 有 subtype 词表（含尚未出现首个对象的领域）
- [x] `domain × form × subtype` 覆盖矩阵可枚举；`general`、`other`、`CLASSIFICATION_REVIEW` 有边界夹具
- [x] authoring 必填受控 `classification`；自由文本绕过失败关闭
- [x] convert 可从 current 的 Scope 分类 + Plan 组装四卡 request；`--request` 变为可选且不得改写已登记分类
- [x] RUN-01 既有 `--request` 路径与 focused 测试仍 PASS
- [x] 不扩 PORTAL、不改 v1 FACT 键集、不 merge、不现网

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（KNOW-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计条目）
- `docs/superpowers/specs/2026-08-31-classification-registry-design.md`
- `docs/superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md`（`--request` 变为可选）
- `docs/superpowers/specs/2026-08-31-rabbit-end-to-end-acceptance-design.md`（分类改从 authoring 来）
- server `knowledge-pipeline-v1`：`classification` 注册表、authoring、validator、converter、accept、examples、focused 测试

## Out of Scope

- TMPL-01 模板族覆盖与 `TEMPLATE_GAP`
- 改 v1 FACT 键集 / generation-input 密封字段 / AUTHOR-05 默认 Projection 表
- PORTAL-01、AGE-02、ACCEPT-02、SKILL-03
- 接线新公网 HTTP
- merge `knowledge-pipeline-v1`、push、deploy、现网
- 提交 `uv.lock`、`outputs/`

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 分类注册表是服务器权威，不是第五个治理对象；写入 Knowledge Scope，不回写命题。
- 已有 RUN-01 `--request` 调用必须继续可用；分类冲突 fail closed，而不是让 CLI 覆盖 Scope。
- 不覆盖 server 未跟踪的 `uv.lock`。
- 不改 AUTHOR-02 真实来源与命题正文。

## Verification Plan

- server focused：`tests.test_classification_registry` + authoring / converter / accept 相关项 PASS
- pipeline 回归：与 ACCEPT-01 同组 focused 套件 PASS
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/cognitive-card-os-system-design.md` §3.2 / §4.1
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md` §14
- core snapshot 内存档分类规范（classification v2）
- `docs/superpowers/specs/2026-08-31-classification-registry-design.md`
