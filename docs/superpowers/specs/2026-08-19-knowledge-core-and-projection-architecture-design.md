# Cognitive Card OS Knowledge Core 与多 Projection 架构设计

- Status: Approved
- Date: 2026-08-19
- Owners: 项目所有者、OpenAI Codex
- Related Decision: `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- Scope: 长期知识模型、学习设计、Projection、版本时效、本地与服务器边界及 MVP 验证

## 1. 目标与边界

本设计把 Cognitive Card OS 从“四卡生产系统”扩展为“知识核心生产与长期管理系统”。本地工作流负责形成可验证的知识候选和产物包，个人服务器负责保存、浏览、检索、复核、发布、版本历史和长期更新。四卡、打印页、网页、交互探索和其他表现形式均由同一 Knowledge Core 派生。

本设计解决五个问题：

1. 如何让事实和来源独立于具体页面与交互形式；
2. 如何表达单一主题、复合主题和逐步深入主题；
3. 如何在知识与产物之间区分学习计划、学习路径和 Projection；
4. 如何管理会过期、需周期复核或由事件触发更新的知识；
5. 如何保留完整架构，又不让日常使用变成八层填表流程。

本设计不定义 JSON Schema、数据库表、HTTP API、具体 UI、Renderer 实现和生产迁移脚本。它也不授权更新现网、执行历史资产迁移或启动 API-01 后续批次。

## 2. 术语与边界

**Knowledge Core**：由 Evidence / Source、Proposition Graph 和 Knowledge Scope 构成的可追溯知识集合；不包含特定受众的教学顺序或页面布局。
_Avoid_: 把四卡文本、PDF 或页面模板称为 Knowledge Core。

**Evidence / Source**：支持、限定或反驳某个命题的来源记录和证据片段。

**Proposition**：具有稳定 ID、确定性、来源和时效属性的最小可治理知识主张。

**Proposition Graph**：命题及其支持、限定、冲突、组成、比较和先修关系的逻辑集合；MVP 不要求图数据库。

**Knowledge Scope**：一次知识产品选择哪些命题、知识单元和组合关系，以及明确排除哪些内容的边界声明。

**Knowledge Unit**：围绕一个可独立理解的小问题组织的一组命题引用；同一命题可被多个知识单元复用。

**Learning Plan**：针对目标人群、语言、深度、时长、学习目标和使用场景的教学约束。

**Learning Path**：在一个 Learning Plan 下，知识单元的选择、顺序、分支、示例和先修结构。

**Projection Blueprint**：平台中立的呈现意图和内容槽位；只选择和组织已有知识，不新增事实。

**Renderer Binding**：把 Blueprint 槽位映射到具体平台、媒介和能力的规则。

**Artifact Package**：由确定版本的 Knowledge Core、Learning Spec 和 Projection Spec 生成的文件集合及其 manifest。

**Revision**：不可原地修改的对象版本；修改产生新 revision，并通过 `supersedes` 或 current pointer 建立关系。

## 3. 设计原则

### 3.1 知识优先，产物后置

事实、来源、确定性、未知项和安全边界先进入 Knowledge Core。Learning Plan、Learning Path、Projection 和 Renderer 只能引用或省略命题，不能增加事实。需要增加事实时，必须回到 Knowledge Core 创建新 revision。

### 3.2 逻辑分层不等于用户步骤

八层用于划分责任、验证和版本影响，不要求八个用户表单、八个文件、八个数据库表或八个服务。标准流程由系统自动推导中间层，并把相关决策合并为一次方案确认。

### 3.3 版本不可变，更新显式

任何已验证或已发布对象都不原地覆盖。新来源、新事实、时效复核、学习路径调整和布局调整分别产生适当层级的新 revision。服务器 current pointer 只指向经过门禁的 revision。

### 3.4 阶段越靠后，门禁越严格

draft 的价值是捕捉思路，允许不完整；candidate 的价值是可审查，必须结构闭合；published 的价值是可长期信任，必须通过来源、时效、引用、摘要和发布门禁。

### 3.5 默认自动化，异常显式化

系统为普通主题建议 Scope、Plan、Path 和 Projection。只有实质歧义、来源冲突、高风险、关键时效或不可逆发布取舍才增加人工复核。自动化不能静默猜测互相排斥的事实路线。

### 3.6 四卡是兼容能力，不是知识模型

现有中英文观察卡与知识卡继续作为 `four-card` Projection family。它仍适合一部分儿童打印场景，但主题是否使用四卡由知识结构与学习目标决定。

## 4. 八个逻辑层

| 层 | 主要职责 | 主要输入 | 主要输出 | 禁止承担 |
| --- | --- | --- | --- | --- |
| 1. Evidence / Source | 保存来源、证据、出处和证据质量 | 原始资料、人工记录 | source records、evidence spans | 教学排序、页面布局 |
| 2. Proposition Graph | 形成稳定命题与逻辑关系 | evidence spans | propositions、relations、certainty | 受众语言、卡片文案 |
| 3. Knowledge Scope | 选定单一、复合或渐进知识边界 | propositions、knowledge units | included/excluded scope、composition | 教学时长、平台布局 |
| 4. Learning Plan | 定义谁学、为何学、学多深、学多久 | scope、用户目标 | audience、language、depth、duration、goals | 事实新增、像素布局 |
| 5. Learning Path | 组织内容结构和学习顺序 | scope、plan | nodes、edges、strategy、prerequisites | 自由改写事实 |
| 6. Projection Blueprint | 定义呈现语义和槽位 | path、场景约束 | blueprint family、content slots | 平台私有实现、事实新增 |
| 7. Renderer Binding | 绑定平台能力与降级规则 | blueprint、renderer capabilities | renderer mapping、asset needs | 修改学习目标或事实 |
| 8. Artifact Package | 组装、校验和交付产物 | 以上精确 revisions | files、manifest、QA、state | 反向覆盖上游 revision |

### 4.1 Knowledge Core 的边界

第 1–3 层共同构成 Knowledge Core。Knowledge Scope 被纳入核心，是因为同一命题库可以被不同主题组合使用，而“本次究竟在讲什么”必须在进入教学设计前固定。受众、语言、深度和时长从第 4 层开始，不能回写事实层。

### 4.2 层间引用

下游对象必须引用上游精确 revision 和稳定 ID：

```text
source_id
  -> proposition_id
  -> knowledge_unit_id / scope_revision
  -> learning_plan_revision
  -> learning_path_revision
  -> projection_revision
  -> renderer_binding_revision
  -> artifact_manifest_digest
```

引用链可以打包在四个物理对象中，但验证器必须能重建它。任何断链都只能保存为 draft，不能成为 published current。

## 5. Knowledge Core 模型

### 5.1 Evidence / Source

来源记录至少能够表达：

- 稳定 `source_id`；
- 来源类型、标题、作者或机构、定位信息和获取时间；
- 支持的命题及证据片段或定位；
- 来源质量、许可或使用边界；
- 来源本身的发布日期、版本或有效期；
- 支持、限定、反驳或仅提供背景的关系。

来源记录不复制不必要的完整外部内容。不能长期保存的来源至少保留可复核定位和摘要；无法复核的主张不能伪装成已验证事实。

### 5.2 Proposition

每个命题至少具有：

- `proposition_id` 与不可变 revision identity；
- 规范语义，不绑定某种语言的最终展示句；
- certainty、unknowns、confusion boundary 和 safety scope；
- supporting / limiting / conflicting source references；
- temporal policy 和当前 freshness；
- 与其他命题的显式关系。

CN、EN 或其他语言可以拆分、合并和简化句子，但必须回指相同命题集合并保持确定性与边界一致。

### 5.3 Proposition relations

MVP 只需要受控关系集合，不建设通用知识图谱：

- `supports`：证据或命题支持另一命题；
- `limits`：限定适用条件；
- `conflicts_with`：存在未解决冲突；
- `part_of`：组成更大知识单元；
- `compares_with`：适合并列比较；
- `prerequisite_of`：理解先后关系；
- `supersedes`：新 revision 替代旧 revision。

关系集合未来可以版本化扩展，但 Renderer 不得自定义事实关系。

### 5.4 Knowledge Unit

Knowledge Unit 是命题引用的可复用聚合，不复制命题正文。一个单元回答一个相对独立的问题，例如“兔子的外观特征”“兔子的基本解剖”或“照顾家兔的基本条件”。单元可以设置推荐深度、适用年龄提示和风险提示，但这些提示不代替 Learning Plan。

### 5.5 Knowledge Scope 类型

首版支持三种 Scope：

1. `single`：围绕一个核心知识单元组织，可附少量背景或例证；
2. `composite`：由多个知识单元组合成一个复合主题，组件可并列、包含、比较或共享命题；
3. `progressive`：由多个深度阶段或先修单元组成，允许从基础概念逐步进入更抽象层次。

复合与渐进不是互斥的底层存储类型。一个复杂主题可以在 Scope 中声明 `composite`，并由 Learning Path 选择其中一条渐进路线；MVP 不为所有组合建立新的类型枚举。

### 5.6 范围闭合

Scope 必须明确：

- included knowledge units 和 propositions；
- explicitly excluded questions；
- 组件关系与范围层级；
- unresolved gaps；
- 对关键安全或时效命题的处理。

“主题名称相同”不代表 Scope 相同。任何下游产物都绑定具体 scope revision。

## 6. 时效、寿命与更新

### 6.1 Temporal policy

命题使用四种时效策略：

- `timeless`：在可预见范围内不依赖日期，仍可因发现错误而修订；
- `slow-changing`：变化缓慢，由较长周期复核；
- `periodic`：按明确周期复核，例如规则、统计、开放信息；
- `event-driven`：由外部事件触发复核，同时可以设置最长复核间隔作为兜底。

Scope 可以提供默认策略，但命题级策略优先。关键命题不能仅因所在主题看似稳定而继承宽松策略。

### 6.2 Temporal fields

时效记录至少支持：

- `reviewed_at`；
- `review_interval`；
- `next_review_at`；
- `valid_from`；
- `valid_until`；
- `expiry_behavior`；
- 触发复核的事件类型或来源提示。

这些字段允许为空的条件由 temporal policy 决定，而不是所有命题都强制填写全部日期。

### 6.3 状态轴

状态分为四个正交轴，避免一个枚举同时表达全部含义：

| 状态轴 | 值 | 含义 |
| --- | --- | --- |
| lifecycle | `draft`、`candidate`、`validated`、`published`、`withdrawn` | 对象所处治理阶段 |
| freshness | `fresh`、`review_due`、`stale`、`expired` | 时间新鲜度 |
| proposition standing | `active`、`disputed`、`superseded` | 命题是否仍被当前知识接受 |
| downstream health | `healthy`、`degraded`、`broken` | 下游 Plan、Path、Projection 是否仍满足引用与能力 |

例如，一个已发布 Artifact 可以同时是 `published + stale + active + degraded`。它不会因为单一状态枚举而丢失语义。

### 6.4 复核与更新行为

- `review_due` 默认产生非阻断提醒；关键策略可以在发布新 revision 时升级为阻断。
- `expired` 按 `expiry_behavior` 执行警告、阻止新发布或从 current 列表下架；历史 revision 和审计关系保留。
- 过期只触发来源检查和更新候选，不能自动把抓取到的新内容替换为权威事实。
- 更新完成后创建新 proposition 或 scope revision，并通过 `supersedes` 建立关系；旧 revision 不覆盖、不删除。
- 影响分析标记依赖旧命题的 Learning Path 和 Artifact 为 `degraded` 或 `broken`，但不自动重新发布。

## 7. Learning Plan

Learning Plan 回答“为谁、为什么、学到什么程度、在什么条件下学”，至少包含：

- 目标人群与年龄/能力 profile；
- 输出语言和语言难度；
- 学习深度；
- 预计时长；
- 学习目标与成功表现；
- 使用场景，如亲子共读、独立探索、课堂讲解、打印复习；
- 可访问性、设备、打印和联网约束；
- 必须覆盖与允许省略的 Scope 内容。

系统可以根据主题和常用偏好生成默认 Plan。用户在第一次合并确认中看到关键取舍，不需要逐字段填写。互相矛盾的要求，例如“5 分钟内覆盖全部多层内容并达到深入推导”，必须显式提示调整，不能静默截断。

## 8. Learning Path

### 8.1 Path contract

Learning Path 是带版本的节点与边集合。每个内容节点引用 knowledge unit 或 proposition；示例、提问、练习等教学节点必须声明其依据和目的。Path 可以组织事实，但不能自创事实。

### 8.2 支持策略

首版允许以下策略作为建议标签，而不是为每种策略创建独立系统：

- `flat`：并列浏览；
- `hierarchical`：总分层级；
- `progressive`：由基础到深入；
- `example-first`：先例证后概念；
- `concept-first`：先概念后例证；
- `compare`：对照差异；
- `inquiry`：问题驱动；
- `spiral`：多轮回访并增加深度；
- `mixed`：明确组合以上策略。

系统根据 Scope、Plan、内容密度和先修关系提出一个主候选；用户可以修改或选择替代候选。正式发布前 Path 必须可重放、可验证，不能只存在于一次模型对话中。

### 8.3 Path validation

- 所有知识节点必须引用当前 Scope；
- `prerequisite_of` 不得形成循环；
- 必须覆盖 Plan 声明的学习目标；
- 不得静默丢弃 required content；
- 预计时长明显不匹配时给出调整建议；
- 示例和练习不得引入未追踪事实。

## 9. Projection 与 Renderer

### 9.1 Projection Blueprint

Blueprint 描述学习内容如何被体验，例如：

- 四卡观察/知识包；
- 单页或多页打印讲义；
- 复合主题章节；
- 渐进式课程或探索路线；
- 比较表、时间线、过程图；
- 网页交互探索；
- 家长引导版与儿童自主版。

Blueprint 尽量平台中立，并声明内容槽、顺序约束、交互语义、可选区和必须保留的命题引用。同一 Blueprint 可以有多个 Renderer Binding。

如果不同平台只是在布局、交互能力或分页上不同，应共享 Blueprint；只有学习结构本身发生实质变化时，才创建新的 Blueprint revision。

### 9.2 Renderer Binding

Renderer Binding 声明：

- 目标媒介、尺寸、平台和能力版本；
- Blueprint 槽位到组件、页面或文件的映射；
- 字体、图像、音频、动画和交互资产要求；
- 不支持能力的显式降级方式；
- 需要的 QA profile。

Renderer 缺少可选能力可以生成 `degraded` candidate，但不能静默删除 required content。无法绑定关键内容时必须阻止发布。

### 9.3 Projection 选择

Planner 根据 Learning Path、内容密度、目标人群、时长、使用场景、打印需求、可访问性和设备能力给出建议。默认只展示推荐方案和关键理由；其他方案作为可选项，不要求用户先理解所有 Projection family。

四卡适用于事实密度适中、观察与知识可以清晰分工、需要双语打印练习的主题。它不适合承载所有复合主题、长链推导或大量可交互内容。

## 10. 四类物理对象

八层逻辑在 MVP 中打包为四类持久化对象：

| 物理对象 | 包含逻辑层 | 责任 |
| --- | --- | --- |
| `knowledge-core` | 1–3 | sources、propositions、relations、knowledge units、scope、temporal policy |
| `learning-spec` | 4–5 | plan、path、goals、nodes、edges、覆盖与时长判断 |
| `projection-spec` | 6–7 | blueprint、renderer binding、capability 与降级声明 |
| `manifest` | 8 | 精确上游 revisions、文件、摘要、QA、状态和发布身份 |

四类对象是 MVP 的打包边界，不是永久数据库边界。未来只有在真实规模或并发证明需要时才拆分；拆分不能改变逻辑身份和引用语义。

Artifact Package 中的图片、HTML、PDF、JSON 或音频不是第五种治理对象，它们是 manifest 声明并按摘要绑定的 files/assets。

## 11. 生成与确认流程

### 11.1 标准流程

```text
用户提交主题与用途
-> 本地捕捉来源和初始知识意图
-> 构建或复用 Knowledge Core
-> 自动提出 Scope + Learning Plan + Learning Path + Projection 候选
-> 显式确认 1：合并方案确认
-> 生成 candidate Artifact Package
-> 分层验证与必要修正
-> 显式确认 2：发布确认
-> 服务器保存不可变 revision 并更新 current pointer
```

用户最初提交主题不是额外确认点。普通主题从提交到发布最多两个显式确认点。若出现实质冲突、高风险安全内容、关键时效策略或不可逆发布选择，可以增加专项复核；系统必须说明触发条件和所需决定。

### 11.2 Draft

Draft 可以缺来源、缺完整 Scope 或缺 Projection；它只用于本地捕捉和继续编辑，不应上传为服务器候选。Draft 验证以提示和自动补全为主。

### 11.3 Candidate

Candidate 必须具有四类对象、完整引用、显式 unresolved items 和可复算摘要。服务器可以保存通过结构闭包验证的 private candidate，但不能把未解决关键问题的 candidate 提升为 published。

### 11.4 Published

Published revision 必须通过严格门禁、记录复核 actor 和决策，并以不可变 identity 保存。修改产生新 revision，current pointer 的变化单独审计。

## 12. 验证与错误处理

### 12.1 分层验证

| 层 | 代表性验证 |
| --- | --- |
| Evidence | 来源可定位、证据关系存在、许可和质量边界可解释 |
| Proposition | ID 稳定、确定性一致、冲突与未知项显式、时效策略有效 |
| Scope | included/excluded 闭合、组件引用存在、关键 gap 显式 |
| Learning Plan | 目标、深度、时长和受众不自相矛盾 |
| Learning Path | 节点均在 Scope 内、无先修环、required content 不丢失 |
| Projection | 所有展示事实有命题引用，不新增事实，不静默改变确定性 |
| Renderer | required slots 可绑定，降级被声明，资产需求可满足 |
| Artifact | 文件均被声明、摘要闭合、上游 revision 精确、QA 与状态一致 |

### 12.2 发布硬阻断

以下问题不能通过通用跳过按钮绕过：

- 关键命题没有来源或来源不可复核；
- 关键时效命题已过期且策略要求阻断；
- 未解决事实冲突会改变学习结论；
- Learning Path 存在先修环或无法满足 Plan；
- Projection 新增 Knowledge Core 外的事实或改变确定性；
- required content 无 Renderer 绑定或被静默删除；
- manifest 摘要不闭合、包含未声明文件或引用错误 revision。

### 12.3 非阻断警告

以下情况可在记录理由后接受：

- 普通命题进入 `review_due` 但尚未 `expired`；
- 可选 Renderer 不可用；
- 已声明且不影响关键学习目标的能力降级；
- 预计时长轻微偏差；
- 非关键来源质量低于推荐等级，但有更高质量来源支撑核心主张。

警告集中显示，不在生成过程反复打断。任何经常被无操作接受的警告都应在试跑后删除、降级为信息或改进默认值。

## 13. 本地与服务器职责

### 13.1 本地工作流

本地负责：

- 捕捉主题、用途和来源；
- 构建或修订 Knowledge Core；
- 生成 Scope、Plan、Path 和 Projection 候选；
- 执行无需服务器状态的确定性验证；
- 保存不完整 draft；
- 输出通过闭包验证的 candidate package。

当前可以由登录 ChatGPT Pro 的客户端执行生成；未来服务器模型 API 执行器必须消费相同的上游对象和输出合同，不能形成第二套知识模型。

### 13.2 个人服务器

服务器负责：

- 验证并保存闭包完整的 private candidate；
- 管理不可变 revisions、current pointer 和 supersedes 关系；
- 建立搜索、浏览、权限和历史记录；
- 运行发布级验证、人工复核和审计；
- 管理 freshness、复核队列和 downstream health；
- 发布和撤回 Artifact Package；
- 长期备份、恢复和容量治理。

不完整 draft 默认不上传服务器。服务器不能信任客户端自报的摘要、状态或 authority，必须复算其能够权威验证的闭包。

### 13.3 锁与权威

保留现行两级锁：

- generation input lock 固定执行器收到的上游输入；
- final content lock 固定最终 Knowledge Core 引用、学习设计、Projection 内容、来源、未知项、安全边界和资产要求。

Artifact manifest 绑定 final content lock、四类对象 revision 和所有产物摘要。扩大 Projection 类型不改变服务器权威和凭据隔离原则。

## 14. 现有四卡兼容映射

现行四卡包可以映射为：

| 现有概念 | 新模型 |
| --- | --- |
| FACT、SEMANTIC CORE、sources、proposition IDs | `knowledge-core` 的 Evidence 与 Proposition Graph |
| classification、object、覆盖边界 | Knowledge Scope |
| age、language、use location、learning axes | Learning Plan |
| 观察任务、知识顺序、COPY 关系 | Learning Path |
| 固定 CN OBS / EN OBS / CN KNOW / EN KNOW | `four-card` Projection Blueprint |
| family style、print/text-faithful/high-visual | Renderer Binding |
| production record、CONTENT LOCK、package manifest、QA | Artifact Package manifest |

兼容层必须保持四页顺序、共享命题、双语事实一致、COPY 来源和现有内容锁语义。历史包不因新架构自动升级；只有在迁移任务中通过映射和验证后才成为新模型 revision。

## 15. MVP 纵向样例

### 15.1 兔子复合主题

Scope 由外观、基本分类与种类、解剖、行为/生活条件和饲养注意等 Knowledge Units 组成。验证重点：多个单元共享命题、不强制压缩为四页、可以为亲子共读与打印摘要生成不同 Projection。

### 15.2 几何逐步深入主题

Scope 覆盖平面几何、立体几何和多维空间概念，Learning Path 使用显式先修关系和不同深度阶段。验证重点：渐进路线、年龄与深度适配、抽象概念的例证顺序，以及较浅 Plan 不必复制完整高级内容。

### 15.3 时效知识主题

使用“某公共场馆的开放时间与票务规则”作为合成 fixture，不声称任何现实场馆的当前事实。验证重点：`periodic` / `event-driven` policy、`review_due`、`expired`、阻止新发布、创建新 revision 和下游 degraded 标记。

三个样例只验证合同和工作流，不要求首阶段建设完整 Portal、调度器、多 Renderer 或生产内容库。

## 16. 复杂度预算与收缩条件

### 16.1 硬预算

- 普通主题最多两个显式确认点；
- MVP 只有四类持久化对象；
- 不要求图数据库、消息队列、通用规则引擎或独立调度服务；
- 首阶段只实现一个成熟兼容 Projection 和验证样例所需的最小额外 Projection；
- 逻辑层可以是同一对象内的命名区段，不为层级纯度提前拆服务。

### 16.2 观测指标

对三个样例记录：

- 从主题输入到 candidate 的人工结构选择次数；
- 不包含知识研究与产物制作的治理额外耗时；
- 系统建议被用户改写的字段和原因；
- 每条 warning 的实际处理；
- 每个 required field 是否被验证、路由、检索或更新流程真实消费；
- 新 Projection 是否迫使 Knowledge Core schema 改动。

### 16.3 收缩条件

出现以下任一情况，下一轮先简化而不是继续扩展：

- 普通样例需要超过两个显式确认点；
- 单个标准主题的治理额外耗时超过约 5 分钟；
- 同一系统建议在至少两个样例中都被手工改写，说明默认推导不可靠；
- required field 在三个样例中均无验证或消费用途；
- 同类 warning 在所有适用样例中都被无操作接受；
- 新增 Projection 需要改变 Knowledge Core 的事实 schema；
- 为通过样例必须先建设与样例无关的通用基础设施。

收缩方式按顺序为：改进默认值、合并字段、降为可选、改为内部派生、推迟独立持久化、删除未产生价值的抽象。

## 17. 验收标准

书面设计阶段通过条件：

- ADR 与本 Spec 对 Knowledge Core、八层、四对象、门禁和兼容关系表达一致；
- 不存在占位项、互相矛盾的状态或隐藏实现授权；
- 与 ADR-001 的服务器权威和薄客户端边界不冲突；
- 与 API-01 的 executor-neutral 合同、generation input lock 和 final content lock 可组合；
- 明确现行四卡规范在书面复核前继续有效；
- 用户书面复核后才进入系统总设计/路线图更新和实施计划阶段。

未来 MVP 实现通过条件：

- 三个样例均有完整四对象引用链和可复算 manifest；
- 复合、渐进和时效行为分别得到验证；
- 普通流程不超过两个确认点；
- Projection 不新增事实；
- 现行四卡包可以通过兼容映射生成，不损失已治理语义；
- 复杂度指标未触发未处理的收缩条件。

## 18. 后续分解门禁

用户书面批准本 Spec 后，后续工作仍分批授权：

1. 规范收敛批次：更新系统总设计、路线图和现行四卡定位；
2. 合同试验批次：为四类对象和三个样例定义最小 fixture，不改服务器；
3. 本地 MVP 批次：实现自动推导、两次确认和本地验证；
4. 兼容批次：把现行 four-card production record 映射为 Projection；
5. 服务器管理批次：经独立设计后增加 revision、current、freshness 和 candidate 管理；
6. Portal 与更多 Projection：仅在前三个样例证明实际价值后立项。

每一批都必须单独更新 `docs/ai/CURRENT_TASK.md`。本 Spec 的书面批准不自动授权代码、服务器、部署、发布或历史资产迁移。

## 19. References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`
- `skills/cognitive-card-os/SKILL.md`
