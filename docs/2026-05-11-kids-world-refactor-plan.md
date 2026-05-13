# Kids-World App.tsx 搬家式重构 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `boards/kids-world/src/App.tsx`（799 行）拆分为按职责分目录的 ~27 个文件，不改任何功能/视觉/交互。

**Architecture:** 搬家式重构 — 逐块剪切原文件代码到新文件，更新 import 路径，保持所有 className 和 JSX 结构不变。每个 Phase 结束后浏览器验证功能一致。

**Tech Stack:** React 18, TypeScript, Vite 5, CSS（不拆）

**Plan size:** Medium (8 tasks, 3 phases)

**Spec:** `docs/2026-05-11-kids-world-refactor-design.md`

---

## Phase 1: 基础层 — types / lib / hooks / data loaders

Phase 1 不涉及任何 React 组件，只搬类型、纯函数、数据加载器。完成后 App.tsx 仍是唯一组件文件，但 import 已指向新位置。

### Task 1.1: 类型定义

**Files:**
- Create: `boards/kids-world/src/types/world.ts`
- Create: `boards/kids-world/src/types/topic.ts`
- Create: `boards/kids-world/src/types/assets.ts`

**Verify:** `cd /Users/admin/Documents/kids-visual-learning-pack && npx tsc --noEmit --project boards/kids-world/tsconfig.json 2>/dev/null || npx tsc --noEmit` → no errors
**Depends on:** None

- [ ] **Step 1: Create `types/world.ts`**

从 App.tsx 行 45-90 剪切 TopicCard、World、ExplorationMap 类型：

```typescript
// boards/kids-world/src/types/world.ts

export type TopicCard = {
  id?: string;
  slug?: string;
  title: string;
  status: string;
  cardDescription: string;
  childDescription?: string;
  learningGoalTags?: string[];
  suggestedRoute?: string;
  href?: string;
};

export type World = {
  id: string;
  type: string;
  name: string;
  status: string;
  recommendedColor: { hex: string; softHex: string };
  childOneLiner: string;
  parentNote: string;
  entryCard: { title: string; subtitle: string; cta: string; badge: string };
  topicCards: TopicCard[];
};

export type ExplorationMap = {
  title: string;
  subtitle: string;
  homeHero: {
    title: string;
    subtitle: string;
    childIntro: string;
    parentIntro: string;
    primaryCTA: string;
    secondaryCTA: string;
  };
  sections: Array<{ id: string; title: string; description: string; worlds: string[] }>;
  statusLegend: Array<{ status: string; label: string; childLabel: string; description: string }>;
  worlds: World[];
};
```

- [ ] **Step 2: Create `types/topic.ts`**

从 App.tsx 行 40-44、92-157 剪切：

```typescript
// boards/kids-world/src/types/topic.ts

export type Locale = "zh-CN" | "en-US";
export type TaskResult = "idle" | "correct" | "wrong";
export type TextMap = Record<string, string>;

export type ClickTask = {
  id: string;
  type: "singleChoice" | "findTarget" | "sequenceClick" | string;
  title: string;
  prompt?: string;
  options?: Array<{ id: string; label: string }>;
  correctOptionId?: string;
  correctSequence?: string[];
  targetIds?: string[];
  decoyIds?: string[];
  wrongHint?: string;
  wrongHints?: TextMap;
  successCopy?: string;
};

export type Topic = {
  slug: string;
  title: string;
  subtitle: string;
  pageType: string;
  coreQuestion: string;
  learningGoals: string[];
  relatedTopics: string[];
  hero: {
    title: string;
    kicker: string;
    lead: string;
    sceneExplanation: string;
    childPrompt: string;
    parentPrompt: string;
    placeholder?: { type?: string; asset?: string };
  };
  assets?: Record<string, { path: string; purpose?: string; status?: string }>;
  classificationGroups: Array<{
    id: string;
    name: string;
    childExplanation: string;
    parentNote?: string;
  }>;
  representativeObjects: Array<{
    id: string;
    name: string;
    groupId: string;
    childExplanation: string;
    visualHint: string;
    commonMisread?: string;
  }>;
  mechanism: {
    title?: string;
    steps: Array<{ id: string; shortTitle: string; childExplanation: string; parentNote?: string }>;
  };
  secondaryMechanism?: {
    title: string;
    steps: Array<{ id: string; shortTitle: string; childExplanation: string; parentNote?: string }>;
  };
  comparePairs: Array<{
    id: string;
    title: string;
    a: { name: string; points: string[] };
    b: { name: string; points: string[] };
    childConclusion: string;
  }>;
  clickTasks: ClickTask[];
  speakTemplates: string[];
  parentTips: string[];
};
```

- [ ] **Step 3: Create `types/assets.ts`**

从 App.tsx 行 70-74 剪切：

```typescript
// boards/kids-world/src/types/assets.ts

export type GeneratedImageAsset = {
  assetId: string;
  pngPath: string;
  webpPath: string;
};
```

- [ ] **Step 4: 更新 App.tsx — 删除类型定义，改为 import**

删除 App.tsx 行 40-157 的所有类型定义，替换为：

```typescript
import type { ExplorationMap, TopicCard, World } from "./types/world";
import type { ClickTask, Locale, TaskResult, TextMap, Topic } from "./types/topic";
import type { GeneratedImageAsset } from "./types/assets";
```

- [ ] **Step 5: 验证 TypeScript 编译通过**

Run: `cd /Users/admin/Documents/kids-visual-learning-pack && npx tsc --noEmit 2>&1 | head -20`
Expected: 无错误

---

### Task 1.2: 纯函数 — lib/

**Files:**
- Create: `boards/kids-world/src/lib/asset-resolve.ts`
- Create: `boards/kids-world/src/lib/asset-map.ts`
- Create: `boards/kids-world/src/lib/world-icons.ts`

**Verify:** `npx tsc --noEmit` → no errors
**Depends on:** Task 1.1 (types)

- [ ] **Step 1: Create `lib/asset-resolve.ts`**

从 App.tsx 行 268-305 剪切 getTopicHref、getExternalHref、resolveBoardAsset、resolveBoardAssetCandidates：

```typescript
// boards/kids-world/src/lib/asset-resolve.ts

export function getTopicHref(slug: string) {
  return `#topic/${slug}`;
}

export function getExternalHref(href?: string) {
  if (!href) return undefined;
  if (href.startsWith("http") || href.startsWith("../")) return href;
  return `../../${href}`;
}

export function resolveBoardAsset(path?: string) {
  if (!path) return undefined;
  if (/^(https?:|data:|blob:)/.test(path)) return path;

  const normalized = path.replace(/^\/+/, "");
  const baseUrl = ((import.meta as ImportMeta & { env?: { BASE_URL?: string } }).env?.BASE_URL ?? "./");
  const base = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;

  return `${base}${normalized}`;
}

export function resolveBoardAssetCandidates(path?: string) {
  const primary = resolveBoardAsset(path);
  if (!path || !primary || /^(https?:|data:|blob:)/.test(path)) {
    return primary ? [primary] : [];
  }

  const normalized = path.replace(/^\/+/, "");
  const candidates = [];

  if (typeof window !== "undefined" && window.location.pathname.startsWith("/boards/kids-world/")) {
    candidates.push(`/boards/kids-world/public/${normalized}`);
  }

  candidates.push(primary);

  return [...new Set(candidates)];
}
```

- [ ] **Step 2: Create `lib/asset-map.ts`**

从 App.tsx 行 159-176、307-313 剪切：

```typescript
// boards/kids-world/src/lib/asset-map.ts

import imageManifest from "../data/image-generation-manifest.json";
import type { GeneratedImageAsset } from "../types/assets";
import type { TopicCard } from "../types/world";

export const generatedAssets = (imageManifest.assets as GeneratedImageAsset[]).reduce<Record<string, GeneratedImageAsset>>((acc, asset) => {
  acc[asset.assetId] = asset;
  return acc;
}, {});

export const topicHeroAssetBySlug: Record<string, string> = {
  "animal-classification-tree": "life-animal-classification-tree-hero",
  "blood-cells-3d": "body-blood-cells-3d-hero",
  "earth-climate-cities": "earth-climate-cities-hero",
  "insects-and-spiders": "life-insects-and-spiders-hero",
  "llm-kids-basics": "human-made-llm-kids-basics-hero",
  "solar-system-overview": "space-solar-system-overview-hero",
};

export const animationTopicAssetByHref: Array<[string, string]> = [
  ["spider-verse", "animation-spider-verse-card"],
  ["paw-patrol", "animation-paw-patrol-card"],
];

export function getTopicCardAssetId(topic: TopicCard) {
  return animationTopicAssetByHref.find(([hrefFragment]) => topic.href?.includes(hrefFragment))?.[1];
}

export function getKnowledgeTopicAssetId(topic: TopicCard) {
  return topic.slug ? topicHeroAssetBySlug[topic.slug] : undefined;
}
```

- [ ] **Step 3: Create `lib/world-icons.ts`**

从 App.tsx 行 196-204 剪切：

```typescript
// boards/kids-world/src/lib/world-icons.ts

import {
  Activity,
  BrainCircuit,
  Globe2,
  Leaf,
  Orbit,
  Sparkles,
  Zap,
} from "lucide-react";

export const worldIcons = {
  animation: Sparkles,
  life: Leaf,
  body: Activity,
  earth: Globe2,
  space: Orbit,
  energy: Zap,
  humanMade: BrainCircuit,
};
```

- [ ] **Step 4: 更新 App.tsx — 删除搬走的代码，改为 import**

删除对应行，添加：

```typescript
import { getTopicHref, getExternalHref, resolveBoardAssetCandidates } from "./lib/asset-resolve";
import { generatedAssets, topicHeroAssetBySlug, getTopicCardAssetId, getKnowledgeTopicAssetId } from "./lib/asset-map";
import { worldIcons } from "./lib/world-icons";
```

- [ ] **Step 5: 验证编译**

Run: `npx tsc --noEmit`
Expected: 无错误

- [ ] **Step 6: Commit**

```bash
git add boards/kids-world/src/types/ boards/kids-world/src/lib/ boards/kids-world/src/App.tsx
git commit -m "refactor(kids-world): extract types and lib modules from App.tsx"
```

---

### Task 1.3: Data loaders + hook

**Files:**
- Create: `boards/kids-world/src/data/loaders/locale-merge.ts`
- Create: `boards/kids-world/src/data/loaders/load-map.ts`
- Create: `boards/kids-world/src/data/loaders/load-topic.ts`
- Create: `boards/kids-world/src/hooks/use-hash-route.ts`

**Verify:** `npx tsc --noEmit` → no errors + `npm run dev` 启动无报错
**Depends on:** Task 1.1 (types), Task 1.2 (lib)

- [ ] **Step 1: Create `data/loaders/locale-merge.ts`**

从 App.tsx 行 206-242 剪切 mergeByIdArray 和 deepMerge：

```typescript
// boards/kids-world/src/data/loaders/locale-merge.ts

function mergeByIdArray(base: unknown[], overlay: unknown[]): unknown[] {
  const allHaveIds = [...base, ...overlay].every(
    (item) => item && typeof item === "object" && "id" in item,
  );
  if (!allHaveIds) return overlay;

  return base.map((item) => {
    const baseItem = item as { id: string };
    const overlayItem = overlay.find(
      (candidate) => candidate && typeof candidate === "object" && "id" in candidate && candidate.id === baseItem.id,
    );
    return overlayItem ? deepMerge(baseItem, overlayItem) : item;
  });
}

export function deepMerge<T>(base: T, overlay: unknown): T {
  if (Array.isArray(base) && Array.isArray(overlay)) {
    return mergeByIdArray(base, overlay) as T;
  }

  if (
    base &&
    overlay &&
    typeof base === "object" &&
    typeof overlay === "object" &&
    !Array.isArray(base) &&
    !Array.isArray(overlay)
  ) {
    const merged: Record<string, unknown> = { ...(base as Record<string, unknown>) };
    Object.entries(overlay as Record<string, unknown>).forEach(([key, value]) => {
      merged[key] = key in merged ? deepMerge(merged[key], value) : value;
    });
    return merged as T;
  }

  return overlay as T;
}
```

- [ ] **Step 2: Create `data/loaders/load-map.ts`**

从 App.tsx 行 257-260 剪切：

```typescript
// boards/kids-world/src/data/loaders/load-map.ts

import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import explorationMapBase from "../exploration-map.json";
import explorationMapEn from "../locales/en-US/exploration-map.json";
import { deepMerge } from "./locale-merge";

export function getMap(locale: Locale): ExplorationMap {
  const base = explorationMapBase as unknown as ExplorationMap;
  return locale === "en-US" ? deepMerge(base, explorationMapEn) : base;
}
```

- [ ] **Step 3: Create `data/loaders/load-topic.ts`**

从 App.tsx 行 21-36（JSON import）、178-194（映射表）、262-266（getTopic）剪切：

```typescript
// boards/kids-world/src/data/loaders/load-topic.ts

import type { Locale, Topic } from "../../types/topic";
import { deepMerge } from "./locale-merge";

import animalTreeBase from "../topics/animal-classification-tree.json";
import animalTreeEn from "../locales/en-US/topics/animal-classification-tree.json";
import bloodCellsBase from "../topics/blood-cells-3d.json";
import bloodCellsEn from "../locales/en-US/topics/blood-cells-3d.json";
import climateBase from "../topics/earth-climate-cities.json";
import climateEn from "../locales/en-US/topics/earth-climate-cities.json";
import insectsBase from "../topics/insects-and-spiders.json";
import insectsEn from "../locales/en-US/topics/insects-and-spiders.json";
import llmBase from "../topics/llm-kids-basics.json";
import llmEn from "../locales/en-US/topics/llm-kids-basics.json";
import solarBase from "../topics/solar-system-overview.json";
import solarEn from "../locales/en-US/topics/solar-system-overview.json";

const topicBaseBySlug = {
  "animal-classification-tree": animalTreeBase as unknown as Topic,
  "blood-cells-3d": bloodCellsBase as unknown as Topic,
  "earth-climate-cities": climateBase as unknown as Topic,
  "insects-and-spiders": insectsBase as unknown as Topic,
  "llm-kids-basics": llmBase as unknown as Topic,
  "solar-system-overview": solarBase as unknown as Topic,
};

const topicEnBySlug = {
  "animal-classification-tree": animalTreeEn as unknown as Partial<Topic>,
  "blood-cells-3d": bloodCellsEn as unknown as Partial<Topic>,
  "earth-climate-cities": climateEn as unknown as Partial<Topic>,
  "insects-and-spiders": insectsEn as unknown as Partial<Topic>,
  "llm-kids-basics": llmEn as unknown as Partial<Topic>,
  "solar-system-overview": solarEn as unknown as Partial<Topic>,
};

export function getTopic(slug: string, locale: Locale): Topic | null {
  const base = topicBaseBySlug[slug as keyof typeof topicBaseBySlug];
  if (!base) return null;
  return locale === "en-US" ? deepMerge(base, topicEnBySlug[slug as keyof typeof topicEnBySlug]) : base;
}

export function hasTopicData(slug: string): boolean {
  return slug in topicBaseBySlug;
}
```

注意：导出 `hasTopicData` 供 HomePage 的 WorldTopicPanel 判断 topic 是否可点击（原代码行 488 用 `topicBaseBySlug[...]` 判断）。

- [ ] **Step 4: Create `hooks/use-hash-route.ts`**

从 App.tsx 行 244-255 剪切：

```typescript
// boards/kids-world/src/hooks/use-hash-route.ts

import { useEffect, useState } from "react";

export function useHashRoute() {
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    const handler = () => setHash(window.location.hash);
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  const match = hash.match(/^#topic\/(.+)$/);
  return match?.[1] ?? null;
}
```

- [ ] **Step 5: 更新 App.tsx — 删除搬走的代码，改为 import**

删除：JSON import 行 21-36、映射表行 178-194、工具函数行 206-266。添加：

```typescript
import { getMap } from "./data/loaders/load-map";
import { getTopic, hasTopicData } from "./data/loaders/load-topic";
import { useHashRoute } from "./hooks/use-hash-route";
```

- [ ] **Step 6: 验证编译 + dev server**

Run: `npx tsc --noEmit && npm run dev`
Expected: 编译通过，dev server 启动

- [ ] **Step 7: Commit**

```bash
git add boards/kids-world/src/data/loaders/ boards/kids-world/src/hooks/ boards/kids-world/src/App.tsx
git commit -m "refactor(kids-world): extract data loaders and hash route hook"
```

---

## Phase 2: 组件层 — shared / topic / home / layout

将 App.tsx 中的所有 React 组件搬到各自文件。

### Task 2.1: Shared 组件

**Files:**
- Create: `boards/kids-world/src/components/shared/GeneratedImage.tsx`
- Create: `boards/kids-world/src/components/shared/LocaleToggle.tsx`
- Create: `boards/kids-world/src/components/shared/StatusPill.tsx`
- Create: `boards/kids-world/src/components/shared/SectionHeader.tsx`

**Verify:** `npx tsc --noEmit` → no errors
**Depends on:** Task 1.1, Task 1.2

- [ ] **Step 1: Create `components/shared/GeneratedImage.tsx`**

从 App.tsx 行 315-352 剪切：

```tsx
// boards/kids-world/src/components/shared/GeneratedImage.tsx

import { useEffect, useState } from "react";
import { generatedAssets } from "../../lib/asset-map";
import { resolveBoardAssetCandidates } from "../../lib/asset-resolve";

export function GeneratedImage({
  assetId,
  fallbackPath,
  className,
  alt,
}: {
  assetId?: string;
  fallbackPath?: string;
  className: string;
  alt: string;
}) {
  const asset = assetId ? generatedAssets[assetId] : undefined;
  const sources = [asset?.webpPath, asset?.pngPath, fallbackPath]
    .flatMap((path) => resolveBoardAssetCandidates(path))
    .filter(Boolean);
  const [sourceIndex, setSourceIndex] = useState(0);

  useEffect(() => {
    setSourceIndex(0);
  }, [assetId, fallbackPath]);

  const source = sources[sourceIndex];

  if (!source) {
    return null;
  }

  return (
    <img
      alt={alt}
      className={className}
      src={source}
      onError={() => {
        setSourceIndex((current) => (current + 1 < sources.length ? current + 1 : sources.length));
      }}
    />
  );
}
```

- [ ] **Step 2: Create `components/shared/LocaleToggle.tsx`**

从 App.tsx 行 354-366 剪切：

```tsx
// boards/kids-world/src/components/shared/LocaleToggle.tsx

import { Languages } from "lucide-react";
import type { Locale } from "../../types/topic";

export function LocaleToggle({ locale, onChange }: { locale: Locale; onChange: (locale: Locale) => void }) {
  return (
    <div className="locale-toggle" aria-label="Language switch">
      <Languages size={18} />
      <button className={locale === "zh-CN" ? "active" : ""} type="button" onClick={() => onChange("zh-CN")}>
        中文
      </button>
      <button className={locale === "en-US" ? "active" : ""} type="button" onClick={() => onChange("en-US")}>
        English
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Create `components/shared/StatusPill.tsx`**

从 App.tsx 行 368-371 剪切：

```tsx
// boards/kids-world/src/components/shared/StatusPill.tsx

import type { ExplorationMap } from "../../types/world";

export function StatusPill({ status, map }: { status: string; map: ExplorationMap }) {
  const statusText = map.statusLegend.find((item) => item.status === status);
  return <span className={`status-pill status-${status}`}>{statusText?.childLabel ?? status}</span>;
}
```

- [ ] **Step 4: Create `components/shared/SectionHeader.tsx`**

从 App.tsx 行 393-401 剪切：

```tsx
// boards/kids-world/src/components/shared/SectionHeader.tsx

import type { ReactNode } from "react";

export function SectionHeader({ kicker, title, children }: { kicker?: string; title: string; children?: ReactNode }) {
  return (
    <div className="section-head">
      {kicker && <p className="kicker">{kicker}</p>}
      <h2>{title}</h2>
      {children && <p>{children}</p>}
    </div>
  );
}
```

- [ ] **Step 5: 更新 App.tsx — 删除 4 个组件，改为 import**

```typescript
import { GeneratedImage } from "./components/shared/GeneratedImage";
import { LocaleToggle } from "./components/shared/LocaleToggle";
import { StatusPill } from "./components/shared/StatusPill";
import { SectionHeader } from "./components/shared/SectionHeader";
```

- [ ] **Step 6: 验证编译**

Run: `npx tsc --noEmit`
Expected: 无错误

- [ ] **Step 7: Commit**

```bash
git add boards/kids-world/src/components/shared/ boards/kids-world/src/App.tsx
git commit -m "refactor(kids-world): extract shared components"
```

---

### Task 2.2: Topic 组件

**Files:**
- Create: `boards/kids-world/src/components/topic/TopicHero.tsx`
- Create: `boards/kids-world/src/components/topic/ClassificationGroups.tsx`
- Create: `boards/kids-world/src/components/topic/RepresentativeObjects.tsx`
- Create: `boards/kids-world/src/components/topic/MechanismSteps.tsx`
- Create: `boards/kids-world/src/components/topic/ComparePairs.tsx`
- Create: `boards/kids-world/src/components/topic/ClickTaskCard.tsx`
- Create: `boards/kids-world/src/components/topic/SpeakTemplates.tsx`
- Create: `boards/kids-world/src/components/topic/ParentTips.tsx`
- Create: `boards/kids-world/src/components/topic/RelatedTopics.tsx`

**Verify:** `npx tsc --noEmit` → no errors
**Depends on:** Task 2.1 (shared components)

- [ ] **Step 1: Create `components/topic/TopicHero.tsx`**

从 App.tsx 行 373-391（PlaceholderScene）和行 522-537（hero section JSX）组合：

```tsx
// boards/kids-world/src/components/topic/TopicHero.tsx

import { CheckCircle2 } from "lucide-react";
import type { Topic } from "../../types/topic";
import { topicHeroAssetBySlug } from "../../lib/asset-map";
import { GeneratedImage } from "../shared/GeneratedImage";

function PlaceholderScene({ topic }: { topic: Topic }) {
  const type = topic.hero.placeholder?.type ?? topic.pageType;
  const assetId = topicHeroAssetBySlug[topic.slug];
  return (
    <div className={`placeholder-scene ${String(type)} ${assetId ? "generated-scene" : ""}`}>
      <GeneratedImage
        alt=""
        assetId={assetId}
        className="scene-image"
        fallbackPath={topic.hero.placeholder?.asset ?? topic.assets?.hero?.path}
      />
      <span className="scene-orbit" />
      <span className="scene-node one" />
      <span className="scene-node two" />
      <span className="scene-node three" />
      <span className="scene-label">{topic.title}</span>
    </div>
  );
}

export function TopicHero({ topic }: { topic: Topic }) {
  return (
    <section className="topic-hero">
      <div className="topic-hero-copy">
        <p className="kicker">{topic.hero.kicker}</p>
        <h1>{topic.hero.title}</h1>
        <p>{topic.hero.lead}</p>
        <div className="goal-list">
          {topic.learningGoals.map((goal) => (
            <span key={goal}>
              <CheckCircle2 size={16} />
              {goal}
            </span>
          ))}
        </div>
      </div>
      <PlaceholderScene topic={topic} />
    </section>
  );
}
```

- [ ] **Step 2: Create `components/topic/ClassificationGroups.tsx`**

从 TopicPage 行 546-560 提取：

```tsx
// boards/kids-world/src/components/topic/ClassificationGroups.tsx

import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  groups: Topic["classificationGroups"];
  activeGroupId?: string;
  locale: string;
};

export function ClassificationGroups({ groups, activeGroupId, locale }: Props) {
  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "分类线索" : "Sorting clues"} />
      <div className="group-list">
        {groups.map((group) => (
          <button
            className={activeGroupId === group.id ? "group-card active" : "group-card"}
            key={group.id}
            type="button"
          >
            <strong>{group.name}</strong>
            <span>{group.childExplanation}</span>
          </button>
        ))}
      </div>
    </article>
  );
}
```

- [ ] **Step 3: Create `components/topic/RepresentativeObjects.tsx`**

从 TopicPage 行 511-585 提取，封装 activeObjectId 状态：

```tsx
// boards/kids-world/src/components/topic/RepresentativeObjects.tsx

import { useState } from "react";
import { Dna } from "lucide-react";
import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  objects: Topic["representativeObjects"];
  locale: string;
};

export function RepresentativeObjects({ objects, locale }: Props) {
  const [activeObjectId, setActiveObjectId] = useState(objects[0]?.id ?? "");
  const activeObject = objects.find((item) => item.id === activeObjectId) ?? objects[0];

  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "对象卡" : "Object cards"} />
      <div className="object-grid">
        {objects.map((object) => (
          <button
            className={activeObjectId === object.id ? "object-card active" : "object-card"}
            key={object.id}
            type="button"
            onClick={() => setActiveObjectId(object.id)}
          >
            <Dna size={20} />
            <strong>{object.name}</strong>
            <small>{object.visualHint}</small>
          </button>
        ))}
      </div>
      {activeObject && (
        <div className="object-detail">
          <strong>{activeObject.name}</strong>
          <span>{activeObject.childExplanation}</span>
          <small>{activeObject.commonMisread}</small>
        </div>
      )}
    </article>
  );
}
```

- [ ] **Step 4: Create `components/topic/MechanismSteps.tsx`**

从 TopicPage 行 587-613 提取（含 secondaryMechanism）：

```tsx
// boards/kids-world/src/components/topic/MechanismSteps.tsx

import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  mechanism: Topic["mechanism"];
  secondary?: Topic["secondaryMechanism"];
  locale: string;
};

function StepRow({ steps }: { steps: Topic["mechanism"]["steps"] }) {
  return (
    <div className="step-row">
      {steps.map((step, index) => (
        <div className="step-card" key={step.id}>
          <span>{index + 1}</span>
          <strong>{step.shortTitle}</strong>
          <small>{step.childExplanation}</small>
        </div>
      ))}
    </div>
  );
}

export function MechanismSteps({ mechanism, secondary, locale }: Props) {
  return (
    <>
      <article className="panel wide">
        <SectionHeader title={locale === "zh-CN" ? "机制步骤" : "How it works"} />
        <StepRow steps={mechanism.steps} />
      </article>
      {secondary && (
        <article className="panel wide">
          <SectionHeader title={secondary.title} />
          <StepRow steps={secondary.steps} />
        </article>
      )}
    </>
  );
}
```

- [ ] **Step 5: Create `components/topic/ComparePairs.tsx`**

从 TopicPage 行 615-633 提取：

```tsx
// boards/kids-world/src/components/topic/ComparePairs.tsx

import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  pairs: Topic["comparePairs"];
  locale: string;
};

export function ComparePairs({ pairs, locale }: Props) {
  return (
    <article className="panel wide">
      <SectionHeader title={locale === "zh-CN" ? "容易混淆" : "Easy mix-ups"} />
      <div className="compare-grid">
        {pairs.map((pair) => (
          <div className="compare-card" key={pair.id}>
            <strong>{pair.title}</strong>
            <div>
              <span>{pair.a.name}</span>
              <small>{pair.a.points.join(" · ")}</small>
            </div>
            <div>
              <span>{pair.b.name}</span>
              <small>{pair.b.points.join(" · ")}</small>
            </div>
            <em>{pair.childConclusion}</em>
          </div>
        ))}
      </div>
    </article>
  );
}
```

- [ ] **Step 6: Create `components/topic/ClickTaskCard.tsx`**

从 App.tsx 行 676-757 剪切，原样搬：

```tsx
// boards/kids-world/src/components/topic/ClickTaskCard.tsx

import { useState } from "react";
import { Search } from "lucide-react";
import type { ClickTask, TaskResult } from "../../types/topic";

export function ClickTaskCard({ task }: { task: ClickTask }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<TaskResult>("idle");
  const [message, setMessage] = useState("");

  function resolveWrongHint(optionId?: string) {
    if (optionId && task.wrongHints && optionId in task.wrongHints) return task.wrongHints[optionId as keyof typeof task.wrongHints];
    return task.wrongHint ?? "再观察一个线索试试看。";
  }

  function handleSingleChoice(optionId: string) {
    if (optionId === task.correctOptionId) {
      setResult("correct");
      setMessage(task.successCopy ?? "");
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
  }

  function handleFindTarget(optionId: string) {
    if (task.targetIds?.includes(optionId)) {
      const next = Array.from(new Set([...selectedIds, optionId]));
      setSelectedIds(next);
      const complete = task.targetIds.every((id) => next.includes(id));
      setResult(complete ? "correct" : "idle");
      setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
  }

  function handleSequence(optionId: string) {
    const next = [...selectedIds, optionId];
    const expected = task.correctSequence?.[selectedIds.length];
    if (optionId !== expected) {
      setSelectedIds([]);
      setResult("wrong");
      setMessage(resolveWrongHint(optionId));
      return;
    }
    setSelectedIds(next);
    const complete = next.length === task.correctSequence?.length;
    setResult(complete ? "correct" : "idle");
    setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
  }

  function handleClick(optionId: string) {
    if (task.type === "singleChoice") handleSingleChoice(optionId);
    if (task.type === "findTarget") handleFindTarget(optionId);
    if (task.type === "sequenceClick") handleSequence(optionId);
  }

  const options =
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: id.replace(/-/g, " "),
    }));

  return (
    <div className={`task-card ${result}`}>
      <Search size={20} />
      <strong>{task.title}</strong>
      {task.prompt && <span>{task.prompt}</span>}
      <div className="task-options">
        {options.map((option) => (
          <button
            className={selectedIds.includes(option.id) ? "selected" : ""}
            key={option.id}
            type="button"
            onClick={() => handleClick(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>
      {message && <p>{message}</p>}
    </div>
  );
}
```

- [ ] **Step 7: Create `components/topic/SpeakTemplates.tsx`**

```tsx
// boards/kids-world/src/components/topic/SpeakTemplates.tsx

import { SectionHeader } from "../shared/SectionHeader";

type Props = { templates: string[]; locale: string };

export function SpeakTemplates({ templates, locale }: Props) {
  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "讲一讲" : "Try explaining"} />
      <div className="speak-list">
        {templates.map((template) => (
          <span key={template}>{template}</span>
        ))}
      </div>
    </article>
  );
}
```

- [ ] **Step 8: Create `components/topic/ParentTips.tsx`**

```tsx
// boards/kids-world/src/components/topic/ParentTips.tsx

import { SectionHeader } from "../shared/SectionHeader";

type Props = { tips: string[]; locale: string };

export function ParentTips({ tips, locale }: Props) {
  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "家长提示" : "Parent prompts"} />
      <ul className="parent-tips">
        {tips.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </article>
  );
}
```

- [ ] **Step 9: Create `components/topic/RelatedTopics.tsx`**

从 TopicPage 行 663-671 提取：

```tsx
// boards/kids-world/src/components/topic/RelatedTopics.tsx

import type { ExplorationMap } from "../../types/world";
import { StatusPill } from "../shared/StatusPill";

type Props = { topics: string[]; map: ExplorationMap; locale: string };

export function RelatedTopics({ topics, map, locale }: Props) {
  return (
    <section className="related-strip">
      <strong>{locale === "zh-CN" ? "继续探索" : "Keep exploring"}</strong>
      <div className="tag-row">
        {topics.map((related) => (
          <em key={related}>{related}</em>
        ))}
      </div>
      <StatusPill status="building" map={map} />
    </section>
  );
}
```

- [ ] **Step 10: Commit**

```bash
git add boards/kids-world/src/components/topic/
git commit -m "refactor(kids-world): extract 9 topic section components"
```

---

### Task 2.3: HomePage 拆分 + TopicPage 瘦身

**Files:**
- Create: `boards/kids-world/src/components/home/HeroSection.tsx`
- Create: `boards/kids-world/src/components/home/InterestBand.tsx`
- Create: `boards/kids-world/src/components/home/WorldGrid.tsx`
- Create: `boards/kids-world/src/components/home/WorldTopicPanel.tsx`
- Create: `boards/kids-world/src/pages/HomePage.tsx`
- Create: `boards/kids-world/src/pages/TopicPage.tsx`

**Verify:** `npx tsc --noEmit` → no errors
**Depends on:** Task 2.1, Task 2.2

- [ ] **Step 1: Create `components/home/HeroSection.tsx`**

从 HomePage 行 411-435 提取：

```tsx
// boards/kids-world/src/components/home/HeroSection.tsx

import { BadgeCheck, BookOpen, Play } from "lucide-react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { GeneratedImage } from "../shared/GeneratedImage";

type Props = { map: ExplorationMap; locale: Locale };

export function HeroSection({ map, locale }: Props) {
  return (
    <section className="home-hero">
      <div>
        <p className="kicker">{locale === "zh-CN" ? "芋头宇宙" : "Yutou World"}</p>
        <h1>{map.homeHero.title}</h1>
        <p>{map.homeHero.childIntro}</p>
        <div className="hero-actions">
          <a className="primary-button" href="#worlds">
            <Play size={18} />
            {map.homeHero.primaryCTA}
          </a>
          <a className="secondary-button" href="#topics">
            <BadgeCheck size={18} />
            {map.homeHero.secondaryCTA}
          </a>
        </div>
      </div>
      <aside className="parent-note home-hero-visual">
        <GeneratedImage alt="" assetId="homepage-exploration-map-hero" className="home-hero-image" />
        <div>
          <BookOpen />
          <strong>{map.homeHero.subtitle}</strong>
          <span>{map.homeHero.parentIntro}</span>
        </div>
      </aside>
    </section>
  );
}
```

- [ ] **Step 2: Create `components/home/InterestBand.tsx`**

从 HomePage 行 437-453 提取：

```tsx
// boards/kids-world/src/components/home/InterestBand.tsx

import { Sparkles } from "lucide-react";
import type { World } from "../../types/world";
import { GeneratedImage } from "../shared/GeneratedImage";
import { SectionHeader } from "../shared/SectionHeader";
import { getExternalHref } from "../../lib/asset-resolve";
import { getTopicCardAssetId } from "../../lib/asset-map";

type Props = { world: World };

export function InterestBand({ world }: Props) {
  return (
    <section className="interest-band" id="topics">
      <SectionHeader title={world.entryCard.title} kicker={world.entryCard.badge}>
        {world.entryCard.subtitle}
      </SectionHeader>
      <div className="topic-card-grid animation-topics">
        {world.topicCards.map((topic) => (
          <a className="topic-card completed" href={getExternalHref(topic.href)} key={topic.id}>
            <GeneratedImage alt="" assetId={getTopicCardAssetId(topic)} className="topic-card-image" />
            <Sparkles />
            <strong>{topic.title}</strong>
            <span>{topic.cardDescription}</span>
            <div className="tag-row">{topic.learningGoalTags?.map((tag) => <em key={tag}>{tag}</em>)}</div>
            {topic.suggestedRoute && <small>{topic.suggestedRoute}</small>}
          </a>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Create `components/home/WorldGrid.tsx`**

从 HomePage 行 455-478 提取：

```tsx
// boards/kids-world/src/components/home/WorldGrid.tsx

import { CircleHelp } from "lucide-react";
import type { ExplorationMap, World } from "../../types/world";
import type { Locale } from "../../types/topic";
import { worldIcons } from "../../lib/world-icons";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  worlds: World[];
  selectedWorldId: string;
  onSelectWorld: (id: string) => void;
  map: ExplorationMap;
  locale: Locale;
};

export function WorldGrid({ worlds, selectedWorldId, onSelectWorld, map, locale }: Props) {
  return (
    <section className="worlds-section" id="worlds">
      <SectionHeader title={map.sections[1].title} kicker={locale === "zh-CN" ? "六大知识世界" : "Knowledge Worlds"}>
        {map.sections[1].description}
      </SectionHeader>
      <div className="world-grid">
        {worlds.map((world) => {
          const Icon = worldIcons[world.id as keyof typeof worldIcons] ?? CircleHelp;
          return (
            <button
              className={selectedWorldId === world.id ? "world-card active" : "world-card"}
              key={world.id}
              style={{ "--accent": world.recommendedColor.hex, "--soft": world.recommendedColor.softHex } as React.CSSProperties}
              type="button"
              onClick={() => onSelectWorld(world.id)}
            >
              <Icon />
              <span>{world.entryCard.badge}</span>
              <strong>{world.name}</strong>
              <small>{world.childOneLiner}</small>
            </button>
          );
        })}
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Create `components/home/WorldTopicPanel.tsx`**

从 HomePage 行 480-505 提取：

```tsx
// boards/kids-world/src/components/home/WorldTopicPanel.tsx

import { ChevronRight } from "lucide-react";
import type { ExplorationMap, World } from "../../types/world";
import type { Locale } from "../../types/topic";
import { GeneratedImage } from "../shared/GeneratedImage";
import { StatusPill } from "../shared/StatusPill";
import { SectionHeader } from "../shared/SectionHeader";
import { getTopicHref } from "../../lib/asset-resolve";
import { getKnowledgeTopicAssetId } from "../../lib/asset-map";
import { hasTopicData } from "../../data/loaders/load-topic";

type Props = { world: World; map: ExplorationMap; locale: Locale };

export function WorldTopicPanel({ world, map, locale }: Props) {
  return (
    <section className="selected-world-panel">
      <div>
        <SectionHeader title={world.name} kicker={world.entryCard.badge}>
          {world.parentNote}
        </SectionHeader>
      </div>
      <div className="topic-card-grid">
        {world.topicCards.map((topic) => {
          const topicHref = topic.slug && hasTopicData(topic.slug) ? getTopicHref(topic.slug) : undefined;
          return (
            <a className={`topic-card ${topic.status}`} href={topicHref ?? "#worlds"} key={topic.slug ?? topic.id}>
              <GeneratedImage alt="" assetId={getKnowledgeTopicAssetId(topic)} className="topic-card-image" />
              <StatusPill status={topic.status} map={map} />
              <strong>{topic.title}</strong>
              <span>{topic.cardDescription}</span>
              <div className="tag-row">{topic.learningGoalTags?.map((tag) => <em key={tag}>{tag}</em>)}</div>
              {topicHref && (
                <small className="open-topic">
                  {locale === "zh-CN" ? "打开看板" : "Open board"} <ChevronRight size={15} />
                </small>
              )}
            </a>
          );
        })}
      </div>
    </section>
  );
}
```

- [ ] **Step 5: Create `pages/HomePage.tsx`**

组合 4 个 home 子组件：

```tsx
// boards/kids-world/src/pages/HomePage.tsx

import { useState } from "react";
import type { ExplorationMap } from "../types/world";
import type { Locale } from "../types/topic";
import { HeroSection } from "../components/home/HeroSection";
import { InterestBand } from "../components/home/InterestBand";
import { WorldGrid } from "../components/home/WorldGrid";
import { WorldTopicPanel } from "../components/home/WorldTopicPanel";

type Props = { locale: Locale; map: ExplorationMap };

export function HomePage({ locale, map }: Props) {
  const [selectedWorldId, setSelectedWorldId] = useState("animation");
  const selectedWorld = map.worlds.find((world) => world.id === selectedWorldId) ?? map.worlds[0];
  const knowledgeWorlds = map.worlds.filter((world) => world.id !== "animation");
  const animationWorld = map.worlds.find((world) => world.id === "animation") ?? map.worlds[0];

  return (
    <main className="page-shell">
      <HeroSection map={map} locale={locale} />
      <InterestBand world={animationWorld} />
      <WorldGrid
        worlds={knowledgeWorlds}
        selectedWorldId={selectedWorldId}
        onSelectWorld={setSelectedWorldId}
        map={map}
        locale={locale}
      />
      <WorldTopicPanel world={selectedWorld} map={map} locale={locale} />
    </main>
  );
}
```

- [ ] **Step 6: Create `pages/TopicPage.tsx`**

组合 9 个 topic 子组件：

```tsx
// boards/kids-world/src/pages/TopicPage.tsx

import { ArrowLeft } from "lucide-react";
import type { ExplorationMap } from "../types/world";
import type { Locale, Topic } from "../types/topic";
import { getTopic } from "../data/loaders/load-topic";
import { SectionHeader } from "../components/shared/SectionHeader";
import { TopicHero } from "../components/topic/TopicHero";
import { ClassificationGroups } from "../components/topic/ClassificationGroups";
import { RepresentativeObjects } from "../components/topic/RepresentativeObjects";
import { MechanismSteps } from "../components/topic/MechanismSteps";
import { ComparePairs } from "../components/topic/ComparePairs";
import { ClickTaskCard } from "../components/topic/ClickTaskCard";
import { SpeakTemplates } from "../components/topic/SpeakTemplates";
import { ParentTips } from "../components/topic/ParentTips";
import { RelatedTopics } from "../components/topic/RelatedTopics";

type Props = { slug: string; locale: Locale; map: ExplorationMap };

export function TopicPage({ slug, locale, map }: Props) {
  const topic = getTopic(slug, locale);

  if (!topic) {
    return (
      <main className="page-shell topic-page">
        <a className="back-link" href="#">
          <ArrowLeft size={18} />
          {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
        </a>
        <p>Topic not found.</p>
      </main>
    );
  }

  return (
    <main className="page-shell topic-page">
      <a className="back-link" href="#">
        <ArrowLeft size={18} />
        {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
      </a>

      <TopicHero topic={topic} />

      <section className="content-grid">
        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "看一看主场景" : "Look at the scene"} kicker={topic.coreQuestion}>
            {topic.hero.sceneExplanation}
          </SectionHeader>
        </article>

        <ClassificationGroups
          groups={topic.classificationGroups}
          activeGroupId={topic.representativeObjects[0]?.groupId}
          locale={locale}
        />
        <RepresentativeObjects objects={topic.representativeObjects} locale={locale} />
        <MechanismSteps mechanism={topic.mechanism} secondary={topic.secondaryMechanism} locale={locale} />
        <ComparePairs pairs={topic.comparePairs} locale={locale} />

        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "点击任务" : "Tap tasks"} kicker={locale === "zh-CN" ? "不计分，多试几次" : "No score pressure"} />
          <div className="task-grid">
            {topic.clickTasks.map((task) => (
              <ClickTaskCard task={task} key={task.id} />
            ))}
          </div>
        </article>

        <SpeakTemplates templates={topic.speakTemplates} locale={locale} />
        <ParentTips tips={topic.parentTips} locale={locale} />
      </section>

      <RelatedTopics topics={topic.relatedTopics} map={map} locale={locale} />
    </main>
  );
}
```

注意：ClassificationGroups 的 `activeGroupId` 传入默认值（第一个 object 的 groupId），但实际高亮联动由 RepresentativeObjects 内部状态驱动。这保持了原始行为 — 原代码中 ClassificationGroups 的 active 状态也是由 `activeObject?.groupId` 决定的。后续如需跨组件联动可提升状态，但本次不改行为。

**修正**：原代码中 ClassificationGroups 的 active 状态确实依赖 TopicPage 级别的 `activeObjectId`。需要在 TopicPage 中保留该状态并传递下去：

```tsx
// 在 TopicPage 中添加状态：
import { useState } from "react";

// 在 TopicPage 函数体内：
const [activeObjectId, setActiveObjectId] = useState(topic.representativeObjects[0]?.id ?? "");
const activeObject = topic.representativeObjects.find((item) => item.id === activeObjectId) ?? topic.representativeObjects[0];
```

然后修改 ClassificationGroups 和 RepresentativeObjects 的调用：

```tsx
<ClassificationGroups
  groups={topic.classificationGroups}
  activeGroupId={activeObject?.groupId}
  locale={locale}
/>
<RepresentativeObjects
  objects={topic.representativeObjects}
  locale={locale}
  activeObjectId={activeObjectId}
  onSelectObject={setActiveObjectId}
/>
```

对应修改 RepresentativeObjects 为受控组件：

```tsx
// components/topic/RepresentativeObjects.tsx 改为受控模式
type Props = {
  objects: Topic["representativeObjects"];
  locale: string;
  activeObjectId: string;
  onSelectObject: (id: string) => void;
};

export function RepresentativeObjects({ objects, locale, activeObjectId, onSelectObject }: Props) {
  const activeObject = objects.find((item) => item.id === activeObjectId) ?? objects[0];
  // ... 其余不变，把 setActiveObjectId 替换为 onSelectObject
}
```

- [ ] **Step 7: Commit**

```bash
git add boards/kids-world/src/components/home/ boards/kids-world/src/pages/ boards/kids-world/src/components/topic/RepresentativeObjects.tsx
git commit -m "refactor(kids-world): extract HomePage and TopicPage with sub-components"
```

---

## Phase 3: 最终装配 — App.tsx 瘦身 + layout + 验证

### Task 3.1: Layout 组件 + 新 App.tsx

**Files:**
- Create: `boards/kids-world/src/components/layout/Topbar.tsx`
- Create: `boards/kids-world/src/components/layout/PageShell.tsx`
- Rewrite: `boards/kids-world/src/App.tsx`
- Modify: `boards/kids-world/src/main.tsx`（styles import 路径）

**Verify:** `npx tsc --noEmit && npm run dev` → 编译通过 + dev server 启动
**Depends on:** Task 2.3

- [ ] **Step 1: Create `components/layout/Topbar.tsx`**

从 App.tsx 行 768-793 提取：

```tsx
// boards/kids-world/src/components/layout/Topbar.tsx

import { useState } from "react";
import { Menu, Sparkles } from "lucide-react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { LocaleToggle } from "../shared/LocaleToggle";
import { getTopicHref } from "../../lib/asset-resolve";
import { getTopic } from "../../data/loaders/load-topic";
import registry from "../../data/topic-registry.json";

type Props = {
  map: ExplorationMap;
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
};

export function Topbar({ map, locale, onLocaleChange }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <header className="topbar">
      <a className="brand" href="#">
        <Sparkles />
        <span>
          <strong>{map.title}</strong>
          <small>{map.subtitle}</small>
        </span>
      </a>
      <button
        className="mobile-menu-button"
        type="button"
        aria-expanded={mobileNavOpen}
        aria-controls="topic-nav"
        onClick={() => setMobileNavOpen((open) => !open)}
      >
        <Menu size={18} />
        {locale === "zh-CN" ? "主题" : "Topics"}
      </button>
      <nav className={mobileNavOpen ? "open" : ""} id="topic-nav">
        {registry.firstBatch.slice(0, 3).map((topicSlug) => (
          <a href={getTopicHref(topicSlug)} key={topicSlug} onClick={() => setMobileNavOpen(false)}>
            {getTopic(topicSlug, locale)?.title}
          </a>
        ))}
      </nav>
      <LocaleToggle locale={locale} onChange={onLocaleChange} />
    </header>
  );
}
```

- [ ] **Step 2: Create `components/layout/PageShell.tsx`**

```tsx
// boards/kids-world/src/components/layout/PageShell.tsx

import type { ReactNode } from "react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { Topbar } from "./Topbar";

type Props = {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  map: ExplorationMap;
  children: ReactNode;
};

export function PageShell({ locale, onLocaleChange, map, children }: Props) {
  return (
    <div className="app-shell">
      <Topbar map={map} locale={locale} onLocaleChange={onLocaleChange} />
      {children}
    </div>
  );
}
```

- [ ] **Step 3: Rewrite App.tsx**

删除 App.tsx 全部内容，替换为：

```tsx
// boards/kids-world/src/App.tsx

import { useState } from "react";
import type { Locale } from "./types/topic";
import { useHashRoute } from "./hooks/use-hash-route";
import { getMap } from "./data/loaders/load-map";
import { PageShell } from "./components/layout/PageShell";
import { HomePage } from "./pages/HomePage";
import { TopicPage } from "./pages/TopicPage";

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

- [ ] **Step 4: Move styles.css + update main.tsx**

Move `src/styles.css` → `src/styles/styles.css`。

Update `main.tsx` 行 4：

```typescript
// before:
import "./styles.css";
// after:
import "./styles/styles.css";
```

- [ ] **Step 5: 验证编译 + dev server**

Run: `cd /Users/admin/Documents/kids-visual-learning-pack && npx tsc --noEmit 2>&1 | head -20`
Run: `npm run dev`
Expected: 编译通过，dev server 启动无错误

- [ ] **Step 6: Commit**

```bash
git add boards/kids-world/src/
git commit -m "refactor(kids-world): final assembly — App.tsx 25 lines, full directory structure"
```

---

### Task 3.2: 浏览器验证 + 清理

**Files:**
- Delete: 确认 App.tsx 中无残留代码
- Verify: 浏览器功能一致性

**Verify:** 浏览器手动验证 7 项 checklist 全通过
**Depends on:** Task 3.1

- [ ] **Step 1: 验证构建**

Run: `cd /Users/admin/Documents/kids-visual-learning-pack && npm run build 2>&1 | tail -10`
Expected: 构建成功

- [ ] **Step 2: 浏览器验证 checklist**

在 http://127.0.0.1:5174/ 逐项验证：

1. 根入口 → 自动跳转 kids-world
2. HomePage 7 个世界卡片显示正常
3. 世界切换 → topic 卡片列表更新
4. 点击 topic → hash 路由到 TopicPage
5. TopicPage 11 个模块按顺序渲染
6. ClickTask 三种类型（单选/多选/排序）交互正常
7. zh-CN ↔ en-US 切换正常

- [ ] **Step 3: 确认 App.tsx 行数**

Run: `wc -l boards/kids-world/src/App.tsx`
Expected: < 30 行

- [ ] **Step 4: 确认文件数量**

Run: `find boards/kids-world/src -name "*.ts" -o -name "*.tsx" | wc -l`
Expected: ~27 文件

- [ ] **Step 5: 最终 commit（如有微调）**

```bash
git add -A boards/kids-world/src/
git commit -m "refactor(kids-world): verify and clean up after restructure"
```

---

## Summary

| Phase | Tasks | 产出 |
|-------|-------|------|
| 1: 基础层 | 1.1-1.3 | types/ + lib/ + data/loaders/ + hooks/ |
| 2: 组件层 | 2.1-2.3 | components/shared/ + topic/ + home/ + pages/ |
| 3: 装配层 | 3.1-3.2 | layout/ + 新 App.tsx + 验证 |

每个 Phase 结束后编译验证。Phase 3 结束后浏览器全面验证。
