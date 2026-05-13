# 芋头宇宙 — 架构迭代 Spec v1.3

> 生成日期：2026-05-13
> 基线：`spec-v2.md`（12 render-ready topic，79 WebP，validate 全绿）
> v1.3 修正：小程序路线决策树化、EdgeOne 单通配符+caches、Taro 复用率保守化、shared package 前置、channel-policy 接入点完整化

---

## 0. 版本结论与拆分策略

**两条线独立推进，互不阻塞**：

```
Part A: H5 迭代（EdgeOne + 构建链 + IP 清理 + 内容风险收敛）
  → 不依赖小程序审批，可立即开始
  → A0 把公网内容风险收敛也纳入（不只是小程序需要）

Part B: 小程序版本（路线由主体类型决定）
  → B0 Gate 确认主体类型后选择技术路线
  → 前置依赖：Part A 的 A1-A2 完成（图片 CDN + 干净 URL）
```

---

## 1. 当前事实基线（2026-05-13 验证）

| 项目 | 数据 |
|------|------|
| 世界 | 7（1 动画 + 6 知识） |
| registry topic | 18（12 render-ready + 6 planned） |
| 图片 | 79 WebP，135 asset 引用校验通过 |
| 校验 | `npm run validate` 三项全绿 |
| App.tsx | 23 行，33 TS/TSX 文件 |
| 部署 | GitHub + EdgeOne（控制台已关联，代码侧 `edgeone.json` 待补）+ Vercel + 自有服务器 |
| 小程序 | 无代码，认证已提交，**主体类型待确认** |
| 架构债 | 4 HTML 硬编码 IP、构建链未强制 validate、无 edgeone.json、无 legal 页面 |

---

## Part A: H5 迭代

### A.0 公网内容风险收敛

> 不只影响小程序，EdgeOne 正式域名一旦公开，IP 衍生内容也有品牌/版权风险。

**产出**：
- `channel-policy.json`（单一数据源）
- H5 production 默认隐藏 paw-patrol / spider-verse 入口
- preview 环境保留访问
- check-dist 按 CHANNEL 检查入口链接

**channel-policy.json**：

```json
{
  "web-production": {
    "visibleBoards": ["kids-world"],
    "hiddenBoards": ["paw-patrol", "spider-verse"],
    "visibleTopics": "all-render-ready"
  },
  "web-preview": {
    "visibleBoards": ["kids-world", "paw-patrol", "spider-verse"],
    "visibleTopics": "all"
  },
  "miniprogram": {
    "visibleBoards": ["kids-world"],
    "hiddenBoards": ["paw-patrol", "spider-verse"],
    "visibleTopics": [
      "dinosaurs", "ecosystem", "animal-classification-tree",
      "insects-and-spiders", "solar-system-overview", "moon-phases",
      "water-cycle", "earth-climate-cities", "robots",
      "llm-kids-basics", "digestion", "blood-cells-3d"
    ]
  }
}
```

**接入点**（谁读取、在哪里过滤）：

| 接入点 | 行为 |
|--------|------|
| `data/loaders/load-map.ts` | H5 运行时根据 `CHANNEL` 环境变量过滤 topicCards（首版可硬编码 web-production） |
| Taro 首页 | 只展示 miniprogram.visibleTopics |
| `validate-compliance.mjs` | 检查 miniprogram visibleTopics 全部 render-ready + 不含 paw-patrol/spider-verse |
| `check-dist.mjs` | production dist 中 root index.html 不暴露 paw-patrol/spider-verse 链接 |
| `exploration-map.json` | 数据不改，过滤在运行时/构建时做 |

---

### A.1 EdgeOne 配置 + 构建链

**edgeone.json**（遵循 EdgeOne 单通配符规则）：

```json
{
  "name": "yutou-universe",
  "installCommand": "npm ci",
  "buildCommand": "npm run build:edgeone",
  "outputDirectory": "./dist",
  "nodeVersion": "20.18.0",
  "headers": [
    {
      "source": "/*",
      "headers": [
        { "key": "Cache-Control", "value": "no-cache, must-revalidate" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    },
    {
      "source": "/boards/kids-world/assets/*",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/boards/paw-patrol/assets/*",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/shared/icons/*",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=86400" }
      ]
    }
  ],
  "caches": [
    {
      "source": "/boards/kids-world/assets/*",
      "cacheTtl": 31536000
    },
    {
      "source": "/boards/paw-patrol/assets/*",
      "cacheTtl": 31536000
    },
    {
      "source": "/shared/icons/*",
      "cacheTtl": 86400
    }
  ]
}
```

注意：
- source 使用单 `*` 通配（EdgeOne 限制）
- `/*` 作为默认规则设 no-cache，具体 assets 路径覆盖长缓存
- 不设 `X-Frame-Options`（预留 web-view 兼容性）
- 不设 CSP `frame-ancestors`
- `caches` 字段控制边缘缓存 TTL
- **preview 部署后必须实测**：curl 验证 response headers + 微信开发者工具验证 web-view 可加载

**环境变量**：确认 EdgeOne `npm ci` 时 NODE_ENV 不是 `production`。如果是，ajv（devDependency）不会安装，validate 脚本 fail。必要时把 ajv 移到 dependencies。

**build-static.sh**：

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)" && cd "$ROOT"

echo "==> validate"
npm run validate

echo "==> clean"
rm -rf dist && mkdir -p dist/boards

echo "==> generate site meta"
npm run generate:site-meta

echo "==> build kids-world + paw-patrol"
npx vite build boards/kids-world --base=./ --emptyOutDir --outDir ../../dist/boards/kids-world
npx vite build boards/paw-patrol --base=./ --emptyOutDir --outDir ../../dist/boards/paw-patrol

echo "==> copy root + shared + spider-verse + legal + verification"
cp .generated-html/index.html dist/
cp -r shared dist/
cp -r boards/spider-verse dist/boards/
find dist/boards/spider-verse \( -name '*.test.*' -o -name '*.spec.*' -o -name '.DS_Store' \) -delete
[ -d legal ] && cp -r legal dist/
cp public-verification/MP_verify_*.txt dist/ 2>/dev/null || true

echo "==> clean PNG"
find dist/boards -path '*/assets/*.png' -delete

echo "==> check-dist"
npm run check:dist
```

**check-dist.mjs 必检项**：

```
1. dist/index.html 存在
2. dist/boards/kids-world/index.html 存在
3. dist/shared/icons/favicon.ico 存在
4. dist 中不存在 118.145.242.99
5. dist 中不存在 __SITE_URL__ / __SITE_TITLE__ 等未替换占位符
6. dist 中不存在 localhost / 127.0.0.1
7. dist 中不存在 http://（非 https 的外部链接）
8. 如果 CHANNEL=production：dist/index.html 不含 paw-patrol/spider-verse 链接
9. 所有 og:image 值以 https:// 开头
```

**package.json**：

```json
{
  "build": "npm run build:static",
  "build:static": "bash scripts/build-static.sh",
  "build:edgeone": "npm run build:static",
  "check:dist": "node scripts/check-dist.mjs",
  "generate:site-meta": "node scripts/generate-site-meta.mjs",
  "validate": "npm run validate:topics && npm run validate:i18n && npm run validate:assets && npm run validate:compliance",
  "validate:compliance": "node scripts/validate-compliance.mjs"
}
```

`build-vercel.sh` 改为代理：`exec bash scripts/build-static.sh`

---

### A.2 site.config + HTML meta 注入

**模板机制**（源文件与产物分离）：

```
templates/                              # 模板源（带占位符）
├── index.html.tpl
├── boards/kids-world/index.html.tpl
├── boards/paw-patrol/index.html.tpl
└── boards/spider-verse/index.html.tpl

.generated-html/                        # 构建时生成（.gitignore）
├── index.html
└── boards/*/index.html

scripts/generate-site-meta.mjs          # 模板 → .generated-html
```

**site.config.json**：

```json
{
  "siteName": "芋头宇宙",
  "siteUrl": "https://kids.yutou-universe.cn",
  "defaultTitle": "芋头宇宙｜儿童认知可视化学习地图",
  "defaultDescription": "面向孩子和家长共读的可视化认知学习地图。",
  "ogImage": "/shared/icons/og-image.jpg",
  "favicon": "/shared/icons/favicon.ico"
}
```

**注入逻辑**：
1. 读 `site.config.json` + `SITE_URL` 环境变量覆盖
2. 处理 `templates/*.tpl` → `.generated-html/`
3. 替换 `__SITE_URL__`、`__SITE_TITLE__`、`__SITE_DESCRIPTION__`、`__OG_IMAGE__`
4. spider-verse 的 `index.html.tpl` 直接 sed 替换 IP → siteUrl（不用占位符，因为是纯静态 HTML）

`.generated-html/` 加入 `.gitignore`。

---

### A.3 路由增强

修改 `boards/kids-world/src/hooks/use-hash-route.ts`：

```typescript
import { useEffect, useState } from "react";

function resolveSlug(): string | null {
  const params = new URLSearchParams(window.location.search);
  const queryTopic = params.get("topic");
  if (queryTopic) return queryTopic;
  const hashMatch = window.location.hash.match(/^#topic\/(.+)$/);
  return hashMatch?.[1] ?? null;
}

export function useHashRoute() {
  const [slug, setSlug] = useState<string | null>(resolveSlug);

  useEffect(() => {
    const handler = () => {
      setSlug(resolveSlug());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", handler);
    window.addEventListener("popstate", handler);
    return () => {
      window.removeEventListener("hashchange", handler);
      window.removeEventListener("popstate", handler);
    };
  }, []);

  return slug;
}
```

**URL Contract**：

```
H5:
  /boards/kids-world/?topic=dinosaurs&locale=zh-CN
  /boards/kids-world/#topic/dinosaurs  (兼容)

优先级: query.topic > hash topic > home
优先级: query.locale > localStorage.locale > zh-CN

未知 slug: 回首页 + 轻提示"这个探索页还在准备中"
```

---

### A.4-A.6 体验 + 内容（延后不阻塞发布）

- A4: CSS 拆分（946 行 → tokens/layout/home/topic/interactions）
- A5: 页面过渡动画 + 互动反馈动画
- A6: 剩余 6 planned topic 扩展

---

### A.7 部署环境

| 环境 | 分支 | 域名 |
|------|------|------|
| production | `main` | `https://kids.yutou-universe.cn`（ICP 后） |
| preview | `develop` | EdgeOne preview URL |
| 自有服务器 | `main` | `https://118.145.242.99/kids/`（过渡/备用） |

**ICP 并行策略**：域名未备案期间用 EdgeOne 默认域名跑通全链路，备案通过后切自定义域名。

---

### A.8 发布与回滚

**Release Flow**：

```
feature → PR → GitHub check (validate + build + check-dist)
  → EdgeOne preview → 人工验收（5 topic + 分享图 + 移动端）
  → merge main → EdgeOne production
  → 记录 release-manifest.json + docs/releases/YYYY-MM-DD.md
```

**release-manifest.json**（构建时自动生成到 dist/）：

```json
{
  "version": "2026.05.13-001",
  "commit": "GIT_SHA",
  "topics": 12,
  "assets": 79,
  "deployedAt": "ISO_TIMESTAMP"
}
```

**回滚**：EdgeOne 回滚到上一部署 / git revert + redeploy。

---

## Part B: 微信小程序

### B.0 Gate: 主体类型决策

```
主体确认结果 → 技术路线：

┌─ 企业/组织主体（支持 web-view）
│    → 优先 web-view 壳（最快上线，零组件重写）
│    → Part A 的 H5 即为小程序内容
│
├─ 个人主体（不支持 web-view）
│    → Taro 原生小程序（React 语法编译到小程序）
│    → 本文档后续以此路线展开
│
└─ 未确认
     → 只做 B1（合规清单 + 隐私政策），不启动实现
```

**当前状态**：个人主体，确认走 **Taro 原生方案**。

---

### B.1 合规清单

**产出**：
- `docs/compliance/wechat-miniprogram-checklist.md`
- `docs/compliance/content-ip-risk-register.md`
- 隐私政策/用户协议（小程序内原生页面，不需要域名）
- `validate-compliance.mjs`

**隐私政策最小范围**：不收集儿童信息、不登录、进度仅本地存储、不接第三方统计、网络请求仅加载 CDN 图片。

---

### B.2 共享数据层：packages/kids-content

> 不用相对路径 import，直接抽 shared package。

**结构**：

```
packages/
└── kids-content/
    ├── package.json          # { "name": "@yutou/kids-content", "main": "src/index.ts" }
    ├── tsconfig.json
    └── src/
        ├── index.ts          # re-export 所有公共接口
        ├── types/            # ← 从 boards/kids-world/src/types/ 移入
        │   ├── world.ts
        │   ├── topic.ts
        │   └── assets.ts
        ├── data/             # ← 从 boards/kids-world/src/data/ 移入
        │   ├── loaders/
        │   ├── topics/
        │   ├── locales/
        │   ├── schema/
        │   ├── exploration-map.json
        │   ├── topic-registry.json
        │   └── image-generation-manifest.json
        └── lib/              # ← 从 boards/kids-world/src/lib/ 移入
            └── asset-map.ts
```

**H5 和 Taro 都从这里引用**：

```typescript
import { getTopic, getMap, hasTopicData } from "@yutou/kids-content";
import type { Topic, Locale, ExplorationMap } from "@yutou/kids-content";
```

**workspace 配置**（根 package.json）：

```json
{
  "workspaces": ["packages/*", "boards/*", "apps/*"]
}
```

**首版可简化**：如果 monorepo 配置复杂度太高，首版用 tsconfig paths alias 替代：

```json
// apps/miniprogram/tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@yutou/kids-content/*": ["../../packages/kids-content/src/*"]
    }
  }
}
```

---

### B.3 Taro 复用率（保守估计）

| 层 | 复用率 | 说明 |
|---|---:|---|
| TypeScript types | 90-100% | 直接用 |
| topic JSON / overlay / schema | 90-100% | 数据资产直接用 |
| locale merge / load-topic / load-map | 60-90% | 取决于 Taro 对 JSON import 的支持 |
| 组件业务逻辑 | 40-60% | clickTask 状态机可复用，DOM 标签和事件要改 |
| 样式 | 20-40% | CSS → SCSS/rpx，小程序 CSS 子集限制明显 |
| 路由 | 0-20% | hash route 完全重写为 Taro 页面路由 |
| 图片组件 | 30-50% | 思路复用（manifest → URL），实现改为 `<Image>` |
| **整体** | **40-50%** | 主要收益：保留 React/TS 心智模型 + 数据层高复用 |

**Taro 的核心收益不是"代码复用 70%"，而是**：
1. 保留 React + TypeScript 开发体验
2. 数据层（types + JSON + loaders）几乎零改动
3. ClickTask 等交互状态机逻辑直接搬
4. 降低从 H5 到原生的认知切换成本
5. 编译产物是标准小程序包，审核友好

---

### B.4 项目结构

```
apps/miniprogram/
├── project.config.json
├── package.json
├── tsconfig.json
├── config/
│   ├── index.ts              # Taro 编译配置
│   └── prod.ts
└── src/
    ├── app.ts
    ├── app.config.ts
    ├── app.scss
    ├── pages/
    │   ├── index/            # 首页：世界入口 + 推荐 topic
    │   ├── topic/            # Topic 详情页（11 个模块）
    │   └── about/            # 家长说明 + 隐私政策
    ├── components/           # 适配后的小程序组件
    │   ├── topic/            # 9 个 section 组件（View/Text/Image）
    │   ├── home/
    │   └── shared/           # GeneratedImage → <Image src={cdnUrl}>
    └── styles/
        ├── tokens.scss
        └── components.scss
```

### B.5 图片策略

79 张 WebP 远超小程序 2MB 包限制，必须走 CDN：

```tsx
const CDN_BASE = "https://kids.yutou-universe.cn/boards/kids-world/assets";

export function GeneratedImage({ assetPath, className }: Props) {
  if (!assetPath) return null;
  return <Image src={`${CDN_BASE}${assetPath}`} mode="aspectFill" className={className} />;
}
```

**前置依赖**：Part A 完成后 EdgeOne 图片 URL 稳定可访问。

### B.6 路由

| 页面 | 路径 | 参数 |
|------|------|------|
| 首页 | `/pages/index/index` | — |
| Topic | `/pages/topic/index` | `slug` + `locale` |
| 关于 | `/pages/about/index` | — |

```tsx
// 跳转
Taro.navigateTo({ url: `/pages/topic/index?slug=${slug}&locale=${locale}` });

// 读参数
const router = useRouter();
const slug = router.params.slug || "dinosaurs";
```

### B.7 分享

```tsx
useShareAppMessage(() => ({
  title: `芋头宇宙｜${topic.title}`,
  path: `/pages/topic/index?slug=${slug}&locale=${locale}`,
  imageUrl: `${CDN_BASE}/shared/icons/og-image.jpg`
}));
```

### B.8 任务包

| Task | 名称 | 依赖 | 说明 |
|------|------|------|------|
| B1 | 合规清单 | 无 | checklist + 隐私政策 + validate-compliance |
| B2 | 抽 packages/kids-content | Part A A1-A2 | types + data + lib 抽为共享包 |
| B3 | Taro 初始化 + 数据层接入 | B2 | apps/miniprogram + alias/workspace |
| B4 | 首页 | B3 | 世界入口 + topic 推荐 |
| B5 | Topic 详情页（9 组件适配） | B3 | 逐组件：View/Text/Image + rpx |
| B6 | ClickTaskCard 适配 | B5 | 三种互动类型 |
| B7 | 分享 | B5 | useShareAppMessage + useShareTimeline |
| B8 | 真机 QA | B4-B7 | iOS/Android + 5 topic |
| B9 | 提审发布 | B8 | 审核说明 |

B5 工作量最大（9 个组件），可拆子任务逐个推进。

---

## 上线前 Checklist

### Part A

- [ ] `edgeone.json` 提交并 preview 验证 response headers
- [ ] `npm run build:edgeone` 本地通过
- [ ] `check-dist` 通过（无 IP/占位符/localhost）
- [ ] production dist 不暴露 paw-patrol/spider-verse 入口
- [ ] `?topic=slug&locale=xx` 路由工作
- [ ] `#topic/slug` 兼容
- [ ] EdgeOne production HTTPS 正常
- [ ] 图片 CDN URL 稳定（小程序依赖）
- [ ] release-manifest.json 自动生成

### Part B

- [ ] Taro 编译通过，开发者工具可预览
- [ ] packages/kids-content 被正确 import
- [ ] 首页展示世界入口 + 推荐 topic
- [ ] Topic 详情 11 模块渲染正常
- [ ] ClickTaskCard 三种类型工作
- [ ] 图片通过 CDN 加载
- [ ] 分享好友/朋友圈恢复 topic
- [ ] 不展示 paw-patrol/spider-verse
- [ ] 隐私政策页存在
- [ ] 真机 5 topic 通过
- [ ] 审核说明已备

---

## Codex 执行建议

**先交 Part A（A0-A3）**，不交 Part B 全量：

```
1. A0 channel-policy + validate-compliance + check-dist 按 channel 检查
2. A1 edgeone.json + build-static.sh + check-dist.mjs
3. A2 templates/ + site.config.json + generate-site-meta.mjs
4. A3 use-hash-route.ts 支持 ?topic + locale contract
```

Part A 完成后再决定 Part B 的 B2（抽 packages/kids-content）时机。B2 是 H5 和小程序的分水岭——一旦 shared package 抽出，两端共享数据层就确立了。

---

## 后续路线

| Phase | 内容 | 前置 |
|-------|------|------|
| 1 | Part A 上线（EdgeOne + CDN + 构建链） | 无 |
| 2 | Part B 上线（Taro 原生小程序） | Phase 1 + packages/kids-content |
| 3 | H5 体验优化（动画 + CSS + 响应式） | Phase 1 |
| 4 | 内容自动化（import.meta.glob + compile-content） | Phase 1 |
| 5 | 内容扩展（50+ topic） | Phase 4 |
| 6 | 产品化（家长模式 + 进度 + PWA + 云同步） | Phase 2 + 5 |
| 7 | H5 ↔ 小程序体验对齐 | Phase 2 + 3 |

**长期关系**：
- H5 是开发主体（React，快速迭代）
- 小程序通过 Taro 编译，共享 packages/kids-content
- 新 topic 只写一次（JSON + 组件逻辑），两端自动可用
- 样式各自适配（H5 px / 小程序 rpx）
