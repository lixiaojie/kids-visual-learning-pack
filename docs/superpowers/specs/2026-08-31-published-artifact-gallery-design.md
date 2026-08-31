# 已发布 Artifact 只读画廊（PORTAL-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §11 / §12](../../cognitive-card-os-system-design.md)、[PUBLISH-01](2026-08-31-immutable-package-publish-design.md)、[BROWSE-01](2026-08-30-knowledge-browse-projection-confirmation-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把 PUBLISH-01 不可变 package catalog 做成**只读 Artifact 画廊**：

1. 列出已发布 current 包；按 slug / 摘要筛选；
2. 展示四卡预览、A4 PDF、manifest、来源、QA、内容锁与 package 摘要、版本历史；
3. 状态隔离：未授权观众看不到 owner-only、撤回或草稿；发布版本可稳定下载。

本设计满足路线图 PORTAL-01 的本机完成条件。目标路径前缀是 `/card-os/`；公网域名与旧站替换仍属 SITE-01。

## 2. 非目标

- 不替代 [BROWSE-01](2026-08-30-knowledge-browse-projection-confirmation-design.md)：确认点 1 仍是知识库 + Projection 选择面。
- 不把 Projection family、页面骨架或 Renderer 写入 Knowledge Core。
- 不做知识 CMS：无命题编辑、无 family 覆盖、无 publish-from-UI。
- 不等于 SITE-01 / SITE-02、AUTH-01 浏览器会话、UPLOAD-01、MCP-01。
- 不 merge server `main`；不 push；不现网；不把服务绑到非 loopback。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、PUBLISH-01 内容身份。

## 3. 在分层中的位置

```text
Knowledge Core          事实；禁止呈现方案
        ↓
BROWSE-01               确认点 1；本设计不进入
        ↓
AGE / CONV / LOCK / RENDER / QA
        ↓
PUBLISH-01              不可变 package revision + current pointer
        ↓
PORTAL-01（本设计）    已发布 Artifact 消费面
        ↓
SITE-01                 后期：公网入口与 kids-world 替换
```

画廊是 Artifact 消费层。Knowledge library 仍是知识权威；BROWSE-01 继续承担确认点 1。

## 4. 观众与状态隔离

| 状态 | 磁盘事实 | 公开观众 | owner（admin token / CLI `--viewer owner`） |
| --- | --- | --- | --- |
| 已发布 public | 有 current，且 `visibility` 缺省或 `public` | 列表、详情、下载 current 与该包历史 revision | 可见 |
| owner-only | 有 current，`visibility=owner-only` | 与不存在相同：404，不出现在列表 | 可见，标明 owner-only |
| 撤回 | current 为空，历史 revision 仍在 | 与不存在相同 | 可见，标明 withdrawn |
| 草稿 | 不在 catalog（QA 工作区、无 `revision-NNNN` 的目录） | 不可见 | 不作为 package 列出 |

`visibility.json` 与 `current.json` 并列，**不是**治理对象，不进入 `package_sha256`。缺省为 `public`。公开查询不得因筛选词泄漏 owner-only / 撤回 slug。

允许下载的相对路径仅限：

```text
manifest.json
qa-report.json
sources.json
print.pdf
cards/cn-observe.png
cards/en-observe.png
cards/cn-know.png
cards/en-know.png
```

禁止路径穿越、符号链接跟随、把 candidate / library / Knowledge Core 当画廊根。

## 5. 界面与 CLI

单人、本机：

- CLI 写出静态 HTML（列表 + 包页），用本地浏览器打开。公开页无 `<form>` 写路径。
- loopback HTTP：公开 GET 不要求 token；owner 列表与 owner-only 下载要求既有 `admin` token。仍只监听 `127.0.0.1`。

`python3 -m cognitive_card_server.four_card_portal`

- `gallery --catalog-root --output-dir [--viewer public|owner] [--query]`
- `list --catalog-root [--viewer public|owner] [--query]`
- `visibility --catalog-root --slug --visibility public|owner-only --actor [--now]`

输出目录不得落在 catalog 根内。成功与失败均一行 canonical JSON。

## 6. HTTP 面

前缀：页面 `/card-os/`，JSON `/card-os/api/v1/portal`。catalog 根默认 `$CARD_OS_CANDIDATE_ROOT/package-catalog`。不新增生产必填环境变量。

| 方法 | 路径 | 鉴权 | 行为 |
| --- | --- | --- | --- |
| GET | `/card-os/` | 无 | 公开 HTML 列表（可 `?q=`） |
| GET | `/card-os/packages/{slug}` | 无 | 公开 HTML 详情；非公开 404 |
| GET | `/card-os/packages/{slug}/revisions/{nnnn}/files/{path}` | 无 | 公开下载；非公开 404 |
| GET | `/card-os/api/v1/portal/packages` | 无 | 公开 JSON 列表（可 `q`） |
| GET | `/card-os/api/v1/portal/packages/{slug}` | 无 | 公开 JSON 详情 |
| GET | `/card-os/api/v1/admin/portal/packages` | `admin` | 含 owner-only 与撤回 |
| GET | `/card-os/api/v1/admin/portal/packages/{slug}` | `admin` | owner 详情 |
| GET | `/card-os/api/v1/admin/portal/packages/{slug}/revisions/{nnnn}/files/{path}` | `admin` | owner 下载 |

公开路由不进入 `PROTECTED_ROUTES`。不新增 POST 发布、unlist、family 覆盖。

## 7. 与相邻切片的边界

| 切片 | 本设计 |
| --- | --- |
| BROWSE-01 | 保持独立 CLI / HTML / GET；本画廊不列出 Knowledge Core 命题或 family 选择面 |
| PUBLISH-01 | 只读消费 catalog；不改 revision 字节与内容身份 |
| ACCEPT-01 | 本机 `view/` 仍可存在；画廊是 catalog 级，不是单次验收页 |
| SITE-01 | 公网域名、kids-world 替换、移动端主入口验收不在本批 |

## 8. 验收

- 合成兔子 `age-5-6` 发布后：公开列表含该 slug；四卡、PDF、manifest、来源、QA、摘要可打开；下载字节等于 catalog 文件。
- `withdraw` 后公开列表与下载 404；owner 仍能看见历史。
- `visibility=owner-only` 后公开列表与下载 404；owner 可见。
- catalog 旁的草稿目录不出现。
- 画廊写入前后 Knowledge Core 字节不变；HTML 不含 Projection family 选择面与知识编辑表单。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 9. 错误码

| 码 | 含义 |
| --- | --- |
| `PORTAL_NOT_FOUND` | 公开观众不可见，或 slug/revision/文件不存在 |
| `PORTAL_UNSAFE_OUTPUT` | 画廊输出落在 catalog 内 |
| `PORTAL_UNSAFE_ROOT` | catalog 根不安全 |
| `PORTAL_VISIBILITY_INVALID` | visibility 不是 `public` / `owner-only` |
| `PORTAL_ACTOR_REQUIRED` | 缺少合法人类 actor |
| `PORTAL_QUERY_INVALID` | 筛选串非法 |
