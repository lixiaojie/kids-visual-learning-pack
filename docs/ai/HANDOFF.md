# Latest Handoff

## Metadata

- Updated At: 2026-08-31
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 8b07277
- Kids HEAD: 8b07277 `docs(card-os): record DEPLOY-02 production gallery landing`
- Server Branch: `knowledge-pipeline-v1` @ `fd696c2`（本批未改 server 代码；未 merge `main`）
- Server Worktree: `.worktrees/cognitive-card-server-knowledge-core`
- Server Generation-Input Worktree: `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Server main checkout: Documents Codex `cognitive-card-server` @ `c2a898c`（现网 `current` 已不指向它）
- Working Tree: 仅既有 `outputs/` 未跟踪
- Task Status: **Done（DEPLOY-02 现网已落地，文档已提交 `8b07277`）。** 未 merge server `main`；未 push kids。

## Summary

DEPLOY-02 已按硬顺序落地：从 `knowledge-pipeline-v1` @ `fd696c2` 打 release 并安装到 `127.0.0.1:8765`（画廊与 health/capabilities 并存）→ 种子 ACCEPT-01 `rabbit` public current → reload 仓库 Nginx snippet → `scripts/deploy.sh` 根 hub 与 13 个 stub。公网 `/card-os/` 是画廊，不再 307 到 capabilities。来源 schema 未改。

## Completed

- 本机 `npm run test:knowledge-entry`、`npm run test:deploy`、`npm run validate`、`npm run test:card-os-deploy`（95 项，需非沙箱）PASS
- release 归档 SHA-256 `6a3b8cd2bf336f65da454003ca135904613880af9410dfce2ce4b7eb295ca9ed`；ops commit `3432e83`
- 生产 `current` → `fd696c2a8cab5400a5d78669031a501390ab5318`；Uvicorn 仍只听回环
- 画廊列出 `rabbit`；PDF `200` 1728853 bytes
- Nginx snippet `d3d38a36…`；替换前备份 `…20260831T083618Z.pre-deploy-02.conf`
- 根 CTA 进画廊；`#dinosaurs` 打开冻结主题；`/kids/boards/dinosaurs/` 替代说明页非 404
- 运维记录第 10 节已追加；0.3.1 历史表未改写

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | 已提交 `8b07277`：DEPLOY-02 Done |
| kids | `docs/ai/HANDOFF.md` | 已提交 `8b07277`；本交接补记 SHA |
| kids | `docs/cognitive-card-os-roadmap.md` | 已提交 `8b07277`：DEPLOY-02 DONE |
| kids | `docs/cognitive-card-os-system-design.md` | 已提交 `8b07277`：§11 DEPLOY-02 Done |
| kids | `docs/operations/cognitive-card-server-deployment-2026-07-14.md` | 已提交 `8b07277`：第 10 节 |
| kids | SITE-02 实现 | 已提交 `44e0990`；记录 SHA `3432e83` |
| kids | `outputs/` | 既有未跟踪；不纳入 |
| server | （无代码） | 仅生产安装该已有 commit |

## Decisions Made

- 试点从管线分支打 release，未 merge server `main`。
- 空画廊不得切主 CTA；先上架 `rabbit` 再 rsync hub。
- 画廊 Nginx 回滚恢复 `pre-deploy-02` snippet，不跑过期的 §7.1 SHA 检查。
- 不补知识源字段。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `kids-visual-learning-pack` `main` @ `8b07277` | DEPLOY-02 文档已提交；`outputs/` 不纳入 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `fd696c2` | 本批未改代码；现网已安装该 commit |
| 现网对应 | `/opt/cognitive-card-server/current` → `fd696c2` | 旧 `c2a898c` 仍在 `releases/` |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `npm run test:knowledge-entry` | PASS | 执行会话开始时 |
| `npm run test:deploy` | PASS | |
| `npm run validate` | PASS | |
| `npm run test:card-os-deploy` | PASS | 95 项；沙箱内会因 `git init` hooks 失败 |
| 回环 health / capabilities / `GET /card-os/` | PASS | 标题 Published artifacts |
| 公网画廊 / PDF / skill manifest / 敏感 404 | PASS | admin portal 无 token 为 401 |
| `scripts/deploy.sh` | PASS | stub rsync 无 `--delete` |
| 浏览器：CTA、`#dinosaurs`、stub | PASS | |
| 第 4 节健康检查 | PASS | NRestarts=0；8765 仅回环；integrity ok |
| `git diff --check` | PASS | |
| 未 merge server `main` / 未 push kids | PASS | |
| `bash scripts/ai/check-handoff.sh` | PASS | |
| `bash scripts/ai/check-task-state.sh` | PASS | Status Done，验收项全勾选 |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交文档仍在。
- 文档地图 Last Reviewed `2026-07-24` / Next Review Due `2026-08-24` 已过期，属既有治理 WARN。
- 第 7.1 节 `ACTIVE_SNIPPET_SHA256=e8579a5…` 在 DEPLOY-02 之前就已漂移（Skill 注册表 snippet `f734b0e9…`）；画廊回滚用第 10.6 节备份。
- 生产 `docs/` 仍可能是 rsync 当时的 In Progress 任务稿，直到下次文档部署。

## Risks and Caveats

- 未授权把 `knowledge-pipeline-v1` merge 进 server `main`。
- `uv.lock` 与 `outputs/` 不要混入提交。
- 同 SHA release 再次安装会 `RELEASE_EXISTS`。
- 回滚 hub 必须跑 `node scripts/render-knowledge-entry.mjs --write-hub`。

## Remaining Work

1. 用户若要让 server `main` 与现网尖端一致，另开会话明确授权 merge。
2. thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。

## Exact Next Action

不要重做 DEPLOY-02。下一动作由用户选：提交本批文档、或授权 merge `knowledge-pipeline-v1` 到 server `main`、或处理后置项（`API-01` 自由编译、`MIG-03` 等）。不要绑 Uvicorn 到非 loopback。

## Recovery Notes

- kids：`kids-visual-learning-pack` `main` @ `8b07277`；仅 `outputs/` 未跟踪。
- 现网：`/opt/cognitive-card-server/current` → `fd696c2`。
- 任务：`docs/ai/CURRENT_TASK.md`（DEPLOY-02 Done）。
- 入口合同：`shared/knowledge-entry.json`（`activeMode=card-os`）
- 画廊回滚：运维记录 §10.6
- 入口回滚：`activeMode=parallel` → 生成器 → `scripts/deploy.sh`
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：ADR-002/003/004/005、SITE-01/SITE-02/PORTAL-01 设计、运维记录第 10 节。
