# Latest Handoff

## Metadata

- Updated At: 2026-08-31
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 16e16f8
- Kids HEAD: 本提交
- Server Branch: `knowledge-pipeline-v1` @ `cbaf2b4`
- Server Worktree: `.worktrees/cognitive-card-server-knowledge-core` 现为 `knowledge-pipeline-v1`
- Server Generation-Input Worktree: `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Server main checkout: Documents Codex `cognitive-card-server` @ `c2a898c`
- Working Tree: kids 本提交后仅 `outputs/` 未跟踪；server 仅 `uv.lock` 未跟踪
- Task Status: **Done（TMPL-01 已本地提交 server `cbaf2b4`）。** 未 merge server `main`；未 push；未现网。

## Summary

TMPL-01 把 four-card 模板族做成 `template-registry-v1`：精确 mammal / dinosaur 与全部紧凑 domain/form 族登记在服务器。相同主路由得到同一四页骨架；未登记路由返回 `TEMPLATE_GAP`，不再把 `animal/bird` 等 gap 单元格静默套到 generic。每个 family 至少两个对象夹具。convert 密封前走注册表。不改 snapshot 字节，不扩 PORTAL，不 merge，不现网。

## Completed

- 设计：`docs/superpowers/specs/2026-08-31-template-family-registry-design.md`
- 实现：server `templates` 注册表 / resolve / converter 门禁；已本地提交 `cbaf2b4`
- 测试：template focused 10 项 PASS；pipeline 回归 136 项 PASS
- 未 merge、未 push、未现网

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | 本提交：TMPL-01 Done |
| kids | `docs/ai/HANDOFF.md` | 本提交：本交接 |
| kids | `docs/cognitive-card-os-roadmap.md` | 本提交：TMPL-01 DONE `cbaf2b4` |
| kids | `docs/cognitive-card-os-system-design.md` | 本提交：交付阶段第 12 条 |
| kids | `docs/README.md` | 本提交：设计条目 |
| kids | `docs/superpowers/specs/2026-08-31-template-family-registry-design.md` | 本提交 |
| kids | `docs/superpowers/specs/2026-08-31-classification-registry-design.md` | 本提交：gap 指向 TEMPLATE_GAP |
| kids | `outputs/` | 未跟踪；不纳入 |
| server | `src/cognitive_card_server/templates/` | 已提交 `cbaf2b4` |
| server | `src/cognitive_card_server/four_card_converter/convert.py` | 已提交 `cbaf2b4` |
| server | `tests/test_template_registry.py` | 已提交 `cbaf2b4` |
| server | `README.md` | 已提交 `cbaf2b4` |
| server | `uv.lock` | 未跟踪；不要 add |

## Decisions Made

- 主路由只匹配精确元组；`life + entity + general` 是自己的族，不接收 `animal/bird`。
- 分类 `gap` 仍可 authoring；四卡 convert 无映射则 `TEMPLATE_GAP`。
- 数学 `space-geometry` 与社会 `schedule` 不是 four-card 族，四卡解析为缺口。
- 恐龙 `paleontology + entity + dinosaur` 分类矩阵为 gap，但模板已登记，可以解析。
- 不 merge、不 push、不现网。server TMPL-01 已本地提交 `cbaf2b4`。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `kids-visual-learning-pack` `main` | 本批后仅 `outputs/` 未跟踪 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `cbaf2b4` | 不 merge `main` |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；不在本批改 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `.venv/bin/python -m unittest tests.test_template_registry` | PASS | 10 项 |
| `.venv/bin/python -m unittest` template + classification + authoring + converter + accept + projection + library + browse + HTTP library + joined + generation-input + AGE + lock | PASS | 136 项 |
| `git diff --check` | PASS | kids 文档与 server |
| `bash scripts/ai/check-handoff.sh` | 本提交后跑 | Base Commit `16e16f8` |
| `bash scripts/ai/check-task-state.sh` | 本提交后跑 | Status Done，验收全勾 |
| `bash scripts/ai/check-agent-state.sh` | 本提交后跑 | 预期既有 WARN |
| 未 merge server `main` / 未 push / 未现网 | PASS | server 尖端 `cbaf2b4` |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交文档仍在。
- 文档地图 Last Reviewed `2026-07-24` / Next Review Due `2026-08-24` 已过期，属既有治理 WARN。
- `/tmp/card-os-accept-01` 不是 git 产物；重启后需重跑 CLI。

## Risks and Caveats

- 未授权不要 merge `knowledge-pipeline-v1`、不要 push/deploy。
- `uv.lock` 与 `outputs/` 不要混入提交。
- generation-input 低层 snapshot resolver 仍可对未登记 subtype 做 compact fallback；知识管线 convert/accept 已先挡 `TEMPLATE_GAP`。
- ACCEPT-02 仍未跑第二个哺乳动物正式试产。

## Remaining Work

1. 下一实现会话：按路线图 §5 编号 9（PORTAL-01），或用户指定 ACCEPT-02。
2. thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。

## Exact Next Action

新开会话，按路线图 §5 编号 9 把 `PORTAL-01` 写入 `CURRENT_TASK.md`，或按用户指定做 ACCEPT-02。不 merge、不现网。活 server 尖端为 `knowledge-pipeline-v1` @ `cbaf2b4`。

## Recovery Notes

- kids：`kids-visual-learning-pack` `main`；本提交记录 kids SHA。
- 活 server：`knowledge-pipeline-v1` @ `cbaf2b4`；KNOW-01 `4083ce7`；ACCEPT-01 `10b14c8`；PUBLISH-01 `7a127b4`；QA-01 `37a5927`；RENDER-01 `1ef6edc`；AGE-01 `4e0ea52`；RUN-01 `c55f51b`；main `c2a898c`。
- 无 `--request` 复跑：`python3 -m cognitive_card_server.four_card_accept --authoring examples/authoring/rabbit-real.json --repo-root . --work-root /tmp/card-os-accept-01 --actor owner --now 2026-08-31T04:00:00Z`
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：ADR-002/003/004、TMPL-01 设计。
