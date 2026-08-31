# Latest Handoff

## Metadata

- Updated At: 2026-08-31
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: e8789a7
- Kids HEAD: e8789a7 `docs(ai): record DEPLOY-02 kids commit SHA`（本提交收录 WB-01 文档与 Nginx）
- Server Branch: `knowledge-pipeline-v1` @ `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`（未 merge `main`）
- Server Worktree: `.worktrees/cognitive-card-server-knowledge-core`
- Server Generation-Input Worktree: `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Working Tree: 本提交收录 WB-01；`outputs/` 仍未跟踪、不纳入；server `uv.lock` 未纳入
- Task Status: **In Progress（WB-01 本地已提交；现网待从 `115377b` 打 release、种子 library、reload Nginx）。** 未 merge server `main`；未 push kids。

## Summary

用户授权提交。server `knowledge-pipeline-v1` 已提交 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`（`knowledge_ops`）。kids 本提交收录 WB-01 设计、实施计划、Nginx `/card-os/ops/` 与部署测试。未打 release、未种子生产 knowledge-library、未 reload 生产 Nginx。公网画廊仍是 DEPLOY-02 ACCEPT-01 四卡包。

## Completed

- WB-01 spec 与实施计划已写入
- server：`115377b` `knowledge_ops` pages/http；`PROTECTED_ROUTES` admin GET；`OPS_NO_CURRENT` → 409
- kids：Nginx `/card-os/ops/` GET/HEAD 反代；`EXPECTED_NGINX` 同步
- 运维记录第 11 节：本地证据与现网硬顺序
- 路线图 WB-01 仍 `IN PROGRESS`（已提交，现网未做）

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md` | 本提交新增 |
| kids | `docs/superpowers/plans/2026-08-31-operator-knowledge-workbench-implementation-plan.md` | 本提交新增 |
| kids | `docs/ai/CURRENT_TASK.md` | 本提交：WB-01 本地完成项已勾 |
| kids | `docs/ai/HANDOFF.md` | 本提交：本交接 |
| kids | `docs/cognitive-card-os-roadmap.md` | 本提交：WB-01 server SHA |
| kids | `docs/cognitive-card-os-system-design.md` | 本提交：§11 WB-01 |
| kids | `docs/README.md` | 本提交：设计/计划地图 |
| kids | `docs/operations/cognitive-card-server-deployment-2026-07-14.md` | 本提交：第 11 节 |
| kids | `ops/cognitive-card-server/nginx/card-os.conf` | 本提交：ops 反代 |
| kids | `tests/test_card_os_deployment_assets.py` | 本提交：ops location 断言 |
| kids | `outputs/` | 既有未跟踪；不纳入 |
| server | `knowledge_ops` + HTTP 挂载 | 已提交 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd` |
| server | `uv.lock` | 未跟踪；不纳入 |

## Decisions Made

- 公网画廊保持 PORTAL-01；生产在 `/card-os/ops/`，admin token，不做浏览器会话。
- 四刀都做，顺序不得并行混进 WB-01。
- 任务账本只写路线图，不另建第二份待办。
- 用户已授权提交；未授权打 release、reload 生产 Nginx、merge server `main`。
- 不得先 reload `/card-os/ops/` 再种子知识库；也不得在旧 `fd696c2` 应用上 reload ops（会 404）。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `kids-visual-learning-pack` `main`（本提交 WB-01） | 不改 server 提交 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `115377b` | 不 merge `main` |
| 现网对应 | `/opt/cognitive-card-server/current` → `fd696c2` | 画廊仍是 DEPLOY-02；ops 未上线 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server `python -m unittest tests.test_http_knowledge_ops tests.test_http_knowledge_library tests.test_http_portal -v` | PASS | 16 tests |
| kids `python3 -m unittest tests.test_card_os_deployment_assets tests.test_card_os_release -v` | PASS | 67 tests |
| WB-01 生产种子 / Nginx reload / 现网抽查 | 未执行 | 待授权从 `115377b` 打 release |
| `bash scripts/ai/check-doc-governance.sh` | WARN | Last Reviewed 过期 3 项，与本批无关 |
| `bash scripts/ai/check-task-state.sh` | PASS | Status In Progress |
| `bash scripts/ai/check-handoff.sh` | WARN | 生产项明确标为未执行（允许） |
| `bash scripts/ai/check-agent-state.sh` | WARN | 汇总 pass=2 warn=3 fail=0 |
| `git diff --check` | PASS | kids 工作区 |
| 未 merge server `main` | PASS | |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交文档仍在。
- 文档地图 Last Reviewed `2026-07-24` / Next Review Due `2026-08-24` 已过期，属既有治理 WARN。
- 生产 `docs/` 仍可能是 rsync 当时的旧任务稿，直到下次文档部署。

## Risks and Caveats

- 同一 SHA `fd696c2` 不能再装一次；现网要上 ops 必须从 `115377b` 打新 release。
- 未授权 merge `knowledge-pipeline-v1` 进 server `main`。
- `uv.lock` 与 `outputs/` 不要混入提交。

## Remaining Work

1. 从 server `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd` 打不可变 release 并安装到 `127.0.0.1:8765`。
2. 种子 AUTHOR-02 `rabbit-real.json` 为 knowledge-library `rabbit` current（不覆盖 four-card）；核对话廊 `package_sha256=sha256:c56a29475a585a1bf33a35beb306d64e2157e83910647ec0368f19c111c9b69f`。
3. 应用 kids `card-os.conf` 并 `nginx -t` + reload。
4. 抽查 ops HTML/JSON 与画廊 PDF 后进入 WB-02。

## Exact Next Action

若要把 WB-01 接到现网：从 server `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd` 打不可变 release 并安装，再种子 knowledge-library，最后 reload `/card-os/ops/`。不要在未种子时 reload。不要开始 WB-02。未授权则不要 push、不要 merge server `main`。

## Recovery Notes

- kids：`kids-visual-learning-pack` `main` 本提交收录 WB-01；`outputs/` 未跟踪。
- server：`.worktrees/cognitive-card-server-knowledge-core` `knowledge-pipeline-v1` @ `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`。
- 现网：`/opt/cognitive-card-server/current` → `fd696c2`；画廊未改。
- 任务：`docs/ai/CURRENT_TASK.md`（WB-01 In Progress，本地已提交）。
- 队列：路线图 §5 第 13–16 项。
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：ADR-002/003/004、WB-01 设计与实施计划、BROWSE-01、PORTAL-01。
