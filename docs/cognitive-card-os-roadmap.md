# Cognitive Card OS 路线图与任务账本

状态：活动中  
最近更新：2026-09-02
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

**单人知识主路径**

目标：单人维护、单人使用。先跑通 结构化输入 → 四对象 revision → library current → **浏览并确认 Projection family**。现网 `0.3.1` 继续承担锁定任务领取与提交。第二台电脑、加密异地备份、公网 Portal、旧站替换不是本里程碑门禁。见 [ADR-004](decisions/ADR-004-single-operator-main-flow.md)。

本里程碑当前切片：`API-01` 本刀已在 server worktree 实施（未 commit、未生产）；2026-09-02 本机 loopback 试用 `ragdoll-cat` 已 Confirm current，**止于知识源冻结**。下一会话：`API-01-TPL`。图形打印/插画另立 `IMG-01`（未设计）。`WB-03` 本机 `DONE`（文字四卡；不接生图；样式后置）。`WB-02` 本机 `DONE`。不打 release、不默认上现网画廊。

**M1（历史，单人门禁已关闭）**

原目标：安装薄 Skill 的受信任 Codex 客户端，经 `www.yutou.space` 领取生成包并上传候选。单人侧已由本机代码、双隔离安装与现网上传满足（`SKILL-01` / `SKILL-02` / `DEPLOY-01` / `PROTO-01`）。第二台真实电脑改为 `SKILL-03`。`API-01` 的自由概念编译入口与 `AUTH-01` 浏览器会话仍不阻塞知识主路径。

资产迁移作为并行治理工作流推进，但在正式导入工具完成前不写入服务器。发现清单见 [历史资产迁移清单](cognitive-card-os-asset-migration-inventory.md)。

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
| BROWSE-01 | 知识浏览与 Projection 确认 | DONE | 已本地提交进 `e9bfd22`；未 merge 进 main |
| CONV-01 | four-card converter | DONE | 已本地提交进 `e9bfd22`；未 merge 进 main |
| RUN-01 | 本机执行接合密封 | DONE | 已本地提交 `c55f51b`；未 merge 进 main |
| KNOW-01 | 分类与对象类型体系 | DONE | 已本地提交 `4083ce7`；未 merge 进 main |
| TMPL-01 | 领域/形态模板族 | DONE | 已本地提交 `cbaf2b4`；未 merge 进 main |
| AGE-01 | 3–4、5–6 岁配置 | DONE | 已本地提交 `4e0ea52`；未 merge、未现网 |
| AGE-02 | 8、10、15 岁配置 | BACKLOG | 分年龄建立认知与语言规范 |
| EXEC-01 | 订阅执行核心 | DONE | 作为 API 应用服务使用 |
| API-01 | HTTPS 写入 API | IN PROGRESS | server `91b7cf3` 已提交 compile+TPL；未现网；不标 DONE |
| API-01-TPL | 加厚知识编译提示词 | IN PROGRESS | 已随 `91b7cf3` 提交；未现网 |
| IMG-01 | 图形投影生图提示词 | BACKLOG | 选打印/插画时扩完整 ChatGPT 生图提示词并收回图；对标 API-01 复制/粘贴 |
| AUTH-01 | Card OS 身份与权限 | IN PROGRESS | machine token 已部署；浏览器会话不阻塞主路径 |
| PROTO-01 | capability/protocol discovery | DONE | 作为 Skill 注册表和部署兼容门禁使用 |
| SKILL-01 | Skill 发布注册表 | DONE | 完整 `0.1.1` 已 provisional 激活生产 stable；回滚与不可变历史已实证 |
| SKILL-02 | 薄 Skill 客户端 | DONE | 单人门禁：本机、双隔离安装、现网上传已通过；第二台电脑改 SKILL-03 |
| SKILL-03 | 第二终端同一摘要 | BACKLOG | 多终端阶段再做；不阻塞主路径 |
| MIG-01 | 历史资产发现、摘要与去重清单 | DONE | 人工复核重复与衍生候选，等待 MIG-02 导入条件 |
| MIG-02 | A/B 级结构化 package 导入 | BACKLOG | 依赖导入接口、严格验证和 MIG-01 |
| MIG-03 | C 级旧主题重制 | BACKLOG | 依赖模板、发布链路和 MIG-01 |
| PORTAL-01 | 只读资产门户 | DONE | 已本地提交进 `fd696c2`；未 merge 进 main |
| UPLOAD-01 | 浏览器手动上传 | BACKLOG | 依赖 AUTH-01、API-01 |
| SITE-01 | Card OS 替换 `kids-world` | DONE | 现网根 CTA 指向画廊；Nginx 已反代 `/card-os/` |
| SITE-02 | 旧站兼容与重定向 | DONE | 现网 stub/hash 已抽查；回滚仍是 `activeMode=parallel` |
| RENDER-01 | 四卡排版与打印 PDF | DONE | 已本地提交 `1ef6edc`；未 merge、未现网 |
| QA-01 | 严格 QA 与人工复核 | DONE | 已本地提交 `37a5927`；未 merge、未现网 |
| PUBLISH-01 | 不可变 package 发布 | DONE | 已本地提交 `7a127b4`；未 merge、未现网 |
| MCP-01 | 只读 MCP | BACKLOG | 依赖稳定查询 API |
| DEPLOY-01 | Card OS 服务部署 | DONE | 0.3.1 基线；升级门禁见运维记录 |
| DEPLOY-02 | 现网落地试点 | DONE | 现网画廊+兔子包+根 CTA；未 merge server `main` |
| WB-01 | 令牌操作台只读知识源 | DONE | 现网 `115377b`；ops `/card-os/ops/`；library AUTHOR-02；画廊未改 |
| KNOW-03 | 知识源覆盖与准确性 | DONE | 本机 `7aaeb2b`；实现不重开；现网切应用见 KNOW-03-prod |
| KNOW-03-prod | 现网装上 KNOW-03 应用 | DONE | 现网 `current`=`7aaeb2b`；library AUTHOR-02；Nginx 未 reload；未 merge `main` |
| KNOW-04 | 兼容套件上库 | DONE | 生产六主题 current；`rabbit`=`0002`；无格温；应用仍 `7aaeb2b` |
| WB-02 | 四卡成熟视觉投影 | DONE | 本机 `5c11880`；不现网 |
| WB-03 | 选投影→生成→上架画廊 | DONE | 本机 worktree；基础信息已接受；样式后置；未现网 |
| OPS-01 | 本机备份与恢复 | DONE | 本机 SQLite/候选备份、隔离恢复、14 天保留已验收 |
| OPS-02 | 异地拷贝与告警 | BACKLOG | 可选：把已验证本机备份拷到第二块盘；不做加密复制服务 |
| ACCEPT-01 | 兔子完整验收 | DONE | 已本地提交 `10b14c8`；未 merge、未现网 |
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

### BROWSE-01 知识浏览与 Projection 确认

- 状态：`DONE`（实现与 focused 测试完成；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（实现）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：[ADR-004](decisions/ADR-004-single-operator-main-flow.md)、[独立设计](superpowers/specs/2026-08-30-knowledge-browse-projection-confirmation-design.md)、LIB-01、PROJ-01、WIRE-01。
- 目标：确认点 1 的人机界面——列出 topic / current / 历史 revision，只读展示 Knowledge Core，展示 Projection family 选择面。默认确认不写盘；覆盖 family 仍走 CLI 重编译。
- 完成结果：CLI `browse` 写出 `index.html` 与 `{topic}__revision-NNNN.html`；兔子 current chosen 为 `chaptered-guide` 且 `four-card` 为 discouraged；几何 current chosen 为 `progressive-exploration`。loopback GET 列出 topic / revisions / 四对象只读视图。不写 Knowledge Core，不等于 PORTAL-01。
- 验收证据：server `knowledge-pipeline-v1` 上 browse + library / projection-family / HTTP library / auth registry / generation-input / authoring / contract / HTTP compiled 合计 focused `241` 项 PASS。已与 CONV-01 一并本地提交 `e9bfd22`。未 add `uv.lock`。未 merge 进 server `main`（仍 `c2a898c`），未 push。
- 非范围：浏览器会话、公网 Portal、UI 内 publish、CONV-01、Renderer、现网。

### CONV-01 four-card converter

- 状态：`DONE`（实现与 focused 测试完成；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（实现）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：BROWSE-01、接合 lock、ADR-001 抢救边界、[独立设计](superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md)。
- 目标：把 library current 的四对象映射为现有接合 generation-input，使四卡 executor 能密封同一主题。须处理 knowledge-core `source_id` 含点号与 FACT `source_id` 不允许点号的映射。
- 完成结果：CLI `convert` 只读 current；family 必须为显式 `four-card`；FACT `source_id` 把 `.`/`_` 换成 `-`，碰撞 fail closed；磁盘 knowledge-core 不被改写。`canonical_claim` 临时同时填入 FACT `cn`/`en`。不写 production-record 本体。
- 验收证据：server `knowledge-pipeline-v1` 上 converter 10 项 + library / browse / HTTP / projection-family / generation-input / join / authoring / contract / auth 合计 focused `248` 项 PASS。已本地提交 `e9bfd22`。未 add `uv.lock`。未 merge 进 server `main`（仍 `c2a898c`），未 push。
- 非范围：新 Projection family、PORTAL-01、完整 RENDER/QA/PUBLISH、写出 production-record 本体、现网。

### RUN-01 本机执行接合密封

- 状态：`DONE`
- 权威仓库：`cognitive-card-server`（实现）；任务治理为 `kids-visual-learning-pack`。
- 依赖：CONV-01、WIRE-01、EXEC-01；接合 JSON 走已有 `POST /admin/generation-inputs` 与 compiled-job 门禁。
- 目标：把 CONV-01 写出的接合 generation-input 送进本机 loopback store / compiled-job，由现有 executor 产出通过 snapshot validator 的 `production-record`。不在转换器里写 production-record 本体。
- 完成结果：默认兔子 `chaptered-guide` convert 返回 `CONVERTER_FAMILY_NOT_FOUR_CARD`；CLI 显式 `four-card` 后 publish revision 2；convert → import-job → prepare → ae563e validator 退出 0 → `submit-directory` `candidate_staged` 201。接合 lock `sha256:347c3a5c28af…d970`，packet `gp_8b24733af51b494aa5acd664b97dca85`。executor 对接合信封校验内层 v1；`job_id_for` 从内层取 object name。转换器未写 `production-record.json`。generate 仍用 ae563e 兔子夹具（snapshot 视觉/安全注册表），不是 Knowledge Core claim 的忠实投影。已本地提交 `c55f51b`。未 add `uv.lock`；未 merge `main`；未 push；未现网。
- 非范围：新 HTTP convert 端点、PORTAL-01、RENDER-01、改 Knowledge Core、API-01 自由概念编译、merge / deploy。

### KNOW-01 分类与对象类型覆盖

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `4083ce7`；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：[系统总设计 §3.2](cognitive-card-os-system-design.md)、[独立设计](superpowers/specs/2026-08-31-classification-registry-design.md)、存档 `classification-v2.md`。
- 完成结果：`classification-registry-v1` 覆盖全部受控 domain/form，每个 domain 含 subtype 词表（含 `ocean`/`arts` 等尚未出现首个对象的领域）。覆盖矩阵枚举 domain × form × subtype。`general`/`other` 接受；自由文本 `CLASSIFICATION_UNKNOWN`；歧义主路由 `CLASSIFICATION_REVIEW`。authoring 必填分类并写入 Knowledge Scope；convert/accept 可省略 `--request`，CLI 不得覆盖已登记分类。RUN-01 既有 `--request` 路径保持。
- 验收证据：classification + authoring/converter/accept focused 与 pipeline 回归 143 项 PASS；合同校验 141 项 PASS。已本地提交 `4083ce7`。未 add `uv.lock`。未 merge server `main`（仍 `c2a898c`），未 push，未现网。
- 非范围：TMPL-01 模板族、`TEMPLATE_GAP`、PORTAL、改 v1 FACT 键集、merge/现网。

### TMPL-01 领域与形态模板体系

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `cbaf2b4`；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：[系统总设计 §4.1 / §7.3](cognitive-card-os-system-design.md)、[独立设计](superpowers/specs/2026-08-31-template-family-registry-design.md)、KNOW-01、snapshot `template-routing.md`。
- 完成结果：`template-registry-v1` 登记精确 mammal / dinosaur 与全部紧凑 domain/form 族；每个 family 记录四页骨架、槽位、年龄/语言适配、结构指纹与 active 兼容行。每个 family 至少两个对象夹具，相同主路由骨架相等。`gap` 路由与 `animal/bird` 返回 `TEMPLATE_GAP`，不套用 generic fallback。未声明次领域 `INVALID_SECONDARY_MODULE`。convert 密封前走注册表。未改 snapshot 字节。
- 验收证据：template focused 10 项 PASS；与 classification / authoring / converter / accept / projection / library / browse / HTTP library / joined / generation-input / AGE / lock 合计 136 项 PASS。已本地提交 `cbaf2b4`。未 add `uv.lock`。未 merge server `main`，未 push，未现网。
- 非范围：ACCEPT-02 正式第二哺乳动物试产、PORTAL、改 v1 FACT 键集、改 snapshot、merge/现网。

### AGE-01 现有年龄与语言配置

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `4e0ea52`；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：[系统总设计 §7](cognitive-card-os-system-design.md)、[CONV-01](superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md)、独立设计 [AGE-01](superpowers/specs/2026-08-31-age-language-adapter-design.md)。
- 完成结果：`age-language-adapter-v1` 覆盖 `age-3-4` / `age-5-6`、CN 同年龄、EN `beginner`。converter 在密封前把登记儿童表达写入 FACT `cn`/`en`；未登记 claim `AGE_EXPRESSION_GAP`。安全边界原文不随年龄改写。COPY 计划不写入 generation-input；`age-3-4` 抑制正式 COPY。age-3-4 不走 snapshot 模板解析。
- 验收证据：适配器 + converter focused `27` 项 PASS；与 library / browse / HTTP library / joined / authoring 合计 `83` 项 PASS。完整 suite `561` 项中 `559` PASS，2 项既有 real-uvicorn 502。已本地提交 `4e0ea52`。未 add `uv.lock`。未 merge server `main`（仍 `c2a898c`），未 push，未现网。
- 非范围：四对象 schema、v1 FACT 键集、PORTAL、RENDER、AGE-02、HTTP 新端点、merge/现网。

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
- 未完成：HTTPS/生产验收与 2026-07-31 salvage 仍后置。本刀（ChatGPT 会员复制/粘贴 → 四对象 current）已在 server worktree `knowledge-pipeline-v1` 实施，**未 commit、未打 release、未接现网**；不得标 `DONE`。2026-09-02 隔离 loopback `/tmp/card-os-api01`：`ragdoll-cat` Confirm current r1；ChatGPT 自造 schema 缺 `learning`/`units`；本轮止于知识源冻结。下一刀 `API-01-TPL`。spec Approved：[自由 prompt 编译成知识源](superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md)。[2026-07-31](superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md) packet salvage 仍后置。当前批次仍不能被描述为通用概念创建 API。存档 `core/` 不得直接从 Skill 包形态合入（ADR-001）。
- 抢救进度：API-01-IMPL-1 snapshot 已在 `codex/api-01-core-snapshot`；API-01-IMPL-2/3/4 确定性封印、sealed-input store、compiled-jobs 与 prepare/submit 辅助已在隔离分支 `codex/api-01-generation-input-v1` 本地提交 `878a28d`（基线 `9c1b82b`，未 push）。接合合同（四对象 revision lock）已在同一分支本地提交 `4ca3e0e`。用户授权后已开 `knowledge-pipeline-v1`（基线 knowledge-core `1facb79`，merge `4ca3e0e`，authoring lock `1f9c42f`）；两条功能分支未 merge 进 `main`。未 add `uv.lock`；v1 FACT 密封合同未改。兔子/mammal production-record 兼容 snapshot `sha256:ae563e…1f20` 已导入并将 `47d2…d4c1` retained；introducing commit 为 `878a28d`，catalog `registry_commit` 仍为 `9c1b82b`。本机 loopback 已用全新 `/tmp` 与短期 job-bound token 完成 A→B→C：seal lock `sha256:15b8ea…ce2a`，新 packet（未复用 `gp_453f…cc06`），snapshot validator 退出 0，`submit-directory` 为 `candidate_staged`。自由概念仍失败关闭。未接现网。不得把当前状态描述为可执行生产流程。
- 实施计划：[远程 API、认证与协议实施计划](superpowers/plans/2026-07-13-cognitive-card-remote-api-auth-protocol-plan.md)。首批只接受可信上游产生的已锁定任务，不把自由主题输入伪装为服务器端知识编译。

### API-01-TPL 加厚知识编译提示词

- 状态：`IN PROGRESS`
- 权威仓库：`cognitive-card-server`；任务治理为 `kids-visual-learning-pack`。
- 依赖：API-01 本刀 worktree 代码（未 commit）。
- 目标：`knowledge-compile-v1` 模板列出与 `examples/authoring/rabbit-real.json` 同形的必填键（`topic.scope_type`、`classification` 合同字段、`units`+`coverage_facet`、`learning`、`sources.slug`/`kind`/`intake.search`、命题 `claim`/`source_slug`/`safety_scope` 用英文原文以便 AGE 登记表命中）。解析层对 ChatGPT 常见输出做确定性归一（围栏/说明文字、`id`/`canonical_claim`/`coverage.facets`/`learning_goal`、分类学 classification），不发明命题。操作台失败态展示 `error.code` 与 `error_path`。本机 loopback 用新主题再贴一次真实 ChatGPT 回复，不经人工改写成合同 JSON 即能 `compiled`。
- 非范围：生图提示词（`IMG-01`）；生产安装；merge `main`；打开 `source-intake-search.v1.json` 全局 enabled；改四对象 schema；从散文抽命题。
- 完成条件：模板 digest 变更；focused unittest 覆盖 ChatGPT 形态夹具过门、合同夹具仍绿、不可映射回复失败；loopback 能做则做否则交接标明；不打 release。

### IMG-01 图形投影 ChatGPT 生图提示词

- 状态：`BACKLOG`
- 权威仓库：产品规范 `kids-visual-learning-pack`；实现落在 `cognitive-card-server`。
- 依赖：知识源已能 Confirm current（API-01）；WB-02/WB-03 文字四卡路径已存在。生图不走现有 Pillow `render_locked`。
- 目标：操作员在映射阶段选择图形可视化/打印插画时，服务器扩出**完整生图提示词**（版本化模板），人复制到 ChatGPT 会员生图，再把图贴回/上传操作台后装箱。服务器仍无图像 API、无 claim。
- 非范围：本刀未开始前不写实施代码；不把「图装得下」写成知识源准入；不改 KNOW-04 六主题 current。
- 下一动作：独立设计会话写 spec，经操作者批准后再写计划与实施。
- 完成条件：待 spec 锁定（入口、模板、回传合同、与 WB-03 文字渲染的边界）。

### AUTH-01 Card OS 身份与权限

- 状态：`IN PROGRESS`
- 依赖：API-01 的路由边界。
- 范围：`read`、`submit`、`review`、`admin`；CLI/Skill scoped token；撤销与轮换；审计 actor。浏览器会话不在单人主路径上，见 ADR-004。
- 不包含：ChatGPT 登录代理、ChatGPT Cookie、OpenAI Token。
- 已实现：machine token 签发、列表和按 token ID 撤销；scope implication、过期与即时撤销；请求级仓储关闭；原始 token 只在签发时返回一次，日志和数据库仅保留安全标识/摘要。
- 已部署：machine token 的 TLS 路径、跨服务重启持久化和即时撤销已用一次性 token 验收；当前没有遗留长期验收 token。
- 未完成：浏览器会话、面向个人服务器运维的正式轮换/恢复流程和长期客户端凭据操作面。这些不阻塞 BROWSE-01（首版用 loopback 静态 HTML 或本机 token）。
- `0.3.1` 批次验收：machine token 最小权限生效；撤销立即阻止认领和提交；日志和数据库不含原始密钥。
- `AUTH-01` 完成条件：machine token 批次保持通过。浏览器会话留到多用户/公网 Portal 阶段，不作为单人主路径完成条件。

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

- 状态：`DONE`（2026-08-30，[ADR-004](decisions/ADR-004-single-operator-main-flow.md) 关闭单人门禁）
- 依赖：API-01、AUTH-01、PROTO-01、SKILL-01。
- 已完成：本机代码、两个隔离 `CODEX_HOME` 安装、生产 stable `0.1.1`、现网领取与候选上传。
- 范围：输入收集、本地形状校验、服务发现、任务创建、包领取、摘要确认、候选上传、错误解释、离线限制和版本升级。
- 完成条件（单人）：上述本机与现网路径通过。历史「两台独立 Codex 电脑」改由 `SKILL-03` 承担，不再阻塞本任务。

### SKILL-03 第二终端同一摘要

- 状态：`BACKLOG`
- 依赖：SKILL-02、多终端实际需求。
- 范围：第二台真实 Codex 电脑安装与生产 stable 相同的归档摘要，完成 doctor 与同一服务器上的领取/上传。
- 完成条件：两台独立客户端、相同摘要、同一服务器任务闭环。
- 非范围：不阻塞单人知识主路径或 BROWSE-01。

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

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `fd696c2`；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 目标入口：本机 `/card-os/`（loopback）；公网 `https://www.yutou.space/card-os/` 仍属 SITE-01。
- 范围：已发布 Artifact 的搜索、筛选、四卡预览、PDF、manifest、来源、QA、摘要、版本历史和状态隔离。
- 与 BROWSE-01 的边界：本任务不承担确认点 1（源头知识浏览与 Projection 选择）。BROWSE-01 先于本任务，且不依赖本任务。画廊不写 Knowledge Core。
- 本批结果：CLI `four_card_portal` 写出静态画廊；公开 GET 无 token；owner-only / 撤回 / 草稿对公开观众 404；`admin` 可见隔离包。下载字节等于 catalog revision。focused portal 10 项、pipeline 回归 145 项 PASS。已本地提交 `fd696c2`。未 merge、未现网。
- 完成条件：未授权用户看不到 owner-only、隔离或草稿资产；发布版本可稳定下载。
- 独立设计：[已发布 Artifact 只读画廊](superpowers/specs/2026-08-31-published-artifact-gallery-design.md)。

### UPLOAD-01 浏览器手动上传

- 状态：`BACKLOG`
- 依赖：AUTH-01、API-01。
- 范围：查看已领取生成包、上传声明文件、显示摘要和验证结果、按错误修正重试。
- 完成条件：不依赖 MCP 写能力即可完成 eligible packet；验证规则与薄 Skill 完全相同。

### SITE-01 Card OS 替换 `kids-world`

- 状态：`DONE`（仓库内入口合同、根 CTA、冻结档案与 Nginx snippet 已完成；未现网应用）
- 权威仓库：`kids-visual-learning-pack`（入口与 Nginx snippet）；画廊 HTML 仍由 server PORTAL-01 提供。
- 范围：以 Card OS 画廊为知识主入口；旧 `kids-world` 并行可达并降为冻结档案；13 个现站主题按 MIG-01 C 级冻结。
- 依赖：PORTAL-01、PUBLISH-01、MIG-01。[ADR-005](decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md) 确认不必等 MIG-03 重制。
- 本批结果：`shared/knowledge-entry.json` `activeMode=card-os`；根 `index.html` 主 CTA 指向 `https://www.yutou.space/card-os/`；Nginx snippet 反代 `/card-os/` 与 `/card-os/packages/`；capabilities 仍在 `/card-os/api/v1/capabilities`。未 merge server `main`；未 push；未现网。
- 完成条件：新站通过仓库内入口、权限隔离（沿用 PORTAL-01）、打印下载路径与链接合同验收后成为主 CTA；`spider-verse` 与 `paw-patrol` 继续作为旧版主题馆且生产根入口不暴露。
- 独立设计：[Card OS 替换 kids-world 知识入口](superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md)。

### SITE-02 旧站兼容与重定向

- 状态：`DONE`（仓库内映射、替代说明页与 `activeMode` 回滚开关已完成；未现网）
- 依赖：SITE-01。
- 权威仓库：`kids-visual-learning-pack`（入口合同、根 hub 生成器、旧路径替代说明页、kids-world hash 解析）。
- 范围：旧 URL 映射与一次部署回滚开关。不做主题重制。
- 本批结果：`#slug` / `#topic/{slug}` / `?topic=` 打开冻结主题；`boards/{slug}/index.html` 为替代说明页；根 hub 由 `activeMode` 生成，`parallel` 一次部署回滚主 CTA。默认 `activeMode=card-os`。未改 `/card-os/` Nginx。未 push；未现网。
- 完成条件：已索引旧链接无静默 404；可在一次部署内把 `activeMode` 切回 `parallel` 并重新生成根入口。
- 独立设计：[旧 URL 映射与一次部署回滚](superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md)。

### RENDER-01 四卡与打印渲染

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `1ef6edc`；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 范围：固定四页顺序、文本忠实布局、图像轨、A4 PDF、字体与中英文断行、manifest 指纹。
- 抢救来源（ADR-001）：存档分支的受治理 renderer（A4/Pillow/断行/几何校验/CropBox PDF）为合同来源；不把客户端 workspace lock 或恐龙-only family 钉死合入。真实高视觉素材上的排版质量尚未验证。
- 本批结果：服务器 `four_card_render` 消费锁定记录与 AGE-01 `copy_plan`；generate COPY 被覆盖；四页 A4 300dpi PNG + CropBox PDF；输入/输出摘要；清场区拒插图。focused renderer 11 项 PASS。未改 Knowledge Core、未扩 PORTAL、未新增 HTTP。已本地提交 `1ef6edc`。
- 完成条件：渲染器只消费内容锁；输出字节和渲染输入均有摘要；打印 QA 通过。
- 独立设计：[锁定内容四卡排版](superpowers/specs/2026-08-31-locked-four-card-render-design.md)。

### QA-01 严格 QA 与人工复核

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `37a5927`；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 范围：分类、模板、命题、语言、COPY、来源、未知项、安全、图像清场、排版摘要、未声明文件和内容锁复算；机器通过后才进入 `awaiting_review`；人工复核记录 actor、决策与审计。
- 抢救来源（ADR-001）：采用存档验证器的锁复算、COPY 溯源、双语命题绑定、未声明文件与打印页几何合同；不把客户端 `audit-package` receipt、恐龙 visual vocabulary 或 package-v5 钉死合入。人工复核按服务器权威模型重建。
- 本批结果：服务器 `four_card_qa` 消费锁定记录与 RENDER-01 产物；issues 非空则 `machine_failed`；通过后 `awaiting_review`。`approve`/`reject` 需要非空人类 actor 并追加 `audit.jsonl`。不发布、不改 Knowledge Core、不扩 PORTAL、不新增 HTTP。focused QA 12 项 PASS。已本地提交 `37a5927`。
- 完成条件：机器 QA 通过后才进入 `awaiting_review`；人工复核有明确 actor、决策和审计记录。
- 独立设计：[严格 QA 与人工复核](superpowers/specs/2026-08-31-strict-qa-human-review-design.md)。

### PUBLISH-01 不可变发布

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `7a127b4`；未 merge 进 main，未 push）
- 权威仓库：`cognitive-card-server`（`knowledge-pipeline-v1`）；设计与任务治理为 `kids-visual-learning-pack`。
- 依赖：QA-01。
- 范围：package revision、manifest、四卡、PDF、来源、QA 摘要、创建历史；本机 revision 目录即本批次下载句柄。
- 抢救来源（ADR-001）：采用存档 package-v5 的不可变包、内容锁贯穿 manifest、撤回/替代保留历史合同；不把 `e78c2fa` 上传面、客户端打包器或恐龙词表钉死合入。公网 URL、容量门禁与部署硬化仍属 PORTAL / 运维后续。
- 本批结果：服务器 `four_card_publish` 只消费 QA-01 `approved` 报告与 RENDER-01 产物；`revision-NNNN` 不可覆盖；相同内容对 current 幂等；撤回清空 pointer 并保留目录；替代写入新 revision 并记录 `supersedes`。不改 Knowledge Core、不扩 PORTAL、不新增 HTTP。focused publish 12 项 PASS。已本地提交 `7a127b4`。
- 完成条件：发布版本不可原地修改；撤回和替代保留历史关系。
- 独立设计：[不可变 package 发布](superpowers/specs/2026-08-31-immutable-package-publish-design.md)。

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

### DEPLOY-02 现网落地试点

- 状态：`DONE`（2026-08-31）
- 权威仓库：`kids-visual-learning-pack`（入口、Nginx snippet、rsync）；`cognitive-card-server`（从 `knowledge-pipeline-v1` 打 release 与 catalog）。
- 依赖：DEPLOY-01、PORTAL-01、SITE-01、SITE-02、PUBLISH-01、ACCEPT-01。
- 目标：公网 `https://www.yutou.space/card-os/` 提供已发布包画廊；根入口主 CTA 指向该画廊；旧 hash 与 `boards/{slug}/` 不静默 404；一次部署可把主 CTA 回滚到 `parallel`。
- 已完成：release `fd696c2a8cab5400a5d78669031a501390ab5318`（版本号仍 `0.3.1`）在 `127.0.0.1:8765` 同时提供画廊与 health/capabilities；Nginx snippet 已换成仓库 `card-os.conf`；ACCEPT-01 `rabbit` `revision-0001` 为 public current；`scripts/deploy.sh` 已上传根 hub 与 13 个 stub。未 merge server `main`。
- 完成条件：已满足。证据见 [生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md) 第 10 节。
- 非范围：知识源 schema、API-01 自由概念编译、MIG-02/03、默认 merge server `main`、Uvicorn 非 loopback。

### WB-01 令牌操作台只读知识源

- 状态：`DONE`（2026-08-31；现网 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`）
- 权威仓库：`kids-visual-learning-pack`（产品规范、Nginx snippet、任务治理）；实现落在 `cognitive-card-server` `knowledge-pipeline-v1`。
- 依赖：BROWSE-01、PROJ-01、WIRE-01、LIB-01、AUTHOR-02、DEPLOY-02。
- 目标：admin token 操作台浏览知识库 current 与 Projection 选择面；生产兔子 library current 为 AUTHOR-02 章节导读知识源；公开画廊仍是 ACCEPT-01 四卡包。
- 完成条件：已满足。证据见 [生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md) 第 11 节。
- 独立设计：[令牌操作台只读知识源](superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md)。
- 非范围：WB-02 / WB-03 / API-01 实现、浏览器会话、在画廊加操作台链接、merge server `main`。

### KNOW-03 知识源覆盖、准确性与可插拔升级

- 状态：`DONE`（2026-09-01；本机 server `7aaeb2b`；未生产 release）
- 依赖：KNOW-01、AUTHOR-02、WB-01（只读看见现有源）。
- 权威仓库：`cognitive-card-server`（实现）；任务治理为 `kids-visual-learning-pack`。
- 目标：知识源全面性与准确性；每种 `primary_form` 有可插拔 coverage pack；领域 overlay 可插拔；吸收 Skill 的 FACT/分类/事实检查，忽略投影呈现。
- 完成条件：已满足（本机）。主机+内核+全 form pack 文件可加载；§8.1 七主题按所选 pack 过门；几何/时效夹具不被 `defined` 包误杀；格温不上画廊；不实施 WB-02。生产 release 不是本任务门禁。
- 独立设计：[知识源覆盖与准确性](superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md)（Approved/Implemented；本机，非现网）。
- 实施计划：[KNOW-03 实施计划](superpowers/plans/2026-09-01-entity-knowledge-coverage-implementation-plan.md)（经 SDD 执行；server `7aaeb2b` on `knowledge-pipeline-v1`，未 merge `main`、未生产 release；focused 六模块 121 tests OK；全量 discover 631：failures=0 + errors=11（fastapi/httpx，既有））。
- 非范围：生产 library / 画廊 / Nginx；WB-02；search/fetch 编译器；merge server `main`。生产切应用另立 `KNOW-03-prod`。

### KNOW-03-prod 现网装上 KNOW-03 应用

- 状态：`DONE`（2026-09-01；切片 A；现网 `7aaeb2b`）
- 依赖：KNOW-03（本机 `7aaeb2b`）、WB-01（现网 `115377b` 与 ops 路由）。
- 权威仓库：`cognitive-card-server`（release 源提交）；任务治理与运维证据为 `kids-visual-learning-pack`。
- 目标：把 KNOW-03 应用提交装上现网 `current`，使操作台与锁定任务 API 跑 coverage 代码。不把本机七主题库种子进生产。
- 完成条件：已满足。证据见 [生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md) 第 12 节。
- 非范围：重种 `rabbit-real.json`（切片 B，须另授权）；reload Nginx；merge server `main`；push；WB-02。
- 回滚：把 `current` 指回 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`；不删旧 release。

### KNOW-04 兼容套件上库

- 状态：`DONE`（2026-09-01）
- 依赖：KNOW-03-prod（现网应用 `7aaeb2b`）、KNOW-03 本机七主题夹具、WB-01 操作台与 library 根。
- 权威仓库：`cognitive-card-server`（只读编译源提交）；任务治理与运维证据为 `kids-visual-learning-pack`。
- 目标：把兼容套件里允许上库的对象做成生产 knowledge-library current，使操作台列出它们。不换应用、不 reload Nginx、不改画廊。
- 完成条件：已满足。证据见 [生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md) 第 13 节。
- 独立设计：[兼容套件上库](superpowers/specs/2026-09-01-knowledge-suite-library-seed-design.md)。
- 非范围：格温；新 release；Nginx；merge server `main`；WB-02。

### WB-02 四卡成熟视觉投影

- 状态：`DONE`（2026-09-01；本机 server `5c11880`；未生产 release）
- 依赖：KNOW-03、KNOW-04。
- 权威仓库：`cognitive-card-server`（实现）；任务治理为 `kids-visual-learning-pack`。
- 目标：操作台完成确认点 1 的映射半截：选择 Projection family，锁定四卡槽位方案；不把视觉方案写入 Knowledge Core，不输出 PNG/PDF。
- 完成条件：已满足（本机）。证据：server `5c11880` focused unittest PASS；`lock_mapping` 不改 `current.json`。现网应用 / Nginx / 画廊不是本刀门禁。
- 独立设计：[操作台映射方案确认](superpowers/specs/2026-09-01-operator-mapping-scheme-design.md)（Approved）。实施计划：[映射方案实施](superpowers/plans/2026-09-01-operator-mapping-scheme-implementation-plan.md)。旧稿 [四卡文字成熟投影](superpowers/specs/2026-08-31-four-card-text-mature-projection-design.md) 保持 Parked。
- 2026-09-01：操作者批准实施。映射 revision 不抢 knowledge current。未打 release。

### WB-03 选投影→生成→上架画廊

- 状态：`DONE`（2026-09-02 本机；未 commit、未现网）
- 依赖：WB-02。
- 权威仓库：`cognitive-card-server`（实现）；任务治理为 `kids-visual-learning-pack`。
- 目标：操作台按已锁定 mapping revision 生成并发布到 PORTAL-01 catalog；不得把 mapping 包设为 knowledge current；不得静默写 Knowledge Core。
- 完成条件：已满足（本机信息层）。证据：server worktree `convert_mapping` / `pack_from_mapping` / generate+publish / ops 第四块；加权版式后 rabbit-real pack/generate unittest `awaiting_review`；操作者 2026-09-02 看过四卡 PNG/`print.pdf`，接受基础信息。现网应用 / Nginx / 画廊不是本刀门禁。
- 明确未验收：打印样式（区框、留白、字重、标签等）。操作者要求全部阶段完工后，再以最终投影产物反查各阶段调优。不在本刀开样式批次。
- 独立设计：[按映射生成并上架](superpowers/specs/2026-09-01-operator-mapping-artifact-publish-design.md)（Approved）；打印绑定补丁 [加权版式](superpowers/specs/2026-09-02-mapping-artifact-weighted-layout-design.md)（Approved）。实施计划：[映射产物上架](superpowers/plans/2026-09-01-operator-mapping-artifact-publish-implementation-plan.md)、[加权版式](superpowers/plans/2026-09-02-mapping-artifact-weighted-layout-implementation-plan.md)。旧稿 [四卡文字成熟投影](superpowers/specs/2026-08-31-four-card-text-mature-projection-design.md) 保持 Parked；溢出到来源区不采纳。
- 2026-09-02：操作者接受基础信息，标本机 `DONE`。未打 release。

### OPS-01 本机备份与恢复

- 状态：`DONE`（2026-08-30，[ADR-004](decisions/ADR-004-single-operator-main-flow.md) 关闭单人门禁）
- 已完成：根磁盘使用率 55%/inode 21% 的终态基线；SQLite 在线备份、候选摘要、14 天本机保留、唯一规范批次、manifest 校验和隔离恢复演练均通过；Certbot timer 活动。
- 单人完成条件：本机恢复点可验证。不把本机副本描述为完整灾难恢复。
- 操作入口见 [生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md)。

### OPS-02 异地拷贝与告警

- 状态：`BACKLOG`
- 简化设计：不建加密复制服务、不建告警栈。需要时由维护者把已验证的 `/var/backups/cognitive-card-server` 拷到第二块盘或另一台机器，并抽查一次隔离恢复。
- 后期可选：根磁盘早于 75% 的容量/inode/备份新鲜度提醒；证书与 health 失败的可投递告警。
- 完成条件：至少一份与本机备份分离的可恢复拷贝，或明确记录「单人接受仅本机风险」。
- 非范围：不阻塞 BROWSE-01 或知识主路径。

### ACCEPT-01 兔子端到端验收

- 状态：`DONE`（实现与 focused 测试完成；已本地提交 `10b14c8`；未 merge 进 main，未 push）
- 输入：兔子、深圳、`age-5-6`、中英文、打印版（AUTHOR-02 `rabbit-real.json` + Shenzhen four-card request）。
- 依赖：RUN-01、AGE-01、RENDER-01、QA-01、PUBLISH-01。
- 本批结果：确定性 lock assembler + `four_card_accept` 编排从正式输入写到四卡 PNG、A4 PDF、QA `approved`、不可变 `rabbit/revision-0001`。本机 `view/index.html` 与 package / browse 共用同一 `content_lock_sha256`。不扩 PORTAL，不新增公网 HTTP。focused lock+accept 9 项、pipeline 回归 118 项 PASS。证据见 [ACCEPT-01 Evidence](cognitive-card-os-accept-01-evidence.md)。已本地提交 `10b14c8`。
- 单人完成条件（[ADR-004](decisions/ADR-004-single-operator-main-flow.md)）：从正式输入到四卡、PDF、QA、复核和不可变 package 全链路完成；本机可查看同一版本。
- 不作为本任务门禁：公网门户（`PORTAL-01`）、第二终端（`SKILL-03`）。
- 独立设计：[兔子端到端验收](superpowers/specs/2026-08-31-rabbit-end-to-end-acceptance-design.md)。

### ACCEPT-02 第二个哺乳动物一致性验收

- 状态：`BACKLOG`
- 依赖：ACCEPT-01、TMPL-01。
- 对象选择规则：与兔子同为 `life + entity + animal/mammal`，但外观、习性和人与其关系足够不同。
- 完成条件：两者解析为同一模板族和固定骨架；差异只来自事实、可选槽位和图像元素。

## 5. 近期执行顺序

按单人知识主路径 **一次一个会话、一个任务 ID**（[ADR-004](decisions/ADR-004-single-operator-main-flow.md)）。新会话先把该 ID 写入 `CURRENT_TASK.md` 再实现。

已完成（不要再开实现切片）：`BROWSE-01`、`CONV-01`（`e9bfd22`）、`RUN-01`（`c55f51b`）、`AGE-01`（`4e0ea52`）、`RENDER-01`（`1ef6edc`）、`QA-01`（`37a5927`）、`PUBLISH-01`（`7a127b4`）、`ACCEPT-01`（`10b14c8`）、`KNOW-01`（`4083ce7`）、`TMPL-01`（`cbaf2b4`）、`PORTAL-01`（`fd696c2`）、`SITE-01`（现网根 CTA 与 Nginx 画廊反代）、`SITE-02`（`44e0990`；记录 SHA `3432e83`）、`DEPLOY-02`（现网画廊 `fd696c2` 基线）、`WB-01`（现网曾为 `115377b`）、`KNOW-03`（本机 `7aaeb2b`）、`KNOW-03-prod`（现网 `current`=`7aaeb2b`）、`KNOW-04`（生产 library 六主题 current）、`WB-02`（本机 `5c11880`）、`WB-03`（本机 worktree；样式后置）。

下一会话起按此编号：

1. ~~**RUN-01**~~（本机完成）。
2. ~~**AGE-01**~~（本机完成）。
3. ~~**RENDER-01**~~（本机完成，`1ef6edc`）。
4. ~~**QA-01**~~（本机完成，`37a5927`）。
5. ~~**PUBLISH-01**~~（本机完成，`7a127b4`）。
6. ~~**ACCEPT-01**~~（本机完成，`10b14c8`）。
7. ~~**KNOW-01**~~（本机完成，`4083ce7`）。
8. ~~**TMPL-01**~~（本机完成，`cbaf2b4`）。
9. ~~**PORTAL-01**~~（本机完成，`fd696c2`）。
10. ~~**SITE-01**~~（现网完成）。
11. ~~**SITE-02**~~（`44e0990`；现网 stub/hash 已抽查）。
12. ~~**DEPLOY-02**~~（现网完成；应用 `fd696c2`；未 merge server `main`）。
13. ~~**WB-01**~~ 令牌操作台只读知识源（现网完成，`115377b`）。
14. ~~**KNOW-03**~~ 知识源覆盖与准确性（本机完成，`7aaeb2b`）。
15. ~~**KNOW-03-prod**~~ 现网只换应用（`7aaeb2b`；library / Nginx 未改）。
16. ~~**KNOW-04**~~ 兼容套件上库（生产六主题 current；不含格温）。
17. ~~**WB-02**~~ 操作台映射方案确认（本机完成，`5c11880`；不现网）。
18. ~~**WB-03**~~ 选投影 → 生成 → 上架画廊（本机完成；样式后置；未现网）。
19. **API-01** 自由 prompt 编译成知识源（worktree 已实施；试用止于冻结；**不**在本项里加厚模板或生图）。
20. **API-01-TPL** 加厚模板 + 解析层兼容 ChatGPT 自造 schema（worktree 已实施；试用 JSON 可未改写编过；未 commit）。
21. **IMG-01** 图形/打印插画：扩完整生图提示词并收回图（先设计；不与 TPL 混开）。

不把 `knowledge-pipeline-v1` merge 进 server `main`、不 push server 远程，除非用户在**该会话**里明确授权。`DEPLOY-02` 已落地现网，仍不构成对 merge `main` 的授权。

**不要排进上述队列**（后置，另立会话且须再授权）：`SKILL-03`、`OPS-02`、`AUTH-01` 浏览器会话、`MCP-01`、`UPLOAD-01`、`AGE-02`、`ACCEPT-02`、`MIG-02` / `MIG-03`、打印样式调优（等全部阶段完工后，以最终投影产物反查各阶段；不以当前四卡观感开新切片）、API-01 生产安装 / merge `main`、kids+server 提交（须该会话明确要求 commit）。

存档生产核心仍按 ADR-001 留给 RENDER/QA/PUBLISH 抢救，不充当 Knowledge Core 存储层。工作区仍按 [ADR-003](decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md) 三角色。

## 6. 更新记录

### 2026-09-02

- API-01-TPL：server `91b7cf3` 提交加厚模板 + ChatGPT 形态归一；focused compile 27 PASS；库存未改写 ragdoll JSON 可编过。未现网、未 merge `main`。
- API-01-TPL：server worktree 加厚 `knowledge-compile-v1`；`parse_authoring_reply` 归一 ChatGPT 自造 schema。focused `test_knowledge_compile`+`test_http_knowledge_compile` 27 PASS。未改写的 `/tmp/card-os-api01/ragdoll-chatgpt.json` 可 `compile_authoring_request(..., allow_search=True)`。未新开 8765、未 commit、未打 release。
- API-01 本机试用收口：隔离 `/tmp/card-os-api01` 已停（原 8765）。`ragdoll-cat` Confirm current r1。ChatGPT JSON 缺合同键，经人工映射才编过。操作者判定本轮止于知识源冻结。现有 WB-03 是 Pillow 文字四卡，不是会员生图。新增队列 `API-01-TPL`（READY）、`IMG-01`（BACKLOG）。8765 已停。
- API-01：本刀已在 server worktree 实施（提示词模板、compile-intent、reply/`allow_search`、confirm current、admin JSON、ops HTML）。focused unittest 44 PASS（`test_knowledge_compile` 12 + `test_http_knowledge_compile` 8 + `test_http_knowledge_ops` 13 + `test_http_auth` 11）。未 commit、未打 release、未现网。路线图仍 `IN PROGRESS`。
- API-01：操作者批准 ChatGPT 会员复制/粘贴设计。spec Approved；计划 `docs/superpowers/plans/2026-09-02-operator-free-prompt-knowledge-compile-implementation-plan.md`。未实施、未打 release。
- WB-03：本机 `DONE`。操作者看过加权四卡 PNG/`print.pdf`：基础信息可接受；样式问题很大，全部阶段完工后再以最终投影反查各阶段调优。未 commit、未打 release、未现网。
- WB-03：加权版式已在 server worktree 实施（`weighted_layout` + pack/COPY/RENDER 共用区高）。rabbit-real `pack_from_mapping` / `generate_from_mapping` focused unittest 不再 `TEXT_OVERFLOW`；`test_rabbit_real_generate_awaits_review` PASS。未 commit、未打 release。WB-03 仍 `IN PROGRESS`（待操作者接受可见卡）。加权 spec 保持 Approved。
- WB-03：加权版式书面 spec Draft `docs/superpowers/specs/2026-09-02-mapping-artifact-weighted-layout-design.md`。分层纪律写进该 spec（不新开 ADR）。待操作者审查后再写实施计划。未实施、未打 release。

### 2026-09-01

- WB-03：仍 `IN PROGRESS`。server `knowledge-pipeline-v1` worktree 已有 `convert_mapping` / `pack_from_mapping` / generate+publish / ops 第四块（未 commit）；focused 117+6 unittest OK；rabbit-real pack/generate 按规格 `TEXT_OVERFLOW`，§11 未满足。未打 release、未 reload Nginx、未改画廊、未生产安装。
- WB-03：操作者确认 spec。计划 `docs/superpowers/plans/2026-09-01-operator-mapping-artifact-publish-implementation-plan.md`。未实施、未打 release、未 reload Nginx、未改画廊。
- WB-03：书面 spec Draft `docs/superpowers/specs/2026-09-01-operator-mapping-artifact-publish-design.md`。待操作者审查。未实施、未打 release、未 reload Nginx、未改画廊。
- WB-03：立项为 `IN PROGRESS`。本回合只写书面设计；输入预定为 mapping revision 而非 knowledge current。未实施、未打 release、未 reload Nginx、未改画廊。
- WB-02：本机 `DONE`。server `5c1188074846acbf8652ccb888792080697d140e`（`feat(knowledge): lock projection mapping without moving current`）。未打 release、未 reload Nginx、未上画廊。
- WB-02：本机 `DONE`。server worktree 实现 `preview_mapping` / `lock_mapping` / `mapping.json` / 安全登记 / ops 第三块；focused unittest PASS。未 commit、未打 release、未 reload Nginx、未上画廊。
- WB-02：spec 批准并开始实施。计划 `docs/superpowers/plans/2026-09-01-operator-mapping-scheme-implementation-plan.md`。不打 release、不上画廊。
- KNOW-04：`DONE`。生产 library 六主题 current；`rabbit`=`revision-0002`（AUTHOR-02 `0001` 保留）；无格温；应用仍 `7aaeb2b`；Nginx / 画廊未改。证据见运维记录第 13 节。
- KNOW-04：操作者点名「新知识源切片」。把兼容套件六主题（不含格温）写成生产 library current；兔子为 `revision-0002`。不换应用、不 reload Nginx。
- KNOW-03-prod：切片 A `DONE`。现网 `current`=`7aaeb2b`；library AUTHOR-02 哈希未变；Nginx snippet 未 reload。未 merge `main`、未 push。证据见运维记录第 12 节。
- KNOW-03-prod：操作者点名并选择切片 A（只换应用 `7aaeb2b`）。不重种 library、不 reload Nginx、不实施 WB-02。
- KNOW-03：操作者接受本机完成条件，标 `DONE`。不等于现网已装 `7aaeb2b`。下一编号 WB-02 仍搁置。
- KNOW-03：server 已提交 `7aaeb2b80e591f348c54eb35fb18793e213c5122`（`knowledge-pipeline-v1`，未 merge `main`）。focused 六模块 121 tests OK；全量 discover 631：failures=0、errors=11（fastapi/httpx，既有）。未生产 release、未 reload、未种子新 library。格温仅 `examples/authoring/`。
- KNOW-03：spec 已批准；实施计划经 SDD 执行（server Task 1.1–3.3 + Task 4.2）；rabbit-real 重切已修复。操作者 2026-09-01 授权 commit。
- WB-02：四卡文字成熟投影 spec 被判定偏离知识源目标，改为 `BACKLOG` / Parked，不实施。

### 2026-08-31

- WB-02：四卡文字成熟投影书面 spec `docs/superpowers/specs/2026-08-31-four-card-text-mature-projection-design.md`。本刀文字-only、本机验收；插图与上架属 WB-03。待用户审查书面 spec 后再写实施计划。
- WB-01：令牌操作台只读知识源 `DONE`。release `115377b` 已安装；knowledge-library `rabbit` 为 AUTHOR-02（4/8/4，chosen `chaptered-guide`）；Nginx `/card-os/ops/` 已 reload；画廊 `package_sha256` 未变。未 merge server `main`。证据见运维记录第 11 节。
- WB-01：令牌操作台只读知识源仍 `IN PROGRESS`。server `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd` 已提交 `knowledge_ops`；kids Nginx `/card-os/ops/` 已入库。未种子生产 knowledge-library；未 reload 生产 Nginx。
- WB-01：令牌操作台只读知识源立项为 `IN PROGRESS`。独立设计 `docs/superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md`。公网画廊保持 PORTAL-01。新增队列 WB-01 → WB-02 → WB-03 → API-01；API-01 自由编译从「不要排进队列」移入第 16 项。未开始 server 实现。
- DEPLOY-02：现网落地试点 `DONE`。release `fd696c2`（ops `3432e83`）已安装；`/card-os/` 为画廊；兔子 `public` current 已上架；根 CTA 与 13 个 stub 已 rsync。未 merge server `main`。证据见运维记录第 10 节。
- DEPLOY-02：现网落地试点立项为 `IN PROGRESS`。SITE-02 已提交 `44e0990`。来源字段不扩展。顺序为从 `knowledge-pipeline-v1` 打 release（默认不 merge `main`）、回环证明画廊与 health/capabilities 并存、reload Nginx、至少一个公开包、再 rsync 根入口与 stub。范围见 `docs/ai/CURRENT_TASK.md`。
- SITE-02：旧 `kids-world` hash/query 打开冻结主题；`boards/{slug}/index.html` 为替代说明页；根 hub 由 `activeMode` 生成，切到 `parallel` 可一次部署回滚主 CTA。独立设计 `docs/superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md`。未现网。
- SITE-01：Card OS 替换 kids-world 知识入口。根入口主 CTA 指向画廊；旧站冻结并行可达；Nginx snippet 反代 `/card-os/` 与 `/card-os/packages/`。13 个 C 级主题按 [ADR-005](decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md) 冻结，不等 MIG-03。独立设计 `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`。未现网应用。SITE-02 只做旧 URL 映射与回滚开关。
- PORTAL-01：已发布 Artifact 只读画廊。CLI 静态 HTML + loopback `/card-os/`；公开观众只看 public current；owner-only / 撤回 / 草稿 404。不替代 BROWSE-01，不写 Knowledge Core / Projection family。独立设计 `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`。focused portal 10 项、pipeline 回归 145 项 PASS。已本地提交 `fd696c2`。未 add `uv.lock`；未 merge `main`；未 push；未现网。
- TMPL-01：`template-registry-v1` 把精确 mammal/dinosaur 与紧凑 domain/form 族迁入服务器；相同主路由稳定骨架；缺口 `TEMPLATE_GAP`；每 family 两个对象夹具。独立设计 `docs/superpowers/specs/2026-08-31-template-family-registry-design.md`。focused template 10 项、pipeline 回归 136 项 PASS。已本地提交 `cbaf2b4`。未改 snapshot 字节。未 add `uv.lock`；未 merge `main`；未 push；未现网。
- KNOW-01：`classification-registry-v1` 覆盖矩阵与领域 subtype 词表迁入服务器；authoring 必填受控分类；convert/accept 可省略 `--request`。独立设计 `docs/superpowers/specs/2026-08-31-classification-registry-design.md`。focused classification + authoring/converter/accept 与 pipeline 回归 143 项 PASS；合同校验 141 项 PASS。已本地提交 `4083ce7`。未 add `uv.lock`；未 merge `main`；未 push；未现网。
- ACCEPT-01：AUTHOR-02 真实兔子 + Shenzhen age-5-6 打印请求本机跑通四卡/PDF/QA/不可变 package。确定性 lock 不经 LLM。本机 `view/index.html` 与 package 同一 `content_lock_sha256`。focused lock+accept 9 项、pipeline 回归 118 项 PASS。证据 `docs/cognitive-card-os-accept-01-evidence.md`。已本地提交 `10b14c8`；未 add `uv.lock`；未 merge `main`；未 push；未现网。
- PUBLISH-01：服务器 `four_card_publish` 把 QA-01 `approved` 四卡写成不可变 package revision；撤回/替代只改 current pointer。独立设计 `docs/superpowers/specs/2026-08-31-immutable-package-publish-design.md`。focused publish 12 项 PASS；pipeline 回归 109 项 PASS。已本地提交 `7a127b4`；未 add `uv.lock`；未 merge `main`；未 push；未现网。
- QA-01：服务器 `four_card_qa` 对 RENDER-01 产物做机器门禁；通过后才 `awaiting_review`；人工 `approve`/`reject` 绑定 actor 与 `audit.jsonl`。独立设计 `docs/superpowers/specs/2026-08-31-strict-qa-human-review-design.md`。focused QA 12 项 PASS。已本地提交 `37a5927`；未 add `uv.lock`；未 merge `main`；未 push；未现网。
- RENDER-01：服务器 `four_card_render` 按内容锁与 AGE-01 `copy_plan` 排出四页 A4 PNG/PDF；generate COPY 不进字形。独立设计 `docs/superpowers/specs/2026-08-31-locked-four-card-render-design.md`。focused renderer 11 项、pipeline+renderer 85 项 PASS；完整 suite 572 中 2 项既有 real-uvicorn 502。已本地提交 `1ef6edc`；未 add `uv.lock`；未 merge `main`；未 push；未现网。
- AGE-01：`age-language-adapter-v1` 把 3–4 / 5–6 儿童中文与 beginner 英文做成服务器适配；命题 id、确定性、安全原文跨年龄不变。converter 密封前替换 CONV-01 临时 cn=en。独立设计 `docs/superpowers/specs/2026-08-31-age-language-adapter-design.md`。focused 适配器+converter `27` 项、pipeline 回归 `83` 项 PASS；完整 suite `561` 中 2 项既有 real-uvicorn 502。已本地提交 `4e0ea52`；未 add `uv.lock`；未 merge `main`；未 push；未现网。
- RUN-01：显式 four-card 兔子 current 本机 loopback 跑通 convert → 入库 → prepare → validator 退出 0 → `candidate_staged`。默认 `chaptered-guide` 先被拒绝。executor / `job_id_for` 接接合信封。focused pipeline+converter+library 等 83 项 PASS；完整 suite 544 项中 2 项既有 real-uvicorn 502。已本地提交 `c55f51b`；未 add `uv.lock`；未 merge `main`；未 push；未现网。
- 按 ADR-004 把 CONV-01 之后的剩余工作排成一次一会话队列。新增 `RUN-01`（现为 `DONE`）为当时下一刀；§5 编号 1–10。KNOW-01 / TMPL-01 / AGE-01 仍为 IN PROGRESS，但顺序上不挡 RUN-01。自由概念编译、第二终端、异地备份、浏览器会话不进入该队列。

### 2026-08-30

- CONV-01：显式 four-card current → 接合 generation-input。独立设计 `docs/superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md`。CLI `convert` 映射 `source_id` 点号；默认 chaptered-guide 拒绝。`knowledge-pipeline-v1` focused `248` 项 PASS。已与 BROWSE-01 一并本地提交 `e9bfd22`；kids 治理 `a85a785`。未 add `uv.lock`；server `main` 仍 `c2a898c`；未 push、未现网。
- BROWSE-01：确认点 1 静态 HTML + 只读 GET。CLI `browse` 写出列表与 revision 页；兔子/几何选择面与 unlist 历史浏览已由 focused 测试覆盖。`knowledge-pipeline-v1` focused `241` 项 PASS。未 add `uv.lock`；server `main` 仍 `c2a898c`；未 push、未现网。
- [ADR-004](decisions/ADR-004-single-operator-main-flow.md) 接受：单人维护、单人使用，主流程优先。新增 `BROWSE-01`（现为 `DONE`）与独立设计 `docs/superpowers/specs/2026-08-30-knowledge-browse-projection-confirmation-design.md`；`CONV-01` 现为 `DONE`。`SKILL-02` 单人门禁 `DONE`，第二台电脑改 `SKILL-03`。`OPS-01` 本机恢复点 `DONE`，加密异地与告警改 `OPS-02`（简化为可选手工拷贝，不设计加密复制服务）。PORTAL-01 明确不替代确认点 1。
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
