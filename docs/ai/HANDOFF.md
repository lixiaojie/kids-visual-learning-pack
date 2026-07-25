# Latest Handoff

## Metadata

- Updated At: 2026-07-25
- Agent: OpenAI Codex
- Branch: codex/project-doc-governance
- Base Commit: c4237d2（扩大修复范围前的 clean HEAD）
- Working Tree: 扩大范围修复完成，用户已授权提交当前 9 个路径；恢复时先运行 `git status --short`
- Task Status: Done（治理实现、既有 validation failure 修复、完整验证与独立 re-review 均完成；本轮 commit 已获授权）

## Summary

本分支以 `81f6a7f` 为基线完成跨模型文档治理闭环：`PROJECT_CONTEXT.md` 提供稳定读取顺序，`docs/README.md` 提供正式文档地图，`docs/ai/` 保持动态任务和交接真值，archive manifest 保留两份被明确替代的历史文档，项目内 memory 只保存人工筛选的次级 Markdown 快照。

whole-branch final review 发现 4 个 Important 与 2 个 Minor。fix wave 已把文档日期转换为严格 UTC epoch day，强制 `due > last` 且 `due - last <= 31`，并仅依据 `today - last > 31` 产生 overdue WARN；archive manifest 的两条映射改为 fail-closed 精确验证；`PROJECT_CONTEXT.md` 纳入纯文档豁免。连续 re-review 后，Hook 最终在 `mktemp -d` 中物化完整 index，运行快照自身的 infra checker，并将 Git 查询绑定到原始 index；准备或检查任一步失败都阻断提交，staged `.gitignore` 隐藏的同路径 recreation 也不能绕过。设计、计划与 docs map 已同步为 Approved/Implemented、Completed、Implemented/Completed。

最终复核确认 index-snapshot 代码与 4/4 fixture 已关闭原 Hook finding，同时指出 design/plan 仍把行为写成“拒绝所有 partial staging”。本次仅同步正式文档为真实行为：验证完整 index snapshot，拒绝工作树掩盖暂存损坏，同时允许合法 partial staging；Hook 实现未再修改。

整分支 reviewer 最终确认原 6 项与后续文档漂移全部关闭，结论为 `Ready to merge: Yes`。随后按 `finishing-a-development-branch` 运行全项目 `npm run validate`，在 `validate:interaction-graph` 发现 6 个 `cicada-life` representative object visual-slot 错误；同一失败已在 `main` 工作区复现，因此不是本治理分支引入。按 finishing gate，在全项目 suite 绿色前不提供 merge/push 菜单。

2026-07-25 用户已授权扩大范围修复上述基线。根因核实表明，2026-05-17 引入的验证规则只接受通用 `representativeObjects` slot，而 2026-06-03 有意 materialize 的 6 个 `cicada-life` exact bindings 分别指向 lifecycle、molting、task 与 compare slot；它们均以 `hotspot` 聚焦对象自身，且同时包含对象自身的 active region 与 materialized region。运行时 strict diagnostics 对这些绑定为零错误，因此修复目标是消除验证器与运行时契约漂移，不回退专题数据。

interaction-graph 修复采用 fail-closed 双路径：通用 representative-object slot 继续通过；精确 slot 仅在 slot 确实存在，且 `hotspot`、active region 与 materialized region 都指向对象自身时通过。新增临时隔离 fixture 先复现 6 项 RED，再验证当前 6 项正例、移除 `cicadaEggs` 自身 active focus 以及引用不存在 slot 的两类反例。

完整 suite 随后暴露两个同源的 Scene Deck 迁移漂移。第一，`cicada-life` 已有意压缩为 5 个 authored navigation stages，但 legacy normalizer 只按同名 graph stage 取 blocks，导致 `inspect` 和 `tasks` 内容丢失；现改为把当前 authored stage 到下一个 authored stage 之间的 graph stages 合并到同一 stage。第二，alignment validator 仍要求旧 `LearningFlowRail`、`resolveTopicPresentation` 与 `ComparePairCard`；现改为检查 Web/小程序当前 `SceneDeckTopicPage` 的 runtime、导航、focus evidence、visual regions、content blocks、tasks/feedback，以及每个含 compare evidence 的 topic 均有可解释的 `compare-split` scene。最终 `npm run validate` 全绿。

独立终审首轮发现 3 个 Important。修复后，折叠来源 stage 不同于 authored stage 时 block ID 会纳入 graph stage，duplicate/unknown authored stage 直接失败，并以 authored stage 重排 fixture 证明不会重复或错配 graph blocks；alignment wrapper 以隔离 repo fixture 证明只有 import/comment、或字符串形式的伪 JSX 而无真实 JSX render 会失败，compare scene 使用非 `comparePairs.*` focus 或空 explanation 也会失败；interaction-graph 另增加 exact focus 指向不存在 slot 的反例。re-review 进一步发现伪 JSX 字符串边界，现已补充 RED→GREEN，JSX 检查会剥离注释和字符串字面量。最终窄 re-review 为 PASS，Critical/Important/Minor 均为 0，`Ready to finish: Yes`。

实施计划的日期为 2026-07-24，实际收口和本 HANDOFF 更新发生在 2026-07-25；Metadata 使用实际日期，不回填计划日期。

## Completed

- Task 1：新增稳定根索引、正式 docs map 和跨模型读取顺序。
- Task 2：将 `docs/spec-v1.md` 与 `docs/architecture-iteration-v1.2.md` 原样归档至 `docs/archive/2026-07-24-doc-governance/`，并记录 replacement。
- Task 3：新增筛选的 memory 索引、耐久规则和两份 rollout 摘要；不复制全局 memory、原始会话、凭证或私有配置。
- Task 4：新增并接入只读文档治理 checker；fixture 13/13 通过；review fix 覆盖严格日期、外部 URI、`mktemp` fail-closed 和单一失败隔离。
- Task 5：完成 inventory、隐私扫描、完整验证集、CURRENT_TASK Done 收口和本 HANDOFF 动态状态刷新。
- Whole-branch final-review fix wave：文档治理 fixture 扩展到 18/18，Hook fixture 扩展到 4/4；2099 due、超过 31 天、manifest 缺行/错配、staged broken/worktree clean、staged deletion/same-path recreation（含被 staged `.gitignore` 忽略）均不能通过，恰好 31 天、PROJECT_CONTEXT-only staged 与无关 untracked 保持通过。

## Changed Files

final-review fix wave 开始时 `HEAD=1b0fe83` 且工作区 clean；content fix 为 `9e5c040`，status record 为 `ef405e8`，首轮 re-review fix 为 `f20ea87`，其 status record 为 `45bb139`，最终 index-snapshot fix 为 `6ef6887`。下表为累计 final wave 文件：

| File | Change | Reason |
| --- | --- | --- |
| `.githooks/pre-commit` | 修改 | 对完整 index snapshot 运行 infra checker；PROJECT_CONTEXT 纳入豁免 |
| `AGENTS.md` | 修改 | 同步 targeted tests 与 Hook 行为 |
| `docs/README.md` | 修改 | design/plan 状态改为 Implemented/Completed |
| `docs/ai/README.md` | 修改 | 记录日期、manifest 与 Hook 检查边界 |
| `docs/ai/CURRENT_TASK.md` | 修改 | 记录 final-review fix wave 与验证 |
| `docs/ai/HANDOFF.md` | 修改 | 记录实际修复、验证与提交边界 |
| `docs/superpowers/plans/2026-07-24-project-documentation-governance-implementation.md` | 修改 | 标记 Completed，勾选已执行步骤，修正旧路径验证与 index-snapshot 行为描述 |
| `docs/superpowers/specs/2026-07-24-project-documentation-governance-design.md` | 修改 | 标记 Approved/Implemented，并说明完整 index snapshot 会拒绝掩盖暂存损坏但允许合法 partial staging |
| `package.json` | 修改 | 增加 `test:pre-commit`，并将 interaction-graph 入口接到正反例回归 wrapper |
| `scripts/ai/check-agent-infra.sh` | 修改 | 登记 Hook 测试资产 |
| `scripts/ai/check-doc-governance.sh` | 修改 | UTC day/31 天与 manifest fail-closed 检查 |
| `scripts/ai/test-doc-governance.sh` | 修改 | 新增日期与 manifest 对抗 fixture |
| `scripts/ai/test-pre-commit.sh` | 新建 | 隔离 Git repo 的 Hook 回归测试 |
| `scripts/validate-interaction-graph.mjs` | 修改 | 允许具备自身 hotspot/active/materialized region 的精确对象绑定 |
| `scripts/validate-interaction-graph.test.mjs` | 新建 | 隔离临时 fixture 覆盖 exact-focus 正例与缺 focus 反例 |
| `packages/kids-content/src/normalize-topic-interaction.ts` | 修改 | 将被 5 阶段 authored flow 折叠的 graph stages 合并回相邻导航阶段 |
| `scripts/normalize-topic-interaction.test.ts` | 修改 | 锁定 5 阶段导航不丢 classification/objects 与 compare/tasks blocks |
| `scripts/validate-content-alignment.mjs` | 修改 | 以当前 Scene Deck runtime/UI/compare-scene 代替 legacy TopicPage 符号检查 |
| `scripts/validate-content-alignment.test.mjs` | 新建 | 隔离验证真实 JSX render、comparePairs focus 与非空 explanation 的负向边界 |

## Decisions Made

- `PROJECT_CONTEXT.md` 保持稳定薄索引；`docs/ai/HANDOFF.md` 是唯一动态交接真值，不新增根级 HANDOFF。
- `docs/README.md` 是正式文档唯一导航地图；无明确替代证据的历史文档仍保留为 Historical Reference 或 Needs Review。
- memory 快照仅为人工筛选的次级材料；代码、测试和正式仓库文档优先，且不自动同步用户级 memory。
- 归档保留历史并记录 replacement，不删除文档。
- 文档治理采用任务事件更新和 31 天复核 WARN，不使用 cron 或读取用户目录。
- `Next Review Due` 是最长 31 天周期的结构化声明；overdue 只由 `today - Last Reviewed` 决定，远期 due 不能延长周期。
- Hook 的 infra 检查读取临时物化的完整 index snapshot；`GIT_DIR` 指向原仓库、`GIT_WORK_TREE` 指向快照，使 Git 查询与文件读取都对应待提交状态。targeted Hook test 不接入统一五步入口。
- 用户已授权本 feature branch 的 Task 1–5 commits；push、merge 和 PR 仍未授权。
- 用户已授权扩大当前任务范围修复既有 `cicada-life` interaction-graph failure；验证规则仍须 fail-closed，只允许通用对象 slot 或在精确 slot 上明确聚焦对象自身 region 的 binding。
- 2026-07-25 用户已明确授权提交扩大范围修复；该授权不包含 push、merge 或 PR。

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| `bash -n`（本轮改动 shell/Hook） | PASS | checker、两组 test、infra/state 与 Hook 语法通过 |
| `npm run test:doc-governance` | PASS | 18/18 fixture，含 2099 due、31 天边界、manifest 缺行/错配 |
| `npm run test:pre-commit` | PASS | 4/4：staged broken/worktree clean、两类 staged deletion/same-path recreation 拒绝；PROJECT_CONTEXT-only + unrelated untracked 通过 |
| `npm run check:doc-governance` | PASS | required files、精确 archive mappings、受路由链接和复核日期均通过 |
| `bash scripts/ai/check-agent-infra.sh` | WARN | 0 FAIL；既有 secret-field-name 人工复核 WARN |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL；仅既有 secret-field-name 人工复核 WARN，handoff/doc/task/diff steps PASS |
| `bash scripts/ai/check-handoff.sh` | PASS | content commit 前 Base Commit 与 `45bb139` 一致，非空工作区描述一致 |
| `npm run validate:interaction-graph` | PASS | 隔离 fixture 覆盖 6 个 exact-focus 正例、缺少自身 active focus 与不存在 slot 两类反例 |
| `npm run test:topic-interaction` | PASS | 5 阶段导航保留完整 blocks，ID 唯一；重排、duplicate、unknown 与 strict focus diagnostics 通过 |
| `npm run validate:alignment` | PASS | 13 topics/16 package files；comment-only、string-only、错误 compare focus、空 explanation 四类反例通过 |
| `npm run validate` | PASS | 13 topic/overlay、230 assets、evidence、interaction、scene deck/UI、kids-content、miniprogram、alignment 全部通过 |
| 独立最终 re-review | PASS | Critical 0、Important 0、Minor 0；`Ready to finish: Yes` |
| active old-path Markdown link probe | PASS | 两个旧 active path 均无 Markdown link target；历史普通文本说明合法 |
| `git diff --check` | PASS | content commit 前无空白错误 |
| `git status --short` | NON-CLEAN（预期） | 当前 9 个扩大范围修复路径待最终审查与用户 commit 授权 |
| `node boards/kids-world/structure.test.mjs` | 未重跑 | 已知既有 `19 !== 18`；本任务未改 `boards/`，不可表述为本轮验证 |

## Known Failures

- `node boards/kids-world/structure.test.mjs` 存在既有断言失败 `19 !== 18`。本任务未运行该命令、未修改 `boards/`，故该问题不影响本轮文档治理验证结论。

## Risks and Caveats

- `check-agent-state.sh` 的 secret-field-name WARN 来自既有代码和文档的字段名提及；高置信 secret-value 扫描通过。本任务未弱化该扫描。
- `check-doc-governance.sh` 的 BSD 日期路径已在当前 macOS 环境执行；GNU fallback 仅静态兼容实现，未在本轮运行。
- Task 5 内容提交为 `a9007bb`，后续修正到 `1b0fe83`；final-review 与 re-review 提交链已延伸到 `6ef6887`。恢复时只把 `git rev-parse HEAD` 的结果视为当前符号 HEAD。
- tracked HANDOFF 不能自编码包含其自身的 commit hash；后续 status-only commit 只记录该事实、提交链和 clean state，不表示有待提交工作。

## Remaining Work

1. 实现、验证和独立审查均无剩余工作。
2. 执行用户已授权的本地 commit。
3. commit 后按 `finishing-a-development-branch` 提供 merge/push/keep 选择；push、merge、PR 仍需单独授权。

## Exact Next Action

若 `git status --short` 仍非空，执行已授权的本地 commit；若已 clean，则向用户提供 merge/push/keep 选择。

## Recovery Notes

- 分支基线为 `81f6a7f`；Task 1 完成于 `6c87d6f`，Task 2 于 `c2aeded`，Task 3 于 `49efcff`，Task 4 初版于 `2f49ce8`、review fix 于 `8c8545d`，Task 5 内容提交为 `a9007bb`，whole-branch review fix 起点为 `1b0fe83`。
- Task 4 ledger 记录 review clean；Task 5 的运行记录位于本 worktree 的 `.superpowers/sdd/2026-07-24-project-documentation-governance-implementation/`，不作为仓库交接真值。
- 未执行 push、merge、rebase、reset、删除操作或业务代码、CI、部署、用户级 memory 的修改。
- final-review content fix 为 `9e5c040`，首个 status record 为 `ef405e8`，首轮 re-review fix 为 `f20ea87`，对应 status record 为 `45bb139`，最终 index-snapshot fix 为 `6ef6887`，后续状态记录为 `ce7ba4f` 与 `cbb3d36`。本 formal-doc sync commit 只修正文档行为描述；其自身 hash 不能被同一 tracked HANDOFF 自编码。恢复任何后续状态均先运行 `git rev-parse HEAD` 与 `git status --short`；不执行 push、merge、rebase 或 PR。
