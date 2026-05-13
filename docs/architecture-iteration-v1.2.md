# 芋头宇宙 — 架构迭代 Spec v1.2

> 生成日期：2026-05-13
> 基线文档：`spec-v2.md`（2026-05-13 核对，12 render-ready topic，79 WebP，validate 全绿）
> v1.2 变更：修正 v1.1 评审问题 + 拆分为 Part A（H5 迭代）和 Part B（小程序）两条独立可执行线

---

## 0. 版本结论与拆分策略

**两条线独立推进，互不阻塞**：

```
Part A: H5 迭代（EdgeOne 部署 + 构建链 + 体验优化）
  → 不依赖小程序主体审批
  → 可立即开始

Part B: 小程序版本（web-view 壳 + 合规 + 分享）
  → 阻断于主体类型确认（个人主体不支持 web-view）
  → 主体确认后才启动 Task 实施
```

**为什么拆开**：
1. 小程序主体审批/ICP 备案可能需要 2-4 周，H5 迭代不应等待
2. Part A 的产出（EdgeOne 稳定站点 + 干净 URL + 构建链）是 Part B 的前置依赖
3. 即使小程序方案最终不走 web-view（个人主体限制），Part A 产出仍有独立价值

---

## 1. 当前事实基线（2026-05-13 验证）

### 1.1 产品与内容

| 项目 | 数据 |
|------|------|
| 世界数量 | 7 个（1 动画入口 + 6 知识世界） |
| exploration-map worlds | 7 条（animation + life/body/earth/space/energy/humanMade） |
| topic-registry topics | 18 个（12 render-ready + 6 planned） |
| 知识世界 topic 分布 | life 4, body 2, earth 2, space 2, humanMade 2（registry 的 world 字段覆盖 6 个知识世界） |
| 图片资产 | 79 张 WebP，135 个 asset 引用通过校验 |
| 校验状态 | `npm run validate` 三项全绿 |

### 1.2 技术栈

| 层 | 当前实现 |
|---|---|
| 构建 | Vite 5，多入口 |
| UI | React 18 + TypeScript（kids-world 33 文件 + paw-patrol 19 文件）；spider-verse 纯静态 |
| App.tsx | 23 行，纯装配 |
| 路由 | hash route `#topic/{slug}`（kids-world） |
| i18n | zh-CN base + en-US overlay，锁字段守卫 |
| 校验 | Ajv（devDependency）+ 3 个 validate 脚本 |
| 部署 | Vercel（build-vercel.sh）+ 自有服务器 rsync + GitHub |

### 1.3 部署现状

| 渠道 | 状态 |
|------|------|
| GitHub | `origin git@github.com:lixiaojie/kids-visual-learning-pack.git` |
| EdgeOne | **控制台已关联 GitHub repo，代码侧 `edgeone.json` 待补** |
| Vercel | `build-vercel.sh` 可用，`vercel.json` 存在 |
| 自有服务器 | `deploy.sh` rsync 到 118.145.242.99 |
| 小程序 | **无任何代码**，认证申请已提交，主体类型待确认 |

### 1.4 必须纠正的架构债

| 问题 | 风险 | 归属 |
|------|------|------|
| 4 个 HTML 硬编码 `118.145.242.99` og:image | 微信分享/品牌可信度 | Part A |
| 构建链未强制 validate | 部署成功≠内容引用正确 | Part A |
| 无 `edgeone.json` | EdgeOne 配置不可复现 | Part A |
| paw-patrol/spider-verse 有 IP 指向 | 版权/审核风险 | Part B |
| 无 legal 页面 | 小程序审核阻断 | Part B |
| 小程序主体类型未确认 | web-view 方案可能不可行 | Part B Gate |

---

## Part A: H5 迭代

> 目标：让 EdgeOne 成为稳定主站，构建链收敛，IP 清理，体验优化。不依赖小程序审批。

### A.1 优先级

```
A1. EdgeOne 配置文件化 + 构建链收敛
A2. site.config + HTML meta 注入 + IP 清理
A3. 路由增强（支持 ?topic=slug）
A4. CSS 拆分 + 响应式修复
A5. 页面过渡动画 + 互动反馈
A6. 内容扩展（剩余 6 planned topic）
```

### A.2 Task A1: EdgeOne 配置 + 构建链

**产出**：
- `edgeone.json`（根目录）
- `scripts/build-static.sh`（统一构建入口）
- `scripts/check-dist.mjs`（构建产物校验）
- `build-vercel.sh` 改为代理 `build-static.sh`

**edgeone.json**：

```json
{
  "name": "yutou-verse",
  "installCommand": "npm ci",
  "buildCommand": "npm run build:edgeone",
  "outputDirectory": "./dist",
  "nodeVersion": "20.18.0",
  "headers": [
    {
      "source": "/**/*.html",
      "headers": [{ "key": "Cache-Control", "value": "no-cache, must-revalidate" }]
    },
    {
      "source": "/boards/*/assets/**",
      "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]
    },
    {
      "source": "/shared/icons/**",
      "headers": [{ "key": "Cache-Control", "value": "public, max-age=86400" }]
    },
    {
      "source": "/**",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

注意：
- 不设 `X-Frame-Options: DENY`（预留 web-view 兼容）
- 不设 CSP `frame-ancestors`（同上）
- `/boards/*/assets/**` 长缓存覆盖 hashed JS/CSS（Vite 产物带 hash 在 assets/ 下）
- `/**/*.html` 匹配所有 HTML 保持新鲜
- EdgeOne 规则优先级：最具体路径优先（需 preview 验证）

**build-static.sh**：

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> validate"
npm run validate

echo "==> clean dist"
rm -rf dist && mkdir -p dist/boards

echo "==> generate site meta"
npm run generate:site-meta

echo "==> build kids-world"
npx vite build boards/kids-world --base=./ --emptyOutDir --outDir ../../dist/boards/kids-world

echo "==> build paw-patrol"
npx vite build boards/paw-patrol --base=./ --emptyOutDir --outDir ../../dist/boards/paw-patrol

echo "==> copy root + shared + spider-verse"
cp dist-ready/index.html dist/
cp -r shared dist/
cp -r boards/spider-verse dist/boards/
find dist/boards/spider-verse \( -name '*.test.*' -o -name '*.spec.*' -o -name '.DS_Store' \) -delete

echo "==> copy legal + verification (if exists)"
[ -d legal ] && cp -r legal dist/
cp public-verification/MP_verify_*.txt dist/ 2>/dev/null || true

echo "==> remove source PNG"
find dist/boards -path '*/assets/*.png' -delete

echo "==> check-dist"
npm run check:dist

echo "==> done"
```

**check-dist.mjs 必检项**：

```
1. dist/index.html 存在
2. dist/boards/kids-world/index.html 存在
3. dist/shared/icons/favicon.ico 存在
4. dist 中不存在 118.145.242.99
5. dist 中不存在未替换的 __SITE_URL__ / __OG_IMAGE__
6. dist 中不存在 localhost / 127.0.0.1
```

**package.json 脚本更新**：

```json
{
  "build": "npm run build:static",
  "build:static": "bash scripts/build-static.sh",
  "build:edgeone": "npm run build:static",
  "check:dist": "node scripts/check-dist.mjs",
  "generate:site-meta": "node scripts/generate-site-meta.mjs"
}
```

**验收**：
- EdgeOne preview 部署成功
- Response headers 符合预期（用 curl 验证）
- 微信开发者工具 web-view 能加载 preview URL（无 X-Frame-Options / CSP 阻断）

**环境变量注意**：EdgeOne `npm ci` 时确认 NODE_ENV 不是 production（否则 devDeps 含 ajv 不会安装，validate 脚本 fail）。如果 EdgeOne 强制 production，需把 ajv 移到 dependencies。

---

### A.3 Task A2: site.config + HTML meta 注入

**产出**：
- `site.config.json`
- `scripts/generate-site-meta.mjs`
- 4 个 HTML 改为占位符模板 → 构建时注入

**site.config.json**：

```json
{
  "siteName": "芋头宇宙",
  "siteUrl": "https://kids.yutou-verse.cn",
  "defaultTitle": "芋头宇宙｜儿童认知可视化学习地图",
  "defaultDescription": "面向孩子和家长共读的可视化认知学习地图。",
  "ogImage": "/shared/icons/og-image.jpg",
  "favicon": "/shared/icons/favicon.ico"
}
```

**注入逻辑**：
1. 读 `site.config.json` + 环境变量 `SITE_URL` 覆盖
2. 扫描源 HTML（非 dist），生成 `dist-ready/` 中间产物
3. 替换 `__SITE_URL__` / `__SITE_TITLE__` / `__SITE_DESCRIPTION__` / `__OG_IMAGE__`
4. build-static.sh 从 `dist-ready/index.html` 拷贝（而非源 index.html）

**特殊处理**：spider-verse 的 `index.html` 是纯静态非模板——`generate-site-meta.mjs` 需要直接 sed 替换 `118.145.242.99` → `${siteUrl}`，不用占位符。

**IP 清理规则**（生产构建禁止出现）：
```
118.145.242.99
http://（非 https）
localhost
127.0.0.1
```

---

### A.4 Task A3: 路由增强

**需求**：H5 支持 `?topic=slug&locale=zh-CN`，为小程序 web-view 做准备。

**实现**：修改 `boards/kids-world/src/hooks/use-hash-route.ts`：

```typescript
import { useEffect, useState } from "react";

export function useHashRoute() {
  const [slug, setSlug] = useState<string | null>(() => resolveSlug());

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

function resolveSlug(): string | null {
  // 优先级：?topic > #topic/{slug} > null (home)
  const params = new URLSearchParams(window.location.search);
  const queryTopic = params.get("topic");
  if (queryTopic) return queryTopic;

  const hashMatch = window.location.hash.match(/^#topic\/(.+)$/);
  return hashMatch?.[1] ?? null;
}
```

**验收**：
- `?topic=dinosaurs` → 打开恐龙 topic
- `#topic/dinosaurs` → 打开恐龙 topic（兼容）
- `?topic=nonexistent` → 首页 + 轻提示
- 无参数 → 首页

---

### A.5 Task A4-A5: 体验优化

（与 v1.1 spec 一致，略。CSS 拆分 + 响应式 + 动画，延后不阻塞发布。）

---

### A.6 Task A6: 内容扩展

剩余 6 个 planned topic：immune-system, heart, volcano-earthquake, asteroid-belt, internet-message, search-engine-kids。

按 spec-v2.1 Section 12 的生产模板执行。

---

### A.7 部署环境矩阵

| 环境 | 分支 | 域名 | 用途 |
|------|------|------|------|
| production | `main` | `https://kids.yutou-verse.cn`（ICP 备案后） | 正式站 |
| preview | `develop` | EdgeOne preview URL | 内测验收 |
| 自有服务器 | `main` | `https://118.145.242.99/kids/` | 过渡期 + 备用 |

**ICP 并行策略**：域名未备案期间，先用 EdgeOne 默认域名（非自定义）跑通全链路。备案通过后切换自定义域名，再配置到小程序业务域名。

---

## Part B: 微信小程序（Taro 原生方案）

> 目标：用 Taro（React 语法）开发原生小程序，复用现有组件逻辑和数据层。
> **背景**：个人主体不支持 web-view，必须走原生开发。Taro 选型核心收益：70-80% 代码可复用。
> **硬性前置**：Part A 的 A1-A2 完成（数据层 + 图片 CDN 可用）。

### B.0 技术选型：为什么 Taro

| 维度 | 微信原生 | Taro (React) | 选择 |
|------|---------|-------------|------|
| 复用现有 React 代码 | 0% | 70-80% | **Taro** |
| TypeScript 类型系统 | 全部重写 | 直接用 | **Taro** |
| topic JSON + loaders | 需适配 require | 直接 import | **Taro** |
| 组件逻辑 | 全部重写 | 改标签名即可 | **Taro** |
| 审核友好度 | 最高 | 高（编译产物=标准小程序） | 均可 |
| Runtime 开销 | 0 | ~50KB | 可接受 |
| 跨端能力 | 仅微信 | 微信/H5/支付宝 | **Taro** |

### B.1 代码复用策略

**可直接复用（零改动）**：

| 模块 | 文件 | 说明 |
|------|------|------|
| types/ | world.ts, topic.ts, assets.ts | TypeScript 类型定义 |
| data/ | 全部 topic JSON + overlay + registry + manifest | 数据层 |
| data/loaders/ | locale-merge.ts, load-map.ts, load-topic.ts | 数据加载逻辑 |
| data/schema/ | topic.schema.json, i18n-overlay.schema.json | 校验 schema |
| lib/ | asset-map.ts（映射表） | 图片 assetId 查找 |

**需适配（改标签名 + 样式单位）**：

| 模块 | 改动内容 |
|------|---------|
| components/topic/ | `<div>` → `<View>`，`<span>` → `<Text>`，`<img>` → `<Image>` |
| components/home/ | 同上 + 路由从 hash 改为 Taro.navigateTo |
| components/shared/ | GeneratedImage 改为 `<Image>` + CDN URL |
| styles/ | px → rpx，移除不支持的 CSS（CSS 变量可用） |

**需重写**：

| 模块 | 原因 |
|------|------|
| 路由 | Taro 页面路由替代 hash route |
| App.tsx | Taro app 入口格式不同 |
| styles.css | 小程序 CSS 子集 + rpx 适配 |
| 图片加载 | CDN URL + `<Image>` mode 属性 |

### B.2 项目结构

```
apps/miniprogram/
├── project.config.json
├── src/
│   ├── app.ts                    # Taro 入口
│   ├── app.config.ts             # 页面路由配置
│   ├── app.scss
│   │
│   ├── shared/                   # 从 H5 项目 symlink 或 copy
│   │   ├── types/                # → boards/kids-world/src/types/
│   │   ├── data/                 # → boards/kids-world/src/data/
│   │   └── lib/                  # → boards/kids-world/src/lib/ (asset-map)
│   │
│   ├── components/               # 适配后的小程序组件
│   │   ├── topic/
│   │   │   ├── TopicHero.tsx
│   │   │   ├── ClassificationGroups.tsx
│   │   │   ├── RepresentativeObjects.tsx
│   │   │   ├── MechanismSteps.tsx
│   │   │   ├── ComparePairs.tsx
│   │   │   ├── ClickTaskCard.tsx
│   │   │   ├── SpeakTemplates.tsx
│   │   │   ├── ParentTips.tsx
│   │   │   └── RelatedTopics.tsx
│   │   ├── home/
│   │   │   ├── WorldGrid.tsx
│   │   │   └── WorldTopicPanel.tsx
│   │   └── shared/
│   │       ├── GeneratedImage.tsx  # <Image src={cdnUrl} mode="aspectFill" />
│   │       ├── StatusPill.tsx
│   │       └── SectionHeader.tsx
│   │
│   ├── pages/
│   │   ├── index/                # 首页：世界入口 + 推荐 topic
│   │   │   ├── index.tsx
│   │   │   ├── index.config.ts
│   │   │   └── index.scss
│   │   ├── topic/                # Topic 详情页
│   │   │   ├── index.tsx
│   │   │   ├── index.config.ts
│   │   │   └── index.scss
│   │   └── about/                # 家长说明 + 隐私政策
│   │       ├── index.tsx
│   │       └── index.config.ts
│   │
│   └── styles/
│       ├── tokens.scss           # CSS 变量 + rpx
│       └── components.scss       # 组件公共样式
│
├── config/
│   ├── index.ts                  # Taro 编译配置
│   └── prod.ts
├── package.json
└── tsconfig.json
```

### B.3 数据共享方案

**推荐 monorepo 结构**（让 H5 和小程序共享 types + data + lib）：

```
kids-visual-learning-pack/          # 项目根（现有）
├── boards/kids-world/              # H5 版本（现有）
├── apps/miniprogram/               # 小程序版本（新增）
└── packages/shared/                # 共享层（新增，从 kids-world 抽出）
    ├── types/
    ├── data/
    └── lib/
```

或者更简单的首版方案：**直接在 Taro 项目中 import 相对路径**：

```typescript
// apps/miniprogram/src/pages/topic/index.tsx
import { getTopic } from "../../../boards/kids-world/src/data/loaders/load-topic";
import type { Topic } from "../../../boards/kids-world/src/types/topic";
```

首版用相对路径，验证跑通后再抽 packages/shared。

### B.4 图片策略

小程序不能直接读 `public/assets/` 目录。两种方案：

| 方案 | 说明 | 推荐 |
|------|------|------|
| CDN | 图片上传到 EdgeOne / 腾讯云 COS，小程序用 HTTPS URL | **首版推荐** |
| 本地打包 | WebP 放入小程序包（但 2MB 限制） | 不可行（79 张图远超 2MB） |

**CDN 策略**：
- 图片已在 EdgeOne 站点 `https://kids.yutou-verse.cn/boards/kids-world/assets/`
- 小程序 GeneratedImage 组件直接拼 CDN URL：

```tsx
// apps/miniprogram/src/components/shared/GeneratedImage.tsx
import { Image } from "@tarojs/components";

const CDN_BASE = "https://kids.yutou-verse.cn/boards/kids-world/assets";

export function GeneratedImage({ assetPath, className }: { assetPath?: string; className?: string }) {
  if (!assetPath) return null;
  const src = `${CDN_BASE}${assetPath}`;
  return <Image src={src} mode="aspectFill" className={className} />;
}
```

**前置依赖**：Part A 完成后 EdgeOne 站点稳定，图片 URL 可用。

### B.5 路由设计

| 小程序页面 | 路径 | 对应 H5 |
|-----------|------|---------|
| 首页 | `/pages/index/index` | HomePage |
| Topic 详情 | `/pages/topic/index?slug=dinosaurs&locale=zh-CN` | TopicPage |
| 家长说明 | `/pages/about/index` | — |

**页面跳转**：

```tsx
// 从首页进入 topic
Taro.navigateTo({ url: `/pages/topic/index?slug=${topic.slug}&locale=${locale}` });
```

**分享恢复**：

```tsx
// pages/topic/index.tsx
import Taro, { useRouter } from "@tarojs/taro";

export default function TopicPage() {
  const router = useRouter();
  const slug = router.params.slug || "dinosaurs";
  const locale = router.params.locale || "zh-CN";
  const topic = getTopic(slug, locale);
  // ...
}
```

### B.6 优先级

```
B1. 合规清单 + 隐私政策
B2. Taro 项目初始化 + 数据层接入
B3. 首页（世界入口 + topic 推荐）
B4. Topic 详情页（11 个模块逐个适配）
B5. 互动任务（ClickTaskCard 适配）
B6. 分享功能
B7. 真机 QA
B8. 提审发布
```

### B.7 Task B1: 合规清单

**产出**：
- `docs/compliance/wechat-miniprogram-checklist.md`
- `docs/compliance/content-ip-risk-register.md`
- 隐私政策/用户协议页面（小程序内原生页面，不需要域名）

**channel-policy.json**（唯一的渠道可见性配置）：

```json
{
  "miniprogram": {
    "visibleTopics": [
      "dinosaurs", "ecosystem", "animal-classification-tree",
      "insects-and-spiders", "solar-system-overview", "moon-phases",
      "water-cycle", "earth-climate-cities", "robots",
      "llm-kids-basics", "digestion", "blood-cells-3d"
    ],
    "hiddenBoards": ["paw-patrol", "spider-verse"]
  },
  "web": {
    "visibleBoards": ["kids-world"],
    "hiddenBoards": ["paw-patrol", "spider-verse"]
  }
}
```

**隐私政策**（原生小程序不需要域名托管 legal 页面，直接在小程序内展示）：

| 条款 | 首版 |
|------|------|
| 收集儿童信息 | 不收集 |
| 登录 | 不登录 |
| 学习进度 | Taro.setStorageSync 本地，可清除 |
| 第三方统计 | 首版不接 |
| 网络请求 | 仅加载 CDN 图片 |

### B.8 Task B2: Taro 项目初始化

```bash
# 在项目根目录
npx @tarojs/cli init apps/miniprogram --template react-ts

# 安装后配置 tsconfig paths 指向 shared 数据层
```

**config/index.ts 关键配置**：

```typescript
export default {
  projectName: "yutou-verse-miniprogram",
  designWidth: 750,
  deviceRatio: { 750: 1 },
  sourceRoot: "src",
  outputRoot: "dist",
  plugins: [],
  framework: "react",
  compiler: "webpack5",
  mini: {
    postcss: {
      pxtransform: { enable: true, config: { designWidth: 750 } }
    }
  },
  alias: {
    "@shared": "../../boards/kids-world/src"
  }
};
```

### B.9 Task B3-B4: 首页 + Topic 页

**首页** `/pages/index/index.tsx`：

```tsx
import { View, Text, Image } from "@tarojs/components";
import Taro from "@tarojs/taro";
import { getMap } from "@shared/data/loaders/load-map";

export default function IndexPage() {
  const map = getMap("zh-CN");
  const knowledgeWorlds = map.worlds.filter(w => w.id !== "animation");

  function goTopic(slug: string) {
    Taro.navigateTo({ url: `/pages/topic/index?slug=${slug}` });
  }

  return (
    <View className="home">
      <View className="hero">
        <Image src="...logo..." className="logo" />
        <Text className="title">{map.homeHero.title}</Text>
      </View>
      <View className="world-grid">
        {knowledgeWorlds.map(world => (
          <View key={world.id} className="world-card">
            <Text>{world.name}</Text>
            {world.topicCards.filter(t => t.status === "render-ready").map(topic => (
              <View key={topic.slug} className="topic-entry" onClick={() => goTopic(topic.slug!)}>
                <Text>{topic.title}</Text>
              </View>
            ))}
          </View>
        ))}
      </View>
    </View>
  );
}
```

**Topic 页**：复用 TopicPage 结构，逐个适配 11 个模块组件（`<div>` → `<View>`）。

### B.10 Task B5: ClickTaskCard 适配

ClickTaskCard 逻辑（86 行）可完整复用，只改标签：

```tsx
// 原 H5
<div className={`task-card ${result}`}>
  <button onClick={() => handleClick(option.id)}>{option.label}</button>
</div>

// Taro 小程序
<View className={`task-card ${result}`}>
  <View className="task-option" onClick={() => handleClick(option.id)}>
    <Text>{option.label}</Text>
  </View>
</View>
```

### B.11 Task B6: 分享

```tsx
// pages/topic/index.tsx
import Taro, { useShareAppMessage, useShareTimeline } from "@tarojs/taro";

useShareAppMessage(() => ({
  title: `芋头宇宙｜${topic.title}`,
  path: `/pages/topic/index?slug=${slug}&locale=${locale}`,
  imageUrl: `${CDN_BASE}/shared/icons/og-image.jpg`
}));

useShareTimeline(() => ({
  title: `芋头宇宙｜${topic.title}`,
  query: `slug=${slug}&locale=${locale}`,
  imageUrl: `${CDN_BASE}/shared/icons/og-image.jpg`
}));
```

### B.12 Task B7: 真机 QA

**设备矩阵**：

| 维度 | 必测 |
|------|------|
| iOS 微信 | iPhone 小屏 + 刘海屏 |
| Android 微信 | 主流国产 + 中低端 |

**小程序专项**：

| 场景 | 验收 |
|------|------|
| 首次加载 | 不白屏，图片 CDN 加载正常 |
| 低网速 | Image placeholder / loading 态 |
| 分享好友 | path 恢复 topic |
| 分享朋友圈 | query 恢复 topic |
| 返回栈 | topic → 首页 正常 |
| safe-area | 顶部/底部不被遮挡 |
| 微信字体放大 | 卡片不重叠 |

**必测 topic**：dinosaurs、water-cycle、llm-kids-basics、solar-system-overview、digestion

### B.13 Task B8: 提审发布

**审核说明文案**：

```
本小程序为儿童科普认知学习工具，面向 5-8 岁儿童与家长共读使用。
首版内容包括恐龙、太阳系、月相、水循环、机器人、身体消化等通用科普主题。
小程序不提供用户登录、不收集儿童个人信息、不提供用户上传内容、不涉及支付。
所有内容为自有原创视觉素材和通用科普知识表达。
首版仅开放原创科普内容，不包含第三方动画、影视、游戏角色或商标内容。
```

**发布流程**：

```
开发 → 真机预览 → 体验版 → 审核 → 发布
```

**回滚**：

| 场景 | 处理 |
|------|------|
| 小程序崩溃 | 微信后台回退上一线上版本 |
| 版权风险 | 更新 channel-policy → 重新编译 → 提审 |
| 图片 CDN 异常 | 检查 EdgeOne 状态，必要时切备用 CDN |

---

## 上线前总 Checklist

### Part A 完成标准

- [ ] `edgeone.json` 已提交并生效
- [ ] `npm run build:edgeone` 本地通过
- [ ] `npm run check:dist` 通过
- [ ] dist 中无 IP / 无占位符 / 无 localhost
- [ ] EdgeOne preview 可访问
- [ ] `?topic=slug` 路由工作
- [ ] `#topic/slug` 兼容
- [ ] production 域名 HTTPS 正常（备案后）
- [ ] 图片 CDN URL 稳定可访问（小程序依赖）

### Part B 完成标准（Taro 原生小程序）

- [ ] Taro 项目编译通过，微信开发者工具可预览
- [ ] 共享数据层（types + data + lib）正确 import
- [ ] 首页展示世界入口 + 推荐 topic
- [ ] Topic 详情页 11 个模块正常渲染
- [ ] ClickTaskCard 三种互动类型工作
- [ ] 图片通过 CDN URL 加载
- [ ] 分享好友/朋友圈恢复 topic
- [ ] 小程序首版不展示 paw-patrol/spider-verse
- [ ] 隐私政策页面存在
- [ ] 真机 QA 5 个 topic 通过
- [ ] 审核说明已准备

---

## Codex 任务包

### Part A 任务（可立即执行）

| Task | 名称 | 依赖 | 说明 |
|------|------|------|------|
| A1 | EdgeOne 配置 + 构建链 | 无 | edgeone.json + build-static.sh + check-dist.mjs |
| A2 | site.config + meta 注入 | A1 | site.config.json + generate-site-meta.mjs + IP 清理 |
| A3 | 路由增强 | 无 | use-hash-route.ts 支持 ?topic + 未知 topic 回退 |

A1-A3 完成后：Part A 上线可用，图片 CDN 稳定可用。A4-A6 为体验和内容迭代，持续推进。

### Part B 任务（Taro 原生小程序）

| Task | 名称 | 依赖 | 说明 |
|------|------|------|------|
| B1 | 合规清单 | 无 | channel-policy.json + 隐私政策 + IP 风险登记 |
| B2 | Taro 项目初始化 + 数据层接入 | Part A done（图片 CDN 可用） | apps/miniprogram + alias 指向 shared 数据 |
| B3 | 首页开发 | B2 | 世界入口 + topic 推荐 + 家长说明 |
| B4 | Topic 详情页 | B2 | 11 个模块组件逐个适配（View/Text/Image） |
| B5 | ClickTaskCard 适配 | B4 | 三种互动任务在小程序中工作 |
| B6 | 分享功能 | B4 | useShareAppMessage + useShareTimeline |
| B7 | 真机 QA | B3-B6 | 设备矩阵验收 |
| B8 | 提审发布 | B7 | 审核说明 + 发布 |

B4 是工作量最大的 task（9 个组件适配），可拆为子任务按组件逐个推进。

---

## 后续阶段路线

| Phase | 内容 | 前置 |
|-------|------|------|
| Phase 1 | Part A 上线（EdgeOne 稳定站 + 图片 CDN） | 无 |
| Phase 2 | Part B 上线（Taro 原生小程序首版） | Phase 1（图片 CDN 依赖） |
| Phase 3 | H5 体验优化（动画 + CSS 拆分 + 响应式） | Phase 1 |
| Phase 4 | 内容自动化（import.meta.glob + compile-content） | Phase 1 |
| Phase 5 | 内容扩展（50+ topic） | Phase 4 |
| Phase 6 | 产品化（家长模式 + 进度 + PWA + 云同步） | Phase 2 + Phase 5 |
| Phase 7 | H5 ↔ 小程序体验对齐 | Phase 2 + Phase 3 |

**H5 与小程序的长期关系**：
- H5 是开发主体（React 生态，快速迭代）
- 小程序通过 Taro 编译产出，共享数据层和组件逻辑
- 新 topic 只需写一次（topic JSON + 组件），两端自动可用
- 样式层各自适配（H5 用 CSS px，小程序用 rpx）
