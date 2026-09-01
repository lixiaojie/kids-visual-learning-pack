# 四卡文字成熟投影（WB-02）

- Status: Parked — not approved for this phase
- Date: 2026-08-31
- Parked At: 2026-09-01
- Parked Reason: 本阶段核心是知识源建立与维护，不是四卡投影填满。本文件保留为后续投影切片，不实施。
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[AGE-01](2026-08-31-age-language-adapter-design.md)、[CONV-01](2026-08-30-knowledge-four-card-converter-design.md)、[RENDER-01](2026-08-31-locked-four-card-render-design.md)、[ACCEPT-01](2026-08-31-rabbit-end-to-end-acceptance-design.md)、[WB-01](2026-08-31-operator-knowledge-workbench-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把 four-card 从「锁排版后几乎看不见知识」恢复为**有内容**的成熟投影，且不把视觉方案写入 Knowledge Core：

1. 知识卡尽量展示 FACT 已有命题，而不是提前把多数命题丢进来源区；
2. 观察卡「看」跟上同语言知识卡已出现的命题，不再只剩一句外形；
3. 中文卡安全区显示可追溯的中文投影；英文卡仍显示 Knowledge Core 安全原文；
4. 来源区显示机构标题，id 只作追溯；
5. 本机对 AUTHOR-02 兔子 current 显式转 four-card 验收；不发布、不改现网画廊包。

本设计满足路线图 `WB-02` 在本刀的范围。路线图原句「有图、有内容」拆成两刀：本刀只做内容；插图与上架属 `WB-03`。

本设计修订 [ACCEPT-01](2026-08-31-rabbit-end-to-end-acceptance-design.md) §5 第 2–4 条的**新锁呈现规则**。已发布 ACCEPT-01 包字节不变。

## 2. 非目标

- 不恢复高视觉插图、不调用生图、不把图像资产写入 Knowledge Core（`WB-03`）。
- 不替换现网画廊 ACCEPT-01 包，不跑 PUBLISH-01，不在 `/card-os/ops/` 增加生成按钮（`WB-03`）。
- 不编译自由 prompt（`API-01`）。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、packet 契约。
- 不改 `examples/authoring/rabbit-real.json` 或任何 Knowledge Core 文件字节；中文安全不写进 `safety_scope`。
- 不把观察卡 `record` 拿去塞字；该区仍是孩子书写/描画的清场区。
- 不新增公网 HTTP 端点；不 merge server `main`；不 push；不现网。
- 不等于 AGE-02 / ACCEPT-02 / chaptered-guide 排版。

## 3. 在分层中的位置

```text
Knowledge Core          事实；safety_scope 保持机构原文；禁止呈现方案
        ↓
AGE-01（本刀扩展）      儿童表达登记表 + 安全中文登记表 + 放宽 age-5-6 COPY
        ↓
CONV-01 / 锁装箱        按 RENDER 几何预演装箱；look ⊆ 同语言知识卡命题
        ↓
RENDER-01（本刀扩展）   来源标题；CN 安全用 safety.cn；record 仍清场
        ↓
本机 PNG / PDF          不发布
```

视觉与文案都是投影，不是第五个治理对象。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 本刀内容层 | 文字成熟；插图留给 WB-03 |
| 交付面 | 本机转换/排版验收；现网画廊仍展示 ACCEPT-01 |
| 路径 | 投影层填满，不改年龄身份字段，不改 Knowledge Core |
| 记录区 | 保持空清场区 |
| 中文安全 | 必须中文；库无中文时走 fail-closed 登记表，禁止运行时翻译 |

## 5. 安全区中文投影

AUTHOR-02 兔子 `safety_scope` 目前全是英文。本刀**不**把中文写进 Core。

FACT 仍含每条 `safety_id` 与 `policy=from-knowledge-core`：

- `safety[].en` = Knowledge Core `safety_scope` 该条原文（Unicode 完全一致）；
- `safety[].cn` = 版本化登记表中、以该英文原文为键的中文投影。

登记规则：

- 与 AGE-01 claim 表相同：精确字符串键、fail closed、不调用外部模型。
- 首批必须覆盖 AUTHOR-02 这三条英文原文（键必须逐字一致）：
  1. `Ask a rabbit-savvy veterinarian before making significant diet changes.`
  2. `Children must be supervised; only adults or responsible older children should pick up rabbits.`
  3. `A struggling rabbit can injure its fragile spine, so handling must stay calm and secure.`
- 未登记 → `AGE_SAFETY_EXPRESSION_GAP`，禁止转换。
- 中文投影不得弱化或省略边界（不得删「须监护 / 不可抓耳朵 / 伤脊椎」这类约束）。
- 适配器版本字符串纳入 `render_input_sha256`。

RENDER-01：`CN_*` 页安全区只排 `safety[].cn`；`EN_*` 页只排 `safety[].en`。禁止在中文页回落英文原文。

AGE-01 原合同「`safety[].cn` / `safety[].en` 保持原文且跨年龄相同」改为：`en` 与身份字段跨年龄相同；`cn` 为登记投影，跨年龄相同（安全不随 3–4 / 5–6 改写措辞）。命题 id、certainty、source_ids 仍不随年龄改变。

## 6. 锁装箱与观察卡

锁仍只投影 FACT 已有命题，不得添加 claim。

### 6.1 知识卡

不再用与排版无关的英文行数预算把命题提前丢进来源区。装箱预演必须使用与 RENDER-01 相同的页区几何、字体、字号与中英断行规则。

顺序：按 FACT 命题顺序填 `appearance`，再填 `uncertainty`（未知项边界仍只来自 `unknown` 命题）。下一条会触发 `TEXT_OVERFLOW` / `LAYOUT_OVERLAP` / `LAYOUT_OUT_OF_BOUNDS` 时停止填框，剩余命题全文进入 `sources` 区并保留命题 id。两页命题 id 集合必须等于 FACT。

兔子验收：中文知识卡可见命题不少于 4 条 distinct `proposition_id`（8 条中至少一半进框，而不是几乎全部进 sources）。

### 6.2 观察卡

- `look`：只使用已出现在**同语言**知识卡可见文本中的命题；至少 2 条 distinct `proposition_id`；优先按知识卡出现顺序多装，直到该区预演溢出。
- `record`：无正文；只允许区标题；插图仍禁止进入。
- `copy` / `trace`：仍由 RENDER-01 按 `copy_plan` 覆盖 generate 文本。

### 6.3 age-5-6 COPY

删除 AGE-01 §4.3 对 `age-5-6` 的「每语言最多 2 句」「CN 优先 ≤12 个汉字」「EN 优先 ≤8 词」。

新规则：按知识卡 `visible_text` 句子顺序切**精确 span**；能整句则整句；加入后该区预演溢出则停止。`trace` 仍为每语言 1–6 项精确 span。span 必须能切片还原；找不到合法 span → `AGE_COPY_SPAN_UNAVAILABLE`。

`age-3-4` COPY 仍抑制。口头复述规则不变。

## 7. 来源区显示

FACT 已有 `sources[].title`（core `title`）与 `institution`（core `creator`）。本刀不改映射。

RENDER-01：来源区主行是 `title`；`source_id` 放在同一条的括号内。缺 `title` → `RENDER_SOURCE_TITLE_MISSING`。全部 FACT `source_id` 仍必须出现。兔子验收：中文或英文知识卡来源区字形含 `Description and Physical Characteristics of Rabbits` 或 `Diet for Rabbits` 或 RSPCA 标题之一，不得只见 `src-rabbit-` 前缀。

## 8. 错误码

| 码 | 含义 |
| --- | --- |
| `AGE_SAFETY_EXPRESSION_GAP` | 某条 `safety_scope` 英文原文无中文登记 |
| `AGE_COPY_SPAN_UNAVAILABLE` | 沿用 AGE-01：无法切出合法 COPY span |
| `RENDER_SOURCE_TITLE_MISSING` | FACT 来源无 title |
| `TEXT_OVERFLOW` / `LAYOUT_*` | 沿用 RENDER-01；装箱预演与最终排版必须同码 |

未登记 claim 仍是 `AGE_EXPRESSION_GAP`。不得为了填满而发明命题。

## 9. 验收

本机：AUTHOR-02 兔子 library current（与现网种子同一编译，`projection: {}`）+ 显式 four-card request（深圳、`age-5-6`、双语、打印）→ convert → 锁 → 四页 PNG + A4 PDF。

必须成立：

1. 输入 Knowledge Core 文件字节与 `knowledge_core_sha256` 相对输入包不变。
2. 中文观察「看」至少 2 条 distinct 命题，且均为中文知识卡可见命题的子集。
3. 中文观察「记录」无命题/COPY/来源正文。
4. 中文安全区含汉字登记文案；对应 `safety[].en` 仍等于 Core 英文原文。
5. 来源区可见机构标题，不只内部 id。
6. 中文知识卡可见命题 ≥ 4 条 distinct id；COPY/描红 span 可切片还原。
7. 无溢出、重叠、越界。
8. 现网 ACCEPT-01 `package_sha256` 不在本刀被改写。

测试：扩展 AGE-01、锁装箱、RENDER-01 focused 用例；涉及 converter 时跑既有 pipeline 回归。不要求完整 suite 清零既有 real-uvicorn 502。

## 10. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓只改本设计、路线图、任务/交接与文档地图。不改 Nginx、不打生产 release。

优先改 AGE-01 登记表与 COPY 计划、锁装箱预演、RENDER-01 安全/来源绘制。不新增 HTTP。
