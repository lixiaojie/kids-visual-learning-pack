# Kids Visual Learning Pack — Spec v2.1

> 基于 2026-05-13 实际代码状态核对并更新。本文档可直接交给其他模型做架构校验和下阶段规划。

---

## 1. 项目定位

面向 5-8 岁儿童 + 家长共读的多主题视觉学习看板集合。每个看板从动画 IP 或知识领域出发，用"认知-互动-表达"三段式引导孩子理解世界。

**目标用户**：学龄前/低年级儿童（主体验者）+ 家长（共读引导者）
**核心体验**：看图认知 → 点击互动 → 口头复述/创作
**长期方向**：扩展到覆盖完整世界知识体系（50+ topic）

---

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 构建 | Vite 5，多入口（boards/* 各自独立） |
| UI | React 18 + TypeScript（kids-world、paw-patrol）；纯静态 HTML/CSS/JS（spider-verse） |
| 样式 | 手写 CSS + CSS 变量做 design token，单文件 `styles/styles.css`（946 行，未拆分） |
| 字体 | Google Fonts: Baloo 2（display）+ Noto Sans SC（body） |
| 图标 | Lucide React |
| 状态 | React hooks（useState/useEffect/useRef），无全局状态库 |
| 路由 | Hash-based `#topic/{slug}`（kids-world），Tab 切换（paw-patrol），锚点滚动（spider-verse） |
| 持久化 | localStorage（仅 paw-patrol 徽章） |
| i18n | 自研 deep merge（zh-CN base + en-US overlay），有锁字段校验 |
| 校验 | Ajv（JSON Schema draft 2020-12）+ 自研引用完整性脚本 |
| 部署 | Vercel（自动）+ 自有服务器（rsync）+ GitHub，相对路径 `base: "./"` |

---

## 3. 项目结构（当前实际）

```
/
├── index.html                         # 根入口，自动跳转 kids-world，含 favicon + og:image
├── shared/
│   ├── styles/home.css                # 根页面样式
│   └── icons/                         # favicon.ico, icon-*.png, apple-touch-icon.png, og-image.jpg
├── boards/
│   ├── kids-world/                    # 芋头世界（主入口，React）
│   │   ├── index.html                 # 含 favicon + og:image meta
│   │   ├── src/
│   │   │   ├── App.tsx                # 23 行，纯装配
│   │   │   ├── main.tsx
│   │   │   ├── types/                 # world.ts, topic.ts, assets.ts
│   │   │   ├── lib/                   # asset-resolve.ts, asset-map.ts, world-icons.ts
│   │   │   ├── hooks/                 # use-hash-route.ts
│   │   │   ├── data/
│   │   │   │   ├── loaders/           # locale-merge.ts, load-map.ts, load-topic.ts (12 topics)
│   │   │   │   ├── schema/            # topic.schema.json, i18n-overlay.schema.json
│   │   │   │   ├── topics/            # 12 个 topic JSON（render-ready）
│   │   │   │   ├── locales/en-US/     # 12 个 overlay JSON（锁字段已清理）
│   │   │   │   ├── exploration-map.json  # 7 世界 + 17 topic cards
│   │   │   │   ├── topic-registry.json  # 18 个 topic（12 ready + 6 planned）
│   │   │   │   └── image-generation-manifest.json  # 79 assets
│   │   │   ├── pages/                 # HomePage.tsx, TopicPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── shared/            # GeneratedImage, LocaleToggle, StatusPill, SectionHeader
│   │   │   │   ├── topic/             # 9 个 section 组件
│   │   │   │   ├── home/              # HeroSection, InterestBand, WorldGrid, WorldTopicPanel
│   │   │   │   └── layout/            # Topbar, PageShell
│   │   │   └── styles/styles.css      # 946 行（未拆分）
│   │   └── public/assets/             # 79 张 WebP（全部到位）
│   ├── paw-patrol/                    # 汪汪队（React，8 Tab，独立完整）
│   └── spider-verse/                  # 蛛网故事板（纯静态，10 section，独立完整）
├── scripts/
│   ├── validate-topics.mjs            # schema + 引用完整性
│   ├── validate-i18n.mjs              # overlay 锁字段守卫
│   ├── validate-assets.mjs            # 图片存在性检查
│   ├── check-image-assets.mjs         # PNG/WebP 配对（Vercel build 调用）
│   ├── build-vercel.sh                # Vercel 构建（含 check-image-assets）
│   ├── deploy.sh                      # 服务器部署（rsync，含 kids-world build）
│   ├── import-kids-world-image-prompts.mjs
│   └── import-kids-world-generated-images.mjs
└── docs/
    ├── spec-v2.md                     # 本文件
    ├── architecture-review-v1.md
    ├── 2026-05-11-kids-world-refactor-design.md
    └── 2026-05-11-kids-world-refactor-plan.md
```

---

## 4. Kids-World 详细 Spec

### 4.1 信息架构

**7 个世界**（1 动画入口 + 6 知识世界），**18 个 topic**（12 render-ready + 6 planned）：

| 世界 | 色值 | render-ready | planned |
|------|------|-------------|---------|
| 动画世界 | #8B5CF6 紫 | spider-verse, paw-patrol | — |
| 生命世界 | #22C55E 绿 | insects-and-spiders, animal-classification-tree, dinosaurs, ecosystem | — |
| 身体世界 | #EF4444 红 | blood-cells-3d, digestion | immune-system, heart |
| 地球世界 | #0EA5E9 蓝 | earth-climate-cities, water-cycle | volcano-earthquake |
| 宇宙世界 | #4F46E5 靛 | solar-system-overview, moon-phases | asteroid-belt |
| 物质与能量世界 | #F97316 橙 | — | （未注册） |
| 人造系统世界 | #06B6D4 青 | llm-kids-basics, robots | internet-message, search-engine-kids |

**exploration-map.json 当前 topic card 数量**：
- animation: 2 cards
- life: 5 cards
- body: 2 cards
- earth: 2 cards
- space: 2 cards
- energy: 2 cards
- humanMade: 2 cards

### 4.2 Topic 数据模型

每个 topic 是一个 `src/data/topics/{slug}.json`（10-16KB），遵循 `topic.schema.json`（JSON Schema draft 2020-12）。

核心字段：
```
slug, title, subtitle, world, priority, ageRange, pageType, coreQuestion,
learningGoals[], misconceptions[], hero{}, classificationGroups[],
representativeObjects[], mechanism{}, secondaryMechanism?,
comparePairs[], clickTasks[], speakTemplates[], parentTips[],
relatedTopics[], assets{}
```

**clickTask 三种类型**（schema 有条件必填规则）：
- `singleChoice` — 必填 options + correctOptionId
- `findTarget` — 必填 targetIds（可选 decoyIds）
- `sequenceClick` — 必填 options + correctSequence

### 4.3 Topic 页面模块（从上到下 11 个）

1. **TopicHero** — 场景大图 + PlaceholderScene + 核心问题 + 学习目标
2. **Scene Explanation** — 场景文字解读（内联在 TopicPage）
3. **ClassificationGroups** — 分类卡片 2 列，高亮联动
4. **RepresentativeObjects** — 实体卡片 4 列（受控组件，状态提升到 TopicPage）
5. **MechanismSteps** — 流程步骤 4 列 + 可选 secondaryMechanism
6. **ComparePairs** — A vs B 对比 3 列
7. **ClickTaskCard** — 互动任务 2 列（86 行，含三种 handler）
8. **SpeakTemplates** — 口头表达模板
9. **ParentTips** — 家长指导清单
10. **RelatedTopics** — 关联 topic 标签条

### 4.4 组件架构（33 个 TS/TSX 文件，23 行 App.tsx）

```
App (23 行: hash router + locale state + PageShell)
├── PageShell
│   └── Topbar (brand + mobile menu + topic nav + locale toggle)
├── HomePage (含 useRef + scrollIntoView)
│   ├── HeroSection (36 行)
│   ├── InterestBand (30 行, 动画世界)
│   ├── WorldGrid (42 行, 6 知识世界按钮)
│   └── WorldTopicPanel (44 行, forwardRef, 点击世界后 scrollIntoView)
└── TopicPage (含 activeObjectId 状态管理)
    ├── TopicHero (45 行, 含内部 PlaceholderScene)
    ├── ClassificationGroups (28 行, activeGroupId 受控)
    ├── RepresentativeObjects (41 行, activeObjectId + onSelectObject 受控)
    ├── MechanismSteps (39 行, 含 StepRow 内部组件)
    ├── ComparePairs (28 行)
    ├── ClickTaskCard (86 行)
    ├── SpeakTemplates (16 行)
    ├── ParentTips (16 行)
    └── RelatedTopics (18 行)
```

### 4.5 数据加载

```
data/loaders/
├── locale-merge.ts   — deepMerge(base, overlay)，数组按 id 匹配合并
├── load-map.ts       — getMap(locale): 加载 exploration-map + en-US overlay
└── load-topic.ts     — getTopic(slug, locale): 12 个 topic JSON 静态 import + merge
                        hasTopicData(slug): 判断是否有 topic 数据
                        当前 26 行 import（12 base + 12 en-US overlay）
```

新增 topic 只需：在 `load-topic.ts` 加 2 行 import + 2 行映射。

### 4.6 图片系统

- **Manifest**: `image-generation-manifest.json`（**79 个 asset**，全部 WebP 到位）
- **磁盘文件**: **79 张 WebP**，按 `{world}/{topic}/` 分目录存储
- **降级链**: GeneratedImage 组件 → manifest assetId → WebP path → null
- **命名**: `{world}-{topic}-{description}-v02.webp`
- **asset-map.ts**: `topicHeroAssetBySlug` 包含 12 个 slug → hero assetId 映射
- **生图词包**: V2.1（通用前缀/后缀 + 芋头兄弟识别系统），已覆盖全部 79 张
- **Topic assets 字段**: 已全部指向 v02 WebP 路径

### 4.7 i18n

- zh-CN 基础数据 + en-US overlay（deep merge by id）
- **12 对 topic 文件**（base + overlay 各 12 个）
- **锁字段守卫**（validate-i18n.mjs）：overlay 不允许包含 `type`, `correctOptionId`, `correctSequence`, `targetIds`, `decoyIds`
- overlay 中数组条目的 `id` 必须与 base 一致

### 4.8 导航行为

- hash 变化 → `scrollTo(0,0)`，页面从顶部开始
- 世界卡片点击 → `requestAnimationFrame` + `scrollIntoView({ behavior: "smooth", block: "start" })` 到 WorldTopicPanel
- planned topic 卡片 → `<div>` 不可点击（无 href）
- render-ready topic 卡片 → `<a href="#topic/{slug}">` 跳转

### 4.9 Favicon & OG Image

- **favicon**: `shared/icons/favicon.ico` + `icon-32.png` + `icon-192.png`
- **apple-touch-icon**: `shared/icons/apple-touch-icon.png`（180x180）
- **og:image**: `shared/icons/og-image.jpg`（1200x630，白底 logo 居中）
- **og:image URL**: 绝对路径 `https://118.145.242.99/kids/shared/icons/og-image.jpg`（微信爬虫需要）
- 所有 4 个 HTML 文件均已配置

---

## 5. Paw-Patrol Spec（独立完整，无变更）

React + TypeScript，8 Tab，5 实体类型（Character/Mission/Badge/Location/GearItem），MissionGame 核心交互（best/helpful/try-again），localStorage 徽章持久化。803 行组件 + 358 行数据。

---

## 6. Spider-Verse Spec（独立完整，无变更）

纯静态 HTML/CSS/JS，10 section + 附录，549 行 script.js，50+ WebP 素材，IntersectionObserver 滚动进入，story modal，儿童/家长模式切换，A4 打印。

---

## 7. 校验体系（已落地）

```bash
npm run validate          # 三项全跑
npm run validate:topics   # schema + 引用完整性（groupId/correctOptionId/relatedTopics/slug 一致性）
npm run validate:i18n     # overlay 锁字段守卫 + id 匹配
npm run validate:assets   # manifest 图片 + topic assets 路径存在性
```

当前状态（2026-05-13 验证）：
- **validate:topics**: 12 files checked, 0 errors
- **validate:i18n**: 12 overlays checked, 0 errors
- **validate:assets**: 135 assets checked, 0 missing

---

## 8. 部署

| 渠道 | 方式 | 地址 |
|------|------|------|
| Vercel | `npm run build`（build-vercel.sh）→ 自动部署 | vercel 域名 |
| 自有服务器 | `bash scripts/deploy.sh`（build kids-world + paw-patrol → rsync） | https://118.145.242.99/kids/ |
| GitHub | `git push origin main` | github.com/lixiaojie/kids-visual-learning-pack |

build-vercel.sh 流程：check-image-assets → clean dist → build paw-patrol → build kids-world → copy root + shared + spider-verse → remove PNG from dist。

deploy.sh 流程：build kids-world → build paw-patrol → rsync 5 部分（root entry + shared + kids-world dist + spider-verse static + paw-patrol dist）。

---

## 9. 已完成清单

| 时间 | 项目 | 状态 |
|------|------|------|
| 2026-05-11 | App.tsx 重构 799→23 行 | Done，33 个 TS/TSX，17 个目录 |
| 2026-05-11 | 校验脚本三件套 | Done，Ajv + 引用完整性 + 资产存在性 |
| 2026-05-11 | i18n overlay 锁字段清理 | Done，55 个违规已修 |
| 2026-05-11 | topic-registry 补 12 个 planned topic | Done |
| 2026-05-11 | asset 路径 v01→v02 修正 | Done，20 个路径 |
| 2026-05-11 | 导航 UX（scrollTo + scrollIntoView + div fallback） | Done |
| 2026-05-11 | Vercel 构建修复 | Done |
| 2026-05-12 | 新增 6 个 topic（digestion/dinosaurs/ecosystem/moon-phases/robots/water-cycle） | Done，12→18 registry，79 assets |
| 2026-05-12 | Favicon + OG image（浏览器 tab + 微信分享） | Done |
| 2026-05-12 | 部署（服务器 + GitHub + Vercel） | Done |

---

## 10. 待做（按优先级）

### P0：体验质量

| 任务 | 说明 |
|------|------|
| **CSS 拆分** | styles.css 946 行 → tokens.css / layout.css / home.css / topic.css / interactions.css |
| **响应式 QA** | 375/768/1280 三宽度验收，修复移动端排版问题 |
| **页面过渡动画** | topic 切换 fade/slide，homepage 卡片 stagger 入场 |
| **互动反馈动画** | ClickTask 正确/错误动效，mechanism step 进度动画 |

### P1：内容扩展（剩余 6 个 planned topic）

| slug | 世界 | 说明 |
|------|------|------|
| `immune-system` | body | 免疫系统，与 blood-cells-3d 配合 |
| `heart` | body | 心脏与循环 |
| `volcano-earthquake` | earth | 地质活动 |
| `asteroid-belt` | space | 小行星带深入 |
| `internet-message` | humanMade | 网络通信原理 |
| `search-engine-kids` | humanMade | 搜索引擎 |

### P2：物质与能量世界启动

energy 世界当前 status=comingSoon，无 render-ready topic。建议首批：
- `light-and-color` — 光与颜色
- `fission-fusion-kids` — 核裂变/聚变儿童版

### P3：工程化

| 任务 | 说明 |
|------|------|
| shared 组件层收敛 | 提取跨 board 复用的 CSS tokens 和组件 |
| spider-verse React 迁移评估 | 先抽 shared 能力再决定 |
| 测试覆盖 | structure test + 交互 test |
| PWA | Service Worker + 离线缓存 |
| CDN | 图片上 CDN，减轻服务器带宽 |

---

## 11. 给续写模型的 Checklist

用这个 checklist 验证对当前实现的理解：

- [x] 根 index.html 自动跳转到 boards/kids-world/，含 favicon + og:image
- [x] App.tsx 23 行，纯装配（router + locale + PageShell）
- [x] 7 个世界，**12 个 render-ready topic**，6 个 planned topic
- [x] topic 页面 11 个模块（hero → related strip），每个是独立组件文件
- [x] RepresentativeObjects 是受控组件（activeObjectId + onSelectObject 从 TopicPage 传入）
- [x] ClassificationGroups 的 activeGroupId 由 TopicPage 的 activeObject.groupId 驱动
- [x] clickTask 有 3 种类型（singleChoice/findTarget/sequenceClick）
- [x] i18n overlay 有锁字段守卫（type/correctOptionId/etc 不允许出现）
- [x] **79 张 WebP** 图片全部到位，**135 个 asset 引用**全部通过校验
- [x] hash 变化时 scrollTo(0,0)
- [x] 世界卡片点击 scrollIntoView 到 topic panel
- [x] planned topic 卡片用 `<div>` 不可点击
- [x] `npm run validate` 三项全绿（12 topics + 12 overlays + 135 assets）
- [x] 新增 topic 只需：load-topic.ts 加 import + topic JSON + overlay + 图片 + manifest + asset-map
- [x] favicon + og:image 配置在所有 4 个 HTML 中
- [x] og:image 使用绝对 URL（微信分享兼容）

---

## 12. 新 topic 生产模板

给续写模型的快速参考——新增一个 topic 需要做什么：

```bash
# 1. 创建 topic JSON
# 放入 boards/kids-world/src/data/topics/{slug}.json
# 遵循 data/schema/topic.schema.json（约 15KB，含 hero/groups/objects/mechanism/compare/tasks/tips）

# 2. 创建 en-US overlay
# 放入 boards/kids-world/src/data/locales/en-US/topics/{slug}.json
# 只翻译文案字段，不包含 type/correctOptionId/targetIds/correctSequence/decoyIds

# 3. 更新 load-topic.ts
# 加 2 行 import（base + en）+ 2 行映射到 topicBaseBySlug/topicEnBySlug

# 4. 更新 topic-registry.json
# 把对应 slug 的 status 从 planned 改为 render-ready

# 5. 生成图片（用 V2.1 词包模板：通用前缀 + 单图正文 + 通用后缀）
# 每个 topic 需要 4-6 张：hero + object-icons + mechanism + compare + click-task + parent-guide
# 生成后放入 boards/kids-world/public/assets/{world}/{slug}/
# 命名：{world}-{slug}-{description}-v02.webp
# 更新 image-generation-manifest.json（加 asset 条目，含 assetId/webpPath/pngPath）

# 6. 更新 asset-map.ts
# topicHeroAssetBySlug 加一行："{slug}": "{assetId-of-hero}"

# 7. 更新 exploration-map.json（如果 topic 不在 topicCards 里）
# 在对应 world 的 topicCards 数组加一条

# 8. 更新 topic JSON 的 assets 字段
# 把 hero/compare/cards 等 key 的 path 指向实际 WebP 路径

# 9. 校验
npm run validate  # 必须全绿

# 10. 浏览器验证
# dev server 上检查：首页世界列表显示 + 点击进入 TopicPage + 11 个模块正常渲染
```
