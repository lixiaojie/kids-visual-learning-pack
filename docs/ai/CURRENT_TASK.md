# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: bc1c07f

## Objective

把 PORTAL-01 做成已发布 Artifact 的只读画廊：列出 PUBLISH-01 catalog 的 current 包，提供四卡预览、PDF、manifest、来源、QA、摘要、版本历史与状态隔离。未授权用户看不到 owner-only、撤回或草稿。不做成知识 CMS，不替代 BROWSE-01，不把 Projection family 写进 Knowledge Core。不 merge、不现网。

## Background

- PUBLISH-01 已在 `knowledge-pipeline-v1` 本地提交 `7a127b4`：不可变 `revision-NNNN/`、current pointer、撤回保留历史。本机路径尚未映射为画廊。
- BROWSE-01（`e9bfd22`）是确认点 1：只读浏览 Knowledge Core 与 Projection 选择面。PORTAL-01 不得复用或替换该界面。
- ACCEPT-01 本机 `view/index.html` 只证明同一 lock，不是门户。
- ADR-004：PORTAL-01 与知识浏览职责分开，避免八层表单。

## Acceptance Criteria

- [x] CLI 对 catalog 写出静态画廊：current 包可看四卡、PDF、manifest、来源、QA、摘要与版本历史
- [x] 公开观众只看到 `visibility=public` 且有 current 的包；owner-only、撤回、草稿目录均不出现在公开列表与下载
- [x] 已发布 current 的文件可按稳定相对路径 / loopback URL 下载，字节与 catalog revision 一致
- [x] 画廊不写 Knowledge Core、不展示 Projection family 选择面、不提供知识编辑表单；BROWSE-01 CLI 行为不变
- [x] 既有 RUN-01 / KNOW-01 / TMPL-01 兔子路径与 focused 套件仍 PASS
- [x] 不 merge、不现网、不把 `/card-os/` 接到公网

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（PORTAL-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计条目）
- `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- server `knowledge-pipeline-v1`：catalog 列表/可见性、画廊 HTML/CLI、loopback 只读 GET 与下载、focused 测试

## Out of Scope

- 替换 BROWSE-01 或把知识浏览并进画廊
- 把 Projection family 或呈现方案写入 Knowledge Core
- 浏览器会话（AUTH-01）、SITE-01 / SITE-02、UPLOAD-01、MCP-01
- ACCEPT-02、AGE-02、SKILL-03
- 接线新公网 HTTP、绑定非 loopback、merge `knowledge-pipeline-v1`、push、deploy
- 提交 `uv.lock`、`outputs/`
- 修改不可变 core snapshot 字节、v1 FACT 键集、AUTHOR-05 默认表

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 画廊只消费 PUBLISH-01 catalog；知识权威仍是 library revision。
- `visibility` sidecar 不是第五个治理对象，不进入 `package_sha256`。
- 不覆盖 server 未跟踪的 `uv.lock`。
- 不覆盖 kids 未跟踪的 `outputs/`。

## Verification Plan

- server focused：portal HTML/CLI/隔离 + HTTP 公开/管理员下载 PASS
- pipeline 回归：与 TMPL-01 同组 focused 套件仍 PASS
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/cognitive-card-os-system-design.md` §11 / §12
- `docs/superpowers/specs/2026-08-31-immutable-package-publish-design.md`
- `docs/superpowers/specs/2026-08-30-knowledge-browse-projection-confirmation-design.md`
