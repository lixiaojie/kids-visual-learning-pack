# 多 Agent 统一工程基础设施

本目录是仓库级共享配置的核心：任务状态、交接记录、Backlog、本地配置边界和启动提示词。配合根目录 `AGENTS.md`（唯一通用规则源）与 `CLAUDE.md`(Claude Code 适配层）使用。

## 1. 为什么需要多 Agent 统一基础设施

本项目会分别通过 Claude Code、OpenAI Codex、Kimi Code 三个入口开发。不统一客户端、终端、模型或账号，但必须统一事实来源：项目事实、工程规则、当前任务、架构决策、验证标准和交接记录全部落盘在 Git 仓库中，避免项目状态只存在于某个 Agent 的会话历史里，降低切换成本。

## 2. 三层配置模型

### 第一层：仓库级共享配置（进 Git，所有 Agent 共享）

```text
AGENTS.md                  # 唯一通用规则源
PROJECT_CONTEXT.md         # 稳定根索引与规范读取顺序
CLAUDE.md                  # Claude Code 适配层(只引用,不复制)
docs/README.md             # 唯一正式文档地图与状态
docs/ai/                   # 本目录:任务、交接、Backlog、启动提示词
docs/archive/              # 已归档文档与替代指针
docs/knowledge/codex-memory/ # 人工维护的项目记忆快照
docs/decisions/            # ADR(架构决策记录)
docs/                      # 正式架构文档、superpowers/specs|plans、operations、compliance
构建/测试/校验脚本(scripts/、package.json、tests/)
格式化与部署配置(vercel.json、edgeone.json 等)
```

保存：项目事实、工程规则、当前任务、验收标准、架构决策、交接信息、可复现命令。

### 第二层：仓库级客户端适配（可进 Git，只放客户端差异）

```text
CLAUDE.md                              # Claude Code 适配(当前唯一已建立的适配文件)
.claude/ 中确认适合共享的项目配置       # 当前仓库不存在,不虚构
.codex/ 中确认适合共享的项目配置        # 当前仓库不存在,不虚构
```

规则：通用规则只以 `AGENTS.md` 为来源；适配文件尽量只引用通用规则；不维护多份内容相同的规则文件；不创建当前客户端不支持或未经验证的配置目录。

Kimi Code 的项目级能力已在当前版本核实：会自动读取项目根目录的 `AGENTS.md`，无需额外配置文件。若其他版本不支持自动加载，使用 `START_PROMPTS.md` 的启动提示词，不虚构配置。

### 第三层：用户级私有配置（不进 Git，不由基础设施修改）

各 Agent 的登录信息、API Key、OAuth Token、内部 LLM Proxy 地址、个人 MCP 配置、本机路径、Shell 配置、个人权限规则。边界详见 `LOCAL_CONFIG.md`。

## 3. 各文件职责

| 文件 | 职责 | 不是什么 |
| --- | --- | --- |
| `AGENTS.md` | 唯一通用工程规则源 | 不是任务状态，不是交接记录 |
| `PROJECT_CONTEXT.md` | 稳定根索引与规范读取顺序 | 不复制动态任务进度 |
| `docs/README.md` | 唯一正式文档地图与状态 | 不替代代码、测试、任务状态或交接记录 |
| `CLAUDE.md` | Claude Code 适配层 | 不复制 AGENTS.md 内容 |
| `docs/ai/CURRENT_TASK.md` | 当前正式任务与验收标准 | 不是需求池，不是历史记录 |
| `docs/ai/HANDOFF.md` | 最近一次可靠交接 | 不是长期架构真值 |
| `docs/ai/BACKLOG.md` | 未进入执行范围的事项 | 不是执行计划 |
| `docs/ai/LOCAL_CONFIG.md` | 本地私有配置边界说明 | 不记录任何真实凭证 |
| `docs/ai/START_PROMPTS.md` | 可复制的标准启动提示词 | 不是规则来源 |
| `docs/archive/` | 已归档文档与替代指针 | 不存放尚未证实被替代的历史文件 |
| `docs/knowledge/codex-memory/` | 人工维护的项目记忆快照 | 不替代代码、测试或正式文档 |
| `docs/decisions/ADR-TEMPLATE.md` | ADR 模板 | 不是决策本身 |
| `scripts/ai/check-agent-infra.sh` | 基础设施完整性只读检查 | 不修改文件 |
| `scripts/ai/check-task-state.sh` | CURRENT_TASK 状态一致性只读检查 | 不修改文件 |
| `scripts/ai/check-handoff.sh` | HANDOFF 时效性与完整性只读检查 | 不修改文件 |
| `scripts/ai/check-agent-state.sh` | 统一检查入口（基础设施、文档治理、任务状态、HANDOFF + `git diff --check`) | 不修改文件 |
| `scripts/ai/check-doc-governance.sh` | 文档地图、链接、状态与复核日期检查 | 不修改文件 |
| `scripts/ai/test-doc-governance.sh` | 文档治理日期、manifest 和链接的隔离 fixture 回归测试 | 只写 `mktemp -d` 临时目录 |
| `scripts/ai/test-pre-commit.sh` | Hook index snapshot 隔离、same-path recreation 与 HANDOFF 豁免的隔离 Git fixture 回归测试 | 只写 `mktemp -d` 临时目录 |
| `scripts/ai/install-hooks.sh` | 安装仓库级 Git Hook（每个 clone 一次） | 不触碰用户级配置 |
| `.githooks/pre-commit` | 提交前快速检查与 HANDOFF 强制 | 与任何特定 Agent 无关 |

与既有文档的关系（迁移后只保留一套正式机制）:

- `docs/cognitive-card-os-roadmap.md`:Card OS 专项任务账本，继续由 Card OS 工作流维护；`BACKLOG.md` 不复制其内容，只引用。
- `docs/kids-world-image-generation-handoff.md`：主题级专项交接，保留原位置；仓库级最近交接以 `docs/ai/HANDOFF.md` 为准。
- `docs/cross-renderer-decisions.md`：既有正式决策记录，保留原位置，视为 ADR 之前的决策文档；新增决策用 `docs/decisions/` 下的 ADR。
- `.superpowers/`（已被 `.gitignore` 忽略）：会话级非正式工作记录，不作为交接真值。
- `docs/knowledge/codex-memory/`：项目记忆快照仅作次级参考，必须人工整理；代码、测试和正式仓库文档冲突时优先。

## 4. 开始新任务的流程

```text
读取规则(AGENTS.md)
→ 读取稳定根索引(PROJECT_CONTEXT.md)
→ 读取文档地图(docs/README.md)
→ 读取 CURRENT_TASK
→ 读取 HANDOFF
→ 检查相关代码和文档
→ 实施
→ 验证
→ 更新 HANDOFF
```

新任务先写入 `CURRENT_TASK.md`(Objective / Acceptance Criteria / In Scope / Out of Scope / Constraints / Verification Plan)，边界明确后再实施。

## 5. 串行切换 Agent 的流程

```text
当前 Agent 完成可验证的小阶段
→ 更新 HANDOFF
→ 保持 Git 状态清晰
→ 下一 Agent 读取同一套文件(AGENTS.md / PROJECT_CONTEXT.md / docs/README.md / CURRENT_TASK / HANDOFF)
→ 继续执行
```

## 6. 多 Agent 并行流程

```text
一个任务一个分支
一个 Agent 一个 Worktree(本仓库惯例:.worktrees/ 目录,已被 .gitignore 忽略)
禁止共享同一工作目录并行修改
通过 commit / cherry-pick / merge 汇总
```

Card OS 另受 [ADR-003](../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md) 约束：kids 只做治理；知识权威在 `cognitive-card-server`；常态活 checkout 为 kids `main` + server 主工作区 + 至多两条功能工位（存储 / 四卡执行）。已完成切片撤 worktree，靠 tag 与分支名归档。搬迁后先 `git worktree repair` 再 `prune`。

## 7. 任务结束流程

1. 执行 `AGENTS.md` 第 8 节的验证要求。
2. 更新 `CURRENT_TASK.md` 的 Status 和 Current State。
3. 更新 `HANDOFF.md`（基于真实 `git status` 与验证输出）。
4. 发生正式文档增删、移动、替代或状态变化时，同步更新 `PROJECT_CONTEXT.md` 和 `docs/README.md`。
5. 长期决策补建 ADR；未完成事项移回 `BACKLOG.md`。
6. 是否提交由用户决定；Agent 不自动 commit / push。

## 8. 哪些信息不能进入 Git

密钥、Token、Cookie、OAuth 凭证、内部代理地址、本机绝对路径、个人客户端配置。详见 `LOCAL_CONFIG.md`。

## 9. 如何运行基础设施检查脚本

统一入口（推荐）:

```bash
bash scripts/ai/check-agent-state.sh
# 或
npm run check:agent-state
```

它按序执行 `check-agent-infra.sh`（基础设施完整性）、`check-doc-governance.sh`（文档治理）、`check-task-state.sh`(CURRENT_TASK 一致性）、`check-handoff.sh`(HANDOFF 时效性）和 `git diff --check`，汇总 PASS / WARN / FAIL；任一 FAIL 时以非零退出码结束。单项脚本也可单独运行（如 `npm run check:agent-infra`)。全部检查脚本只读；targeted test 只在 `mktemp -d` 创建的临时 fixture 中写入测试数据。

文档治理检查：

```bash
bash scripts/ai/check-doc-governance.sh
# 或
npm run check:doc-governance
```

在正式文档增删、移动、替代或状态变化时运行；另外在任务事件发生时复核相关入口，并每 31 天复核一次文档地图与人工维护的项目记忆快照。脚本不得从用户目录或全局记忆自动复制内容。

治理 checker 的 fixture 测试：

```bash
bash scripts/ai/test-doc-governance.sh
# 或
npm run test:doc-governance
```

测试仅在 `mktemp -d` 创建的临时目录内写入 fixture，退出时清理；不写入项目文件。

Git Hook 的 targeted fixture 测试：

```bash
bash scripts/ai/test-pre-commit.sh
# 或
npm run test:pre-commit
```

该测试在隔离 Git 仓库中以四个 fixture 验证：staged 破损版本不能被 clean worktree 绕过；staged deletion 不能被同路径 untracked recreation 掩盖；同一路径即使被 staged `.gitignore` 忽略也不能掩盖 deletion；只暂存 `PROJECT_CONTEXT.md` 且存在无关 untracked 文件时不会触发 HANDOFF 强制。它不接入 `check-agent-state.sh` 的五步入口，避免每次状态检查递归或变慢。

## 10. 如何新增 ADR

1. 复制 `docs/decisions/ADR-TEMPLATE.md` 为 `docs/decisions/ADR-NNN-kebab-case-title.md`(NNN 递增)。
2. 填写 Context / Decision / Alternatives / Consequences / Verification。
3. Status 初始为 `Proposed`，评审后改 `Accepted`。
4. 在 `AGENTS.md` 的 Sources of Truth 可检索位置引用（如相关架构约束条目）。
5. 不为已有架构推测性补写 ADR；既有决策文档保留原位置。

## 11. 如何从 Backlog 启动任务

1. 在 `BACKLOG.md` 中把事项 Status 改为 `Ready`（确认依赖已满足）。
2. 用 `START_PROMPTS.md` 的“启动新任务”提示词，把事项整理进 `CURRENT_TASK.md`。
3. `BACKLOG.md` 中该事项 Status 改为 `In Progress`。
4. 任务结束后，`BACKLOG.md` 中标记 `Done` 并注明完成证据位置。

## 12. Git Hook 与安装边界

### 安装

```bash
bash scripts/ai/install-hooks.sh
# 或
npm run hooks:install
```

该脚本只做两件事：执行仓库本地配置 `git config core.hooksPath .githooks`，并验证 `.githooks/pre-commit` 具有执行权限。不修改任何用户级配置。

### 边界（必须理解）

- 脚本（`scripts/ai/`）是**仓库级**：随 Git 分发，所有 Agent、所有 clone 共用同一份。
- Hook(`.githooks/`）是 **Git 仓库副本级**，不是 Agent 级：与 Claude Code / Codex / Kimi Code 均不绑定，对 `git commit` 的所有入口（CLI、IDE、各 Agent）统一生效。
- 同一个仓库目录只需安装一次（`core.hooksPath` 写入该副本的 `.git/config`)。
- 不同 clone、不同电脑需要分别安装；每个独立 Git 仓库也需要各自安装。
- Worktree 复用同一仓库的 Hook 配置：`core.hooksPath` 为相对路径 `.githooks`，在各 worktree 的工作区根目录解析；只要 worktree 检出了包含 `.githooks/` 的提交即生效（未包含时需在该 worktree 重新安装或同步文件）。
- CI 是服务端统一兜底：即使本地用 `git commit --no-verify` 跳过 Hook,CI（若已配置）仍应执行 `scripts/ai/check-agent-state.sh`。`--no-verify` 仅限人工明确例外场景。
- 本机全局 `core.hooksPath`（如已配置）会被仓库级配置覆盖；`.githooks/pre-commit` 在自身检查通过后，会链式调用全局 hooks 目录中同名的 `pre-commit`（存在且可执行时），不吞掉既有全局钩子。
- 不得把真实凭证放入 Hook、脚本或文档；Hook 只输出文件路径和字段名，不输出疑似密钥内容。
- Hook 的第一步用 `git checkout-index --all` 将当前 index 完整物化到 `mktemp -d` 临时快照，再从快照运行 `scripts/ai/check-agent-infra.sh`。通过 `GIT_DIR` 指回原仓库、`GIT_WORK_TREE` 指向快照，脚本的文件读取与 `git ls-files` 分别对应待提交文件树和原始 index；`mktemp`、物化、脚本存在性或 infra 检查任一步失败都阻断提交，退出时由 `trap` 清理快照，不写 worktree。
- 只暂存 `PROJECT_CONTEXT.md` 等纯文档路径不要求同步暂存 `HANDOFF.md`；业务代码仍必须同步交接记录。

### CI 兜底（当前未启用）

本仓库当前没有 CI 配置文件（无 `.github/`、`.gitlab-ci.yml`，2026-07-17 核查）。如需增加轻量兜底 job，建议插入位置与片段:

GitHub Actions（新建 `.github/workflows/agent-state.yml`):

```yaml
name: agent-state
on: [push, pull_request]
jobs:
  agent-state:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash scripts/ai/check-agent-state.sh
```

GitLab CI（`.gitlab-ci.yml` 增加一个 job):

```yaml
agent-state:
  stage: test
  script:
    - bash scripts/ai/check-agent-state.sh
```
