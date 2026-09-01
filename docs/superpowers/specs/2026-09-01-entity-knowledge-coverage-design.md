# 知识源覆盖、准确性与可插拔升级（KNOW-03）

- Status: Approved/Implemented
- Date: 2026-09-01
- Related: [ADR-001](../../decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[KNOW-01](2026-08-31-classification-registry-design.md)、[KNOW-02 / 四对象合同](../../cognitive-card-os-roadmap.md)、[TMPL-01](2026-08-31-template-family-registry-design.md)、[AUTHOR-02](../../cognitive-card-os-roadmap.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`
- Supersedes: 同日初稿「只启用 entity 七面」；本文件改为完整知识源设计。四卡投影仍见已搁置的 [WB-02](2026-08-31-four-card-text-mature-projection-design.md)。

## 1. 目标

**名词（避免和「可学习对象」混用）**

| 说法 | 指什么 | 不是什么 |
| --- | --- | --- |
| **四对象** | 一次 revision 落盘的四份合同文件：`knowledge-core`、`learning-spec`、`projection-spec`、`manifest`（[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md) 第 4 条；[KNOW-02](../../cognitive-card-os-roadmap.md)） | 不是兔子、故宫这类主题；不是四张卡 |
| **可学习对象 / 知识对象** | 分类指向的那一个主题（兔子、鹅掌藤、霸王龙…） | 不是四对象文件 |
| **四卡** | `four-card` Projection 的四页产物 | 本刀不做 |

「不改四对象顶层文件名」= 仍只持久化上述四份 JSON，不把 coverage 注册表做成第五个文件。知识对象**内部**字段由 `record-shape` 升级。

本环节只做知识源，不做投影：

1. **全面性**：一类可学习对象在进入 candidate 前，必选知识面都被 sourced 命题覆盖，或对该面显式 unresolved；
2. **准确性**：命题有可复核来源与证据定位；禁止无来源推断；图像/玩具/影视/生成图不得当唯一事实源；确定性、未知项、混淆边界、安全边界诚实；
3. **类型覆盖**：分类里每一种 `primary_form` 都有可插拔的覆盖包；领域特有事实检查是另一类插件，不把哺乳动物字段强加给地点或原理。

从前期 Skill 吸收的是 **CLASSIFICATION → FACT → SEMANTIC CORE（作为知识轴，不是插图清单）** 以及各领域 **Fact Checks**。忽略 Skill 中 TEMPLATE / LEARNING AXES 任务槽 / 四卡文案 / COPY / IMAGE / CONTENT LOCK / Renderer。

本设计满足路线图 `KNOW-03`。Learning Plan、Projection、四卡排版不在本刀。

## 2. 非目标

- 不实施 WB-02，不改 AGE COPY、RENDER、画廊、操作台生成。
- 不把 `record`、`copy`、描红、口头复述、visual_grammar、page_order 写入 Knowledge Core。
- 不把覆盖注册表做成第五个治理对象；不改四对象**顶层文件名**。知识对象**内部**字段由 `record-shape` 插件升级，不改 v1 FACT 键集与 packet 契约。
- 本刀不在服务器上实现 ChatGPT web search；源头获取合同见 §4.5。
- 不在本刀为套件外的每种 subtype 写百科正文；cycle/structure 等仍只登记 pack 文件。
- 格温夹具不上画廊、不进小程序、不 reload 生产 library。
- 不 reload 生产 library、不 merge server `main`、不 push、不现网。

## 3. 从 Skill 吸收 / 丢弃

| Skill 阶段 | 本环节 | 理由 |
| --- | --- | --- |
| CLASSIFICATION v2 | 吸收（已由 KNOW-01 落地词表） | 对象类型入口 |
| FACT：来源、命题、confidence、confusions、safety、unknowns | 吸收进准确性内核 | 知识权威 |
| 「不可把图像当唯一事实源」 | 吸收 | 准确性 |
| 领域 Fact Checks（古生物时间/证据/重建不确定；地点官方源；历史时间-地点-证据） | 吸收为 domain overlay | 类型特有准确性 |
| SEMANTIC CORE 八轴（visual/spatial/temporal/functional/historical/contextual/relational + entity_or_concept） | 吸收为可选知识轴，由 coverage pack 声明哪些轴必填 | 全面性，不是插图 |
| form pack 的知识面（recognition、landmarks、state_rule…） | 吸收为 coverage pack facets | 全面性 |
| LEARNING AXES / TEMPLATE / 四卡 / COPY / IMAGE / LOCK | **丢弃** | 投影呈现 |
| 年龄语言适配 | 丢弃（已在 AGE-01 / Plan） | 学习者身份，属投影前一层但不是本刀知识源 |

ADR-001：迁到服务器并重审，不把 Skill 包形态直接合入。

## 4. 可插拔架构

三层插件，主机只做解析与执行，不把某类对象的字段写死在 Core schema。

```text
classification-registry-v1     这是什么类型（KNOW-01）
        ↓
coverage-host-v1
   ├ record-shape-v1           知识记录有哪些字段（可升级）
   ├ source-intake-v1          源头如何进入记录（本刀 manual）
   ├ accuracy-kernel-v1        共享准确性
   ├ coverage-pack/{form}.vN
   ├ coverage-pack/overrides/{domain}.{form}.{subtype}.vN
   └ domain-overlay/{domain}.vN
        ↓
Knowledge Core
        ↓
library candidate
        ↓
Projection（后期）
```

### 4.1 主机

`coverage-host-v1` 输入：authoring 编译后的 Knowledge Core + `scope.classification`。

解析顺序：

1. 选择 coverage pack（精确，禁止猜测）：
   - 若登记了 `(primary_domain, primary_form, object_subtype)` 的 **pack override** 文件 → 用该 pack（独立 id+sha）；
   - 否则用 `primary_form` 的默认 pack；
   - 都没有 → `COVERAGE_PACK_GAP`（新 authoring 不得静默跳过）。
2. 若存在 `domain-overlay` 且 overlay 声明适用于该 form，则合并 **额外** 必选面与禁止推断规则；overlay 不得删除**当前选中 pack** 的必选面。换 pack 只能走 override 文件，不能靠 overlay 删面。
3. `secondary_forms` / `secondary_domains` 只激活 pack 里已声明的 `modules`；未声明 → `COVERAGE_MODULE_UNKNOWN`。不得用次形态换主 pack。
4. 跑 `accuracy-kernel`，再跑 pack 全面性，再跑 overlay。
5. 把所用插件身份写入 Core 或 manifest 旁路字段：`coverage_host`、`accuracy_kernel`、`coverage_pack_id`、`coverage_pack_sha256`、可选 `overlay_id` + sha、若用了 override 则记 `coverage_pack_override=true`。revision 绑定当时插件字节，升级插件不改写旧 revision。

主机与插件都是校验权威，不是第五个治理对象。

### 4.2 插拔升级

| 动作 | 怎么做 | 不做什么 |
| --- | --- | --- |
| 新增一种 form 或 subtype 专用面 | 加默认 pack，或加 `(domain, form, subtype)` override 文件 | 不改 unit/proposition 通用 schema；不靠 overlay 删掉哺乳动物面来「适配」格温 |
| 收紧某类对象 | 发 `{form}.v2`（新 sha）；新编译走 v2；旧 revision 仍引用 v1 sha | 不原地改 v1 文件语义 |
| 新增领域检查 | 加 `domain-overlay/{domain}.v1` | 不把古生物字段写进 entity pack |
| 停用某面 | 新 major；列出 `removed_facets`；旧面在新包中变为 optional 或 forbidden | 不无声删旧 pack 文件 |

每个插件文件含：`id`、`version`、`applies_to`（form 或 domain）、`required_facets[]`、`optional_facets[]`、`modules`、`forbidden_inferences[]`、`required_source_kinds[]`（可空=沿用内核）、`enforcement`（`required` / `defined`）。

`defined`：结构已登记，schema 测试加载；该 form 的新 authoring 若 enforcement 尚未切到 `required`，只警告不挡 candidate（测试必须能列出「已定义未强制」）。

本刀全局：默认 pack `entity` 为 `required`（无 override 时）。其余默认 pack 仍为 `defined`，避免 AUTHOR-03 几何、AUTHOR-04 时效日程被未完成的包误杀。

**例外**：§8 兼容套件里的主题，对**它们选中的 pack** 一律按 `required` 过门（place / event / rule-principle / fictional-character 含在内）。套件外的既有夹具不走这条例外。把某默认 pack 全局改为 `required` 仍是另一次显式升级。

### 4.3 现码缺口（为何显得不够丰富）

相对 ADR-002 §5 与 Skill FACT/SEMANTIC CORE，当前 authoring 编译结果少了这些**记录能力**（不是少了四卡槽）：

| 缺口 | 现码实际 | Skill / ADR 已有 |
| --- | --- | --- |
| 对象身份 | 只有 topic.title | `name_cn` / `name_en` / `scientific_name` |
| 命题类型 | 无 `fact_type` | FACT `fact_type` |
| 语义轴 | 无 | SEMANTIC CORE 八轴列表 |
| 来源–命题关系 | 每条命题恰好一个 source，关系写死 `supports` | supports / limits / conflicts / background |
| 获取时间 | `retrieved_at` 复制 `authored_at` | 独立获取时间 |
| 检索过程 | 无 | Skill 用 ChatGPT web search 找页，但**没有**把 query/工具写入 Core |
| Scope 排除 | 无 `excluded_questions` | ADR-002 §5.6 |
| 单元问题 | 只有 title | 单元应回答一个独立问题 |

本刀用 `record-shape-v1` 把这些加成 Core 字段，仍由 pack 决定哪些必填。不把插图清单或 COPY 槽加进来。

### 4.4 知识记录形状 `record-shape-v1`

一组可版本化的字段组。主机校验「记录是否长得像知识源」；coverage pack 只引用组名，不复制字段定义。升级形状 = 发 `record-shape-v1.1`，旧 revision 仍绑 v1 sha。

**identity（对象）**

- `names.cn`、`names.en`（必填于 entity `required` 编译）
- `names.scientific`（可空；空则该 identity 点必须 unresolved 或 overlay 声明不适用，如虚构几何对象）
- `aliases[]`（可空）

**source（来源）**

在现有 kind/title/locator/creator/version/license/usage_boundaries/quality/valid_until 之上：

- `retrieved_at`：独立于 `authored_at`
- `source_language`
- `intake`：`{method: manual|search|fetch, query?: string, tool?: string, captured_at}`
  本刀只允许 `method=manual`。`search` / `fetch` 键位先留下，内核遇到未启用 method → `INTAKE_METHOD_DISABLED`
- `evidence_spans[].relation`：`supports` | `limits` | `conflicts_with` | `background`（不再写死 supports）
- `evidence_spans[].representation`：`paraphrase` | `locator_only`（禁止把外部正文整段拷进 Core）

**proposition（命题）**

在现有 canonical_claim / certainty / unknowns / confusion_boundary / safety_scope / temporal / standing 之上：

- `fact_type`：`identity` | `property` | `process` | `relation` | `safety` | `unknown_boundary`
- `semantic_axes[]`：`visual` | `spatial` | `temporal` | `functional` | `historical` | `contextual` | `relational` | `entity_or_concept` 的子集
- `source_ids[]`：允许多个；每个带 relation（与 span 一致）
- 不再要求恰好一个 `source_slug`

**unit**

- `coverage_facet`（entity 强制）
- `question`：该单元回答的独立问题（可与 title 相同，但必须是问句或等价命题标签）

**scope**

- `excluded_questions[]`：本次明确不讲的问题（可空，但空必须是有意，不是漏记；entity 本刀至少 1 条，防止「主题名当百科」）

**relations**

现有 `prerequisite_of` / `supersedes` 保留。`record-shape-v1` 增加可选 `proposition_relations[]`：`supports` | `limits` | `conflicts_with` | `part_of` | `compares_with`。Renderer 仍不得自定义关系类型。

entity 强制编译还要求：每个必选 facet 的 unit 里至少一条命题带与该面相符的 `semantic_axes`（例：`appearance` → `visual`；`habits` → `functional` 或 `relational`；`environment` → `spatial` 或 `contextual`）。

### 4.5 源头获取（现在没有 web search）

**现状（代码真值）**

- Skill 生成 FACT 时，操作员在 ChatGPT 里用 **web search** 找到机构页，再写入命题。检索过程没有进 Knowledge Core。
- 当前项目形态：`rabbit-real.json` 由人写死 Merck / RSPCA 的 `locator`；`compile_authoring_request` **不访问网络**、不搜索、不抓正文。准确性内核只能检查「字段在不在」，不能证明页上真有这句话。
- [API-01](2026-07-31-cognitive-card-trusted-upstream-compiler-design.md) 才把「受信 Codex + ChatGPT Pro 做 CLASSIFICATION/FACT」定为编译器；队列在 WB-03 之后，**不是**本刀、也还没接到 knowledge-library CLI。

**合同（可插拔，本刀只启用 manual）**

```text
人（或未来编译器）查到页
        ↓
source-intake-{manual|search|fetch}.vN
        ↓
Source 记录（locator + intake 元数据 + paraphrase span）
        ↓
accuracy-kernel   只校验记录，不负责去网上找页
```

| 插件 | 谁做检索 | 本刀 |
| --- | --- | --- |
| `source-intake-manual-v1` | 人在写作前打开机构页，写入 locator、retrieved_at、paraphrase | **启用** |
| `source-intake-verify-v1` | 服务器对 locator 做可达性检查（HEAD/GET），仍不搜索、不把正文当命题 | 登记 `defined`，不强制 |
| `source-intake-search-v1` | 未来 API-01 编译器（或其它带检索的执行器）写入 `intake.query` + `tool` + 命中 locator | **键位预留，本刀禁用** |

禁止：服务器在 compile 时调用 ChatGPT / 任意搜索 API 发明 locator；禁止把搜索摘要直接当成 `canonical_claim` 而不建 Source 记录。

兔子修订仍用手工 Merck/RSPCA locator；`intake.method=manual`，`retrieved_at` 写实际查阅日，不得再等于 `authored_at` 的静默复制。

### 4.6 与 TMPL-01 隔离

知识源过覆盖门 **不要求** 有四卡模板。`TEMPLATE_GAP` 只在 convert 到 four-card 时出现。没有模板的类型仍然可以有完整知识源（例如 `abstract-concept` 走 progressive，不走四卡）。

## 5. 准确性内核 `accuracy-kernel-v1`

对每条纳入 Scope 的命题：

1. `established` / `probable` 必须有 `source_id` 与可复核 `evidence_locator`（URL 或与 AUTHOR-04 同等的合成定位，且不得伪装成外部论文）；
2. 来源记录含 title、creator 或机构、locator、license/usage 边界；禁止复制外部正文；
3. 图像、玩具、影视、生成图不得作为该命题的**唯一**来源；
4. 无来源的主张只能是 `unknown` / unresolved，文案不得改成肯定句；
5. `confusion_boundary` 与 `safety_scope` 不得用投影任务顶替；空安全仅在 pack 未要求 `safety` 面时允许；
6. 确定性不得为了过门而升级。

内核版本独立升级。领域 overlay 可追加禁止推断（例：恐龙体色），不能放宽 1–4。

## 6. Coverage packs（知识面，已去掉任务槽）

Facet 是知识面 id，不是四卡 zone。每个 unit 恰好一个 `coverage_facet`。命题通过所在 unit 归属一面。`care` 与 `safety` 不得同单元。

下列 facet 从 Skill form pack / 领域 Fact Checks 抽出，去掉 `record`/`copy`。`care` 是本设计相对历史 entity pack 的显式补面。

### 6.1 `entity`（`required`，本刀强制）

`recognition`，`appearance`，`physical_features`，`habits`，`environment`，`safety`，`care`。

植物与哺乳动物共用。`care`：饲养/栽培，或不饲养、不乱采、观察距离。必选 SEMANTIC 轴：`visual` 或 `functional` 至少一面有对应命题（appearance/physical/habits 可满足）。

Paleontology 以 entity 为主路由时，**叠加** §7 古生物 overlay（时间、证据、重建不确定），不另造一套 entity 面。

### 6.2 其余 form（`defined`，本刀登记结构）

| pack | 必选知识面（无 record/copy） | 主要来源 |
| --- | --- | --- |
| `place` | `locate`，`spatial_range`，`landmarks`，`function`，`visit_safety` | 地点 pack；官方地图/场所源 |
| `structure` | `parts`，`arrangement`，`load_path`，`function`，`public_safety` | 桥梁等 structure pack |
| `system` | `components`，`interaction`，`flow`，`use_boundary` | 地点文档 system pack |
| `process` | `start_state`，`sequence`，`observed_change`，`result`，`safety_boundary` | chemistry process pack |
| `cycle` | `stages`，`sequence`，`loop`，`conditions` | water-cycle pack |
| `event` | `time_place`，`actors`，`sequence`，`before_after`，`evidence`，`result` | 历史 event + 天气 before/during/after |
| `phenomenon` | `observation`，`conditions`，`effect`，`limits` | 现象；与 rule 的 limits 区分 |
| `relationship` | `members`，`direction`，`roles`，`dependency` | ecology relationship |
| `rule-principle` | `try_case`，`compare_outcome`，`state_rule`，`limits` | physics pack |
| `evidence-record` | `source_type`，`observable_clue`，`provenance`，`uncertainty`，`supports` | 历史 evidence pack |
| `material` | `identity`，`properties`，`uses`，`safety` | 分类 form；Skill 无独立 family 时本包为结构占位 |
| `abstract-concept` | `identity`，`definition`，`example`，`limits`，`relations` | 几何试产应对齐的面；本刀 `defined`（AUTHOR-03 不进 §8 套件） |
| `fictional-character` | `identity`，`appearance`，`role`，`continuity`，`publication_provenance`，`confusion_boundary`，`ip_safety` | **pack override**，不是第 15 个 `primary_form`。路由 `arts + entity + fictional-character`。证明格温不能套哺乳动物 `habits`/`care` |
| `other` | 无必选面；新 authoring 用 `other` → `CLASSIFICATION_REVIEW`（KNOW-01 已有精神） | 禁止当跳过覆盖的出口 |

次形态模块（仅 pack 声明后可开），例：`entity` 可声明 `comparison` optional；`structure` 可声明 `place_context`。与 Skill secondary_modules 同构，但不激活四卡槽。

## 7. Domain overlays

| overlay | 适用 | 额外准确性 / 面 |
| --- | --- | --- |
| `paleontology` | primary 或 secondary domain | 地质时间、发现区域、可观察证据、重建不确定必现为命题或 unresolved；禁止把体色、软组织、声音、速度、育幼、羽毛状态写成 `established`（除非 overlay 列出的 sourced 例外） |
| `geography-place` | 该 domain | 来源优先政府/官方地图/场所；禁止把生物外形字段当成必选 |
| `history-archaeology` | 该 domain | 事件：时间、地点、行动者、序列、结果、证据；影视不是事实源；禁止虚构对话与内心；战争/战役用中性低刺激表述 |
| `fiction-media` | `arts` + fictional-character pack | 故事世界主张必须 `standing=fictional`（或等价）；漫画/影视**可以**作为虚构身份的来源，**不得**作为现实生物/物理命题的唯一来源；禁止把角色当真实人物做 `care`/`habits`；`names.scientific` 不适用 |

没有 overlay 的 domain 只走 pack + 内核。新增海洋、材料等领域时只加 overlay 文件。

`fiction-media` 收窄内核第 3 条对「影视不得当唯一事实源」的解释：仅对 `standing=fictional` 的命题允许故事媒介作源；现实命题仍禁止。不得把该 overlay 套到霸王龙或故宫。

## 8. Authoring 合同

1. 选中 pack 为默认 `entity`（无 override）的新编译：每个 unit 必填 `coverage_facet`（§6.1 七者之一）；缺 → `AUTHORING_FIELD_REQUIRED`；未知 id → `AUTHORING_COVERAGE_UNKNOWN`。格温等 override pack 用该 pack 自己的 facet 词表。
2. 当前选中 pack 的必选面皆须有 sourced 命题，或该面 unresolved；否则 `CORE_COVERAGE_GAP`。默认 entity 即七面。
3. 默认 entity 的 `safety` 面命题须非空 `safety_scope`，或该面 unresolved。`care` 不得用 `safety_scope` 顶替。override pack 按自身 safety/ip 面执行。
4. 编译结果记录所用 pack/kernel/overlay 的 id+sha。
5. 非 entity、且主题不在 §8 套件、且 pack 为 `defined`：本刀不因缺 facet 失败（几何、时效夹具保持）。主机仍必须能解析到 pack 文件。
6. 不改 AUTHOR-03 / AUTHOR-04 既有夹具命题，除非测试需要证明 `defined` 不误杀。套件主题是**新增** authoring JSON，不改生产 library。
7. 套件内以及无 override 的 entity 编译走 `record-shape-v1`：identity 中英名（科学名按 pack/overlay：实体生物尽量有，地点/事件/原理/虚构角色可空并声明不适用）、每命题 `fact_type` 与 `semantic_axes`、来源 `intake.method=manual` 且独立 `retrieved_at`、scope 至少 1 条 `excluded_questions`。
8. 编译不得发起网络检索。`intake.method=search` → `INTAKE_METHOD_DISABLED`。
9. KNOW-01 本刀允许的词表增量（仍不是第五个治理对象）：`arts` 增加 subtype `fictional-character`；`paleontology + entity + dinosaur` 随霸王龙首个对象从 `gap` 记为 `enabled`。**不**把 `paleontology + entity + fossil-animal` 从 `review` 改掉（那条路由仍停止猜测）。

### 8.1 兼容套件（本刀必须过门的知识对象）

下列主题证明：同一四对象合同 + 可插拔 pack，能容纳不同可学习对象，而**不**把哺乳动物字段加给地点、原理或虚构角色。全部 `intake.method=manual`，`projection: {}`，不 reload 生产 library、不上画廊、不进小程序。

| 对象 | 建议 slug | 分类 | 选中 pack | overlay | 过门要点 |
| --- | --- | --- | --- | --- | --- |
| 兔子 | `rabbit` | `life + entity + animal/mammal` | `entity` | — | 修订现有 Merck/RSPCA；见 §8.2 |
| 鹅掌藤 | `heptapleurum-arboricola` | `life + entity + plant` | `entity` | — | 取代无名植物夹具；`care`=栽培/不乱采，不是喂干草 |
| 霸王龙 | `tyrannosaurus-rex` | `paleontology + entity + dinosaur` | `entity` | `paleontology` | **不用** `fossil-animal`（KNOW-01 `review`）。体色/软组织/声音/速度不得 `established`。`care`=不饲养、博物馆观察距离 |
| 蜘蛛侠（格温） | `spider-gwen` | `arts + entity + fictional-character` | **override** `fictional-character` | `fiction-media` | 见 §8.5。禁止套用 entity 七面 |
| 故宫 | `forbidden-city` | `geography-place + place + urban-landmark`；次领域 `history-archaeology` | `place` | `geography-place` | 次领域只开已声明 module；不换 place pack；官方/场所源 |
| 四渡赤水 | `four-crossings-chishui` | `history-archaeology + event + historical-event` | `event` | `history-archaeology` | 时间-地点-行动者-序列-结果-证据；影视不是事实源；战役中性表述，禁止虚构对话 |
| 牛顿第一定律 | `newton-first-law` | `physics + rule-principle + general` | `rule-principle` | — | `try_case` / `compare_outcome` / `state_rule` / `limits`；科学名不适用 |

反例（必须失败）：

- 格温未登记 override、却按默认 entity 七面编译 → `PACK_OVERRIDE_REQUIRED`。
- 霸王龙把体色写成 `established` → `OVERLAY_INFERENCE_FORBIDDEN`。
- 四渡赤水唯一来源是影视 → `CORE_ACCURACY_GAP`。
- 故宫 unit 使用 `care` / `habits` → `AUTHORING_COVERAGE_UNKNOWN`。
- 牛顿第一定律缺 `limits` 且无 unresolved → `CORE_COVERAGE_GAP`。

套件主题的 locator 优先真实机构/教材/官方页；没有则该面 unresolved 或诚实合成源（须标明合成，禁止伪装论文）。禁止无来源中文杜撰。

### 8.2 兔子（真实来源，entity 过门）

修订 `rabbit-real.json`。优先切开现有 Merck / RSPCA 八条命题：

| facet | 现有命题 |
| --- | --- |
| `recognition` | 从 `body-shape` 切出类属（哺乳动物） |
| `appearance` | `body-shape` 外形 |
| `physical_features` | `hopping`，`growing-teeth`，`cecotropes` |
| `habits` | `social-curious` |
| `environment` | `safe-hiding` |
| `care` | `hay-and-fiber` |
| `safety` | `safe-handling` |

拆掉混用的 `care-safety` 单元。无证据的面：unresolved，或新增真实机构 locator。禁止无来源中文杜撰。`projection` 仍 `{}`。

identity：`names.cn=兔子`，`names.en=rabbit`，`names.scientific=Oryctolagus cuniculus`（家兔常见学名须仍绑 Merck 页能支持的释义；若该页不够则 unresolved 学名，不得杜撰）。每条来源 `intake.method=manual`。本机过门；不更新生产 library，除非另授权。

### 8.3 鹅掌藤（entity 植物，不是第二只哺乳动物）

`heptapleurum-arboricola.json`：`life + entity + plant`，七面过门。身份：`names.cn=鹅掌藤`，`names.en` 用园艺通名（如 umbrella tree / dwarf schefflera），`names.scientific=Heptapleurum arboricola`（或 sourced 的现行学名）；`aliases` 可含旧名 `Schefflera arboricola`，分类变动标 `probable` 或 unresolved，不得把未核对的学名写成 `established`。`care` 为室内栽培/毒性接触边界，不得抄兔子的干草命题。合成来源须诚实标注。

### 8.4 霸王龙 / 故宫 / 四渡赤水 / 牛顿第一定律

各一份 authoring JSON，facet 对齐所选 pack + overlay。霸王龙地质时间、发现区域、可观察证据、重建不确定必须有命题或 unresolved。故宫 `visit_safety` 不得鼓励翻越、进入非开放区。四渡赤水不写战场观光任务（知识源阶段只记录边界，不写投影任务槽）。牛顿第一定律 `limits` 至少覆盖「理想化 / 近似」类未知或 sourced 限定。

### 8.5 蜘蛛侠（格温）（虚构角色；证明 override）

本夹具只验证知识源结构与准确性，**不是**授权公网或小程序发布。`docs/compliance/content-ip-risk-register.md` 将 Spider-Verse 列为 P0；本 JSON 留在 server examples，禁止 PORTAL / kids-world / 画廊 / 生产 library。

知识合同：

- 走 `fictional-character` pack，不走 entity 七面。`names.scientific` 空且 overlay 声明不适用。
- 出版事实（首次登场、创作者、作品名）可 `established`，须有可复核 locator（出版社/图书馆书目/可靠辞书），禁止整页拷官方设定集。
- 故事内能力、服装、经历一律 `standing=fictional`；漫画与电影格温分 `continuity` 单元或 unresolved，禁止焊成一个真人。
- `confusion_boundary`：虚构格温 ≠ 现实人物；不同媒介连续性不可混称「就是同一个人」。
- `ip_safety`：不把官方造型复刻写成观察对象；不把格斗当现实指导。
- 内核：现实命题仍禁止影视唯一源；虚构身份命题允许故事媒介作源（`fiction-media`）。

### 8.6 结构夹具（未进套件的 form）

仓库内每个 **未进 §8.1 套件** 的 `defined` pack 仍须有一份 **最小 JSON 插件文件** + 主机加载测试（能解析 required_facets）。不要求为本刀再写水循环、桥梁等百科正文。

## 9. 错误码

| 码 | 含义 |
| --- | --- |
| `COVERAGE_PACK_GAP` | 该 `primary_form` 无 pack 文件 |
| `COVERAGE_MODULE_UNKNOWN` | secondary_form 未在 pack.modules 声明 |
| `CORE_COVERAGE_GAP` | 强制 pack 缺面且无 unresolved |
| `CORE_ACCURACY_GAP` | 内核准确性失败（无来源、唯一源是图像等） |
| `OVERLAY_INFERENCE_FORBIDDEN` | overlay 禁止的推断被标成 established |
| `AUTHORING_FIELD_REQUIRED` | entity 单元缺 `coverage_facet` |
| `AUTHORING_COVERAGE_UNKNOWN` | facet 不在当前 pack |
| `INTAKE_METHOD_DISABLED` | 使用了本刀未启用的 search/fetch |
| `RECORD_SHAPE_GAP` | 缺 record-shape 必填字段（身份名、fact_type、excluded_questions 等） |
| `PACK_OVERRIDE_REQUIRED` | 套件主题（格温）未走已登记 override，或把 fictional-character 面写进默认 entity 编译 |

分类错误仍 KNOW-01。四卡模板缺口仍 TMPL-01。

## 10. 验收

- 主机能加载 accuracy-kernel、entity pack（required）、以及 §6.2 全部 `defined` pack 文件；各文件有独立 sha。
- 换一份新 pack 文件（测试用假 form 禁止合入正式词表）只需登记、不必改命题 schema：插件测试覆盖「加文件即可解析」。
- entity 无 facet / 缺 environment 无 unresolved / 缺 names 或 fact_type → 对应错误码。
- 修订后兔子含独立 retrieved_at、manual intake、中英名；编译过 entity 门。鹅掌藤过同一 entity 门且 `care` 命题不得与兔子干草相同。
- §8.1 其余五主题各自通过所选 pack（+ overlay）；格温编译记录 `coverage_pack_override=true`，且不得出现 entity 的 `habits`/`care` 作为必选面。
- 格温夹具不得出现在生产 library / 画廊 / 小程序路径的测试里。
- compile 测试不得 mock 成「服务器搜索网页」。
- AUTHOR-03 / AUTHOR-04 编译不因本刀失败。
- 命题不得新增无 locator 的 `established`。
- 不改画廊 ACCEPT-01 包；不实施 WB-02。
- focused：host + kernel + pack/override 加载 + §8.1 七主题 authoring。

## 11. 实现落点与切片

权威仓库：server `knowledge-pipeline-v1`。kids：本设计与账本。

建议代码顺序（同一 spec，可分 commit）：(1) record-shape + 插件文件 + 主机加载（含 override）；(2) accuracy-kernel + manual intake；(3) entity 强制 + 兔子/鹅掌藤；(4) overlay + 霸王龙/故宫/四渡赤水/牛顿第一定律；(5) fictional-character override + 格温（本机 only）。不实现 search intake。不打生产 release。不把格温写入现网。
