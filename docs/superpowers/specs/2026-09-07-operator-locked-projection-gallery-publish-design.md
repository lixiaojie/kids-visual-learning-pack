# 操作台：锁定带图投影上画廊（PUBLISH-02）

- Status: Approved for this execution tranche
- Date: 2026-09-07
- Related: [FLOW-01](2026-09-04-operator-iterative-workflow-design.md)、[IMG-03](2026-09-07-operator-frozen-node-illustration-compose-lock-design.md)、[PUBLISH-01](2026-08-31-immutable-package-publish-design.md)、[PORTAL-01](2026-08-31-published-artifact-gallery-design.md)、[WB-03](2026-09-01-operator-mapping-artifact-publish-design.md)、[QA-01](2026-08-31-strict-qa-human-review-design.md)、[COMPOSE-01](2026-09-03-operator-composite-projection-display-design.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)
- Does not implement: 改 PUBLISH-01 身份算法；改 PORTAL-01 下载允白或详情页；把 compose HTML / 节点 PNG 写入 package；OpenAI / 图像 API；Skill claim；打印铬；改 `lock_mapping`；改 Confirm current；第五个治理对象；可交互运行时；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`。FLOW-01 仍是程序级工作流；本文件是 PUBLISH-02 的实施授权。

## 1. 目标

人已经用 IMG-03 把投影工作区锁成 QA `approved` 之后，才能把该工作区写成不可变 package revision，并出现在本机 PORTAL 画廊。

上架是显式第二步，不是锁定的副作用。包形状守 [PUBLISH-01](2026-08-31-immutable-package-publish-design.md)：四页 PNG、`print.pdf`、`manifest.json`、`qa-report.json`、`sources.json`。compose HTML 与节点 PNG 留在 ops 工作区，不进包、不上公开画廊。

本设计满足路线图 `PUBLISH-02`，并完成 FLOW-01 §5.4。它叠加在 [IMG-03](2026-09-07-operator-frozen-node-illustration-compose-lock-design.md) 锁定与 [PUBLISH-01](2026-08-31-immutable-package-publish-design.md) / [PORTAL-01](2026-08-31-published-artifact-gallery-design.md) 之上，不改包身份闭包。

相对 FLOW-01 §5.4：程序写「锁定且 approved 的带图投影才能写成不可变包；PORTAL 只读列表/详情/下载/历史；ops 未发布合成稿不上公开画廊」。

## 2. 非目标

- 不改 `package_sha256` 闭包字段，不把 compose HTML、节点 PNG、illustration intent 算进身份。
- 不改 PORTAL-01 下载允白、公开/owner 隔离、列表/详情 HTML。
- 不把锁定做成发布；不在 `lock_composed_projection` 里调用 `publish_approved`。
- 不接 OpenAI / 图像 API，不写 Skill claim，不读 Cookie。
- 不改 `lock_mapping`、Confirm current、四对象 schema、v1 FACT 键集。
- 不新增第五个治理对象。
- 不改打印图像带公式；打印仍只读 `hero.png`。
- 不把「图未回填齐 / 模块未出齐」写成发布门禁。
- 不写生产 package catalog，不改现网画廊 `rabbit` 摘要，不 reload Nginx。
- 不 merge/push/release，不标 IMG-01 / IMG-02 / IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-01 / PORTAL-01 / PUBLISH-02 `DONE`。
- 不修 ops mapping-lock `LEGEND_ROLE_MISSING`。

## 3. 在主路径中的位置

```text
IMG-03 锁定     QA-01 approve；不发布；knowledge current 不变
        ↓
本刀·上架       已 approved + freeze 未 stale + compose 身份一致
                → publish_approved → 本机 catalog revision
        ↓
PORTAL-01       只读 current 与历史：四页 PNG / PDF / manifest
```

无 `media-plan.json` pointer 的 topic：既有 `publish_from_artifact`（IMG-03 文中曾称 `publish_from_work`）/ WB-03 `artifact-publish`（approve + 发布）**字节级合同不变**。

有 pointer 之后：禁止再走一刀「批准并上架」。必须先 IMG-03 锁定，再走本刀 `publish_locked_projection`。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 切片 | PUBLISH-02 上架画廊一刀；不是改 PORTAL、不是改身份算法 |
| 触发 | 显式「上架画廊」；锁定不发布 |
| 函数 | 新 `publish_locked_projection`（artifact-work 旁）；只调 `publish_approved` |
| 旧入口 | 有 pointer 时 `publish_from_artifact` / POST `artifact-publish` → `PUBLISH_LOCKED_PATH_REQUIRED` |
| 包形状 | PUBLISH-01 既有目录与身份闭包 |
| 画廊面 | PORTAL-01 现有四页 PNG + PDF；不挂 compose HTML |
| 缺槽 | 缺节点 PNG 不失败（与 IMG-03 锁定相同） |
| slug | `package_slug` = topic slug |
| catalog | 调用方注入的本机根；不得指向现网 PORTAL catalog |
| visibility | 缺省 `public`（PORTAL-01 缺省）；本刀不新增 visibility 控件 |
| current.json | knowledge library `current.json` 字节不变 |
| ChatGPT | 不在本刀；不接模型 API |
| 现网 | 不由本文件授权 |

## 5. 旧路怎么收

`publish_from_artifact` 与 POST `/card-os/api/v1/admin/knowledge-library/{topic}/artifact-publish` 在调用前读 `{topic}/media-plan.json`：

1. 无 pointer → 行为与本刀之前相同（可 approve + `publish_approved`）。
2. 有 pointer → 409 `PUBLISH_LOCKED_PATH_REQUIRED`。不得隐式 `record_review(approve)`，不得调用 `publish_approved`。

ops 主题 artifact 第四块：有 pointer 时不展示「批准并上架」（或展示为不可点，文案指向 compose 页「上架画廊」）。无 pointer 时该按钮不变。

`generate_from_mapping`、compose GET、`lock_composed_projection` 本刀不改。

例外（Task 1 审查接受，禁止回退）：`compose_projection` 在 overlay/`render_locked` 之后重跑 `run_machine_qa`，把新 PNG/PDF 摘要写入 `qa-report.json`。状态仍停在 `awaiting_review`；锁定仍只 `record_review(approve)`，仍禁止 `publish_approved`。原因：overlay 改了渲染字节，PUBLISH-01 `publish_approved` 对照 `render_output_sha256`；本刀发布禁止再 `record_review`。

## 6. `publish_locked_projection`

新函数（HTTP 见 §9）。与 CLI 同一实现。落在 artifact-work 旁（与 `publish_from_artifact` 同层），**禁止**写进 `lock_composed_projection`。

成功条件同时成立：

| 条件 | 失败码 |
| --- | --- |
| 合法 slug、有 knowledge current | 沿用 `ILLUS_SLUG_INVALID` / `MAPPING_NO_CURRENT` |
| 有 media-plan pointer 且 frozen 且 `is_stale=false` | `MEDIA_PLAN_NOT_FROZEN` / `MEDIA_PLAN_STALE` |
| 存在 compose `meta.json` 且身份与当前 illustrated intent、mapping、freeze 六键一致 | `COMPOSE_NO_COMPOSE` / `COMPOSE_IDENTITY_MISMATCH` / `ILLUS_PLAN_UNBOUND` |
| artifact QA `status=approved` 且 `review.decision=approve` | 沿用 `PUBLISH_NOT_APPROVED` |
| 人类 actor，去空白后非空，且不是 `publish-01-v1` / `qa-01-v1` / `machine` | 沿用 `PUBLISH_ACTOR_REQUIRED` |
| catalog 根由调用方注入 | 测试/HTTP 夹具目录；禁止默认现网 catalog |
| RENDER 四页 PNG + `print.pdf` 摘要等于 QA 报告 `render_output_sha256` | 沿用 `PUBLISH_RENDER_DIGEST` |
| 报告 `content_lock_sha256` 等于锁定记录声明值 | 沿用 `PUBLISH_LOCK_MISMATCH` |

成功：只调用 `publish_approved(...)`，`package_slug=topic`。**禁止**再次 `record_review`。knowledge `current.json` 与 mapping pointer、media-plan pointer 字节不变。

无 pointer：本函数 409 `MEDIA_PLAN_NOT_FROZEN`。无 pointer 主题继续用旧 `publish_from_artifact`。

缺节点 PNG **不是**发布失败。hero 仍须 illustrated（compose / 锁定已要求）。

`is_stale` 复用 `knowledge_layout.plan.is_stale`；禁止另写一套 stale 公式。GET 仍不因本刀改写 pointer。

锁定之后 Core 或 mapping 漂了：发布失败 `MEDIA_PLAN_STALE`，即使 QA 仍是 `approved`。须重冻、重合成、重锁定后再上架。

## 7. 包内容与身份

写入目录与 PUBLISH-01 §5 相同：

```text
{catalog_root}/{slug}/revision-NNNN/
  manifest.json
  qa-report.json
  sources.json
  cards/cn-observe.png
  cards/en-observe.png
  cards/cn-know.png
  cards/en-know.png
  print.pdf
```

禁止把下列任何一项拷进 revision 目录：compose HTML、节点 PNG、hero 源文件、illustration intent、media-plan JSON、Knowledge Core。

`package_sha256` 仍由服务器按 PUBLISH-01 闭包复算：`package_slug`、`content_lock_sha256`、`render_output_sha256`、`qa_report_sha256`、各 artifact 相对路径与 SHA-256。`revision` 不进身份。

内容身份与 current 相同 → PUBLISH-01 幂等，不写新目录。内容不同 → 下一序号，`supersedes` 旧序号，旧目录字节保留。

## 8. 画廊消费

PORTAL-01 合同不变。本机画廊列出新 current；公开观众可打开四页 PNG、PDF、manifest、来源、QA、历史 revision。下载字节等于 catalog 文件。

ops 未调用本函数的合成稿、illustration 槽、compose HTML **不得**出现在公开 `/card-os/` 列表或 `/card-os/packages/`。

visibility 缺省 `public`。本刀不提供改 visibility 的控件。owner-only / 撤回仍走既有 PORTAL / PUBLISH CLI。

现网 `https://www.yutou.space/card-os/` 不被本刀改写。把本机 catalog 同步到现网须另立会话授权。

## 9. HTTP

Admin Bearer。无新公网路由。无新 Nginx location。无新 capability。

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/card-os/api/v1/admin/knowledge-compose/{topic}/publish` | body `{"actor": "<human>"}`；§6 |

有 pointer 时既有：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/card-os/api/v1/admin/knowledge-library/{topic}/artifact-publish` | 409 `PUBLISH_LOCKED_PATH_REQUIRED` |

无 token：JSON 不得 200 空成功。CLI 与 HTTP 同一函数。library / work / catalog 根由调用方注入；不得指向现网 KNOW-04 library 或现网 PORTAL catalog。

## 10. 操作台

`GET /card-os/ops/compose/{topic}`：

| QA 状态 | 控件 |
| --- | --- |
| `awaiting_review` 且已 compose | IMG-03「锁定投影」（本刀不改） |
| `approved` 且 freeze 未 stale | 「上架画廊」；POST §9 |
| 上架后 catalog current 身份等于本次工作区 | 只读已上架；链到本机 `/card-os/packages/{slug}` |
| 无 token | 壳不得含 claim、节点提示词、图片字节、catalog 路径 |

主题详情 artifact 块：有 `media-plan.json` pointer 时不提供「批准并上架」写入口。无 pointer 时 WB-03 按钮不变。

不改 mapping-lock 第三块 markup/JS。不在公开画廊加操作台链接。

## 11. 错误

沿用 `ILLUS_*`、`COMPOSE_*`、`MEDIA_PLAN_*`、`QA_*`、`ARTIFACT_*`、`PUBLISH_*`、WB-01 鉴权。本刀新码：

| 码 | 何时 | HTTP |
| --- | --- | --- |
| `PUBLISH_LOCKED_PATH_REQUIRED` | 有 media-plan pointer 时仍走 `publish_from_artifact` / `artifact-publish` | 409 |

`MEDIA_PLAN_NOT_FROZEN` / `MEDIA_PLAN_STALE` / `PUBLISH_NOT_APPROVED` / compose 身份码用于本刀新函数。HTTP 409（actor 空沿用 PUBLISH-01 既有状态码）。

**不是错误：** 缺节点 PNG；知识卡无 `<img>`；无 pointer 的旧 `publish_from_artifact`；模块未出齐；同一内容身份再点上架（幂等成功）。

## 12. 验收

本机隔离 library + 独立夹具 catalog。不写生产 library。不写生产 catalog。不打 release。不要求打开 ChatGPT。

必须成立：

1. 无 `media-plan.json`：`publish_from_artifact` / `artifact-publish` focused 与本刀之前相同。
2. draft pointer：`publish_locked_projection` → `MEDIA_PLAN_NOT_FROZEN`；`publish_from_artifact` / `artifact-publish` → `PUBLISH_LOCKED_PATH_REQUIRED`。
3. frozen 后 current 或 mapping 漂了：即使 QA `approved`，发布 → `MEDIA_PLAN_STALE`；GET 不改写 pointer。
4. frozen 未 stale、已 compose、仍 `awaiting_review`：发布 → `PUBLISH_NOT_APPROVED`；catalog 无新 revision。
5. IMG-03 锁定后：发布写出 `revision-NNNN`；四页 PNG + PDF 在包内；compose HTML / 节点 PNG 不在包内；knowledge `current.json` 不变。
6. 只回填 hero、不回填任一节点：锁定后仍可发布（缺槽不失败）。
7. 同身份再发布：幂等，不新增目录。
8. 内容不同再发布：新序号；旧 revision 字节不变。
9. 本机 PORTAL 公开列表含该 slug；下载字节等于 catalog；ops 未发布合成稿不在公开列表。
10. 无 token 不能 POST publish；无 token 的 compose HTML 不含 claim。
11. 现网应用、Nginx、生产 library、现网画廊 `rabbit` `package_sha256` 不被本刀改写。
12. 对照旧剑龙卡只验收模块种类该亮/该空，不对整卡像素；本刀不把像素比对写进完成条件。

夹具：有 mapping 且能 freeze、compose、lock 的主题测新路；无 pointer 的兔子/猫测旧路。不要用 `rabbit-composite` 的 `LEGEND_ROLE_MISSING` 当成本刀缺陷去放宽图例。不要改无 pointer 的 `publish_from_artifact` 夹具期望。

## 13. 实现落点

权威仓库：产品规范 `kids-visual-learning-pack`。server 实现须等本文件 Approved，且实施计划落盘之后。

优先：`publish_locked_projection`、有 pointer 时封 `publish_from_artifact`、compose POST publish、ops「上架画廊」、夹具 catalog 的 PORTAL 列表断言。不改 PORTAL 渲染器，不改身份算法，不接图像 API，不改 Nginx，不写生产 catalog。

已知 combined-gate 2 FAIL（ops mapping-lock `LEGEND_ROLE_MISSING`）保持不修。
