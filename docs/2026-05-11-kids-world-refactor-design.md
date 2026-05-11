# Kids-World App.tsx 搬家式重构 — Design Spec

> 2026-05-11。Phase 1 of architecture-review-v1.md。

## 目标

将 `boards/kids-world/src/App.tsx`（799 行）拆分为按职责分目录的文件结构，为后续 50+ topic 扩展做好架构准备。

**硬约束**：不改视觉、不改数据、不改交互、不加依赖、不改构建、不改 CSS className。

## 目标目录结构

```
boards/kids-world/src/
├── App.tsx                              # ~25 行：装配 router + locale + shell
├── main.tsx                             # 不变
│
├── types/
│   ├── world.ts                         # ExplorationMap, World, TopicCard
│   ├── topic.ts                         # Topic, ClickTask, TextMap, TaskResult
│   └── assets.ts                        # GeneratedImageAsset
│
├── data/
│   ├── exploration-map.json             # 原位不动
│   ├── topic-registry.json              # 原位不动
│   ├── image-generation-manifest.json   # 原位不动
│   ├── topics/                          # 6 个 topic JSON 原位不动
│   ├── locales/                         # en-US overlay 原位不动
│   └── loaders/
│       ├── locale-merge.ts              # deepMerge + mergeByIdArray
│       ├── load-map.ts                  # getMap()：import map JSON + en overlay，调用 deepMerge
│       └── load-topic.ts               # getTopic()：topicBaseBySlug/topicEnBySlug 映射表 + JSON import
│
├── hooks/
│   └── use-hash-route.ts               # useHashRoute() hook
│
├── pages/
│   ├── HomePage.tsx                     # selectedWorld 状态 + 4 个 home 子组件组合
│   └── TopicPage.tsx                    # 薄壳：按顺序渲染 9 个 topic section 组件
│
├── components/
│   ├── layout/
│   │   ├── Topbar.tsx                   # brand + mobile hamburger + topic nav + locale toggle
│   │   └── PageShell.tsx                # topbar + <main> slot wrapper
│   ├── home/
│   │   ├── HeroSection.tsx              # 首页 hero（标题 + CTA）
│   │   ├── InterestBand.tsx             # 动画世界 2 列卡片
│   │   ├── WorldGrid.tsx                # 6 个知识世界按钮网格
│   │   └── WorldTopicPanel.tsx          # 选中世界展开的 topic 卡片列表
│   ├── topic/
│   │   ├── TopicHero.tsx                # hero 区 + PlaceholderScene（内联，不单独导出）
│   │   ├── ClassificationGroups.tsx     # 分类卡片 2 列
│   │   ├── RepresentativeObjects.tsx    # 实体卡片 4 列 + activeObject 状态
│   │   ├── MechanismSteps.tsx           # 流程步骤 4 列（含 secondaryMechanism）
│   │   ├── ComparePairs.tsx             # A vs B 对比 3 列
│   │   ├── ClickTaskCard.tsx            # 3 种互动任务 handler
│   │   ├── SpeakTemplates.tsx           # 口头表达模板列表
│   │   ├── ParentTips.tsx               # 家长指导清单
│   │   └── RelatedTopics.tsx            # 关联 topic 标签条
│   └── shared/
│       ├── GeneratedImage.tsx           # asset resolve + WebP→PNG→placeholder 降级
│       ├── LocaleToggle.tsx             # zh-CN / en-US 切换按钮
│       ├── StatusPill.tsx               # 状态徽章
│       └── SectionHeader.tsx            # kicker + title + description 复用头
│
├── lib/
│   ├── asset-resolve.ts                 # resolveBoardAsset(), resolveBoardAssetCandidates()
│   ├── asset-map.ts                     # generatedAssets lookup, topicHeroAssetBySlug, animationTopicAssetByHref, getTopicCardAssetId, getKnowledgeTopicAssetId
│   └── world-icons.ts                  # worldIcons: Record<string, LucideIcon>
│
└── styles/
    └── styles.css                       # 第一轮不拆，原样搬到 styles/ 子目录
```

## 拆分映射表

| 原 App.tsx 行范围 | 内容 | 目标文件 |
|-------------------|------|---------|
| 1-19 | lucide-react import | 分散到各消费组件，按需 import |
| 21-36 | JSON import（12 个 topic + map + manifest） | `data/loaders/load-topic.ts` + `load-map.ts` |
| 38 | ReactNode import | 各消费组件按需 import |
| 40-42 | Locale, TaskResult 类型 | `types/topic.ts` |
| 44-56 | TextMap, TopicCard 类型 | `types/world.ts`（TopicCard）+ `types/topic.ts`（TextMap） |
| 58-90 | World, ExplorationMap 类型 | `types/world.ts` |
| 92-105 | ClickTask 类型 | `types/topic.ts` |
| 107-157 | Topic 类型 | `types/topic.ts` |
| 159-162 | generatedAssets lookup | `lib/asset-map.ts` |
| 164-176 | topicHeroAssetBySlug, animationTopicAssetByHref | `lib/asset-map.ts` |
| 178-204 | topicBaseBySlug, topicEnBySlug, worldIcons | `data/loaders/load-topic.ts`（映射表）+ `lib/world-icons.ts` |
| 206-242 | mergeByIdArray, deepMerge | `data/loaders/locale-merge.ts` |
| 244-255 | useHashRoute | `hooks/use-hash-route.ts` |
| 257-260 | getMap | `data/loaders/load-map.ts` |
| 262-266 | getTopic | `data/loaders/load-topic.ts` |
| 268-270 | getTopicHref | `lib/asset-resolve.ts` |
| 272-276 | getExternalHref | `lib/asset-resolve.ts` |
| 278-305 | resolveBoardAsset, resolveBoardAssetCandidates | `lib/asset-resolve.ts` |
| 307-313 | getTopicCardAssetId, getKnowledgeTopicAssetId | `lib/asset-map.ts` |
| 315-352 | GeneratedImage | `components/shared/GeneratedImage.tsx` |
| 354-366 | LocaleToggle | `components/shared/LocaleToggle.tsx` |
| 368-371 | StatusPill | `components/shared/StatusPill.tsx` |
| 373-391 | PlaceholderScene | `components/topic/TopicHero.tsx`（内部不导出） |
| 393-401 | SectionHeader | `components/shared/SectionHeader.tsx` |
| 403-508 | HomePage | `pages/HomePage.tsx` → 内部引用 4 个 home/ 子组件 |
| 510-674 | TopicPage | `pages/TopicPage.tsx` → 内部引用 9 个 topic/ 子组件 |
| 676-757 | ClickTaskCard | `components/topic/ClickTaskCard.tsx` |
| 759-799 | App 根组件 | `App.tsx` |

## App.tsx 目标形态

```tsx
import { useState } from "react";
import { useHashRoute } from "./hooks/use-hash-route";
import { getMap } from "./data/loaders/load-map";
import { PageShell } from "./components/layout/PageShell";
import { HomePage } from "./pages/HomePage";
import { TopicPage } from "./pages/TopicPage";
import type { Locale } from "./types/topic";

export function App() {
  const topicSlug = useHashRoute();
  const [locale, setLocale] = useState<Locale>("zh-CN");
  const map = getMap(locale);

  return (
    <PageShell locale={locale} onLocaleChange={setLocale} map={map}>
      {topicSlug ? (
        <TopicPage slug={topicSlug} locale={locale} map={map} />
      ) : (
        <HomePage locale={locale} map={map} />
      )}
    </PageShell>
  );
}
```

## TopicPage 目标形态

TopicPage 是薄壳，按顺序渲染各 section：

```tsx
export function TopicPage({ slug, locale, map }: Props) {
  const topic = getTopic(slug, locale);
  if (!topic) return <NotFound />;

  return (
    <article className="topic-page">
      <TopicHero topic={topic} map={map} />
      <ClassificationGroups groups={topic.classificationGroups} />
      <RepresentativeObjects objects={topic.representativeObjects} groups={topic.classificationGroups} />
      <MechanismSteps mechanism={topic.mechanism} secondary={topic.secondaryMechanism} />
      <ComparePairs pairs={topic.comparePairs} />
      {topic.clickTasks.map((task) => (
        <ClickTaskCard key={task.id} task={task} />
      ))}
      <SpeakTemplates templates={topic.speakTemplates} />
      <ParentTips tips={topic.parentTips} />
      <RelatedTopics topics={topic.relatedTopics} />
    </article>
  );
}
```

## 关键设计决策

### D1：CSS 第一轮不拆

946 行 styles.css 保持单文件，只从 `src/styles.css` 移到 `src/styles/styles.css`，`main.tsx` 的 import 路径相应更新。

理由：CSS class name 是跨组件的全局命名空间，拆 CSS 需要同时理清作用域，和组件拆分混在一起风险叠加。

### D2：PlaceholderScene 不单独导出

PlaceholderScene 只在 TopicHero 内使用，作为 TopicHero.tsx 的内部组件，不放 shared/。

### D3：activeObjectId 状态放在 RepresentativeObjects 内部

当前 TopicPage 里有 `activeObjectId` 状态控制"点击实体卡片展开详情"。这个状态只影响 RepresentativeObjects 区域，封装在该组件内部。

### D4：JSON import 集中在 loaders

`load-topic.ts` 内部 import 所有 12 个 topic JSON + en overlay，对外只暴露 `getTopic(slug, locale)`。这样新增 topic 只需改 `load-topic.ts` 加一行 import + 映射。

### D5：lib/ 只放纯函数

`lib/` 下不放 React 组件，只放纯函数和静态映射。React hook 放 `hooks/`，React 组件放 `components/`。

## 验收标准

1. **功能一致**：重构前后页面视觉、交互、数据完全相同
2. **构建通过**：`npm run dev` + `npm run build` 无报错
3. **App.tsx < 30 行**
4. **无 `any` 类型扩散**：原有的 `as unknown as Topic` 保留在 loaders 内，不外溢
5. **import 路径正确**：所有组件能正确 import types/lib/data
6. **CSS 无断裂**：所有 className 保持不变，视觉输出一致
7. **浏览器验证**：dev server 上 HomePage + 至少 2 个 TopicPage 手动走读确认
