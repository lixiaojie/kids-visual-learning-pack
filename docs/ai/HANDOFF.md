# Latest Handoff

## Metadata

- Updated At: 2026-08-30
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: a85a785
- Kids HEAD: a85a785 `docs(card-os): record ADR-004, browse confirmation, and four-card convert`
- Server Branch: `knowledge-pipeline-v1` @ `e9bfd22`（BROWSE-01 + CONV-01 已本地提交；未 merge `main`）
- Server Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` 现为 `knowledge-pipeline-v1`
- Server Generation-Input Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Server main checkout: `/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server` @ `c2a898c`
- Working Tree: kids 仅 `outputs/` 未跟踪；server 仅 `uv.lock` 未跟踪
- Task Status: **Done（CONV-01 接合密封转换已在 `knowledge-pipeline-v1` 验证并本地提交 `e9bfd22`）。** 未 merge server `main`；未 push、未现网。

## Summary

CONV-01 已落地并提交。CLI `convert` 把显式 four-card 的 library current 映射为接合 generation-input：FACT `source_id` 去点号，knowledge-core 磁盘不变。默认 chaptered-guide 兔子被拒绝。未写 production-record 本体，未扩 PORTAL-01，未 merge server `main`。

## Completed

- kids `a85a785`：ADR-004、BROWSE-01/CONV-01 设计、路线图与任务账本。
- server `e9bfd22`：`browse` 静态 HTML + 只读 GET；`four_card_converter` 与 CLI `convert`。

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | 治理文档（ADR-004、BROWSE-01/CONV-01 设计、路线图、任务账本） | 已提交 `a85a785` |
| kids | `outputs/` | 未跟踪；不纳入 |
| server | browse + convert（14 文件） | 已提交 `e9bfd22` |
| server | `uv.lock` | 未跟踪；不纳入 |

## Decisions Made

- 只转换 current 且 family 为显式 `four-card`。
- FACT `source_id` 把 `.`/`_` 换成 `-`；碰撞与无法映射 fail closed。
- `canonical_claim` 临时同时填入 FACT `cn`/`en`；中文表达留给 AGE-01。
- 不在本批写 production-record 本体；不新增 HTTP convert。
- 分类由 `--request` 提供，不从 Knowledge Core 发明。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `~/projects/family/kids-visual-learning-pack` `main` @ `a85a785` | 本批已提交 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` `knowledge-pipeline-v1` @ `e9bfd22` | BROWSE-01+CONV-01 已本地提交 |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；不在本批改 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server unittest converter + browse / library / HTTP / projection / generation-input / join / authoring / contract / auth | PASS | 248 项 |
| `git merge-base --is-ancestor knowledge-pipeline-v1 main` | PASS | 退出码 1：未 merge 进 main |
| server `main` | PASS | 仍 `c2a898c` |
| `git diff --check`（kids + server） | PASS | 无 whitespace 错误 |
| `bash scripts/ai/check-handoff.sh` | PASS | 本交接写入后对齐 `a85a785` |
| `bash scripts/ai/check-task-state.sh` | PASS | Status Done，验收全勾 |
| `bash scripts/ai/check-doc-governance.sh` | WARN | 0 FAIL；3 项文档复核到期，与本批无关 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL；既有 secret 字段名 WARN + 文档复核到期 |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交文档仍在。
- 文档地图 Last Reviewed `2026-07-24` / Next Review Due `2026-08-24` 已过期，属既有治理 WARN。

## Risks and Caveats

- 转换器是投影，不是 CMS；不要改 Knowledge Core 来迁就 FACT。
- 未授权不要 merge `knowledge-pipeline-v1`、不要 push/deploy。
- `uv.lock` 与 `outputs/` 不要混入提交。
- FACT `cn`/`en` 目前都是英文 `canonical_claim`；儿童中文留给 AGE-01。

## Remaining Work

1. 下一产品切片：把接合密封交给本机 loopback executor（仍不 merge `main`、不现网），或用户另行授权。
2. thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。
3. 未 push；未 merge server `main`。

## Exact Next Action

不要 merge server `main`，不要 push，不要现网，不要扩 PORTAL-01。若继续产品工作，把接合密封接入本机 compiled-job / executor 另立 CURRENT_TASK。

## Recovery Notes

- kids：`/Users/admin/projects/family/kids-visual-learning-pack` `main` @ `a85a785`。
- 活 server：`knowledge-pipeline-v1` @ `e9bfd22`；main `c2a898c`。
- 转换命令：`PYTHONPATH=src python3 -m cognitive_card_server.knowledge_library.cli convert --library-root <library> --topic <slug> --repo-root . --snapshot-id sha256:ae563ea0c9d49046b2ff7e13f6294c1d6ddd1c5666f6bda5bd82d36872da1f20 --registry-commit 9c1b82be69df2da8348f66970a993e9c1984ce6d --request examples/four-card-converter/rabbit-request.json --output <joined.json>`
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：`docs/superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md`、ADR-004。
