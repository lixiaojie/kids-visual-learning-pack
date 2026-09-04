# 投影图例（LEGEND-01）

- Status: Approved for this execution tranche
- Date: 2026-09-03
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[KNOW-03 覆盖面](2026-09-01-entity-knowledge-coverage-design.md)、[TMPL-01](2026-08-31-template-family-registry-design.md)、[AGE-01](2026-08-31-age-language-adapter-design.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[IMG-01](2026-09-02-operator-illustration-hero-page-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)
- Does not implement: IMG-02 多图槽；RENDER-02 模块铬；改四对象 schema；整卡烧字；生产安装。server 登记表已在 `knowledge-pipeline-v1` @ `f9baf8f` 落地（未 push），不属本切片未实施项。
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

在掌握对象全部事实之前，仍能约束 AI 收集与呈现，且不把「恐龙必须有阶元 / 体长」写进合同。

本设计发布 **`projection-legend-v1`**：一张封闭的**认知角色**词表，加上每角色允许的**视觉语法**。有实例才亮模块；没有就空着。禁止发明角色，禁止 `misc` 散文袋，禁止 ChatGPT 把文字烧进图。

本设计满足路线图 `LEGEND-01` 的书面合同。`IMG-02`（多视图像素）与 `RENDER-02`（模块铬）消费本图例，各自另立任务，不在本刀实施。

质量标尺是旧 Skill 剑龙四卡的**教学密度与模块种类**，不是整卡生图做法。

## 2. 非目标

- 不改四对象顶层文件名、v1 FACT 键集、packet 契约、AUTHOR-05 默认 Projection 表。
- 不替换 [KNOW-03](2026-09-01-entity-knowledge-coverage-design.md) 的 `coverage_facet` 知识面（`recognition` / `appearance` / …）。图例角色不是知识分类，也不是四卡 zone。
- 不把「必须有三视图 / 剖面 / 爆炸图 / 环境戏」写成知识源准入或 Confirm current 条件。
- 不实施多 PNG 槽、Pillow 配色大改、时间条/步骤条像素、现网。
- 不新开 ADR。本注册表与 `template-registry-v1` 同类：投影权威，不是第五个治理对象。
- 不 merge server `main`、不 push、不打 release、不 reload Nginx。
- 不等于 AGE-02 / ACCEPT-02 / PORTAL / 可交互烧字页。

## 3. 在分层中的位置

```text
Knowledge Core              命题、来源、未知、安全、coverage_facet
        ↓
legend_role 解析            显式角色，否则按 pack 别名；禁止 misc
        ↓
projection-legend-v1        角色 → 允许画法；空则不画
        ↓
编译 / 映射 / 生图 / 排版   各节点只认这张表
```

相对 ADR-002：角色是 Projection Blueprint 的呈现意图，不是新事实。Learning Path（先学平面再学立体）不是 `sequence`。`sequence` 只描述**对象自身**的过程链。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 图例性质 | 凡例：出现过的信息算哪一类、怎么亮；不是对象字段清单 |
| 主轴 | 认知角色；视觉语法是第二列 |
| 空模块 | 该角色零实例 → 不画；禁止为填满而编造 |
| 烧字 | 继续禁止；字由服务器排 |
| 与 KNOW-03 | `coverage_facet` 保持知识面；`legend_role` 另解 |
| 接合顺序 | 见 §7：显式角色 → coverage 别名 → `process`→`sequence` → 未知确定性 → 否则失败 |
| 旧卡对照 | 查模块是否该亮/该空；不对像素 |
| 深圳 | 不是图例默认；只有存在 `learning_place` 实例才画学习地 |
| 多视图 | 词表先登记；像素槽位属 IMG-02 |

## 5. 认知角色（封闭）

角色 id 为小写蛇形，v0 仅下列值。增删角色必须升 `projection-legend-v1` 的兼容修订或改 major，不得静默加 `misc`。

| 角色 | 孩子这边的意思 | 没有时 |
| --- | --- | --- |
| `observe` | 可指认的外形/姿态 | 不画「看」的细部图 |
| `compare` | 可并列的部件 | 不画部件图标排 |
| `evidence` | 我们怎么知道（化石、骨架、模型、机构记录） | 不画证据盒 |
| `time` | 在时间尺上的位置（地质时代、年代区间） | 不画时间条 |
| `place` | 对象生活地或发现地 | 不画发现地图 |
| `learning_place` | 孩子此刻的学习地 | 可省略；出现则必须和 `place` 分开标记 |
| `habit` | 习性或功能（吃什么、怎么动、防御） | 不画习性块 |
| `kind` | 它是哪一类（有才写，不规定阶元深度） | 不画分类块 |
| `sequence` | 有顺序的过程，步骤不可重排（成长、反应） | 不画步骤条/循环图 |
| `setting` | 对象与环境共存及交互 | 不画在场/互动场景 |
| `uncertain` | 还不是事实 | 有 `unknown`/`disputed` 命题就必须能进此处理，禁止画成肯定 |
| `safety` | 观察/触摸/照护边界 | 沿用现 four-card 安全登记；缺则不能锁四卡 |
| `source` | 署名 | 沿用现来源合同 |
| `name` | 可描红的称呼 | 无描红格 |
| `write` | 从已出现知识句切出的抄写 | 按 AGE：`age-5-6` 有、`age-3-4` 无 |
| `blank` | 孩子自己填或画，不承载命题 | 结构可在；永远不写入知识节点 |

看 / 画 / 比 / 找不是角色，而是 `observe` / `compare` / `evidence` 的学习动作。自由画提示只能引用已出现的 `observe` 或 `compare` 部件。

`time` 与 `sequence` 不得合并：前者是尺上的落点，后者是不可重排的步骤。时间向成长与事件向反应同属 `sequence`，差别只在画法。

## 6. 视觉语法

图资产无字。标注、标题、步骤号、地图名由服务器排。某画法零实例 → 不调用。

### 6.1 `observe` 画法

| 画法 | 孩子在看什么 |
| --- | --- |
| `isolate` | 整只/整件可指认外形（IMG-01 主图属于此列） |
| `three_view` | 同一对象的正/侧/顶 |
| `section` | 从外面看不到的内部 |
| `exploded` | 部件怎么组合 |

不是每个对象都要出齐。爆炸图对剑龙可空，对机械可亮。剖面上画了「内部有 X」即主张该结构；未锁定则必须按 §8 的不确定规则处理。

### 6.2 其他角色允许的画法

| 角色 | 允许 | 禁止 |
| --- | --- | --- |
| `observe` | §6.1；色块「看」 | 画面烧外形名称 |
| `compare` | 图标列；轮廓 + 服务器标注线 | 把未锁定部件画进图 |
| `evidence` | 图标盒 | 把复原、生成图当唯一照片事实 |
| `time` | 时间条 | 把未锁定的精确年份画成已知刻度 |
| `place` / `learning_place` | 地图钉或地点徽章；两地两套标记 | 深圳当古代栖息地；两地共用同一钉 |
| `habit` / `kind` | 模块卡 + 图标 | 为填满而编阶元或体长 |
| `sequence` | 编号步骤条、循环图、前/后对照 | 打乱步骤；把未锁定中间态画成已知 |
| `setting` | `in_situ` 在场场景；`interaction` 互动场景 | 把 `learning_place` 画成对象家园 |
| `uncertain` | 问号模块或虚线标注 | 确定的体色、叫声、未证互动 |
| `safety` / `source` | 页脚模块 | 插图进入清场区 |
| `name` / `write` | 描红格 / 抄写线 | 生图里写好字让孩子描 |
| `blank` | 横线、空画框 | 写入命题 |

`safety`、`source`、`uncertain`、`blank` 以及 AGE 的 `trace` / `copy` / `record` 清场规则与 [RENDER-01](2026-08-31-locked-four-card-render-design.md) / [COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md) 一致：插图不进这些区。

## 7. 角色解析（不改 Core schema）

命题不在 Knowledge Core 里新增必填字段。解析发生在编译输出 → 投影接合，按下列顺序，命中即停：

1. 若 authoring / 编译回复带显式 `legend_role`，且为 §5 之一 → 采用。
2. 否则按该 unit 的 `coverage_facet` 查 **pack 别名表**（§7.1）。
3. 否则若 KNOW-03 `fact_type` 为 `process` → `sequence`。
4. 否则若命题 `certainty` 为 `unknown` 或 `disputed`，或 `fact_type` 为 `unknown_boundary` → `uncertain`。
5. 否则新编译失败 `LEGEND_ROLE_MISSING`。已存在、无显式角色的 library current：仅当第 2 步别名命中才允许继续；不得用 `observe` 兜底吞掉其余句子。

同一命题不得解析出两个角色 → `LEGEND_ROLE_CONFLICT`。

`write` / `name` / `blank` 不由模型发明句子：`name` 与 `write` 来自 AGE-01 `copy_plan` 对已出现知识句的切片；`blank` 永不引用 `proposition_id`。

KNOW-03 `fact_type=identity` 不单独改放置角色；描红仍从身份称呼切片。

### 7.1 entity pack 默认别名

KNOW-03 entity 七面保持原义。v0 别名只用于**缺省投影角色**，不表示两套 id 相等。

| `coverage_facet` | 默认 `legend_role` |
| --- | --- |
| `recognition` | `observe` |
| `appearance` | `observe` |
| `physical_features` | `compare` |
| `habits` | `habit` |
| `environment` | `setting` |
| `safety` | `safety` |
| `care` | `safety` |

`place`、`time`、`kind`、`evidence`、`learning_place` 没有对应 entity facet。它们只在显式 `legend_role` 时出现；否则该模块空着。`sequence` 还可由第 3 步 `fact_type=process` 得到。

其他 coverage pack 必须自带别名表才能走 LEGEND-01 编译门禁；无表 → `LEGEND_ALIAS_PACK_GAP`。不得把 entity 七面强加给地点或原理对象。

### 7.2 `sequence` 全序

该角色下全部实例必须能排成唯一全序。v0 次序来源（先命中先用，禁止模型另写散文顺序）：

1. 显式 `part_of` 链或 unit 内命题声明顺序；
2. 否则 unit 在 authoring 中的顺序。

排不出 → `LEGEND_SEQUENCE_UNORDERED`。学习先修（`prerequisite_of` 用于孩子学什么）不得拿来当对象过程顺序，除非同一条边被明确标成过程组成。

### 7.3 确定性覆盖画法

解析出的角色决定模块归属。若 `certainty` 为 `unknown` / `disputed`：

- 不得使用「已确定」画法（活体着色当事实、步骤当已知、互动当正在发生）；
- 必须能落入 `uncertain` 处理或父模块上的不确定标注；
- 违反 → `LEGEND_UNCERTAIN_AS_FACT`。

## 8. 节点门禁

| 节点 | 机制 | 失败时 |
| --- | --- | --- |
| 编译 API-01-TPL | 提示词只给 §5 角色与 §6 画法；列出 entity 别名；不给恐龙字段清单 | 未知角色 / 缺角色 / 双角色 |
| AGE-01 | `name` / `write` 仍从知识句切片；安全原文规则不变 | 沿用 `AGE_*` |
| 映射 WB-02 | 按角色聚槽；空角色省略；`blank` 无 `node_ids` | `LEGEND_BLANK_HAS_NODES`；禁止把溢出命题塞进 `blank` 或来源区顶替角色 |
| 生图 IMG-01 | 继续一张无字 `isolate` 主图 | 烧字 → `LEGEND_BURN_IN`（IMG-02 再扩槽） |
| 生图 IMG-02 | 只对**已有实例**的角色/画法请求无字资产 | 为填满而要爆炸图；`learning_place` 画成栖息地 |
| 排版 COMPOSE-01 | 现仍主图带 + 文字栈 | 本刀不改像素 |
| 排版 RENDER-02 | 有实例才画模块铬；清场区不变 | 空角色画假模块；插图进清场区 |

IMG-01 现网合同（一张主图）不因本 spec 作废。IMG-02 不得把「图装得下 / 视法出齐」写成知识源准入。

## 9. 错误码

| 码 | 含义 |
| --- | --- |
| `LEGEND_ROLE_UNKNOWN` | `legend_role` 或画法 id 不在 v0 表 |
| `LEGEND_ROLE_MISSING` | 新编译无法按 §7 解析角色 |
| `LEGEND_ROLE_CONFLICT` | 同一命题两个角色 |
| `LEGEND_ALIAS_PACK_GAP` | 当前 coverage pack 无别名表 |
| `LEGEND_SEQUENCE_UNORDERED` | `sequence` 有实例但无全序 |
| `LEGEND_PLACE_COLLAPSE` | `place` 与 `learning_place` 使用同一套地点标记 |
| `LEGEND_UNCERTAIN_AS_FACT` | 未知/争议被画成肯定 |
| `LEGEND_BURN_IN` | 资产上出现可读书面字（含描红底字） |
| `LEGEND_BLANK_HAS_NODES` | `blank` 引用了命题 |
| `LEGEND_VIEW_UNKNOWN` | `observe`/`setting` 使用未登记画法 |
| `LEGEND_MISC_FORBIDDEN` | 出现 `misc`、其它、未分类散文袋 |

既有 `AUTHORING_COVERAGE_UNKNOWN`、`AGE_*`、`MAPPING_*`、`TEMPLATE_GAP`、`RENDER_*`、`COMPOSE_*` 不改语义。

## 10. 验收

书面设计阶段：

- 角色表封闭、无 `misc`、无「必须有晚侏罗世/美国/三视图」类知识字段。
- `coverage_facet` 与 `legend_role` 的边界对照 KNOW-03 §6 无矛盾。
- `time` 与 `sequence` 分列；三视/剖面/爆炸挂在 `observe`；环境挂在 `setting`。
- 节点门禁与错误码可测试；IMG-02 / RENDER-02 只消费本表、不在本刀实施。

对照夹具（不对像素）：旧 Skill 剑龙 `cards.yaml` / `semantic_core.yaml`。

| 旧卡模块 | 期望角色/画法 | 空是否合法 |
| --- | --- | --- |
| 背板、尾刺、拱背 | `observe` | 否（该对象有外形） |
| 小头/背板/尾刺/四腿并置 | `compare` | 若无部件命题则空 |
| 化石、骨架 | `evidence` | 可空 |
| 晚侏罗世时间条 | `time` | 可空 |
| 美国地图钉 | `place` | 可空 |
| 深圳学习地 | `learning_place` | 可空；不得与 `place` 合并 |
| 植食、尾刺防御 | `habit` | 可空 |
| 恐龙阶元 | `kind` | 可空 |
| 背板用途/颜色/叫声 | `uncertain` | 有未知则必须可落 |
| 不爬展柜 | `safety` | four-card 沿用必填 |
| NHM | `source` | 沿用 |
| 描红「剑龙」 | `name` | AGE |
| 抄写句 | `write` | AGE |
| 我看到 / 画一排背板 | `blank` | 结构在、无命题 |

兔子 AUTHOR-02 / KNOW-04 current 必须仍能仅靠 §7.1 别名解析，不得因本 spec 无法 convert。

本文件不授权 merge 进 server `main`、不授权现网。

## 11. 后续任务消费面

| 任务 | 消费本图例的方式 | 不在 LEGEND-01 做 |
| --- | --- | --- |
| LEGEND-01 实施 | 服务器登记表、编译提示词、解析与失败码、映射按角色聚槽 | 多图、模块铬皮肤 |
| IMG-02 | 资产键 = 角色 + 画法；仅已有实例；仍无字。spec：[多视图无字资产](2026-09-03-multi-view-wordless-assets-design.md)。IMG-01 主图并存 | 改 Core；模块铬；视法出齐准入 |
| RENDER-02 | 屏幕 HTML 模块铬；打印不变；额外 PNG 按 sha 引用。spec：[模块铬](2026-09-04-legend-module-chrome-design.md) | 用观感倒逼补事实；改 illustration 提示词 |

## 12. 复杂度

不新增确认点。不新增持久化对象。不要求每个主题填满 §5。触发 [知识核心设计 §16.3](2026-08-19-knowledge-core-and-projection-architecture-design.md) 收缩条件时，先缩别名和画法，不先加角色。
