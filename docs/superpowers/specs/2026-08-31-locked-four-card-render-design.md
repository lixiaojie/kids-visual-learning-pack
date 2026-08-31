# 锁定内容四卡排版与 A4 PDF（RENDER-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-001](../../decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §3.3 / §4.4](../../cognitive-card-os-system-design.md)、[AGE-01](2026-08-31-age-language-adapter-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把**已锁定**的 four-card 内容排成可打印四页，并装订为 A4 PDF：

1. 只消费内容锁与锁定卡片文本，不回写 Knowledge Core，不发明命题；
2. 固定页序 `CN_OBS` → `EN_OBS` → `CN_KNOW` → `EN_KNOW`；
3. 观察卡 COPY / 描红由 AGE-01 `copy_plan` 重算，不采用 generate 写入的 COPY；
4. 渲染输入与输出字节均有摘要。

本设计满足路线图 RENDER-01 完成条件中的排版与打印合同。完整视觉 QA、人工复核与不可变发布仍属 QA-01 / PUBLISH-01。

## 2. 非目标

- 不改四对象 schema、v1 FACT 键集、packet 契约、AUTHOR-05 默认表。
- 不等于 PORTAL-01 / QA-01 / PUBLISH-01 / TMPL-01 / KNOW-01 / AGE-02。
- 不把存档客户端 `governed.lock`、恐龙-only `FAMILY_ID` 钉死或 ChatGPT generation-input 合入服务器。
- 不新增 HTTP 端点；不 merge server `main`；不 push；不现网。
- 不要求真实高视觉素材上的观感验收（路线图已记录该缺口）。

## 3. 在分层中的位置

```text
Knowledge Core          事实；禁止呈现方案
        ↓
AGE-01 + CONV-01        儿童表达写入 FACT；copy_plan 不进 generation-input
        ↓
锁定 production-record  content_lock + 四卡文本 + FACT
        ↓
RENDER-01（本设计）     copy_plan 覆盖观察卡动作区 → A4 PNG + PDF
        ↓
QA-01 / PUBLISH-01      后期
```

渲染器是投影，不是第五个治理对象。

## 4. 准入与消费面

输入是一份锁定记录（可为 production-record 子集），同时满足才渲染：

| 条件 | 失败码 |
| --- | --- |
| `content_lock.sha256` 为 `sha256:` + 64 位小写 hex | `RENDER_LOCK_MISSING` |
| 若带 `artifacts` + `change_policy`，复算摘要必须等于声明值 | `RENDER_LOCK_MISMATCH` |
| `resolved_family.contract.page_order` 恰好四页且顺序固定 | `RENDER_PAGE_ORDER` |
| 每页 `zone_order` 等于 family `page_zones` | `RENDER_ZONE_DRIFT` |
| `normalized_request` 可被 AGE-01 `resolve_profile` 解析 | 沿用 AGE_* |
| FACT 命题可供 `copy_plan` | 沿用 AGE_* |

渲染**覆盖**观察卡 `copy` / `trace` 的可见文本：以 `copy_plan` 为准。记录里 generate 写入的 COPY 不得出现在输出字形中。

知识卡可见文本保持锁定记录原样。每个 COPY/描红 `text` 必须是同语言知识卡全部 `visible_text` 的子串，否则 `RENDER_COPY_NOT_ON_SOURCE`。`source_card` / `action_card` 只用于落位，不授权改写知识卡。

安全区只排 FACT `safety` 原文。排版不得改写确定性、来源 id 或安全边界。

## 5. 排版与打印

抢救（ADR-001）采用存档 renderer 的合同，而不是其客户端工作区：

- 页面：A4 竖版 300 dpi（2480×3508 px），安全边距 12 mm。
- 字体：发布批准的 CJK 字体（本机首版 `Arial Unicode.ttf`）；记录 filename + SHA-256 + 字号；不得低于 16 pt。测试可注入路径，不得用缺字默认位图冒充中文。
- 中文按字断行，英文按空格断行；溢出 `TEXT_OVERFLOW`，重叠 `LAYOUT_OVERLAP`，越界 `LAYOUT_OUT_OF_BOUNDS`。
- 无 family `layouts` 时：按 `zone_order` 单列等分行高填满安全区（mammal `age-5-6` 四区）。带 `layouts` 的 family 才走多列行配置。
- 图像轨可选。资产 `contain` 缩放、禁止裁切。`record` / `trace` / `copy` / `sources` / `safety` / `confusion` 清场，插图不得进入。无资产时仍输出文本忠实四页。
- PDF：四页同尺寸、显式 CropBox；页序与 PNG 一致。

机器打印 QA（本批次，不是 QA-01）：四页、A4 尺寸、无溢出/重叠/越界、COPY span 可切片还原、清场区无插图。

## 6. 摘要

| 摘要 | 覆盖 |
| --- | --- |
| `content_lock_sha256` | 输入声明并（在可复算时）核验的内容锁 |
| `render_input_sha256` | 渲染器版本、family id、页序、知识卡可见文本、`copy_plan`、字体身份、内容锁 |
| 每页 PNG SHA-256 | 该页输出字节 |
| `render_output_sha256` | 四页 PNG + PDF 字节的规范绑定 |

同一输入两次渲染，PNG/PDF 摘要必须稳定。

## 7. 验收

- 合成或真实兔子 `age-5-6` 锁定记录：四页 PNG + A4 PDF；观察卡 COPY 等于 `copy_plan`，且可在知识卡还原。
- 记录中错误的 generate COPY 不出现在 COPY 区字形中。
- `age-3-4` COPY 列表为空，COPY 区不排抄写句。
- 缺内容锁、页序漂移、COPY 不在知识卡：fail closed。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 8. 错误码

| 码 | 含义 |
| --- | --- |
| `RENDER_LOCK_MISSING` | 无内容锁摘要 |
| `RENDER_LOCK_MISMATCH` | 声明锁与可复算 artifacts 不一致 |
| `RENDER_PAGE_ORDER` | 不是固定四页顺序 |
| `RENDER_ZONE_DRIFT` | 页区与 family 不一致 |
| `RENDER_COPY_NOT_ON_SOURCE` | COPY/描红不是知识卡子串 |
| `RENDER_ASSET_IN_CLEAR_ZONE` | 插图进入清场区 |
| `TEXT_OVERFLOW` / `LAYOUT_OVERLAP` / `LAYOUT_OUT_OF_BOUNDS` | 几何失败 |
| `FONT_UNAVAILABLE` | 批准字体不可用 |
