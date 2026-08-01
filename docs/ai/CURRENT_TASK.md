# Current Task

## Metadata

- Updated At: 2026-08-01
- Updated By: Kimi Code
- Status: In Progress
- Branch: main（实施在服务器应用仓新分支）
- Base Commit: d205388

## Objective

实施 API-01-IMPL-1(core snapshot)：按已确认设计 §5/§14.1，从抢救分支 `codex/card-os-salvage-v1` 的 `skills/cognitive-card-os/core/`（34 文件）生成完整的 `cognitive-card-core-snapshot-v1` manifest（每成员 path/mode/size_bytes/sha256、成员按 UTF-8 路径字节升序、root digest、snapshot_id、source identity、origin commit、生成工具版本），在服务器应用仓以受治理资产形式导入 `core-snapshots/<snapshot_root_sha256>/` 并建立只增不改的 snapshot catalog，配套闭包校验工具与固定测试向量、全部负向用例。本批次不触碰服务器应用行为（零 HTTP 面、零运行时变更）。

## Background

- API-01 修订设计已于 2026-08-01 获用户书面确认（`docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`,Approved)；实施按 §16 分批，每批单独立项，本批为 IMPL-1。
- 用户已授权本批立项与后续 push(kids 仓 main 已 push 至 `d205388`)。
- 快照来源：抢救分支 `codex/card-os-salvage-v1`（尖端 `4d5ffe4`,core/ 自 `7f321a6` 起未变）；现有 `source-manifest.json` 只有 27/34 文件带摘要，不能直接充当内容寻址 manifest（设计 §5.1)。
- 服务器应用仓：`/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server`,main @ `c2a898c`（生产 0.3.1，干净）;worktree 惯例使用 kids 仓 `.worktrees/`（已被忽略）。
- `registry_commit` 规则：记录**首次引入该不可变 snapshot 的精确服务器仓 commit**（设计 §5.2)。

## Acceptance Criteria

- [ ] 快照生成工具（Python 3 标准库）从干净、精确 commit 的 checkout 读取 34 文件，打开后复核 stat;dirty tree、错误 commit、symlink、绝对路径/`.`/`..`/空段/反斜杠/NUL、未声明文件一律拒绝
- [ ] manifest 满足设计 §5.1：除自身外每成员 path/mode/size_bytes/sha256；成员 UTF-8 路径字节升序；`snapshot_root_sha256 = sha256(canonical_json(member_records))`;`snapshot_id = "sha256:" + root`;schema、source identity、origin commit、工具版本为说明字段（不进 root digest)
- [ ] 固定测试向量：同一输入跨两次生成 root digest 逐字节一致；manifest canonical JSON（排序键、紧凑分隔符、末尾单换行）
- [ ] 快照导入服务器仓 `core-snapshots/<snapshot_root_sha256>/`（含 manifest 与全部成员文件，root-owned 语义在部署时保证）；重复导入仅允许逐字节相同的幂等复核
- [ ] snapshot catalog（只增不改）记录 `registry_commit`/`snapshot_id`/`manifest_schema`/`state`(active)；格式与设计 §5.2 一致
- [ ] 负向用例全覆盖：缺失、篡改、额外文件、symlink、dirty/wrong commit、路径替换、重复声明、非 canonical manifest
- [ ] 服务器应用现有测试套件全绿（零行为变更的证明）；新工具测试全绿
- [ ] 抢救分支、存档 tag/worktree 零修改；每个可验证阶段更新 HANDOFF

## In Scope

- 服务器应用仓（新任务分支 + worktree):`core-snapshots/`、`tools/`（或仓内等价工具目录）、对应测试目录的新增内容
- kids 仓：`docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`(API-01 进展记录）

## Out of Scope

- 服务器应用任何运行时/HTTP/DB 变更（IMPL-2/3 的事）；编译器（IMPL-2);executor(IMPL-4)；验收（IMPL-5)
- 生产部署与任何现网操作；服务器仓 origin push（需用户另行授权）
- `e78c2fa`（package-v5 接纳面，PUBLISH-01）与其 worktree
- 抢救分支、存档 tag/worktree、kids 仓其他 worktree 的在途状态
- RENDER-01/QA-01/PUBLISH-01

## Constraints

- 生成只从干净、精确 commit 的 checkout 读取；manifest 生成与校验两个实现路径（生成器输出必须经独立校验器复核）
- 成员内容与摘要不进日志/审计以外的任何地方；快照中不含凭据（生成器含凭据形状扫描则更好，参照 builder 既有规则）
- 每个可验证单元 RED → 最小 GREEN → 聚焦测试 → review → commit，不揉提交
- 不改变服务器 `0.3.1` 任何已部署行为；`c2a898c` 保持生产运行版本

## Current State

- 2026-08-01：任务建立；服务器仓分支与 worktree 未创建。

## Next Actions

1. 服务器仓建分支 `codex/api-01-core-snapshot` 与 worktree(kids `.worktrees/`)。
2. RED：先写快照 manifest 固定向量与闭包负向测试，再实现生成/校验工具转 GREEN。

## Verification Plan

- Unit: 新工具与导入/catalog 测试（服务器仓 `python3 -m unittest discover -s tests` 或仓内既有等价入口）
- Regression: 服务器应用既有全套测试（零行为变更）
- Governance(kids 仓）:`bash scripts/ai/check-agent-state.sh`、`git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`(Approved,§5/§14.1/§16)
- 抢救分支 codex/card-os-salvage-v1（快照来源，只读）
- 服务器应用仓 commit `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`（基线）
