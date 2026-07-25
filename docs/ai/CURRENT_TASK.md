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
- [x] scripts/ai/check-doc-governance.sh 检查规范入口、索引目标、两条 archive 映射与严格 31 天复核周期，并接入统一检查入口
- [x] `.githooks/pre-commit` 对完整 index snapshot 运行 infra checker，任何快照准备或检查失败均 fail-closed，且 `PROJECT_CONTEXT.md`-only 暂存不强制 HANDOFF
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
- `scripts/ai/test-doc-governance.sh`
- `scripts/ai/test-pre-commit.sh`
- `scripts/ai/check-agent-infra.sh`
- `scripts/ai/check-agent-state.sh`
- `.githooks/pre-commit`
- `package.json`（仅增加 targeted 检查便捷命令）
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
- 已完成 Task 4：新增只读文档治理 checker、统一入口和 npm 便捷命令；终审 fix wave 将 fixture 扩展为 18 项，覆盖 UTC epoch day、31 天边界、远期 due、manifest 缺行/错配与既有严格日期/链接场景。
- 已完成 Task 5：全量 Markdown inventory、隐私路径扫描、完整文档治理验证、动态交接收口和 shutdown checks。
- 已完成 whole-branch final-review fix wave 及后续 re-review 修复：Hook 在临时目录物化完整 index snapshot，并从快照运行 infra checker；4 项隔离 Git fixture 覆盖 staged broken/worktree clean、同路径 untracked recreation、被 staged `.gitignore` 忽略的同路径 recreation，以及 PROJECT_CONTEXT-only 豁免。design、plan 与 docs map 状态统一为 Implemented/Completed，计划已执行 checklist 全部按提交与报告证据勾选。
- 整分支独立终审已通过并给出 `Ready to merge: Yes`。finishing 阶段随后运行全项目 `npm run validate`，在 `validate:interaction-graph` 发现 6 个既有 `cicada-life` visual-slot 错误；同一失败已在 `main` 工作区复现，本治理分支未修改相关业务文件。
- Task 2 的旧路径验证已收窄为 active Markdown link target；历史治理说明中的普通文本路径保留合法。
- 实施计划日期为 2026-07-24；实际收口发生在 2026-07-25，故本文件使用实际更新日期而非计划日期。

## Next Actions

1. 由用户决定是否另行扩展范围，修复 `main` 已存在的 `cicada-life` interaction-graph 基线问题。
2. 基线问题修复后重跑 `npm run validate`；全项目 suite 绿色后再进入 `finishing-a-development-branch` 的 merge/push/keep 选择。

## Verification Plan

- Build: 本任务仅涉及文档与基础设施脚本，不运行全量业务构建
- Full Project Validation: `npm run validate` 在 `validate:interaction-graph` FAIL；6 个 `cicada-life` representative object 未使用 `representativeObjects` visual slot，同样在 `main` 复现，属于本任务范围外的既有基线问题
- Unit Tests:
  - `npm run test:doc-governance`：PASS（18/18 fixture）
  - `npm run test:pre-commit`：PASS（4/4 隔离 Git fixture）
- Integration Tests: 不适用
- Lint: 仓库未确认通用 lint 命令
- Manual Checks:
  - `rg --files -g '*.md' -g '!node_modules/**' -g '!.worktrees/**' | sort`：本轮完成；正式文档均有路由或受控根/客户端适配说明
  - 隐私路径扫描（绝对本机路径与 raw rollout path metadata key）：PASS（零命中）
  - `bash -n`（本轮所有改动 shell/Hook）：PASS
  - `npm run check:doc-governance`：PASS
  - `bash scripts/ai/check-agent-state.sh`：WARN，0 FAIL；仅既有 secret-field-name 人工复核 WARN
  - `bash scripts/ai/check-handoff.sh`：PASS（content commit 前）
  - `git diff --check`：PASS（content commit 前）
  - `git status --short`：content commit 前仅包含本轮 13 个授权文件；提交后继续复核

## Relevant References

- `AGENTS.md`
- `PROJECT_CONTEXT.md`
- `docs/README.md`
- `docs/ai/HANDOFF.md`
- `docs/archive/README.md`
- `docs/knowledge/codex-memory/README.md`
- `docs/superpowers/specs/2026-07-24-project-documentation-governance-design.md`
- `docs/superpowers/plans/2026-07-24-project-documentation-governance-implementation.md`
