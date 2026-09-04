# 对象类型完整提示词第二轮（API-01-R2）

- Status: Approved for this execution tranche
- Date: 2026-09-04
- Related: [FLOW-01](2026-09-04-operator-iterative-workflow-design.md)、[API-01-R1](2026-09-04-operator-framework-prompt-round-design.md)、[API-01](2026-09-02-operator-free-prompt-knowledge-compile-design.md)、[KNOW-01](2026-08-31-classification-registry-design.md)、[KNOW-03](2026-09-01-entity-knowledge-coverage-design.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)
- Does not implement: media-plan library 文件；GRAPH / FORM / FREEZE；人改形态 UI；OpenAI API；其他对象类型模板；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`
- Supersedes: KNOW-01 / KNOW-03 将 `paleontology + entity + fossil-animal` 标为 `review` 的部分。`paleontology + evidence-record + dinosaur` 仍为 `review`。霸王龙夹具继续用 `paleontology + entity + dinosaur`，本刀不改。

## 1. 目标

在已有恐龙 entity `compile-intent` 上增加**第二轮**：操作员在接受的骨架上显式点「开始第二轮」，服务器扩一份内嵌该骨架的完整 authoring 提示词；人把 ChatGPT 回复贴回来，编译四对象候选，**可以** Confirm current。

可选的 `image_suggestions[]` 校验后只写在 intent 旁路，不进 Knowledge Core，本刀不写 media-plan 文件。FORM-01 再把这份建议收成草稿。

ChatGPT 仍在人的浏览器里。服务器不接模型 API。

省略 `object_type` 的一轮 `cat` 路径行为与本刀之前相同。

本设计满足路线图 `API-01-R2` 在本刀的范围。它叠加在 [API-01-R1](2026-09-04-operator-framework-prompt-round-design.md) 之上，不替换既有一轮完整编译。

相对 FLOW-01 §5.1：程序写「Confirm 后生成 media-plan 草稿」。本刀收窄为 intent 旁路保存建议；library 旁路 media-plan 文件留给 FORM-01。

## 2. 非目标

- 不写 `media-plan` library 元数据，不冻结排版，不画图谱，不提供改形态 UI。
- 不接 OpenAI / 图像 API，不写 Skill claim。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05、KNOW-04 生产 library。
- 不自动从 slug 猜对象类型。
- 不实施哺乳动物 / 植物 / 地点 / 事件 / 定律的完整模板。
- 不把「建议生图未填」「模块未出齐」写成 Confirm 门禁。
- 不 merge/push/release，不 reload Nginx，不标 API-01 / API-01-R1 / FLOW-01 / RENDER-02 `DONE`。

## 3. 在主路径中的位置

```text
API-01-R1     dinosaur-entity → 骨架 → state=framework（禁止 Confirm）
        ↓
本刀·advance  同一 intent；扩完整提示词（内嵌 framework JSON）
本刀·贴回复   解析 authoring；剥 image_suggestions；四对象候选
本刀·Confirm  compiled → current（与 API-01 相同）
        ↓
FORM-01（另刀）读取 intent 旁路建议，写成 media-plan 草稿
```

缺省不传 `object_type`：无 `advance`、无骨架内嵌、无 `image_suggestions.json`。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 同一 intent | R1 与 R2 不是两条 intent。短输入创建后仍不可变 |
| 进入 R2 | 仅 `state=framework` 可 `POST .../advance`。不自动换提示词 |
| 完整模板 | `knowledge-compile-complete-dinosaur-entity-v1`；创建/advance 时快照 id+sha |
| 骨架内嵌 | 完整提示词填入 canonical `framework.json`；有实例的槽才写命题；空槽 unresolved；禁止补编空槽、成年阶元、体长 |
| 分类 | 回复五键必须与骨架一致：paleontology / [] / entity / [] / fossil-animal |
| KNOW-01 | 该单元格改为 `enabled`。`evidence-record + dinosaur` 仍 `review` |
| 建议生图 | 回复顶层可选 `image_suggestions[]`；编译前剥离；写入 `image_suggestions.json` |
| media-plan | 本刀不写 |
| Confirm | `round=complete` 且 `state=compiled` 走既有 `confirm-current`。`round=framework` 仍 409 |
| 回到骨架 | 新动作 `POST .../return-framework`：恢复 R1 提示词，`state=framework`，丢掉候选与建议，保留 `framework.json` |
| 既有 Return | `round=complete` 时只丢掉候选/建议并保持完整提示词，**不**删骨架。`round=framework` 行为与 R1 相同（删骨架，回到 `open`） |
| 既有路径 | 省略 `object_type` 时零行为变化 |

## 5. 状态机

恐龙 entity 路径：

```text
open / round=framework
  → reply 骨架 → framework | failed
framework
  → advance → open / round=complete（保留 framework.json；expanded_prompt 换成完整稿）
  → return → open / round=framework（删除 framework.json）
  → confirm → COMPILE_FRAMEWORK_NOT_CURRENT
open / round=complete
  → reply authoring → compiled | failed
compiled / round=complete
  → confirm-current → current
  → return → open / round=complete（删候选与建议；保留骨架与完整提示词）
  → return-framework → framework（见 §8）
failed / round=complete
  → 再贴回复
  → return-framework → framework
current 终态。cancelled 终态。
```

`advance` 失败关闭，不改磁盘，若：`state` 不是 `framework`、没有 `framework.json`、`object_type` 不是 `dinosaur-entity`。

一轮 `cat` 路径没有 `framework_*` 快照，调用 `advance` 或 `return-framework` → 对应错误码，intent 不变。

## 6. 开始第二轮

`POST /card-os/api/v1/admin/knowledge-compile/{intent_id}/advance`

Body：`{"actor": "<human>"}`。actor 规则与 reply 相同。

成功：

1. 把当前 `prompt_template_id` / `prompt_template_sha256` / `expanded_prompt` 拷到 `framework_prompt_template_id` / `framework_prompt_template_sha256` / `framework_expanded_prompt`（若尚未拷过）。
2. 用完整模板填 `subject` / `goal` / `topic_slug` / `framework_json`（磁盘骨架的 canonical JSON）。
3. `round=complete`，`state=open`，`error=null`。
4. 不删 `framework.json`。不写 `candidate/`。

幂等：同一 intent 已是 `round=complete` 且完整模板快照已在 → 返回当前 intent，不二次扩词。`state=framework` 是唯一会改写提示词的成功入口。

## 7. 提示词模板

模板是服务器受治理文件。恐龙完整提示词必须要求 ChatGPT：

1. 只输出一份 JSON。顶层 `schema` 为 `cognitive-card-authoring-request-v1`；可围栏；不得第二份对象。
2. `topic.slug` 等于给定 slug。
3. `classification` 五键必须与内嵌骨架相同，不得改成 `dinosaur` subtype 或 `evidence-record`。
4. 内嵌骨架是覆盖合同：`legend_slots` 里 `has_instance` 的面必须有命题；`empty` 的面标 unresolved / 缺口，禁止为填满编造。
5. 禁止编造成年阶元、体长、林奈强制阶、化石点精确坐标、体色/软组织/声音/速度的 `established` 主张（沿用 palontology overlay）。
6. 不要写四卡槽、COPY、字号、`projection` 填值。
7. 用网页搜索写 `intake.method=search`（与现 API-01 相同）。
8. 可选顶层 `image_suggestions`：数组；每项 `proposition_id` 必须是**同一份**稿里已有的命题；`form` 只能是 `wordless-image`（可省略，默认该值）；可选短 `note`。不要把建议写进 `canonical_claim`。

已 advance 的 intent 继续用当时快照，不随新模板漂移。

## 8. 回到骨架

`POST /card-os/api/v1/admin/knowledge-compile/{intent_id}/return-framework`

无 body（与既有 `/return` 相同）。

允许：`round=complete` 且 `state` ∈ {`open`,`failed`,`compiled`}，且磁盘仍有 `framework.json`，且 intent 上有 `framework_expanded_prompt`。

成功：

- 恢复三份 `framework_prompt_*` 到当前 `prompt_template_*` / `expanded_prompt`
- `round=framework`，`state=framework`，`error=null`，`revision=null`
- 删除 `candidate/` 与 `image_suggestions.json`
- **保留** `framework.json`

`state=current` → `COMPILE_ALREADY_CURRENT`。一轮完整编译或尚未 advance → `COMPILE_RETURN_FRAMEWORK_INVALID`。

既有 `POST .../return`：

| 当时 round | 行为 |
| --- | --- |
| `framework` | 与 R1 相同：删骨架，`state=open`，提示词仍是框架模板 |
| `complete` | 删候选与 `image_suggestions.json`；**保留**骨架；提示词仍是完整模板；`state=open`，`round=complete` |

既有 `cancel`：删骨架、候选、建议；`cancelled`。

## 9. 贴回复（完整 round）

`round=complete` 且 `state` ∈ {`open`,`failed`} 走 authoring 解析，不走 `parse_framework_reply`。

成功：

1. 从解析对象剥离 `image_suggestions`（缺省当 `[]`）。
2. 按 §10 校验建议；失败则整次回复 `failed`，不写候选。
3. 剩余对象必须通过既有 `parse_authoring_reply` / search intake / `compile_authoring_request(..., allow_search=True)`。因本刀已把该分类单元格改为 `enabled`，不得再因 `CLASSIFICATION_REVIEW` 拒绝恐龙 entity。
4. 写出四对象 `candidate/`。
5. 写出 `image_suggestions.json`（canonical 数组，可空）。
6. `state=compiled`。

把骨架稿贴到 `round=complete` → `COMPILE_REPLY_INVALID`，`failed`。把 authoring 贴到 `round=framework` → 仍按 R1 失败关闭。

## 10. 建议生图合同

```json
[
  {
    "proposition_id": "p_plates",
    "form": "wordless-image",
    "note": "dorsal plates, no glyphs"
  }
]
```

校验失败关闭（`COMPILE_IMAGE_SUGGESTION_INVALID`）：

- `proposition_id` 不是字符串，或不在同一份稿的 `propositions` 里；
- 同一 `proposition_id` 出现两次；
- `form` 出现且不是 `wordless-image`；
- 目标命题所在 unit 的 `coverage_facet` 为 `safety`；
- 目标命题 `fact_type` 为 `safety` 或 `unknown_boundary`。

额外键丢弃。`note` 可省略；出现时必须是字符串。空数组合法。

建议不得写入四对象任何字段。Confirm current 不读、不写、不复制这份文件进 library。

GET `/admin/knowledge-compile/{intent_id}`：磁盘有 `framework.json` 时附带 `framework`（不限 `state=framework`）。磁盘有 `image_suggestions.json` 时附带 `image_suggestions`。`state=compiled` 仍附带既有四对象 `preview`。

## 11. 操作台

`/card-os/ops/compile/{intent_id}`：

| 状态 | Confirm | 主提示词 | 额外动作 |
| --- | --- | --- | --- |
| `framework` | disabled | 框架提示词 | 开始第二轮；Return；Cancel |
| `open`/`failed` 且 `round=complete` | disabled | 完整提示词 | 贴回复；回到骨架；Return；Cancel |
| `compiled` 且 `round=complete` | enabled | 完整提示词 | Confirm；回到骨架；Return；Cancel |
| 一轮 `cat` compiled | enabled | `knowledge-compile-v1` | 无第二轮按钮 |

`framework` 与 `round=complete` 都展示骨架 JSON 预览（经 admin JSON）。`compiled` 另展示建议数组（可空）。无 token 的 HTML 源码不得含提示词、骨架或建议正文。

## 12. 错误

| 码 | 何时 | HTTP |
| --- | --- | --- |
| `COMPILE_ADVANCE_NOT_FRAMEWORK` | 对非 `framework` 调 advance（含一轮 cat） | 409 |
| `COMPILE_RETURN_FRAMEWORK_INVALID` | 对非完整 round、无骨架快照、或无 `framework.json` 调 return-framework | 409 |
| `COMPILE_IMAGE_SUGGESTION_INVALID` | §10 校验失败 | 400（状态 `failed`） |
| `COMPILE_FRAMEWORK_NOT_CURRENT` | 对尚未 compiled 的 framework intent 调 confirm-current | 409 |
| `CLASSIFICATION_REVIEW` | 不得再由 `paleontology + entity + fossil-animal` 触发。`evidence-record + dinosaur` 仍可 | 400 |

其余 `COMPILE_*` 沿用 API-01 / R1。

## 13. 验收

1. 省略 `object_type` 的 `cat` 创建 / 贴回复 / Confirm / 无 advance 与本刀之前相同。
2. `state=framework` 上 advance → `round=complete`，完整提示词含骨架 JSON 与 authoring schema，骨架文件仍在，library 无 current。
3. 合法 authoring（可无建议）→ `compiled`，有四对象候选；Confirm 后该 slug 有 current。
4. 建议指向不存在的命题、或 `safety` 面 → `failed`，无候选，library 空。
5. 建议在 Confirm 前后都不出现在 `knowledge-core.json`。
6. return-framework → `state=framework`，R1 提示词恢复，候选与建议删除，骨架仍在；此时 confirm 仍 409。
7. `round=complete` 的既有 Return 不删骨架。
8. 未知类型、R1 骨架路径、无 token HTML 不含提示词：回归保持。
9. `coverage_status("paleontology","entity","fossil-animal")` 为 `enabled`；`("paleontology","evidence-record","dinosaur")` 仍为 `review`。
10. 本机隔离 library。不写生产 library。不打 release。

对照旧剑龙卡：本刀验收完整对象能否按骨架面写命题，以及空面能否保持 unresolved。不验收打印像素，不验收图谱。
