# 项目结构说明

这个项目现在按“多主题可视化看板”组织。根目录负责总入口，每个具体主题放在 `boards/` 下。

```text
.
├── index.html                  # 所有看板的入口页
├── README.md                   # 项目总说明
├── boards/
│   ├── spider-verse/           # 蜘蛛宇宙视觉学习包
│   │   ├── index.html
│   │   ├── styles.css
│   │   ├── script.js
│   │   └── structure.test.mjs
│   └── paw-patrol/             # 汪汪队视觉学习包占位
│       ├── index.html
│       ├── README.md
│       └── src/                # React + TypeScript 任务指挥中心
├── shared/
│   └── styles/
│       └── home.css            # 根入口页样式
└── docs/
    └── project-structure.md    # 本文档
```

## 新增一个主题看板

1. 在 `boards/` 下创建主题目录，例如 `boards/dinosaur/`。
2. 放入该主题自己的 `index.html`、`styles.css`、`script.js`。
3. 在根目录 `index.html` 的 `.board-grid` 中增加一张入口卡。
4. 如果出现跨主题复用的资源，再移动到 `shared/`。

## 汪汪队任务指挥中心

`boards/paw-patrol/` 使用 Vite + React + TypeScript 实现，数据放在 `src/data/`，页面组件放在 `src/components/`。本主题不包含官方图片、Logo、剧照或品牌素材，只使用原创 UI、图标和文字信息。

## 蜘蛛宇宙视觉故事板

`boards/spider-verse/` 是纯静态 HTML / CSS / JS 页面，包含 10 张主卡和 2 个家长附录。`structure.test.mjs` 用来检查主卡数量、附录、导航、打印按钮和可点击讲解入口是否齐全。

## 命名建议

- 目录名使用英文短横线：`spider-verse`、`paw-patrol`。
- 页面标题和卡片内容使用中文，适合孩子和家长阅读。
- 每个看板尽量自包含，避免不同主题互相依赖。
