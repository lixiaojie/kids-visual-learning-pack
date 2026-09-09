# 操作台：投影块选择、A4 排版与双画廊（PACK-01）

- Status: Approved for this execution tranche
- Date: 2026-09-08
- Related: [FLOW-01](2026-09-04-operator-iterative-workflow-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)、[RENDER-02](2026-09-04-legend-module-chrome-design.md)、[IMG-03](2026-09-07-operator-frozen-node-illustration-compose-lock-design.md)、[PUBLISH-02](2026-09-07-operator-locked-projection-gallery-publish-design.md)、[PUBLISH-01](2026-08-31-immutable-package-publish-design.md)、[PORTAL-01](2026-08-31-published-artifact-gallery-design.md)、[FREEZE-01](2026-09-07-operator-layout-graph-form-freeze-design.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)
- Does not implement: OpenAI / 图像 API；Skill claim；第五个治理对象；改四对象 schema；改 Confirm current；改 `lock_mapping`；可交互运行时；画廊内勾选/重排；缩小字号装页；生产 catalog；现网画廊；merge/push/release
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`。FLOW-01 仍是程序级工作流；本文件是 PACK-01 的实施授权。

## 1. 目标

compose 全量模块铬之后，操作员在锁定上架之前把投影**区块化**：勾选哪些子块进入这一版，按 A4 自动分页，再拖块改页/改序，预览并刷新印样。锁定冻结的是同一组已勾选块的**两种渲染**：

1. **完整投影**：屏幕模块铬，可滚动，不按 A4 切页；
2. **A4 投影**：四卡骨架 + 续页的分页印品。

画廊只读切换这两种。未勾选的块两版都不出现。知识 current 不变。

本设计满足路线图 `PACK-01`，并完成 FLOW-01 中后置的打印铬与「浏览已锁定投影」在画廊侧的选择面（选渲染，不选块）。它叠加在 COMPOSE-01 / RENDER-02 / IMG-03 / PUBLISH-02 之上，**扩展**有 pack-layout 主题的包形状与 PORTAL 详情，不改无 pack-layout 旧主题的四页合同。

相对 IMG-01 首刀「主图 + 条文」：那是打通捷径，不是锁定投影的默认语义。相对 PUBLISH-02：有 pack-layout 之后，禁止再把四张 hero 图像带 PNG 当作上架成品。

## 2. 非目标

- 不接 OpenAI / 图像 API，不写 Skill claim，不读 Cookie。
- 不改四对象 schema、v1 FACT 键集、Confirm current、`lock_mapping`。
- 不新增第五个治理对象。`pack-layout` 与 `media-plan` / `mapping.json` 同属 library 元数据。
- 不把 pack-layout 写入四对象 `revision-NNNN/` 包目录或 Knowledge Core。
- 不在公开画廊里勾选、拖块或重排。
- 不把字号缩小、裁切主图或把图塞进清场区当作装页手段。
- 不把知识卡做成插图页。
- 不实现可交互运行时。
- 不改无 `media-plan.json` pointer 的旧 `publish_from_artifact` 字节合同。
- 不写生产 package catalog，不改现网画廊 `rabbit` 摘要，不 reload Nginx。
- 不 merge/push/release，不标 FLOW-01 / IMG-03 / PUBLISH-02 / PACK-01 `DONE`。
- 不修 ops mapping-lock `LEGEND_ROLE_MISSING`。

## 3. 在主路径中的位置

```text
compose                 全量模块铬；hero 仍须 illustrated（compose 门禁不变）
        ↓
pack-layout 草稿        勾选子块 → 自动分页 → 拖块
                        HTML 预览即时；「刷新印样」出 A4 PNG + PDF
        ↓
lock_pack_layout        冻结草稿 + 两种渲染；印样门禁；QA approve
                        knowledge current 不变
        ↓
publish_locked_projection   一个 package revision（A4 多页 + 完整投影）
        ↓
PORTAL                  同一包：完整投影 | A4 投影
```

有 `media-plan.json` 且已 compose 的主题：

- IMG-03 `lock_composed_projection` **不再**表示可上架。调用返回 `PACK_LAYOUT_LOCK_REQUIRED`（409）。操作台「锁定投影」改为进入 pack 页。
- `publish_locked_projection` 要求 **frozen** pack-layout、未 stale、不过期印样通过、QA `approved`。禁止再发布四张 `CN_OBS:band` hero 带 PNG 作为该主题成品。

无 media-plan pointer 的主题：PUBLISH-02 / WB-03 旧路字节级不变。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 选择发生面 | 操作台；compose 之后、锁定上架之前 |
| 一级块 | 图例角色模块（外形 / 比较 / 证据 / 时间 / 发现地 / 习性等） |
| 模块内可拆 | 每张图、每条 AGE 句、以及记录 / 描红 / 抄写 / 安全 / 来源 |
| 默认勾选 | 第一次建草稿时全选当时 compose 里存在的可勾子块 |
| 中英 | 勾选与页序成对；同一子块在中英同一页序；一侧装不下两侧一起续页 |
| 页骨架 | 中英观察 / 中英知识；溢出加续页；中英每面页数对齐 |
| 重排 | 先自动分页，再拖块改该面内顺序或续页；不能跨观察/知识面；不能把图拖进知识卡 |
| 预览 | HTML 接近 A4、拖动即时、标溢出；「刷新印样」才出真实 A4 PNG |
| 字号 | 不缩小 |
| 锁定最低内容 | 中英观察、中英知识每一面至少一块可见内容；hero 可取消勾选 |
| 缺图 | 不是错误；无 PNG 的图像子块不可勾选 |
| 两种画廊 | 同一已勾选块集：完整投影 = 屏幕铬；A4 投影 = 分页印品 |
| 画廊默认 | A4 投影；列表缩略图 = 中文观察第 1 页 |
| 未勾选 | 留在草稿可加回；不进这一版包；完整投影也不出现 |
| current.json | knowledge library `current.json` 字节不变 |
| 现网 | 不由本文件授权 |

## 5. 子块身份

稳定 id，禁止页码、坐标、随机数。`page_id` ∈ {`CN_OBS`,`EN_OBS`,`CN_KNOW`,`EN_KNOW`}。

| 种类 | id 形状 | 成对键（去掉语种前缀） |
| --- | --- | --- |
| AGE 句 | `text:{page_id}:{proposition_id}` | `text:{FACE}:{proposition_id}` |
| hero | `image:hero:{page_id}` | `image:hero:{FACE}` |
| 视法 | `image:view:{page_id}:{view_key}` | `image:view:{FACE}:{view_key}` |
| 节点图 | `image:node:{page_id}:{proposition_id}` | `image:node:{FACE}:{proposition_id}` |
| 观察清场 | `chrome:{page_id}:record` / `trace` / `copy` | `chrome:{FACE}:record` 等 |
| 知识页脚 | `chrome:{page_id}:safety` / `source` / `uncertainty` | `chrome:{FACE}:safety` 等 |

`FACE` 为 `OBS` 或 `KNOW`。勾选、取消、拖动中文子块时，英文同成对键子块必须同步；不存在的对语种子块视为空占位，仍占页序对齐。

图像子块仅观察卡。知识卡 `image:*` 不出现。无对应 PNG（sha 空）的图像子块不进入草稿可选集。

一级模块勾选是快捷方式：勾选/取消某角色等于对该角色下当前可选子块批量同步；之后仍可拆开单子块。

## 6. 磁盘

候选根与 library 根由调用方注入。pack-layout 落在 library 主题旁，与 media-plan 同层：

```text
{library_root}/{topic_slug}/
  pack-layout.json
  pack-layout-audit.jsonl
  pack-layouts/
    revision-NNNN.json
```

印样与屏幕预览落在候选根，不进 library current 目录：

```text
{candidate_root}/pack-work/{topic_slug}/
  print/cards/{face}-{nn}.png
  print/print.pdf
  print/layout-report.json
  projection/index.html
  projection/meta.json
```

`NNNN` / `{nn}` 为零填充。写入用临时文件 + `os.replace`。禁止覆盖已存在的 frozen `pack-layouts/revision-NNNN.json`。禁止跟随符号链接。

### 6.1 Pointer `pack-layout.json`

```json
{
  "schema": "cognitive-card-knowledge-library-pack-layout-v1",
  "topic_slug": "stegosaurus",
  "revision": 1,
  "status": "draft",
  "identity": null,
  "compose_content_lock_sha256": null,
  "media_plan_revision": null,
  "mapping_revision": null,
  "print_sample_sha256": null,
  "source_current_revision": 5,
  "set_at": "2026-09-08T00:00:00Z",
  "reason": "create_draft"
}
```

磁盘 `status` 仅为 `draft` 或 `frozen`。`stale` 只出现在 GET 响应。`identity` 在 `frozen` 时为 current 六键（与 media-plan / illustration 同形）。`print_sample_sha256` 在印样作废时为 `null`。

### 6.2 Draft / frozen 文件

`pack-layouts/revision-NNNN.json` 至少含：`schema`（`cognitive-card-pack-layout-revision-v1`）、`topic_slug`、`revision`、`status`、`selected[]`（子块 id）、`pages`（每面有序列表，项为 `{page_index, block_ids[]}`）、`source_compose`（intent_id 与 content_lock_sha256）、`created_at`、`actor`。

Draft 可 PATCH 原地替换同一 revision。Frozen 禁止覆盖。下一号 = 已有最大号 + 1。

每次 create_draft / patch / paginate / print_sample / lock 追加 `pack-layout-audit.jsonl`。只追加。

## 7. 状态机

```text
compose 已存在且无 pointer
  → GET pack                 建 revision-0001 draft；selected=当时可勾全集；自动分页
draft
  → PATCH selected           同步成对键；重跑自动分页；印样作废
  → PATCH placement          拖块；镜像对语种页序；印样作废；不重跑全自动分页
  → POST print-sample        重渲 A4 PNG/PDF 与屏幕 projection HTML；写入 print_sample_sha256
  → POST lock                §9
frozen
  → PATCH / print-sample / lock   PACK_LAYOUT_NOT_DRAFT
  → GET 身份/compose/freeze 漂了 → 响应 stale
stale（仅响应）
  → PATCH / lock / print-sample   PACK_LAYOUT_STALE
  → GET                          只读说明；须重合成后 GET 再建新 draft
```

GET **不**把 pointer 改写成 `stale`。stale 公式复用 freeze / compose 身份：current 六键、mapping revision、media-plan revision、compose `content_lock_sha256` 任一不一致即为 stale。

## 8. 自动分页、拖块、印样

四面：`CN_OBS`、`EN_OBS`、`CN_KNOW`、`EN_KNOW`。每面至少 1 页。溢出则该面 `page_index` + 1，对语种同序号页必须存在（可暂无块，随后由成对放置填入）。

自动分页规则（确定性，测试可复现）：

1. 只放置 `selected[]` 中的子块。
2. 观察面顺序：按 LEGEND-01 角色表，角色内先图后文（hero → 该角色视法 → 节点图 → 该角色 AGE 句），然后已勾选的 `record` / `trace` / `copy`（若勾选，默认钉该面最后一页，仍可拖走）。
3. 知识面顺序：角色模块句 → 已勾选的 `uncertainty` / `safety` / `source`（默认末页，可拖）。
4. 一页可用高度 = A4 内容区减去页边与（若该页是该面最后一页且勾选了清场/页脚）预留高度。装不下当前子块则开续页；子块本身高于一页 → `PACK_BLOCK_TOO_LARGE`（该子块必须拆或取消勾选；本设计不把一张图拆成两页）。
5. 放置中文观察页 k 的子块后，英文同成对键放到英文观察页 k；知识面同理。

拖块：仅同一 `FACE` 内。目标页溢出时 HTML 标溢出，允许暂存；印样几何失败则不能锁定。拖中文页序，英文同成对键跟到同一 `page_index`；目标页不存在则两侧同时加续页。

HTML 预览使用接近 A4 的固定框，溢出条可见。它不是锁定真值。

「刷新印样」：对 `pages` 每页出一张 A4 PNG；合并 `print.pdf`；另写 `projection/index.html`（仅 selected 子块的屏幕铬，四段页序仍为 CN_OBS → EN_OBS → CN_KNOW → EN_KNOW，续页在屏幕铬里是连续模块而非 A4 切页）。知识卡 HTML 无 `<img>`。成功才写 `print_sample_sha256`（规范 JSON 对所有印样文件相对路径与 sha 的摘要）。

PATCH selected 或 placement 之后 `print_sample_sha256` 必须清为 `null`，磁盘印样不得再被 lock 接受。

## 9. `lock_pack_layout`

成功条件同时成立：

| 条件 | 失败码 |
| --- | --- |
| 合法 slug、有 current、有 compose | 沿用 `ILLUS_SLUG_INVALID` / `MAPPING_NO_CURRENT` / `COMPOSE_NO_COMPOSE` |
| media-plan frozen 且未 stale；compose 身份一致 | `MEDIA_PLAN_NOT_FROZEN` / `MEDIA_PLAN_STALE` / `COMPOSE_IDENTITY_MISMATCH` |
| pack-layout 为 draft 且未 stale | `PACK_LAYOUT_NOT_DRAFT` / `PACK_LAYOUT_STALE` / `PACK_LAYOUT_NO_DRAFT` |
| `print_sample_sha256` 非空且磁盘印样复算一致 | `PACK_PRINT_SAMPLE_STALE` |
| 印样几何通过（无溢出、无跨清场区插图） | `PACK_PRINT_OVERFLOW` / 沿用 `RENDER_ASSET_IN_CLEAR_ZONE` |
| 中英观察页数相等、中英知识页数相等 | `PACK_PAGE_COUNT_MISMATCH` |
| 四面各至少一个 selected 子块出现在 pages 里 | `PACK_FACE_EMPTY` |
| 人类 actor，非保留名 | 沿用 `ILLUS_UNAUTHORIZED` / `QA_REVIEW_ACTOR_REQUIRED` |

成功：

1. 写下一号 frozen pack-layout（钉 identity、compose lock、media-plan / mapping revision、print_sample_sha256）；
2. 调用 `record_review(..., decision="approve")`；
3. **禁止** `publish_approved`。

`lock_composed_projection` 在存在 compose 且主题有 media-plan pointer 时：409 `PACK_LAYOUT_LOCK_REQUIRED`。不得隐式 approve。

锁定后 pack-layout 不可再 PATCH。要改勾选或页序：重合成（compose 身份变化 → stale）后 GET pack 建新 draft。锁定前草稿可反复 PATCH。不提供独立 Unfreeze 按钮，避免与 QA `approved` 终态并行第二套解冻。

## 10. 包内容与身份

有 frozen pack-layout 的 `publish_locked_projection` 写入：

```text
{catalog_root}/{slug}/revision-NNNN/
  manifest.json
  qa-report.json
  sources.json
  pack-layout.json
  cards/cn-observe-01.png
  cards/cn-observe-02.png
  cards/en-observe-01.png
  cards/en-observe-02.png
  cards/cn-know-01.png
  cards/en-know-01.png
  projection/index.html
  projection/assets/<sha256>.png
  print.pdf
```

页文件名：`{cn|en}-{observe|know}-{nn}.png`，`nn` 从 `01` 起，等于该面 `page_index`。中英观察文件数必须相等；中英知识文件数必须相等。不写无序号的 `cards/cn-observe.png`。

`projection/assets/` 只含 **selected** 图像子块的 PNG（按 sha 命名）。未勾选节点图、未勾选视法、未勾选 hero 不得进包。ops 全量 compose HTML 不得进包。

`package_sha256` 仍由服务器按 PUBLISH-01 规则复算：`package_slug`、`content_lock_sha256`、`render_output_sha256`、`qa_report_sha256`、**本 revision 内每个 artifact 相对路径与 SHA-256**。因此多页 PNG 与 `projection/` 进入身份。`revision` 不进身份。

`render_output_sha256` 对有 pack-layout 的包定义为：印样目录规范列表（所有 A4 PNG + `print.pdf` + `projection/index.html` + `projection/assets/*`）的摘要，必须等于冻结时 `print_sample_sha256`。

无 pack-layout 的旧包：四张无序号 PNG 合同不变。

## 11. 画廊

PORTAL 公开/owner 隔离、visibility、撤回规则不变。有 pack-layout 的包：

- 列表缩略图：`cards/cn-observe-01.png`；
- 详情默认 **A4 投影**：按面分组翻页，可打开 `print.pdf`；
- 切换 **完整投影**：渲染包内 `projection/index.html`（只读）；
- 不得出现 ops compose URL、不得出现未发布草稿。

下载允白改为：**manifest 声明的相对路径**，且必须落在该 revision 目录内、不得 `..`。旧四页包仍只声明原来七个文件路径。新包声明 §10 实际文件。禁止靠开放目录下载 intent / library / compose 工作区。

## 12. HTTP 与操作台

Admin Bearer。无新公网路由。无新 Nginx location。无新 capability。

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| GET | `/card-os/api/v1/admin/knowledge-pack/{topic}` | 读草稿/冻结；无则建 draft |
| PATCH | `/card-os/api/v1/admin/knowledge-pack/{topic}` | body：`selected` 或 `placement` + `actor` |
| POST | `/card-os/api/v1/admin/knowledge-pack/{topic}/print-sample` | body `{"actor": "<human>"}` |
| POST | `/card-os/api/v1/admin/knowledge-pack/{topic}/lock` | body `{"actor": "<human>"}`；§9 |
| GET | `/card-os/ops/pack/{topic}` | 勾选、HTML 预览、拖块、刷新印样、锁定 |

compose 页：已 compose 且有 media-plan 时，主按钮为「进入排版」→ `/ops/pack/{topic}`。不再提供一键 `lock_composed_projection`。

上架仍为 compose/pack 页在 frozen+approved 后的「上架画廊」，POST 既有 `/knowledge-compose/{topic}/publish`。

无 token：壳不得含 claim、子块正文、图片字节、catalog 路径。

## 13. 错误

沿用 `ILLUS_*`、`COMPOSE_*`、`MEDIA_PLAN_*`、`QA_*`、`ARTIFACT_*`、`PUBLISH_*`。本刀新码：

| 码 | 何时 | HTTP |
| --- | --- | --- |
| `PACK_LAYOUT_LOCK_REQUIRED` | 有 media-plan 时仍走 `lock_composed_projection` | 409 |
| `PACK_LAYOUT_NO_DRAFT` | 无 pointer | 409 |
| `PACK_LAYOUT_NOT_DRAFT` | 已 frozen 还 PATCH | 409 |
| `PACK_LAYOUT_STALE` | 身份/compose/freeze 漂了 | 409 |
| `PACK_PRINT_SAMPLE_STALE` | 无印样或印样与草稿不一致 | 409 |
| `PACK_PRINT_OVERFLOW` | 印样几何溢出 | 409 |
| `PACK_PAGE_COUNT_MISMATCH` | 中英页数不对齐 | 409 |
| `PACK_FACE_EMPTY` | 某一面零块 | 409 |
| `PACK_BLOCK_TOO_LARGE` | 单子块高于一页 A4 内容区 | 409 |
| `PACK_CROSS_FACE` | 拖块跨观察/知识或图进知识卡 | 409 |
| `PACK_UNKNOWN_BLOCK` | id 不在可选集 | 404 |

**不是错误：** 缺节点 PNG；取消 hero；取消安全/描红；模块未出齐；同一冻结身份再发布（幂等）。

## 14. 验收

本机隔离 library + 独立夹具 catalog。不写生产 library / catalog。不打 release。不要求打开 ChatGPT。

必须成立：

1. 无 media-plan：`lock_composed_projection` / `publish_from_artifact` 与本刀之前相同。
2. 有 compose + media-plan：`lock_composed_projection` → `PACK_LAYOUT_LOCK_REQUIRED`；GET pack 建全选草稿并自动分页。
3. 取消部分子块后完整投影与 A4 都不含那些块；对语种同步取消。
4. 观察面勾选过多图/句 → 自动续页；英文观察页数等于中文。
5. 拖中文子块到第 2 页 → 英文对应块在英文第 2 页；印样作废。
6. 未刷新印样就 lock → `PACK_PRINT_SAMPLE_STALE`。
7. 某一面全不选 → `PACK_FACE_EMPTY`。
8. 印样通过后 lock：QA `approved`；current.json 不变；不写 catalog。
9. publish：revision 含序号 PNG、`projection/index.html`、selected 图资产、`print.pdf`；不含未勾选节点 PNG、不含 ops 全量 compose HTML。
10. 本机画廊详情可切换完整投影 / A4；默认 A4；列表缩略图为 `cn-observe-01`。
11. 旧四页包下载允白与页面不变。
12. 无 token 不能 PATCH/lock/publish；无 token 的 pack HTML 不含 claim。
13. 现网应用、Nginx、生产 library、现网画廊 `rabbit` 不被本刀改写。
14. 对照剑龙只验收：能拿掉过长句和多余图后锁出可翻页 A4，且完整投影仍是同一组块。不对整卡像素。

拖块与自动分页同属本文件合同。实施计划可把拖块列为靠后任务，但不得把合同改回「只能删块不能续页」或「画廊只有 hero 带」。

## 15. 实现落点

权威仓库：产品规范 `kids-visual-learning-pack`。server 实现须等本文件 Approved，且实施计划落盘之后。

优先：`pack-layout` 存储与状态机、成对勾选、自动分页、HTML 预览、印样、`lock_pack_layout`、扩展 `publish_locked_projection` 包形状、PORTAL 双版本切换。不接图像 API，不写生产 catalog，不 merge `main`。

已知 combined-gate ops mapping-lock `LEGEND_ROLE_MISSING` 保持不修。
