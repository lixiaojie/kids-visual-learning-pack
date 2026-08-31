# Latest Handoff

## Metadata

- Updated At: 2026-08-31
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 52963bb
- Kids HEAD: 52963bb `docs(ai): record SITE-01 kids commit SHA`
- Server Branch: `knowledge-pipeline-v1` @ `fd696c2`（本批未改）
- Server Worktree: `.worktrees/cognitive-card-server-knowledge-core` 现为 `knowledge-pipeline-v1`
- Server Generation-Input Worktree: `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Server main checkout: Documents Codex `cognitive-card-server` @ `c2a898c`
- Working Tree: 本提交后仅 `outputs/` 未跟踪
- Task Status: **Done（SITE-02 已本地提交）。** 未 merge server `main`；未 push；未现网。

## Summary

SITE-02 给 13 个冻结主题接上旧 URL 映射，并把根 hub 接到 `activeMode` 生成器。短 hash / 规范 hash / query 打开旧主题；`boards/{slug}/index.html` 是替代说明页（构建与 `deploy.sh` 生成，不提交 13 份手写 HTML）。`activeMode=parallel` 时 `renderHubHtml` 把主 CTA 交回旧站。默认仍是 `card-os`。未改 `/card-os/` Nginx。

## Completed

- 设计：`docs/superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md`
- 合同：`reservedPageHashes`、`legacyPathPattern`
- 根 hub 生成器与 `parallel` 回滚证明；`card-os` 生成结果与提交的 `index.html` 字节一致
- kids-world 短 hash 解析与入口说明随 `activeMode` 变化
- 构建/部署写入替代说明页；stub 上传不加 `--delete`
- 未 merge、未 push、未现网

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | 本提交：SITE-02 Done |
| kids | `docs/ai/HANDOFF.md` | 本提交：本交接 |
| kids | `docs/cognitive-card-os-roadmap.md` | 本提交：SITE-02 DONE |
| kids | `docs/cognitive-card-os-system-design.md` | 本提交：§11 / §12.3 |
| kids | `docs/README.md` | 本提交：SITE-02 设计条目 |
| kids | `docs/superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md` | 本提交 |
| kids | `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md` | 本提交：指向 SITE-02 设计 |
| kids | `docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md` | 本提交：回滚步骤 |
| kids | `docs/operations/cognitive-card-server-deployment-2026-07-14.md` | 本提交：一次部署回滚步骤 |
| kids | `shared/knowledge-entry.json` | 本提交：hash/路径合同字段 |
| kids | `scripts/knowledge-entry.mjs` | 本提交 |
| kids | `scripts/render-knowledge-entry.mjs` | 本提交 |
| kids | `scripts/knowledge-entry.test.mjs` | 本提交 |
| kids | `scripts/legacy-topic-route.test.ts` | 本提交 |
| kids | `scripts/build-static.sh` | 本提交：生成 stub |
| kids | `scripts/deploy.sh` | 本提交：生成并 rsync stub（无 `--delete`） |
| kids | `scripts/deploy.test.mjs` | 本提交 |
| kids | `scripts/check-dist.mjs` | 本提交：要求 13 个 stub |
| kids | `package.json` | 本提交：`render:knowledge-entry` |
| kids | `boards/kids-world/src/lib/legacy-topic-route.ts` | 本提交 |
| kids | `boards/kids-world/src/lib/knowledge-entry.ts` | 本提交 |
| kids | `boards/kids-world/src/hooks/use-hash-route.ts` | 本提交 |
| kids | `boards/kids-world/src/pages/HomePage.tsx` | 本提交 |
| kids | `boards/kids-world/src/pages/TopicPage.tsx` | 本提交 |
| kids | `boards/kids-world/src/components/home/KnowledgeEntryNotice.tsx` | 本提交 |
| kids | `boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx` | 本提交 |
| kids | `index.html` | 未改（生成器与现文件一致） |
| kids | `PROJECT_CONTEXT.md` | 未改 |
| kids | `shared/styles/home.css` | 未改 |
| kids | `outputs/` | 既有未跟踪；不纳入 |
| server | （无） | 本批未改；尖端仍 `fd696c2` |

## Decisions Made

- 独立路径 `boards/{slug}/index.html` 做替代说明页，不做即时自动跳转。
- SPA 短 hash `#dinosaurs` 与 `#topic/dinosaurs`、`?topic=` 直接打开冻结主题。
- `#worlds` / `#recent-observation` 仍是页内锚点。
- 回滚不恢复根入口 `http-equiv refresh`；只交换主 CTA。
- 不把 stub 提交为 13 份源 HTML；由构建/`deploy.sh` 生成。
- 不改 `/card-os/` Nginx。不 merge、不 push、不现网。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `kids-visual-learning-pack` `main` | SITE-02 本提交；另有 `outputs/` 未跟踪 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `fd696c2` | 本批未改；不 merge `main` |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；`/card-os/` 仍 307 到 capabilities |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `npm run test:knowledge-entry` | PASS | 含 hub 两相、13 slug 映射、stub 生成 |
| `npm run test:deploy` | PASS | stub 生成与无 `--delete` rsync |
| `npm run test:card-os-deploy` | PASS | 95 项（需非沙箱，因 release 测试 `git init`） |
| `npm run validate` | PASS | 含 `test:knowledge-entry` |
| 本机 hub `http://127.0.0.1:5173/index.html` | PASS | 主链 Card OS；档案链旧站 |
| 本机 `#dinosaurs` / `?topic=moon-phases` | PASS | 打开对应主题，并显示冻结说明 |
| 本机 `http://127.0.0.1:8766/boards/dinosaurs/index.html` | PASS | 替代说明页；预览 stub 已从 `boards/` 删除 |
| `git diff --check` | PASS | |
| `bash scripts/ai/check-handoff.sh` | WARN | 0 FAIL；本更新后 Base Commit 与 HEAD 对齐 |
| `bash scripts/ai/check-task-state.sh` | PASS | CURRENT_TASK 路径引用全部存在 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL 预期；既有 secret 字段名 WARN + 文档复核到期 |
| 未 merge server `main` / 未 push / 未现网 | PASS | server 尖端仍 `fd696c2` |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交文档仍在。
- 文档地图 Last Reviewed `2026-07-24` / Next Review Due `2026-08-24` 已过期，属既有治理 WARN。
- `/tmp/card-os-accept-01` 不是 git 产物；重启后需重跑 CLI。
- 现网 `/card-os/` 仍是 0.3.1 capabilities 307；仓库 snippet 尚未 reload。
- 浏览器未能点进替代说明页的「打开旧主题页」（MCP 在该步断开）；该 href 由测试覆盖为 `../kids-world/index.html#topic/{slug}`。
- 未构建 Vite 时，从静态服务器打开 `boards/kids-world/index.html` 只有壳；短 hash 行为由 Vite 与测试覆盖。

## Risks and Caveats

- 未授权不要 merge `knowledge-pipeline-v1`、不要 push/deploy。
- `uv.lock` 与 `outputs/` 不要混入提交。
- 现网顺序仍是：先应用 Nginx 画廊反代，再部署根入口。回滚到 `parallel` 不能替代该顺序。
- 回滚必须跑 `node scripts/render-knowledge-entry.mjs --write-hub`，只改 JSON 会使 hub 漂移；测试会拒绝漂移。
- `deploy.sh` 上传 stub 不得加 `--delete`，否则会删掉 `kids-world` 等兄弟目录。

## Remaining Work

1. 授权现网时：先 reload Nginx snippet，再 rsync 根入口与 stub。
2. thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。

## Exact Next Action

不要重做 SITE-02。授权现网时先 reload Nginx 画廊反代，再部署静态根入口与 `boards/{slug}/` stub。活 server 尖端仍为 `knowledge-pipeline-v1` @ `fd696c2`。队列 §5 编号 11 之后无下一强制切片；后置项须另立会话再授权。

## Recovery Notes

- kids：`kids-visual-learning-pack` `main`；SITE-02 本提交记录 kids SHA。
- 活 server：`knowledge-pipeline-v1` @ `fd696c2`；本批未改。
- 入口合同：`shared/knowledge-entry.json`
- 生成 hub：`node scripts/render-knowledge-entry.mjs --write-hub`
- 回滚：`activeMode=parallel` → 同上生成器 → `scripts/deploy.sh`
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：ADR-002/003/004/005、SITE-01/SITE-02 设计。
