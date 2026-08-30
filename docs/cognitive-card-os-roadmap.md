# Cognitive Card OS 路线图与任务账本

状态：活动中  
最近更新：2026-08-30
整体设计：[Cognitive Card OS 整体设计](cognitive-card-os-system-design.md)

## 1. 维护规则

本文是 Cognitive Card OS 唯一动态待办账本。

状态只使用：

- `DONE`：实现、验证和必要审查全部完成；
- `IN PROGRESS`：已有活动实施批次；
- `READY`：依赖满足，可立即进入设计或实施；
- `BLOCKED`：存在明确外部阻塞；
- `BACKLOG`：已定义但尚未达到开始条件；
- `REQUIRES AUDIT`：历史上做过工作，但当前状态需要重新核实。

每个任务必须记录权威仓库、依赖和可验证的完成条件。设计通过不等于实现完成；代码存在也不等于部署完成。

## 2. 当前里程碑

**M1：可远程领取与提交**

目标：一个安装薄 Skill 的受信任 Codex 客户端，通过 `www.yutou.space` 发现服务、登录 Card OS、领取生成包并上传候选结果；整个流程不需要 OpenAI API Key，也不传递 ChatGPT 身份。

M1 包含：`API-01`、`AUTH-01`、`PROTO-01`、`SKILL-01`、`SKILL-02`、`DEPLOY-01`。

资产迁移作为并行治理工作流推进，但在 API、认证和正式导入工具完成前不写入服务器。发现清单见 [历史资产迁移清单](cognitive-card-os-asset-migration-inventory.md)。

## 3. 总览

| ID | 工作流 | 状态 | 下一动作 |
| --- | --- | --- | --- |
| GOV-01 | 总设计与唯一任务账本 | DONE | 后续变更持续更新 |
| KNOW-02 | Knowledge Core four-object contract | DONE | 四对象纯合同、fixtures、证据与独立复审完成；下一步进入最小 local authoring MVP |
| AUTHOR-01 | Local authoring vertical slice | DONE | 标准库 CLI 已跑通结构化输入、四对象、Publish 校验和可浏览 revision 目录 |
| AUTHOR-02 | 真实兔子复合主题试产 | DONE | 4 个真实来源、8 条命题、4 个知识单元已闭环；下一步试产 progressive 几何主题 |
| AUTHOR-03 | 真实几何渐进主题试产 | DONE | 平面→立体→高维的显式先修链、必修/选修 Plan 与分阶段 Projection 已闭环；下一步试产时效性主题 |
| AUTHOR-04 | 合成时效主题试产 | DONE | review due、expiry、block/unlist 与 revision 替代已由 CLI 闭环；下一步汇总三类试产摩擦 |
| AUTHOR-05 | 三类试产字段消费证据 | DONE | 无字段达到三次未消费门槛；不改合同；分类/AGE 仍独立；current pointer 见 LIB-01 |
| LIB-01 | 知识库 candidate / 不可变 revision / current | DONE | 进程内 library 已在 `knowledge-pipeline-v1` 验证；未 merge 进 main |
| PROJ-01 | Projection family 选择面 | DONE | 已本地提交进 `9e0c353`；未 merge 进 main |
| WIRE-01 | HTTP/DB 受控接线 | DONE | loopback HTTP 已接 library / 选择面 / 接合 current 门禁；已本地提交 `9e0c353`；未 merge 进 main |
| KNOW-01 | 分类与对象类型体系 | IN PROGRESS | 做覆盖矩阵与缺口测试 |
| TMPL-01 | 领域/形态模板族 | IN PROGRESS | 补齐模板注册表和跨对象夹具 |
| AGE-01 | 3–4、5–6 岁配置 | IN PROGRESS | 服务端化并验证路由 |
| AGE-02 | 8、10、15 岁配置 | BACKLOG | 分年龄建立认知与语言规范 |
| EXEC-01 | 订阅执行核心 | DONE | 作为 API 应用服务使用 |
| API-01 | HTTPS 写入 API | IN PROGRESS | 集成分支含 LIB-01 `b672949` 与 PROJ-01/WIRE-01 `9e0c353`；功能分支未 merge 进 main；现网仍 `0.3.1` |
| AUTH-01 | Card OS 身份与权限 | IN PROGRESS | 补浏览器会话、正式轮换与长期客户端凭据操作面 |
| PROTO-01 | capability/protocol discovery | DONE | 作为 Skill 注册表和部署兼容门禁使用 |
| SKILL-01 | Skill 发布注册表 | DONE | 完整 `0.1.1` 已 provisional 激活生产 stable；回滚与不可变历史已实证 |
| SKILL-02 | 薄 Skill 客户端 | IN PROGRESS | 本机代码、双隔离安装与现网上传验收已通过；保留第二台真实 Codex 电脑安装同一摘要的历史完成条件 |
| MIG-01 | 历史资产发现、摘要与去重清单 | DONE | 人工复核重复与衍生候选，等待 MIG-02 导入条件 |
| MIG-02 | A/B 级结构化 package 导入 | BACKLOG | 依赖导入接口、严格验证和 MIG-01 |
| MIG-03 | C 级旧主题重制 | BACKLOG | 依赖模板、发布链路和 MIG-01 |
| PORTAL-01 | 只读资产门户 | BACKLOG | 依赖认证和资产查询 API |
| UPLOAD-01 | 浏览器手动上传 | BACKLOG | 依赖 AUTH-01、API-01 |
| SITE-01 | Card OS 替换 `kids-world` | BACKLOG | 依赖门户、发布和迁移覆盖 |
| SITE-02 | 旧站兼容与重定向 | BACKLOG | 依赖 SITE-01 切换门禁 |
| RENDER-01 | 四卡排版与打印 PDF | BACKLOG | 依赖内容锁和资产接口 |
| QA-01 | 严格 QA 与人工复核 | BACKLOG | 依赖 RENDER-01 |
| PUBLISH-01 | 不可变 package 发布 | BACKLOG | 依赖 QA-01 |
| MCP-01 | 只读 MCP | BACKLOG | 依赖稳定查询 API |
| DEPLOY-01 | Card OS 服务部署 | DONE | 按生产运维记录持续执行升级与回滚门禁 |
| OPS-01 | 容量、备份与监控治理 | IN PROGRESS | 增加异地备份、容量及证书/健康告警 |
| ACCEPT-01 | 兔子完整验收 | BACKLOG | 依赖发布链路 |
| ACCEPT-02 | 第二个哺乳动物一致性验收 | BACKLOG | 依赖 ACCEPT-01 与模板族 |

## 4. 任务明细

### GOV-01 总设计与治理入口

- 状态：`DONE`
- 权威仓库：`kids-visual-learning-pack`
- 产物：整体设计、路线图、README 导航、子系统文档索引。
- 完成条件：整体边界、权威来源、路线图状态语义和文档更新规则明确。

### KNOW-02 Knowledge Core 四对象合同

- 状态：`DONE`
- 权威仓库：`cognitive-card-server`；产品架构、批准设计与任务治理权威为 `kids-visual-learning-pack`。
- 依赖：[ADR-002](decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[Knowledge Core 已批准设计](superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md)，以及 API-01 snapshot base `9c1b82b`。
- 完成批次：从 `codex/api-01-core-snapshot` @ `9c1b82b` 创建隔离分支 `codex/knowledge-core-contract-v1`，实现并验证 `knowledge-core`、`learning-spec`、`projection-spec`、`manifest` 四对象的 pure validator、稳定错误、temporal/stage gate、跨对象 closure、两级 lock 和 manifest 校验。
- 验收证据：兔子 composite、几何 progressive、合成 time-sensitive revision 和 `four-card` compatibility fixture 的正反向验证通过；Projection/Renderer 变化不能改写 Knowledge Core；过期知识不能错误发布；未声明 fact/artifact 被拒绝。见 [Pilot Evidence](knowledge-core-contract-pilot-evidence.md)。
- 非范围：HTTP route、SQLite/schema、subscriber/auth、renderer、Portal、部署和生产接线；本地 authoring MVP、实际 four-card `production-record` converter、服务器 revision/current/freshness 管理与 Portal 分别在后续批次立项。
- Review evidence：2026-08-21 fresh focused suite `128` 项通过，变更 allowlist 和 runtime-reference scan 证明零 HTTP/DB/runtime wiring；补齐 `pyproject.toml` 声明的 test dependencies 后，contract + authoring 所在完整 suite `444` 项全部通过。原 2 Critical、4 Important、1 Minor 以及后续两项文档 residual 均已关闭，docs-only scoped re-review 和 targeted recheck 为 CLEAN。

### AUTHOR-01 Local authoring vertical slice

- 状态：`DONE`
- 权威仓库：`cognitive-card-server`；任务治理为 `kids-visual-learning-pack`。
- 目标：结构化主题输入经现有四对象合同编译和 Publish 校验后，原子写入可长期保留的 revision 目录，并生成结构化本地浏览页。
- 首批边界：当前 Codex/人工提供来源与命题；CLI 不联网、不生成事实、不接 HTTP/DB/Portal/正式 Renderer。
- 完成结果：rabbit composite 示例端到端通过；无效输入和重复 revision fail closed；产物含四对象、validation 记录与 escaped HTML 浏览页；默认 Projection 按 scope 路由，`four-card` 只在显式请求时使用。
- 验收证据：2026-08-21 fresh authoring suite `5` 项、contract + authoring suite `133` 项均通过，`py_compile` 和 server `git diff --check` 通过；使用声明 test dependencies 的完整 suite `444` 项全部通过。实现已提交到隔离 server 分支 commit `120e5fc`，未 push/merge。
- 后续：真实内容试产由 `AUTHOR-02` 承接。

### AUTHOR-02 真实兔子复合主题试产

- 状态：`DONE`
- 权威仓库：`cognitive-card-server`；任务治理为 `kids-visual-learning-pack`。
- 完成结果：基于 Merck Veterinary Manual 与 RSPCA 的 4 个机构页面，形成外观与运动、牙齿与消化、行为与需要、饲养与安全 4 个知识单元和 8 条命题；每条命题绑定自己的来源与 evidence span。Learning Plan 为 `age-5-6`、中英双语、入门深度、15 分钟亲子共读，composite 默认选择 `chaptered-guide`，未强制 four-card。
- 最小缺口修复：真实试产证明单来源 request 会错误压平 provenance，因此增加兼容旧 `source` 的 `sources + source_slug`；同时允许命题声明 temporal 复核策略，生物基础事实按 730 天 slow-changing 复核，行为与照护建议按 365 天 periodic 复核。两项均由 focused regression test 保护。
- 产物检查：临时 revision 目录包含四对象、manifest、`validation.json` 与 escaped HTML 共 6 个文件；Publish validation 为 valid、issues 为 0；直接 CLI 编译耗时 `0.06s`。产物只写 `/tmp`，未写用户 `outputs/`。
- 本地提交：AUTHOR-02/03/04 实现与试产夹具已提交到隔离 server 分支 `codex/knowledge-core-contract-v1` commit `1facb79`，未 push/merge。
- 真实摩擦记录：人工需要决定 4 个单元边界、8 条命题的来源归属、unknown/confusion/safety 边界及复核周期；默认 Projection 无需改写。事实检索、阅读与治理的总人工耗时未单独埋点，不能给出可信总时长。`age-5-6` 与双语当前只被保存为 Learning Plan 元数据，结构浏览页仍直接显示英文 canonical claim；分类信息也尚未进入 authoring request。这些不阻断结构化闭环，留待后续批次，不扩建当前框架。
- 后续：用 progressive 几何主题验证逐步深入路径；再用时效性主题验证更新/过期行为。正式儿童表达、图片、PDF、library current/index、Portal 与服务器存储仍保持独立立项。

### AUTHOR-03 真实几何渐进主题试产

- 状态：`DONE`
- 权威仓库：`cognitive-card-server`；任务治理为 `kids-visual-learning-pack`。
- 完成结果：基于 OpenStax 平面/三维坐标教材页与 Plus Maths 高维空间文章，形成平面、立体和更高维 3 个知识单元、6 条命题。Knowledge Core 显式保存 2 条 `prerequisite_of`，Learning Path 派生对应 `prerequisite` edges；循环图在 revision 写入前拒绝。
- Plan / Projection：`age-5-6`、中英双语、入门、15 分钟亲子学习；平面和立体为 required，更高维为 optional。默认 `progressive-exploration` 为 3 个阶段分别建立 slot，不使用 four-card，也不在 Projection 增加数学事实。
- 最小缺口修复：authoring request 兼容增加顶层 `prerequisites` 与 `learning.optional_unit_slugs`；progressive Projection 由单一不透明 slot 调整为每个路径节点一个 slot。无显式先修关系的旧 progressive request 继续保留数组顺序生成 `next` 的兼容行为。
- 产物检查：临时 revision `/tmp/cognitive-card-author03.0JlqVj/geometry/revision-0001` 含四对象、manifest、`validation.json` 和 escaped HTML 共 6 个文件；Publish validation 为 valid、issues 为 0；直接 CLI 编译耗时 `0.06s`。authoring/contract/full suites 分别为 `12/140/451` 项 PASS。
- 真实摩擦记录：每条命题仍需人工选择来源、边界和复核周期；本主题 6 条稳定数学命题重复填写相同 1095 天策略，提示未来可能需要受控默认，但两次试产证据还不足以扩建。分类仍未进入 request，年龄与语言仍只保存为 Plan 元数据，结构预览仍显示英文 canonical claim；均不阻断本次知识结构闭环。
- 后续：用合成但时效机制真实的主题验证 review due、expiry、block/unlist 与 revision 替代。完成三类试产后再决定 library current/index、分类接入和年龄/语言表达适配，不提前进入 Portal、Renderer 或服务器存储。

### AUTHOR-04 合成时效主题试产

- 状态：`DONE`
- 权威仓库：`cognitive-card-server`；任务治理为 `kids-visual-learning-pack`。
- 完成结果：合成 after-school slot fixture 证明过期命题默认 Publish CLI fail closed；`block_publish` 与 `unlist_current` 在 Publish 均报告 `KNOWLEDGE_EXPIRED` 且不写目录。`temporal.reviewed_at` 可早于 `authored_at`，使 review due 可被计算；Publish 因 freshness/health 门禁拒绝，`--stage candidate` 物化 `REVIEW_DUE` 警告与 `degraded` health。revision 2 保留 superseded 历史命题、原 temporal 记录和 `supersedes` 关系，新命题可 Publish，final-content lock 与 revision 1 不同。Projection 显式 `time-sensitive-brief`。
- 最小缺口修复：authoring 按 temporal 计算 `freshness`；命题可声明 `standing`/`revision`；顶层 `supersedes`；superseded 命题不进入当前 unit/path；CLI `--stage candidate`；Publish 只对 blocking error fail closed，warnings 写入 `validation.json`。
- 产物检查：临时 library `/tmp/cognitive-card-author04/fixture-after-school-slot` 含 revision-0001（candidate）与 revision-0002（publish）。authoring/contract suites `17/145` PASS。声明依赖 full suite `456` 项中 454 PASS；2 项既有 `test_real_uvicorn_*` 返回 502，属本地 HTTP 环境，与本批无关。
- 真实摩擦记录：`unlist_current` 在无 current pointer 时与 `block_publish` 的 CLI 行为相同，区别留给后续 library current/index。review due 不能在 Publish 下物化，必须 Candidate。替代 revision 仍需人工同时给出 superseded 命题与 `supersedes` 对。分类、年龄/语言儿童正文仍未消费。证据仍不足以增加全局 temporal 默认。
- 后续：汇总 AUTHOR-02/03/04 未消费字段和重复默认；之后按证据决定 library current/index、分类接入和年龄/语言表达。抢救批次、Portal 与 Renderer 保持独立。

### AUTHOR-05 三类试产字段消费与默认策略证据

- 状态：`DONE`
- 权威仓库：`kids-visual-learning-pack`（治理）；对照物为 server `examples/authoring/` 与 `authoring.py`。
- 样本：AUTHOR-02 `rabbit-real.json`；AUTHOR-03 `geometry-progressive-real.json`；AUTHOR-04 `schedule-expired-synthetic.json` + `schedule-replacement-synthetic.json`（同一主题的过期与替代，计为一次时效试产）。
- 门槛：连续三次未进入四对象，或三次都手工改写**同一**默认，才允许收缩字段或增加受控默认。HTML 预览未展示不等于未消费。
- 本批代码：未改四对象合同，未改 authoring 默认。

对照表（C = 进入 Knowledge Core / Learning / Projection；P = 进入 HTML 预览；空 = 该试产未出现或恒为空）：

| 字段或决策 | A02 兔子 | A03 几何 | A04 时效 | 三次门槛 | 本批 |
| --- | --- | --- | --- | --- | --- |
| `sources[]` + `source_slug` | C | C | C | 已消费 | 保留 |
| `prerequisites` | 无 | C | 无 | 未三次出现 | 保留可选 |
| `optional_unit_slugs` | 无 | C | 无 | 未三次出现 | 保留可选 |
| `supersedes` + `standing` | 无 | 无 | C | 一次 | 保留 |
| `projection.family` 显式 | 默认 chaptered-guide | 默认 progressive-exploration | 显式 time-sensitive-brief | 默认路由 2/3 可用 | 不改默认表 |
| `learning.audience_profiles` = age-5-6 | C 非 P | C 非 P | C 非 P | 三次写入 Plan，预览不用 | 不删字段；表达适配另立项 |
| `learning.languages` 含 zh-CN | C 非 P | C 非 P | C 非 P | 三次无中文 claim | 同上 |
| `claim` / `claim_language=en` | C+P 英文 | C+P 英文 | C+P 英文 | 三次无儿童中文正文 | 不改合同 |
| `temporal` 整块手写 | 每命题 730 或 365 | 每命题 1095 | 每命题 7 日 + 到期 | 三次都手写，但**默认值不同** | 不加全局 interval |
| `temporal.valid_from` | 恒 null | 恒 null | 恒 null | 三次空值 | **达标可改为可选 omit**；本批推迟（exact keys 防漏填仍有价值） |
| `temporal.event_triggers` | [] | [] | 仅 replacement 非空 | 未三次空 | 保留 |
| `temporal.expiry_behavior` | 均为 warn | 均为 warn | block_publish / unlist 试过 | 已按主题分化 | 保留 |
| `source.published_at` | 恒 null | 有日期 | 恒 null | 未三次空 | 保留 |
| `source.valid_until` | 恒 null | 恒 null | 有日期 | 未三次空 | 保留 |
| `unknowns` / `confusion_boundary` / `safety_scope` | 有空有填 | 有空有填 | 有填 | 已消费 | 保留 |
| request 内分类 domain/form/subtype | 无此键 | 无此键 | 无此键 | 三次不在 authoring schema | **不是收缩，是未立项接入 KNOW-01** |
| library current / `unlist_current` 下架 | 无 | 无 | Publish 与 block 同码 | 三次无 current pointer | 不改 validator；current/index 另立项 |
| four-card / 图片 / PDF | 无 | 无 | 无 | 故意 Out of Scope | 不在本证据触发 |

人工结构选择（三次都要人做，不自动默认）：单元切分、命题归属来源、unknown/confusion/safety、复核周期、先修边、必修/选修、是否替代。

结论：

1. 不加全局 temporal 默认（interval 730/1095/7 不一致）。
2. 不从 request 删除 Plan 年龄/语言；它们已进 learning-spec，缺的是儿童表达 Projection（AGE-01），不是未消费。
3. 分类接入、library current/index、中文 claim 投影均为**新能力**，未达“删字段”门槛。
4. 唯一触及三次空值的可选项是 authoring 层 `valid_from` 可省略；推迟到下一次有人被 null 填表明显拖慢时再做。

- 后续：抢救批次（存档生产核心 → 可信上游）优先于从零重建；分类/AGE 表达按独立任务，不混入 authoring CLI。library current 见 `LIB-01`。

### LIB-01 知识库 candidate / 不可变 revision / current pointer

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `b672949`，未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：[ADR-002](decisions/ADR-002-knowledge-core-and-projection-architecture.md) §18.5、[Knowledge Core 设计](superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md) §13.2、[独立设计](superpowers/specs/2026-08-30-knowledge-library-revision-current-design.md)、接合 lock `1f9c42f`。
- 完成结果：`accept_candidate` 只保存 Candidate 闭包且不设 current；`publish` 原子写入 `revision-NNNN/` 并更新 `current.json`；已有 revision 不覆盖；`unlist_current` 过期在 `get_current(now)` 下架且保留历史；服务器复算 identity，篡改 lock fail closed。无 HTTP/SQLite。
- 验收证据：`tests.test_knowledge_library` 14 项 PASS；与 generation-input / 接合 / authoring / contract 合计 focused `178` 项 PASS。本地提交 `b672949`（5 文件）。未 add `uv.lock`。未 merge 进 server `main`（仍 `c2a898c`），未 push。
- 非范围：HTTP、Portal、Renderer、four-card converter、KNOW-01、AGE-01、改 validator 的 Publish 语义。

### PROJ-01 Projection family 选择面

- 状态：`DONE`（实现与 focused 测试完成；已本地提交进 `9e0c353`，未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：[ADR-002](decisions/ADR-002-knowledge-core-and-projection-architecture.md) §9.3、[独立设计](superpowers/specs/2026-08-30-projection-family-selection-design.md)、AUTHOR-05 默认表、LIB-01。
- 完成结果：`select_projection_family` 返回 recommended / chosen / options（eligible 或 discouraged）；省略 family 时三类试产 chosen 与 AUTHOR-05 默认表相同；`four-card` 不自动选中；未知 family fail closed。authoring 用 chosen 填 blueprint，HTML 预览展示理由，package 文件集合不变。无第五个治理对象。
- 验收证据：`tests.test_projection_family` 9 项 PASS；与 library / generation-input / 接合 / authoring / contract 合计 focused `187` 项 PASS。已与 WIRE-01 一并本地提交 `9e0c353`（14 文件）。未 add `uv.lock`。未 merge 进 server `main`（仍 `c2a898c`），未 push。
- 非范围：新 family、改四对象 schema、改默认表使兔子/几何换 family、Portal/Renderer。

### WIRE-01 HTTP/DB 受控接线

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `9e0c353`，未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：[独立设计](superpowers/specs/2026-08-30-knowledge-library-http-db-wiring-design.md)、LIB-01、PROJ-01、接合 lock `4ca3e0e`。
- 完成结果：loopback HTTP 调用现有 `KnowledgeLibrary` 与 `select_projection_family`；接合 generation-input 仅当 library current identity 匹配时才能写入 GenerationInputStore 并创建 SQLite compiled-job；v1 FACT 密封路径不变。无新 SQLite 表，无第五个治理对象，未接现网。
- 验收证据：`tests.test_http_knowledge_library` 6 项 PASS；与 library / projection-family / generation-input / 接合 / authoring / contract / HTTP compiled 合计 focused `200` 项 PASS；含 auth registry 的 HTTP 回归 `251` 项 PASS。已本地提交 `9e0c353`（14 文件，含 PROJ-01）。未 add `uv.lock`。未 merge 进 server `main`（仍 `c2a898c`），未 push。
- 非范围：新 SQLite 表、Portal、Renderer、改 v1 FACT 合同、生产 env 必填项。

### KNOW-01 分类与对象类型覆盖

- 状态：`IN PROGRESS`
- 权威来源：当前 `cognitive-card-os` 分类规范；目标迁入服务器版本化注册表。
- 已有：领域、概念形态、领域自有 subtype、稳定 machine value 和分类停机规则。
- 待办：
  - 建立 `domain x form x subtype` 覆盖矩阵；
  - 为尚未出现首个对象的领域补充 subtype 词表；
  - 为 `general`、`other` 和 `CLASSIFICATION_REVIEW` 增加边界夹具；
  - 将注册表、版本和摘要纳入服务器权威发布。
- 完成条件：所有受控枚举可机器校验；新增概念不会靠自由文本绕过分类。

### TMPL-01 领域与形态模板体系

- 状态：`IN PROGRESS`
- 已有：哺乳动物 3–4、5–6 岁精确模板，以及多个 domain/form 家族和受控 fallback。
- 待办：
  - 建立模板族覆盖报告；
  - 记录每个 family 的固定四页骨架、槽位、年龄/语言适配和结构指纹；
  - 为每个已启用大类配置至少两个对象夹具；
  - 保证次领域和次形态只能激活已声明模块；
  - 将模板发布、回滚和兼容矩阵迁入服务器。
- 完成条件：相同主路由得到稳定骨架；模板缺口返回 `TEMPLATE_GAP`，不静默套用错误模板。

### AGE-01 现有年龄与语言配置

- 状态：`IN PROGRESS`
- 范围：`age-3-4`、`age-5-6`、CN 同年龄配置、EN `beginner`。
- 待办：把年龄与语言规则发布为带版本的服务器适配器；增加跨对象事实不漂移和 COPY 来源测试。
- 完成条件：年龄只改变表达与任务负荷；四卡命题、确定性和安全边界保持一致。

### AGE-02 未来年龄升级

- 状态：`BACKLOG`
- 范围：分别设计约 8、10、15 岁的独立年龄配置。
- 依赖：AGE-01 稳定、每个年龄拥有代表性对象和语言验收集。
- 完成条件：每个年龄带有独立阅读、因果、系统、证据、任务负荷和 QA 规则；请求按一个主年龄版本输出。

### EXEC-01 订阅执行核心

- 状态：`DONE`
- 权威仓库：`https://github.com/lixiaojie/cognitive-card-server`（私有）
- 版本：`0.2.0`
- 提交：`b74c401bd8f04aa5e765cd4d1e8cdccf8f0bf596`
- 已完成：SQLite 事务、任务状态、生成包、租约、幂等结果、候选隔离存储、摘要校验、审计、撤销和恢复。
- 验证：133 项测试通过；完整分支审查为 Critical 0、Important 0、Minor 0。

### API-01 HTTPS 应用 API

- 状态：`IN PROGRESS`
- 权威仓库：`cognitive-card-server`
- 依赖：EXEC-01。
- 当前已审查批次：服务版本 `0.3.1`，提交 `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`；提供 health、capability、锁定任务、包签发/领取/完成、候选结果提交、状态与事件查询共 11 条路径，并保留在线 WAL keeper 修复。
- 已验证：该精确提交的完整应用测试与发布审查通过；真实 Uvicorn 并发认领、重启恢复、幂等、媒体/大小限制、鉴权先于 body 解析、凭据零写入和日志脱敏均覆盖；协议仍为 `1`，minimum Skill release 仍为 `0.1.0`。
- 第一批端点职责：
  - 健康和 capability 查询；
  - 创建规范化任务；
  - 查询任务状态；
  - 领取和下载生成包；
  - 标记客户端生成完成；
  - 上传 manifest 与候选文件；
  - 查询稳定错误和审计摘要。
- 约束：HTTP 适配器不复制状态机；只调用现有应用服务。请求必须有大小、超时、媒体类型和幂等限制。
- `0.3.1` 批次验收：真实 HTTP 集成测试覆盖正常流程、错误码、重启恢复和并发认领。
- `API-01` 完成条件：上述批次保持通过；服务经 `www.yutou.space` 的 HTTPS 和持久化部署验收；受信任上游能把用户请求转换为规范化锁定任务，而服务器仍拒绝自由 payload 绕过内容锁。
- 已部署：`0.3.1` 经 `www.yutou.space/card-os` 的 HTTPS、持久化和非 root 服务验收，health/capabilities 与受保护路径均通过；见 [生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md)。
- 未完成：把自由概念请求编译为规范化锁定任务的可信上游接口。因此当前批次不能被描述为通用概念创建 API。该入口是 ACCEPT-01 的真正前置；候选实现为存档 tag `archive/card-os-thin-skill-v1-20260717` 中 `skills/cognitive-card-os/core/` 的生产核心（分类 v2、27 步工作流、full-spec v4.3/v5.0、哺乳动物 v1 与恐龙 v2 模板族），按 ADR-001 须迁移到服务器侧并重新评审，不得直接从 Skill 包形态合入。
- 抢救进度：API-01-IMPL-1 snapshot 已在 `codex/api-01-core-snapshot`；API-01-IMPL-2/3/4 确定性封印、sealed-input store、compiled-jobs 与 prepare/submit 辅助已在隔离分支 `codex/api-01-generation-input-v1` 本地提交 `878a28d`（基线 `9c1b82b`，未 push）。接合合同（四对象 revision lock）已在同一分支本地提交 `4ca3e0e`。用户授权后已开 `knowledge-pipeline-v1`（基线 knowledge-core `1facb79`，merge `4ca3e0e`，authoring lock `1f9c42f`）；两条功能分支未 merge 进 `main`。未 add `uv.lock`；v1 FACT 密封合同未改。兔子/mammal production-record 兼容 snapshot `sha256:ae563e…1f20` 已导入并将 `47d2…d4c1` retained；introducing commit 为 `878a28d`，catalog `registry_commit` 仍为 `9c1b82b`。本机 loopback 已用全新 `/tmp` 与短期 job-bound token 完成 A→B→C：seal lock `sha256:15b8ea…ce2a`，新 packet（未复用 `gp_453f…cc06`），snapshot validator 退出 0，`submit-directory` 为 `candidate_staged`。自由概念仍失败关闭。未接现网。不得把当前状态描述为可执行生产流程。
- 实施计划：[远程 API、认证与协议实施计划](superpowers/plans/2026-07-13-cognitive-card-remote-api-auth-protocol-plan.md)。首批只接受可信上游产生的已锁定任务，不把自由主题输入伪装为服务器端知识编译。

### AUTH-01 Card OS 身份与权限

- 状态：`IN PROGRESS`
- 依赖：API-01 的路由边界。
- 范围：`read`、`submit`、`review`、`admin`；浏览器会话；CLI/Skill scoped token；撤销与轮换；审计 actor。
- 不包含：ChatGPT 登录代理、ChatGPT Cookie、OpenAI Token。
- 已实现：machine token 签发、列表和按 token ID 撤销；scope implication、过期与即时撤销；请求级仓储关闭；原始 token 只在签发时返回一次，日志和数据库仅保留安全标识/摘要。
- 已部署：machine token 的 TLS 路径、跨服务重启持久化和即时撤销已用一次性 token 验收；当前没有遗留长期验收 token。
- 未完成：浏览器会话、面向个人服务器运维的正式轮换/恢复流程和长期客户端凭据操作面。
- `0.3.1` 批次验收：machine token 最小权限生效；撤销立即阻止认领和提交；日志和数据库不含原始密钥。
- `AUTH-01` 完成条件：上述批次保持通过；浏览器会话、正式轮换/恢复流程和 TLS 部署身份边界完成验收。

### PROTO-01 协议发现与兼容

- 状态：`DONE`
- 依赖：EXEC-01。
- 范围：server version、protocol range、packet/result schema、minimum Skill release、capability flags 和稳定升级错误。
- 已完成：`0.3.1` capability 文档、规范无符号十进制协议头、minimum Skill release `0.1.0` 检查，以及稳定的 `CLIENT_UPGRADE_REQUIRED` / `SERVER_UPGRADE_REQUIRED` 前置拒绝。
- 验证：不兼容请求在任务/包工作之前拒绝；版本、运行时包和 capability 版本一致；生产文档端点关闭。
- 完成条件：不兼容客户端在认领前收到 `CLIENT_UPGRADE_REQUIRED`；不兼容服务器在创建任务前收到 `SERVER_UPGRADE_REQUIRED`。

### SKILL-01 Skill 发布注册表

- 状态：`DONE`（2026-07-31，完整 `0.1.1` 生产 stable provisional 门禁通过后）
- 依赖：PROTO-01。
- 进展：registry/installer 基础设施已完成本地与生产门禁；完整 `0.1.0` 于 2026-07-31 首次激活生产 stable 后，因现网验收发现客户端 `auth delete` 缺陷执行 provisional 回滚恢复 absence（门禁按设计工作），修复版 `0.1.1`（归档 `f162ad7b…`，source commit `f8abe20`）同日重新发布并激活 stable;immutable `0.1.0` 保留为不激活历史。
- 目标路径：
  - `/skill/v1/manifest.json`
  - `/skill/v1/releases/<version>/cognitive-card-os.zip`
  - `/skill/v1/releases/<version>/sha256.txt`
- 完成条件：发布不可变、摘要可验证、stable 可回滚、旧客户端可检测兼容性。

### SKILL-02 薄 Skill 客户端

- 状态：`IN PROGRESS`（本地代码、两个隔离安装与现网上传验收已通过；待第二台真实 Codex 电脑安装同一摘要）
- 依赖：API-01、AUTH-01、PROTO-01、SKILL-01。
- 前置条件：API/AUTH 最小生产门禁与 SKILL-01 registry/installer 基础设施均已验证；完整客户端由本任务实现并激活生产 stable（实际发布版本 `0.1.1`，见 SKILL-01 进展）。
- 范围：输入收集、本地形状校验、服务发现、任务创建、包领取、摘要确认、候选上传、错误解释、离线限制和版本升级。
- 完成条件：两台独立 Codex 客户端安装相同发布摘要，并能完成同一服务器上的任务领取与结果上传。

### MIG-01 历史资产发现、摘要与去重

- 状态：`DONE`
- 权威清单：[历史资产迁移清单](cognitive-card-os-asset-migration-inventory.md)。
- 已完成：10 个声明根全部只读扫描；808 个来源别名聚合为 622 个 SHA-256 内容对象，形成 170 个重复组、159 个同名不同内容候选组和 138 个 PNG/WebP 衍生候选组。
- 测量：来源总计 893,825,675 字节，唯一内容 571,623,546 字节；盘点前后设备/inode/路径/大小/mtime/ctime 摘要一致，内容级复现检查通过。
- warnings：共 70 条规则性跳过记录，其中 28 条 `excluded_name`、42 条 `unsupported_extension`；没有缺失根、不可读元数据、扫描中变化、不安全源项或媒体类型不匹配。
- 产物：[latest 指针](../migration/card-os/generated/latest.json)、[机器 inventory](../migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/inventory.json)、[重复报告](../migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/duplicate-report.md) 和 [warnings](../migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/scan-warnings.json)。
- 后续：人工复核 170 个重复组、159 个同名候选组和 138 个衍生候选组；在导入 API、严格 package 验证和不可变存储就绪后启动 MIG-02，不在盘点阶段自动删除、选择或发布资产。
- 完成条件：每个候选文件有稳定 `migration_asset_id`；相同内容合并来源别名；无文件在盘点阶段被移动或删除。
- 实施计划：[历史资产机器清单与去重实施计划](superpowers/plans/2026-07-13-cognitive-card-asset-inventory-dedup-plan.md)。

### MIG-02 A/B 级结构化 package 导入

- 状态：`BACKLOG`
- 范围：兔子完整包，以及升级后的古生物包。
- 依赖：MIG-01、API-01、严格 package 验证和服务器不可变存储。
- 完成条件：所有声明文件、摘要、模板、内容锁和 QA 由目标服务器版本复算；重复 Stegosaurus 包有明确主来源和 provenance 关系。

### MIG-03 C 级旧主题重制

- 状态：`BACKLOG`
- 范围：7 种深圳植物、13 个旧 `kids-world` 知识主题和可复用旧图片。
- 依赖：TMPL-01、AGE-01、RENDER-01、QA-01、PUBLISH-01。
- 完成条件：每个迁移主题通过现行分类、来源、命题、四卡、内容锁、打印和 QA；旧图只作为审核过的素材或参考，不继承旧发布状态。

### PORTAL-01 只读资产门户

- 状态：`BACKLOG`
- 目标入口：`https://www.yutou.space/card-os/`
- 范围：搜索、筛选、四卡预览、PDF、manifest、来源、QA、摘要、版本历史和状态隔离。
- 完成条件：未授权用户看不到 owner-only、隔离或草稿资产；发布版本可稳定下载。

### UPLOAD-01 浏览器手动上传

- 状态：`BACKLOG`
- 依赖：AUTH-01、API-01。
- 范围：查看已领取生成包、上传声明文件、显示摘要和验证结果、按错误修正重试。
- 完成条件：不依赖 MCP 写能力即可完成 eligible packet；验证规则与薄 Skill 完全相同。

### SITE-01 Card OS 替换 `kids-world`

- 状态：`BACKLOG`
- 范围：以 `/card-os/` 提供新的知识首页、搜索、package 详情、四卡、PDF、来源、QA 和历史版本。
- 依赖：PORTAL-01、PUBLISH-01、MIG-01；13 个旧主题均有迁移或归档决定。
- 完成条件：新站通过移动端、桌面端、权限、打印和链接验收后成为主入口；`spider-verse` 与 `paw-patrol` 继续作为旧版主题馆。

### SITE-02 旧站兼容与重定向

- 状态：`BACKLOG`
- 依赖：SITE-01。
- 范围：旧 `kids-world` 只读兼容页、旧 URL 映射、替代说明、渐进重定向和回滚开关。
- 完成条件：已索引旧链接无静默 404；新旧 package/provenance 映射可查询；可在一次部署内回滚入口切换。

### RENDER-01 四卡与打印渲染

- 状态：`BACKLOG`
- 范围：固定四页顺序、文本忠实布局、图像轨、A4 PDF、字体与中英文断行、manifest 指纹。
- 抢救来源（ADR-001）：存档分支的受治理 renderer（`render_card_candidate.py`、family style/profile、不可变 render-set 与原子指针）为候选实现；真实高视觉素材上的排版质量尚未验证。
- 完成条件：渲染器只消费内容锁；输出字节和渲染输入均有摘要；打印 QA 通过。

### QA-01 严格 QA 与人工复核

- 状态：`BACKLOG`
- 范围：分类、模板、命题、语言、COPY、来源、未知项、安全、图像、排版、未声明文件和内容锁复算。
- 抢救来源（ADR-001）：存档分支的 production-record 验证器、双语 registry 绑定与 `audit-package` 离线审计为候选实现；注意其"人工复核"目前只是本地 receipt，须按服务器权威模型重建。
- 完成条件：机器 QA 通过后才进入 `awaiting_review`；人工复核有明确 actor、决策和审计记录。

### PUBLISH-01 不可变发布

- 状态：`BACKLOG`
- 依赖：QA-01。
- 范围：package revision、manifest、四卡、PDF、来源、QA 摘要、创建历史和授权下载。
- 抢救来源（ADR-001）：存档分支的 package-v5 客户端打包/审计工具与服务器接纳面 `e78c2fa` 是本条目的候选实现；抢救前必须先关闭两个评审 Block（服务器 authority 闭包复算、gallery revision 资产绑定），修复 publisher fixture 失同步与过时 mode pin 使分支套件转绿，并完成 withdraw、容量门禁、备份与部署硬化。
- 完成条件：发布版本不可原地修改；撤回和替代保留历史关系。

### MCP-01 只读 MCP

- 状态：`BACKLOG`
- 依赖：稳定的查询 API 和 AUTH-01。
- 范围：capability、注册表身份、任务状态、生成包检查、资产搜索、package metadata 和授权下载链接。
- 完成条件：MCP 不拥有独立状态机，不承担首版写入路径。

### DEPLOY-01 Card OS 服务部署

- 状态：`DONE`
- 目标：个人服务器，域名 `www.yutou.space`。
- 依赖：API-01、AUTH-01 的最小可运行版本。
- 已完成：应用 `0.3.1` / `c2a898cba5b8a8948c06688d8c2a387353d7cbbe` 已按 systemd + Python venv + 版本化 release + Nginx 方案部署；非 root 运行、HTTPS、回环监听、持久化、一次性 token 撤销、本机备份、隔离恢复和 Nginx 配置级回滚均通过。
- 证据：[生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md)。
- 正式设计：[个人服务器部署设计](superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md)。
- 实施计划：[个人服务器部署实施计划](superpowers/plans/2026-07-14-cognitive-card-server-deployment-plan.md)。
- 完成条件：已满足；现有 `/`、`/kids/`、`/sync/` 行为保持不变。

### OPS-01 容量、备份与监控

- 状态：`IN PROGRESS`
- 已完成：根磁盘使用率 55%/inode 21% 的终态基线；SQLite 在线备份、候选摘要、14 天本机保留、唯一规范批次、manifest 校验和隔离恢复演练均通过；Certbot timer 活动。
- 待办：加密异地副本；根磁盘早于 75% 的容量/inode/备份新鲜度告警；域名证书、Certbot 和 health/capabilities 的可投递告警。操作入口见 [生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md)。
- 完成条件：异地副本可验证恢复；容量告警早于 75%；备份新鲜度、证书和健康异常均能可靠投递。

### ACCEPT-01 兔子端到端验收

- 状态：`BACKLOG`
- 输入：兔子、深圳、`age-5-6`、中英文、打印版。
- 完成条件：从正式输入到四卡、PDF、QA、复核和门户发布全链路完成；可从第二终端查看同一不可变版本。

### ACCEPT-02 第二个哺乳动物一致性验收

- 状态：`BACKLOG`
- 依赖：ACCEPT-01、TMPL-01。
- 对象选择规则：与兔子同为 `life + entity + animal/mammal`，但外观、习性和人与其关系足够不同。
- 完成条件：两者解析为同一模板族和固定骨架；差异只来自事实、可选槽位和图像元素。

## 5. 近期执行顺序

下一轮按依赖顺序一次启动一个可独立验收的子项目：

1. 工作区按 [ADR-003](decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md) 收敛到知识管线三角色；已合入切片撤 checkout。AUTHOR 本地提交 `1facb79`，generation-input 本地提交 `4ca3e0e`（含接合），均未 push。
2. **接合合同**：已本地提交 `4ca3e0e`。focused `18` 项 PASS（v1 `11` + join `7`）。接合 lock 摘要四对象 `final_content_lock`（与 AUTHOR `rabbit-composite` manifest 对照一致）；同一 FACT、不同 knowledge-core revision 产生不同接合 lock；FACT 中不存在于 knowledge-core 的 `proposition_id` fail closed。v1 FACT 密封合同未改。功能分支未 merge 进 `main`。
3. **集成分支**：已开 `knowledge-pipeline-v1`（基线 `1facb79`，merge `4ca3e0e` @ `3001ba1`，authoring 接合 lock `1f9c42f`，LIB-01 `b672949`，PROJ-01/WIRE-01 `9e0c353`）。ADR-002 §18 服务器管理批次已落地。选择面与 HTTP/DB 接线已本地提交。未 merge 进 server `main`，未 push。
4. 分类接入（KNOW-01）和年龄/语言表达（AGE-01）保持独立立项，不因预览未展示而删 Plan 元数据。
5. 存档生产核心（tag `archive/card-os-thin-skill-v1-20260717`）仍按 ADR-001 留给 RENDER/QA/PUBLISH 抢救，不充当 Knowledge Core 存储层，也不再为该切片保持长期 worktree。
6. 客户端、发布链与可信上游可用后执行 `ACCEPT-01`。并行治理项继续人工复核 MIG-01 的重复组，不自动删除。

门户、渲染（独立立项部分）和 MCP 不进入下一实现批次。

## 6. 更新记录

### 2026-08-30

- WIRE-01：HTTP/DB 受控接线。独立设计 `docs/superpowers/specs/2026-08-30-knowledge-library-http-db-wiring-design.md`。`knowledge-pipeline-v1` 上 focused HTTP library + 回归合计 `200` 项 PASS，含 auth registry 的 HTTP 套件 `251` 项 PASS。已与 PROJ-01 一并本地提交 `9e0c353`；未 add `uv.lock`；server `main` 仍 `c2a898c`；未 push。
- PROJ-01：Projection family 选择面。独立设计 `docs/superpowers/specs/2026-08-30-projection-family-selection-design.md`。`knowledge-pipeline-v1` 上 focused projection-family 9 项 + 回归合计 `187` 项 PASS。已与 WIRE-01 一并本地提交 `9e0c353`；未 add `uv.lock`；server `main` 仍 `c2a898c`；未 push。
- ADR-002 §18 / LIB-01：在 `knowledge-pipeline-v1` 增加知识库 candidate 接收、不可变 revision、current pointer 与 `unlist_current` 解析。独立设计 `docs/superpowers/specs/2026-08-30-knowledge-library-revision-current-design.md`。对照设计补路径安全与验收缺口测试后 focused library+回归 `178` 项 PASS。已本地提交 `b672949`（5 文件）；未 add `uv.lock`；server `main` 仍 `c2a898c`；未 push。
- 用户授权后开 `knowledge-pipeline-v1`：从 knowledge-core `1facb79` 建分支，merge 迁入 `4ca3e0e`（`3001ba1`），authoring lock 改为接合 revision（`1f9c42f`）。focused generation-input+authoring `36` 项、contract `128` 项 PASS。功能分支尖端未动；server `main` 仍 `c2a898c`。未 push、未现网。
- 接合合同已在 `codex/api-01-generation-input-v1` 本地提交 `4ca3e0e`（6 文件；未 add `uv.lock`）。focused `18` 项 PASS。`merge-base --is-ancestor 1facb79 HEAD` 与反向在功能分支上均为非 0；集成分支上两者均为祖先。
- [ADR-003](decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md) 接受：工作区按知识管线三角色治理；活 checkout 设上限；generation-input 与四对象存储在接合合同测试通过前不得 merge。server 活 checkout 已收成 main + knowledge-core + generation-input；kids 撤掉 5 个已合入/归档 worktree，thin-skill 因未提交文档未强制删除。
- 用户授权后三个工作区分别本地提交，未混提交、未 push：knowledge-core `1facb79`（AUTHOR-02/03/04）；IMPL-2 `878a28d`（IMPL-2/3/4 + snapshot compat + catalog 新条目）；kids 三份任务文档另一次 commit。ae563e introducing commit 为 `878a28d`；catalog `registry_commit` 仍为 `9c1b82b`。
- 新 snapshot 上兔子 A→B→C generate 本机 loopback 已跑通：全新 `/tmp/card-os-impl4-rabbit-ae563e.*`，短期 job-bound 0600 token，seal lock `sha256:15b8ea8b5ceb…ce2a`，packet `gp_3216c83d9a4340b2bb2a5bd3c23c6d06`（未复用 `gp_453f503267f24e7aa40c65dd3db1cc06`），`build_rabbit_record` 写出的 production record 经 `ae563e` validator 退出 0，`submit-directory` 为 `candidate_staged` 201。token 已撤销，loopback 已停。未接现网。
- 兔子/mammal snapshot 兼容修复：新不可变 snapshot `sha256:ae563ea0…1f20` active，旧 `47d2…d4c1` retained。mammal `page_zones`、life/mammal learning-axis、rabbit visual vocabulary、safety 文本与 sealed FACT 对齐；空 unknowns / 空 uncertainty 不再被恐龙假设拒绝。focused 107 项 PASS（含 9 项 compat）。独立评审五闭包 PASS。未接现网。
- `API-01-IMPL-4` 确定性切片已落地（focused 98 项 PASS）。新 snapshot 上兔子 generate 本机 A→B→C 已跑通（validator 退出 0、`candidate_staged`）。未接现网。
- `API-01-IMPL-3` sealed-input store、`compiler_import` 写入、受限 GET、原子 compiled-jobs 与 executor 门禁已在同一隔离分支落地。focused HTTP/auth/generation-input 回归 92 项 PASS。未接 Codex。
- `API-01-IMPL-2` generation-input 纯合同在隔离 server 分支 `codex/api-01-generation-input-v1`（基线 IMPL-1 `9c1b82b`）落地：schema、snapshot catalog 绑定、模板 resolver 复算、template composite 固定向量、generation input lock、FACT/source/unknown 闭包。focused suite 11 项 PASS。未接 HTTP/DB。未启动 Codex。
- `AUTHOR-04` 合成时效试产完成：CLI 对过期 Publish fail closed；review due 走 Candidate；revision 替代保留 superseded 历史。authoring/contract `17/145` PASS。
- `AUTHOR-05` 三类试产字段证据完成：无全局 temporal 默认；`valid_from` 三次空值但推迟可选化；分类/AGE/current 另立项。未改合同。

### 2026-08-19

- 用户书面批准 [ADR-002](decisions/ADR-002-knowledge-core-and-projection-architecture.md) 与 Knowledge Core 设计；[Knowledge Core Contract Pilot 实施计划](superpowers/plans/2026-08-19-knowledge-core-contract-pilot-implementation-plan.md) 已获执行审阅通过。
- 新增 `KNOW-02`：以 API-01 snapshot base `9c1b82b` 为基线，在隔离分支验证 Knowledge Core 四对象纯合同、闭包、两级锁和 rabbit/geometry/time/four-card fixtures；本批零 HTTP、DB 或 runtime wiring。
- 将本地 authoring MVP、实际 four-card converter、服务器 revision/current/freshness 管理与 Portal 明确拆为后续批次；近期执行顺序不再把第二台电脑验证列为当前动作，未改变 `SKILL-02` 的历史完成条件。
- `KNOW-02` 合同与 [Pilot Evidence](knowledge-core-contract-pilot-evidence.md) 已完成并随 AUTHOR-01 固化到 server commit `120e5fc`；2026-08-21 fresh 结果为 `128` 项 focused PASS、零 runtime 引用，声明依赖环境下完整 suite `444` 项 PASS。原 2 Critical、4 Important、1 Minor 及两项文档 residual 均已关闭，状态为 `DONE`。
- `AUTHOR-01` 已完成最小 local authoring vertical slice：标准库 CLI 从已提供来源/命题的 request 生成四对象、Publish validation、不可覆盖 revision 目录和 escaped HTML 浏览页；fresh authoring/combined suites 为 `5/133` 项 PASS，完整 suite `444` 项 PASS。下一步直接做真实主题试产。

### 2026-08-01

- 完成 API-01-IMPL-1(core snapshot，服务器应用仓分支 `codex/api-01-core-snapshot`，本地未 push):`cognitive-card-core-snapshot-v1` 生成/校验/catalog 工具 + 35 项测试转绿；34 成员完整快照（snapshot_id `sha256:47d2cb65…d4c1`，源自抢救分支 `4d5ffe4`）导入 `core-snapshots/` 并在 catalog 激活（registry_commit `2837c8b`)；独立评审发现 1 Important（忽略文件可进入快照）与 3 Minor，已全部修复并补回归测试；服务器应用零行为变更（既有套件 307/309，仅 2 项 real-uvicorn 集成测试在基线同样失败，属本地环境问题）。
- API-01 可信自由请求编译入口修订设计（`docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`）经用户书面确认：executor-neutral compile/generate 两阶段合同、服务器不可变 sealed input store、两级内容锁、完整 34 成员 core snapshot manifest、compiler/submitter 凭据隔离、原子 compiled-jobs、executor capability 门禁（旧 `0.1.1` 不可见/不可 claim)、执行侧代码经 governed Skill release 分发；实施按 IMPL-1..5 分批另行立项，不授权任何实现与生产变更。

### 2026-07-31

- 完成 SKILL-02 薄客户端实施（分支 `codex/card-os-thin-client-v1`，计划 Task 1–9):packet 契约客户端（transport/capability 协商、三级凭据后端、packets/jobs 命令、结果校验与自动上传）、Skill 文档与契约测试（279 项 thin-client 测试）、pre-publish 与 install/boundary forward tests 全部通过。
- 完整 `0.1.0`（归档 `217efb34…`，source commit `6f06d7a`）首次激活生产 stable;Task 8 现网验收主流程（claim→get→本地生成→complete→submit→exact replay→`ATTEMPT_BODY_CHANGED`→撤销→403 `AUTH_REVOKED`）全部通过，但发现 macOS Keychain `auth delete` 实际不删除数据的缺陷（Important)；按计划执行 provisional 回滚恢复 manifest absence 并复验 404——provisional 门禁按设计工作。
- 修复版 `0.1.1`（零长度非空 buffer 截断，不突破五函数绑定集；归档 `f162ad7b…`,source commit `f8abe20`）经 0C/0I 评审、双构建字节一致后发布并激活 stable;Task 7 关键项与 Task 8 全流程在新版本上重跑通过，`auth delete` 真实后端实证 absent;Task 8 独立评审 0C/0I。immutable `0.1.0` 保留为不激活历史。
- `SKILL-01` 标记 `DONE`;`SKILL-02` 标记 `IN PROGRESS`（完成条件的"第二台真实 Codex 电脑安装同一摘要"尚未满足，该硬条件超出本任务可控范围）。
- 客户端 attempt journal 记录 `content_lock_digest` 与 per-artifact `media_type`（满足跨调用 exact replay 的最小元数据，与设计 §10 清单存在有意偏差，待设计文档下次修订追认）。
- 审计 `codex/card-os-thin-skill-v1`（领先 main 29 个提交）：其中 SKILL-02 薄客户端计划（`docs/superpowers/plans/2026-07-15-cognitive-card-thin-client-plan.md`）Task 1–9 均未执行，分支上的 `card_os_client.py` 是另一套 package-v4/v5 契约；PORTAL/RENDER/QA/PUBLISH 与恐龙模板族属越序 BACKLOG 工作；`skills/cognitive-card-os/core/` 将生产核心迁入 Skill 包的方向与本账本"服务器统一权威"约束冲突。分支尖端未通过自身测试套件且 Task 8 评审未关闭，已用 tag `archive/card-os-thin-skill-v1-20260717` 存档，不整体合入。
- 客户端契约与生产核心归属已经用户书面选定并固化为 [ADR-001](decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md)：M1 领取/提交只走 packet 契约，SKILL-02 按 2026-07-15 thin-client 计划实施；生产核心权威保留服务器；package-v5 上传面归入 PUBLISH-01 后续批次；分支资产按批抢救。
- 用户进一步确认：存档分支抢救**优先于从零重建**（此前重新生成时发现历史积累丢失）。执行顺序插入独立抢救批次（SKILL-02 之后、ACCEPT-01 之前）；API-01 可信自由请求编译入口以存档 `core/` 为候选实现，PUBLISH-01/RENDER-01/QA-01 均登记对应抢救来源与前置修复项。
- 回填 2026-07-16 的 SKILL-01 基础设施状态修正（原记录长期滞留在分支 worktree 未提交）。

### 2026-07-16

- 完成 SKILL-01 registry/installer 基础设施本地门禁与生产 provisional 部署：确定性构建、验证优先安装、不可变 publisher、只读 Nginx namespace、回滚和公网边界均已验证；生产 stable 与 release 按设计保持不存在。
- `SKILL-01` 保持 `IN PROGRESS`，等待 SKILL-02 完成并激活完整 `0.1.0`；`SKILL-02` 从 `BLOCKED` 转为 `READY`。
- 生产 installer bootstrap 指向 reviewed immutable snapshot；精确 preflight 备份保留到远端源码权威与最终基础设施 gate marker 通过。

### 2026-07-15

- 完成 `DEPLOY-01`：应用 `0.3.1` 已通过正式 HTTPS、非 root systemd、持久化、回环监听、一次性 token 撤销、本机备份、隔离恢复和 Nginx 回滚门禁；生产证据与日常命令已进入权威运维记录。
- `OPS-01` 保持 `IN PROGRESS`：本机恢复点已经验证，剩余异地备份、容量/备份新鲜度和证书/健康告警。
- 下一执行顺序调整为 `SKILL-01`、`SKILL-02`、`ACCEPT-01`；`SKILL-02` 的服务器部署阻塞已经解除，只等待可安装 Skill release。
- 将受治理部署链当前目标提升为已审查的应用 `0.3.1` / `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`；release schema 保持 v2，协议保持 `1`，minimum Skill release 保持 `0.1.0`。
- 将在线备份门禁补强为：从只读在线 WAL 源完成 backup 后，先把隔离目标精确归一化为 `journal_mode=DELETE`，再做完整性、manifest 与原子发布；不得改动源 WAL。

### 2026-07-14

- 完成远程锁定任务 API、machine scoped token 与 capability/protocol 批次；服务版本 `0.3.0`，273 项测试和 whole-branch C0/I0/M0 审查通过。
- 将 `PROTO-01` 标记为 `DONE`；`API-01`、`AUTH-01` 保持 `IN PROGRESS`，明确部署、自由规范化任务入口和浏览器会话尚未完成。
- 将 `SKILL-01` 转为 `READY`，并在 API/AUTH 部署和可安装 release 完成前把 `SKILL-02` 标记为 `BLOCKED`。
- 完成 MIG-01 机器清单与去重快照：10 个根、808 个来源别名、622 个内容对象；盘点前后守卫一致。

### 2026-07-13

- 建立整体设计和唯一任务账本。
- 记录订阅执行核心 `0.2.0` 完成状态。
- 将“可远程领取与提交”设为当前里程碑。
- 将 API、认证和协议发现设为下一独立设计批次。
- 确认 Cognitive Card OS 将替换 `kids-world` 知识站；旧故事主题保留为旧版主题馆。
- 扫描指定 Codex 任务及工作目录，建立历史资产迁移分级和双轨切换门禁。
