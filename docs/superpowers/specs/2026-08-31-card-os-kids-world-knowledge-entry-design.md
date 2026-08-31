# Card OS 替换 kids-world 知识入口（SITE-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-005](../../decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md)、[系统总设计 §11 / §12](../../cognitive-card-os-system-design.md)、[PORTAL-01](2026-08-31-published-artifact-gallery-design.md)、[MIG-01 清单](../../cognitive-card-os-asset-migration-inventory.md)
- Authority: kids 仓为产品规范与静态入口、Nginx snippet；画廊 HTML 仍由 server PORTAL-01 提供

## 1. 目标

把 Card OS 已发布 Artifact 画廊做成**知识主入口**，替换 `kids-world` 承担的知识首页职责：

1. 先并行：`/card-os/` 画廊与旧 `kids-world` 都可打开；
2. 再切主入口：根页面主 CTA 指向 Card OS 画廊；旧站降为冻结档案；
3. `spider-verse` 与 `paw-patrol` 继续作为旧版主题馆，生产根入口不暴露它们。

本设计满足路线图 SITE-01。SITE-02 的旧 URL 映射与回滚开关不在本批。

## 2. 非目标

- 不等于 [SITE-02](2026-08-31-card-os-legacy-url-and-rollback-design.md)：旧 hash/URL 一对一映射、替代说明页、一次部署回滚开关接线见该设计。
- 不等于 MIG-02 / MIG-03：不把 13 个 C 级主题重制成四卡 package。
- 不替代 [BROWSE-01](2026-08-30-knowledge-browse-projection-confirmation-design.md)。
- 不把 Projection family 写入 Knowledge Core。
- 不 merge server `main`；不 push；不现网；不把 Uvicorn 绑到非 loopback。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、PORTAL-01 可见性合同。

## 3. 在分层中的位置

```text
Knowledge Core          事实；禁止呈现方案
        ↓
BROWSE-01               确认点 1；本设计不进入
        ↓
PUBLISH-01 / PORTAL-01  不可变 package + 只读画廊
        ↓
SITE-01（本设计）      公网知识入口与 kids-world 主 CTA 切换
        ↓
SITE-02                 后期：旧 URL 映射与回滚开关
```

知识权威仍是 library revision。根入口只指向已发布画廊，不指向 Knowledge Core 浏览面。

## 4. 两相入口

合同文件：`shared/knowledge-entry.json`。

| 相 | `activeMode` | 根入口主 CTA | 旧站 |
| --- | --- | --- | --- |
| 并行验收 | `parallel` | `kids-world` | Card OS 为次入口 |
| 切主入口 | `card-os` | `https://www.yutou.space/card-os/` | `boards/kids-world/index.html` 为冻结档案 |

本批交付 `activeMode=card-os`。并行相保留在合同里，供 SITE-02 回滚开关读取；本批不接线该开关。

根 `index.html`：

- 取消自动跳进 `kids-world`；
- 主卡片：Card OS 知识画廊；
- 次卡片：冻结的旧知识站；
- 生产构建不得出现 `spider-verse` / `paw-patrol` 链接。

`kids-world` 首页增加迁移说明，主题页保持可打开。旧 hash（`#dinosaurs` 等）仍落在旧站，直到 SITE-02。

## 5. 13 个旧主题的冻结决定

MIG-01 已将现站 13 个知识主题定为 C 级：不能机械映射为四卡，须按新工作流重制。SITE-01 把该决定当作入口切换门禁中的「明确归档/冻结决定」：

| slug | 决定 |
| --- | --- |
| `insects-and-spiders` | C 级冻结；仍由旧站提供 |
| `cicada-life` | 同上 |
| `animal-classification-tree` | 同上 |
| `blood-cells-3d` | 同上 |
| `solar-system-overview` | 同上 |
| `earth-climate-cities` | 同上 |
| `llm-kids-basics` | 同上 |
| `dinosaurs` | 同上 |
| `ecosystem` | 同上 |
| `digestion` | 同上 |
| `water-cycle` | 同上 |
| `robots` | 同上 |
| `moon-phases` | 同上 |

正式四卡发布仍走 PUBLISH-01 catalog。旧主题不得因为曾公开展示而进入画廊。

## 6. Nginx 公网接线

现网 `0.3.1` snippet 把精确 `/card-os/` 307 到 capabilities，并把非 API `/card-os/` 子路径 catch-all 404。SITE-01 改为：

| 路径 | 行为 |
| --- | --- |
| `/card-os` | 仍 `308` 到 `/card-os/` |
| `/card-os/` | GET/HEAD 反代 `127.0.0.1:8765`（PORTAL-01 公开列表） |
| `/card-os/packages/` | GET/HEAD 反代同一应用（详情与允许的文件下载） |
| `/card-os/api/` | 不变；含 health、capabilities、portal JSON、受保护 API |
| `/card-os/skill/v1/` | 不变 |
| 其余 `/card-os/` | 仍 catch-all `404`，无 `root`/`alias`/`try_files`/`proxy_pass` |

Uvicorn 仍只听 `127.0.0.1:8765`。本批只改仓库内 snippet 与测试，不 reload 生产 Nginx。

## 7. 与相邻切片的边界

| 切片 | 本设计 |
| --- | --- |
| PORTAL-01 | 消费已有画廊 HTML/JSON；不改可见性或 catalog 字节 |
| BROWSE-01 | 保持独立；根入口不链到确认点 1 |
| SITE-02 | 旧 URL 映射与回滚开关 |
| DEPLOY-01 | 0.3.1 历史证据保留；本批路由是待应用合同 |

## 8. 验收

- 合同 `activeMode=card-os`；根入口主 CTA 为 Card OS URL；旧站链接仍在。
- 生产根 HTML 不含 `paw-patrol` / `spider-verse`。
- Nginx 选择：`/card-os/` 与 `/card-os/packages/...` 进反代；`/card-os/api/v1/capabilities` 仍进 API；`/card-os/candidates/` 等仍 404。
- `kids-world` 首页有迁入口说明；至少一个现有主题 JSON 仍可被旧站打开。
- 本设计不授权 merge server `main`、不授权现网。

## 9. 错误与回退

生产尚未应用本 snippet 时，点击 Card OS 仍可能落到 capabilities 307。这是已知缺口，须在授权现网时先 reload Nginx、再部署根入口。回滚开关属于 SITE-02。
