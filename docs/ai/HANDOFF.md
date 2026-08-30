# Latest Handoff

## Metadata

- Updated At: 2026-08-30
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: c6973ef5afde8c6ca394508b71981f0a2e644f7a
- Kids HEAD: this commit of join-task CURRENT_TASK / HANDOFF / roadmap
- Server Branch: `codex/knowledge-core-contract-v1` 与 `codex/api-01-generation-input-v1` 均未 merge
- Server Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`（接合 6 文件已本地提交；`uv.lock` 仍未跟踪）
- Server Knowledge-Core Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` @ `1facb79`
- Server main checkout: `/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server` @ `c2a898c`
- Working Tree: 本 commit 含 CURRENT_TASK / HANDOFF / roadmap；`outputs/` 仍排除。server generation-input 工位仅剩未跟踪 `uv.lock`，未纳入提交
- Task Status: **Done（接合合同已本地提交 `4ca3e0e`，未 merge、未开集成分支）。** ADR-003 门禁测试已通过：接合 lock 摘要四对象 `final_content_lock`，平行 FACT 命题不能脱离 knowledge-core。未开 `knowledge-pipeline-v1`，未 push、未现网。

## Summary

用户审阅授权后，在 generation-input worktree 本地提交接合 6 文件：`4ca3e0e` `feat(api-01): bind generation-input lock to four-object revision identity`。未 add `uv.lock`。未 merge `codex/knowledge-core-contract-v1`，未创建 `knowledge-pipeline-v1`，未 push。focused `18` 项在提交前复跑 PASS。`merge-base --is-ancestor 1facb79 HEAD` 与反向仍为非 0。

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | 记录 IMPL-2 HEAD `4ca3e0e` |
| kids | `docs/ai/HANDOFF.md` | 本批交接 |
| kids | `docs/cognitive-card-os-roadmap.md` | §5 第 2 项与 API-01 抢救进度改为已提交 |
| server (generation-input) | `src/cognitive_card_server/generation_input/knowledge_revision.py` | 已提交于 `4ca3e0e` |
| server (generation-input) | `tests/test_generation_input_knowledge_revision.py` | 已提交于 `4ca3e0e` |
| server (generation-input) | `tests/fixtures/knowledge_revision/rabbit/{knowledge-core,learning-spec,projection-spec,manifest}.json` | 已提交于 `4ca3e0e` |

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `~/projects/family/kids-visual-learning-pack` `main` | 规范与任务；不存知识 revision |
| 知识存储 | `.worktrees/cognitive-card-server-knowledge-core` @ `1facb79` | 四对象 authoring；本批只读 |
| 四卡执行 | `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e` | 接合代码已本地提交；未 merge |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；不在本批改 |
| 例外 | `.worktrees/card-os-thin-skill-v1` | 脏；未强制删除 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `PYTHONPATH=src python3 -m unittest tests.test_generation_input tests.test_generation_input_knowledge_revision` | PASS | 18 项；v1 11 + join 7；提交前复跑 |
| `git show --stat HEAD` | PASS | 仅 6 个接合文件；无 `uv.lock` |
| `git merge-base --is-ancestor 1facb79 HEAD` | PASS | exit 1，knowledge-core 不是 generation-input 祖先 |
| `git merge-base --is-ancestor HEAD 1facb79` | PASS | exit 1，反向同样未包含 |
| 未创建 `knowledge-pipeline-v1` / 未 merge / 未 push | PASS | `git branch --list knowledge-pipeline-v1` 空；worktree 仍为 main + knowledge-core + generation-input |
| 未改 knowledge-core 代码 | PASS | 该 worktree 本批未写 |
| kids `git diff --check` | PASS | 文档更新后 |
| `bash scripts/ai/check-handoff.sh` | PASS | 独立运行全绿 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL；既有 secret 字段名与文档复核到期。task-state PASS |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交 `docs/cognitive-card-os-roadmap.md`、`docs/superpowers/specs/2026-07-16-cognitive-card-client-production-library-design.md`，以及三份 07-16 plan 未跟踪文件。
- v1 `assemble_generation_input` 仍允许 FACT-only 密封（兼容已存 packet）；接合路径才强制四对象 revision。把 knowledge-core 的 request 摘要 lock 改成接合 lock 须等集成分支。

## Risks and Caveats

- `uv.lock` 仍未跟踪，不要混入后续提交。
- knowledge-core `source_id` 含点号（`src.rabbit.primary`），generation-input FACT `source_id` 不允许点号；本批只强制 `proposition_id` 属于 knowledge-core，完整 source 映射留给 converter。
- 先 repair 再 prune 仍是硬顺序。
- 未授权前不要 push/merge/deploy，也不要开 `knowledge-pipeline-v1`。

## Remaining Work

1. 用户明确授权后才开 `knowledge-pipeline-v1`，按「存储先、执行后」迁入，并把 knowledge-core 的 `generation_input_lock_sha256=sha256_ref(request)` 改为接合 lock。
2. 用户决定 thin-skill 脏文档：提交到该分支、迁到治理仓、或丢弃后再 `worktree remove`。不要 `--force`。

## Exact Next Action

不要开 `knowledge-pipeline-v1`，除非用户在本会话或后续明确授权集成分支。下一步若授权：从 knowledge-core `1facb79` 建 `knowledge-pipeline-v1`，再 cherry-pick / 迁入 generation-input `4ca3e0e` 的接合提交，并把 knowledge-core 的 `generation_input_lock_sha256=sha256_ref(request)` 改为接合 lock。不要 push。不要 merge 两条功能分支到 server `main`。

## Recovery Notes

- kids：`/Users/admin/projects/family/kids-visual-learning-pack`；本批任务/交接/路线图在此 commit；治理基线 `c6973ef`。
- 活 server：knowledge-core `1facb79`；generation-input `4ca3e0e`（接合已提交）+ 未跟踪 `uv.lock`；main `c2a898c`。
- 保留无 checkout 的分支：`codex/card-os-salvage-v1`、`codex/harness-v1`、`codex/api-01-core-snapshot`、`codex/remote-api-v03`。
- tag：`archive/card-os-thin-skill-v1-20260717`。
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 验证命令：`cd .worktrees/cognitive-card-server-api-01-impl-2 && PYTHONPATH=src python3 -m unittest tests.test_generation_input tests.test_generation_input_knowledge_revision`
