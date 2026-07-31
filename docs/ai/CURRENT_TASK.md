# Current Task

## Metadata

- Updated At: 2026-07-31
- Updated By: Kimi Code
- Status: In Progress
- Branch: main（实施前新建抢救任务分支与 worktree）
- Base Commit: 9ff068f

## Objective

对存档分支 `codex/card-os-thin-skill-v1`（封存于 tag `archive/card-os-thin-skill-v1-20260717` = `7f321a6`）的可抢救资产完成**盘点与修复**小切片：从 archive tag 另起抢救分支，修复 publisher fixture 失同步与过时 mode pin 使分支测试套件转绿，逐项处置误提交的 `.superpowers` 文件、3 个未跟踪计划与 library-design 未提交修订，产出抢救清单（资产→目标批次映射）与 package-v5 两个评审 Block 的修复方案文档。本切片**不**迁移 `core/`、**不**合入任何资产到 main、**不**触碰服务器。

## Background

2026-07-31 SKILL-02 完成（生产 stable `0.1.1`,release gate 已提交，SKILL-02 保持 IN PROGRESS 等待第二台真实 Codex 电脑——用户侧动作）。按 roadmap 2026-07-31 记录（用户书面决定）：存档分支抢救**优先于从零重建**，执行顺序为 SKILL-02 之后、ACCEPT-01 之前。用户 2026-07-31 选定先执行小切片（盘点+修复）,`core/` 迁移与 package-v5 合入另行立项。

存档分支状态（2026-07-31 审计）：套件 386 项 = 19 errors(publisher fixture 与加固后 builder 闭包失同步，`SOURCE_TREE_CLOSURE_MISMATCH`)+ 1 failure(`validate_package_v5.py` 过时 mode pin,420 != 493)；另有 367 项通过。分支 worktree 有 2 modified + 3 untracked 既有在途修改（roadmap 旧版修正、library-design 48 行修订、3 个未跟踪计划），保持原样不得触碰。package-v5 两个评审 Block：服务端 authority 闭包可伪造、gallery revision 资产未绑定。

## Acceptance Criteria

- [ ] 抢救分支 `codex/card-os-salvage-v1` 从 tag `archive/card-os-thin-skill-v1-20260717` 创建于 `.worktrees/card-os-salvage-v1`；存档 tag 与 `.worktrees/card-os-thin-skill-v1` 全程零修改（开工与收工各核对一次 `git status` 与 tag 指向）
- [ ] publisher fixture 与 builder 闭包重新同步，publisher 模块单跑转绿（19 errors 清零）
- [ ] 过时 mode pin 修正（420 != 493 失败清零）
- [ ] 抢救分支全量套件转绿（两轮独立复跑一致；`PYTHONDONTWRITEBYTECODE=1`，结束后无 `__pycache__` 污染）
- [ ] 误提交的 `.superpowers` 文件、3 个未跟踪计划文档、library-design 未提交修订逐项处置并记录理由（处置动作限于抢救分支/主仓文档，不动存档 worktree 原件）
- [ ] 抢救清单文档：资产（production core、renderer、package-v5、审计工具、模板族等）→ 目标批次（API-01/RENDER-01/QA-01/PUBLISH-01/ACCEPT-01）映射、现状与前置修复项
- [ ] package-v5 两个评审 Block 的修复方案文档（仅方案，不实施）
- [ ] 不合入 main、不修改服务器、不进行生产操作；每个可验证阶段结束更新 HANDOFF

## In Scope

- 新抢救分支 `codex/card-os-salvage-v1` 与 worktree `.worktrees/card-os-salvage-v1`（从 archive tag `7f321a6` 创建）
- 抢救分支上的测试 fixture、发布/验证工具脚本（publisher、builder、validate_package_v5 等）修复
- 抢救清单与评审 Block 修复方案文档（随抢救分支提交，后续经评审授权后再集成 main)
- `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`（状态记录，main 侧）

## Out of Scope

- `core/` 迁移至服务器侧可信上游（另行立项，涉及服务器应用仓）
- package-v5 上传面合入 main 或服务器接纳面 `e78c2fa` 的合并与生产硬化（PUBLISH-01 批次）
- 存档 tag `archive/card-os-thin-skill-v1-20260717`、存档 worktree `.worktrees/card-os-thin-skill-v1` 及其未提交修改（只读）
- 服务器应用、Nginx、数据库、registry 的任何改动；任何生产操作
- `outputs/`、其他 worktree 的在途状态、用户级 `~/.codex/` 配置
- SKILL-02 的 DONE 条件（第二台真实 Codex 电脑，用户侧）
- push、merge、PR（需用户另行授权）;ACCEPT-01

## Constraints

- 抢救分支只做修复与文档，不改变被抢救资产的功能行为；评审 Block 只产出方案
- 修复必须让真实套件转绿，不得删除/跳过测试或用假实现掩盖失败
- 不含凭据、本机绝对路径进 Git；测试运行避免 `__pycache__` 污染
- 每个修复遵循 RED（复现失败）→ 最小修复 → 聚焦测试 → review → commit，不揉提交
- 提交前钩子要求暂存业务代码时同步更新并暂存 `docs/ai/HANDOFF.md`

## Current State

- 2026-07-31:SKILL-02 完成并收尾（main `9ff068f`)；用户选定抢救小切片；本文件建立任务。
- 抢救分支与 worktree 未创建；存档审计证据在 roadmap 2026-07-31 记录与 SKILL-02 各版 HANDOFF。

## Next Actions

1. 从 archive tag `7f321a6` 创建 `codex/card-os-salvage-v1` 与 `.worktrees/card-os-salvage-v1`，同步 `docs/ai/` 任务状态。
2. 复跑存档套件复现 19 errors + 1 failure(RED 基线），逐项修复 publisher fixture 与 mode pin。

## Verification Plan

- Focused: publisher 模块单跑、`validate_package_v5` 相关测试（修复后转绿）
- Full: 抢救分支全量 `python3 -m unittest discover -s tests`（两轮，`PYTHONDONTWRITEBYTECODE=1`)
- Archive integrity: tag 指向与存档 worktree `git status` 开工/收工核对
- Governance: `bash scripts/ai/check-agent-state.sh`、`git diff --check`

## Relevant References

- tag `archive/card-os-thin-skill-v1-20260717` = `7f321a6`（封存只读）
- `docs/cognitive-card-os-roadmap.md`（2026-07-31 记录：抢救优先与批次映射）
- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`（分支资产按批抢救）
- `docs/ai/HANDOFF.md`(SKILL-02 各阶段记录）
