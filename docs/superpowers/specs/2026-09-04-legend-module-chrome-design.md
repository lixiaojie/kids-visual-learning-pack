# 图例模块铬（RENDER-02）

- Status: Approved for this execution tranche
- Date: 2026-09-04
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-003](../../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[IMG-02](2026-09-03-multi-view-wordless-assets-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)、[RENDER-01](2026-08-31-locked-four-card-render-design.md)、[加权版式](2026-09-02-mapping-artifact-weighted-layout-design.md)
- Does not implement: 打印 PNG 铬；改 illustration / compile 提示词；对象类型 → 画法清单；OpenAI 图像 API；整卡烧字；改四对象 schema；改 ACCEPT-01 等分；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

在 [COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md) 已经合成的无字主图 + 锁定四卡文案上，把**屏幕 HTML** 按 [投影图例](2026-09-03-projection-legend-v1-design.md) 收成模块铬：有实例才亮，空角色不画假框。字仍是 DOM 文本。打印四页 PNG/PDF **字节与现 COMPOSE-01 相同**。

本设计满足路线图 `RENDER-02` 本刀书面合同。质量标尺是旧 Skill 剑龙卡的**模块种类**，不是整卡像素，也不是 ChatGPT 整卡生图。

三视 / 剖面 / 爆炸 / 在场 / 互动的**请图与提示词**不在本刀，见 §6。

## 2. 非目标

- 不改打印图像带公式、不往打印页加时间条/比列/三视板。打印 PNG sha 必须与本刀之前同一输入的 COMPOSE-01 重渲相同。
- 不改 `compose_projection` 门禁：仍须同一 topic 的有效 `illustrated` intent 与 `awaiting_review` 映射工作区，身份一致。
- 不改 `generate_from_mapping` 无图成功路径。
- 不重切 WB-02 的页归属：不把观察卡已锁定的句搬到知识卡，反之亦然。
- 不扩写、不替换 IMG-01 `illustration-hero-v1` 或 IMG-02 `illustration-view-v1`。不在 API-01 编译 / 对象解析里增加「该对象必须出三视/剖面/爆炸」。
- 不把「视法出齐 / 模块出齐」写成知识源准入或 Confirm current 条件。
- 不把旧卡「看 / 画 / 比 / 找」做成四个图例角色。
- 不改四对象、ACCEPT-01 等分、KNOW-04 生产 library、Nginx、server `main`。
- 不接图像 API、不写 Skill claim、不跑生产 OCR。
- 不标 IMG-01 / IMG-02 / COMPOSE-01 / LEGEND-01 / API-01 / RENDER-02 `DONE`。

## 3. 在主路径中的位置

```text
API-01 · Confirm current
        ↓
IMG-01 / IMG-02          提示词 + 无字 PNG（hero 与可选 views/）
        ↓
WB-02 lock → WB-03 generate   锁定 AGE 四卡 + mapping legend
        ↓
COMPOSE-01 compose_projection
        ├─ 打印 PNG/PDF              本刀不改字节
        └─ 屏幕 /compose/{topic}     本刀：按角色换壳
```

相对 ADR-002：本刀仍是 Renderer Binding，不是第五个治理对象，不回写 Knowledge Core。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 打印 | 与现 COMPOSE-01 字节相同 |
| 屏幕 | 同一 `/card-os/ops/compose/{topic}` 四段页换壳，不是新路径 |
| 门禁 | 仍须 illustrated + awaiting_review；身份规则不变 |
| 文案 | 在**该页**已锁定 AGE 句上按 `legend_role` 收模块；空角色不出现；不另复制一份 |
| 无 legend 块 | compose 不失败；HTML 退回今天的区栈 |
| 主图 | `hero.png` 只在 `CN_OBS` / `EN_OBS` 的 `observe` 视觉槽；知识卡无主图 |
| 额外 PNG | 只按 sha 引用 IMG-02 已存键；无 sha 跳过该板。**所有 `<img>` 只出现在观察卡 HTML**；知识卡铬无插图 |
| 铬标题 | 服务器中英表，不是 Core `claim`，不烧进图 |
| 清场区 | `record` / `trace` / `copy` / `safety` / `source` / `uncertain` / `blank` 无 `<img>` |
| 两地 | `place` 与 `learning_place` 两套标记 |
| 无图 generate | 仍出文字四卡；只是没有铬 HTML |
| 屏幕溢出 | HTML 可滚动；铬不触发 `TEXT_OVERFLOW` |

## 5. 页内收模块

WB-02 已经决定某句在哪一页。本刀只在该页锁定文案里按角色分组。

稳定序用 [LEGEND-01 §5](2026-09-03-projection-legend-v1-design.md) 的 v0 角色表顺序，跳过本页零实例的角色。不按旧 Skill 像素排。

观察卡页底 `record` / `trace` / `copy` 仍是 AGE `copy_plan` 清场区，不进 `modules[]` 的命题分组。`name` / `write` / `blank` 不从命题发明。

知识卡 `safety` / `source` 仍页脚。`uncertain` 有 unknown/disputed 实例则必须能落该模块，且不得画成肯定。

`CN_OBS` / `EN_OBS` **始终**为 `hero.png` 留 `observe` 视觉槽（isolate）。即使该页 `look` 没有 observe 句，主图仍在——这是 compose 插画合同，不是空文案假框。有 observe 句则与主图同模块。

## 6. 与 IMG 的边界（提示词不在本刀）

不同对象可能需要三视、剖面、爆炸、在场、互动，这是**请图合同**，不是排版合同。

| 环节 | 谁做 | 本刀 |
| --- | --- | --- |
| 允许像素键 | IMG-02：intent 创建时对钉住的 current 做 `assign_legend`；有 `observe` 实例才列 `observe.three_view` / `section` / `exploded`；有 `setting` 才列 `in_situ` / `interaction` | 只读已有 sha |
| 提示词 | IMG-02 `illustration-view-v1`（外加 IMG-01 `illustration-hero-v1`）；操作员复制后贴进 ChatGPT | 不改模板、不新扩写 |
| 上传无字 PNG | IMG-02 额外槽；须先 `illustrated` | 不上传 |
| HTML 子板 | 本刀：该键 `png_sha256` 非空才出 `<img>` | 无 sha 不加板、不失败 |

若要把「机械倾向爆炸、剑龙爆炸可空」写成**更细的提示词规范**，仍属 IMG：或收紧 IMG-02 允许集/画法说明，或另立 IMG 切片。那一步发生在 illustration-intent 扩写（或后续 IMG 编译提示），**不是** compose / 本刀 HTML。

禁止把画法清单写进 Knowledge Core，禁止写成 Confirm current / 知识源准入。禁止在 API-01 对象解析里为了排版去要图。

COMPOSE-01 打印路径继续只读 `hero.png`，不读 `views/`。本刀 HTML 可以读 `views/` 的 sha；打印仍然不读。

## 7. 角色 HTML 语法

铬标题来自服务器表（中文页中文、英文页英文）。图资产无字；标注是 DOM。

| 角色 | 该页有实例时 | 没有时 |
| --- | --- | --- |
| `observe` | 模块含 hero（仅观察卡）+ 观察句。IMG-02 的 `three_view` / `section` / `exploded` 有 PNG 才加子板 | 观察卡仍可只有 hero 槽；无观察句不加空标题。知识卡无 hero |
| `compare` | 部件横排：服务器标注 + 色块；文案进这块。不请 PNG | 整块不出现 |
| `evidence` | 证据盒（服务器图标）；不把复原图当照片事实 | 整块不出现 |
| `time` | CSS 时间条；刻度只来自已锁定时间句；未锁定年份不当已知刻度 | 不画时间条、无「时间」标题 |
| `place` | 发现地/生活地徽章或地图钉 | 不画 |
| `learning_place` | 另一套学习地徽章；不得与 `place` 共用同一钉 | 可省略 |
| `habit` / `kind` | 模块卡 + 图标；不编阶元或体长 | 整块不出现 |
| `sequence` | 编号步骤条；顺序用 LEGEND-01 全序 | 不画步骤条 |
| `setting` | 有锁定句则出文字模块。`in_situ` / `interaction` PNG 仅当该模块在**观察卡**且有 sha 时加板 | 无句不画；知识卡有句无图；无 PNG 只跳过该板 |
| `uncertain` | 问号/虚线模块；禁止肯定语气或实线「已确定」样式 | 有未知则必须能落这块 |
| `safety` / `source` | 页脚；清场，无插图 | 四卡安全/来源合同不变 |
| `name` / `write` / `blank` | 观察卡描红/抄写/空白，来自 AGE | `age-3-4` 无抄写则不排抄写句 |

不做「暂无」「待补充」假框。不把看/画/比/找做成角色模块。

## 8. JSON 与 HTML

`GET /card-os/api/v1/admin/knowledge-compose/{topic}` 在既有四页锁定区文案之外增加 `pages[].modules`（可缺省）。

每个 module：

- `role`：LEGEND-01 v0 角色 id
- `texts`：该页该角色的锁定 AGE 可见句，顺序稳定
- `hero`：仅观察卡 `observe` 为 true
- `views`：本模块允许展示的 IMG-02 键；每项含 `key` 与 `png_sha256`（无图则该键不出现在 `views` 里）。**仅观察卡 modules 可含非空 `views` / `hero`**；知识卡 module 的 `hero` 恒为 false，`views` 恒为空。

无 mapping `legend`：省略 `modules` 或空数组；ops HTML 退回今天按 `zone_order` 排 `visible_text`。

有 `modules` 时 HTML 按 `modules` 渲染命题铬，再排该页清场区。`<img>` 只允许：

- 观察卡 hero（现有 illustration GET）
- 观察卡 `views[]` 里已有 sha 的键（现有 extra-view GET）

知识卡 HTML 不得有 `<img>`（色块、时间条、图标用 CSS/SVG 绘制，不是 PNG 插图）。若 `setting` 句只在知识卡，该页出文字模块；对应 PNG 本刀不往知识卡塞，也不因此失败。

禁止匿名读图。无 token 的 HTML 壳不得内嵌锁定文案、模块标题+正文、或图片字节。Token 规则同 WB-01 / COMPOSE-01。

不新增 HTTP 路径、不新增 capability、不新增 Nginx location。POST compose 语义不变。

## 9. 错误码

| 码 | 含义 |
| --- | --- |
| 既有 `COMPOSE_*` / `ILLUS_*` / `ARTIFACT_*` | 语义不变 |
| `COMPOSE_ASSET_IN_CLEAR_ZONE` | 铬把 `<img>` 放进清场区或知识卡 |
| `LEGEND_PLACE_COLLAPSE` | `place` 与 `learning_place` 使用同一套地点标记 |
| `LEGEND_UNCERTAIN_AS_FACT` | 未知/争议模块画成肯定 |

不新增「模块未出齐」「视法未出齐」。缺时间条、缺三视板不是错误。

屏幕侧不因铬触发 `TEXT_OVERFLOW`。打印几何仍只由 COMPOSE-01 图像带公式决定。

## 10. 验收

本机：显式 library / candidate 根。夹具 PNG。不要求本刀打开 ChatGPT。不安装现网。

必须成立：

1. **空模块不画假框**：无 `time` 实例 → HTML 无时间条、无时间标题；GET `modules` 无 `time`。
2. **清场区无插图**：`record` / `trace` / `copy` / `safety` / `source` / `uncertain` / `blank` 无 `<img>`。
3. **打印不动**：同一输入四页 PNG sha 与本刀之前 COMPOSE-01 重渲相同。
4. **无图 generate 仍可用**：无插画时 `generate_from_mapping` 仍 `awaiting_review`。
5. **两地两钉**：同时有 `place` 与 `learning_place` 时标记不同；故意同钉 → `LEGEND_PLACE_COLLAPSE`。
6. **额外图可选**：有 `observe.three_view` sha 才在**观察卡**出三视板；无 sha 无该板、无失败码。HTML 不得为了缺板去调用生图或改提示词。知识卡 HTML 无 `<img>`。
7. **无 token**：壳无锁定正文、无模块文案、拉不到图。
8. **无 legend 退回**：缺少 mapping `legend` 时 compose 成功，HTML 为区栈，打印仍成功。
9. 现网应用、Nginx、生产 library、画廊包摘要不被本刀改写。

对照旧 Skill 剑龙卡：只查模块该亮/该空（外形、可比部件、证据、时间、美国发现地、深圳学习地、习性、阶元、未知、安全、来源、描红/抄写），不对像素。夹具用已能 mapping-lock 的对象（如 rabbit-real）；不把 `rabbit-composite` 的 `LEGEND_ROLE_MISSING` 当成本刀缺陷去放宽图例门禁。

测试落在 server worktree 的 compose / legend 相关 unittest，并纳入既有 combined focused 门禁。不要求完整 suite 清零既有 real-uvicorn 502。不要求生产安装。

## 11. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓：本设计、实施计划 `docs/superpowers/plans/2026-09-04-legend-module-chrome-implementation-plan.md`、路线图、任务/交接、文档地图。

优先：GET `modules`、ops HTML 按角色换壳、清场区无图断言、打印 sha 不变。不改 illustration 提示词，不改打印绑定，不接图像 API，不改 Nginx，不写生产 library，不改四对象。

本文件不授权 merge 进 server `main`、不授权现网。
