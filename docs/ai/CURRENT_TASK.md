# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main`；server `knowledge-pipeline-v1` 只打生产 release，默认不 merge `main`
- Base Commit: e8789a7

## Objective

做 **WB-01 令牌操作台只读知识源**：公网画廊保持 PORTAL-01；操作员用 admin token 浏览 AUTHOR-02 兔子知识源与 Projection 选择面。本地 server ops HTML/JSON 与 kids Nginx snippet 已实现、测试并通过提交。现网仍待：从 server `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd` 打不可变 release、种子 knowledge-library、reload Nginx。

## Background

- DEPLOY-02 已把 `/card-os/` 变成已发布四卡画廊。兔子观察卡接近空白；公众看不到知识源；不能选投影；也不能从 prompt 生产。用户确认产品面为 B：公网只陈列成品，生产放令牌操作台。
- 四刀都要做，顺序已锁定：看见知识源（WB-01）→ 四卡成熟视觉（WB-02）→ 选投影并生成上架（WB-03）→ 自由 prompt 编译（API-01）。
- BROWSE-01 本机 CLI 已完成，未接现网。本任务把它做成 `/card-os/ops/` 的 admin HTTP 面，并保证生产 library current 是章节导读知识源，不是四卡覆盖。

## Acceptance Criteria

- [x] 独立设计已写入 `docs/superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md`
- [x] `docs/README.md` 已挂上该设计
- [x] `docs/cognitive-card-os-roadmap.md` 总览与明细含 WB-01 / WB-02 / WB-03；§5 队列为这三项再加 API-01；API-01 已从「不要排进队列」移入第 4 项
- [x] `docs/cognitive-card-os-system-design.md` §11 指向 WB-01，状态仍以路线图为准
- [x] 用户已审查书面 spec（「没问题」后「执行吧」）；实施计划已写出
- [x] server `knowledge-pipeline-v1` @ `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd` 提供 `/card-os/ops/` 壳与 admin knowledge-library JSON；无 admin token 看不到命题正文（本地 unittest；未现网）
- [x] kids 仓库 Nginx snippet 已含 `/card-os/ops/` GET/HEAD 反代；Uvicorn 仍只听 `127.0.0.1:8765`；未 merge server `main`
- [ ] 生产知识库兔子 current 为 AUTHOR-02（chosen `chaptered-guide`，`four-card` discouraged）；画廊 ACCEPT-01 包摘要不变
- [ ] 生产 Nginx 已 reload `/card-os/ops/`；带 token 打开现网兔子详情可见 4 单元 / 8 命题 / 4 来源；不带 token 的公网画廊与 DEPLOY-02 一致

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md`
- spec 批准后的实施计划（`docs/superpowers/plans/`）
- spec 批准后：server `knowledge-pipeline-v1` 操作台 HTML/admin 适配器；`ops/cognitive-card-server/nginx/card-os.conf`；生产 knowledge-library 种子与运维记录追加

## Out of Scope

- WB-02 四卡高视觉、WB-03 选投影生成上架、API-01 自由概念编译的实现
- AUTH-01 浏览器会话、UPLOAD-01、MCP-01
- AGE-02、ACCEPT-02、SKILL-03、OPS-02
- MIG-02 / MIG-03
- 改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、ACCEPT-01 包字节
- 把 Projection family 写入 Knowledge Core
- 把 Uvicorn 绑到非 loopback；开放 8765 公网
- 提交 `outputs/`、server `uv.lock`
- 改公网画廊文案或根 CTA；在画廊加操作台链接
- 默认 merge server `main` 或 push 远程 server 分支

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新，不另建第二份待办。
- 画廊只消费 PUBLISH-01 catalog；知识权威仍是 library revision。
- 操作台 JSON 只接受 `admin` scope。
- 现网 Skill packet 领取/提交必须继续可用。
- 工作区继续按 ADR-003 三角色；kids 提交与 server release 分开。
- 未完成兔子知识库种子前不得 reload 把 `/card-os/ops/` 接到空库。

## Verification Plan

- `bash scripts/ai/check-doc-governance.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-agent-state.sh`
- `git diff --check`
- spec 批准并实现后：server focused 操作台测试；回环与公网无 token / 有 admin token 对照；画廊包摘要不变；`npm run test:card-os-deploy`（涉及 Nginx/release 时）

## Relevant References

- `docs/superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md`
- `docs/superpowers/plans/2026-08-31-operator-knowledge-workbench-implementation-plan.md`
- `docs/superpowers/specs/2026-08-30-knowledge-browse-projection-confirmation-design.md`
- `docs/superpowers/specs/2026-08-30-projection-family-selection-design.md`
- `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/cognitive-card-os-roadmap.md`
- `ops/cognitive-card-server/nginx/card-os.conf`
