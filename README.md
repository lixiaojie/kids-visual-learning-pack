# 芋头宇宙

Project slug: `kids-visual-learning-pack`

这是一个独立静态网页项目，不属于 `xiaojie-shares`。

项目用于按不同孩子喜欢的主题制作可视化学习看板，比如蜘蛛宇宙、汪汪队、生命世界、身体世界、宇宙世界等。最高层入口是“芋头宇宙”，它把已完成的动画主题和数据驱动的知识主题统一组织起来。

当前主题：

- `boards/kids-world/`：芋头宇宙，包含动画世界入口、六大知识世界、6 个首批知识主题、点击式任务和中英文切换。
- `boards/spider-verse/`：原创蛛网主题亲子故事板，包含 10 个视觉模块和家长讲解附录，覆盖角色、关系、能力、双剧情地图、问题卡、多元故事书、选择、艺术和创作卡，并已接入批量生成的图片素材。
- `boards/paw-patrol/`：汪汪队任务指挥中心，包含角色分工、地图热点、装备工坊、任务小游戏、流程复述和徽章收集。

详细目录说明见 `docs/project-structure.md`。

## Cognitive Card OS

儿童知识卡生产能力正在升级为“薄 Skill + 个人服务器核心”。`0.3.1` 服务端核心已经部署到
`https://www.yutou.space/card-os/`；首版仍由登录 ChatGPT Pro 的 Codex 客户端执行模型生成，
服务器统一负责协议、任务状态、候选、资产、排版、QA 和发布，不依赖 OpenAI API Key：

- [Cognitive Card OS 整体设计](docs/cognitive-card-os-system-design.md)
- [Cognitive Card OS 路线图与任务账本](docs/cognitive-card-os-roadmap.md)
- [生产部署证据、调用与运维手册](docs/operations/cognitive-card-server-deployment-2026-07-14.md)
- [Cognitive Card OS 历史资产迁移清单](docs/cognitive-card-os-asset-migration-inventory.md)
- [Pro 会员客户端执行架构](docs/superpowers/specs/2026-07-13-cognitive-card-pro-subscriber-execution-design.md)
- [订阅客户端执行基础实施计划](docs/superpowers/plans/2026-07-13-cognitive-card-subscriber-execution-foundation-plan.md)
- [远程 API、认证与协议实施计划](docs/superpowers/plans/2026-07-13-cognitive-card-remote-api-auth-protocol-plan.md)
- [历史资产机器清单与去重实施计划](docs/superpowers/plans/2026-07-13-cognitive-card-asset-inventory-dedup-plan.md)
- [个人服务器部署设计](docs/superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md)
- [个人服务器部署实施计划（DEPLOY-01 已完成；OPS-01 继续）](docs/superpowers/plans/2026-07-14-cognitive-card-server-deployment-plan.md)

现网公开发现入口：

```bash
curl --fail-with-body --silent --show-error \
  https://www.yutou.space/card-os/api/v1/health
curl --fail-with-body --silent --show-error \
  https://www.yutou.space/card-os/api/v1/capabilities
```

受保护 API 还需要 Card OS token、协议 `1` 和 minimum Skill release `0.1.0` 请求头；完整占位符示例、
日常检查、升级、备份恢复和回滚命令见上面的生产运维手册。当前服务只接受规范化锁定任务，
薄 Skill 的不可变发布与跨终端安装仍按路线图中的 `SKILL-01`、`SKILL-02` 推进。

历史资产机器盘点入口：

- [便携来源配置](migration/card-os/inventory-sources.json)
- [最新快照指针](migration/card-os/generated/latest.json)
- [机器 inventory](migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/inventory.json)
- [重复与候选关系报告](migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/duplicate-report.md)
- [扫描 warnings](migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/scan-warnings.json)

本机先从 `migration/card-os/inventory-roots.example.json` 创建被 Git 忽略的 `inventory-roots.local.json`，再运行：

```bash
npm run inventory:card-os
python3 scripts/card_os_asset_inventory.py \
  --config migration/card-os/inventory-sources.json \
  --roots migration/card-os/inventory-roots.local.json \
  --output-root migration/card-os/generated \
  --check
```

## 本地预览

打开总入口：

```bash
open index.html
```

总入口会进入：

```text
boards/kids-world/index.html
```

也可以直接打开某个主题：

```bash
open boards/spider-verse/index.html
```

汪汪队任务指挥中心是 Vite + React 页面，推荐安装依赖后启动本地服务器：

```bash
npm install
npm run dev
```

然后访问：

```text
http://127.0.0.1:5173/boards/kids-world/
http://127.0.0.1:5173/boards/paw-patrol/
```

也可以先构建：

```bash
npm run build:paw
npm run build:kids-world
```

其他静态主题可启动静态服务器：

```bash
python3 -m http.server 8000
```

然后访问总入口：

```text
http://localhost:8000
```

## 打印

具体主题页面右上角有“打印”按钮，也可以使用浏览器打印功能。

建议设置：

- 纸张：A4
- 方向：竖向
- 边距：默认或较小
- 背景图形：开启

每张学习卡会独立分页。

## 图片素材规范

图片源文件统一保留两份：

- `.png`：原始生成图，作为可回溯、可二次处理的源文件保留在仓库源码中。
- `.webp`：部署浏览版本，用于控制体积，适合 Vercel 免费服务的初期部署。

页面运行时优先引用 `.webp`。构建脚本会把各看板 `assets/` 目录中的 `.png` 原图排除在 `dist/` 外，只部署 `.webp`。

新增图片后可以运行：

```bash
npm run check:images
```

该检查会要求 `boards/**/assets/` 下的图片遵守 PNG/WebP 同名配对规则。

芋头宇宙的批量生图交接见 [docs/kids-world-image-generation-handoff.md](docs/kids-world-image-generation-handoff.md)。

## 版权边界

本项目使用原创 HTML/CSS 信息图表达，不包含官方截图、官方 Logo、精确角色服装复刻或影视分镜复刻。内容定位为家庭教育和亲子讲解材料。
