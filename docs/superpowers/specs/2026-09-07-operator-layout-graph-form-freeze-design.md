# 操作台排版：图谱、形态、冻结（GRAPH-01 / FORM-01 / FREEZE-01）

- Status: Approved for this execution tranche
- Date: 2026-09-07
- Related: [FLOW-01](2026-09-04-operator-iterative-workflow-design.md)、[API-01-R2](2026-09-04-operator-complete-prompt-round-design.md)、[API-01](2026-09-02-operator-free-prompt-knowledge-compile-design.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[LIB-01](2026-08-30-knowledge-library-revision-current-design.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[IMG-01](2026-09-02-operator-illustration-hero-page-design.md)、[KNOW-03](2026-09-01-entity-knowledge-coverage-design.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)
- Does not implement: IMG-03 请图导出 / PNG 回填；OpenAI API；canvas 图谱；第五个治理对象；改 `lock_mapping`；改 Confirm current；inline 改 Core；可交互运行时；打印铬；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`。FLOW-01 仍是程序级工作流；本文件是 GRAPH+FORM+FREEZE 竖切的实施授权。

## 1. 目标

Confirm current 之后，操作员在**新的排版页**上看到 current 的分类 / 内容 / 角色大纲，按命题改形态，并在已有 mapping-lock 的前提下**冻结**排版。

形态只写 library 元数据 `media-plan`，不写 Knowledge Core。冻结钉 current 六键身份与 mapping revision。此后才允许 IMG-03（另刀）导出请图提示词。本刀不导出提示词、不收回 PNG。

ChatGPT 仍在人的浏览器里。服务器不接模型 API。

本设计满足路线图 `GRAPH-01` / `FORM-01` / `FREEZE-01` 在本刀的合并范围。它叠加在 [API-01-R2](2026-09-04-operator-complete-prompt-round-design.md) 与 [WB-02](2026-09-01-operator-mapping-scheme-design.md) 之上。

相对 FLOW-01 §5.2：程序写「R2 Confirm 后生成 media-plan 草稿」。R2 已收窄为 intent 旁路。本刀在**第一次 layout GET** 时从 current 命题 + 该 slug 最近一次 Confirm 的 compile-intent `image_suggestions.json` 写成草稿。Confirm 路径仍不写 media-plan。

## 2. 非目标

- 不导出无字请图提示词，不上传 PNG，不改 illustration-intent。
- 不接 OpenAI / 图像 API，不写 Skill claim。
- 不改 `lock_mapping`、mapping 预览、mapping 第三块 HTML/JS。
- 不改 Confirm current：不把 suggestions 拷进 library，不在 Confirm 时写 `media-plan.json`。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05、KNOW-04 生产 library。
- 不新增第五个治理对象。`media-plan.json` 与 `mapping.json` 同属 library 元数据。
- 不把 media-plan 节点写进四对象 `revision-NNNN/` 包目录。
- 不画 SVG/canvas 图谱；不实现可交互页运行时。
- 不 inline 改 Core JSON；「补知识点」只链到 compile。
- 不把「模块未出齐」「图未回填齐」写成 Confirm 或 freeze 门禁。
- 不 merge/push/release，不 reload Nginx，不标 API-01 / API-01-R1 / API-01-R2 / FLOW-01 / IMG-03 / RENDER-02 `DONE`。
- 不修 ops mapping-lock `LEGEND_ROLE_MISSING`。

## 3. 在主路径中的位置

```text
API-01-R2     Confirm current（不写 media-plan）
        ↓
WB-02         lock_mapping（既有页；本刀不改）
        ↓
本刀·GET      /ops/layout/{topic} → 无 pointer 则建 draft
本刀·PATCH    改节点形态（仅 draft）
本刀·Freeze   要求 listed mapping；写 frozen revision；钉身份
        ↓
IMG-03（另刀）仅 status=frozen 且身份未 stale 才导出请图词
```

冻结**要求**已有 mapping-lock。Layout 页 Freeze 在 `mapping_listed=false` 时禁用。Mapping 仍在知识详情第三块完成。

同一 layout 页同时展示分类（只读）与形态（可改）。写入分叉不变：分类/命题变更走新 compile → 新 current → 已冻计划 stale；形态变更只写 media-plan。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 切片 | GRAPH-01 + FORM-01 + FREEZE-01 一刀；不是三份独立实施授权 |
| 冻结与 mapping | Freeze 要求 listed `mapping.json`；不改 `lock_mapping` |
| 存储 | `{topic}/media-plan.json` pointer + `{topic}/media-plans/revision-NNNN.json` |
| 草稿时机 | 该 topic 第一次 layout GET 且无 pointer 时创建；Confirm 不写 |
| 建议来源 | `state=current` 且 `topic_slug` 匹配的 compile-intent 中，最近一次 Confirm 的 `image_suggestions.json` |
| 排版页 | 新页 `/card-os/ops/layout/{topic}`；非 canvas |
| 图谱 | 按 `legend_role` 分组（空角色缺席）；unit 嵌套；命题行；关系为节点上的文本 |
| 形态词表 | `text` / `wordless-image` / `interactive`；`interactive` 可登记，本刀不导出提示词 |
| 解冻 | 冻结 revision 不可变；Unfreeze 拷到新 draft revision |
| stale | GET 计算；不因 GET 改写 pointer 文件 |
| 补知识点 | 链到 `/card-os/ops/compile`；禁止 inline Core |
| 现网 | 不由本文件授权 |

## 5. 目录与 schema

```text
{library_root}/{topic_slug}/
  current.json
  mapping.json
  media-plan.json
  media-plan-audit.jsonl
  media-plans/
    revision-NNNN.json
  revision-NNNN/          # 四对象包；本刀不往这里写 media-plan
```

`NNNN` 为零填充四位。写入用临时文件 + `os.replace`。禁止覆盖已存在的 `media-plans/revision-NNNN.json`。禁止跟随符号链接。

### 5.1 Pointer `media-plan.json`

```json
{
  "schema": "cognitive-card-knowledge-library-media-plan-v1",
  "topic_slug": "stegosaurus",
  "revision": 1,
  "status": "draft",
  "identity": null,
  "mapping_revision": null,
  "source_current_revision": 2,
  "source_compile_intent_id": "ci_ab12",
  "set_at": "2026-09-07T00:00:00Z",
  "reason": "create_draft"
}
```

| 字段 | 规则 |
| --- | --- |
| `status` | 磁盘上仅为 `draft` 或 `frozen`。`stale` 只出现在 GET 响应 |
| `identity` | `draft` 为 `null`。`frozen` 为 current 的六键：`object_id`、`revision`、`knowledge_core_sha256`、`learning_spec_sha256`、`projection_spec_sha256`、`final_content_lock_sha256`（与 illustration-intent / `LibraryRevision.identity` 同形） |
| `mapping_revision` | `draft` 为 `null`。`frozen` 为当时 `mapping.json.revision`（整数） |
| `source_current_revision` | 创建或冻结时 `get_current` 的 revision 号 |
| `source_compile_intent_id` | 建草稿时用到的 intent；没有则 `null` |
| `reason` | `create_draft` / `patch` / `freeze` / `unfreeze` |

### 5.2 Plan file `media-plans/revision-NNNN.json`

```json
{
  "schema": "cognitive-card-media-plan-revision-v1",
  "topic_slug": "stegosaurus",
  "revision": 1,
  "status": "draft",
  "nodes": [
    {"proposition_id": "p_plates", "form": "wordless-image"}
  ],
  "source_compile_intent_id": "ci_ab12",
  "created_at": "2026-09-07T00:00:00Z",
  "actor": "owner"
}
```

`nodes[].form` ∈ {`text`, `wordless-image`, `interactive`}。同一 `proposition_id` 不得出现两次。额外键丢弃。

**Draft 文件可被 PATCH 原地替换**（同一 `revision` 号，原子替换）。**Frozen 文件禁止覆盖。** 下一号 = 已有 `media-plans/revision-*.json` 的最大号 + 1。

### 5.3 审计

每次 create_draft / patch / freeze / unfreeze 追加一行 `media-plan-audit.jsonl`：`set_at`、`actor`、`reason`、`revision`、`status`。只追加，不改历史行。

## 6. 状态机

Pointer 磁盘 `status`：`draft` | `frozen`。响应 `status`：`draft` | `frozen` | `stale`。

```text
no pointer
  → GET layout（有 current）     创建 revision-0001 draft
  → GET layout（无 current）     listed=false，HTTP 200，不建文件
  → PATCH / freeze / unfreeze    LAYOUT_NO_CURRENT

draft
  → PATCH                        原地写同一 draft 文件
  → Freeze                       要求 listed mapping；写下一号 frozen；钉身份
  → GET                          大纲来自今日 current；形态来自 draft
  → Unfreeze                     MEDIA_PLAN_NOT_FROZEN

frozen
  → PATCH / Freeze               MEDIA_PLAN_NOT_DRAFT
  → Unfreeze                     拷节点 → 新 draft；pointer 前进；清 identity
  → GET                          若身份或 mapping revision 漂移 → 响应 status=stale
  → GET 未漂移                   status=frozen

stale（仅响应）
  → PATCH / Freeze               MEDIA_PLAN_STALE 或 MEDIA_PLAN_NOT_DRAFT
  → Unfreeze                     允许：从该 frozen 快照拷新 draft
```

GET **不**把 pointer 改写成 `stale`。IMG-03（另刀）必须在导出前复算；本刀 Freeze 在响应已是 stale 时拒绝。

## 7. 大纲（GRAPH-01）

只读 **library current**。不把大纲存成图文件。

输入：`get_current` 四对象。`standing` 缺省 `active`；`superseded` 不进大纲、不进冻结快照。

1. 对每条 active 命题调用既有 `assign_legend`。解析失败的命题仍出现在所属 unit 下，`legend_role` 为 `null`；不因此 500；不放宽 mapping-lock 图例门禁。
2. 按 LEGEND-01 角色表顺序分组。零命题的角色**不出现**。`source` 角色不建形态节点（来源不是命题）。
3. 组内按 `knowledge_units` 嵌套。没有命题的 unit 只作分组标题，无 form 控件，不能标 `wordless-image`。
4. 命题行字段：`proposition_id`、`claim`（current 原文）、`coverage_facet`（所在 unit）、`legend_role`、`form`、`related[]`（current `relations` 里指向其他命题的 id，文本即可）。
5. 顶部只读：classification 五键（若有）、mapping listed 与 revision、media-plan `status` / revision。

关系不是可编辑边。禁止为填满而发明角色或命题。

## 8. 草稿创建（第一次 GET）

当 topic **有 current** 且 **无** `media-plan.json`：

1. 收集 current 全部 active `proposition_id`，默认 `form=text`。
2. 查找建议 intent：扫描 `compile-intents/*/intent.json`，过滤 `topic_slug` 相等且 `state=current`。多条时取 `revision` 最大（Confirm 写入的 library revision）；并列取 `set_at` 最新；再并列取 `intent_id` 字典序最大。
3. 若找到且磁盘有 `image_suggestions.json`：对仍存在于 current active 集合的 `proposition_id`，把 `form` 设为 `wordless-image`（sidecar 已禁止其他 form）。未知 id 忽略。
4. 写 `media-plans/revision-0001.json`（或下一号，若目录里已有文件）、`media-plan.json`、审计行。
5. 返回大纲 + 该草稿。

有 pointer 时 GET **不**重建草稿，即使 current 已变。

无 current：`listed=false`，HTTP 200，不创建文件。响应不含命题正文。

## 9. PATCH（FORM-01）

`PATCH /card-os/api/v1/admin/knowledge-library/{topic}/media-plan`

Body：`{"actor": "<human>", "nodes": [{"proposition_id": "...", "form": "text|wordless-image|interactive"}]}`。

Actor 规则与 mapping-lock / confirm-current 相同：非空人类，禁止机器名。

仅 `status=draft`。只改列出的 id；未列出的节点保持。`proposition_id` 必须是 **current active** 命题，否则 `MEDIA_PLAN_NODE_UNKNOWN`，文件不变。

禁止 `wordless-image` 与 `interactive` 当：

- 所在 unit `coverage_facet` ∈ {`safety`, `unknown`}；
- 命题 `fact_type` ∈ {`safety`, `unknown_boundary`}；
- 目标不是命题（来源行）。

命中 → `MEDIA_PLAN_FORM_FORBIDDEN`，400，文件不变。

原地原子替换当前 draft 文件；pointer `reason=patch`，`revision` 不变；审计一行。

`interactive` 合法节点可保存。本刀不为其导出提示词，冻结后阶段 3（另刀）忽略该节点的请图，不失败。

## 10. Freeze

`POST /card-os/api/v1/admin/knowledge-library/{topic}/media-plan-freeze`

Body：`{"actor": "<human>"}`。

失败关闭（不写新 revision），若：

| 条件 | 码 |
| --- | --- |
| 无 current | `LAYOUT_NO_CURRENT` |
| pointer 不是 draft（含已冻 / stale） | `MEDIA_PLAN_NOT_DRAFT` |
| `mapping.json` 不存在或不 listed | `MEDIA_PLAN_MAPPING_REQUIRED` |
| 物化后任一节点形态禁止 | `MEDIA_PLAN_FORM_FORBIDDEN` |

成功：

1. **物化快照**：每个 current active 命题一行。形态取 draft 中该 id，缺省 `text`。Draft 里不在 current 的 id **不拷进** frozen 文件。
2. 再跑禁止形态校验。
3. 写下一号 `media-plans/revision-NNNN.json`，`status=frozen`，禁止之后覆盖该文件。
4. Pointer：`status=frozen`，`identity` = 此刻 `get_current().identity` 六键，`mapping_revision` = `mapping.json.revision`，`source_current_revision` = current revision，`reason=freeze`。
5. `current.json` 与 `mapping.json` 字节不变。
6. 审计一行。

本刀成功后**不**调用 illustration 扩词。Freeze 只打开 IMG-03 的门；本刀测试不得依赖请图路由。

## 11. Unfreeze 与 stale

`POST /card-os/api/v1/admin/knowledge-library/{topic}/media-plan-unfreeze`

Body：`{"actor": "<human>"}`。

允许 pointer 磁盘 `status=frozen`（含 GET 会报 stale 的情况）。无 pointer 或磁盘 `draft` → `MEDIA_PLAN_NOT_FROZEN`。

成功：拷该 frozen 文件的 `nodes` 到下一号 draft；pointer 改为 draft；`identity` 与 `mapping_revision` 置 `null`；`reason=unfreeze`。旧 frozen 文件保留。

**stale 计算**（GET layout 与 freeze 防御）：磁盘 `status=frozen` 且下列任一成立 → 响应 `status=stale`：

1. 无 current；
2. `get_current().identity` 六键与 pointer `identity` 不完全相等；
3. `mapping.json` 不 listed，或其 `revision` ≠ pointer `mapping_revision`。

stale 时 PATCH 与 Freeze 失败关闭。Unfreeze 仍允许。禁止静默用旧形态去请图（IMG-03 另刀必须复用此计算）。

Core 前进（新 Confirm / publish）或重新 `lock_mapping` 都会让已冻计划 stale。

## 12. HTTP

Admin Bearer。前缀 `/card-os/api/v1/admin/knowledge-library`。无新公网路由。无新 Nginx location。

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| GET | `/{topic}/layout` | §7–8。有 current 则可能建草稿。返回 `listed`、`status`、`mapping_listed`、`can_freeze`、`can_unfreeze`、`identity`、`outline` |
| PATCH | `/{topic}/media-plan` | §9 |
| POST | `/{topic}/media-plan-freeze` | §10 |
| POST | `/{topic}/media-plan-unfreeze` | §11 |

无 token：JSON 不得 200 空成功。沿用 WB-01 鉴权码。未知 topic → `OPS_NOT_FOUND`。

CLI 与 HTTP 同一函数。测试可只跑 CLI + HTTP unittest。library 根必须由调用方注入；不得指向现网 KNOW-04 library。

GET 无 current 示例：`{"listed": false, "topic_slug": "x"}`，HTTP 200，无 `outline`。

`can_freeze` = listed current + pointer draft + `mapping_listed`。`can_unfreeze` = 磁盘 frozen。

## 13. 操作台

`GET /card-os/ops/layout/{topic}`（admin 壳 + 页面 JS 调 §12）。

- 大纲：角色组 → unit → 命题行；每行 facet / role / claim / form `<select>` / related 文本。
- 顶栏：classification、mapping 状态（只读；链到既有知识详情 mapping 块，不复制 lock UI）、media-plan status。
- 按钮：Freeze（`can_freeze`）、Unfreeze（`can_unfreeze`）。无「导出提示词」。
- 「补知识点」：`/card-os/ops/compile`（新建 intent）。本页不得提交 Core JSON。
- Draft 下 select 变更走 PATCH。Frozen/stale 下 select disabled。

`/card-os/ops/compile/{intent_id}`：intent `state=current` 时增加 **Open layout** → `/card-os/ops/layout/{topic}`。其他 compile 行为不变。

知识详情页：仅增加指向 layout 的文本链接。**不改 mapping-lock 第三块 markup/JS。**

无 token 的 HTML 源码不得含 claim、form、proposition_id、plan 节点。

## 14. 错误

沿用 WB-01 鉴权 / `OPS_NOT_FOUND`。

| 码 | 何时 | HTTP |
| --- | --- | --- |
| `LAYOUT_NO_CURRENT` | PATCH / freeze / unfreeze 且无 current | 409 |
| `MEDIA_PLAN_NOT_DRAFT` | PATCH 或 freeze 时磁盘不是 draft | 409 |
| `MEDIA_PLAN_NOT_FROZEN` | unfreeze 时磁盘不是 frozen | 409 |
| `MEDIA_PLAN_FORM_FORBIDDEN` | 安全 / 未知 / 非命题节点标 `wordless-image` 或 `interactive` | 400 |
| `MEDIA_PLAN_NODE_UNKNOWN` | PATCH 的 id 不是 current active 命题 | 400 |
| `MEDIA_PLAN_MAPPING_REQUIRED` | freeze 时 mapping 未 listed | 409 |
| `MEDIA_PLAN_STALE` | freeze（或另刀导出）时身份或 mapping revision 已漂 | 409 |
| `LAYOUT_UNAUTHORIZED` | actor 空或机器名（与 confirm-current 相同规则：非空、非 `machine` / `qa-01-v1` / `publish-01-v1`） | 400 |

GET layout 缺 mapping 不 409：`mapping_listed=false`，`can_freeze=false`。

**不是错误：** 无 compile-intent 或空 suggestions（全 `text`）；`interactive` 落在合法节点；大纲省略 draft 多余 id；模块未出齐；无 PNG。

不采用已废的 `MEDIA_PLAN_NODE_MISSING`：freeze 物化时丢弃 draft 中已不在 current 的 id，并为新命题补 `text`。

## 15. 验收

本机隔离 library。不写生产 library。不打 release。

1. Confirm current 前后都没有 `media-plan.json`，直到第一次 layout GET。
2. 无 pointer 的 GET layout（有 current）写出 `revision-0001` draft；无 suggestions intent 则全 `text`；有则建议 id 为 `wordless-image`。
3. 大纲按 `legend_role` 分组；空角色缺席；无命题 unit 无 form。
4. PATCH draft 成功；对 safety/unknown 标 `wordless-image` → 400，文件不变。
5. 无 mapping 时 freeze → 409；listed mapping 时 freeze → 新 frozen 文件 + 六键 identity + `mapping_revision`；`current.json` 与 `mapping.json` 字节不变。
6. PATCH frozen → 409；unfreeze → 新 draft，旧 frozen 仍在；再 freeze → 更新的 frozen 号。
7. 前进 current 或 relock mapping 后 GET `status=stale`；freeze 409；unfreeze 允许。
8. 无 token HTML 不含 claim。省略 `object_type` 的 `cat` 编译路径行为与本刀之前相同。
9. 对照旧剑龙卡：只验收模块种类该亮/该空（由 current + legend 决定），不验收像素，不验收请图词。

夹具：有 mapping 的主题（如兔子 four-card lock）测 freeze；恐龙 entity 测 suggestions → draft。不要用 `rabbit-composite` 的 `LEGEND_ROLE_MISSING` 当成本刀缺陷去放宽图例。

## 16. 实现落点

权威仓库：产品规范 `kids-visual-learning-pack`。server 实现须等本文件 Approved，且实施计划落盘之后。

优先：library `media-plan` pointer/revision、outline 纯函数、PATCH/freeze/unfreeze、ops layout HTML、compile「Open layout」链接、layout 链到知识详情。不接生图，不改 Nginx，不改 `lock_mapping`。

已知 combined-gate 2 FAIL（ops mapping-lock `LEGEND_ROLE_MISSING`）保持不修。
