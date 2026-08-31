# Latest Handoff

## Metadata

- Updated At: 2026-08-31
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: c2bae22
- Kids HEAD: c2bae22 `feat(card-os): switch knowledge home from kids-world to the Card OS gallery`
- Server Branch: `knowledge-pipeline-v1` @ `fd696c2`（本批未改）
- Server Worktree: `.worktrees/cognitive-card-server-knowledge-core` 现为 `knowledge-pipeline-v1`
- Server Generation-Input Worktree: `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Server main checkout: Documents Codex `cognitive-card-server` @ `c2a898c`
- Working Tree: 本提交后仅 `outputs/` 未跟踪；server 仅 `uv.lock` 未跟踪
- Task Status: **Done（SITE-01 已本地提交）。** 未 merge server `main`；未 push；未现网应用 Nginx 或静态根入口。

## Summary

SITE-01 把知识主 CTA 从 `kids-world` 切到 Card OS 画廊，同时保留旧站为冻结档案。根 `index.html` 不再自动跳进旧站；Nginx snippet 把 `/card-os/` 与 `/card-os/packages/` GET 反代到 loopback 应用。13 个现站主题按 ADR-005 视为 C 级冻结，不等 MIG-03。SITE-02（旧 URL 映射与回滚开关）未做。

## Completed

- 设计：`docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`
- 决策：`docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md`
- 入口合同：`shared/knowledge-entry.json` `activeMode=card-os`
- 根 hub、kids-world 冻结说明、Nginx 画廊反代与测试
- 未 merge、未 push、未现网

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | 本提交：SITE-01 Done |
| kids | `docs/ai/HANDOFF.md` | 本提交：本交接 |
| kids | `docs/cognitive-card-os-roadmap.md` | 本提交：SITE-01 DONE |
| kids | `docs/cognitive-card-os-system-design.md` | 本提交：§11 / §12.3 |
| kids | `docs/README.md` | 本提交：设计与 ADR 条目 |
| kids | `PROJECT_CONTEXT.md` | 本提交：ADR-005 |
| kids | `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md` | 本提交 |
| kids | `docs/decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md` | 本提交 |
| kids | `docs/operations/cognitive-card-server-deployment-2026-07-14.md` | 本提交：待应用路由说明 |
| kids | `index.html` | 本提交 |
| kids | `shared/knowledge-entry.json` | 本提交 |
| kids | `shared/styles/home.css` | 本提交 |
| kids | `boards/kids-world/src/pages/HomePage.tsx` | 本提交 |
| kids | `boards/kids-world/src/styles/styles.css` | 本提交 |
| kids | `ops/cognitive-card-server/nginx/card-os.conf` | 本提交 |
| kids | `tests/test_card_os_deployment_assets.py` | 本提交 |
| kids | `scripts/knowledge-entry.test.mjs` | 本提交 |
| kids | `package.json` | 本提交：`test:knowledge-entry` |
| kids | `outputs/` | 未跟踪；不纳入 |
| server | （无） | 本批未改；尖端仍 `fd696c2` |

## Decisions Made

- MIG-01 对 13 个主题的 C 级重制决定，视为 SITE-01 入口切换所需的冻结/归档决定（ADR-005）。
- 本批交付 `activeMode=card-os`；`parallel` 相保留在合同中，SITE-02 再接线回滚。
- 根入口主 CTA 用绝对 URL `https://www.yutou.space/card-os/`，避免 Vercel/EdgeOne 静态站没有画廊反代。
- 生产根入口继续隐藏 `spider-verse` / `paw-patrol`。
- 不 merge、不 push、不现网。现网须先 reload Nginx snippet，再部署根入口。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `kids-visual-learning-pack` `main` | SITE-01 未提交；另有 `outputs/` 未跟踪 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `fd696c2` | 本批未改；不 merge `main` |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；`/card-os/` 仍 307 到 capabilities |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `node scripts/knowledge-entry.test.mjs` | PASS | 合同、根 hub、Nginx 无 307 |
| `npm run test:card-os-deploy` | PASS | 95 项（需非沙箱，因 release 测试 `git init`） |
| `npm run validate` | PASS | 含 `test:knowledge-entry` |
| 本机 hub `http://127.0.0.1:8766/` | PASS | 主链到 Card OS；档案链到 `boards/kids-world/index.html`；无自动跳转 |
| `git diff --check` | PASS | |
| `bash scripts/ai/check-handoff.sh` | PASS | Base Commit `fc6b26f` 与 HEAD 对齐 |
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
- 未构建 Vite 时，从静态服务器打开 `boards/kids-world/index.html` 只有壳，看不到 React 冻结条；冻结条文案由 `HomePage.tsx` 与 `validate` 覆盖。

## Risks and Caveats

- 未授权不要 merge `knowledge-pipeline-v1`、不要 push/deploy。
- `uv.lock` 与 `outputs/` 不要混入提交。
- 现网顺序：先应用 Nginx 画廊反代，再部署根 `index.html`。只部署根入口会把用户送到 capabilities JSON。
- SITE-02 才接线回滚开关与旧 hash URL 映射。

## Remaining Work

1. 用户提交 SITE-01 后，下一实现会话按路线图 §5 编号 11 做 SITE-02（旧 URL 映射与回滚开关）。
2. 授权现网时：reload Nginx snippet，再 rsync 根入口；不要在本批未授权时执行。
3. thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。

## Exact Next Action

新开会话不要重做 SITE-01。下一刀把 `SITE-02` 写入 `CURRENT_TASK.md`：旧 `kids-world` hash/URL 映射，以及一次部署内把 `activeMode` 切回 `parallel` 的回滚开关。不 merge、不现网，除非用户在该会话明确授权。活 server 尖端仍为 `knowledge-pipeline-v1` @ `fd696c2`。

## Recovery Notes

- kids：`kids-visual-learning-pack` `main` @ `c2bae22`；本提交记录 kids SHA。
- 活 server：`knowledge-pipeline-v1` @ `fd696c2`；本批未改。
- 入口合同：`shared/knowledge-entry.json`
- 画廊：`PYTHONPATH=src python3 -m cognitive_card_server.four_card_portal gallery --catalog-root /tmp/card-os-accept-01/catalog --output-dir /tmp/card-os-portal`
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：ADR-002/003/004/005、SITE-01 设计。
