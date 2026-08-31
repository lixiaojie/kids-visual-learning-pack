# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1` 只读（本批不改 server 代码）
- Base Commit: c2bae22

## Objective

把 SITE-01 做成 Card OS 替换 `kids-world` 的知识入口：先让 `/card-os/` 画廊与旧站并行可访问，再把根入口主 CTA 切到 Card OS。13 个旧主题按 MIG-01 C 级冻结，仍可从旧站打开。不 merge、不现网。SITE-02（旧 URL 映射与回滚开关）不在本批。

## Background

- PORTAL-01 已在 server `knowledge-pipeline-v1` @ `fd696c2` 提供 loopback 画廊 HTML；现网 Nginx 仍把精确 `/card-os/` 307 到 capabilities，非 API 子路径 catch-all 404。
- 根 `index.html` 目前自动跳进 `boards/kids-world/`。
- 用户本会话授权：SITE-01 先并行验收再切主入口；SITE-02 下一会话只做旧 URL 映射与回滚开关。
- MIG-01 已将 13 个现站知识主题定为 C 级重制；本批把该决定视为入口切换的冻结/归档决定，不等 MIG-03。

## Acceptance Criteria

- [x] 知识入口合同写明 `parallel` 与 `card-os` 两相；本批 `activeMode=card-os`
- [x] 根入口主 CTA 指向 `https://www.yutou.space/card-os/`；旧 `kids-world` 仍可从根入口作为冻结档案打开
- [x] 生产根入口不暴露 `spider-verse` / `paw-patrol`
- [x] Nginx snippet 把画廊 HTML 与 `/card-os/packages/` 代理到 loopback 应用；capabilities 仍在 `/card-os/api/v1/capabilities`；敏感非画廊路径仍 404
- [x] `kids-world` 首页标明知识主入口已迁走，主题页仍可打开
- [x] 既有 Card OS deploy 测试与知识入口测试 PASS
- [x] 不 merge server `main`、不 push、不现网、不改 uvicorn 绑定

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`
- `docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`（仅 SITE-01 待应用路由说明，不改写 0.3.1 历史证据表）
- `PROJECT_CONTEXT.md`
- `index.html`
- `shared/knowledge-entry.json`
- `shared/styles/home.css`
- `boards/kids-world/src/pages/HomePage.tsx`
- `boards/kids-world/src/styles/styles.css`
- `ops/cognitive-card-server/nginx/card-os.conf`
- `tests/test_card_os_deployment_assets.py`
- `scripts/knowledge-entry.test.mjs`
- `package.json`

## Out of Scope

- SITE-02：旧 hash/URL 映射、替代说明页、一次部署回滚开关的运维接线
- MIG-02 / MIG-03 主题重制或导入
- 替换 BROWSE-01、把 Projection family 写入 Knowledge Core
- AUTH-01 浏览器会话、UPLOAD-01、MCP-01、ACCEPT-02
- 修改不可变 core snapshot、v1 FACT 键集、AUTHOR-05 默认表
- merge `knowledge-pipeline-v1`、push、deploy、把服务绑到非 loopback
- 提交 `outputs/`、server `uv.lock`
- 改 `spider-verse` / `paw-patrol` 内容或把它们放进生产根入口

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 画廊仍只消费 PUBLISH-01 catalog；知识权威仍是 library revision。
- 生产根入口继续隐藏旧版主题馆链接（`scripts/check-dist.mjs`）。
- 现网 Nginx / kids rsync 本批不执行。

## Verification Plan

- `node scripts/knowledge-entry.test.mjs`
- `npm run test:card-os-deploy`
- `npm run validate`（涉及 `boards/kids-world` 与根入口）
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/decisions/ADR-004-single-operator-main-flow.md`
- `docs/cognitive-card-os-system-design.md` §11 / §12
- `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- `docs/cognitive-card-os-asset-migration-inventory.md`
- `ops/cognitive-card-server/nginx/card-os.conf`
