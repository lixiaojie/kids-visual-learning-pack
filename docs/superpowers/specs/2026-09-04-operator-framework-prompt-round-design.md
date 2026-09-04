# 对象类型粗框架提示词（API-01-R1）

- Status: Approved for this execution tranche
- Date: 2026-09-04
- Related: [FLOW-01](2026-09-04-operator-iterative-workflow-design.md)、[API-01](2026-09-02-operator-free-prompt-knowledge-compile-design.md)、[KNOW-01](2026-08-31-classification-registry-design.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)
- Does not implement: R2 完整 authoring / Confirm current；`image_suggestions`；media-plan；图谱；排版冻结；生图；OpenAI API；其他对象类型的 R1 模板；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

在已有 `compile-intent` 上增加**第一轮**：按对象类型扩一份可复制的粗框架提示词，收回一份骨架稿，存下来，**禁止**设为 knowledge current。

本刀只做一种类型：恐龙 entity。ChatGPT 仍在人的浏览器里。服务器不接模型 API。

质量标尺是旧 Skill 剑龙卡的**模块种类该问/该空**，不是编造阶元或体长，也不是完整四对象入库。

本设计满足路线图 `API-01-R1` 在本刀的范围。它叠加在 [API-01](2026-09-02-operator-free-prompt-knowledge-compile-design.md) 之上，不替换既有一轮完整编译路径。

## 2. 非目标

- 不扩 R2 完整 authoring 提示词，不解析 `cognitive-card-authoring-request-v1`，不写四对象候选，不 `confirm-current`。
- 不生成 `image_suggestions` 或 media-plan。
- 不接 OpenAI / 图像 API，不写 Skill claim。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05、KNOW-04 生产 library。
- 不因 `paleontology + entity + fossil-animal` 的 KNOW-01 `review` 单元格拒绝骨架（骨架不走 `compile_authoring_request`）。
- 不自动从 slug 或中文名猜对象类型。操作员必须显式选择。
- 不实施哺乳动物 / 植物 / 地点 / 事件 / 定律的框架模板。
- 不 merge/push/release，不 reload Nginx，不标 API-01 / FLOW-01 / RENDER-02 `DONE`。

## 3. 在主路径中的位置

```text
本刀·短输入     slug + subject + goal + object_type=dinosaur-entity
本刀·扩提示词   恐龙框架模板 → 可复制完整提示词（round=framework）
        ↓
人 · ChatGPT    复制提问
        ↓
本刀·贴回复     解析 knowledge-framework-v1 骨架
本刀·状态       framework；禁止 Confirm current
        ↓
API-01-R2（另刀）同一 intent 再扩完整对象提示词
```

缺省不传 `object_type`（或空串）：行为与现 API-01 完全相同（`round=complete`，`knowledge-compile-v1`，可贴 authoring，可 Confirm）。本刀不得破坏 `cat` 夹具路径。

相对 FLOW-01：R1 与 R2 是**同一 intent 上的两个 round**。本刀只把 round 推进到 `framework`。R2 另立切片。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 对象类型键 | 封闭小写蛇形。本刀仅 `dinosaur-entity`。未知键 → `COMPILE_OBJECT_TYPE_UNKNOWN` |
| 分类映射 | `dinosaur-entity` = `paleontology` + `entity` + `fossil-animal`（KNOW-01 词表；不在本刀改注册表） |
| 提示词模板 | `knowledge-compile-framework-dinosaur-entity-v1`；创建时快照 id+sha；人不可改写正文 |
| 骨架 schema | `cognitive-card-knowledge-framework-v1` |
| 图例槽 | 必须恰好列出：`observe` `compare` `evidence` `time` `place` `learning_place` `habit` `kind` `uncertain` |
| 槽状态 | 每槽 `has_instance` 或 `empty`；空槽禁止为填满编造 |
| 学习地 | 默认可 `empty`；只有回复声称有实例才 `has_instance` |
| 拟议单元 | 可有 slug/title/可选 coverage_facet；**不得**带 `propositions` / `claim` |
| 缺口 | `gaps.unknown` / `gaps.safety` / `gaps.sources` 为字符串列表，允许空 |
| 入库 | 骨架写入 intent 旁 `framework.json`；不写 `candidate/` 四对象 |
| Confirm | `state=framework` 或 `round=framework` 且尚未 `compiled` → `COMPILE_FRAMEWORK_NOT_CURRENT` |
| 既有路径 | 省略 `object_type` 时零行为变化 |

## 5. 创建 intent

沿用 API-01：`POST /card-os/api/v1/admin/knowledge-compile`。短输入仍不可变。新增可选字段：

| 字段 | 规则 |
| --- | --- |
| `object_type` | 省略或 `""` → 既有完整编译。`dinosaur-entity` → 本刀框架模板。其他非空 → `COMPILE_OBJECT_TYPE_UNKNOWN` |

`dinosaur-entity` 创建成功后：

- `state` = `open`（等待贴骨架）
- `round` = `framework`
- `object_type` = `dinosaur-entity`
- `prompt_template_id` = `knowledge-compile-framework-dinosaur-entity-v1`
- `expanded_prompt` 来自该模板，填入 `subject` / `goal` / `topic_slug`
- slug / actor / 幂等 / `COMPILE_SLUG_*` / `COMPILE_INTENT_ACTIVE` 规则不变
- 幂等相同键须连 `object_type` 一起比；缺省与 `"dinosaur-entity"` 视为不同 body

非终态集合加入 `framework`：骨架已接受但未取消时，同一 slug 不得另开 intent。

## 6. 提示词模板

模板是服务器受治理文件。恐龙框架提示词必须要求 ChatGPT：

1. 只输出一份 JSON，`schema` 为 `cognitive-card-knowledge-framework-v1`；可围栏；不得第二份对象。
2. `topic.slug` 等于给定 slug。
3. `object_type` 为 `dinosaur-entity`。
4. `classification` 五键必须是 paleontology / [] / entity / [] / fossil-animal。
5. 列出 §4 九个 `legend_slots`，每个 `legend_role` + `status`（`has_instance`|`empty`）+ 可选短 `note`。
6. `proposed_units` 只描述拟议分组，不要命题句。
7. 没有的面标 `empty`。禁止为填满编造成年阶元、体长、林奈强制阶、三视图、化石点坐标。
8. 不要输出 authoring-request、四卡槽、COPY、字号、`image_suggestions`。
9. `gaps` 记录未知 / 安全 / 来源缺口；不确定就写进 unknown，不要编造 locator。

已创建 intent 继续用创建时快照，不随新模板漂移。

## 7. 贴回复

`POST .../reply` 在 `round=framework` 且 `state` ∈ {`open`,`failed`} 时走骨架解析，不走 `parse_authoring_reply` / `compile_authoring_request`。

成功：

- 写出 `framework.json`（canonical JSON）
- `state` = `framework`
- `error` = null
- 不得存在 `candidate/` 四对象文件

失败（结构不符、slug 不符、缺槽、多槽、带 `propositions`/`claim`、schema 不是框架）：`state=failed`，`COMPILE_REPLY_INVALID`（或既有过大码），library 不变。

`round=complete` 的 intent 行为与 API-01 相同。把完整 authoring 贴到 framework intent → 解析失败关闭。

`framework` 后再贴回复：本刀不允许（不在 `_REPLYABLE`）。要重做骨架：`return` → `open`，丢弃 `framework.json`。取消：`cancelled`，丢弃骨架。

## 8. 骨架合同

```json
{
  "schema": "cognitive-card-knowledge-framework-v1",
  "topic": {"slug": "stegosaurus", "title": "剑龙"},
  "object_type": "dinosaur-entity",
  "classification": {
    "primary_domain": "paleontology",
    "secondary_domains": [],
    "primary_form": "entity",
    "secondary_forms": [],
    "object_subtype": "fossil-animal"
  },
  "proposed_units": [
    {"slug": "body", "title": "背部骨板", "coverage_facet": "appearance"}
  ],
  "legend_slots": [
    {"legend_role": "observe", "status": "has_instance", "note": ""},
    {"legend_role": "compare", "status": "has_instance", "note": ""},
    {"legend_role": "evidence", "status": "has_instance", "note": ""},
    {"legend_role": "time", "status": "empty", "note": "do not invent stage"},
    {"legend_role": "place", "status": "has_instance", "note": ""},
    {"legend_role": "learning_place", "status": "empty", "note": ""},
    {"legend_role": "habit", "status": "has_instance", "note": ""},
    {"legend_role": "kind", "status": "has_instance", "note": ""},
    {"legend_role": "uncertain", "status": "has_instance", "note": ""}
  ],
  "gaps": {
    "unknown": ["adult length not used as a required fact"],
    "safety": [],
    "sources": []
  }
}
```

校验失败关闭，不发明缺字段。额外顶层键丢弃。`proposed_units` 允许空列表。`legend_slots` 必须恰好九个角色、顺序不限、不得重复。

GET intent 在 `state=framework` 时附带 `framework` 对象（磁盘骨架），无四对象 `preview`。无 token 的 HTML 源码不得含提示词或骨架正文。

## 9. 操作台

`/card-os/ops/compile` 表单增加可选 `object_type`：默认空（一轮完整编译）；选项 `dinosaur-entity`（恐龙框架）。HTML 壳仍不内嵌提示词。

`/card-os/ops/compile/{intent_id}`：`framework` 时 Confirm 保持 disabled；展示骨架 JSON 预览（经 admin JSON）。可 Return / Cancel。文案标明第二轮不在本刀。

## 10. 错误

| 码 | 何时 | HTTP |
| --- | --- | --- |
| `COMPILE_OBJECT_TYPE_UNKNOWN` | 非空且不是 `dinosaur-entity` | 400 |
| `COMPILE_FRAMEWORK_NOT_CURRENT` | 对 framework 未 compiled 的 intent 调用 confirm-current | 409 |
| `COMPILE_REPLY_INVALID` | 骨架不合 §8 | 400（状态 `failed`） |

其余 `COMPILE_*` 沿用 API-01。

## 11. 验收

1. 省略 `object_type` 的 `cat` 创建 / 贴回复 / Confirm 与本刀之前相同。
2. `object_type=dinosaur-entity` 扩出的提示词含九个角色名，且禁止编造成年阶元与体长。
3. 合法骨架 → `state=framework`，有 `framework.json`，无 `candidate/`，library 无 current。
4. 该状态下 confirm-current → `COMPILE_FRAMEWORK_NOT_CURRENT`，library 仍空。
5. 缺槽、带 claim、authoring schema 贴到 framework intent → `failed`，不入库。
6. 未知 `object_type` → 创建失败，无 intent。
7. ops HTML 无 token 时源码不含框架提示词。
8. 本机隔离 library。不写生产 library。不打 release。

对照旧剑龙卡：本刀只验收提示词是否问到该问的模块，以及空面能否标 empty。不验收完整知识卡像素。
