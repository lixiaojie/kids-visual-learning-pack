# 操作台迭代工作流（FLOW-01）

- Status: Approved（操作者 2026-09-04 审阅本文件；程序 spec，不授权一刀实施；首刀见 API-01-R1）
- Date: 2026-09-04
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-003](../../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[API-01](2026-09-02-operator-free-prompt-knowledge-compile-design.md)、[API-01-R1](2026-09-04-operator-framework-prompt-round-design.md)、[API-01-R2](2026-09-04-operator-complete-prompt-round-design.md)、[KNOW-01](2026-08-31-classification-registry-design.md)、[KNOW-03](2026-09-01-entity-knowledge-coverage-design.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[IMG-01](2026-09-02-operator-illustration-hero-page-design.md)、[IMG-02](2026-09-03-multi-view-wordless-assets-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)、[RENDER-02](2026-09-04-legend-module-chrome-design.md)、[PUBLISH-01](2026-08-31-immutable-package-publish-design.md)、[PORTAL-01](2026-08-31-published-artifact-gallery-design.md)
- Does not implement: 任何 server 代码；OpenAI API；可交互页运行时；打印时间条/地图/比列尺；整卡烧字；第五个治理对象；生产安装。API-01-R1 / API-01-R2 另立切片 spec/计划。
- Authority: kids 仓为产品规范；实现仍落在 server `knowledge-pipeline-v1`。本文件不授权一刀开工；可执行子刀以 [API-01-R1](2026-09-04-operator-framework-prompt-round-design.md) 与 [API-01-R2](2026-09-04-operator-complete-prompt-round-design.md) 为准。

## 1. 目标

用同一条单人主路径，迭代逼近旧 Skill 卡的**教学密度**（模块该亮/该空），而不是逼近整卡烧字像素。

操作员流程固定为四阶段：

1. **提示词**：按学习对象类型两轮扩词。第一轮只要覆盖面骨架。第二轮才出可编译的完整知识对象，并可附带「哪些节点建议生图」。
2. **排版**：系统拼出知识图谱初版（分类、内容、形态）。人可补知识点、改分类、改形态建议，然后**排版冻结**。冻结后系统才按形态导出请图提示词。
3. **视觉**：人按节点导出提示词、在 ChatGPT 等平台生无字图、回填。系统投影；人锁定该投影。
4. **画廊**：浏览、下载、打印已锁定的历史版本。

ChatGPT 仍在人的浏览器里。服务器不接模型 API、不写 Skill claim。

本设计满足路线图 `FLOW-01` 的书面合同。它是程序级工作流，不是一刀实现。首个可执行子刀是 `API-01-R1`。

质量标尺仍是旧 Skill 剑龙四卡的模块种类，不是海报像素。

## 2. 非目标

- 不把本文件当成实施授权。不写 server 代码。不写实施计划。
- 不新开 ADR。不新增第五个治理对象。四对象合同不变。`media-plan` 与 mapping 一样，是 library 元数据，不是 Core。
- 不接 OpenAI / 图像 API。不实现可交互页。不把字烧进图。
- 不把「视法出齐 / 模块出齐 / 建议生图已回填」写成 Confirm current 或知识源准入。
- 不在排版冻结时改写 Knowledge Core 字节。分类变更必须另开 Core revision。
- 不把旧卡「看 / 画 / 比 / 找」做成图例角色。
- 不改 KNOW-04 生产 library、ACCEPT-01 等分、Nginx、server `main`。
- 不标 API-01 / IMG-01 / IMG-02 / COMPOSE-01 / LEGEND-01 / RENDER-02 / PORTAL-01 `DONE`。

## 3. 在主路径中的位置

```text
API-01-R1  粗框架提示词 → 人 + ChatGPT → 骨架稿（不是 current）
        ↓
API-01-R2  完整对象提示词 → 人 + ChatGPT → 四对象候选 → Confirm current
        ↓
GRAPH-01   图谱初版（coverage + legend_role + 命题）
FORM-01    每节点形态建议 text | wordless-image | interactive
        ↑ 人改分类 / 补知识点：回到 R2 或手工补命题，新 Core revision
        ↓ 人改形态：只写 media-plan
FREEZE-01  排版冻结（mapping + media-plan）；Core 身份钉死
        ↓
IMG-03     按冻结的 image 节点导出无字提示词 → 人回填 PNG
COMPOSE / RENDER-02  投影；人锁定
        ↓
PUBLISH-02 / PORTAL  锁定包进画廊；浏览 / 下载 / 打印历史 revision
```

相对 ADR-002：阶段 1 生成 Core；阶段 2 确认 Projection Blueprint（含形态计划）；阶段 3 是 Renderer Binding；阶段 4 是 Artifact Package。新 Projection 不得新增 Core 中不存在的事实。

同一排版屏可以同时展示「改分类」和「改形态」。写入分叉：

| 操作 | 写入 | 冻结后的后果 |
| --- | --- | --- |
| 补知识点、改 `coverage_facet` / 分类 / 命题 | 新 `knowledge-core` revision，再 Confirm current | 已冻 media-plan 作废，必须重冻 |
| 改节点形态 text / wordless-image / interactive | `media-plan` 草稿 | 未冻可改；已冻须显式解冻或新 plan revision |
| 冻结排版 | mapping pointer + media-plan revision，钉 Core 六键身份 | 此后才导出请图提示词 |

操作者 2026-09-04 接受该分写。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 推理位置 | 人 + ChatGPT 会员（或同类平台）；服务器无 LLM |
| 两轮提示词 | R1 骨架不得 Confirm current；R2 才可入库 |
| 对象类型 | 用 KNOW-01 `primary_domain` × `primary_form` × `object_subtype` 选框架模板；一次一类型 |
| 首轮类型 | 恐龙 entity（对照旧剑龙模块种类） |
| 建议生图 | R2 回复可带节点建议；编译后进入 media-plan **建议**，不进命题正文 |
| 缺图 | 不拒 Confirm current；不拒 generate 文字四卡 |
| 图谱 | 只展示 current 上已有单元/命题/角色；空角色不出现 |
| 形态词表 | `text` / `wordless-image` / `interactive`；interactive 本里程碑只登记 |
| 冻结 | 扩展 WB-02 mapping-lock，附加 media-plan；不是新治理对象 |
| 请图键 | 冻结后的 `wordless-image` 节点，而不是 IMG-02 固定五键（五键可作默认建议） |
| 回填 | 无字 PNG + sha + Core 身份钉；缺槽不失败 |
| 投影锁定 | 人锁定的是带图投影 revision，不改 knowledge current |
| 画廊 | 只读已锁定 package 历史；ops 合成稿必须先 PUBLISH 才能上架 |
| 打印铬 | 不在本工作流首竖切；时间条/地图/比列尺另开切片 |
| 现网 | 不由本文件授权 |

## 5. 阶段合同

### 5.1 提示词（API-01-R1 / API-01-R2）

依赖已有 API-01 compile-intent：短输入 → 服务器扩可复制提示词 → 贴回复 → 解析。

R1 与 R2 **同一 intent 上的两个状态**，不是两条互不相干的 intent：

| 状态 | 扩出的提示词要求 ChatGPT 输出 | 解析成功后 | 失败 |
| --- | --- | --- | --- |
| `framework` | 覆盖面骨架：类型、拟议单元、每面是否有实例、未知/安全/来源缺口；禁止编造成年阶元或体长 | 存骨架稿；**禁止** set current | 保持 `framework`，可再贴 |
| `complete` | 与现 authoring 夹具同形的结构化稿；可另附 `image_suggestions[]`（必须能解析到已有 `proposition_id` → 建议画法） | 四对象候选；人 Confirm 才 current | 不入库 |

R1 提示词必须按对象类型问出 LEGEND-01 对照旧卡时该出现的面（恐龙：外形、可比部件、证据、时间、发现地、学习地若有实例、习性、类别、未知）。没有的面在骨架里标空，禁止为填满编造。

`image_suggestions` 编译规则：

- 只能指向**同一份**完整稿里已经写出的 `proposition_id`（不是 coverage 面名，也不是尚未成命题的 unit）；
- 未知/安全/来源/清场区不得建议生图；
- 建议默认 `wordless-image`；不得写成 Core `claim`。

R2 Confirm 后，系统用建议生成 **media-plan 草稿**（全部节点默认 `text`，被建议的改为 `wordless-image`）。人在排版阶段可改。

后续对象类型（哺乳动物、植物、地点、事件、定律）只换 R1 模板，不换两轮协议。

### 5.2 排版（GRAPH-01 / FORM-01 / FREEZE-01）

GRAPH-01：只读 current。图谱节点以命题为请图与形态单位；没有命题的 unit 只作分组，不能标 `wordless-image`。边用已有关系。每命题节点标注 `coverage_facet` 与 `assign_legend` 的 `legend_role`。无角色实例不画模块。

FORM-01：每节点一个形态。默认来自 R2 建议，否则 `text`。人可改。`interactive` 可选但冻结后阶段 3 忽略（不导出提示词、不失败）。

FREEZE-01：

1. 校验 media-plan 每个节点 id 都在 current 上；
2. 钉 `object_id` / `revision` / 四对象 sha / `final_content_lock_sha256`（与 illustration identity 同形）；
3. 与 mapping-lock 一起写成 library 元数据 revision；
4. 成功后才允许导出请图提示词。

Core 前进或 identity 不匹配 → 已冻计划 `stale`。解冻或新 plan。禁止静默沿用旧形态去请图。

人在同一屏点「补知识点」：不得 inline 改 Core JSON；须走新 compile 或明确的命题补丁入口（另刀），产出新 revision 后再刷新图谱。

### 5.3 视觉（IMG-03）

依赖 IMG-01 无字合同与身份钉。IMG-02 五键仍可作为某节点的**默认画法建议**，不再是唯一请图槽。

对每个冻结为 `wordless-image` 的节点：

- 服务器扩一份无字提示词（版本化模板，人不可改写正文合同）；
- 人复制、生图、回填 PNG；
- 未回填：投影跳过该图，模块仍可有文字。

观察卡才允许 `<img>`。知识卡继续无插图（RENDER-02）。hero isolate 仍可作 `observe` 节点的默认主图。

人锁定：在 compose 身份一致且 mapping+media-plan 未 stale 时，走 QA-01 语义的人工 `approve`（actor + 审计）。锁定的是投影工作区，不是 knowledge current。

### 5.4 画廊（PUBLISH-02）

锁定且 `approved` 的带图投影才能写成不可变 package revision（扩展 PUBLISH-01 消费面，不改 package 身份算法的既有闭包规则，除非另开 PUBLISH 切片写明）。

PORTAL-01 继续只读 public current 与历史 revision：列表、详情、下载、现有四页 PNG/PDF。ops 未发布的合成稿不出现在公开画廊。

## 6. 子刀与依赖

| ID | 阶段 | 依赖 | 本程序完成条件 |
| --- | --- | --- | --- |
| API-01-R1 | 提示词 | API-01 模板机制 | 恐龙类型粗框架提示词可复制；贴骨架稿不设 current |
| API-01-R2 | 提示词 | R1 骨架 | 完整 authoring 可 Confirm；`image_suggestions` 本刀进 intent 旁路，media-plan 草稿留给 FORM-01 |
| GRAPH-01 | 排版 | Confirm current、LEGEND-01 | 操作台显示分类/内容/角色；空角色缺席 |
| FORM-01 | 排版 | GRAPH-01 | 人可改三态形态；interactive 可登记 |
| FREEZE-01 | 排版 | FORM-01、WB-02 mapping | 冻结钉 Core 身份；之后才出请图词；Core 变则 stale |
| IMG-03 | 视觉 | FREEZE-01、IMG-01 无字合同 | 按节点导出/回填；缺槽不失败 |
| PUBLISH-02 | 画廊 | 人锁定投影、PUBLISH-01 | 锁定包可在画廊浏览/下载/打印历史 |

竖切顺序：R1 → R2 → GRAPH+FORM+FREEZE → IMG-03 投影锁定 → PUBLISH-02。对象类型轮次与打印铬、可交互运行时都排在恐龙竖切之后。

## 7. 错误与门禁

沿用 API-01 / mapping / illustration / compose 既有码。新增语义（具体码名在子刀 spec 钉死）：

| 语义 | 何时 |
| --- | --- |
| 骨架稿当完整对象入库 | R1 禁止 set current |
| 建议生图指向不存在的命题 | R2 编译失败 |
| 清场区/安全/未知被标 wordless-image | FORM 拒绝 |
| 用 stale plan 导出提示词或回填 | 失败关闭 |
| 知识卡 `<img>` | 沿用 RENDER-02 |

不新增「模块未出齐」「图未回填齐」为阻断码。

## 8. 验收（本文件，设计层）

1. 分类变更与形态变更在文中是两次写入。
2. R1 不能被描述为 Confirm current。
3. 建议生图不能被描述为 Knowledge Core 字段。
4. 子刀表完整，且声明本文件不实施。
5. 对照旧剑龙卡只验收模块种类的路径写进竖切，不把烧字像素写进完成条件。

子刀实现验收在各自 spec。本机隔离 library。不写生产 library。不打 release。

## 9. 实现落点

权威仓库：产品规范 `kids-visual-learning-pack`。server 实现须等本文件 Approved，且当前子刀 spec/计划落盘之后。

优先文档：本文件、路线图 `FLOW-01`、文档地图、系统总设计 §11 指针。

本文件不授权 merge server `main`、不授权现网、不授权把 FLOW-01 当一刀实施。API-01-R1 / API-01-R2 的实施授权只在各自切片 spec/计划里。R2 本刀把 `image_suggestions` 写在 intent 旁路；media-plan 草稿仍属 FORM-01。
