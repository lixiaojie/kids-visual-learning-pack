# Latest Handoff

## Metadata

- Updated At: 2026-08-31
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 7e311c0
- Kids HEAD: 7e311c0 `docs(card-os): record PORTAL-01 published artifact gallery`
- Server Branch: `knowledge-pipeline-v1` @ `fd696c2`
- Server Worktree: `.worktrees/cognitive-card-server-knowledge-core` 现为 `knowledge-pipeline-v1`
- Server Generation-Input Worktree: `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Server main checkout: Documents Codex `cognitive-card-server` @ `c2a898c`
- Working Tree: kids 本提交后仅 `outputs/` 未跟踪；server 仅 `uv.lock` 未跟踪
- Task Status: **Done（PORTAL-01 已本地提交 server `fd696c2`）。** 未 merge server `main`；未 push；未现网。

## Summary

PORTAL-01 把 PUBLISH-01 catalog 做成只读 Artifact 画廊：静态 HTML + loopback `/card-os/`。公开观众只看到 `visibility=public` 且有 current 的包；owner-only、撤回、草稿对公开列表与下载为 404。不替代 BROWSE-01，不写 Knowledge Core，不展示 Projection family 选择面。公网域名仍属 SITE-01。

## Completed

- 设计：`docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- 实现：server `four_card_portal` 画廊/CLI/HTTP；catalog `list_summaries` / visibility sidecar；已本地提交 `fd696c2`
- 测试：portal focused 10 项 PASS；pipeline 回归 145 项 PASS
- 未 merge、未 push、未现网

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | 本提交：PORTAL-01 Done |
| kids | `docs/ai/HANDOFF.md` | 本提交：本交接 |
| kids | `docs/cognitive-card-os-roadmap.md` | 本提交：PORTAL-01 DONE `fd696c2` |
| kids | `docs/cognitive-card-os-system-design.md` | 本提交：交付阶段第 13 条 |
| kids | `docs/README.md` | 本提交：设计条目 |
| kids | `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md` | 本提交 |
| kids | `outputs/` | 未跟踪；不纳入 |
| server | `src/cognitive_card_server/four_card_portal/` | 已提交 `fd696c2` |
| server | `src/cognitive_card_server/four_card_publish/publish.py` | 已提交 `fd696c2` |
| server | `src/cognitive_card_server/four_card_publish/__init__.py` | 已提交 `fd696c2` |
| server | `src/cognitive_card_server/http/app.py` | 已提交 `fd696c2` |
| server | `tests/test_four_card_portal.py` | 已提交 `fd696c2` |
| server | `tests/test_http_portal.py` | 已提交 `fd696c2` |
| server | `README.md` | 已提交 `fd696c2` |
| server | `uv.lock` | 未跟踪；不要 add |

## Decisions Made

- 画廊只消费 package catalog，不读 Knowledge library，不调用 Projection 选择面。
- 公开 GET 不要求 token；owner-only / 撤回用同一 `PORTAL_NOT_FOUND`，避免泄漏存在性。
- `visibility.json` 与 current pointer 并列，不进入 `package_sha256`。
- 本机 loopback `/card-os/` 满足 PORTAL-01；公网 `yutou.space` 与 kids-world 替换仍属 SITE-01。
- 不 merge、不 push、不现网。server PORTAL-01 已本地提交 `fd696c2`。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `kids-visual-learning-pack` `main` | 本批后仅 `outputs/` 未跟踪 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `fd696c2` | 不 merge `main` |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；不在本批改 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `.venv/bin/python -m unittest tests.test_four_card_portal tests.test_http_portal` | PASS | 10 项 |
| `.venv/bin/python -m unittest` template + classification + authoring + converter + accept + projection + library + browse + HTTP library + joined + AGE + lock + publish + portal | PASS | 145 项 |
| `git diff --check` | PASS | kids 文档与 server |
| `bash scripts/ai/check-handoff.sh` | PASS | Base Commit 与 HEAD 在 SHA 记录提交后对齐 |
| `bash scripts/ai/check-task-state.sh` | PASS | CURRENT_TASK 路径引用全部存在 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL 预期；既有 secret 字段名 WARN + 文档复核到期 |
| 未 merge server `main` / 未 push / 未现网 | PASS | server 尖端 `fd696c2` |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交文档仍在。
- 文档地图 Last Reviewed `2026-07-24` / Next Review Due `2026-08-24` 已过期，属既有治理 WARN。
- `/tmp/card-os-accept-01` 不是 git 产物；重启后需重跑 CLI。

## Risks and Caveats

- 未授权不要 merge `knowledge-pipeline-v1`、不要 push/deploy。
- `uv.lock` 与 `outputs/` 不要混入提交。
- 公开 loopback 画廊没有浏览器会话；不要把服务绑到非 127.0.0.1。
- SITE-01 才会把 `/card-os/` 接到公网并替换 kids-world。

## Remaining Work

1. 下一实现会话：按路线图 §5 编号 10（SITE-01），或用户指定 ACCEPT-02。
2. thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。

## Exact Next Action

新开会话不要重做 PORTAL-01。下一刀按路线图 §5 编号 10 把 `SITE-01` 写入 `CURRENT_TASK.md`，或按用户指定做 ACCEPT-02。不 merge、不现网。活 server 尖端为 `knowledge-pipeline-v1` @ `fd696c2`。

## Recovery Notes

- kids：`kids-visual-learning-pack` `main` @ `7e311c0`；本提交记录 kids SHA。
- 活 server：`knowledge-pipeline-v1` @ `fd696c2`；TMPL-01 `cbaf2b4`；KNOW-01 `4083ce7`；ACCEPT-01 `10b14c8`；PUBLISH-01 `7a127b4`；QA-01 `37a5927`；RENDER-01 `1ef6edc`；AGE-01 `4e0ea52`；RUN-01 `c55f51b`；main `c2a898c`。
- 画廊：`PYTHONPATH=src python3 -m cognitive_card_server.four_card_portal gallery --catalog-root /tmp/card-os-accept-01/catalog --output-dir /tmp/card-os-portal`
- 无 `--request` 复跑：`python3 -m cognitive_card_server.four_card_accept --authoring examples/authoring/rabbit-real.json --repo-root . --work-root /tmp/card-os-accept-01 --actor owner --now 2026-08-31T04:00:00Z`
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：ADR-002/003/004、PORTAL-01 设计。
