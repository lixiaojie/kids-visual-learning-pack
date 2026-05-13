# Kids Visual Learning Pack — Spec v1

> 基于 2026-05-11 代码扫描生成，用于跨模型校验和下一步规划。

## 1. 项目定位

面向 5-8 岁儿童 + 家长共读的多主题视觉学习看板集合。每个看板从一个动画 IP 或知识领域出发，用"认知-互动-表达"三段式引导孩子理解世界。

**目标用户**：学龄前/低年级儿童（主体验者）+ 家长（共读引导者）
**核心体验**：看图认知 → 点击互动 → 口头复述/创作

## 2. 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 构建 | Vite 5 | 多入口构建，`boards/*` 各自独立 |
| UI | React 18 + TypeScript | kids-world、paw-patrol 用 React；spider-verse 纯静态 |
| 样式 | 手写 CSS + Tailwind 基础 | 无 CSS-in-JS，CSS 变量做 design token |
| 字体 | Google Fonts: Baloo 2（display）+ Noto Sans SC（body） | 中英双语 |
| 图标 | Lucide React | 仅 paw-patrol 使用 |
| 状态 | React hooks（useState/useEffect） | 无全局状态库 |
| 路由 | Hash-based（kids-world）/ Tab 切换（paw-patrol）/ 锚点滚动（spider-verse） | 无 React Router |
| 持久化 | localStorage（paw-patrol 徽章） | 其余无持久化 |
| 部署 | Vercel（`scripts/build-vercel.sh`） | 相对路径 `base: "./"` |
| i18n | 自研 deep merge（zh-CN base + en-US overlay） | 仅 kids-world |

## 3. 项目结构

```
/
├── index.html                     # 根入口，自动跳转 kids-world
├── shared/styles/home.css         # 根页面样式
├── boards/
│   ├── kids-world/                # 芋头宇宙（主入口，React）
│   │   ├── index.html
│   │   ├── src/
│   │   │   ├── App.tsx            # 799 行，含所有组件+数据加载
│   │   │   ├── main.tsx
│   │   │   └── styles.css         # 946 行
│   │   └── public/assets/         # AI 生成图片（PNG+WebP 配对）
│   ├── paw-patrol/                # 汪汪队任务指挥中心（React）
│   │   ├── index.html
│   │   └── src/
│   │       ├── App.tsx            # 163 行，Tab 路由
│   │       ├── types.ts           # 5 实体类型
│   │       ├── components/        # 10 组件，共 803 行
│   │       ├── data/              # 5 数据文件，共 358 行
│   │       └── styles.css         # 1429 行
│   └── spider-verse/              # 蛛网亲子故事板（纯静态 HTML/CSS/JS）
│       ├── index.html             # 222 行，10 section + 附录
│       ├── script.js              # 549 行，全部数据+渲染+交互
│       ├── styles.css             # 1389 行
│       └── assets/                # AI 生成图片（50+ 素材）
├── scripts/
│   ├── build-vercel.sh
│   ├── deploy.sh
│   ├── check-image-assets.mjs     # PNG/WebP 配对校验
│   ├── import-kids-world-image-prompts.mjs
│   └── import-kids-world-generated-images.mjs
└── docs/
    ├── project-structure.md
    └── kids-world-image-generation-handoff.md
```

## 4. Board 详细 Spec

### 4.1 Kids World（芋头宇宙）

**技术**：React + TypeScript，单文件 App.tsx（799 行）
**路由**：`#topic/{slug}` hash 路由
**i18n**：zh-CN 基础 + en-US overlay，LocaleToggle 组件切换

#### 4.1.1 信息架构

**7 个世界**（1 动画入口 + 6 知识世界）：

| 世界 | 状态 | 色值 | 已有主题 | 规划中主题 |
|------|------|------|---------|-----------|
| 动画世界 | completed | #8B5CF6 紫 | spider-verse, paw-patrol | — |
| 生命世界 | building | #22C55E 绿 | animal-classification-tree, insects-and-spiders | plant-life-cycle |
| 身体世界 | building | #EF4444 红 | blood-cells-3d | digestion-journey |
| 地球世界 | building | #0EA5E9 蓝 | earth-climate-cities | water-cycle |
| 宇宙世界 | building | #4F46E5 靛 | solar-system-overview | moon-phases |
| 物质与能量世界 | comingSoon | #F97316 橙 | — | light-and-color, fission-fusion-kids |
| 人造系统世界 | building | #06B6D4 青 | llm-kids-basics | robot-sense-think-act |

**状态系统**：completed / building / comingSoon / planned

#### 4.1.2 Topic 数据模型

每个 topic 对应一个 `src/data/topics/{slug}.json`（10-16KB），结构：

```typescript
interface Topic {
  slug: string;
  title: string;
  subtitle: string;
  pageType: string;           // 页面布局类型
  coreQuestion: string;       // 核心问题（驱动整个 topic）
  learningGoals: string[];    // 学习目标
  relatedTopics: string[];    // 关联 topic
  hero: {
    title, kicker, lead, sceneExplanation,
    childPrompt, parentPrompt,
    placeholder?: { type, asset }
  };
  assets?: Record<string, { path, purpose?, status? }>;
  classificationGroups: Array<{
    id, name, childExplanation, parentNote?
  }>;
  representativeObjects: Array<{
    id, name, groupId, childExplanation, visualHint, commonMisread?
  }>;
  mechanism: {
    title?, steps: Array<{ id, shortTitle, childExplanation, parentNote? }>
  };
  secondaryMechanism?: { /* 同 mechanism */ };
  comparePairs: Array<{
    id, title,
    a: { name, points[] }, b: { name, points[] },
    childConclusion
  }>;
  clickTasks: ClickTask[];    // 3 种互动类型
  speakTemplates: string[];   // 口头表达模板
  parentTips: string[];       // 家长指导
}

type ClickTask = {
  type: "singleChoice" | "findTarget" | "sequenceClick";
  title, prompt?,
  options?, correctOptionId?, correctSequence?,
  targetIds?, decoyIds?,
  wrongHint?, successCopy?
};
```

**首批 6 个 P0 topic**：insects-and-spiders, animal-classification-tree, blood-cells-3d, solar-system-overview, earth-climate-cities, llm-kids-basics

#### 4.1.3 Topic 页面模块（从上到下）

1. **Hero** — 场景大图 + 核心问题 + 儿童/家长提示
2. **Scene Explanation** — 场景文字解读
3. **Classification Groups** — 分类卡片（2 列），点击切换
4. **Object Cards** — 代表性实体（4 列），点击展开详情
5. **Mechanism Steps** — "怎么工作的"流程（4 列，编号圆圈）
6. **Secondary Mechanism** — 可选第二流程
7. **Compare Pairs** — "容易搞混"对比（3 列，A vs B）
8. **Click Tasks** — 互动任务（2 列，含正确/错误反馈）
9. **Speak Templates** — 口头表达提示
10. **Parent Tips** — 家长指导清单
11. **Related Topics** — 相关 topic 标签条

#### 4.1.4 图片管线

- **Manifest**：`image-generation-manifest.json`（v2.1，43 个 asset）
- **格式**：PNG 原图（2048×1152 / 1024×1024）+ WebP 部署图
- **组件**：`GeneratedImage` 智能降级（WebP → PNG → CSS placeholder）
- **目录**：`public/assets/{world}/{topic}/` 按世界-主题分类

#### 4.1.5 组件树

```
App (hash router + locale)
├── Topbar (brand + mobile menu + topic nav + locale toggle)
├── HomePage
│   ├── HeroSection
│   ├── InterestBand (动画世界，2 列)
│   ├── WorldGrid (知识世界，3 列)
│   └── SelectedWorldPanel (动态 topic 卡片)
└── TopicPage
    ├── TopicHero + PlaceholderScene
    ├── ContentGrid (上述 11 个模块)
    └── ClickTaskCard (互动处理器)
```

---

### 4.2 Paw Patrol（汪汪队任务指挥中心）

**技术**：React + TypeScript，组件化架构
**路由**：Tab 切换（8 个 Tab），无 URL 路由
**持久化**：localStorage 存徽章解锁状态

#### 4.2.1 数据模型

```typescript
// 5 个实体类型
Character { id, nameZh, nameEn, role, shortRole, vehicle, tools[], strengths[], bestFor[], badgeId, colorHint, childIntro, parentNote }
Mission   { id, title, locationId, problemType, description, recommendedCharacterIds[], bestCharacterId, reason, wrongChoiceHint, badgeRewardId }
Badge     { id, name, meaning, childText, relatedCharacterIds[], icon }
Location  { id, name, description, commonProblems[], recommendedCharacterIds[], icon }
GearItem  { id, name, characterId, type: "vehicle"|"tool", functions[], bestForProblemTypes[] }
```

#### 4.2.2 功能模块（8 个 Tab）

| Tab | 组件 | 行数 | 功能 |
|-----|------|------|------|
| 首页 | HomeDashboard | 116 | 概览仪表盘，快捷入口，徽章进度 |
| 角色 | CharacterPanel | 103 | 角色卡片选择，详情展示（childIntro + parentNote） |
| 地图 | MapExplorer | 56 | 地点浏览，常见问题，推荐角色 |
| 装备 | GearWorkshop | 58 | 装备列表，按角色/类型筛选 |
| 任务 | MissionGame | 151 | 核心玩法：读任务描述 → 选角色 → 判定 best/helpful/try-again → 解锁徽章 |
| 流程 | FlowPanel | 71 | 任务解决流程可视化 |
| 复述 | StoryLab | 65 | 引导孩子用自己的话复述任务过程 |
| 徽章 | BadgePanel | 46 | 已解锁徽章展示 |

**家长说明**：ParentGuide 组件（70 行），侧栏 overlay，含重置功能

#### 4.2.3 核心交互：任务匹配游戏

```
读任务描述 → 选一个角色
  → bestCharacterId匹配 → "best" → 解锁 badge
  → recommendedCharacterIds匹配 → "helpful"（可再试）
  → 都不匹配 → "try-again" + wrongChoiceHint
→ 下一个任务（随机）
```

---

### 4.3 Spider-Verse（蛛网亲子故事板）

**技术**：纯静态 HTML + CSS + Vanilla JS（无框架）
**路由**：锚点滚动（#section-1 ~ #section-10 + #appendix）
**特色**：儿童/家长双模式切换 + A4 打印支持

#### 4.3.1 内容结构（10 个 Section + 附录）

| Section | 标题 | 内容 |
|---------|------|------|
| 封面 | 不止一个城市小英雄 | Hero 大图 + 关键词 |
| 01 角色阵容 | 先把朋友认清楚 | 8 个原创角色卡，点击展开家长讲解 |
| 02 关系图 | 故事不是一个人完成的 | 关系网（家人/朋友/导师/问题 4 类） |
| 03 能力图鉴 | 能力是解决问题的工具 | 8 种能力，点击查看用途+亲子问题 |
| 04 故事板一 | 从紧张到相信自己 | 12 格图，点击打开 modal（情绪+提问） |
| 05 故事板二 | 世界变大，选择也变难 | 12 格图，同上 |
| 06 问题角色 | 有情绪，也要做对选择 | 4 个角色："想要→做错→学到" |
| 07 多元地图 | 很多本不同风格的故事书 | 7 个世界概念 |
| 08 关键选择 | 成长就是遇到难选择 | 4 个天平（勇气/家人/规则/朋友） |
| 09 艺术实验室 | 像一本会动的漫画故事书 | 6 个视觉元素解读 |
| 10 创作卡 | 创造我的城市小英雄 | 表单（9 字段）+ 绘画区 |
| 附录 | 家长讲解附录 | 体验目标 + 讲解目标 + 素材替换说明 |

#### 4.3.2 数据规模

- **角色**：8 个（含属性、标签、childLine、parentNote）
- **关系**：7 条（含类型：family/friend/mentor/conflict/problem）
- **能力**：8 种
- **故事格**：24 格（2 段 × 12 格，每格含情绪标签+亲子问题）
- **问题角色**：4 个（情绪→行为→后果）
- **选择天平**：4 个
- **素材清单**：50 个 WebP（PNG/WebP 配对）

#### 4.3.3 交互特性

- **IntersectionObserver**：滚动进入视口时 reveal 动画 + 导航高亮
- **Story Modal**：点击故事格打开 dialog（图片+儿童文字+家长讲解+提问）
- **模式切换**：`data-mode="child|parent"`，CSS 控制 `.parent-note` 可见性
- **打印**：`window.print()` + 打印样式
- **重置**：清除所有互动状态
- **图片降级**：`img[data-fallback]` + error handler + `.is-missing` 样式

---

## 5. 跨 Board 共性

### 5.1 设计语言

| 属性 | 值 |
|------|---|
| 主字体 | Noto Sans SC（400-900） |
| 展示字体 | Baloo 2（600-800） |
| 背景色 | #fffaf0（cream） |
| 面板色 | rgba(255,255,255,0.9) |
| 主文字 | #172033 |
| 副文字 | #647085 |
| 圆角 | 12-16px |
| 阴影 | rgba(23,32,51,0.12) |

### 5.2 响应式策略

| 断点 | 栅格 | 导航 |
|------|------|------|
| >980px | 3-4 列 | 完整导航 |
| 640-980px | 2 列 | 折叠/hamburger |
| <640px | 1 列 | 全宽，紧凑内边距 |

### 5.3 儿童/家长双模式

三个 board 都有"双模式"概念，实现方式不同：
- **kids-world**：数据层分 childPrompt / parentPrompt，UI 同时渲染
- **paw-patrol**：ParentGuide 侧栏 overlay + 数据层 childIntro / parentNote
- **spider-verse**：CSS `data-mode` 控制 `.parent-note` 显示/隐藏

### 5.4 图片管线

- **格式**：PNG 原图 + WebP 部署图，页面引用 WebP
- **校验**：`scripts/check-image-assets.mjs` 检查配对完整性
- **降级**：WebP → PNG → CSS placeholder（kids-world 有 manifest 驱动；spider-verse 用 data-fallback）
- **构建**：Vercel 构建时从 dist 删除源 PNG

---

## 6. 完成度评估

| Board | 代码 | 数据 | 图片 | 交互 | i18n | 总评 |
|-------|------|------|------|------|------|------|
| spider-verse | 100% | 100% | ~80%（部分 WebP 缺配对） | 100% | — | **90% MVP 完成** |
| paw-patrol | 100% | 100% | 0%（纯图标，无生成图） | 100% | — | **95% MVP 完成** |
| kids-world 框架 | 100% | 100%（6 topic JSON） | ~50%（43 asset 约半数） | 90%（缺动画） | zh-CN 100% / en-US 部分 | **70% MVP** |
| kids-world 内容扩展 | — | 6/14 topic | — | — | — | **43% 内容覆盖** |

---

## 7. 已知问题 & 技术债

| # | 类型 | 描述 | 影响 |
|---|------|------|------|
| T1 | 架构 | kids-world App.tsx 799 行单文件，组件/数据/路由混在一起 | 可维护性，多人协作 |
| T2 | 架构 | spider-verse 纯静态 JS，数据硬编码在 script.js | 内容更新需改代码 |
| T3 | 一致性 | 三个 board 技术栈不统一（React×2 + 静态×1） | 共享组件困难 |
| T4 | 图片 | kids-world 图片约 50% 缺失，依赖 AI 生成补齐 | 视觉体验不完整 |
| T5 | 交互 | kids-world 无 CSS/JS 动画，页面切换生硬 | 儿童体验吸引力 |
| T6 | 可访问性 | 缺 ARIA live region（kids-world）、键盘导航不完整 | 辅助设备支持 |
| T7 | 性能 | spider-verse 预加载 50 张图片（preloadGeneratedAssets） | 首屏加载慢 |
| T8 | 测试 | 仅 spider-verse 有 structure.test.mjs，其余无测试 | 回归风险 |
| T9 | PWA | 无 Service Worker、无离线支持 | 弱网/离线不可用 |

---

## 8. 下一步规划

### Phase 1：稳固基础（1-2 天）

| 任务 | 优先级 | 说明 |
|------|--------|------|
| **P1.1** kids-world App.tsx 拆分 | P0 | 拆出 HomePage, TopicPage, GeneratedImage, ClickTaskCard 等独立文件 |
| **P1.2** 图片缺失审计 | P0 | 跑 check-image-assets.mjs，列出所有缺失 WebP，生成补图任务清单 |
| **P1.3** 响应式 QA | P1 | 三个 board 在 375/768/1280 三个宽度下验收 |

### Phase 2：体验提升（3-5 天）

| 任务 | 优先级 | 说明 |
|------|--------|------|
| **P2.1** 页面过渡动画 | P1 | kids-world topic 切换加 fade/slide，homepage 卡片加 stagger 入场 |
| **P2.2** Topic 页面动画 | P1 | classification 选中动效、mechanism 步骤进度动画、task 正确/错误反馈动画 |
| **P2.3** 补齐 kids-world 图片 | P0 | 用 image-generation-manifest.json 中的 prompt 批量生成剩余 ~20 张 |
| **P2.4** en-US overlay 补全 | P2 | 6 个 topic 的英文 overlay 补齐 |

### Phase 3：内容扩展（按需）

| 任务 | 说明 |
|------|------|
| **P3.1** 新增 topic：plant-life-cycle | 生命世界第 3 个 topic |
| **P3.2** 新增 topic：water-cycle | 地球世界第 2 个 topic |
| **P3.3** 新增 topic：digestion-journey | 身体世界第 2 个 topic |
| **P3.4** 物质与能量世界启动 | light-and-color 作为首个 topic |
| **P3.5** robot-sense-think-act | 人造系统世界第 2 个 topic |

### Phase 4：工程化（可选）

| 任务 | 说明 |
|------|------|
| **P4.1** 统一技术栈 | spider-verse 迁移到 React（复用 kids-world 组件） |
| **P4.2** 共享组件库 | 提取 shared/ 下的 React 组件（ImageWithFallback, ModeToggle, SectionHeader） |
| **P4.3** 测试覆盖 | 每个 board 加 structure test + 交互 test |
| **P4.4** PWA | Service Worker + 离线缓存，适合课堂/户外无网环境 |

---

## 9. 给校验模型的 Checklist

用这个 checklist 验证当前实现是否与 spec 一致：

- [ ] 根 index.html 自动跳转到 boards/kids-world/index.html
- [ ] kids-world 有 7 个世界（exploration-map.json），6 个已实现 topic
- [ ] kids-world topic 页面包含 11 个模块（hero → related strip）
- [ ] kids-world 支持 zh-CN / en-US 切换
- [ ] kids-world clickTask 有 3 种类型（singleChoice/findTarget/sequenceClick）
- [ ] paw-patrol 有 8 个 Tab，MissionGame 支持 best/helpful/try-again 三档判定
- [ ] paw-patrol 徽章持久化到 localStorage
- [ ] spider-verse 有 10 个 section + 附录
- [ ] spider-verse 支持儿童/家长模式切换 + 打印
- [ ] spider-verse story modal 展示 情绪+儿童文字+家长讲解+提问
- [ ] 所有 board 在 640px 以下单列布局
- [ ] 图片降级链：WebP → PNG → placeholder
