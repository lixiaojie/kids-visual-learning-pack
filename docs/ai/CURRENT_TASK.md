# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`；server `knowledge-pipeline-v1` 只打生产 release，默认不 merge `main`
- Base Commit: 3432e83

## Objective

做 **DEPLOY-02 现网落地试点**：把已本地完成的 PORTAL-01 画廊与 SITE-01/SITE-02 入口合同应用到 `www.yutou.space`，使单人能在公网看到同一版已发布包，并保留一次部署回滚。不补知识源 schema，不扩 PORTAL，不把自由概念编译或旧主题重制混入本批。

## Background

- 加长队列 RUN-01 → SITE-02 已在仓库完成本地交付。kids HEAD `3432e83` 记录 SITE-02（实现 `44e0990`）。server 尖端 `knowledge-pipeline-v1` @ `fd696c2`。现网仍是 `0.3.1` @ `c2a898c`，`/card-os/` 仍 307 到 capabilities。
- 用户 2026-08-31 选择：来源字段够用；先做现网落地试点，不先补知识源实现。
- 只 rsync 根 `index.html`、画廊仍停在 capabilities，会把家用入口指到空壳。顺序必须是：应用能同时提供画廊与既有 API → reload Nginx 画廊反代 → 至少一个公开包可列 → 再部署根入口与 stub。
- 试点允许从 `knowledge-pipeline-v1` 打不可变 release，不必先 merge server `main`。merge `main` 须执行会话另作明确授权。
- 本文件划定范围。SITE-02 已提交。release、reload、rsync 在执行会话按验收项做，不在起草步执行。

## Acceptance Criteria

- [x] SITE-02 已提交到 kids `main`（`44e0990` / `3432e83`）；后续提交仍不要纳入 `outputs/` 或 server `uv.lock`
- [x] 执行会话开始时本机 `npm run test:knowledge-entry`、`npm run test:deploy`、`npm run validate` 仍 PASS
- [x] 生产 Uvicorn 仍只听 `127.0.0.1:8765`；未把服务绑到非 loopback
- [x] 从 `knowledge-pipeline-v1` 打出的 release 在回环上同时提供：`GET /card-os/api/v1/health` `200`、`GET /card-os/api/v1/capabilities` `200`（协议仍为现网 Skill 可领取的版本）、PORTAL-01 公开画廊 HTML
- [x] 若上一条无法同时满足：停止，不 reload 把 `/card-os/` 从 capabilities 307 改走，不部署根 CTA；在 HANDOFF 记 blocker
- [x] 已按仓库 `ops/cognitive-card-server/nginx/card-os.conf` reload Nginx：`GET https://www.yutou.space/card-os/` 为画廊而非 capabilities 307；`/card-os/packages/` 可下载允许的包文件；`/card-os/api/v1/health` 与 capabilities 仍 200；`/card-os/skill/v1/` 不变；敏感非画廊路径仍 404
- [x] 公开画廊至少列出 1 个 `public` current 包（优先 ACCEPT-01 兔子打印包）后，才 rsync 根入口；空画廊不得把主 CTA 切到 Card OS
- [x] `scripts/deploy.sh` 部署根 hub 与 13 个 `boards/{slug}/` stub，rsync **不加** `--delete`；生产根 HTML 不含 `spider-verse` / `paw-patrol`；`activeMode` 保持 `card-os`
- [x] 现网抽查：根主 CTA 进画廊；短 hash（如恐龙主题）打开冻结主题；构建生成的独立路径替代说明页非 404
- [x] 回滚路径可执行：画廊 Nginx 恢复 DEPLOY-02 前 snippet 备份（见运维记录第 10 节）；入口按 `activeMode=parallel` → `node scripts/render-knowledge-entry.mjs --write-hub` → 一次 `scripts/deploy.sh`。不恢复 `http-equiv refresh`
- [x] 运维记录追加本批证据，不改写 0.3.1 历史证据表
- [x] 未 merge server `main`（除非执行会话另作明确授权）；未改四对象 schema、v1 FACT 键集、来源字段

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`（仅追加 DEPLOY-02 证据与步骤，不改写 0.3.1 表）
- `docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md`（仅现网落地引用，不改 ADR 决定）
- `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`
- `docs/superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md`
- `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- `ops/cognitive-card-server/nginx/card-os.conf`（优先原样应用；仅当与现网冲突时做最小修正）
- `scripts/deploy.sh`
- `scripts/render-knowledge-entry.mjs`
- `shared/knowledge-entry.json`
- `index.html`（仅经生成器写入，禁止手改与 JSON 漂移）
- `package.json`（`build:card-os-release` / 既有 deploy 脚本，不新增无关脚本）
- SITE-02 已在 `44e0990` 提交；本批不重做映射逻辑
- server：按 DEPLOY-01 门禁从 `knowledge-pipeline-v1` 构建/安装 release 与 catalog 种子；不改 Knowledge Core schema

## Out of Scope

- 补知识源字段、拆 `creator`、改 `source.kind` 词表、改四对象 exact-keys
- API-01 自由概念编译、AUTH-01 浏览器会话、UPLOAD-01、MCP-01
- AGE-02、ACCEPT-02、SKILL-03、OPS-02
- MIG-02 / MIG-03；把 13 个冻结主题做成 PUBLISH-01 package 或写入画廊
- 替换 BROWSE-01；把 Projection family 写入 Knowledge Core
- 修改不可变 core snapshot、v1 FACT 键集、AUTHOR-05 默认表
- 把 Uvicorn 绑到非 loopback；开放 8765 公网
- 提交 `outputs/`、server `uv.lock`
- 改 `spider-verse` / `paw-patrol` 内容或把它们放进生产根入口
- 默认 merge server `main` 或 push 远程 server 分支

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 画廊只消费 PUBLISH-01 catalog；知识权威仍是 library revision；根入口不链到 BROWSE-01。
- 现网 0.3.1 packet 领取/提交必须继续可用，直到验收证明新 release 的 `/card-os/api/` 兼容。
- `scripts/deploy.sh` 上传 stub 不得加 `--delete`。
- 回滚必须跑 hub 生成器；只改 `activeMode` JSON 会使 hub 漂移。
- 工作区继续按 ADR-003 三角色；kids 提交与 server release 分开，不混提交。
- catalog `registry_commit` 诚实性缺口不在本批「顺手修」。

## Verification Plan

- `npm run test:knowledge-entry`
- `npm run test:deploy`
- `npm run test:card-os-deploy`
- `npm run validate`
- `npm run build:card-os-release`（或运维记录中的等价 release 构建）仅在安装前
- 回环：`127.0.0.1:8765` health / capabilities / 画廊
- 现网：`https://www.yutou.space/card-os/`、`/card-os/api/v1/health`、`/card-os/api/v1/capabilities`、至少一个 package 下载路径、根 hub、一条旧 hash、一个 stub
- 运维记录第 4 节检查（API/Nginx/timer/回环/UFW）在 reload 后重跑
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/cognitive-card-os-roadmap.md` DEPLOY-02
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- `docs/superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md`
- `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`
- `docs/superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md`
- `ops/cognitive-card-server/nginx/card-os.conf`
- `docs/cognitive-card-os-accept-01-evidence.md`
