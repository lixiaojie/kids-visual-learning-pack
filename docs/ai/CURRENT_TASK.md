# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1`
- Base Commit: 83888dd

## Objective

把 QA-01 已 `approved` 的锁定四卡产物发布为不可原地修改的 package revision；撤回和替代只移动 current pointer，历史目录保留。不改 Knowledge Core，不扩 PORTAL，不 merge、不现网。

## Background

- QA-01 已在 `knowledge-pipeline-v1` 本地提交 `37a5927`；`approve` 不发布。
- 路线图 PUBLISH-01 完成条件：发布版本不可原地修改；撤回和替代保留历史关系。
- 抢救来源（ADR-001）：采用存档 package-v5 的不可变包、manifest 身份、撤回/替代历史合同；不把 `e78c2fa` 上传面、客户端打包器或恐龙词表钉死合入。
- 活 server checkout：`.worktrees/cognitive-card-server-knowledge-core` @ `7a127b4`。

## Acceptance Criteria

- [x] 只消费 QA-01 `approved` 报告与 RENDER-01 产物；复算锁、QA 摘要与渲染字节
- [x] 已存在的 package revision 目录不得覆盖；相同内容对 current 幂等
- [x] 撤回清空 current，历史 revision 仍在；替代写入新 revision 并记录 supersedes
- [x] 不改 Knowledge Core 字节；不扩 PORTAL、不新增 HTTP、不 merge、不现网
- [x] focused publish 测试 PASS

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`（PUBLISH-01 状态与更新记录）
- `docs/cognitive-card-os-system-design.md`（交付阶段）
- `docs/README.md`（新设计条目）
- `docs/superpowers/specs/2026-08-31-immutable-package-publish-design.md`
- server `knowledge-pipeline-v1`：`four_card_publish` 模块、CLI、focused 测试

## Out of Scope

- 改四对象 schema / v1 FACT 键集 / AUTHOR-05 默认表
- PORTAL-01、KNOW-01、TMPL-01、AGE-02、ACCEPT-01
- 接线 subscriber `JobState` / packet HTTP / SQLite 任务表
- 合入 `e78c2fa`、package-v5 客户端、恐龙 visual vocabulary
- 现网下载 URL、容量门禁、备份与部署硬化
- 新增 HTTP 端点
- merge `knowledge-pipeline-v1`、push、deploy、现网
- 提交 `uv.lock`、`outputs/`

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- Package 是 Artifact 层，不是第五个治理对象；不改 Knowledge Core 字节。
- 授权本机路径不等于公网下载；PORTAL-01 再挂 URL。
- 不覆盖 server 未跟踪的 `uv.lock`。

## Verification Plan

- server focused：`tests.test_four_card_publish` 12 项 PASS
- pipeline 回归：publish + QA + renderer + AGE + converter + library/browse/HTTP library/joined/authoring 合计 109 项 PASS
- 完整 suite 596 项中 594 PASS；2 项既有 real-uvicorn 502
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/superpowers/specs/2026-08-31-strict-qa-human-review-design.md`
- `docs/superpowers/specs/2026-08-31-locked-four-card-render-design.md`
- `docs/cognitive-card-os-roadmap.md` PUBLISH-01
