# 操作台按映射生成并上架（WB-03）

- Status: Approved for this execution tranche
- Date: 2026-09-01
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[CONV-01](2026-08-30-knowledge-four-card-converter-design.md)、[AGE-01](2026-08-31-age-language-adapter-design.md)、[RENDER-01](2026-08-31-locked-four-card-render-design.md)、[加权版式](2026-09-02-mapping-artifact-weighted-layout-design.md)、[QA-01](2026-08-31-strict-qa-human-review-design.md)、[PUBLISH-01](2026-08-31-immutable-package-publish-design.md)、[PORTAL-01](2026-08-31-published-artifact-gallery-design.md)、[ACCEPT-01](2026-08-31-rabbit-end-to-end-acceptance-design.md)、[WB-01](2026-08-31-operator-knowledge-workbench-design.md)
- Does not implement: [四卡文字成熟投影](2026-08-31-four-card-text-mature-projection-design.md)（保持 Parked；本文件只吸收其 COPY 放宽与来源标题，**不**吸收「溢出命题进来源区」）
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

按主路径补上确认点 2（发布 Artifact）：

1. 操作员在令牌操作台对**已锁定**的 four-card mapping revision 点「生成」；
2. 服务器用映射槽位 + AGE/安全登记 + 与 RENDER 相同的几何预演，写出文字成熟的锁定四卡（无插图）；
3. 机器 QA 通过后停在 `awaiting_review`，操作台可预览四页；
4. 操作员点「批准并上架」后，以人类 actor 写入 QA approve，再 PUBLISH 到本机 package catalog；`package_slug` 等于 topic slug；
5. 本机 PORTAL 画廊该 slug 的 current 指向新 revision。未锁定 mapping、非 four-card、映射已过期，一律不得生成。

本设计满足路线图 `WB-03` 在本刀的范围。知识 current 仍是知识源；mapping 包不得被 `publish` 成 current。

## 2. 非目标

- 不调用 Skill / executor / 0.3.1 packet 领取，不写出客户端 `production-record-v1` 全量生成器，不生图。
- 不把溢出命题写进知识卡来源区；不缩小字号硬塞。
- 不改 Knowledge Core 字节；不把 mapping revision 设为 knowledge current；不调用会移动 `current.json` 的 library `publish`。
- 不改现网画廊 ACCEPT-01 `package_sha256`；不写生产 package catalog；不打应用 release；不 reload Nginx；不 merge server `main`；不 push。
- 不在公网画廊加操作台链接；不把草稿/预览 PNG 挂到公开 `/card-os/packages/`。
- 不编译自由 prompt（`API-01`）；不改命题（更改）；不等于 AGE-02 / ACCEPT-02。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、packet 契约。
- 不重开 ACCEPT-01 编排器，不要求六主题全部上架。

## 3. 在主路径中的位置

```text
知识源管理·浏览     WB-01
知识源管理·选择     WB-02：选 family
映射方案            WB-02：preview → lock_mapping（不抢 current）
        ↓
本刀·生成           mapping revision → FACT → 几何装箱 → RENDER → 机器 QA
本刀·确认点 2       批准并上架 → PUBLISH-01
        ↓
本机画廊            PORTAL-01 读 catalog current
```

相对 ADR-002：确认点 1 的映射半截已由 WB-02 完成；本刀完成确认点 2。

```text
library current          知识源；兔子 = chaptered-guide
        ↓
mapping.json             指向 four-card 映射 revision；current.json 不变
        ↓
本刀 convert_mapping     只读该映射目录；不入库 WIRE-01
        ↓
本刀 pack_from_mapping   槽位 node_ids → 锁定记录；装不下 fail closed
        ↓
RENDER / QA / PUBLISH    既有函数；catalog 独立于生产
```

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 输入 | `mapping.json` 指向的 revision，不是 knowledge current |
| 几何装不下 | 该槽主区 fail closed；来源区只显示机构标题 |
| 操作流 | 两步：生成 → `awaiting_review`；批准并上架 = 确认点 2 |
| 包身份 | `package_slug` = topic slug；新 revision 替换**本机** gallery current |
| 验收 | 只钉兔子；其他主题有合格 mapping 时可走同一路径，非完成条件 |
| 插图 | 无；图像轨空 |
| 交付面 | 本机操作台 + 独立 catalog；现网应用 / Nginx / 生产 catalog 不改 |
| 人类 actor | 批准并上架请求体必填；禁止 `qa-01-v1` / `publish-01-v1` / `machine`；验收默认 `owner` |

## 5. 准入

`generate_from_mapping(topic)` 同时满足才继续：

| 条件 | 失败码 |
| --- | --- |
| knowledge current 存在 | `MAPPING_NO_CURRENT` |
| `mapping.json` 存在且 `listed` | `ARTIFACT_NO_MAPPING` |
| `mapping.family` 为 `four-card` | `ARTIFACT_FAMILY_NOT_FOUR_CARD` |
| `mapping.source_current_revision` 等于当前 knowledge current 的 revision | `ARTIFACT_MAPPING_STALE` |
| 映射包事实载荷（对齐 revision 后）等于 current | `MAPPING_CORE_DRIFT` |
| 映射包 `projection-spec.blueprint.family` 为 `four-card` | `ARTIFACT_FAMILY_NOT_FOUR_CARD` |
| 安全登记可覆盖映射包全部 safety 英文原文 | `AGE_SAFETY_EXPRESSION_GAP` |
| 学习规格可组装完整四卡 request（不发明缺字段） | `ARTIFACT_REQUEST_REQUIRED` |

无 mapping 时操作台不展示可用的「生成」。`chaptered-guide` 等非 four-card 映射允许存在，生成必须拒绝。兔子验收另要求该 request 为深圳、`age-5-6`、中英双语、打印；缺一则失败，不发明默认值。

CONV-01 `convert_current` 行为不变：兔子 knowledge current 仍是 `chaptered-guide`，直接 convert 仍是 `CONVERTER_FAMILY_NOT_FOUR_CARD`。本刀不得靠先 `publish` 映射包来绕过。

WIRE-01「入库 revision 必须等于 current」不适用于本路径：`convert_mapping` 只写出接合 JSON 给装箱器，**不得**调用 compiled-job / `POST /admin/generation-inputs`。

## 6. 转换与装箱

### 6.1 `convert_mapping`

只读 mapping 目录四对象。`fact_from_knowledge_core` + `apply_age_language` 沿用 AGE-01。安全：`safety[].en` 必须与 Core 原文 Unicode 一致；`safety[].cn` 来自 WB-02 安全登记表；未命中不得生成。

`assemble_from_knowledge_revision` 的知识目录是**映射 revision 目录**，不是 current 目录。接合 JSON 的 `knowledge_revision` 记录映射 revision 号。

不得新增命题、不得改 claim/safety 英文原文。

### 6.2 `pack_from_mapping`

输入：接合 JSON + 映射 `projection-spec` 槽位 + 与 RENDER 相同的字体、字号、中英断行规则。区高：**等分四区不再用于本路径**；改走 [mapping-artifact 加权版式](2026-09-02-mapping-artifact-weighted-layout-design.md)（弹性区知识卡 `appearance`、观察卡 `look`）。ACCEPT-01 等分几何不变。

输出：RENDER-01 / QA-01 消费的锁定记录（`normalized_request`、`fact`、`cards`、`resolved_family`、`content_lock`）。确定性 lock 替代 Codex generate。不是第五个治理对象。

槽位 id 沿用 WB-02：`slot.{topic_slug}.{cn-observation|en-observation|cn-knowledge|en-knowledge}`。

| 区 | 规则 |
| --- | --- |
| 知识卡 `appearance` / `uncertainty` | 必须放下该语言知识槽**全部** `node_ids` 对应命题（active；中英集合相等）。`unknown` 进 `uncertainty`，其余进 `appearance`。下一条会触发 `TEXT_OVERFLOW` / `LAYOUT_OVERLAP` / `LAYOUT_OUT_OF_BOUNDS` → **整次生成失败**，不得把该命题改写入来源区 |
| 观察「看」 | 映射观察槽全部 `node_ids`；必须 ⊆ 同语言知识卡主区已出现的命题；≥ 2 个 distinct；中英集合相等；装不下同样 fail closed |
| 观察「记录」 | 无节点、无 COPY、无来源正文 |
| 来源区 | 只排 FACT 来源：主行 `title`，括号内 `source_id`。缺 title → `RENDER_SOURCE_TITLE_MISSING`。禁止出现命题 id 或命题全文 |
| 安全区 | `CN_*` 只排 `safety[].cn`；`EN_*` 只排 `safety[].en`。禁止中文页回落英文原文 |

FACT 中每条 active 知识命题必须属于知识槽 `node_ids`。多出未映射命题 → `ARTIFACT_FACT_UNMAPPED`。槽内 node 在 FACT 中缺失 → `ARTIFACT_SLOT_NODE_MISSING`。

插图轨空。`record` / `trace` / `copy` / `sources` / `safety` / `confusion` 仍清场，不得进图。

不调用 ACCEPT-01 §5 第 2 条（英文行数装箱 + 溢出到来源区）。该规则只约束历史 ACCEPT-01 包，本路径不得使用。

### 6.3 COPY / 描红（本路径覆盖 AGE-01 §4.3）

在知识卡主区文本确定之后，由装箱器重算 `copy_plan`，供 RENDER-01 覆盖观察卡动作区。COPY 区预演几何改走 [加权版式 §5.2](2026-09-02-mapping-artifact-weighted-layout-design.md)（随 `look` 最小高度停止追加），不再使用等分 `max_lines`。

| 年龄 | COPY | 描红 |
| --- | --- | --- |
| `age-3-4` | 仍抑制（空列表） | 沿用 AGE-01 |
| `age-5-6` | 按同语言知识卡 `visible_text` 句子顺序切**精确 span**；能整句则整句；加入后 COPY 区预演溢出则停止。**不**再适用「每语言最多 2 句 / CN≤12 字 / EN≤8 词」 | 每语言 1–6 项精确 span |

span 必须能切片还原；找不到任何合法 COPY span（`age-5-6`）→ `AGE_COPY_SPAN_UNAVAILABLE`。COPY 区装不下后续句只停止追加，**不**因此失败整卡——前提是知识卡主区已经 fail-closed 装下全部映射命题。

本覆盖只作用于 mapping-artifact 路径。`convert_current` / ACCEPT-01 历史锁不改 AGE-01 §4.3。

### 6.4 摘要

`content_lock.sha256` 由服务器复算 `artifacts + change_policy`。`render_input_sha256` 纳入适配器版本、`safety-expression-registry-v1`、装箱器版本。同一映射身份两次生成，在相同 `at` 下锁与渲染摘要稳定。

## 7. 工作区与幂等

生成写入独立工作根，不得写入 knowledge-library，不得写入 package catalog：

```text
{candidate_root}/artifact-work/{topic}/
  mapping-identity.json     # 映射 revision 与四对象摘要
  convert/joined.json
  record/locked-record.json
  render/                   # 四页 PNG + print.pdf + layout 报告
  qa/qa-report.json
  qa/audit.jsonl
```

| 情况 | 行为 |
| --- | --- |
| 同一 mapping identity 且已有 `awaiting_review` | 不重渲；返回已有工作区 |
| 同一 identity 且 `machine_failed` | 允许再次生成，覆盖工作区，不碰 catalog |
| mapping pointer 已前进 | 新工作区对应新 identity；GET artifact 只看当前 mapping |
| 批准并上架时 QA 已是 `approved` 且 catalog current 已是该 lock | 幂等返回已有 package current |
| 已 `approved` 但 publish 未成功 | 只重试 `publish`，不重跑机器 QA |

草稿对公开观众等同不存在。

## 8. 操作台与 HTTP

本机 loopback 扩展 WB-01/WB-02 详情页，不改公网画廊。第三块映射方案保留。新增第四块 **产物**：

1. 当前 mapping revision / family / 是否过期
2. 按钮「生成」：仅当 §5 准入可满足时可用；无「生成并上架」
3. 状态：无产物 / 生成失败码 / `awaiting_review` / 已上架 revision
4. `awaiting_review` 时预览四页（admin 鉴权拉 PNG；HTML 壳仍不得预渲染命题）
5. 按钮「批准并上架」：仅 `awaiting_review` 可用；请求带人类 `actor`（界面默认 `owner`，可改，不得空）
6. 上架成功后显示 package revision；操作台可链到本机 `/card-os/` 该包页。公网画廊不加回链

写路径（admin Bearer，与 WB-01 同一前缀 `/card-os/api/v1/admin/knowledge-library`）：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `.../{topic}/artifact-generate` | `generate_from_mapping`；无 body |
| GET | `.../{topic}/artifact` | 当前 mapping 对应工作区状态；无则 `listed=false`、HTTP 200 |
| GET | `.../{topic}/artifact/cards/{page}` | `page` ∈ `cn-observe` / `en-observe` / `cn-know` / `en-know`；admin 返回 PNG；无产物或非法 page → `OPS_NOT_FOUND`；非 admin 不得 200 |
| POST | `.../{topic}/artifact-publish` | body `{"actor":"..."}`；QA `approve` + PUBLISH-01 `publish`；slug=topic |

无 token：与 WB-01 相同，JSON 不得 200 空成功；HTML 壳不得含命题或预览图。不新增公网匿名端点。不新增 Nginx location（走既有 `/card-os/api/` 与 `/card-os/ops/`）。

「批准并上架」不提供本刀必做的 reject。拒绝仍可用 QA-01 CLI。

CLI 与 HTTP 同一函数。测试可只跑 CLI。

Catalog 根必须由调用方显式注入（CLI `--catalog-root` 或测试夹具）。HTTP 本机验收把 catalog 指到临时/夹具目录，**不得**复用现网 PORTAL 正在服务的 catalog 路径。本刀验收禁止改写现网 `rabbit` `package_sha256`。

## 9. 发布后画廊

PUBLISH-01 合同不变：不可覆盖 revision；内容不同则新序号，`supersedes` 旧序号；旧目录保留。visibility 缺省 `public`。

本机 PORTAL 列出新 current。若夹具 catalog 已有 ACCEPT-01 风格 `revision-0001`，本刀成功后为下一号，且 `revision-0001` 字节不变。若 catalog 为空，则本刀写出 `revision-0001`。

现网 `https://www.yutou.space/card-os/` 在本刀结束后仍展示 ACCEPT-01。安装本刀应用到生产、reload Nginx、把本机 catalog rsync 到现网，均须另立会话授权。

## 10. 错误码

| 码 | 含义 |
| --- | --- |
| `ARTIFACT_NO_MAPPING` | 无 mapping pointer |
| `ARTIFACT_FAMILY_NOT_FOUR_CARD` | 映射不是 four-card |
| `ARTIFACT_MAPPING_STALE` | mapping 的 source current 已不是 knowledge current |
| `ARTIFACT_REQUEST_REQUIRED` | 映射包无法组装完整四卡 request |
| `ARTIFACT_FACT_UNMAPPED` | FACT 有未进入知识槽的 active 知识命题 |
| `ARTIFACT_SLOT_NODE_MISSING` | 槽内 node 在 FACT 中不存在 |
| `ARTIFACT_NOT_AWAITING_REVIEW` | 批准并上架时不是 `awaiting_review` |
| `MAPPING_NO_CURRENT` / `MAPPING_CORE_DRIFT` | 沿用 WB-02 |
| `AGE_SAFETY_EXPRESSION_GAP` / `AGE_EXPRESSION_GAP` / `AGE_COPY_SPAN_UNAVAILABLE` | 沿用 AGE / WB-02 |
| `RENDER_SOURCE_TITLE_MISSING` | 来源无 title |
| `TEXT_OVERFLOW` / `LAYOUT_*` | 几何预演或最终排版失败（含知识主区或观察「看」装不下） |
| `QA_*` / `PUBLISH_*` / `OPS_NOT_FOUND` | 沿用 QA-01 / PUBLISH-01 / WB-01 |

本路径上 QA-01 `QA_SAFETY_REWRITTEN` 的比较对象是锁定记录 FACT 的分语言字段（CN 页对 `cn`，EN 页对 `en`），不是要求 `cn` 等于 Core 英文。`QA_PROPOSITION_DRIFT`：中英知识卡**主区**命题 id 集合等于 FACT；来源区不得含命题 id。`QA_SOURCE_MISSING`：全部 FACT `source_id` 出现在来源区标题行。

不得为填满而发明命题。

## 11. 验收

本机：生产同构的 library 兔子 current（KNOW-04 `revision-0002` 或等价 chaptered-guide）+ 已 `lock_mapping(family=four-card)` + 独立 catalog + 本机操作台/CLI。不安装到现网。

必须成立：

1. 无 mapping 或 family 非 four-card：生成失败；knowledge `current.json` 与 Core 字节不变。
2. 锁定 four-card 后生成：写出四页 PNG 与 A4 PDF；状态 `awaiting_review`；catalog 尚无新 current（或仍为夹具旧 revision）。
3. 中文知识卡可见命题 ≥ 4 条 distinct `proposition_id`，且主区包含该槽全部映射节点；观察「看」≥ 2 且 ⊆ 知识主区；记录无正文；来源区含机构标题（`Description and Physical Characteristics of Rabbits` / `Diet for Rabbits` / RSPCA 之一），不见命题溢出。
4. 中文安全区为登记汉字；对应 `safety[].en` 等于 Core 原文；无溢出/重叠/越界。
5. COPY/描红为知识卡精确 span，可切片还原。
6. `actor=owner` 批准并上架后：本机 catalog `rabbit` current 为新 revision；QA `approved`；夹具中既有 ACCEPT-01 目录字节不变（若存在）。
7. knowledge `current.json` 在生成与上架前后仍指向原知识源 revision；`mapping.json` 不被上架改写。
8. 不带 token 的 ops 壳不含命题正文或预览图；公开 `/card-os/packages/` 未挂草稿。
9. 现网 ACCEPT-01 `package_sha256` 不被本刀改写。

若兔子该知识槽**全部**映射命题无法落入知识卡主区：生成必须失败，完成条件不成立。不得改回溢入来源区来换取 Done。AUTHOR-02 / KNOW-04 兔子当前为 9 条命题（全部 `known`），不是 8。等分四区装不下时，排版合同见 [mapping-artifact 加权版式](2026-09-02-mapping-artifact-weighted-layout-design.md)；不得为此改 Core。

2026-09-02：操作者看过加权四卡 PNG/`print.pdf`，接受基础信息；打印样式（区框、留白、字重、标签等）未验收。该观感不阻断本刀本机 `DONE`。样式调优后置到全部阶段完工后，以最终投影产物反查各阶段；不以当前四卡观感另开切片。

测试：`convert_mapping`、装箱 fail-closed、过期 mapping、ops 生成/发布幂等、既有 WB-01/WB-02 与 QA/PUBLISH focused 回归。不要求完整 suite 清零既有 real-uvicorn 502。不要求生产安装本刀应用。

## 12. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓：本设计、路线图、任务/交接、文档地图。

优先：`convert_mapping`、`pack_from_mapping`（几何预演 fail-closed）、artifact 工作区、ops 第四块与三条 admin 路由、本路径 COPY 计划。RENDER 按新锁定记录绘制来源标题与分语言安全区；不重渲 ACCEPT-01。不接生图，不改 Nginx，不写生产 catalog。

ACCEPT-01 CLI 保留。本刀新 CLI 可与 HTTP 共用函数，例如 `python3 -m cognitive_card_server.knowledge_ops` 子命令 `artifact-generate` / `artifact-publish`。
