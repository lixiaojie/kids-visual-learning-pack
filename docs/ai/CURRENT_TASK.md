# Current Task

## Metadata

- Updated At: 2026-07-25
- Updated By: OpenAI Codex
- Status: In Progress
- Branch: main
- Base Commit: 3e0d392

## Objective

参考“成长打卡”项目与 `fp-project` 工作区的文档治理结构，建立完全位于本仓库内的跨模型协作上下文：根级项目索引、统一文档地图、当前任务与交接状态、历史文档归档、精选 Codex memory 快照，以及可机械检查的定期更新机制，确保 Claude Code、OpenAI Codex、Kimi Code 或其他模型工具可以从仓库事实无缝继续工作。

在治理任务完成并进入 finishing 验证后，修复阻断全项目 `npm run validate` 的既有 `cicada-life` interaction-graph 基线问题，同时保留精确 visual focus 绑定的运行时语义。

完成用户授权的本地合并、`main` 推送和静态站点生产部署；若部署门禁暴露既有构建问题，以最小修复恢复规范构建路径，并在重新推送后完成线上验收。

## Background

用户已批准治理闭环方案、精选 memory 项目内快照和有替代证据的历史文档归档，并已明确授权 `codex/project-doc-governance` 上 Task 1–5 的 feature-branch commits。2026-07-25 用户进一步授权扩大范围，修复 `main` 同样存在的 `cicada-life` interaction-graph validation failure；随后明确授权合并回 `main`、推送并部署到生产服务器。

## Acceptance Criteria

- [x] 根级 PROJECT_CONTEXT.md 提供稳定薄索引，不复制动态任务状态
- [x] docs/README.md 成为正式文档唯一导航地图，标注文档角色与状态
- [x] `AGENTS.md`、`docs/ai/README.md`、`docs/ai/START_PROMPTS.md` 写明跨模型必读顺序和定期更新规则
- [x] 项目相关 Codex memory 以精选 Markdown 快照保存于 docs/knowledge/codex-memory/，并标明来源、快照性质、`Last Reviewed`、`Next Review Due` 和冲突优先级
- [x] 有明确替代证据的旧文档移入带 manifest 的 docs/archive/2026-07-24-doc-governance/，现行入口不再路由到旧版本
- [x] scripts/ai/check-doc-governance.sh 检查规范入口、索引目标、两条 archive 映射与严格 31 天复核周期，并接入统一检查入口
- [x] `.githooks/pre-commit` 对完整 index snapshot 运行 infra checker，任何快照准备或检查失败均 fail-closed，且 `PROJECT_CONTEXT.md`-only 暂存不强制 HANDOFF
- [x] 不复制原始会话 JSONL、凭证、私有配置或整个全局 memory 树
- [x] 不修改 Card OS 实现、CI 或部署配置
- [x] `bash scripts/ai/check-doc-governance.sh` 与 `git diff --check` PASS；`bash scripts/ai/check-agent-state.sh` 为 0 FAIL，WARN 已记录
- [x] `docs/ai/HANDOFF.md` 基于实际修改和验证结果更新
- [x] `validate:interaction-graph` 接受绑定到通用 representative-object slot 的对象，也接受在精确 slot 上以自身 region 明确聚焦的对象
- [x] 不通过放宽“任意 slot 均合法”或将 `cicada-life` 退回信息更弱的通用 slot 消除错误
- [x] `npm run validate:interaction-graph` PASS
- [x] 5 阶段 Scene Deck learning flow 在 legacy normalizer 中保留全部 inspect/task blocks
- [x] 折叠后的 block ID 保持唯一，duplicate/unknown authored stage fail-closed，重排 authored navigation 不造成 graph block 重复或错配
- [x] alignment validator 检查当前 Scene Deck runtime，不再要求已废弃的旧 TopicPage 组件符号
- [x] alignment 负向 fixture 拒绝“只有 import/comment/伪 JSX 字符串而没有真实 JSX”、非 comparePairs focus 与空 compare explanation
- [x] `npm run validate` PASS
- [x] `codex/project-doc-governance` fast-forward 合并回 `main` 并推送到 `origin/main`
- [x] 部署脚本通过仓库规范 `build:kids-world` 命令加载根 `vite.config.ts`
- [x] 部署构建回归测试先 RED 后 GREEN
- [x] `npm run build`、`npm run check:dist` 与完整验证 PASS
- [ ] 修复提交推送到 `origin/main`，`npm run deploy` 完成生产同步
- [ ] 公开生产 URL 完成有界 HTTP 验收

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
- `scripts/validate-interaction-graph.mjs`
- `scripts/validate-interaction-graph.test.mjs`
- `packages/kids-content/src/normalize-topic-interaction.ts`
- `scripts/normalize-topic-interaction.test.ts`
- `scripts/validate-content-alignment.mjs`
- `scripts/validate-content-alignment.test.mjs`
- `package.json`（仅调整 interaction-graph targeted regression 入口）
- `scripts/deploy.sh`（仅修复 kids-world 规范构建入口）
- `scripts/deploy.test.mjs`
- `package.json`（仅增加部署回归入口与部署前门禁）

## Out of Scope

- `cicada-life` 内容、图片和运行时交互语义的重写
- 其他 topic、`apps/`、`ops/`、`skills/`、`tests/` 下的无关实现
- `outputs/` 既有未跟踪目录
- CI、Nginx、Card OS 服务端 release、生产服务器系统服务与非静态站点目录
- 用户级 `~/.codex/memories/`、`~/.claude/` 或其他客户端私有配置
- 自动复制整个 memory 树或原始会话 JSONL
- 没有明确替代证据的历史文档批量移动
- PR、强制推送、历史重写或非本任务分支集成

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
- 已完成扩展范围的 RED 与根因核实：旧验证器要求 representative object 只能绑定通用 `representativeObjects` slot；后续有意加入的 6 个 `cicada-life` 精确绑定均使用 `hotspot`，且 `activeRegionIds` 与 materialized region 都包含对象自身。运行时严格诊断已通过，证明问题位于验证规则而非内容缺失。
- 已完成 interaction-graph RED→GREEN：新增隔离临时 fixture，正向验证 6 个 exact-focus binding；负向移除 `cicadaEggs` 自身 active focus 或将其指向不存在的 slot 后都必须失败。
- 完整验证继续暴露并修复两个同源基线漂移：Scene Deck 将导航压缩为 5 阶段后，legacy normalizer 会丢弃 `inspect` 与 `tasks` blocks；alignment validator 仍检查已被 Scene Deck 替代的旧 TopicPage 符号。当前 normalizer 按相邻 authored stage 区间合并 graph stages，alignment 改检 Web/小程序 Scene Deck 的导航、focus、region、content、task 和 compare-scene 契约。
- 独立审查首轮发现 3 个 Important：折叠 stage 的 block ID 重复且 authored stage 缺少 duplicate/unknown 防御；Scene Deck 源码检查可被注释 token 绕过；compare scene 未确认真实 `comparePairs.*` focus。修复均已完成：block ID 纳入来源 graph stage，authored stage fail-closed，并新增顺序重排/唯一性/duplicate/unknown 回归；alignment wrapper 新增 JSX 缺失、伪 JSX 字符串、错误 compare source 与空 explanation 的隔离反例，JSX 检查会忽略注释与字符串字面量。
- 最终窄 re-review 确认首轮 findings 与 string-only 伪 JSX边界全部关闭，Critical/Important/Minor 均为 0，结论为 `Ready to finish: Yes`。
- `npm run validate` 已完整 PASS，覆盖 13 topic/overlay、230 assets、evidence、interaction、scene deck/UI、TypeScript、miniprogram 与 alignment。
- Task 2 的旧路径验证已收窄为 active Markdown link target；历史治理说明中的普通文本路径保留合法。
- 实施计划日期为 2026-07-24；实际收口发生在 2026-07-25，故本文件使用实际更新日期而非计划日期。
- `codex/project-doc-governance` 已 fast-forward 合并到本地 `main`，合并后 `npm run validate` PASS，feature worktree 与本地分支已清理，`origin/main` 已推进到 `3e0d392`。
- 首次 `npm run deploy` 在任何 rsync 前失败：`scripts/deploy.sh` 直接执行未带根配置的 Vite 命令，无法解析仅由根 `vite.config.ts` 提供 alias 的 `@yutou/kids-content`；规范 `npm run build:kids-world` 已在同一环境成功，证明部署脚本与规范构建命令发生漂移。

## Next Actions

1. 为部署脚本规范构建入口增加失败回归测试并确认 RED。
2. 将 `scripts/deploy.sh` 切换为 `npm run build:kids-world`，确认 targeted GREEN。
3. 运行完整 build/validation/shutdown checks，提交并推送 `main`。
4. 重新执行 `npm run deploy`，随后对生产 URL 做有界 HTTP 验收。

## Verification Plan

- Build: `npm run build` + `npm run check:dist`
- Full Project Validation: `npm run validate` PASS
- Unit Tests:
  - `npm run test:doc-governance`：PASS（18/18 fixture）
  - `npm run test:pre-commit`：PASS（4/4 隔离 Git fixture）
- Integration Tests: `npm run validate:alignment` PASS；Web/小程序均检查当前 Scene Deck runtime contract
- Targeted Regression:
  - `npm run validate:interaction-graph` PASS；隔离 fixture 证明 exact-focus 正例通过，缺少自身 active focus 或引用不存在 slot 的反例失败
  - `npm run test:topic-interaction` PASS；覆盖 5 阶段合并、block ID 唯一、authored stage 重排、duplicate 与 unknown
  - `npm run validate:alignment` PASS；隔离 fixture 拒绝 comment-only、string-only 伪 render、错误 compare focus 与空 explanation
- Lint: 仓库未确认通用 lint 命令
- Manual Checks:
  - `rg --files -g '*.md' -g '!node_modules/**' -g '!.worktrees/**' | sort`：本轮完成；正式文档均有路由或受控根/客户端适配说明
  - 隐私路径扫描（绝对本机路径与 raw rollout path metadata key）：PASS（零命中）
  - `bash -n`（本轮所有改动 shell/Hook）：PASS
  - `npm run check:doc-governance`：PASS
  - `bash scripts/ai/check-agent-state.sh`：WARN，0 FAIL；仅既有 secret-field-name 人工复核 WARN
  - `bash scripts/ai/check-handoff.sh`：PASS（content commit 前）
  - `git diff --check`：PASS（content commit 前）
  - `git status --short`：扩大范围修复当前包含 9 个未提交路径；符合无新增 commit 授权时的预期状态

## Relevant References

- `AGENTS.md`
- `PROJECT_CONTEXT.md`
- `docs/README.md`
- `docs/ai/HANDOFF.md`
- `docs/archive/README.md`
- `docs/knowledge/codex-memory/README.md`
- `docs/superpowers/specs/2026-07-24-project-documentation-governance-design.md`
- `docs/superpowers/plans/2026-07-24-project-documentation-governance-implementation.md`
