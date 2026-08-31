# 令牌操作台只读知识源（WB-01）

- Status: Approved for this planning tranche
- Date: 2026-08-31
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[BROWSE-01](2026-08-30-knowledge-browse-projection-confirmation-design.md)、[PROJ-01](2026-08-30-projection-family-selection-design.md)、[WIRE-01](2026-08-30-knowledge-library-http-db-wiring-design.md)、[PORTAL-01](2026-08-31-published-artifact-gallery-design.md)、[AUTHOR-02 试产](../../cognitive-card-os-roadmap.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把确认点 1 接到单人能打开的**令牌操作台**，而不把公网画廊改成 CMS：

1. 操作员用现有 admin machine token 浏览知识库 topic、current 与历史 revision；
2. 只读看到 Knowledge Core 的单元、命题、来源、确定性与时效，以及 Projection family 选择面；
3. 生产知识库的兔子 current 是 AUTHOR-02 知识源（默认 `chaptered-guide`），与画廊里的 ACCEPT-01 四卡打印包分开。

本设计满足路线图 `WB-01`。公网 `https://www.yutou.space/card-os/` 继续只陈列已发布 Artifact。

## 2. 非目标

- 不替代 [BROWSE-01](2026-08-30-knowledge-browse-projection-confirmation-design.md) 的本机 CLI 静态 HTML；本设计是其令牌 HTTP 操作面。
- 不替代 [PORTAL-01](2026-08-31-published-artifact-gallery-design.md)；根 CTA 仍指向画廊；画廊不加「去生产」链接。
- 不在界面里改命题、覆盖 family、publish 或生成可视化（`WB-03`）。
- 不恢复四卡高视觉（`WB-02`）；不编译自由 prompt（`API-01`）。
- 不做 AUTH-01 浏览器登录会话、cookie、OAuth。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、PUBLISH-01 包字节。
- 不把 Uvicorn 绑到非 loopback；不默认 merge server `main`。

## 3. 程序位置

四刀都是痛点，必须排队。账本只在 [路线图](../../cognitive-card-os-roadmap.md)：

```text
Knowledge Core / library current
        ↓
WB-01（本设计）     令牌操作台：只读知识源 + 投影菜单
        ↓
WB-02               四卡恢复为有图、有内容的成熟投影
        ↓
WB-03               操作台选投影 → 生成 → 上架画廊
        ↓
API-01              自由 prompt 编译成知识源，进入同一操作台
```

`WB-01` 结束时：`WB-02` 为 `READY`；`WB-03` 仍 `BACKLOG`（依赖 `WB-02`）；`API-01` 保持 `IN PROGRESS`，作为队列第 4 项。不另建第二份待办文件。

公网画廊与操作台并行：

```text
公众     /card-os/          PORTAL-01 已发布四卡 / PDF
操作员   /card-os/ops/      本设计；无 admin token 看不到知识正文
```

## 4. 入口与鉴权

| 表面 | 路径 | 鉴权 | 可见内容 |
| --- | --- | --- | --- |
| 公开画廊 | `/card-os/`、`/card-os/packages/` | 无 | 与 DEPLOY-02 相同 |
| 操作台壳 | `/card-os/ops/`、`/card-os/ops/{topic}` | 无 | 不含命题/来源正文的 HTML 壳；可含 token 输入 |
| 操作台数据 | `/card-os/api/v1/admin/knowledge-library*` | `admin` Bearer | 主题列表、四对象只读视图、选择面 |

Token 规则：

- 沿用现有 `ccos_v1.` admin machine token 与 `Authorization: Bearer`；协议头与现网 Skill 调用相同。
- 页面可用本地输入把 token 放入 `sessionStorage`，随后 `fetch` 带 Authorization。禁止写入 Git、URL query、cookie、`localStorage`。
- 无 token 或非 `admin`：JSON **不得**返回 200 空列表。HTML 壳不得内嵌任何 claim、source locator 或 family 理由正文。
- 不做新的会话子系统。`capabilities.features.browser_session` 保持 `false`。

本机 BROWSE-01 的 `read` scope 列表路由保持原样，供 CLI 测试。公网操作台**只**打上表 admin 前缀，避免持有 Skill `read`/`submit` 令牌的客户端枚举知识库。

## 5. 页面

两个只读页，不做成表单 CMS，不提供搜索筛选。

### 5.1 主题列表 `/card-os/ops/`

列出知识库 topic：slug、是否有 current、revision 数、chosen family（有 current 时）。无 current 的 topic 可出现，并标明不是 current。

### 5.2 主题详情 `/card-os/ops/{topic}`

默认打开 current。同一页两块，缺一不可：

1. **知识**：units、propositions（对象原文 `claim`）、sources（title / institution / locator / source_id）、确定性、freshness/health。不把 family 或页面骨架写入此块。
2. **投影菜单**：recommended、chosen、`source`、options 的 `fit`（`eligible` / `discouraged`）与 `reason_codes`。计算继续调用 `select_projection_family`；本页只展示。

投影项这一刀只能看。点击不得生成、不得写 revision。覆盖 family 仍走 authoring CLI 后重新 publish（`WB-03` 才把选择接到生成）。

可从详情打开历史 `revision-NNNN` 只读视图；unlist 历史不得显示为 current。

`{topic}` 与 library slug 相同：`^[a-z][a-z0-9-]{2,63}$`。非法 slug 与未知 topic 对调用方表现相同（见 §9）。

## 6. HTTP 面

前缀：页面 `/card-os/ops/`，JSON `/card-os/api/v1/admin/knowledge-library`。library 根仍为 `$CARD_OS_CANDIDATE_ROOT/knowledge-library`。不新增生产必填环境变量。适配器只调用已有 `KnowledgeLibrary` 与 `select_projection_family`，不复制 accept/publish/unlist 规则，不新增 SQLite 表。

| 方法 | 路径 | Scope | 行为 |
| --- | --- | --- | --- |
| GET / HEAD | `/card-os/ops/` | 无 | 列表壳 HTML |
| GET / HEAD | `/card-os/ops/{topic}` | 无 | 详情壳 HTML |
| GET | `/card-os/api/v1/admin/knowledge-library` | `admin` | topic 与 current 摘要 |
| GET | `/card-os/api/v1/admin/knowledge-library/{topic}/current` | `admin` | `get_current`；无 current 时 `listed=false`、HTTP 200 |
| GET | `/card-os/api/v1/admin/knowledge-library/{topic}/revisions` | `admin` | revision 号与 identity |
| GET | `/card-os/api/v1/admin/knowledge-library/{topic}/revisions/{nnnn}` | `admin` | 四对象 + 已声明 artifacts 的只读视图 |
| GET | `/card-os/api/v1/admin/knowledge-library/{topic}/projection-family` | `admin` | 对 **current** 四对象重算选择面，不要求客户端 POST authoring JSON |

`{nnnn}` 为四位 revision 号。写路径保持 WIRE-01（accept / publish / unlist / refresh），本批不从 UI 调用。

选择面 GET：无 current 时 fail closed（§9），不得拿历史 revision 冒充 current 的 chosen。对指定历史 revision 看选择面不在本批；操作员先打开该 revision 的四对象视图。

公开 `GET /knowledge-library`（`read`）本批不改语义、不在 Nginx 为它增加除既有 `/card-os/api/` 之外的入口。

## 7. Nginx

在仓库 `ops/cognitive-card-server/nginx/card-os.conf` 增加 `/card-os/ops/` 的 GET/HEAD 反代，超时与头字段与现有 `/card-os/` 画廊相同。Uvicorn 仍只听 `127.0.0.1:8765`。

精确 `/card-os/`、`/card-os/packages/`、`/card-os/api/`、`/card-os/skill/v1/` 行为不变。catch-all `location ^~ /card-os/` 继续对其余路径 404。

未完成兔子知识库种子之前，不得 reload 把 `/card-os/ops/` 接到空库。回滚：去掉 ops location，恢复 DEPLOY-02 snippet；不删除 library 种子；不改画廊 catalog。

## 8. 种子数据

生产必须同时存在、且 **identity 分开**：

| 存储 | 内容 | 观众 |
| --- | --- | --- |
| knowledge-library `rabbit` current | AUTHOR-02 `rabbit-real.json` 编译结果；运行时 **不** 覆盖 `projection.family=four-card` | 操作台 |
| package-catalog `rabbit` current | ACCEPT-01 四卡打印包（现网已上架） | 公开画廊 |

验收时操作台兔子 chosen 必须为 `chaptered-guide`，`four-card` 为 `discouraged`。若现网 library current 已被四卡覆盖，先拆开再开放 ops。几何主题若库中已有则按 PROJ-01 显示 `progressive-exploration`；本批不强制向生产种子几何。

种子不得改写 catalog 里 ACCEPT-01 的 `package_sha256` / `content_lock_sha256`。

## 9. 错误处理

JSON 使用既有稳定信封 `{"error":{"code","message","request_id"}}`。Bearer 缺失或无效走既有鉴权码，本批不新造登录错误。

| 条件 | HTTP | 码 |
| --- | --- | --- |
| 无 token / 坏 token（admin JSON） | 401 | 既有鉴权码 |
| token 存在但无 `admin` | 403 | 既有鉴权码 |
| slug 非法或 topic / revision 不存在 | 404 | `OPS_NOT_FOUND` |
| current GET 但无 current | 200 | 无 error；body `listed=false` |
| 选择面 GET 但无 current | 409 | `OPS_NO_CURRENT` |
| 输出路径不安全或路径穿越 | 400 | `OPS_UNSAFE_PATH` |

禁止：未授权时 `200` 加空 `items`；在 HTML 壳里预渲染 claim；把 token 写入应用日志。未知 topic 与非法 slug 对公开探测同为 404，避免用 400 做 slug 预言机。

HEAD 对 ops HTML 必须与 GET 同码，不得沿用包文件当前的 HEAD 405。

## 10. 与相邻切片的边界

| 切片 | 本设计 |
| --- | --- |
| BROWSE-01 | CLI 静态 HTML 与 `read` GET 保留；本批不删 |
| PORTAL-01 / SITE-01 | 画廊与根 CTA 不改文案、不加 ops 链接 |
| CONV-01 / RUN-01 / RENDER-01 | 不调用 |
| WB-02 / WB-03 / API-01 | 只在路线图占位；本批不实现 |
| AUTH-01 浏览器会话 | 不提前做 |

## 11. 验收

- 带 admin token：列表含 `rabbit`；详情可见 4 个单元、8 条命题、4 个机构来源；chosen 为 `chaptered-guide`；`four-card` 在 options 且 `discouraged`。
- 不带 token：公网画廊外观与 DEPLOY-02 一致；admin JSON 401；ops HTML 源码不含命题正文。
- Skill `read`/`submit` token 不能列出 admin knowledge-library。
- 画廊 `rabbit` 包摘要仍为 ACCEPT-01 已记录值。
- 知识库兔子 current 的 Knowledge Core 文件在打开 ops 前后字节不变。
- 生产 Uvicorn 仍只听 `127.0.0.1:8765`。本设计不授权 merge server `main`，除非该执行会话另作明确授权。

## 12. 错误码汇总

| 码 | 含义 |
| --- | --- |
| `OPS_NOT_FOUND` | slug 非法，或 topic / revision 对 admin 亦不存在 |
| `OPS_NO_CURRENT` | 选择面要求 current，但 pointer 为空 |
| `OPS_UNSAFE_PATH` | 路径穿越或不安全输出 |

鉴权失败继续使用既有 AUTH 码，不在本表重复。
