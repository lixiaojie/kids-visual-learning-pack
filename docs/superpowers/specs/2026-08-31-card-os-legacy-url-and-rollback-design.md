# Card OS 旧 URL 映射与一次部署回滚（SITE-02）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-005](../../decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md)、[SITE-01](2026-08-31-card-os-kids-world-knowledge-entry-design.md)、[系统总设计 §11 / §12](../../cognitive-card-os-system-design.md)
- Authority: kids 仓为产品规范、静态入口与构建/部署脚本；不改 `/card-os/` Nginx 语义；画廊 HTML 仍由 server PORTAL-01 提供

## 1. 目标

在 SITE-01 已把知识主 CTA 切到 Card OS 之后，补两件入口兼容工作：

1. **旧 URL 映射**：已索引或可书签的旧 `kids-world` 链接不再静默 404；hash/query 打开冻结主题，独立路径保留替代说明。
2. **一次部署回滚**：合同 `activeMode` 切回 `parallel` 并重新生成根 hub 后，一次静态部署即可把主 CTA 交回旧站。

本设计满足路线图 SITE-02。默认交付仍是 `activeMode=card-os`；回滚是可执行开关，不是本批现网动作。

## 2. 非目标

- 不等于 MIG-02 / MIG-03：不把 13 个 C 级主题重制成四卡 package，也不写入 PUBLISH-01 catalog。
- 不把旧主题「升级」成画廊条目；一对一映射的目标是冻结档案，不是尚未存在的 Card OS package。
- 不替代 [BROWSE-01](2026-08-30-knowledge-browse-projection-confirmation-design.md)。
- 不改 `ops/cognitive-card-server/nginx/card-os.conf` 的 `/card-os/` 路由。
- 不 merge server `main`；不 push；不现网；不把 Uvicorn 绑到非 loopback。
- 不恢复 SITE-01 之前根入口的 `http-equiv refresh` 自动跳转。回滚只交换主 CTA。

## 3. 在分层中的位置

```text
SITE-01                 根入口主 CTA → Card OS；旧站为冻结档案
        ↓
SITE-02（本设计）      旧 URL 映射 + activeMode 回滚开关
        ↓
MIG-03                  后期：C 级主题按新工作流重制
```

知识权威仍是 library revision。映射不得把旧网页 JSON 当作已发布 package。

## 4. 旧 URL 合同

合同文件仍是 `shared/knowledge-entry.json`。冻结 slug 列表沿用 SITE-01 的 `frozenKidsWorldTopics`。

每个冻结 slug 承认以下来源，均不得 404：

| 来源 | 例 | 行为 |
| --- | --- | --- |
| SPA 规范 hash | `boards/kids-world/index.html#topic/dinosaurs` | 打开旧主题页 |
| SPA 短 hash | `boards/kids-world/index.html#dinosaurs` | 与规范 hash 相同 |
| SPA query | `boards/kids-world/index.html?topic=dinosaurs` | 打开旧主题页 |
| 独立路径（registry `href`） | `boards/dinosaurs/index.html` | **替代说明页**，不是旧站 SPA |

保留页内锚点，不当成主题 slug：`#worlds`、`#recent-observation`、空 hash。

未知但形如主题的 hash（例如计划中的 `immune-system`）继续使用旧站已有的「这个探索页还在准备中。」，不静默回到空白首页。

独立路径替代说明页必须同时提供：

- 打开冻结旧主题页（`boards/kids-world/index.html#topic/{slug}`）；
- 打开 Card OS 画廊（`cardOsPublicUrl`）；
- 说明：该主题仍是 C 级冻结档案，还不是四卡 package。

不在替代说明页上做即时自动跳转。书签用户必须能读到说明；主链是旧主题页。

## 5. 回滚开关

`activeMode` 仍只有两相，SITE-01 已定义：

| 相 | 根入口主 CTA | 次入口 |
| --- | --- | --- |
| `card-os`（默认） | `cardOsPublicUrl` | 冻结旧站 |
| `parallel`（回滚） | `kidsWorldArchiveHref` | Card OS 画廊 |

根 `index.html` **由合同生成**，不得再手写与 `activeMode` 不一致的主 CTA。生成器：`scripts/render-knowledge-entry.mjs`。

一次部署回滚（授权现网时才执行，本批不跑）：

1. 把 `shared/knowledge-entry.json` 的 `activeMode` 改为 `parallel`；
2. 运行 `node scripts/render-knowledge-entry.mjs --write-hub`；
3. 按既有 `scripts/deploy.sh` 或静态构建部署一次（含根 `index.html` 与 `shared/`）。

两相都禁止 `http-equiv refresh`。回滚不是把根入口重新自动灌进旧站。

`kids-world` 顶栏说明随 `activeMode` 变化：`card-os` 时标明本页是冻结档案；`parallel` 时标明 Card OS 为并行次入口、本页仍是主入口。该文案随 kids-world 构建打进包，因此回滚部署必须包含 kids-world 重建（`deploy.sh` 已如此）。

## 6. 构建与部署接线

| 通道 | 替代说明页如何到达公网 |
| --- | --- |
| `scripts/build-static.sh`（Vercel / EdgeOne） | 写入 `dist/boards/{slug}/index.html` |
| `scripts/deploy.sh`（自有服务器） | 生成后 rsync 到服务器 `boards/{slug}/`，**不加** `--delete`，以免删掉 `kids-world` / 主题馆 |

不把 stub 提交为 13 份手写 HTML 源文件；由冻结 slug 与 `topic-registry.json` 标题生成。

生产根入口继续隐藏 `spider-verse` / `paw-patrol`。

## 7. 与相邻切片的边界

| 切片 | 本设计 |
| --- | --- |
| SITE-01 | 消费已有两相合同与 Nginx 画廊反代；不改 `/card-os/` 语义 |
| PORTAL-01 | 不改画廊可见性或 catalog 字节 |
| MIG-03 | 重制完成后，才允许把某 slug 的映射目标从档案改到 package；本批不预置空 package 链接 |
| DEPLOY-01 | 0.3.1 历史证据保留；本批只追加回滚步骤说明 |

## 8. 验收

- 13 个冻结 slug：短 hash、规范 hash、query 都能打开旧主题。
- 13 个 `boards/{slug}/index.html` 存在于静态构建产物，含替代说明与两条链。
- `renderHubHtml(card-os)` 与提交的根 `index.html` 一致；`renderHubHtml(parallel)` 的 `data-knowledge-entry="primary"` 指向旧站。
- 生产根 HTML 不含 `paw-patrol` / `spider-verse`。
- 本设计不授权 merge server `main`、不授权现网回滚或部署。

## 9. 错误与回退

若只改 JSON 不重新生成 hub，根 CTA 会与合同漂移。测试必须拒绝该漂移。

现网仍须先有 SITE-01 的 Nginx 画廊反代，再部署根入口。SITE-02 回滚不能替代该顺序：`parallel` 只把主 CTA 交回旧站，Card OS 次入口在 Nginx 未 reload 时仍可能打到 capabilities 307。
