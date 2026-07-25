# 跨模型项目文档治理设计

- Date: 2026-07-24
- Status: Approved/Implemented
- Scope: repository documentation governance and read-only validation infrastructure
- Related Task: `docs/ai/CURRENT_TASK.md`

## 1. Objective

把项目基础信息、规划上下文、当前任务、最近进度、长期决策、运维事实和可复用经验全部保存在项目目录内，并建立清晰的真值层级与更新机制，使任意 Coding Agent 不依赖某个客户端的会话历史或隐藏全局状态即可继续工作。

本设计参考两个已存在的本地项目模式：

- “成长打卡”参考项目的 `AGENTS.md + docs/ai/` 任务状态闭环；
- `fp-project` 参考工作区的根级薄索引、统一 docs map、归档 manifest 和项目内 Codex memory 快照。

采用“治理闭环”方案：任务事件驱动更新负责日常连续性，31 天复核提醒负责长期清理；memory 只人工筛选，不自动整库复制。

Implementation evidence: Task 1–5 landed on `codex/project-doc-governance` in commits `2d7b987` through `1b0fe83`; the final-review fix wave hardens the 31-day interval, archive mappings, and Hook index/worktree consistency.

## 2. Pre-Implementation State and Gaps (Historical)

设计批准时，仓库已有但尚未提交的基础设施包括：

- `AGENTS.md`：跨 Agent 唯一通用规则源；
- `CLAUDE.md`：Claude Code 适配层；
- `docs/ai/CURRENT_TASK.md`、`HANDOFF.md`、`BACKLOG.md`、`START_PROMPTS.md`；
- `docs/decisions/ADR-TEMPLATE.md`；
- `scripts/ai/` 状态检查脚本；
- `.githooks/pre-commit`；
- `package.json` 中的 Agent 基础设施命令。

主要缺口：

1. 根目录没有稳定的项目上下文薄索引；
2. `docs/` 没有统一导航和文档状态标记；
3. 现行与历史版本混在同一活动路径；
4. 项目经验部分只存在于 `~/.codex/memories/`；
5. 文档和 memory 没有定期复核门禁；
6. 新模型虽能找到任务文件，但不容易判断应该先读哪些长期文档。

## 3. Sources of Truth

真值优先级沿用并收敛为：

1. 可执行代码和正式配置；
2. 自动化测试；
3. 构建、部署和生产运维配置；
4. 已接受的架构文档、ADR、规范性系统设计；
5. `README.md`、`PROJECT_CONTEXT.md`、`docs/README.md` 等稳定索引；
6. `docs/ai/CURRENT_TASK.md`；
7. `docs/ai/HANDOFF.md`；
8. 项目内 Codex memory 快照；
9. Agent 会话内容。

索引文件只负责导航，不得覆盖代码、测试或正式设计。memory 快照只提供检索线索和复用经验，不是当前实现真值。

## 4. Information Architecture

```text
/
├── README.md                    # 产品用途、运行方式、协作文档入口
├── AGENTS.md                    # 唯一跨模型工程规范
├── PROJECT_CONTEXT.md           # 稳定薄索引，不保存动态任务进度
└── docs/
    ├── README.md                # 正式文档唯一导航地图
    ├── ai/
    │   ├── CURRENT_TASK.md      # 当前唯一执行任务
    │   ├── HANDOFF.md           # 最近一次可靠交接
    │   ├── BACKLOG.md           # 未启动事项
    │   └── START_PROMPTS.md     # 跨模型启动与交接提示词
    ├── knowledge/
    │   └── codex-memory/
    │       ├── README.md        # 来源、边界、更新时间、复核日期
    │       ├── memory_summary.md
    │       └── rollout-summaries/
    │           ├── Card OS 部署经验
    │           └── 本地 Skill 安装经验
    ├── archive/
    │   ├── README.md            # 统一归档 manifest
    │   └── 2026-07-24-doc-governance/
    ├── decisions/               # ADR
    ├── superpowers/specs|plans/ # 正式设计与实施计划
    ├── operations/              # 运维真值
    └── compliance/              # 合规真值
```

不新增根级 `HANDOFF.md`。动态交接仍以 `docs/ai/HANDOFF.md` 为唯一真值，避免同一状态维护两份。

## 5. File Responsibilities

### 5.1 Root Entry Points

- `README.md`：回答“这是什么、如何运行”，只增加一段跨模型入口。
- `AGENTS.md`：回答“所有 Agent 必须遵守什么”，加入文档治理和更新周期。
- `PROJECT_CONTEXT.md`：回答“仓库有哪些模块、当前长期方向、接手时先读什么”，保持精简稳定。

### 5.2 Documentation Map

`docs/README.md` 按以下类别组织：

- Canonical Current Docs；
- Current Task and Handoff；
- Active Product and Architecture Docs；
- Active Plans；
- Operations and Compliance；
- Historical Reference；
- Needs Review；
- Codex Memory Snapshots；
- Archive Policy。

每条至少包含路径、角色和状态。目录不复制正文，也不把历史报告描述为当前实现。

### 5.3 Task State

- `CURRENT_TASK.md`：唯一当前任务范围和验收标准；
- `HANDOFF.md`：最近一次可靠状态、真实验证和 Exact Next Action；
- `BACKLOG.md`：尚未进入执行范围的事项；
- Card OS 动态专项任务继续由 `docs/cognitive-card-os-roadmap.md` 维护，`BACKLOG.md` 只引用。

## 6. Codex Memory Snapshot

### 6.1 Included Content

首批只包含与本仓库直接相关的两类经验：

1. Card OS subagent-driven deployment ops；
2. 本地 Cognitive Card OS Skill ZIP 安装。

保存内容：

- 一份项目级 `memory_summary.md`；
- 两份已整理的 rollout summary Markdown；
- `README.md` 中的来源、用途、刷新流程和冲突优先级。

### 6.2 Excluded Content

不得复制：

- 整个全局 `MEMORY.md`；
- 原始 rollout JSONL 或会话日志；
- Key、Token、Cookie、OAuth 凭证；
- 用户级客户端配置；
- 与本项目无关的其他项目记忆；
- 只对某台机器临时有效且无复用价值的状态。

### 6.3 Snapshot Semantics

`docs/knowledge/codex-memory/README.md` 必须声明：

- `~/.codex/memories/` 是 Codex 的全局来源；
- 仓库内文件是人工筛选的时间点快照；
- 代码、测试和正式仓库文档优先；
- 快照可能过期，使用前应按任务风险重新验证；
- `Last Reviewed` 和 `Next Review Due` 使用 `YYYY-MM-DD`。

## 7. Archive Policy

### 7.1 Eligibility

只有满足至少一项明确证据才可归档：

- 新文档明确声明替代旧版本；
- 版本号和内容关系能够证明新版本是现行基线；
- 计划已完成且现行入口已有稳定替代；
- 正式决策把旧方案标为 Superseded 或 Deprecated。

不得因为“看起来旧”就移动文件。

### 7.2 Initial Archive Set

首批明确归档：

- `docs/spec-v1.md`，替代文档为 `docs/spec-v2.md`；
- `docs/architecture-iteration-v1.2.md`，替代文档为 `docs/architecture-iteration-v1.3.md`。

首批不移动：

- `docs/2026-05-11-kids-world-refactor-design.md`；
- `docs/2026-05-11-kids-world-refactor-plan.md`；
- `docs/architecture-review-v1.md`；
- 仍被现行设计引用或没有明确替代证据的其他文档。

这些文件先在 `docs/README.md` 标为 Historical Reference 或 Needs Review。

### 7.3 Manifest

`docs/archive/README.md` 对每个归档文件记录：

| Original Path | Archived Path | Date | Reason | Replacement |
| --- | --- | --- | --- | --- |

归档只移动，不删除历史内容。受影响的现行引用必须改指向替代文档或 archive manifest。

## 8. Update Lifecycle

### 8.1 Event-Driven Updates

- 新任务启动：更新 `CURRENT_TASK.md`；
- 可验证阶段结束、阻塞或切换模型：更新 `HANDOFF.md`；
- 项目结构、命令或长期方向改变：更新 `PROJECT_CONTEXT.md` 和 `docs/README.md`；
- 新增、移动、取代正式文档：同步更新 docs map 和 archive manifest；
- 产生仓库尚未记录的可复用经验：人工筛选后更新 memory 快照；
- 长期架构决定：新增 ADR，不只写入 HANDOFF 或 memory。

### 8.2 Periodic Review

每月首次项目工作或距 `Last Reviewed` 超过 31 天时，执行：

1. 检查 `PROJECT_CONTEXT.md` 与实际目录；
2. 检查 `docs/README.md` 的链接、角色和状态；
3. 检查活动文档是否存在明确被取代项；
4. 检查 archive manifest 和替代指针；
5. 检查是否有新的项目相关 memory 值得筛选；
6. 更新 `Last Reviewed` 和 `Next Review Due`；
7. 运行统一 Agent 状态检查。

不使用 cron 或脚本自动从用户目录复制 memory。过期只产生提醒，由 Agent 或维护者审阅后更新。

## 9. Validation Infrastructure

已实现 `scripts/ai/check-doc-governance.sh`，并接入 `check-agent-infra.sh` 与 `check-agent-state.sh`；`.githooks/pre-commit` 另以 targeted fixture 覆盖 index/worktree 一致性，不接入统一五步入口。

检查范围：

- 必需入口存在；
- docs map、archive manifest、memory README 存在；
- docs map 中的仓库相对 Markdown 路径存在；
- archive manifest 的两条明确映射必须逐项包含 original path、archive path、reason 和 replacement，缺行或错配时 `FAIL`；
- `Last Reviewed` 与 `Next Review Due` 必须以 BSD/GNU `date` 严格 UTC round-trip 解析；
- `Next Review Due` 必须晚于 `Last Reviewed` 且间隔不超过 31 天；
- `today - Last Reviewed > 31` 时输出 `WARN`，不能用远期 `Next Review Due` 绕过；
- 必需文件缺失或索引目标不存在时输出 `FAIL`；
- 脚本只读，不移动、不生成、不刷新任何文件。

`package.json` 提供以下便捷命令：

```text
check:doc-governance
test:doc-governance
test:pre-commit
```

`test:pre-commit` 在 `mktemp -d` 下创建隔离 Git repo，验证 Hook 对完整 index snapshot 执行基础设施检查：暂存损坏内容或暂存删除不能被工作树中的 tracked、untracked 或 ignored 同路径文件掩盖，且 `PROJECT_CONTEXT.md`-only 暂存属于 HANDOFF 豁免。Hook 语义允许 index snapshot 自身合法的 partial staging；当前 fixture 不把所有合法 partial-staging 形态列为覆盖项。不增加 CI，不运行全量业务构建。

## 10. Cross-Model Recovery Flow

新模型的统一读取顺序：

```text
AGENTS.md
→ PROJECT_CONTEXT.md
→ docs/README.md
→ docs/ai/CURRENT_TASK.md
→ docs/ai/HANDOFF.md
→ 当前任务相关的设计、ADR、代码和测试
```

`START_PROMPTS.md` 提供可复制提示词，要求模型在修改前报告仓库根目录、分支、未提交改动、任务范围、验收标准、Exact Next Action 和预计修改范围。

## 11. Security and Privacy

- 不把内部代码或文档发送到外部服务；
- 不复制凭证或用户级配置；
- 快照中的绝对路径只在说明来源确有必要时使用，项目内导航统一使用仓库相对路径；
- 复制 rollout summary 前执行疑似密钥字段扫描，只保留整理后的 Markdown；
- 如果内容是否适合进入 Git 不明确，则不复制并在 HANDOFF 记录。

## 12. Implementation Scope

新增：

- `PROJECT_CONTEXT.md`
- `docs/README.md`
- `docs/archive/README.md`
- `docs/archive/2026-07-24-doc-governance/`
- `docs/knowledge/codex-memory/**`
- `scripts/ai/check-doc-governance.sh`
- 本设计对应实施计划

修改：

- `README.md`
- `AGENTS.md`
- `docs/ai/README.md`
- `docs/ai/START_PROMPTS.md`
- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `scripts/ai/check-agent-infra.sh`
- `scripts/ai/check-agent-state.sh`
- `package.json`
- 因归档产生的现行 Markdown 引用

不修改业务代码、Card OS 实现、测试、CI、部署配置或 `outputs/`。

## 13. Acceptance and Verification

完成时必须满足：

1. 新模型按统一读取顺序可以找到项目事实、当前任务、最近进度和相关设计；
2. 主要 Markdown 均能从 `docs/README.md` 定位并理解角色与状态；
3. 活动入口不再把已归档版本描述为现行文档；
4. memory 快照带来源、复核日期和冲突优先级；
5. `today - Last Reviewed > 31` 产生 `WARN`，复核间隔超过 31 天、manifest 缺行/错配、缺失入口或断链产生 `FAIL`；
6. 不含凭证、原始会话 JSONL或无关项目 memory；
7. `HANDOFF.md` 记录实际修改、验证、风险、剩余工作和 Exact Next Action；
8. 以下命令通过：

```bash
bash scripts/ai/check-doc-governance.sh
bash scripts/ai/test-doc-governance.sh
bash scripts/ai/test-pre-commit.sh
bash scripts/ai/check-agent-state.sh
git diff --check
```

并使用定向 `rg` 验证旧路径只保留在 archive manifest 或历史正文语境中。

## 14. Alternatives Rejected

### Lightweight Index Only

只新增索引和快照，不增加更新规则与检查。维护成本最低，但会再次出现状态过期，不能满足“确保定期更新”。

### Fully Automated Sync

用 CI、cron 或脚本自动复制全局 memory。自动化程度高，但可能复制隐私、噪声或过期状态，也会错误地让快照看起来像实时真值，因此不采用。

## 15. Open Issues

无阻塞设计问题。实施过程中若发现其他历史文档可能失效但缺少明确替代证据，只标为 Needs Review，不扩大本轮归档范围。
