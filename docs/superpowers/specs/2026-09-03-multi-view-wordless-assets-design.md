# 多视图无字资产（IMG-02）

- Status: Approved for this execution tranche
- Date: 2026-09-03
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-003](../../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[IMG-01](2026-09-02-operator-illustration-hero-page-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)
- Does not implement: RENDER-02 模块铬；作废 IMG-01 单主图路径；OpenAI 图像 API；Skill claim；生产 OCR；把多图塞进四卡布局；改四对象 schema；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

在 [IMG-01](2026-09-02-operator-illustration-hero-page-design.md) 一张无字 `observe.isolate` 主图之外，按 [投影图例](2026-09-03-projection-legend-v1-design.md) 为**已有实例**的像素画法增加可选无字 PNG。资产键 = 角色 + 画法。ChatGPT 仍不烧字。不得把「视法出齐」写成知识源准入或 Confirm current 条件。

本刀满足路线图 `IMG-02` 的书面合同。四卡里多图如何落位属 `RENDER-02`，不在本刀。

## 2. 非目标

- 不废止 IMG-01：`hero.png` 仍是 `observe.isolate`；创建 intent、主图上传、演示页条文合同不变。
- 不经 WB-02 `mapping-lock`；允许键从 intent 钉住的 library current 上 `assign_legend` 得到。
- 不把 chrome 角色做成 PNG 槽：`compare` / `evidence` / `time` / `place` / `learning_place` / `habit` / `kind` / `sequence` / `uncertain` / `safety` / `source` / `name` / `write` / `blank` 仍由 RENDER-02 画模块，本刀不请这些图。
- 不要求 `three_view` / `section` / `exploded` / `in_situ` / `interaction` 出齐。
- 不接图像 API、不写 Skill claim、不跑生产 OCR、不改 COMPOSE-01 主图带。
- 不改四对象、KNOW-04 生产 library、Nginx、server `main`。
- 不标 IMG-01 / COMPOSE-01 / LEGEND-01 / API-01 `DONE`。

## 3. 在主路径中的位置

```text
API-01 · Confirm current
        ↓
IMG-01 · illustration-intent     扩 isolate 提示词；上传 hero.png
        ↓
本刀 · 同一 intent               列出允许的额外像素键；每键一份提示词；可选上传
        ↓
COMPOSE-01                       本刀仍只用 hero.png
        ↓
RENDER-02（后置）                 有额外 PNG 才往模块铬里放
```

相对 ADR-002：额外图仍是下游投影资产，不是第五个治理对象，不写回 Knowledge Core。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| IMG-01 | **并存**。`hero.png` = `observe.isolate`，不另存第二份 isolate |
| 额外画法 | **可选子集**。缺槽不失败、不倒逼知识源 |
| Intent | 沿用 `cognitive-card-illustration-intent-v1`，不新建 views-intent |
| 允许键来源 | 钉住的 current 上 `assign_legend`；不经 mapping-lock |
| 像素键本刀 | `observe.three_view` / `observe.section` / `observe.exploded` / `setting.in_situ` / `setting.interaction` |
| 主图顺序 | 须先 `illustrated`（已有合法 hero）才接受额外槽上传 |
| 额外槽替换 | `illustrated` 且四对象摘要仍匹配时可覆盖重传该键；不必 cancel 整单 |
| 合成 | COMPOSE-01 本刀仍只读 hero |
| 推理位置 | 人 + ChatGPT 会员生图；服务器无图像模型 |
| 烧字检测 | 每份提示词禁止文字；上传走可注入检测器；本刀不交付生产 OCR |
| 交付面 | 本机操作台 + 显式注入的 library 根 |

## 5. 像素键与允许集

键格式：`{role}.{view}`，均为图例已登记的小写蛇形 id，中间一个点。合法像素键仅 §4 表中五键。`observe.isolate` 不是额外键。

允许集在**创建 intent 时**按钉住的 knowledge-core 快照计算，写入 meta，之后不随后来的 current 漂移（current 前进会使整单 `stale`，与 IMG-01 相同）。

计算：

1. 对快照调用既有 `assign_legend`（只读，不改 Core）。
2. 若调用失败：允许集为空；IMG-01 主图路径仍可用；对任何额外键上传 → `ILLUS_SLOT_NOT_ALLOWED`。
3. 若 `roles["observe"]` 至少一条非 superseded 命题：允许 `observe.three_view`、`observe.section`、`observe.exploded`。
4. 若 `roles["setting"]` 至少一条：允许 `setting.in_situ`、`setting.interaction`。
5. `learning_place` 有实例**不**产生像素键。请求 `learning_place.*` → `ILLUS_SLOT_NOT_ALLOWED`。
6. 未登记 view → `LEGEND_VIEW_UNKNOWN`。登记了但本刀非像素角色 → `ILLUS_SLOT_NOT_ALLOWED`。

「有实例」指该角色下有可解析命题，不表示该画法有独立命题。剑龙有外形即可列出三视/剖面/爆炸，操作员可以一张都不传。

禁止：为填满允许集而编造命题；把允许集空缺当成编译失败或 Confirm 失败。

## 6. 提示词

主图继续 `illustration-hero-v1`，字节合同不变。额外键使用新模板 `illustration-view-v1`，创建时按键各扩一份，快照进 intent。操作员不得改写。

每份 `illustration-view-v1` 必须包含：

- 该键的画法说明（见下表），且**恰好一张图、单一主体**；
- **画面中不得出现任何文字、字母、数字、标题、标签、字幕、水印、UI 框**（与 hero 相同）；
- 主体显示名、分类三键、active `safety_scope` 原文（规则同 IMG-01）；
- **不含**任一命题 `claim` 全文、来源 locator、四卡槽、COPY、字号。

| 键 | 画法说明（写入提示词） | 额外禁令 |
| --- | --- | --- |
| `observe.three_view` | 同一对象的正/侧/顶，同一姿态与外形 | 不得写成三张独立图或拼贴文字标注 |
| `observe.section` | 从外面看不到的内部 | 未在知识里锁定的内部结构不得画成确定事实 |
| `observe.exploded` | 部件如何组合 | 不得把未锁定部件画进去 |
| `setting.in_situ` | 对象处于其生活/发现环境 | 不得把孩子的学习地画成对象家园 |
| `setting.interaction` | 对象与环境的互动 | 同上；不得把 `learning_place` 画成栖息地 |

`setting.*` 提示词无论 current 是否含 `learning_place` 实例，都必须含「学习地 ≠ 栖息地」禁令。测试断言该句存在，不靠像素分类器。

模板变更必须改 `prompt_template_id` 或内容 digest。已创建 intent 继续用创建时各键快照。

## 7. 状态与上传

IMG-01 状态机不改：`open` → `illustrated` / `failed`；`cancelled` / `stale` 终态。

| 动作 | 允许状态 | 失败 |
| --- | --- | --- |
| 上传 hero | `open` / `failed`，摘要匹配 | 同 IMG-01 |
| 读/上传额外槽 | 仅 `illustrated`，摘要匹配 | `open` 下 → `ILLUS_NOT_ILLUSTRATED`；`stale` → `ILLUS_CURRENT_MOVED` |
| 覆盖已有额外槽 | `illustrated`，摘要匹配 | 成功则更新该键 sha；intent 保持 `illustrated` |
| cancel | 同 IMG-01 | 额外 PNG 随 intent 作废，不再当作有效资产 |

无 claim、无租约。额外槽缺失不是 `failed`。

## 8. 磁盘

候选根下，不进 library current 目录（沿用 IMG-01 根）。`store.intent_dir` 仍是 `{root}/{intent_id}/`：

```text
{intent_id}/
  meta.json                 # 增 allowed_view_keys、views.{key}.png_sha256、view_prompt_template_*
  expanded_prompt.txt       # isolate / IMG-01，不变
  hero.png                  # 仅 illustrated
  views/
    observe.three_view.prompt.txt
    observe.three_view.png      # 可选
    …
```

只为**允许集内**的键写 `.prompt.txt`。未上传则没有对应 `.png`。禁止对不允许的键建文件。`meta.json` schema id 保持 `cognitive-card-illustration-intent-v1`；新增字段必须可缺省，使本刀之前的 intent 仍能读（无 `allowed_view_keys` 视为空允许集，行为等于纯 IMG-01）。

## 9. HTTP

前缀仍是 `/card-os/api/v1/admin/knowledge-illustration`。IMG-01 五条路由语义不变。

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| GET | `/{intent_id}` | 除 IMG-01 字段外：`allowed_view_keys`（只列出允许的；稳定序固定为 `observe.three_view`、`observe.section`、`observe.exploded`、`setting.in_situ`、`setting.interaction`，跳过不在允许集的键）；`views`：每允许键含是否已有 PNG、`png_sha256`（无则 null）、该键 `expanded_prompt` |
| POST | `/{intent_id}/views/{key}/image` | `multipart` 字段 `image` + `actor`；`key` 为 `{role}.{view}`；仅 `illustrated` 且摘要匹配且 key ∈ 允许集 |
| GET | `/{intent_id}/views/{key}/image` | 该键已有 PNG 且 `illustrated` 且摘要匹配；`Cache-Control: private` |

`key` 不在允许集 → `ILLUS_SLOT_NOT_ALLOWED`。view id 不是图例登记画法 → `LEGEND_VIEW_UNKNOWN`。PNG 上限、魔数、鉴权与 IMG-01 相同。检测器判定烧字 → `LEGEND_BURN_IN`，不写（或不替换）该键 PNG。

无 token：JSON 不得 200 空成功；额外图 URL 不得匿名读取。不新增 Nginx location。不新增 capability。

CLI 与 HTTP 同一函数。library 根由调用方显式注入。本机验收不得复用现网 KNOW-04 library 路径。

## 10. 烧字检测器

每份提示词的无字条款是合同，不是检测器。

仅**额外槽**上传在写入前调用 `detect_burn_in(png_bytes) -> bool`。hero 仍只走 IMG-01 的 PNG 魔数与大小检查，以免改主图合同。

- 本刀默认实现返回 false（不假装有 OCR）。
- 测试可注入对指定夹具返回 true 的检测器。
- true → `LEGEND_BURN_IN`；intent 保持 `illustrated`；该键旧 PNG 若有则保留、新字节不落盘。

生产 OCR、人工看图外形 QA 不在完成条件里。

## 11. 操作台

路径仍是 `/card-os/ops/illustration/{intent_id}`。`illustrated` 后在主图与命题列表之外增加「额外视图」区：

- 只渲染 `allowed_view_keys`；
- 每键：复制该键提示词、上传 PNG、已上传则缩略图；
- 未上传的键显示为可空，不报错；
- 不展示不允许的键，不展示 chrome 角色。

无 token 的 HTML 壳不得内嵌额外提示词或额外图字节。Token 规则同 WB-01。

## 12. 错误码

| 码 | 含义 |
| --- | --- |
| `ILLUS_SLOT_NOT_ALLOWED` | 额外键不在允许集（无实例、非本刀像素键、旧 intent 无字段） |
| `LEGEND_VIEW_UNKNOWN` | `{view}` 不是 `projection-legend-v1` 已登记画法 |
| `LEGEND_BURN_IN` | 检测器认为画面含可读书面字 |

既有 `ILLUS_*`、`LEGEND_*`（除上表新接线）、`OPS_NOT_FOUND`、AUTH 码语义不变。不新增「视法未出齐」码。

`learning_place` 画成栖息地：用 setting 提示词禁令覆盖；不单列上传错误码（无像素分类器）。请求 `learning_place.*` 走 `ILLUS_SLOT_NOT_ALLOWED`。

## 13. 与 COMPOSE-01 / RENDER-02

COMPOSE-01 继续只取 `hero.png`。本刀 focused 测试须断言 compose 夹具不读取 `views/`。

RENDER-02 可按 sha 引用已存额外 PNG；不得把本刀完成条件写成「四卡上已有三视板」。无图 generate 路径保持可用。

不得把额外视图登记为新的 `projection.family`。

## 14. 验收

本机：显式 library 根 + 夹具 PNG。不要求本刀会话打开 ChatGPT。不安装现网。

必须成立：

1. **无实例不请图**：current 经 `assign_legend` 后无 `setting` 实例 → GET 的 `allowed_view_keys` 不含 `setting.*`；POST `setting.in_situ` 图 → `ILLUS_SLOT_NOT_ALLOWED`；磁盘无该键文件。有 `observe` 无 `setting` 时 observe 三键可列。
2. **可选子集**：允许 `observe.exploded` 但不上传 → intent 保持 `illustrated`；GET 该键 `png_sha256` 为 null；不产生失败码。
3. **烧字失败**：注入检测器对夹具返回 true → 额外槽 POST 得 `LEGEND_BURN_IN`；该键无新 PNG。默认检测器不阻挡合法夹具 PNG。
4. **`learning_place` 不得画成栖息地**：`setting.*` 在允许集内时，其 `expanded_prompt` 含学习地 ≠ 栖息地禁令；POST `learning_place.isolate`（或任何 `learning_place.*`）→ `ILLUS_SLOT_NOT_ALLOWED`。
5. 无 observe 实例时允许集不含 observe 额外三键；IMG-01 仍可对同一 slug 建 intent 并上传 hero（与今日合同一致）。
6. `open` 时 POST 额外槽 → `ILLUS_NOT_ILLUSTRATED`。`illustrated` 后可传、可覆盖。
7. current 前进后 GET/POST 额外槽 → `stale` + `ILLUS_CURRENT_MOVED`。
8. 额外提示词不含任何 `claim` 全文；无 token 拉不到额外 PNG。
9. 既有 IMG-01 / COMPOSE-01 focused 回归仍过；compose 不读 `views/`。
10. 现网应用、Nginx、生产 library、画廊包摘要不被本刀改写。

测试落在 server worktree 的 illustration + legend 相关 unittest，并纳入既有 combined focused 门禁（或与 illustration 测试并列的显式命令）。不要求完整 suite 清零既有 real-uvicorn 502。不要求真实 ChatGPT 会话。不要求生产安装。

## 15. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓：本设计、路线图、任务/交接、文档地图。

优先：允许集、`illustration-view-v1`、额外槽读写、ops 额外视图区、烧字检测注入点。不接图像 API，不接 Skill claim，不改 Nginx，不写生产 library，不改四对象，不改 COMPOSE 主图带，不实施 RENDER-02。

本文件不授权 merge 进 server `main`、不授权现网。
