# Project Agent Instructions

本文件是本仓库跨 Coding Agent(Claude Code / OpenAI Codex / Kimi Code)的唯一通用工程规则源。客户端专属适配只放在 `CLAUDE.md` 等适配文件中，不得在此之外复制第二套通用规则。

## 1. Project Overview

- 项目名称:`kids-visual-learning-pack`（芋头宇宙）。来源:`package.json` 的 `name`、`README.md`。
- 项目用途:按孩子喜欢的主题制作可视化学习看板（蜘蛛宇宙、汪汪队、生命世界等）的独立静态网页项目；同时包含“Cognitive Card OS”儿童知识卡生产系统（薄 Skill + 个人服务器核心）。来源:`README.md`。
- 主要模块（来源:`docs/project-structure.md`、`README.md`、仓库目录）:
  - `boards/kids-world/`:芋头宇宙，最高层入口，React + TypeScript 数据驱动看板。
  - `boards/spider-verse/`:蜘蛛宇宙，纯静态 HTML/CSS/JS 故事板。
  - `boards/paw-patrol/`:汪汪队任务指挥中心，Vite + React + TypeScript。
  - `packages/kids-content/`:共享内容包（TypeScript,`tsc --noEmit` 校验）。来源:`package.json` 的 `validate:kids-content`。
  - `apps/miniprogram/`:Taro 3 微信小程序。来源:`apps/miniprogram/package.json`。
  - `ops/cognitive-card-server/`:Card OS 服务端核心（Python）。来源:`ops/cognitive-card-server/`、`package.json` 的 `build:card-os-release`。
  - `ops/cognitive-card-skill/`、`skills/cognitive-card-os/`:Card OS 薄 Skill 发布与安装。来源:`package.json` 的 `build:card-os-skill`、`skills/cognitive-card-os/SKILL.md`。
  - `migration/card-os/`:历史资产机器盘点。来源:`README.md`、`migration/card-os/inventory-sources.json`。
- 技术栈（来源:`package.json`、`apps/miniprogram/package.json`、`requirements-card-os-inventory.txt`、`tests/`):
  - 前端:Vite 5 + React 18 + TypeScript 5 + Tailwind CSS 3 + PostCSS。
  - 小程序:Taro 3.6 + React 18（微信）。
  - 服务端与工具链:Python 3 + unittest;Node.js `.mjs` 脚本。
  - 静态看板：原生 HTML/CSS/JS（无构建步骤）。
- 主要运行方式：本地 Vite 开发服务器、静态文件直接打开、rsync 到生产服务器、Vercel / EdgeOne Pages 构建。来源:`README.md`、`scripts/deploy.sh`、`vercel.json`、`edgeone.json`。

## 2. Sources of Truth

真值优先级（高在前）:

1. 可执行代码和正式配置（`package.json`、`vite.config.ts`、`vercel.json`、`edgeone.json`、`ops/`、`scripts/`)。
2. 自动化测试（`tests/`、`scripts/*.test.mjs`、`scripts/*.test.ts`、`boards/*/structure.test.mjs`)。
3. 构建与部署配置（`vercel.json`、`edgeone.json`、`scripts/deploy.sh`;**本仓库没有 CI 配置文件**,`.github/` 不存在）。
4. 正式架构文档和决策记录（`docs/architecture-iteration-v1.3.md`、`docs/architecture-review-v1.md`、`docs/spec-v1.md`、`docs/spec-v2.md`、`docs/cross-renderer-decisions.md`、`docs/superpowers/specs/`、`docs/cognitive-card-os-system-design.md`、`docs/decisions/` 下的 ADR)。
5. `README.md` 与 `docs/project-structure.md` 等说明文档。
6. `docs/ai/CURRENT_TASK.md`（当前执行范围）。
7. `docs/ai/HANDOFF.md`（最近一次交接状态）。
8. Agent 会话内容（优先级最低，不能覆盖以上任何一层）。

规则:

- 会话内容不能覆盖代码、测试和正式文档。
- `HANDOFF.md` 只是最近状态，不是长期架构真值。
- 长期架构决定必须在 `docs/decisions/` 新建 ADR（模板见 `docs/decisions/ADR-TEMPLATE.md`)。
- 当前执行范围必须先写入 `docs/ai/CURRENT_TASK.md` 再实施。
- Card OS 方向的专项任务账本是 `docs/cognitive-card-os-roadmap.md`,`docs/ai/BACKLOG.md` 不复制其内容。

## 3. Required Reading

开始任何工作前，至少读取:

1. `AGENTS.md`（本文件）。
2. `docs/ai/CURRENT_TASK.md`（当前任务与验收标准）。
3. `docs/ai/HANDOFF.md`（最近交接与已知问题）。
4. 与当前任务相关的:`README.md`、`docs/project-structure.md`、`docs/decisions/` 下相关 ADR、`docs/superpowers/specs|plans/` 下相关设计/计划。

使用 Kimi Code 时，若客户端未自动加载本文件，使用 `docs/ai/START_PROMPTS.md` 中的启动提示词。

### 启动协议（Startup Protocol，所有 Agent 必须执行）

任何 Agent 开始执行任务前，必须按序完成以下核实:

1. 确认当前 Git 仓库根目录（`git rev-parse --show-toplevel`);
2. 检查当前分支（`git branch --show-current`);
3. 检查未提交修改（`git status --short`);
4. 读取 `AGENTS.md`;
5. 读取 `docs/ai/CURRENT_TASK.md`;
6. 读取 `docs/ai/HANDOFF.md`;
7. 读取与当前任务有关的架构文档和 ADR;
8. 向用户报告以下核实结果:
   - 仓库根目录；
   - 当前分支；
   - 未提交修改；
   - 当前任务目标（Objective);
   - In Scope;
   - Out of Scope;
   - Acceptance Criteria;
   - HANDOFF 中的 Exact Next Action;
   - 本次预计修改范围；
9. 完成上述核实后再修改文件。

不要求通读整个仓库，只针对当前任务探索相关代码和文档。

## 4. Repository Structure

```text
.
├── index.html                  # 所有看板的入口页
├── boards/                     # 各主题看板(kids-world / spider-verse / paw-patrol)
├── shared/                     # 跨看板共享样式与图标
├── packages/kids-content/      # 共享内容包(TypeScript)
├── apps/miniprogram/           # Taro 微信小程序
├── ops/                        # Card OS 服务端与 Skill 的发布/部署脚本(Python)
├── skills/cognitive-card-os/   # Card OS 薄 Skill 源
├── migration/card-os/          # 历史资产盘点配置与产物
├── scripts/                    # 构建、校验、导入、检查脚本(bash / .mjs / .py)
│   └── ai/                     # 多 Agent 基础设施脚本
├── tests/                      # Card OS Python unittest
├── docs/                       # 全部正式文档
│   ├── ai/                     # 多 Agent 任务状态与交接(CURRENT_TASK / HANDOFF / BACKLOG)
│   ├── decisions/              # ADR(架构决策记录)
│   ├── superpowers/specs|plans # 正式设计与实施计划
│   ├── operations/             # 生产部署与运维手册
│   └── compliance/             # 内容合规与风险清单
└── dist/                       # 构建产物(已被 .gitignore 忽略)
```

来源:`docs/project-structure.md`、`README.md`、仓库实际目录。

## 5. Development Commands

以下命令均有仓库来源；无法确认的项目明确标注，不得编造。

### 安装依赖

```bash
npm install                                    # 来源:README.md、package-lock.json
pip install -r requirements-card-os-inventory.txt  # 来源:requirements-card-os-inventory.txt(Card OS inventory 脚本依赖 Pillow/pypdf)
```

小程序依赖在 `apps/miniprogram/` 内单独安装（其目录有自己的 `package.json` / `package-lock.json`)。来源:`apps/miniprogram/package.json`。

### Build

```bash
npm run build               # = build:static,完整校验+静态构建。来源:package.json → scripts/build-static.sh
npm run build:kids-world    # Vite 构建芋头宇宙。来源:package.json
npm run build:paw           # Vite 构建汪汪队。来源:package.json
npm run build:card-os-release   # Card OS 服务端 release。来源:package.json → ops/cognitive-card-server/build_release.py
npm run build:card-os-skill     # Card OS Skill release。来源:package.json → ops/cognitive-card-skill/build_release.py
cd apps/miniprogram && npm run build:weapp   # 微信小程序构建。来源:apps/miniprogram/package.json
```

### Unit Test

```bash
npm run test:card-os-inventory      # Python unittest。来源:package.json → tests/test_card_os_asset_inventory.py
npm run test:card-os-deploy         # Python unittest(backup/acceptance/deployment/release)。来源:package.json
npm run test:card-os-skill-registry # Python unittest(skill release/installer/publisher)。来源:package.json
npm run test:visual-navigation      # Node 测试。来源:package.json → scripts/visual-navigation.test.mjs
npm run test:topic-interaction      # sucrase-node。来源:package.json → scripts/normalize-topic-interaction.test.ts
npm run test:scene-deck             # sucrase-node。来源:package.json → scripts/scene-deck.test.ts
node boards/spider-verse/structure.test.mjs   # 结构检查,可直接执行。来源:docs/project-structure.md,已实测可运行
node boards/kids-world/structure.test.mjs     # 可直接执行;当前存在与基础设施无关的既有断言失败(19 !== 18)
```

### Integration Test

本仓库没有独立的集成测试目录。最接近的是 `tests/test_card_os_acceptance.py`（包含在 `npm run test:card-os-deploy` 中）和生产手册中的验收命令。来源:`package.json`、`docs/operations/cognitive-card-server-deployment-2026-07-14.md`。其他集成测试：**未在当前仓库中确认**。

### Lint / Format

**未在当前仓库中确认**:`package.json` 中没有 lint/format 脚本，也没有 ESLint、Prettier 配置文件。不得虚构 lint 命令；如需引入，先建 ADR 讨论。

### 综合验证

```bash
npm run validate        # 全量内容校验链(topics/i18n/assets/compliance/evidence/interaction/scene-deck/kids-content/miniprogram/alignment)。来源:package.json
npm run check:images    # PNG/WebP 配对检查。来源:package.json → scripts/check-image-assets.mjs
npm run check:dist      # 构建产物完整性检查。来源:package.json → scripts/check-dist.mjs
```

### 本地运行

```bash
npm run dev                     # Vite 开发服务器(127.0.0.1:5173)。来源:package.json、README.md
open index.html                 # 静态入口。来源:README.md
python3 -m http.server 8000     # 静态服务器。来源:README.md
cd apps/miniprogram && npm run dev:weapp   # 小程序 watch 构建。来源:apps/miniprogram/package.json
```

### 部署

```bash
npm run deploy   # rsync 到生产服务器。来源:package.json → scripts/deploy.sh
```

Vercel:`vercel.json` 的 `buildCommand: npm run build`,`outputDirectory: dist`。EdgeOne:`edgeone.json` 的 `buildCommand: npm run build:edgeone`（等价于 `build:static`)。Card OS 服务端部署与回滚见 `docs/operations/cognitive-card-server-deployment-2026-07-14.md`。

### 基础设施自检

```bash
bash scripts/ai/check-agent-state.sh   # 统一入口:infra + task-state + handoff + git diff --check;或 npm run check:agent-state
bash scripts/ai/check-agent-infra.sh   # 单项:基础设施完整性。或 npm run check:agent-infra
bash scripts/ai/check-task-state.sh    # 单项:CURRENT_TASK.md 状态一致性
bash scripts/ai/check-handoff.sh       # 单项:HANDOFF.md 时效性与完整性
bash scripts/ai/install-hooks.sh       # 安装仓库级 Git Hook(每个 clone 一次);或 npm run hooks:install
```

## 6. Architecture Constraints

以下为仓库中已文档化的约束，来源见每条标注:

- 每个看板尽量自包含，避免不同主题互相依赖；跨主题复用资源移到 `shared/`。来源:`docs/project-structure.md`。
- 图片素材规则：`boards/**/assets/` 下正式图片必须保留同名 `.png` 原图与 `.webp` 部署图；页面引用 `.webp`，构建时 `.png` 不进入 `dist/`。来源:`README.md`、`docs/project-structure.md`、`scripts/check-image-assets.mjs`。
- 版权边界：不使用官方截图、官方 Logo、精确角色服装复刻或影视分镜复刻，内容为原创家庭教育材料。来源:`README.md`、`docs/compliance/content-ip-risk-register.md`。
- 跨渲染端（EdgeOne H5 / 微信小程序）的既有决策（如小程序全展开静态渲染、不做 active-group 高亮）记录在 `docs/cross-renderer-decisions.md`，属于有意简化，不是 parity bug。来源:`docs/cross-renderer-decisions.md`。
- 架构迭代基线与拆分策略（H5 与小程序两条线独立推进）见 `docs/architecture-iteration-v1.3.md`。
- Card OS：服务器统一负责协议、任务状态、候选、资产、排版、QA 和发布；薄 Skill 不保存 OpenAI API Key；现网只接受规范化锁定任务。来源:`README.md`、`docs/cognitive-card-os-system-design.md`。
- Card OS 生产部署、升级、备份、回滚的门禁见 `docs/operations/cognitive-card-server-deployment-2026-07-14.md`。
- `scripts/deploy.sh` 只上传构建产物与静态文件，不触碰服务器 nginx 配置。来源:`scripts/deploy.sh` 注释。

新增长期架构决策：在 `docs/decisions/` 按 `docs/decisions/ADR-TEMPLATE.md` 新建 ADR，不要只在会话或 HANDOFF 中记录。

## 7. Scope and Change Rules

- 开始修改前必须检查 `git status`，确认工作区状态。
- 不覆盖用户未提交的修改；不删除、不重置、不强制 checkout。
- 不修改 `docs/ai/CURRENT_TASK.md` 中 `In Scope` 之外的文件。
- 不进行与当前任务无关的重构。
- 不静默改变公共 API、数据结构（如 `topic-registry.json`、`exploration-map.json`、Card OS 协议）和兼容规则；必须变更时先更新设计与 ADR。
- 不因测试失败直接删除或跳过测试；不使用假实现掩盖失败。
- 不声称“已完成”，除非已执行第 8 节的对应验证；无法验证的结果必须明确标记。
- 新需求不得直接混入当前任务，先更新 `CURRENT_TASK.md` 的任务范围。
- Card OS 专项事项先核对 `docs/cognitive-card-os-roadmap.md`，避免与专项账本冲突。

## 8. Verification Requirements

完成条件（全部满足才可声称完成）:

```text
代码修改完成
+ 相关测试通过(见第 5 节,按改动范围选择)
+ 必要的全量验证完成(npm run validate / npm run build,按改动范围选择)
+ 文档与行为一致
+ docs/ai/HANDOFF.md 已更新
```

改动范围与最小验证对照:

| 改动范围 | 最小验证 |
| --- | --- |
| `boards/**` 内容/样式/交互 | `npm run validate` + `npm run check:images`（涉及图片时） |
| `packages/kids-content/**` | `npm run validate:kids-content` |
| `apps/miniprogram/**` | `npm run validate:miniprogram` |
| `ops/`、`tests/`、`skills/`(Card OS) | 对应 `npm run test:card-os-*` |
| 构建/部署脚本 | `npm run build` + `npm run check:dist` |
| 仅基础设施文档/脚本 | `bash scripts/ai/check-agent-state.sh`（含 `git diff --check`) |

如果全量测试因既有问题失败，必须在 `HANDOFF.md` 记录：失败命令、失败测试、错误摘要、是否与本次修改相关、判断依据。

## 9. Git Safety Rules

- 不直接覆盖用户改动；不自动删除文件。
- 不自动切换、重写分支；不执行 `git reset --hard`、`git clean`、强制 checkout 或 rebase。
- 不自动 commit、push、merge 或创建 PR，除非用户明确要求。
- 多 Agent 并行时：一个任务一个分支，一个 Agent 一个 Git Worktree（本仓库惯例使用 `.worktrees/`，该目录已被 `.gitignore` 忽略）。来源：`.worktrees/`、`.gitignore`。
- 禁止两个 Agent 同时修改同一个工作目录。
- 串行切换 Agent 前，当前 Agent 必须先更新 `docs/ai/HANDOFF.md` 并保持 Git 状态清晰。
- 并行成果的汇总只通过 commit / cherry-pick / merge 进行。
- 提交前钩子 `.githooks/pre-commit` 对所有 Git 提交入口统一生效，不与任何特定 Agent 绑定；暂存业务代码时必须同步更新并暂存 `docs/ai/HANDOFF.md`（纯文档、基础设施初始化等豁免规则见 Hook 输出）。`--no-verify` 仅限人工明确例外场景；CI（若已配置）仍会执行 `scripts/ai/check-agent-state.sh` 兜底。

## 10. Task State Protocol

- `docs/ai/CURRENT_TASK.md`：当前正式任务，唯一执行范围来源。开始实施前必须存在且边界清晰。
- `docs/ai/HANDOFF.md`：最近一次可靠交接，记录真实修改与验证结果，禁止凭会话印象填写。
- `docs/ai/BACKLOG.md`：尚未进入执行范围的事项；不等于执行计划；只收录仓库中有明确证据的事项。
- `docs/cognitive-card-os-roadmap.md`:Card OS 专项任务账本，BACKLOG 不复制其内容，只引用。
- `docs/decisions/`：长期架构决策（ADR)。
- 新需求必须先更新 `CURRENT_TASK.md` 或放入 `BACKLOG.md`，不得直接混入当前任务。
- `.superpowers/` 下的会话级报告（已被 `.gitignore` 忽略）是非正式工作记录，不作为交接真值。

## 11. Handoff Protocol

- 每个可验证的小阶段结束后更新 `docs/ai/HANDOFF.md`，字段按该文件模板。
- HANDOFF 必须基于实际 `git status` / `git diff` 和真实执行过的验证命令填写。
- 已知失败（无论是否与本次相关）必须写入 `Known Failures`。
- 下一位 Agent 的 `Exact Next Action` 必须是可直接执行的具体动作。
- 主题级专项交接（如 `docs/kids-world-image-generation-handoff.md`）继续保留在其主题文档中；仓库级最近交接以 `docs/ai/HANDOFF.md` 为准。

### 结束协议（Shutdown Protocol，所有 Agent 必须执行）

发生以下任一情况前，必须先更新 `docs/ai/HANDOFF.md`:

- 准备结束会话；
- 准备切换客户端；
- 一个可验证阶段已经完成；
- 出现阻塞；
- 额度可能耗尽；
- 工作区需要他人接手。

结束协议步骤（内容必须来自实际仓库状态和命令结果，不得只凭会话记忆）:

1. 检查实际 Git 状态（`git status --short`、`git branch --show-current`);
2. 更新 `docs/ai/HANDOFF.md`;
3. 记录实际修改文件（以 `git status` / `git diff` 为准）;
4. 记录实际运行的验证命令；
5. 记录 PASS、WARN 和 FAIL;
6. 记录已知失败是否与本次修改相关及判断依据；
7. 记录剩余工作；
8. 写出 Exact Next Action;
9. 执行 `git diff --check`;
10. 输出 `git status --short`。

## 12. Security and Data Handling

- 密钥、Token、Cookie、OAuth 凭证、内部代理地址和个人配置不得进入 Git；边界见 `docs/ai/LOCAL_CONFIG.md`。
- 不读取、不输出认证信息；发现疑似泄露时停止扩散并报告用户。
- 不主动把内部代码或文档发送给外部服务（包括联网搜索、外部上传）。
- 使用外部模型前遵循项目的数据安全要求；`migration/card-os/inventory-roots.local.json` 等本机路径配置保持本地（已被 `.gitignore` 忽略）。
- `ops/cognitive-card-server/env/card-os.env` 是仓库内的服务端路径配置模板，不是密钥库；新增密钥类字段一律不得提交。
- 不确定是否可外发时：停止外发，但可以继续本地检查和文档整理。

## 13. Agent-Specific Boundaries

- **Claude Code**：通过根目录 `CLAUDE.md` 适配，该文件只做引用与客户端差异说明，不复制本文件规则。
- **OpenAI Codex**：直接读取本 `AGENTS.md`，不另建规则副本。
- **Kimi Code**：自动读取项目根目录 `AGENTS.md`（已在当前版本核实）；若使用的版本未自动加载，用 `docs/ai/START_PROMPTS.md` 的启动提示词显式指定，不虚构配置文件。
- 各 Agent 的用户级登录信息、API Key、个人 MCP 配置属于第三层（用户级私有配置），不得写入仓库，本次基础设施也不修改这些目录。
- 客户端专属项目配置（如 `.claude/`、`.codex/` 中确认适合共享的内容）允许提交，但只能保存客户端适配，不得包含完整通用规则或任何凭证。
- Git Hook(`.githooks/`）是 Git 仓库副本级机制，不是 Agent 级：与 Claude Code / Codex / Kimi Code 均不绑定，对所有 Git 提交入口统一生效；安装边界见 `docs/ai/README.md`。
