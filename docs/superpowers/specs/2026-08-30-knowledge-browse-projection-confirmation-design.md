# 知识浏览与 Projection 确认（BROWSE-01）

- Status: Approved for this planning tranche
- Date: 2026-08-30
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[Knowledge Core 设计](2026-08-19-knowledge-core-and-projection-architecture-design.md) §11.1 / §13.2、[PROJ-01](2026-08-30-projection-family-selection-design.md)、[WIRE-01](2026-08-30-knowledge-library-http-db-wiring-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`（另立实施任务）

## 1. 目标

为单人知识主路径补上 **确认点 1（合并方案确认）** 的人机界面：

1. 浏览知识库里的 topic、current 与历史 revision；
2. 只读查看 Knowledge Core 的单元与命题（来源、确定性、时效），不在界面里改事实；
3. 展示已有 Projection family 选择面（recommended / chosen / options），确认默认或知道如何用 CLI 覆盖。

本设计满足 Spec §11.1 的第一个显式确认点，以及 ADR-004「先看见知识、再确认映射」。它授权的是只读浏览 + 选择面展示，不是 Portal，也不是 CMS。

## 2. 非目标

- 不在 `knowledge-core` 内存页面布局、family 或 Renderer。
- 不新增第五个治理对象；不把选择记录写进 SQLite。
- 不等于 [PORTAL-01](../../cognitive-card-os-roadmap.md)：门户是已发布 Artifact（四卡预览、PDF、manifest）的画廊。
- 不做浏览器会话（AUTH-01 未完成项）；首版走 loopback + 现有 machine token，或由 CLI 写出静态 HTML。
- 不在 UI 里覆盖 family 并直接 publish。显式覆盖仍走 authoring CLI（`projection.family`）后重新 publish。
- 不实现 CONV-01、Renderer、打印、公网入口、现网部署。
- 不改 AUTHOR-05 默认表、四对象 schema、v1 FACT 密封合同。

## 3. 在分层中的位置

```text
Knowledge Core          事实；禁止呈现方案
        ↓
library current         不可变 revision + pointer
        ↓
BROWSE-01（本设计）    只读浏览 + 展示选择面 = 确认点 1
        ↓
projection-spec         已锁定的 family / blueprint
        ↓
PORTAL-01（后期）       已发布 Artifact 消费面 = 确认点 2 之后
```

选择计算继续调用 `select_projection_family`；本界面只展示 WIRE-01 已接的 `POST /projection-family` 结果。

## 4. 首版能力

| 能力 | 行为 |
| --- | --- |
| 主题列表 | 列出 library 根下的 topic；标明是否有 current、revision 数 |
| current / 历史 | 打开 current；可选打开 `revision-NNNN`；不提供删除 |
| 知识只读 | 展示 units、propositions、sources、freshness/health；命题 claim 按对象原文（当前多为英文 canonical） |
| 选择面 | 对当前包或等价 request 显示 recommended、chosen、`source`、options 的 fit 与 reason_codes |
| 确认默认 | 若 chosen = recommended：操作者继续接合 / 下游，界面不写盘 |
| 覆盖提示 | 若要选 options 中的 family：提示用 CLI 显式 `projection.family` 后重新 publish；UI 不写 revision |

可复用 authoring 已写出的 escaped HTML artifact 作为知识结构预览，但必须同时展示选择面，不能只有结构页。

## 5. 只读 HTTP 缺口

WIRE-01 已有 `GET .../current` 与 `POST /projection-family`。浏览还需要只读适配器（仍只调用 `KnowledgeLibrary`，不复制规则）：

| 方法 | 路径 | Scope | 行为 |
| --- | --- | --- | --- |
| GET | `/knowledge-library` | `read` | 列出 topic 与 current 摘要 |
| GET | `/knowledge-library/{topic}/revisions` | `read` | 列出 revision 号与 identity |
| GET | `/knowledge-library/{topic}/revisions/{nnnn}` | `read` | 返回四对象 + 已声明 artifacts 的只读视图 |

写路径保持 WIRE-01：accept / publish / unlist / refresh。本批不新增 publish-from-UI。

`{nnnn}` 为四位 revision 号。路径安全与 slug 规则同 library 设计。

## 6. 界面形态（首版）

单人、本机：

- 优先：CLI 对某个 topic/revision 生成一个静态 HTML 页（列表 + 知识 + 选择面），用本地浏览器打开。不依赖公网、不依赖 HTTP-only 会话。
- 可选：loopback HTTP 提供同上只读 JSON，同一 HTML 从 loopback 拉数据。machine token 放本机配置，不进 Git。

禁止：把完整 Knowledge Core 表单化；禁止在首版做搜索/筛选/多用户权限矩阵（那是 PORTAL-01）。

## 7. 与主路径其它切片的边界

| 切片 | 本设计 |
| --- | --- |
| LIB-01 / WIRE-01 | 已完成存储与接线；本设计只加只读列表/revision GET 与展示 |
| PROJ-01 | 选择算法不变 |
| CONV-01 | 确认之后才把 current 映射为 four-card / generation-input；不在本界面做 |
| PORTAL-01 | 后期；消费已发布包，不替代本界面 |
| SKILL-03 / OPS-02 | 不依赖 |

## 8. 验收

- 兔子 current：页面能列出单元与命题；选择面 chosen 为 `chaptered-guide`，`four-card` 为 discouraged。
- 几何 current：chosen 为 `progressive-exploration`。
- 改变 family 不会出现「只改 HTML、不经 CLI 就改了 knowledge-core 摘要」的路径。
- 无 current 的 topic 可浏览历史 revision，选择面仍可对包计算，但不把 unlist 状态显示为 current。
- 本设计不授权 merge 进 server `main`、不授权现网。
