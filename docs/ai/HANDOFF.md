# Latest Handoff

## Metadata

- Updated At: 2026-08-30
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 49a1d34
- Kids HEAD: this commit of WIRE-01 design + CURRENT_TASK / HANDOFF / roadmap / docs/README
- Server Branch: `knowledge-pipeline-v1` @ `9e0c353`（LIB-01 `b672949` + PROJ-01 / WIRE-01）；`codex/knowledge-core-contract-v1` 仍 `1facb79`；`codex/api-01-generation-input-v1` 仍 `4ca3e0e`；均未 merge 进 `main`
- Server Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` 现为 `knowledge-pipeline-v1` @ `9e0c353`
- Server Generation-Input Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`（功能分支 checkout 暂留）
- Server main checkout: `/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server` @ `c2a898c`
- Working Tree: this commit 含任务/交接/路线图/WIRE-01 设计/文档地图；`outputs/` 仍排除。server pipeline 仅余未跟踪 `uv.lock`
- Task Status: **Done（kids 治理文档已提交；server PROJ-01 / WIRE-01 已本地提交 `9e0c353`）。** 未 merge 进 server `main`，未 push、未现网。

## Summary

用户授权提交后，server `knowledge-pipeline-v1` 本地提交 `9e0c353`（PROJ-01 选择面 + WIRE-01 HTTP/DB 接线，14 文件）。kids 本 commit 登记独立设计与路线图。未 add `uv.lock`。未 merge 进 server `main`（仍 `c2a898c`），未 push。

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | this commit：WIRE-01 任务，Done |
| kids | `docs/ai/HANDOFF.md` | this commit：本批交接 |
| kids | `docs/cognitive-card-os-roadmap.md` | this commit：登记 WIRE-01 / `9e0c353` |
| kids | `docs/superpowers/specs/2026-08-30-knowledge-library-http-db-wiring-design.md` | this commit：WIRE-01 独立设计 |
| kids | `docs/README.md` | this commit：登记该设计 |
| server (`knowledge-pipeline-v1`) | 14 files | 已提交 `9e0c353`：projection_family、library HTTP、接合 current 门禁、测试、README |

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `~/projects/family/kids-visual-learning-pack` `main` | 规范与任务；不存知识 revision |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `9e0c353` | 存储 + 执行 + 选择面 + HTTP 同树；本批活工位 |
| 四卡执行（功能分支暂留） | `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e` | 未 merge 进 main；本批未撤 checkout |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；不在本批改 |
| 例外 | `.worktrees/card-os-thin-skill-v1` | 脏；未强制删除 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| focused library + projection-family + generation-input + 接合 + authoring + contract + HTTP compiled + HTTP library | PASS | `200` 项 |
| HTTP auth/admin/public/subscriber + 上述 focused | PASS | `251` 项；含 PROTECTED_ROUTES=18 |
| `git merge-base --is-ancestor HEAD c2a898c` | PASS | exit 1，集成分支未进 main |
| 功能分支尖端未动 | PASS | knowledge-core `1facb79`；generation-input `4ca3e0e` |
| server main `HEAD` | PASS | `c2a898c` |
| 未 add `uv.lock` / 未 push | PASS | pipeline `?? uv.lock`；`9e0c353` 无 upstream |
| kids `git diff --check` | PASS | 文档更新后 |
| server `git diff --check` | PASS | 提交后工作区仅 `uv.lock` |
| `bash scripts/ai/check-handoff.sh` | PASS | 独立运行；Base Commit 对齐提交前 HEAD `49a1d34` |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL；既有 secret 字段名与文档复核到期。task-state PASS |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交 `docs/cognitive-card-os-roadmap.md`、`docs/superpowers/specs/2026-07-16-cognitive-card-client-production-library-design.md`，以及三份 07-16 plan 未跟踪文件。
- v1 `assemble_generation_input` 仍允许 FACT-only 密封（兼容已存 packet）；接合路径才强制四对象 revision，且 HTTP 接合现在还要求 library current。authoring manifest lock 现为 revision-record 摘要，不是带 FACT 的完整 executor join lock。
- generation-input 功能分支 worktree 仍在，活 checkout 尚未收到「main + 一条集成分支」；本批明确不撤。

## Risks and Caveats

- `uv.lock` 仍未跟踪，不要混入后续提交。
- knowledge-core `source_id` 含点号（`src.rabbit.primary`），generation-input FACT `source_id` 不允许点号；完整 source 映射留给 converter。
- 先 repair 再 prune 仍是硬顺序。
- 未授权不要把 `knowledge-pipeline-v1` merge 进 server `main`，不要 push/deploy。
- current pointer 变化有审计；`get_current` 对 `unlist_current` 过期只读下架，`refresh` 才持久化清空 pointer。
- `block_publish` 过期不自动下架，只阻止新 Publish。
- 选择面不持久化 `source=explicit`；编译后的包若 family 等于 scope 默认，`--package-dir` 会显示 `default`。这是有意不增加第五对象。
- 省略 family 的时效主题 recommended/chosen 仍是 `chaptered-guide`；`time-sensitive-brief` 只作为 eligible option。
- 接合 HTTP GET 在 unlist 之后对已存储密封返回 404；磁盘字节仍在 GenerationInputStore，只是不再发给 executor。

## Remaining Work

1. 未授权不要 merge 进 server `main`，不要 push、不要现网。
2. 用户决定 thin-skill 脏文档：提交到该分支、迁到治理仓、或丢弃后再 `worktree remove`。不要 `--force`。
3. 用户决定是否撤 generation-input 功能分支 worktree（保留分支名 `codex/api-01-generation-input-v1`）。

## Exact Next Action

不要 merge `knowledge-pipeline-v1` 进 server `main`，不要 push。thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。

## Recovery Notes

- kids：`/Users/admin/projects/family/kids-visual-learning-pack`；本批治理文档已提交；基线见本 commit。
- 活 server：`knowledge-pipeline-v1` @ `9e0c353` + 未跟踪 `uv.lock`；generation-input 仍 `4ca3e0e`；main `c2a898c`。
- 保留无 checkout 的分支：`codex/card-os-salvage-v1`、`codex/harness-v1`、`codex/api-01-core-snapshot`、`codex/remote-api-v03`。knowledge-core 功能分支 `codex/knowledge-core-contract-v1` 无独立 checkout（工位已切到集成分支）。
- tag：`archive/card-os-thin-skill-v1-20260717`。
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 验证命令：`cd .worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python3 -m unittest tests.test_http_knowledge_library tests.test_http_compiled tests.test_projection_family tests.test_knowledge_library tests.test_generation_input tests.test_generation_input_knowledge_revision tests.test_knowledge_contract_authoring`
