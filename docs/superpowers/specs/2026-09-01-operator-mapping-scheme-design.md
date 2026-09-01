# 操作台映射方案确认（WB-02）

- Status: Approved for this execution tranche
- Date: 2026-09-01
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[LIB-01](2026-08-30-knowledge-library-revision-current-design.md)、[PROJ-01](2026-08-30-projection-family-selection-design.md)、[WB-01](2026-08-31-operator-knowledge-workbench-design.md)、[CONV-01](2026-08-30-knowledge-four-card-converter-design.md)、[AGE-01](2026-08-31-age-language-adapter-design.md)
- Supersedes for WB-02 scope: [四卡文字成熟投影](2026-08-31-four-card-text-mature-projection-design.md)（该文件保持 Parked，不实施）
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

按主路径 **生成 → 管理（浏览/更改/选择）→ 映射方案 → 产物输出** 补上确认点 1 的映射半截：

1. 操作员在令牌操作台对已有 knowledge current **显式选择** Projection family（`four-card` 仍为 opt-in）；
2. 系统给出**可检查的槽位方案**（命题/path 节点 → blueprint 槽），而不是 PNG；
3. 操作员确认后锁定为 library **映射 revision**；**不**把该 revision 设为 knowledge current；
4. 不生成四卡、不改画廊、不改 Knowledge Core 字节。

本设计满足路线图 `WB-02` 在本刀的范围。插图、convert/render、上架属 `WB-03`。更改命题属知识源管理的后续切片，不在本刀。

## 2. 非目标

- 不调用 CONV-01 / RENDER-01 / QA-01 / PUBLISH-01，不写出 PNG/PDF，不在操作台加「生成」按钮（`WB-03`）。
- 不替换现网画廊 ACCEPT-01 包；不 reload Nginx；不打生产应用 release。
- 不在界面改命题、来源或 Scope（更改）；不编译自由 prompt（`API-01`）。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、packet 契约。
- 不把视觉方案或中文安全写进 Knowledge Core。
- 不新增第五个治理对象。映射 pointer 与 current pointer 同属 library 元数据。
- 不 merge server `main`；不 push；不等于 AGE-02 / ACCEPT-02。

## 3. 在主路径中的位置

```text
知识源生成          KNOW-03 / KNOW-04 / CLI authoring
        ↓
知识源管理·浏览     WB-01 只读操作台
知识源管理·选择     本刀：选 family（更改命题不在本刀）
        ↓
映射方案设计        本刀：预览槽位 → lock_mapping
        ↓
投影产物输出        WB-03：按映射 revision 生成并上架
```

相对 ADR-002 §11.1：本刀完成「显式确认 1：合并方案确认」里 **Projection 映射** 部分。确认 2（发布 Artifact）仍是 WB-03。

```text
Knowledge Core          事实；禁止呈现方案
        ↓
library current         知识源默认 family（兔子 = chaptered-guide）
        ↓
本刀 mapping preview    对 requested family 分配 blueprint.slots
        ↓
mapping.json            指向映射 revision；current.json 不变
```

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 本刀产物 | 槽位方案 + 映射 revision；不是排版 |
| 超载 | fail closed，禁止把装不下的命题丢进来源区 |
| knowledge current | 确认映射后仍指向原知识源 revision |
| 来源槽 | 只承载来源记录，不收容溢出命题 |
| 记录区 | 观察卡 record 仍空；映射不往该区写节点 |
| 中文安全 | 登记表投影；未登记不得锁定 four-card |
| 交付面 | 本机操作台 + library；现网画廊 / Nginx / 应用 current 不改 |

## 5. 选择

WB-01 投影菜单只读。本刀允许点击 options 中的 family，作为 `requested_family` 重算选择面（PROJ-01 合同不变：`four-card` 永不自动 recommended）。

- 未确认前：只改预览，不写盘。
- 选中 `discouraged` family 仍可预览；锁定时须在响应里带回 `fit` 与 `reason_codes`，不得静默改 recommended。
- 未知 family：选择面既有错误，不得预览。

## 6. 映射方案

输入：topic 的 **knowledge current** 四对象 + `requested_family`。
输出：预览 JSON（不写盘）或锁定后的新四对象包。

`knowledge-core` 与 `learning-spec` 字节必须与 current 完全一致。只重写 `projection-spec`（blueprint.family、slots.node_ids、renderer_binding 能力钉）和 `manifest`。

### 6.1 槽位 id

沿用合同试点四卡槽，顺序固定：

`cn-observation` → `en-observation` → `cn-knowledge` → `en-knowledge`

`node_ids` 引用 current `learning-spec` 已有 path 节点，不新增节点、不在 Projection 里写命题正文。落地 `slot_id` 沿用 authoring：`slot.{topic_slug}.{suffix}`（suffix 为上列四名），不是无前缀的裸 id。

### 6.2 four-card 分配规则

只分配 scope 内 `standing=active`（缺省 active）的节点/命题。`superseded` 不进槽。

| 槽 | 规则 |
| --- | --- |
| `cn-knowledge` / `en-knowledge` | 同一组知识节点：全部须被覆盖的 active 知识节点。中英槽 `node_ids` 集合相等 |
| `cn-observation` / `en-observation` | 「看」：知识槽集合的子集；至少 2 个 distinct 节点；中英集合相等；优先 FACT/命题顺序中的非 `unknown` |
| 观察「记录」 | 无节点；禁止把知识节点写入 record 语义 |
| 来源 | 不占用上述四槽的溢出位。来源仍来自 Core `sources`；预览列出 `title`（缺 title 则 `MAPPING_SOURCE_TITLE_MISSING`，不得锁定） |

禁止：用像素/行数预算决定谁进知识槽、谁进来源区。若无法把全部应覆盖的 active 知识节点放入知识槽 → `MAPPING_FOUR_CARD_OVERLOADED`，提示改 Scope（更改，非本刀）或改选 family。

兔子验收下限：知识槽 ≥ 4 个 distinct 可追溯 `proposition_id`；观察「看」≥ 2 且 ⊆ 知识槽。

### 6.3 其他 family

`chaptered-guide` / `progressive-exploration` / `time-sensitive-brief`：预览展示 PROJ-01 已有槽位策略（四槽或 `main` / 每节点一槽），允许锁定。本刀不为它们新设计语义。锁定后同样写入映射 revision，不抢 current。

### 6.4 安全中文登记

不写进 Core。预览从 current 命题的 `safety` 列表（及若存在的顶层 `safety_scope`）收集英文原文，查版本化登记表（精确键，fail closed，不调用外部模型）：

- 命中：预览给出 `safety[].cn`；`en` 必须与 Core 原文 Unicode 一致
- 未命中：`AGE_SAFETY_EXPRESSION_GAP`，**禁止锁定 `four-card`**
- 中文不得弱化边界（须监护 / 伤脊椎等）

首批必须覆盖 AUTHOR-02 兔子这三条原文（键逐字一致）：

1. `Ask a rabbit-savvy veterinarian before making significant diet changes.`
2. `Children must be supervised; only adults or responsible older children should pick up rabbits.`
3. `A struggling rabbit can injure its fragile spine, so handling must stay calm and secure.`

登记表版本钉在映射包 `projection-spec.renderer_binding.required_capabilities`：`age-language-adapter-v1` 与 `safety-expression-registry-v1`。不得把登记正文写入 Core。

非 four-card 锁定不要求安全中文登记。

## 7. 持久化

LIB-01 `publish` 会移动 `current.json`。本刀新增 library 操作，**禁止**用 `publish` 锁定映射。

| 操作 | 写 revision | 改 current.json | 改 mapping.json |
| --- | --- | --- | --- |
| `preview_mapping` | 否 | 否 | 否 |
| `lock_mapping` | 是 | **否** | 是（指向新 revision） |

`mapping.json` 与 `current.json` 同级，同为 library 元数据：

```json
{
  "schema": "cognitive-card-knowledge-library-mapping-v1",
  "topic_slug": "rabbit",
  "revision": 3,
  "family": "four-card",
  "identity": {
    "object_id": "core.rabbit",
    "revision": 3,
    "knowledge_core_sha256": "<hex>",
    "learning_spec_sha256": "<hex>",
    "projection_spec_sha256": "<hex>",
    "final_content_lock_sha256": "sha256:<hex>"
  },
  "source_current_revision": 2,
  "set_at": "2026-09-01T00:00:00Z",
  "reason": "lock_mapping"
}
```

约束：

- 新 revision **必须**前进四对象上的 `revision` 字段（及 `learning_spec.knowledge_core_ref.revision` / `projection_spec.learning_spec_ref.revision`），否则 library 目录号冲突。因此新包的 `knowledge_core_sha256` **不等于** current（revision 字段变了）。
- 事实载荷必须与 current 一致：`sources`、`propositions`、`relations`、`knowledge_units`、`scope`（含 classification）、`coverage`（若有）的 canonical JSON 在把双方 `revision` 对齐后完全相等。不得增删命题或改 claim/safety 正文。
- `mapping.json.identity` 记录**新**映射包；`source_current_revision` 指向锁定时的 knowledge current。
- 新 revision 目录不可覆盖；审计追加 `mapping-audit.jsonl`
- 再次锁定同一 family：新 revision 号，mapping pointer 前进；旧映射目录保留
- 无 mapping pointer 不是错误；预览仍可用
- `get_current` 行为不变

## 8. 操作台与 HTTP

本机 loopback 上扩展 WB-01 详情页，不改公网画廊。

详情页第三块 **映射方案**（前两块知识 / 投影菜单保留）：

1. 当前 `requested_family`（默认等于选择面 chosen，可点选 options）
2. 各槽 `slot_id` + 节点/命题 id + 可见 claim 原文（只读）
3. 观察「看」是否 ⊆ 知识槽；记录区标明空
4. 来源标题列表
5. 安全登记：已覆盖 / GAP
6. 按钮「确认映射」；无「生成」

写路径（admin Bearer，与 WB-01 同一前缀）：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| GET | `.../{topic}/mapping-preview?family=` | 对 **current** 预览；不写盘 |
| GET | `.../{topic}/mapping` | 读 `mapping.json`；无则 `listed=false`、HTTP 200 |
| POST | `.../{topic}/mapping-lock` | body `{"family":"..."}`；`lock_mapping` |

无 token：与 WB-01 相同，JSON 不得 200 空成功；HTML 壳不得预渲染命题。不新增公网匿名端点。

CLI 与 HTTP 同一函数：`preview_mapping` / `lock_mapping`。测试可只跑 CLI。

## 9. 错误码

| 码 | 含义 |
| --- | --- |
| `MAPPING_NO_CURRENT` | 无 knowledge current |
| `MAPPING_FAMILY_UNKNOWN` | 沿用选择面未知 family |
| `MAPPING_FOUR_CARD_OVERLOADED` | 无法在不溢出到来源区的前提下覆盖全部应映射知识节点 |
| `MAPPING_LOOK_UNDERFILLED` | 观察「看」不足 2 个 distinct 节点，或不是知识槽子集 |
| `MAPPING_SOURCE_TITLE_MISSING` | 某来源无 title |
| `AGE_SAFETY_EXPRESSION_GAP` | four-card 锁定时某条 safety 英文无中文登记 |
| `MAPPING_CORE_DRIFT` | 组装时 core/learning 摘要已不等于 current |
| `OPS_NOT_FOUND` / 鉴权码 | 沿用 WB-01 |

不得为填满而发明命题。未登记 claim 仍是 `AGE_EXPRESSION_GAP`（预览 four-card 时应可见；本刀不扩展 AGE claim 表，除非兔子八条已覆盖）。

## 10. 验收

本机：生产同构的 library 兔子 current（KNOW-04 `revision-0002` 或等价 chaptered-guide 编译）+ 本机操作台/CLI。

必须成立：

1. 预览 `family=four-card` 不写盘；current pointer 与 core 字节不变。
2. 锁定后出现新 `revision-NNNN`；`current.json` 仍指向原知识源 revision；`mapping.json` 指向新号；新包事实载荷（对齐 revision 后）等于 current。
3. 四卡映射：知识槽 ≥ 4 条 distinct 命题；观察「看」≥ 2 且 ⊆ 知识槽；记录无节点；来源预览含机构标题（如 `Description and Physical Characteristics of Rabbits` / `Diet for Rabbits` / RSPCA 之一）。
4. 安全：预览含汉字登记；对应英文等于 Core 原文；缺登记时锁定 four-card 失败。
5. 操作台无生成按钮、无 PNG/PDF 新文件；现网 ACCEPT-01 `package_sha256` 不被本刀改写。
6. 不带 token 的 ops 壳仍不含命题正文。

测试：library mapping 操作 + 预览分配 + 安全 GAP；涉及 ops 适配器时跑既有 WB-01 用例。不要求完整 suite 清零既有 real-uvicorn 502。不要求生产安装本刀应用。

## 11. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓：本设计、路线图、任务/交接、文档地图；旧文字成熟 spec 保持 Parked 并注明被本文件取代 WB-02 范围。

优先：mapping 预览纯函数、`lock_mapping`、`mapping.json`、ops 第三块与两条 admin 路由、安全登记表。不接生图，不改 Nginx。

## 12. 与旧 WB-02 稿

旧稿把 RENDER 几何装箱、COPY 放宽和本机出 PNG 算进 WB-02。那些属于产物层，改挂 `WB-03`（或 WB-03 的子切片）。本刀只吸收其中的**映射语义**：知识槽覆盖命题、看 ⊆ 知、来源标题、安全中文登记、记录留空；明确拒绝「溢出进来源区」。
