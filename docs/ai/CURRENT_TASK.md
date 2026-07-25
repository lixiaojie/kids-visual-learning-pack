# Current Task

## Metadata

- Updated At: 2026-07-25
- Updated By: OpenAI Codex
- Status: Done
- Branch: codex/project-doc-governance
- Base Commit: 81f6a7f

## Objective

参考“成长打卡”项目与 `fp-project` 工作区的文档治理结构，建立完全位于本仓库内的跨模型协作上下文：根级项目索引、统一文档地图、当前任务与交接状态、历史文档归档、精选 Codex memory 快照，以及可机械检查的定期更新机制，确保 Claude Code、OpenAI Codex、Kimi Code 或其他模型工具可以从仓库事实无缝继续工作。

## Background

用户已批准治理闭环方案、精选 memory 项目内快照和有替代证据的历史文档归档，并已明确授权 `codex/project-doc-governance` 上 Task 1–5 的 feature-branch commits；push、merge 和 PR 仍未授权。

## Acceptance Criteria

- [x] 根级 PROJECT_CONTEXT.md 提供稳定薄索引，不复制动态任务状态
- [x] docs/README.md 成为正式文档唯一导航地图，标注文档角色与状态
- [x] `AGENTS.md`、`docs/ai/README.md`、`docs/ai/START_PROMPTS.md` 写明跨模型必读顺序和定期更新规则
- [x] 项目相关 Codex memory 以精选 Markdown 快照保存于 docs/knowledge/codex-memory/，并标明来源、快照性质、`Last Reviewed`、`Next Review Due` 和冲突优先级
- [x] 有明确替代证据的旧文档移入带 manifest 的 docs/archive/2026-07-24-doc-governance/，现行入口不再路由到旧版本
- [x] scripts/ai/check-doc-governance.sh 检查规范入口、索引目标与 31 天复核周期，并接入统一检查入口
- [x] 不复制原始会话 JSONL、凭证、私有配置或整个全局 memory 树
- [x] 不修改业务代码、Card OS 实现、CI 或部署配置
- [x] `bash scripts/ai/check-doc-governance.sh` 与 `git diff --check` PASS；`bash scripts/ai/check-agent-state.sh` 为 0 FAIL，WARN 已记录
- [x] `docs/ai/HANDOFF.md` 基于实际修改和验证结果更新

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
- push、merge 或 PR

## Constraints

- 保留现有未提交基础设施改动，不覆盖或回退无关内容
- 根级动态状态只保留一个真值源：`docs/ai/HANDOFF.md`，不新增第二份根级 HANDOFF
- PROJECT_CONTEXT.md 只保存稳定索引；动态任务状态继续由 `docs/ai/CURRENT_TASK.md` 与 `docs/ai/HANDOFF.md` 维护
- memory 快照为次级检索路径；与代码、测试或正式文档冲突时，以仓库当前事实为准
- 归档不删除历史；manifest 必须记录原路径、归档路径、原因与替代文档
- 定期更新采用任务事件驱动与 31 天复核提醒，不自动从用户目录复制内容
- 文档与脚本使用 UTF-8；命令、文件名和 API 名称保留英文

## Current State

- 已完成 Task 1：新增稳定根索引、正式 docs map，并更新跨模型读取顺序。
- 已完成 Task 2：归档两份有明确替代证据的文档，并以 archive manifest 记录替代关系。
- 已完成 Task 3：新增精选项目内 Codex memory 快照，只涵盖 Card OS 部署运维和本地 Skill 安装经验。
- 已完成 Task 4：新增只读文档治理 checker、13 项隔离 fixture、统一入口和 npm 便捷命令；review fix 已完成并记录为 clean。
- 已完成 Task 5：全量 Markdown inventory、隐私路径扫描、完整文档治理验证、动态交接收口和 shutdown checks。
- 本轮 inventory 未发现漏路由或误分类的正式文档；`docs/README.md` 无需调整。
- 实施计划日期为 2026-07-24；实际收口发生在 2026-07-25，故本文件使用实际更新日期而非计划日期。

## Next Actions

1. 对整个 feature branch 做独立终审。
2. 审核通过后，按 `finishing-a-development-branch` 的交付选择完成后续操作；不得在未经授权时 push、merge 或创建 PR。

## Verification Plan

- Build: 本任务仅涉及文档与基础设施脚本，不运行全量业务构建
- Unit Tests: `bash scripts/ai/test-doc-governance.sh` 本轮 PASS（13/13 fixture）
- Integration Tests: 不适用
- Lint: 仓库未确认通用 lint 命令
- Manual Checks:
  - `rg --files -g '*.md' -g '!node_modules/**' -g '!.worktrees/**' | sort`：本轮完成；正式文档均有路由或受控根/客户端适配说明
  - 隐私路径扫描（绝对本机路径与 raw rollout path metadata key）：PASS（零命中）
  - `bash scripts/ai/check-doc-governance.sh`：PASS
  - `bash scripts/ai/check-agent-state.sh`：WARN，0 FAIL；既有 secret-field-name 人工复核 WARN 与 HANDOFF 提交链信息级 WARN 已记录
  - `bash scripts/ai/check-handoff.sh`：WARN，0 FAIL；tracked HANDOFF 的提交链信息级 WARN 已记录
  - `git diff --check`：PASS
  - `git status --short`：收口前 clean；提交后复核

## Relevant References

- `AGENTS.md`
- `PROJECT_CONTEXT.md`
- `docs/README.md`
- `docs/ai/HANDOFF.md`
- `docs/archive/README.md`
- `docs/knowledge/codex-memory/README.md`
- `docs/superpowers/specs/2026-07-24-project-documentation-governance-design.md`
- `docs/superpowers/plans/2026-07-24-project-documentation-governance-implementation.md`
