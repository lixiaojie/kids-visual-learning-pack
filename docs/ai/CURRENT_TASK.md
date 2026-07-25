# Current Task

## Metadata

- Updated At: 2026-07-25
- Updated By: OpenAI Codex
- Status: In Progress
- Branch: codex/project-doc-governance
- Base Commit: 81f6a7f

## Objective

参考“成长打卡”项目与 `fp-project` 工作区的文档治理结构，建立完全位于本仓库内的跨模型协作上下文：根级项目索引、统一文档地图、当前任务与交接状态、历史文档归档、精选 Codex memory 快照，以及可机械检查的定期更新机制，确保 Claude Code、OpenAI Codex、Kimi Code 或其他模型工具可以从仓库事实无缝继续工作。

## Background

仓库已经有一批尚未提交的多 Agent 基础设施：`AGENTS.md`、`CLAUDE.md`、`docs/ai/`、`docs/decisions/`、`scripts/ai/`、`.githooks/` 和 `package.json` 便捷命令。现状缺口是：

- 没有根级薄索引，模型需要在 `README.md` 与 `docs/ai/` 之间自行推断入口；
- 没有统一 docs 文档地图标注各文档角色、状态和替代关系；
- 项目相关经验仍部分只存在于 `~/.codex/memories/`；
- 历史版本与现行文档混在 `docs/` 活动路径；
- 尚未建立“每个任务收尾 + 每月复核”的文档与 memory 更新闭环。

用户已批准治理闭环方案、精选 memory 项目内快照和有替代证据的历史文档归档。

## Acceptance Criteria

- [ ] 根级 PROJECT_CONTEXT.md 提供稳定薄索引，不复制动态任务状态
- [ ] docs/README.md 成为正式文档唯一导航地图，标注文档角色与状态
- [ ] `AGENTS.md`、`docs/ai/README.md`、`docs/ai/START_PROMPTS.md` 写明跨模型必读顺序和定期更新规则
- [ ] 项目相关 Codex memory 以精选 Markdown 快照保存于 docs/knowledge/codex-memory/，并标明来源、快照性质、`Last Reviewed`、`Next Review Due` 和冲突优先级
- [ ] 有明确替代证据的旧文档移入带 manifest 的 docs/archive/2026-07-24-doc-governance/，现行入口不再路由到旧版本
- [ ] scripts/ai/check-doc-governance.sh 检查规范入口、索引目标与 31 天复核周期，并接入统一检查入口
- [ ] 不复制原始会话 JSONL、凭证、私有配置或整个全局 memory 树
- [ ] 不修改业务代码、Card OS 实现、CI 或部署配置
- [ ] `bash scripts/ai/check-doc-governance.sh`、`bash scripts/ai/check-agent-state.sh` 与 `git diff --check` 通过
- [ ] `docs/ai/HANDOFF.md` 基于实际修改和验证结果更新

## In Scope

- PROJECT_CONTEXT.md
- `README.md`（仅增加跨模型协作入口）
- `AGENTS.md`（仅增加文档治理与必读顺序）
- docs/README.md
- `docs/ai/README.md`
- `docs/ai/START_PROMPTS.md`
- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- docs/archive/**
- docs/knowledge/codex-memory/**
- `docs/superpowers/specs/2026-07-24-project-documentation-governance-design.md`
- `docs/superpowers/plans/2026-07-24-project-documentation-governance-implementation.md`
- scripts/ai/check-doc-governance.sh
- `scripts/ai/check-agent-infra.sh`
- `scripts/ai/check-agent-state.sh`
- `package.json`（仅增加文档治理检查便捷命令）
- 因归档导致的现行 Markdown 引用修正

## Out of Scope

- `boards/`、`apps/`、`packages/`、`ops/`、`skills/`、`tests/` 下的业务与 Card OS 实现
- `outputs/` 既有未跟踪目录
- CI、部署配置与生产环境
- 用户级 `~/.codex/memories/`、`~/.claude/` 或其他客户端私有配置
- 自动复制整个 memory 树或原始会话 JSONL
- 没有明确替代证据的历史文档批量移动
- git commit / push / merge / PR（除非用户另行明确要求）

## Constraints

- 保留现有未提交基础设施改动，不覆盖或回退无关内容
- 根级动态状态只保留一个真值源：`docs/ai/HANDOFF.md`，不新增第二份根级 HANDOFF
- PROJECT_CONTEXT.md 只保存稳定索引；动态任务状态继续由 `docs/ai/CURRENT_TASK.md` 与 `docs/ai/HANDOFF.md` 维护
- memory 快照为次级检索路径；与代码、测试或正式文档冲突时，以仓库当前事实为准
- 归档不删除历史；manifest 必须记录原路径、归档路径、原因与替代文档
- 定期更新采用任务事件驱动与 31 天复核提醒，不自动从用户目录复制内容
- 文档与脚本使用 UTF-8；命令、文件名和 API 名称保留英文

## Current State

- 已完成：启动协议核实；读取本仓库及两个参考项目的入口、任务、交接、索引和归档结构；筛选项目相关 memory；用户批准并审阅书面设计；实施计划已落盘并完成覆盖、自洽和未完成标记自审
- 进行中：用户已授权 Subagent-Driven 所需的 feature branch、基线 commit 与隔离 worktree；准备从实施计划 Task 1 开始
- 尚未开始：索引、归档、快照、检查脚本实施；最终验证与 HANDOFF
- 已知问题：工作区已有未提交基础设施改动；`outputs/` 为既有未跟踪目录；既有 `node boards/kids-world/structure.test.mjs` 失败 `19 !== 18` 与本任务无关

## Next Actions

1. 按实施计划执行 Task 1：建立根级索引、docs map 与治理规范。
2. 每个任务完成 implementer、task reviewer 与必要 fix/re-review 后再进入下一任务。
3. 完成 Task 1–5、broad final review 与最终验证；不 push、不 merge，除非另行授权。

## Verification Plan

- Build: 本任务仅涉及文档与基础设施脚本，不运行全量业务构建
- Unit Tests: 不修改业务实现，不运行业务单元测试
- Integration Tests: 不适用
- Lint: 仓库未确认通用 lint 命令
- Manual Checks:
  - `bash scripts/ai/check-doc-governance.sh`
  - `bash scripts/ai/check-agent-state.sh`
  - 对归档前后引用执行定向 `rg`
  - 检查 memory 快照不含凭证、本地私有配置和原始会话
  - `git diff --check`
  - `git status --short`

## Relevant References

- `AGENTS.md`
- `docs/ai/README.md`
- `docs/ai/HANDOFF.md`
- `docs/project-structure.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/superpowers/specs/2026-07-24-project-documentation-governance-design.md`
- `docs/superpowers/plans/2026-07-24-project-documentation-governance-implementation.md`
- `fp-project` 参考工作区的根级上下文、文档地图、归档与 memory 快照结构（只读参考，不写入本仓库路径）
- “成长打卡”参考项目的多 Agent 规范、任务状态和启动提示词结构（只读参考，不写入本仓库路径）
