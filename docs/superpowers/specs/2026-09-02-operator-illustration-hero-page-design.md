# 操作台主体插画 + 非图形知识页（IMG-01 首刀）

- Status: Approved for this execution tranche
- Date: 2026-09-02
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-003](../../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[LIB-01](2026-08-30-knowledge-library-revision-current-design.md)、[PROJ-01](2026-08-30-projection-family-selection-design.md)、[WB-01](2026-08-31-operator-knowledge-workbench-design.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[WB-03](2026-09-01-operator-mapping-artifact-publish-design.md)、[API-01 编译](2026-09-02-operator-free-prompt-knowledge-compile-design.md)
- Does not implement: OpenAI 图像 API；Codex claim；WB-02 mapping-lock；Pillow `render_locked`；烧字整卡；可交互页；新 Projection family 注册；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

知识源锁定命题与证据。图怎么画由**投影意图**决定，不是 IMG-01 焊死一种产物：

| 投影意图 | 图 | 知识怎么亮出来 | 本刀 |
| --- | --- | --- | --- |
| 插画 | 无字或极少字资产 | 版式/页面自己排字 | 资产形态采用此列 |
| 可交互页 | 可烧字整卡或场景图 | 图即页面 | 后置 |
| 主图 + 非图形演示 | 一两张主体图 | 知识用非图形面展示 | 展示形态采用此列 |

本刀只打通一条路径：对已 Confirm 的 `library current`，服务器扩出**完整生图提示词**，人复制到 ChatGPT 会员生图，再上传**一张** PNG；操作台给出**新的一页**：主图 + 全部 `standing=active` 命题条文。

对标 API-01：复制/粘贴（本刀是复制提示词 + 上传文件）两端在操作台；服务器无图像模型、无 claim、不改四对象字节。

## 2. 非目标

- 不接 OpenAI / ChatGPT 图像 API，不读取 Cookie 或会员会话。
- 不写 Skill 领取面：无 illustration claim、无租约、无执行器 token。
- 不经 WB-02 `mapping-lock`，不跑 Pillow，不改 WB-03 加权版式。
- 不注册新的 Projection family；不改 PROJ-01 四 family 词表。
- 不把命题全文写入生图提示词；不要求画面烧字、中英标题或 COPY。
- 不接 AGE-01：页面条文用 current 上的年龄中性 `claim`，不翻译、不改编。
- 不改四对象 schema、KNOW-04 六主题 current、生产 knowledge-library。
- 不把「有图 / 图装得下」写成知识源准入或 Confirm current 条件。
- 不多图槽、不 JPEG、不粘贴图、不画廊、不公网 Portal。
- 不打应用 release、不 reload Nginx、不 merge server `main`、不 push。
- 不对像素做知识 QA（外形是否「看起来像」留人工）。

## 3. 在主路径中的位置

```text
API-01 · Confirm current
        ↓
本刀 · illustration-intent     对已有 current 扩生图提示词
人 · ChatGPT 会员生图          复制提问，下载一张图
本刀 · 上传 PNG                哈希 + 钉 current 四对象摘要
本刀 · 一页演示                主图 + active 命题列表
        ↓
（相邻、非完成条件）WB-02 / WB-03 四卡文字仍可另走
```

相对 ADR-002：本刀是下游演示产物，不是第五个治理对象，不把插画写进 Knowledge Core。ChatGPT 是人用的会员工具，不是服务器权威。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 知识 vs 投影 | 知识源只锁内容；插画 / 可交互整卡 / 主图演示是投影侧策略，可并存于路线图 |
| 首刀产物 | 一张无字主体插画 + 操作台 HTML 一页（主图 + 命题列表） |
| 推理位置 | 人 + ChatGPT 会员生图；服务器无 LLM、无图像 API |
| 操作台职责 | 扩完整提示词 + 收回 PNG + 只读投影条文 |
| 实现路径 | `illustration-intent`；无 claim/租约 |
| 入口 | 已有 library current 的 topic；**不**经 mapping-lock |
| 图数量 | 恰好一张 PNG 主体主图 |
| 提示词内容 | 对象名、分类、已有 `safety_scope`；**不含**命题 `claim` 全文 |
| 回传 | `multipart` 上传 PNG；SHA-256；钉 current 四对象摘要 |
| 条文 | 全部 `standing=active` 命题；单一 `claim` 只出一行；另有第二语言 claim 字段才出第二行 |
| 年龄 | 不收年龄；不跑 AGE-01 |
| current 前进 | 该 intent 失效；旧 PNG 可留审计，页不再当作有效演示 |
| 验收主题 | 注入 library 里已有 current 的 slug（建议 `cat` / `ragdoll-cat`）；loopback；不写生产 library |
| 交付面 | 本机操作台 + 显式注入的 library 根；现网应用 / Nginx / 生产 library / 画廊不改 |

## 5. illustration-intent

操作员用 admin token `POST` 创建一条 intent。`topic_slug` 创建后不可变；完整提示词由服务器根据**当时** current 生成，操作员不得改写。

| 字段 | 规则 |
| --- | --- |
| `intent_id` | 服务器签发；形如 `ii_` + 小写 hex |
| `topic_slug` | 操作员给出；合法 slug；该 slug **必须已有** library current |
| `knowledge_revision` | 创建时 current 的 revision 号 |
| `identity` | 原样快照 `LibraryRevision.identity`：`object_id`、`revision`、`knowledge_core_sha256`、`learning_spec_sha256`、`projection_spec_sha256`、`final_content_lock_sha256`；上传与展示均须完整匹配 |
| `prompt_template_id` / `prompt_template_sha256` | 当时生效的模板身份；进入 intent 快照 |
| `expanded_prompt` | 模板填入对象名、分类、`safety_scope` 后的完整提示词；只读 |
| `created_at` / `actor` | 须为人类 actor，禁止 `machine` / `qa-01-v1` / `publish-01-v1` |
| `hero_png_sha256` | 仅 `illustrated` 后有值 |

禁止：intent 带年龄、family、mapping、命题改写、操作员自备「完整提示词」。禁止把插画摘要写回四对象。

无 current → `ILLUS_NO_CURRENT`。非法 slug → `ILLUS_SLUG_INVALID`。同一 slug 若已有非终态 intent（`open` / `failed` / `illustrated`）→ `ILLUS_INTENT_ACTIVE`。`illustrated` 在 current 仍匹配时视为占用该 slug 的有效演示，须先取消再新建。

创建可用幂等键：同一 `Idempotency-Key` + 相同 body 返回同一 `intent_id`。不同 body 同键 → 失败关闭。

### 5.1 提示词模板

模板是服务器受治理文件 `illustration-hero-v1`，不是 ChatGPT 系统记忆。`expanded_prompt` 必须包含：

- 一张图、单一主体、儿童百科自然史插画风格；
- **画面中不得出现任何文字、字母、数字、标题、标签、字幕、水印、UI 框**；
- 主体名称（current 主题显示名；若无显示名则用 slug）；
- 分类：`primary_domain`、`primary_form`、`object_subtype`（取 knowledge-core 已有键，不发明分类）；
- 该 current 上所有 active 命题里**非空**的 `safety_scope` 原文，作为禁画场面（不另写新句）；
- 不得发明与所给分类冲突的器官、服饰、道具或场景；可见细节不足时画普通外形，以页面条文为知识权威。

禁止把 `claim`、来源 locator、四卡槽、COPY、字号写入提示词。

模板变更必须改 `prompt_template_id` 或内容 digest。已创建 intent 继续使用创建时快照的 `expanded_prompt` 与四对象摘要，不随新模板或后来的 current 漂移。

## 6. 状态

```text
open → illustrated
     ↘ failed
open ← failed 后重传 PNG（current 摘要仍匹配）
cancelled 终态（确认前/失效前可取消）
stale 终态（current 前进或四对象摘要不再匹配）
```

| 状态 | 含义 | 谁可推进 |
| --- | --- | --- |
| `open` | 完整提示词已生成，等待上传 PNG | admin 上传 |
| `failed` | 上传不是合法 PNG 或摘要已不匹配（若已不匹配则应进 `stale`，见下） | 摘要仍匹配时可重传 |
| `illustrated` | 已收下合法 PNG，演示页可开 | 取消，或 current 前进 → `stale` |
| `cancelled` | 操作员取消 | 终态 |
| `stale` | current 已前进或四对象字节不再等于创建时摘要 | 终态；须新建 intent |

上传时若 current 不存在或四对象摘要与 intent 快照不同 → **不**保持 `open` 重试，进入 `stale`，码 `ILLUS_CURRENT_MOVED`。非法文件且摘要仍匹配 → `failed`，码 `ILLUS_IMAGE_INVALID`。

无 claim、无租约。

## 7. 操作台页面

本机 loopback 扩展 WB-01，不改公网画廊。无 token 的 HTML 壳不得内嵌完整提示词、命题 `claim` 或图片字节。

| 路径 | 作用 |
| --- | --- |
| `/card-os/ops/{topic}` | 既有详情；增加「主体插画」入口（仅当该 topic 有 current） |
| `/card-os/ops/illustration/{intent_id}` | 复制提示词；上传 PNG；`illustrated` 时展示主图 + 命题列表 |

`open` / `failed`：主操作是「复制提示词」和「上传 PNG」。`illustrated`：展示演示页；提供取消。`stale` / `cancelled`：只读说明，须从 topic 页另开。

Token 仍放 `sessionStorage`，规则与 WB-01 相同。完整提示词与 PNG 只经 admin JSON / 鉴权媒体到达页面。

## 8. 鉴权

只要一把 `admin` 钥匙。人既扩词也上传图。本刀不发执行器 token。

| 主体 | scope | 允许 | 禁止 |
| --- | --- | --- | --- |
| 操作员 | 既有 `admin` | 建 intent、读完整提示词、上传 PNG、读演示页、取消 | 改模板快照；改命题；把图写入 current |

已发布 Skill `0.1.1` 的 `read` / `submit` 不能打此面。不新增 capability。

无 token：JSON 不得 200 空成功；媒体 URL 不得匿名读出 PNG。不新增 Nginx location（走既有 `/card-os/api/` 与 `/card-os/ops/`）。

## 9. HTTP

Admin（`Authorization: Bearer` admin，前缀 `/card-os/api/v1/admin/knowledge-illustration`）：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/` | 创建 intent；body `topic_slug`、`actor`；返回 `expanded_prompt` 与四对象摘要 |
| GET | `/{intent_id}` | 状态 + `expanded_prompt`；`illustrated` 时含命题列表与 `hero_png_sha256`；无则 `ILLUS_NO_INTENT` |
| POST | `/{intent_id}/image` | `multipart/form-data`：字段 `image`（PNG 文件）、`actor`；仅 `open` 或 `failed`，且四对象摘要仍匹配 |
| GET | `/{intent_id}/image` | 仅状态为 `illustrated` 且摘要仍匹配；返回 PNG 字节；`Cache-Control: private` |
| POST | `/{intent_id}/cancel` | `open` / `failed` / `illustrated` → `cancelled` |

没有执行器前缀，没有 `claim`。

PNG 上限 12 MiB。过大 → `ILLUS_IMAGE_TOO_LARGE`。魔数或 `Content-Type` 不是 PNG → `ILLUS_IMAGE_INVALID`。成功存储后计算 SHA-256，状态 `illustrated`。已是 `illustrated` 再 POST image → `ILLUS_ALREADY_ILLUSTRATED`（须先 cancel）。`stale` / `cancelled` 下 GET image → `ILLUS_CURRENT_MOVED` / `ILLUS_NOT_ILLUSTRATED`（`cancelled` 用后者）。

CLI 与 HTTP 同一函数。测试用夹具 PNG，不接 ChatGPT。library 根必须由调用方显式注入。HTTP 本机验收**不得**复用现网 KNOW-04 正在服务的 knowledge-library 路径。

磁盘布局（候选根下，不进 library current 目录）：

```text
illustration-intents/{intent_id}/
  meta.json
  expanded_prompt.txt
  hero.png          # 仅 illustrated
```

## 10. 演示页条文合同

`GET .../{intent_id}` 在 `illustrated`（以及创建后的 `open` 预览条文可选；**完成条件只要求 `illustrated` 页**）列出命题：

1. 读 intent 快照钉住的四对象字节；若磁盘上 current 已变，状态应为 `stale`，列表接口失败关闭 `ILLUS_CURRENT_MOVED`。
2. 取 knowledge-core 中 `standing=active` 的命题，稳定顺序：既有 core 文档顺序，不得按字母重排冒充新顺序。
3. 每条输出：`proposition_id`（或 core 上的稳定 id/slug）、`certainty`、`claim`。
4. 双语：当前四对象命题合同是**单一** `claim`。本刀**一行**展示该 `claim`。若未来 core 增加并列语言字段，且该字段非空且与 `claim` 不同，才增加第二行。禁止本刀调用翻译模型或 AGE-01 填第二行。
5. 不展示 `superseded`。`disputed` 不进本刀列表（只出 `active`）。
6. 操作员不能编辑列表。页面不得把 `claim` 画进图的 alt 以外的可复制知识改写框。

`open` 状态允许只读预览同一列表（仍钉快照），以便操作员在生图前看到将要并列的知识；无图时主图位为空。

## 11. 错误码

| 码 | 含义 |
| --- | --- |
| `ILLUS_NO_CURRENT` | slug 没有 library current |
| `ILLUS_SLUG_INVALID` | slug 非法 |
| `ILLUS_INTENT_ACTIVE` | 该 slug 已有未终态（含有效 `illustrated`）intent |
| `ILLUS_ALREADY_ILLUSTRATED` | 该 intent 已有 PNG，须先 cancel |
| `ILLUS_NO_INTENT` | intent 不存在 |
| `ILLUS_IMAGE_TOO_LARGE` | 超过 12 MiB |
| `ILLUS_IMAGE_INVALID` | 不是 PNG 或不被接受的空文件 |
| `ILLUS_CURRENT_MOVED` | current 前进或四对象摘要与快照不符 |
| `ILLUS_NOT_ILLUSTRATED` | 在非 `illustrated` 状态请求 PNG 字节 |
| `OPS_NOT_FOUND` | 沿用 WB-01 |

鉴权失败继续使用既有 AUTH 码。

## 12. 与 WB-03 / 后续投影

WB-03 文字四卡路径不变；本刀不调用 `render_locked`。本刀 PNG **不是** mapping-artifact 的附件，也不上 PORTAL-01 画廊。

后续若做「插画叠在四卡上」或「可交互烧字页」，另立切片：可复用本 intent 已存 PNG（按 sha 引用），或新开多图 intent。不得把那些切片的完成条件回写成本文件。

不得把本刀演示页登记为新的 `projection.family`。

## 13. 验收

本机：显式 library 根（临时或夹具，不是现网 KNOW-04 路径）+ 本机操作台/CLI。测试用夹具 PNG，**不**要求本刀会话内打开 ChatGPT 生图。不安装到现网。

必须成立：

1. 对**没有** current 的 slug 创建 intent 失败 `ILLUS_NO_CURRENT`；KNOW-04 六主题 Core 字节不被本刀改写。
2. 对注入 library 中已有 current 的 slug 创建成功；GET 返回非空 `expanded_prompt`，含对象名/分类/`safety_scope` 约束，且**不含**任一 `claim` 全文；无 token 的 ops 壳不含提示词。
3. 上传非 PNG 或空文件 → `failed` + `ILLUS_IMAGE_INVALID`；library current 不变。
4. 上传夹具 PNG 后状态 `illustrated`；GET 列表含全部 `standing=active` 命题的 `proposition_id` / `certainty` / `claim`；鉴权 GET image 的 sha256 等于文件；无 token 不能拉到图。
5. 在 intent 存活时替换 library current（或改四对象字节）后再 GET / 上传 → `stale` + `ILLUS_CURRENT_MOVED`；演示页不得继续把旧图当作有效页。
6. `failed` 且摘要仍匹配时可在同一 `intent_id` 重传；`cancelled` 后须新建。
7. 现网应用、Nginx、生产 library、画廊 ACCEPT-01 包摘要不被本刀改写。

本刀完成不等于四卡上架、不等于会员生图已人工验收外形。操作员可以在 ChatGPT 里真画一张再上传，那是手工步骤，不是 unittest 完成条件。

测试：intent 创建/幂等、无 current 门禁、模板扩词稳定性（claim 不得出现在 prompt）、PNG 成败、current 前进失效、既有 WB-01/02/03 与 compile-intent focused 回归。不要求完整 suite 清零既有 real-uvicorn 502。不要求生产安装。不要求真实 ChatGPT 会话。

## 14. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓：本设计、路线图、任务/交接、文档地图。

优先：`illustration-intent` 与 `illustration-hero-v1` 模板、`expanded_prompt`、PNG 上传与哈希、ops 插画页（复制提示词 / 上传 / 主图+命题）。不接图像 API，不接 Skill claim，不改 Nginx，不写生产 library，不改四对象，不改 WB-03 渲染。
