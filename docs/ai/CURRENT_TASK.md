# Current Task

## Metadata

- Updated At: 2026-08-31
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`; server `knowledge-pipeline-v1` 只读（本批不改 server 代码）
- Base Commit: 44e0990

## Objective

把 SITE-02 做成旧 `kids-world` URL 映射与一次部署回滚开关：13 个冻结主题的 hash/query/独立路径不再静默 404，历史路径保留替代说明；把 `activeMode` 切回 `parallel` 并重新生成根入口后，一次部署即可回滚主 CTA。不 merge、不现网。

## Background

- SITE-01 已把根入口主 CTA 切到 Card OS，并在合同中保留 `parallel` 相，但未接线回滚，也未映射旧 hash（`#dinosaurs`）与 `topic-registry` 中的独立路径（`boards/{slug}/index.html`）。
- 路线图 SITE-02 完成条件：已索引旧链接无静默 404；可在一次部署内回滚入口切换。ADR-005 禁止把 MIG-03 重制并进本批。
- 用户本会话授权：只做旧 URL 映射与回滚开关。不 merge server `main`、不 push、不现网，除非本会话另作明确授权。

## Acceptance Criteria

- [x] 13 个冻结 slug 的 `#slug`、`#topic/{slug}`、`?topic=` 在旧站打开对应主题，不落到空白首页
- [x] `boards/{slug}/index.html` 为替代说明页（非 404），链到旧主题页与 Card OS 画廊
- [x] 根 hub 由 `shared/knowledge-entry.json` 的 `activeMode` 生成；`card-os` 与 `parallel` 两相的主 CTA 可测
- [x] 回滚步骤写入运维说明：改 `activeMode=parallel`、生成 hub、一次部署；本批默认仍为 `card-os`
- [x] 生产根入口仍不暴露 `spider-verse` / `paw-patrol`
- [x] 既有知识入口测试、Card OS deploy 测试与 validate 按改动范围 PASS
- [x] 不 merge server `main`、不 push、不现网、不改 uvicorn 绑定、不改 `/card-os/` Nginx 语义

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`
- `docs/superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md`
- `docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`（仅 SITE-02 回滚步骤，不改写 0.3.1 历史证据表）
- `PROJECT_CONTEXT.md`
- `index.html`
- `shared/knowledge-entry.json`
- `shared/styles/home.css`
- `scripts/knowledge-entry.mjs`
- `scripts/render-knowledge-entry.mjs`
- `scripts/knowledge-entry.test.mjs`
- `scripts/legacy-topic-route.test.ts`
- `scripts/build-static.sh`
- `scripts/deploy.sh`
- `scripts/deploy.test.mjs`
- `scripts/check-dist.mjs`
- `package.json`
- `boards/kids-world/src/lib/legacy-topic-route.ts`
- `boards/kids-world/src/lib/knowledge-entry.ts`
- `boards/kids-world/src/hooks/use-hash-route.ts`
- `boards/kids-world/src/pages/HomePage.tsx`
- `boards/kids-world/src/pages/TopicPage.tsx`
- `boards/kids-world/src/components/home/KnowledgeEntryNotice.tsx`
- `boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx`

## Out of Scope

- MIG-02 / MIG-03 主题重制或导入
- 把旧主题做成 PUBLISH-01 package 或写入画廊
- 替换 BROWSE-01、把 Projection family 写入 Knowledge Core
- AUTH-01 浏览器会话、UPLOAD-01、MCP-01、ACCEPT-02
- 修改不可变 core snapshot、v1 FACT 键集、AUTHOR-05 默认表
- 修改 `ops/cognitive-card-server/nginx/card-os.conf` 的 `/card-os/` 语义
- merge `knowledge-pipeline-v1`、push、deploy、把服务绑到非 loopback
- 提交 `outputs/`、server `uv.lock`
- 改 `spider-verse` / `paw-patrol` 内容或把它们放进生产根入口

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 画廊仍只消费 PUBLISH-01 catalog；知识权威仍是 library revision。
- 生产根入口继续隐藏旧版主题馆链接（`scripts/check-dist.mjs`）。
- 现网 Nginx / kids rsync 本批不执行。
- 回滚开关默认保持 `activeMode=card-os`；只证明切到 `parallel` 会交换主 CTA。

## Verification Plan

- `node scripts/knowledge-entry.test.mjs`
- `sucrase-node scripts/legacy-topic-route.test.ts`
- `npm run test:deploy`
- `npm run test:card-os-deploy`
- `npm run validate`（涉及 `boards/kids-world` 与根入口）
- 浏览器：旧 hash / 替代说明页 / 根 hub 主 CTA
- `git diff --check`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md`
- `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`
- `docs/superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md`
- `docs/cognitive-card-os-system-design.md` §11 / §12
- `docs/cognitive-card-os-roadmap.md` SITE-02
- `shared/knowledge-entry.json`
- `boards/kids-world/src/data/topic-registry.json`
