# Current Task

## Metadata

- Updated At: 2026-08-30
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: main（kids 治理）；server 功能分支未合并
- Base Commit: kids `34d5bbc`；knowledge-core `1facb79`；IMPL-2 `878a28d`；server main `c2a898c`

## Objective

按已确认的知识管线（Knowledge Core 存储 → 选择 Learning/Projection → 再生成展示产物）治理工作区，并收敛过多分支与 worktree。本批落地三角色规则、安全退役已合入/冗余 checkout，以及接合合同的书面立项。不实现接合代码，不把 knowledge-core 与 generation-input 合成一条分支，不 push、不现网。

## Background

- 用户 2026-08-30 确认：核心目标是知识生产管线、存储知识源、再选择映射展示形态；工作区按该管线治理，而不是按 IMPL 编号合并。
- 同一对话要求分支适当收敛。收敛前 kids 7 个 worktree、server 8 个登记（多数仍指向搬迁前 Documents 路径）。
- 两套知识模型仍并存：四对象 authoring vs FACT/generation-input。接合合同是下一实施批次。

## Acceptance Criteria

- [x] ADR-003 记录三角色、活 worktree 上限、合并顺序与接合门禁
- [x] kids 文档地图与 `AGENTS.md` 可检索到 ADR-003
- [x] 已搬迁的 server worktree 完成 `git worktree repair`；缺失路径 `prune`
- [x] 已合入 main 或对活分支冗余的 checkout 已移除；含独立提交的抢救/PUBLISH 分支只撤 worktree、保留分支名
- [x] 活 checkout 为目标三角色；kids 额外保留 `card-os-thin-skill-v1`（有未提交文档，未 `--force` 删除）
- [x] 未删除 salvage / thin-skill / remote-api-v03 / api-01-core-snapshot 等仍有独立提交的分支
- [x] 未实现接合代码；未 merge 两条 server 功能分支；未 push/deploy/现网
- [x] `docs/ai/HANDOFF.md` 用真实 `git worktree list` 与验证结果更新

## In Scope

- kids：`docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`、`docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`、`docs/README.md`、`docs/ai/README.md`、`PROJECT_CONTEXT.md`、`AGENTS.md`（约束引用）
- kids / server：`git worktree repair|prune|remove` 与对已合入分支的 `git branch -d`
- 只读盘点：两仓分支、worktree、与 main 的包含关系

## Out of Scope

- generation-input 改为摘要四对象 revision 的实现与测试
- 新建或 merge `knowledge-pipeline-v1`
- 把 knowledge-core 与 IMPL-2 合成一次提交
- 删除仍有独立提交的分支；删除 origin 上的 `codex-part-a-edgeone-miniprogram-ready`
- `--force` 删除含未提交修改的 thin-skill worktree
- 把 server 主工作区移出 `~/Documents/Codex/...`
- push / merge 到 server `main` / deploy / 现网 HTTPS
- KNOW-01、AGE-01、ACCEPT-01、Portal、Renderer、新 Skill release

## Constraints

- 一个任务一个活 worktree；归档靠 tag/分支名，不靠长期 checkout。
- `git branch -d` 仅用于已是 main 祖先的分支；禁止 `-D`。
- 先 `repair` 再 `prune`，避免把 family 下仍在用的 server checkout 登记删掉。
- catalog `registry_commit` 仍不改。

## Verification Plan

- 执行后 `git worktree list`（kids 与 server）与分类表一致
- 被删本地分支：删除前为 main 祖先
- kids：`git diff --check`、`bash scripts/ai/check-handoff.sh`、`bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md` §13、§18
