# 项目结构说明

这个项目现在按“最高层探索地图 + 多主题可视化看板”组织。根目录负责进入“芋头世界”，每个具体主题放在 `boards/` 下。

```text
.
├── index.html                  # 所有看板的入口页
├── README.md                   # 项目总说明
├── boards/
│   ├── kids-world/            # 芋头世界，最高层入口
│   │   ├── index.html
│   │   ├── structure.test.mjs
│   │   └── src/               # React + TypeScript 数据驱动看板
│   ├── spider-verse/           # 蜘蛛宇宙视觉学习包
│   │   ├── assets/             # 批量生成图片素材
│   │   ├── index.html
│   │   ├── styles.css
│   │   ├── script.js
│   │   └── structure.test.mjs
│   └── paw-patrol/             # 汪汪队任务指挥中心
│       ├── index.html
│       ├── README.md
│       └── src/                # React + TypeScript 任务指挥中心
├── shared/
│   └── styles/
│       └── home.css            # 根入口页样式
└── docs/
    └── project-structure.md    # 本文档
```

## 最高层探索地图

`boards/kids-world/` 是当前最高层入口，数据放在 `src/data/`。它使用 `exploration-map.json` 组织动画世界和六大知识世界，使用 `topic-registry.json` 管理首批主题，使用 `data/locales/en-US/` 作为英文 overlay。

已完成的 `spider-verse` 和 `paw-patrol` 不再是孤立入口，而是挂在“动画世界”下的已点亮主题。

## 新增一个独立主题看板

1. 在 `boards/` 下创建主题目录，例如 `boards/dinosaur/`。
2. 放入该主题自己的 `index.html`、`styles.css`、`script.js`。
3. 在根目录 `index.html` 的 `.board-grid` 中增加一张入口卡。
4. 如果出现跨主题复用的资源，再移动到 `shared/`。

## 汪汪队任务指挥中心

`boards/paw-patrol/` 使用 Vite + React + TypeScript 实现，数据放在 `src/data/`，页面组件放在 `src/components/`。本主题不包含官方图片、Logo、剧照或品牌素材，只使用原创 UI、图标和文字信息。

## 蜘蛛宇宙视觉故事板

`boards/spider-verse/` 是纯静态 HTML / CSS / JS 页面，包含 10 个视觉模块和家长讲解附录。图片素材按 `assets/cast`、`assets/characters`、`assets/relationships`、`assets/story-01`、`assets/story-02`、`assets/boards` 分类放置。每张正式素材保留同名 `.png` 原图和 `.webp` 部署图；页面引用 `.webp`，构建到 `dist/` 时排除 `.png` 以控制体积。`structure.test.mjs` 用来检查模块数量、附录、导航、打印按钮、素材路径、PNG/WebP 配对和可点击讲解入口是否齐全。

全项目图片素材规则由 `scripts/check-image-assets.mjs` 统一检查：`boards/**/assets/` 下的正式图片需要保存同名 `.png` 原图和 `.webp` 部署图；Vercel 构建会先执行该检查，再从 `dist/boards/**/assets/` 删除源 PNG。

## 命名建议

- 目录名使用英文短横线：`spider-verse`、`paw-patrol`。
- 页面标题和卡片内容使用中文，适合孩子和家长阅读。
- 每个看板尽量自包含，避免不同主题互相依赖。
