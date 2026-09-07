# 操作台：冻结节点请图与投影锁定（IMG-03 + compose lock）

- Status: Approved for this execution tranche
- Date: 2026-09-07
- Related: [FLOW-01](2026-09-04-operator-iterative-workflow-design.md)、[FREEZE-01](2026-09-07-operator-layout-graph-form-freeze-design.md)、[IMG-01](2026-09-02-operator-illustration-hero-page-design.md)、[IMG-02](2026-09-03-multi-view-wordless-assets-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)、[RENDER-02](2026-09-04-legend-module-chrome-design.md)、[QA-01](2026-08-31-strict-qa-human-review-design.md)、[LEGEND-01](2026-09-03-projection-legend-v1-design.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)
- Does not implement: PUBLISH-02 画廊包；OpenAI / 图像 API；Skill claim；canvas 图谱；打印铬；改 `lock_mapping`；改 Confirm current；第五个治理对象；可交互运行时；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`。FLOW-01 仍是程序级工作流；本文件是 IMG-03 与人锁定投影的实施授权。不是 PUBLISH-02。

## 1. 目标

排版冻结之后，操作员才能按节点请无字图。服务器对每个冻结为 `wordless-image` 的命题扩一份版本化提示词；人复制到 ChatGPT 会员生图并回填 PNG。缺槽不失败：投影跳过该图，模块文字仍在。

合成展示身份一致、且 mapping + media-plan 未 stale 时，人用 QA-01 语义的 `approve` **锁定投影工作区**（不是 knowledge current，也不是画廊包）。

ChatGPT 仍在人的浏览器里。服务器不接模型 API。

本设计满足路线图 `IMG-03`，并完成 FLOW-01 §5.3 的「人锁定」。它叠加在 [FREEZE-01](2026-09-07-operator-layout-graph-form-freeze-design.md)、[IMG-01](2026-09-02-operator-illustration-hero-page-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)、[RENDER-02](2026-09-04-legend-module-chrome-design.md) 之上。

相对 FLOW-01 §5.3：程序写「按冻结节点导出/回填；缺槽不失败」。IMG-02 五键仍是某节点的可选画法建议，不再是唯一请图槽。hero isolate 仍是 `observe` 节点的默认主图。

## 2. 非目标

- 不把锁定包写入 PORTAL / 不调用 `publish_approved`（属 PUBLISH-02）。
- 不接 OpenAI / 图像 API，不写 Skill claim，不读 Cookie。
- 不废止无 media-plan 时的 IMG-01 isolate 主图、IMG-02 额外视图、COMPOSE-01 无 freeze 合成。
- 不改 `lock_mapping`、Confirm current、四对象 schema、v1 FACT 键集。
- 不新增第五个治理对象。节点 PNG 仍在 `illustration-intents/`，不进 Knowledge Core，不进 `media-plans/revision-NNNN.json`。
- 不改打印图像带公式；打印仍只读 `hero.png`。节点图只进观察卡屏幕 HTML。
- 不把「图未回填齐 / 模块未出齐」写成 Confirm、freeze、compose 或锁定门禁。
- 不给知识卡 `<img>`。清场区无插图。
- 不 merge/push/release，不 reload Nginx，不标 IMG-01 / IMG-02 / IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`。
- 不修 ops mapping-lock `LEGEND_ROLE_MISSING`。

## 3. 在主路径中的位置

```text
FREEZE-01     media-plan frozen；钉 Core 六键 + mapping revision
        ↓
本刀·扩词     仅 frozen 且 is_stale=false：hero + 每 wordless-image 节点一份提示词
人 · ChatGPT  复制、生无字图、回填 PNG（缺槽允许）
本刀·compose  有 media-plan pointer 时同样要求 frozen 且未 stale
        ↓
本刀·锁定     QA-01 approve；不发布
        ↓
PUBLISH-02（另刀） 已锁定带图投影 → 不可变包 → 画廊
```

无 `media-plan.json` pointer 的 topic：IMG-01 / IMG-02 / COMPOSE-01 / 既有 artifact `publish_from_work` **字节级合同不变**。这是旧 isolate 路径的保留面。

有 pointer 之后，旧路收口如下：请图导出、节点回填、compose POST、投影锁定全部走 freeze 门禁。未绑定该 freeze 的 isolate intent 不得用于该 topic 的 compose / 锁定。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 切片 | IMG-03 请图回填 + compose 锁定一刀；不是 PUBLISH-02 |
| 旧 isolate | 无 pointer 时完全保持；有 pointer 时必须绑定当前 freeze |
| stale | 复用 `knowledge_layout.plan.is_stale`；GET 仍不改写 pointer |
| 请图槽 | frozen 文件里 `form=wordless-image` 的 `proposition_id` |
| 跳过 | `text` / `interactive` 不扩词、不失败 |
| Intent | 沿用 `cognitive-card-illustration-intent-v1`；不新建 intent 类型 |
| hero | 仍是 `observe.isolate` 默认主图；observe 节点缺 PNG 时用 hero |
| 节点模板 | 新 `illustration-node-v1`；人不可改写；**不含** `claim` 全文 |
| IMG-02 | 五键并存；仍须先 `illustrated`；本刀不改其允许集公式 |
| 缺槽 | compose 与锁定都不因缺节点 PNG 失败 |
| `<img>` | 只在 `CN_OBS` / `EN_OBS`；知识卡与清场区禁止 |
| 打印 | 与现 COMPOSE-01 / RENDER-02 相同：只 `hero.png` 图像带 |
| 锁定 | `record_review(..., decision="approve")`；禁止 `publish_approved` |
| 锁定对象 | artifact-work 投影，不是 `current.json` |
| ChatGPT | 人 + 会员生图；服务器无 LLM |
| 现网 | 不由本文件授权 |

## 5. 冻结门禁（旧路怎么收）

导出、回填、compose POST、投影锁定在调用前都要：

1. 读 `{topic}/media-plan.json`；
2. 无 pointer → 走旧 isolate / 旧 compose / 旧 artifact 发布（本刀不改）；
3. 有 pointer 且磁盘不是 `frozen` → `MEDIA_PLAN_NOT_FROZEN`；
4. 有 pointer 且 `is_stale(...)` 为真 → `MEDIA_PLAN_STALE`；
5. 有 pointer 且 frozen 且未 stale → 继续；intent 必须带本 freeze 的绑定（§6）。

`is_stale` 的参数与 FREEZE-01 相同：pointer、`get_current().identity`、listed mapping。禁止复制一套比较。Unfreeze 之后 pointer 是 draft：节点扩词与 compose POST 失败关闭，须再 freeze。

IMG-01 `POST /knowledge-illustration` **无 pointer 时**继续只钉 current 六键，不读 media-plan。有 pointer 时该 POST 必须通过上述 3–5，并把 freeze 写入 intent。

已存在、未绑定 freeze 的 active isolate intent：有 pointer 时不得用于 compose / 锁定。操作员须 cancel 后按绑定路径重建。`ILLUS_INTENT_ACTIVE` 语义不变。

## 6. illustration-intent 绑定

有 freeze 时创建的 intent 在 `meta.json` 增加：

| 字段 | 规则 |
| --- | --- |
| `media_plan_revision` | pointer `revision` 整数；无 freeze 创建则为缺省 `null` / 省略 |
| `media_plan_identity` | 当时 pointer `identity` 六键（与 freeze 钉的 current 相同） |
| `nodes` | 仅 frozen 快照中 `form=wordless-image` 的 id；每项 `{ "png_sha256": null }` |

无 freeze 创建的 intent **不得**出现 `nodes` 键（旧夹具 JSON 形状不变）。

绑定校验：compose / 节点上传 / 锁定时，`intent.media_plan_revision` 必须等于今日 pointer `revision`，且 `intent.media_plan_identity` 必须等于 pointer `identity`。否则 `ILLUS_PLAN_UNBOUND`。

current 前进：沿用 IMG-01，整单 `stale` / `ILLUS_CURRENT_MOVED`。不必另用 media-plan 字段表示 current 漂移。

## 7. 节点提示词

模板 `illustration-node-v1`，创建绑定 intent 时按节点各扩一份，快照进磁盘。操作员不得改写正文。模板变更必须改 `prompt_template_id` 或 digest；已创建 intent 继续用创建时快照。

每份必须包含（与 IMG-01 / IMG-02 同形的无字合同）：

- 恰好一张图、单一主体、儿童百科自然史插画；
- **画面中不得出现任何文字、字母、数字、标题、标签、字幕、水印、UI 框**；
- 主体显示名；分类三键；active `safety_scope` 原文（规则同 IMG-01）；
- `legend_role`（创建时对钉住的 current 调用 `assign_legend` / `resolve_legend_role`；失败则该节点仍扩词，画法说明用「普通外形」，不 500）；
- 该角色的画法说明（下表）；
- **不含**任一命题 `claim` 全文、来源 locator、四卡槽、COPY、字号。

| `legend_role` | 写入提示词的画法说明 |
| --- | --- |
| `observe` | 可指认的外形或姿态；与 hero isolate 同一对象；不要第二张拼贴 |
| `compare` | 可并列的部件；禁止图上标注名称 |
| `evidence` | 化石、骨架、模型或机构记录一类证据物；不要把证据画成活体动物，除非分类已是活体 |
| `time` | 地质环境或时代氛围；禁止年号、数字刻度、字母 |
| `place` | 对象生活地或发现地风景；禁止地图标签 |
| `learning_place` | 孩子的学习地；学习地 ≠ 对象家园（句必须出现） |
| `habit` | 习性或功能正在发生 |
| `kind` | 同类外形归组线索；禁止分类阶元文字 |
| `sequence` | 有顺序的过程；禁止步骤编号 |
| `setting` | 在场或互动；学习地 ≠ 栖息地（句必须出现） |
| 其他 / `null` | 普通外形；可见细节不足时不要发明器官 |

`learning_place` 与 `setting` 的「学习地 ≠ 家园/栖息地」禁令由测试断言字符串存在，不靠像素分类器。

hero 继续 `illustration-hero-v1`，字节合同不变。IMG-02 `illustration-view-v1` 不变。

## 8. 磁盘

候选根下，不进 library current 目录（沿用 IMG-01 根）：

```text
illustration-intents/{intent_id}/
  meta.json
  expanded_prompt.txt          # hero
  hero.png                     # 仅 illustrated
  views/                       # IMG-02；本刀不改键集
  nodes/
    {proposition_id}.txt       # 绑定 freeze 时写入
    {proposition_id}.png       # 可选回填
```

`proposition_id` 只允许 frozen 快照里的 `[A-Za-z0-9_-]+`。路径禁止 `..` 与额外斜杠。节点 PNG 上限 12 MiB，魔数 PNG，规则同 hero。

禁止把节点文件写入 `media-plans/` 或四对象 `revision-NNNN/`。

## 9. 上传与状态

IMG-01 状态机不改：`open` → `illustrated` / `failed`；`cancelled` / `stale` 终态。

| 动作 | 允许 | 失败 |
| --- | --- | --- |
| 上传 hero | 同 IMG-01 | 同 IMG-01 |
| 读/上传节点 PNG | 仅 `illustrated`，摘要匹配，intent 已绑定且 freeze 未 stale，id 在 `nodes` | `open` → `ILLUS_NOT_ILLUSTRATED`；未知 id → `ILLUS_NODE_UNKNOWN`；未绑定/stale → §5 / §6 码 |
| 覆盖已有节点 PNG | 同上 | 成功则更新该 id 的 sha；intent 保持 `illustrated` |
| 缺节点 PNG | 合法 | 不是 `failed` |
| cancel | 同 IMG-01 | 节点 PNG 随 intent 作废 |

无 claim、无租约。`interactive` 与 `text` 不出现在 `nodes`。

## 10. compose

`compose_projection` 在 **有** media-plan pointer 时增加：

1. §5 门禁（frozen、未 stale）；
2. 有效 `illustrated` intent 必须通过 §6 绑定；
3. 构造资源：`CN_OBS:band` / `EN_OBS:band` 仍是 hero（打印合同不变）；
4. 屏幕 chrome 另读节点 PNG：按命题 `legend_role` 放进**该句所在观察卡页**的模块；无 PNG 则该模块只留文字；
5. 若该命题的锁定 AGE 句只在知识卡：节点 PNG **不渲染**，不失败；
6. 知识卡与清场区仍不得出现 `<img>`；违者沿用 `COMPOSE_ASSET_IN_CLEAR_ZONE`。

无 pointer：步骤 1–2 跳过，行为与本刀之前相同（仍要 `illustrated` + `awaiting_review`）。

compose POST 仍要求 QA `awaiting_review`。compose GET 在身份未漂时允许 `awaiting_review` **或** `approved`（锁定后操作员还要能看合成页）。POST 在已 `approved` 时失败关闭，沿用既有 artifact / QA 终态码，不重开合成。

`generate_from_mapping` 仍不得因缺插画或缺节点 PNG 失败。

## 11. 投影锁定

新函数（HTTP 见 §12）：`lock_composed_projection(topic, actor)`。

成功条件同时成立：

| 条件 | 失败码 |
| --- | --- |
| 合法 slug、有 current | 沿用 `ILLUS_SLUG_INVALID` / `MAPPING_NO_CURRENT` |
| 有 media-plan pointer 且 frozen 且 `is_stale=false` | `MEDIA_PLAN_NOT_FROZEN` / `MEDIA_PLAN_STALE` |
| 存在 compose `meta.json` 且身份与当前 illustrated intent、mapping、freeze 六键一致 | `COMPOSE_NO_COMPOSE` / `COMPOSE_IDENTITY_MISMATCH` / `ILLUS_PLAN_UNBOUND` |
| artifact QA 为 `awaiting_review` | `QA_REVIEW_NOT_READY` 或既有 `ARTIFACT_NOT_AWAITING_REVIEW` |
| 人类 actor，非保留名 | 沿用 `ILLUS_UNAUTHORIZED` / `QA_REVIEW_ACTOR_REQUIRED` |

成功：只调用 `record_review(qa_dir, actor=..., decision="approve")`。**禁止**调用 `publish_approved` / `publish_from_work`。`current.json` 字节不变。

无 media-plan pointer：本函数 409 `MEDIA_PLAN_NOT_FROZEN`。旧 `publish_from_work`（approve + 发布）保持给无 pointer 主题；本刀测试不得改其无 pointer 夹具期望。

缺节点 PNG **不是**锁定失败。hero 仍须 illustrated（compose 已要求）。

锁定的是投影工作区。之后 PUBLISH-02（另刀）才把 `approved` 带图投影写成不可变包。

## 12. HTTP

Admin Bearer。无新公网路由。无新 Nginx location。无新 capability。

沿用 `/card-os/api/v1/admin/knowledge-illustration`：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/` | 有 freeze 则 §5–7 绑定并写 `nodes/*.txt`；无 pointer 则旧 isolate |
| GET | `/{intent_id}` | 增加 `media_plan_revision`、`nodes`（id → sha 或 null）；无绑定则无这些键 |
| POST | `/{intent_id}/nodes/{proposition_id}/image` | multipart `image` + `actor`；§9 |
| GET | `/{intent_id}/nodes/{proposition_id}/image` | 仅该 id 已回填且摘要仍匹配；`Cache-Control: private` |

新锁定：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/card-os/api/v1/admin/knowledge-compose/{topic}/lock` | body `{"actor": "<human>"}`；§11 |

compose POST/GET 路径不变；有 pointer 时 POST 加 §10 门禁。

无 token：JSON 不得 200 空成功；节点 PNG URL 不得匿名读出。CLI 与 HTTP 同一函数。library / illustration / compose / work 根由调用方注入；不得指向现网 KNOW-04 library。

## 13. 操作台

`GET /card-os/ops/layout/{topic}`：frozen 且未 stale 时增加「请图」入口，链到该 topic 绑定的 illustration 页（无绑定 intent 则链到创建）。不再把「导出提示词」做在 freeze 按钮上。

`GET /card-os/ops/illustration/{intent_id}`：绑定 freeze 时，hero 区之下列出每个节点：`proposition_id`、`legend_role`、复制提示词、上传 PNG、已回填缩略图。缺 PNG 显示空槽，不显示错误横幅。无绑定则页面与 IMG-01/IMG-02 相同。

`GET /card-os/ops/compose/{topic}`：已 compose 且 `awaiting_review` 时显示「锁定投影」。锁定后 GET 仍可看四段页；按钮变为只读已锁定。无 token 壳不得含 claim、节点提示词或图片字节。

主题详情：有 freeze 时可链 illustration / compose；不改 mapping-lock 第三块 markup/JS。

## 14. 错误

沿用 `ILLUS_*`、`COMPOSE_*`、`MEDIA_PLAN_*`、`QA_*`、`ARTIFACT_*`、WB-01 鉴权。本刀新码：

| 码 | 何时 | HTTP |
| --- | --- | --- |
| `ILLUS_PLAN_UNBOUND` | 有 freeze 但 intent 未绑定，或 revision/identity 对不上 | 409 |
| `ILLUS_NODE_UNKNOWN` | 上传/读取的 id 不在 intent `nodes` | 404 |
| `COMPOSE_NO_COMPOSE` | 锁定时没有 compose meta | 409 |

`MEDIA_PLAN_NOT_FROZEN` / `MEDIA_PLAN_STALE` 用于有 pointer 但不满足 freeze 门禁的扩词、回填、compose POST、锁定。HTTP 409。

**不是错误：** 缺节点 PNG；`text`/`interactive` 无槽；节点图因在知识卡而不渲染；无 pointer 的 isolate 创建；模块未出齐。

## 15. 验收

本机隔离 library。不写生产 library。不打 release。不要求本刀会话打开 ChatGPT。夹具 PNG。

必须成立：

1. 无 `media-plan.json`：创建 isolate intent、compose、既有 IMG-01/IMG-02/COMPOSE focused 与本刀之前相同。
2. draft pointer：创建绑定 intent / 节点上传 / compose POST / 锁定 → `MEDIA_PLAN_NOT_FROZEN`。
3. frozen 后 current 或 mapping 漂了：`is_stale` 为真；扩词、回填、compose POST、锁定 → `MEDIA_PLAN_STALE`；GET 不改写 pointer。
4. frozen 未 stale：创建 intent 含 `nodes` 与每槽 `.txt`；hero 模板仍是 `illustration-hero-v1`；节点模板含无字禁令且不含 `claim`。
5. 只回填 hero、不回填任一节点：compose 成功；观察段有主图；缺节点模块无 `<img>`；锁定成功；`publish_approved` 不被调用；`current.json` 不变。
6. 回填 `kind`（或只出现在知识卡的角色）节点 PNG：知识卡 HTML 无 `<img>`；compose 不失败。
7. 未绑定 freeze 的 isolate intent：有 pointer 时 compose POST / 锁定 → `ILLUS_PLAN_UNBOUND`。
8. 无 token 不能读节点 PNG；无 token 的 illustration / compose HTML 不含提示词与 claim。
9. 打印观察卡仍只消耗 hero 图像带；节点文件不进 RENDER 资源键。
10. 对照旧剑龙卡：只验收模块种类该亮/该空（current + legend + 有图则观察模块可有图），不对整卡像素。
11. 省略 `object_type` 的 `cat` 编译路径行为与本刀之前相同。
12. 现网应用、Nginx、生产 library、画廊包摘要不被本刀改写。

夹具：有 mapping 且能 freeze 的主题测绑定路径；无 pointer 的兔子/猫测旧路。不要用 `rabbit-composite` 的 `LEGEND_ROLE_MISSING` 当成本刀缺陷去放宽图例。

## 16. 实现落点

权威仓库：产品规范 `kids-visual-learning-pack`。server 实现须等本文件 Approved，且实施计划落盘之后。

优先：`is_stale` 门禁、intent 绑定与 `nodes/`、`illustration-node-v1`、compose 有 pointer 时校验、`lock_composed_projection`、ops 请图列表与锁定按钮。不接图像 API，不改 Nginx，不改 `lock_mapping`，不发布画廊。

已知 combined-gate 2 FAIL（ops mapping-lock `LEGEND_ROLE_MISSING`）保持不修。
