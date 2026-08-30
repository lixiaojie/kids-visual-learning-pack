# ADR-003: 知识管线工作区角色与分支收敛

- Status: Accepted
- Date: 2026-08-30
- Owners: 项目所有者（2026-08-30 对话确认：按 Knowledge Core → Projection 选择治理工作区，并收敛过多分支）
- Related Task: `docs/ai/CURRENT_TASK.md`（知识管线工作区治理与分支收敛）
- Related Files: `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`、`docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`、`docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md`、`AGENTS.md`

## Context

Card OS 施工曾按 IMPL 编号和抢救切片开隔离分支。到 2026-08-30，kids 仓同时挂着 7 个 worktree，server 仓登记 8 个 worktree，其中多数仍指向仓库搬迁前的 `~/Documents/kids-visual-learning-pack` 路径。这使「下一个该改哪」变成会话记忆，而不是管线角色。

产品目标已由 ADR-002 固定：先存储 Knowledge Core，再选择 Learning / Projection，最后才生成展示产物。server 上同时存在四对象 authoring（`codex/knowledge-core-contract-v1`）和四卡 generation-input（`codex/api-01-generation-input-v1`）。按 Git 把两条功能分支合成「服务器大分支」会把两套知识模型焊在一起。

因此需要一条工作区规则：角色按管线划分，checkout 是临时工位，归档靠 tag 与分支名。

## Decision

1. **三角色，不三角产品线。**
   - kids `kids-visual-learning-pack`：治理与产品规范（ADR、路线图、任务、薄 Skill 合同、H5 看板）。不保存知识权威 revision。
   - `cognitive-card-server`：知识权威。持久化四对象 revision、current pointer、Projection 选择，以及已锁定 Projection 的执行链。
   - 薄 Skill：packet 领取与提交。不编译事实，不拥有知识库。
2. **活 checkout 上限。** 同一时刻每个角色最多一个活任务 worktree。Card OS 常态允许的 server checkout 只有：主工作区（现网对应的 `0.3.1` / `main`）、知识存储任务、四卡执行任务。接合合同落地后，存储与执行必须收成**一条**集成分支上的**一个** worktree。kids 常态只在 `main` 工作；kids `.worktrees/` 只为当前未完成的 kids 任务存在。
3. **合并顺序。** 先保留 knowledge-core 与 generation-input 为两条隔离分支。只有测试证明 generation-input lock 摘要的是四对象精确 revision（而不是平行 FACT 文件）之后，才允许开 `knowledge-pipeline-v1` 一类集成分支并按「存储先、执行后」迁入。禁止为了工作区干净而提前 merge。
4. **归档方式。** 已合入 main 的本地分支用 `git branch -d` 删除；仍有独立提交、但当前无任务的切片（抢救 thin-skill、PUBLISH package-v5、harness 残余）保留分支名，撤掉 worktree。历史靠已有 tag（如 `archive/card-os-thin-skill-v1-20260717`）和分支尖端，不靠长期 checkout。
5. **禁止把 server checkout 的产品身份藏进 kids 目录语义。** `.worktrees/cognitive-card-server-*` 只是本机放置约定，权威仓库仍是 `cognitive-card-server`。搬迁后必须 `git worktree repair`，不得对仍存在的目录先 `prune`。

## Alternatives Considered

### Option A: 把 kids、knowledge-core、IMPL-2 合成一个仓或一次 merge

优点：表面分支最少。缺点：治理文档、知识合同和四卡执行链的提交历史与回滚边界消失；两套知识模型被焊死。未采用。

### Option B: 继续按 IMPL-N 无限开 worktree，完成也不撤

优点：零协调成本。缺点：路径在仓库搬迁后漂移成 prunable；Agent 无法从 `git worktree list` 判断活任务。未采用。

### Option C: 三角色 + 活 checkout 上限 + 接合门禁后再集成

优点：对齐 ADR-002 管线，收敛磁盘上的僵尸工位，同时保住未合入的抢救与 PUBLISH 提交。缺点：在接合合同实现前仍会暂时保留两条 server 功能分支。采用。

## Consequences

### Positive

- 下一个任务能从角色表判断该打开哪一个目录。
- 已合入切片不再占用 worktree。
- 接合合同成为显式门禁，而不是 merge 时的即兴决定。

### Negative

- 接合完成前仍有两条 server 功能分支，需要交接层写清。
- 撤 worktree 后，要改旧切片必须重新 `git worktree add`。

### Risks

- 对 Documents 旧路径执行 `prune` 可能毁掉 family 下仍用同一 gitdir 的 checkout。必须先 `repair`。
- 误删仍有独立提交的 salvage / `remote-api-v03` 分支会破坏 ADR-001 的抢救入口。本 ADR 禁止对这些分支使用 `-D`。

## Migration or Rollout

1. 书面盘点两仓分支与 worktree 相对 main 的包含关系。
2. 对已搬到 `~/projects/family/kids-visual-learning-pack/.worktrees/` 的 server checkout 执行 `git worktree repair`，再 `prune` 真正缺失的路径。
3. 移除已合入 main 的 kids/server worktree，并对这些分支 `git branch -d`。
4. 对仍有独立提交、当前无任务的分支只 `git worktree remove`，保留分支。
5. 接合合同作为独立实施任务，不在本 ADR 落地时代码化。

## Verification

- `git worktree list`：kids 仅 `main` 为常态；server 仅主工作区 + knowledge-core + generation-input（接合完成前）。
- 被 `branch -d` 的名字在删除前满足 `git merge-base --is-ancestor <branch> main`。
- `codex/card-os-salvage-v1`、`codex/card-os-thin-skill-v1`、`codex/remote-api-v03`、`codex/api-01-core-snapshot` 分支名仍存在。
- 本 ADR 被 `docs/README.md` 与 `AGENTS.md` 引用。

## References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md` §13、§18
- `docs/cognitive-card-os-roadmap.md`
