# Latest Handoff

## Metadata

- Updated At: 2026-08-30
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 34d5bbcb6d93b617bf551284b933370b182328f3
- Kids HEAD: this commit of ADR-003 and governance docs
- Server Branch: `codex/knowledge-core-contract-v1` 与 `codex/api-01-generation-input-v1` 均未 merge
- Server Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-01-impl-2` @ `878a28d`
- Server Knowledge-Core Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` @ `1facb79`
- Server main checkout: `/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server` @ `c2a898c`
- Working Tree: `outputs/` 仍排除；thin-skill worktree 有未提交文档故未撤
- Task Status: **Done（治理与安全收敛已提交）。ADR-003 已写。server 活 checkout 已收成 main + knowledge-core + generation-input。kids 已撤 5 个合入/归档 worktree；`card-os-thin-skill-v1` 因脏工作区未 `--force`。未实现接合代码，未 push。**

## Summary

用户确认知识管线为工作区轴线，并要求收敛过多分支。本批新增 ADR-003（三角色、活 checkout 上限、接合门禁后再 merge）。对已搬迁的 server worktree 先 `repair` 再 `prune`，去掉 Documents 幽灵登记。server 删除已合入分支 `backup-wal-keeper`、`release-0.3.1`、`feature/subscriber-execution-foundation`，并撤掉 api-01 / api-v03 / backup / release 四个 checkout。kids 修了同样的 gitdir 漂移后撤掉 asset-inventory、server-deploy、thin-client、salvage、harness；本地删除已合入的 `codex/asset-inventory-v1`、`codex/card-os-server-deploy`、`codex/card-os-thin-client-v1`、`codex-part-a-edgeone-miniprogram-ready`。thin-skill worktree 留着：有未提交的 07-16 library 计划/设计改动。接合合同未写代码。

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md` | 本 commit 新增 |
| kids | `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md` | 本 commit |
| kids | `docs/README.md`、`docs/ai/README.md`、`PROJECT_CONTEXT.md`、`AGENTS.md` | ADR-003 引用，本 commit |
| kids | 五个已退役 worktree 目录 | 已从磁盘移除 |
| server | worktree 登记与三个已合入本地分支 | repair/prune/remove/`branch -d`；无代码 commit |

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `~/projects/family/kids-visual-learning-pack` `main` | 规范与任务；不存知识 revision |
| 知识存储 | `.worktrees/cognitive-card-server-knowledge-core` @ `1facb79` | 四对象 authoring；勿与 IMPL 混 merge |
| 四卡执行 | `.worktrees/cognitive-card-server-api-01-impl-2` @ `878a28d` | generation-input；接合测试前保持隔离 |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；不在本批改 |
| 例外 | `.worktrees/card-os-thin-skill-v1` | 脏；未强制删除 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server `worktree repair` + `prune` | PASS | 5 条 family 路径登记修复；tmp subscriber 幽灵登记已 prune |
| server 活 `worktree list` | PASS | 仅 main、knowledge-core、generation-input |
| server `branch -d` 已合入 | PASS | 删除 backup-wal-keeper / release-0.3.1 / subscriber-execution-foundation |
| kids `worktree repair` + remove | PASS | 5 个 worktree 已撤；thin-skill 因脏文件拒绝无 force 删除 |
| kids `branch -d` 已合入 | PASS | asset-inventory、server-deploy、thin-client、part-a |
| 独立提交分支仍在 | PASS | salvage、thin-skill、harness、api-01-core-snapshot、remote-api-v03 |
| 未 `--force` thin-skill | PASS | 2 modified + 3 untracked 07-16 docs |
| 未 merge / push / 现网 | PASS | |
| kids `git diff --check` | PASS | 文档更新后 |
| `bash scripts/ai/check-handoff.sh` | PASS | 见本批结束验证 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 既有 secret 字段名与文档复核到期，与本批无关 |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交 `docs/cognitive-card-os-roadmap.md`、`docs/superpowers/specs/2026-07-16-cognitive-card-client-production-library-design.md`，以及三份 07-16 plan 未跟踪文件。

## Risks and Caveats

- 先 repair 再 prune 是硬顺序；对 Documents 旧路径直接 prune 会毁掉 family checkout。
- server 主工作区仍在 `~/Documents/Codex/...`，与本机 `~/projects` 约定不一致；本批未搬迁。
- origin 仍有 `codex-part-a-edgeone-miniprogram-ready`；只删了本地分支。
- 接合合同未实现：两条 server 功能分支仍必须隔离。

## Remaining Work

1. 用户决定 thin-skill 脏文档：提交到该分支、迁到治理仓、或丢弃后再 `worktree remove`。
2. 下一产品任务：generation-input lock 摘要四对象 revision（新 CURRENT_TASK，新 integration worktree）。
3. 未授权前不要 push/merge/deploy。

## Exact Next Action

先更新 `CURRENT_TASK.md` 再开接合合同实施。在那之前不要 merge `codex/knowledge-core-contract-v1` 与 `codex/api-01-generation-input-v1`。若先处理 thin-skill 脏工作区：打开 `.worktrees/card-os-thin-skill-v1`，决定那 5 个文件去留，然后再撤 checkout。不要 `--force`。不要 push。

## Recovery Notes

- kids：`/Users/admin/projects/family/kids-visual-learning-pack`；本批治理文档在此 commit。
- 活 server：knowledge-core `1facb79`；generation-input `878a28d`；main `c2a898c`。
- 保留无 checkout 的分支：`codex/card-os-salvage-v1`、`codex/harness-v1`、`codex/api-01-core-snapshot`、`codex/remote-api-v03`。
- tag：`archive/card-os-thin-skill-v1-20260717`。
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
