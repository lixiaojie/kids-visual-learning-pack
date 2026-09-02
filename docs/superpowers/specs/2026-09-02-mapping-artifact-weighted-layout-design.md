# mapping-artifact 加权版式（打印绑定）

- Status: Approved for this execution tranche
- Date: 2026-09-02
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[WB-03](2026-09-01-operator-mapping-artifact-publish-design.md)、[RENDER-01](2026-08-31-locked-four-card-render-design.md)、[AGE-01](2026-08-31-age-language-adapter-design.md)
- Does not implement: 新 ADR；交互网页终端；新 Projection family；ACCEPT-01 等分版式变更
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

在 **不改 Knowledge Core、不改映射 `node_ids`、不缩小字号、不把命题溢入来源区** 的前提下，让 `lock_version = mapping-artifact-v1` 的打印四卡按**区内容分配行高**，使兔子映射命题全部落入：

1. 知识卡主区（`appearance` + `uncertainty`）；
2. 观察卡「看」。

本设计是 WB-03 spec §11 最后一段所要求的**另立排版合同**。它只约束打印四卡的 Renderer Binding，不是知识入库合同。

## 2. 分层纪律（本刀必须遵守）

ADR-002 已 Accepted：Knowledge Core 不含页面布局；其后才是 Learning Plan / Path → Projection Blueprint → Renderer Binding → Artifact。四卡是第一种兼容 Projection，不是知识模型。

本刀因此：

| 允许 | 禁止 |
| --- | --- |
| 改 `mapping-artifact-v1` 的区高分配与 COPY 预算 | 改 Core 字节、命题文案、确定性、安全原文、映射 `node_ids` |
| 加权后仍装不下 → `TEXT_OVERFLOW`，该投影失败 | 把溢出命题写进来源区；缩小字号硬塞 |
| 换 family 或声明 four-card 打印装不下 | 把「装得下四卡」写成知识源准入或 mapping 锁定条件 |
| 网络可交互等其他终端另立绑定 | 用本打印合同回写学习计划或 Core |

投影前实例（Core + `learning-spec`）在本刀之前已经闭合。本刀只处理版面规范与打印终端（静态四页）。不新开 ADR。

## 3. 非目标

- 不改 ACCEPT-01 `lock_version = accept-01-v1` 的等分四区与溢出到来源区。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、packet 契约。
- 不改 WB-03 生成/上架/catalog/操作台合同，除本文件几何与 COPY 预算。
- 不打应用 release、不 reload Nginx、不 merge server `main`、不 push、不写生产 catalog。
- 不实施交互网页、chaptered-guide 排版、AGE-02、生图。

## 4. 适用范围

只在同时满足时启用加权：

- 装箱 / 渲染路径为 mapping-artifact（`content_lock.artifacts.lock_version = mapping-artifact-v1`）；
- family 为 mammal 四卡、无 family `layouts`（沿用 RENDER-01 单列栈）。

`convert_current` / ACCEPT-01 历史锁继续走 RENDER-01 §5 等分行高。

## 5. 几何合同

装箱预演与最终 RENDER **必须调用同一套区高函数**。不得出现「装箱按等分 6 行通过、渲染按加权溢出」或反向。

页面与字体沿用 RENDER-01：A4 竖版 300 dpi、安全边距 12 mm、字号不得低于 16 pt、中文按字断行、英文按空格断行。区框绘制参数与现行 `_render_page` 对齐：

| 量 | 值 | 来源 |
| --- | --- | --- |
| 区间隙 `gap` | 24 px | `stack_layout` |
| 标签到正文顶 | 112 px | `_render_page` `text_top` |
| 区底内边距 | 28 px | `_render_page` `text_bottom` |
| 正文左右内边距 | 各 28 px | `_render_page` |
| 行高 | `ascent + descent + 8` | `_render_page` / `_layout_budget` |

`usable` 与现行 `stack_layout` 相同：`page_h - 2 * margin - gap * (n - 1)`。四区时 `n = 4`。

区内容高度：

```text
content_h(zone) = 112 + 28 + line_count(visible_text) * line_height
空区（无正文）   = 112 + 28          # 仍画标签带，不删区
```

`line_count` 必须用与 RENDER 相同的 `wrap_text`（同一字体、同一正文宽度）。

### 5.1 弹性区

每页一个弹性区，吃掉 `usable` 减去其他区 `content_h` 之后的剩余：

| 页 | 弹性区 | 其他区 |
| --- | --- | --- |
| `CN_KNOW` / `EN_KNOW` | `appearance` | `uncertainty`、`safety`、`sources` 按内容；空则标签带 |
| `CN_OBS` / `EN_OBS` | `look` | `record` 空则标签带；`copy` / `trace` 按 COPY 计划正文 |

分配：

```text
non_flex = sum(content_h(z) for z ≠ flex)
flex_h   = usable - non_flex
若 flex_h < content_h(flex) → TEXT_OVERFLOW（path = 该页.flex 区）
否则 heights[flex] = flex_h；其余 heights[z] = content_h(z)
```

剩余空白留在弹性区，不均分、不溢入来源区。中英页独立计算；英文通常更紧。

加权后仍装不下：继续 `TEXT_OVERFLOW` / `LAYOUT_*`。不得回写 Core，不得改 `node_ids` 来换通过。

### 5.2 观察卡与 COPY 预算

COPY / 描红仍在知识主区锁定之后由 `copy_plan_from_knowledge_cards` 重算（WB-03 §6.3）。加权后 **COPY 预算不再使用等分 `max_lines`**。

计算顺序：

1. 按 §5.1 分配知识卡区高并 fail-closed 装下全部映射命题；
2. 按知识卡 `visible_text` 切句，逐句追加 COPY；每试加一句，用**该句集合**重算描红（仍每语言 1–6 项精确 span）；
3. 若 `content_h(look) + content_h(record 空) + content_h(copy) + content_h(trace) > usable`，停止追加，不失败整卡；
4. 即使 COPY / 描红都为空，若 `look` 仍装不下 → `TEXT_OVERFLOW` 于该页 `look`；
5. `age-5-6` 找不到任何可切片还原的 COPY span → 仍为 `AGE_COPY_SPAN_UNAVAILABLE`（与几何无关）。`age-3-4` COPY 仍抑制。

装箱时观察卡 `copy` / `trace` 若尚未 overlay，必须用与最终 overlay **同一** COPY 计划来算 `content_h`，禁止按空区标签带装箱、再按有字渲染。

`record` 仍无节点、无 COPY、无来源正文。

## 6. 对既有合同的修订

修订 [WB-03 §6.2](2026-09-01-operator-mapping-artifact-publish-design.md)：mapping-artifact 的几何预演改为本文件 §5，不再使用 `four_card_lock._layout_budget` 的等分 `max_lines`。槽位规则、来源标题、安全分语言、fail-closed、禁止溢入来源区 **不变**。

修订 [WB-03 §11](2026-09-01-operator-mapping-artifact-publish-design.md) 末段：兔子完成条件改为「该知识槽**全部**映射命题落入知识主区」。AUTHOR-02 / KNOW-04 兔子当前为 **9** 条命题、全部 `known`、`uncertainty` 为空；不得为凑「8 条」改 Core。等分四区在 16 pt 下实测不足（中文外形约 9 行、英文约 14 行，等分约 6 行）不是知识源缺陷，是本绑定要修的版面合同。

RENDER-01 §5 等分行高继续约束 ACCEPT-01 与无 `layouts` 的默认栈；`mapping-artifact-v1` 以本文件为准。不改 RENDER-01 正文，以免历史锁语义漂移。

## 7. 验收

本机：与 WB-03 相同的兔子 mapping revision + 独立 catalog。不安装现网。

必须成立：

1. `pack_from_mapping` / `generate_from_mapping` 对兔子真实 mapping **不再**因 `CN_KNOW.appearance` / `EN_KNOW.appearance` / `CN_OBS.look` / `EN_OBS.look` 在等分预算下 `TEXT_OVERFLOW`。
2. 中英知识主区 `proposition_id` 集合等于该语言知识槽全部映射节点；观察「看」≥ 2 且 ⊆ 知识主区；来源区仍是 `title (source_id)`，不见命题全文。
3. 四页 PNG + A4 PDF；无溢出 / 重叠 / 越界；字号 ≥ 16 pt。
4. COPY / 描红仍为知识卡精确 span，可切片还原。
5. 合成夹具：非弹性区按内容取高之后，弹性区正文仍超出剩余高度 → 仍 `TEXT_OVERFLOW`，来源区不含被拒命题。
6. ACCEPT-01 `lock_from_payload` 与等分渲染回归保持原行为（含溢出到来源区）。
7. knowledge `current.json`、映射 `node_ids`、Core 命题字节均不变。

WB-03 其余条（无 mapping 拒绝、批准上架、token 壳、现网包不被改写）仍有效。2026-09-02：操作者接受兔子卡基础信息，路线图 `WB-03` 标本机 `DONE`。打印样式未验收；全部阶段完工后再以最终投影产物反查各阶段。现网安装不是本文件门禁。

测试：装箱加权、COPY 预算随 `look` 剩余高度停止追加、兔子真实 pack/generate、ACCEPT-01 等分回归、既有 mapping-artifact HTTP/pipeline focused。不要求完整 suite 清零既有 real-uvicorn 502。

## 8. 实现落点

权威仓库：server `knowledge-pipeline-v1`。优先：

- 抽出装箱与 RENDER 共用的区高函数（`usable`、`content_h`、弹性分配）；
- `pack_from_mapping` 与 `stack_layout`（仅 `mapping-artifact-v1`）改走该函数；
- `copy_plan_from_knowledge_cards` 的 `_copy_fits` 改为 §5.2 预算；
- ACCEPT-01 `_layout_budget` / `_pack_knowledge_groups` 不动。

不接生图，不改 Nginx，不写生产 catalog。
