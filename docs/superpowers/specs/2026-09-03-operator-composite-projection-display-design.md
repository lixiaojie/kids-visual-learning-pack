# 操作台合成展示（COMPOSE-01）

- Status: Approved for this execution tranche
- Date: 2026-09-03
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-003](../../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[IMG-01](2026-09-02-operator-illustration-hero-page-design.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[WB-03](2026-09-01-operator-mapping-artifact-publish-design.md)、[加权版式](2026-09-02-mapping-artifact-weighted-layout-design.md)、[RENDER-01](2026-08-31-locked-four-card-render-design.md)
- Does not implement: OpenAI 图像 API；ChatGPT 整卡烧字；Codex claim；新 Projection family；知识卡插图；可交互烧字页；Pillow 样式大改；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把已经分开的两段产物合成孩子能看的投影，且字形仍由服务器排：

1. IMG-01 已上传的一张**无字**主体 PNG（按 sha 引用）；
2. WB-03 已生成的**锁定四卡文案**（AGE 改编后的观察/知识卡）。

本刀交付两种 Renderer Binding，同一份内容锁：

| 终端 | 产物 | 文字 |
| --- | --- | --- |
| 屏幕 | 操作台 HTML 一页四段 | 真 DOM 文本，CSS 可好看 |
| 打印 / 本机画廊 PNG | Pillow 四卡；仅观察卡页顶图像带 | 加权版式字形 |

ChatGPT 不发第二轮整卡提示词，不把 `claim` 或四卡文案烧进图。

## 2. 非目标

- 不接图像 API、Cookie、会员会话、Skill claim / 租约。
- 不改 `generate_from_mapping` 的无图成功路径；没图时文字四卡仍可生成。
- 不把「图装得下」写成知识源准入或 Confirm current 条件。
- 不注册新 `projection.family`；不改四对象 schema、KNOW-04 六主题 current。
- 不把 PNG 写入 Knowledge Core 或 mapping revision。
- 不给知识卡插图；插图不得进入 `record` / `trace` / `copy` / `sources` / `safety` / `confusion`。
- 不重开 Pillow 配色/字体大改（样式仍后置）。
- 不打 release、不 reload Nginx、不 merge server `main`、不 push、不写生产 library / catalog。
- 不把 IMG-01 spec 的完成条件改成本刀。

## 3. 在主路径中的位置

```text
library current
    ├─ IMG-01 illustration-intent → illustrated hero.png
    └─ WB-02 lock_mapping → WB-03 generate_from_mapping → artifact-work 文字四卡
            ↓
本刀 compose          两输入都在且身份一致才继续
            ├─ 屏幕 HTML（ops /compose/{topic}）
            └─ 重渲观察卡 PNG/PDF（图像带 + 原锁定文案）
```

相对 ADR-002：本刀是 Renderer Binding，不是第五个治理对象。

WB-03 无图路径保持可用。合成是其后另一步。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 输入门禁 | 同一 `topic`：有效 `illustrated` intent **和** `awaiting_review` 的 mapping-artifact 工作区 |
| 身份 | illustration-intent 六键等于 **knowledge current**；`mapping.source_current_revision` 等于该 current revision；工作区 `mapping-identity.json` 等于现活 mapping pointer |
| 主图位置 | 只进 `CN_OBS` / `EN_OBS` 页顶图像带；知识卡像素与无图生成相同 |
| 图像带 | 上限 `OBS_IMAGE_BAND_PX = 720`；实际高度 = min(720, 观察卡弹性区扣掉 `look` 正文后的剩余 − `ZONE_GAP_PX`)；`contain`、禁止裁切；不是 `zone_order` 里的新区。剩余不足以支付 gap 则 `TEXT_OVERFLOW`。屏幕 HTML 仍用完整主图，不受打印剩余限制。 |
| 屏幕 | 一页四段，页序 `CN_OBS → EN_OBS → CN_KNOW → EN_KNOW` |
| 文字权威 | `artifact-work/{topic}/record/locked-record.json` 的锁定区文案，不是 Core `claim` 原文（观察/知识卡已经 AGE） |
| ChatGPT | 继续只出无字图 |
| 交付面 | 本机操作台 + 显式 candidate 根；现网应用 / Nginx / 生产 library / 画廊不改 |

## 5. 准入

`compose_projection(topic)` 同时满足才继续：

| 条件 | 失败码 |
| --- | --- |
| `topic_slug` 合法 | `ILLUS_SLUG_INVALID`（沿用） |
| 该 slug 有 library current | `MAPPING_NO_CURRENT` |
| 存在状态 `illustrated` 且摘要仍匹配的 intent | `COMPOSE_NO_ILLUSTRATION`；current 已动则 `ILLUS_CURRENT_MOVED` |
| `artifact-work/{topic}` 存在且 QA `awaiting_review` | `COMPOSE_NO_ARTIFACT` |
| 工作区 `mapping-identity.json` 等于现活 mapping pointer | `COMPOSE_IDENTITY_MISMATCH` |
| illustration 六键等于 knowledge current，且 `revision` 等于 `mapping.source_current_revision` | `COMPOSE_IDENTITY_MISMATCH` |
| mapping pointer 仍钉当前 current（与 WB-03 相同） | `ARTIFACT_MAPPING_STALE` |
| 人类 actor，非保留名 | `ILLUS_UNAUTHORIZED`（沿用 actor 规则） |

禁止把图放进清场区。compose 只构造 `CN_OBS:band` 与 `EN_OBS:band` 两个资源键。其它键若进 RENDER → `RENDER_ASSET_IN_CLEAR_ZONE` 或 `COMPOSE_ASSET_IN_CLEAR_ZONE`。

几何失败沿用 `TEXT_OVERFLOW` / `LAYOUT_*`。不得缩小字号、不得把命题写入 `record`。

`generate_from_mapping` **不得**因缺少插画而失败。

## 6. 磁盘

候选根下，不进 library current 目录：

```text
{candidate_root}/compose/{topic}/
  meta.json
  view/index.html      # 可选落盘副本；操作台仍以鉴权 JSON + 媒体为准
```

`meta.json` 至少含：`schema`、`topic_slug`、`intent_id`、`hero_png_sha256`、`identity`（六键）、`mapping_identity`、`content_lock_sha256`、`actor`、`created_at`。

打印仍写 `{candidate_root}/artifact-work/{topic}/render/`：compose **重渲**四页。知识卡 PNG 字节必须与本次 compose 之前该工作区中的知识卡 PNG 相同。观察卡两页与 `print.pdf` 更新。不得改 `record/locked-record.json`。

主图继续只存在于 `illustration-intents/{intent_id}/hero.png`，按 sha 读取，不复制进 Knowledge Core。

## 7. 打印图像带

观察卡区序仍是 `look` / `record` / `trace` / `copy`。清场区不能进图，因此**不把主图塞进 `look` 文本区**，也不使用 RENDER-01 区底 120–260 px 的旧资产槽作为本刀主路径。

Renderer Binding：

1. 先按无图像带的加权公式得到观察卡 `look` 剩余；
2. 实际带宽 = min(720, 剩余 − `ZONE_GAP_PX`)；
3. 在页顶安全边距之下画该带；带与第一区之间保留 `ZONE_GAP_PX`（24 px）；
4. `allocate_zone_heights` 的 `usable` 扣除 `band + 24`；本次 compose 的预演与 RENDER 必须用同一套扣减；
5. 图 `contain` 进该带，禁止裁切。

兔子夹具实测 `look` 剩余约 117 px，因此打印带会远小于 720；屏幕 HTML 仍展示完整 PNG。装不下（剩余 ≤ gap）→ 本投影失败，不回写 Core。

无图的 `generate_from_mapping` 继续用不扣图像带的加权公式，以免改 WB-03 已验收的文字四卡。

兔子 mapping-artifact 夹具加带后 `look` 必须仍装得下。装不下 → 本投影失败，不回写 Core。

知识卡页 `top_band_px = 0`。

## 8. 屏幕 HTML

路径 `/card-os/ops/compose/{topic}` 必须注册在 `/card-os/ops/{topic}` 之前。

无 token 的 HTML 壳不得内嵌锁定文案、`claim` 或图片字节。Token 仍放 `sessionStorage`，规则与 WB-01 相同。

鉴权后一页四段：

- `CN_OBS` / `EN_OBS`：主图 + 该页各区锁定 `visible_text`（含 COPY / 描红）；
- `CN_KNOW` / `EN_KNOW`：无图，只排锁定文案。

主图经已有 `GET .../knowledge-illustration/{intent_id}/image` 拉取。禁止匿名读图。

主题详情页增加「合成展示」入口；仅当该 topic 有 current 时显示按钮，真正能否合成仍由 POST 门禁决定。

## 9. HTTP

Admin（`Authorization: Bearer` admin）：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/card-os/api/v1/admin/knowledge-compose` | body `topic_slug`、`actor`；推导该 slug 唯一有效 `illustrated` intent |
| GET | `/card-os/api/v1/admin/knowledge-compose/{topic}` | 状态 + `intent_id` + `hero_png_sha256` + 四页锁定区文案；无则 `COMPOSE_NO_ARTIFACT` / `COMPOSE_NO_ILLUSTRATION` |

不新增 capability。已发布 Skill `0.1.1` 的 `read` / `submit` 不能打此面。不新增 Nginx location。

同一 topic 重复 POST 且输入身份未变：幂等返回已有 meta，可重渲观察卡（结果字节稳定）。

## 10. 错误码

| 码 | 含义 |
| --- | --- |
| `COMPOSE_NO_ILLUSTRATION` | 没有有效 `illustrated` 主图 |
| `COMPOSE_NO_ARTIFACT` | 没有 `awaiting_review` 的文字四卡工作区 |
| `COMPOSE_IDENTITY_MISMATCH` | 插画 identity 与 mapping-identity 不一致 |
| `COMPOSE_ASSET_IN_CLEAR_ZONE` | 试图把图放进清场区或知识卡 |
| `TEXT_OVERFLOW` / `LAYOUT_*` | 加图像带后几何失败（沿用） |

鉴权失败继续使用既有 AUTH 码。current 前进沿用 `ILLUS_CURRENT_MOVED` / `ARTIFACT_MAPPING_STALE`。

## 11. 验收

本机：显式 library / candidate 根（不是现网 KNOW-04 路径）。测试用夹具 PNG。不要求本刀会话打开 ChatGPT。不安装到现网。

必须成立：

1. 无 illustrated intent → `COMPOSE_NO_ILLUSTRATION`；无 artifact 工作区 → `COMPOSE_NO_ARTIFACT`；library current 字节不变。
2. intent identity 与 mapping-identity 六键不同 → `COMPOSE_IDENTITY_MISMATCH`。
3. 两输入齐全且身份一致：GET 返回四页锁定文案；观察段声明有主图；知识段无主图。
4. 鉴权 GET 插画 image 的 sha 等于 intent `hero_png_sha256`；无 token 不能拉到图；无 token 的 compose HTML 壳不含锁定正文。
5. 重渲后 `cn-know.png` / `en-know.png` 字节与 compose 前相同；`cn-observe.png` / `en-observe.png` 改变。
6. `generate_from_mapping` 在没有插画时仍 `awaiting_review`。
7. 兔子 mapping-artifact 夹具 compose 不得因图像带 `TEXT_OVERFLOW`。
8. 现网应用、Nginx、生产 library、画廊包摘要不被本刀改写。

测试：门禁与身份、HTML 壳、OBS 图像带与加权共用区高、知识卡像素稳定、既有 IMG-01 / WB-03 focused 回归。不要求完整 suite 清零既有 real-uvicorn 502。不要求生产安装。

## 12. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓：本设计、实施计划、路线图、任务/交接、文档地图。

优先：`compose_projection` 门禁、ops HTML、OBS 图像带重渲。不接图像 API，不改 Nginx，不写生产 library，不改四对象，不把无图 generate 焊死到必须有图。
