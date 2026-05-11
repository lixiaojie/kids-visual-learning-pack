# 儿童认知可视化项目架构审查报告 v1

> 依据《Kids Visual Learning Pack — Spec v1》审查。2026-05-11。

---

## 1. 总体结论

当前项目已完成 **从单页实验到多主题儿童认知可视化系统的第一阶段验证**。具备多 board 组织结构、多主题内容模型、儿童/家长共读体验、AI 图片生成管线、基础响应式、初步 i18n、可部署静态站点。

关键拐点：**如果继续直接扩 topic、补图、堆页面，会从"可用 MVP"变成"难维护内容工程"。**

下一阶段最重要的不是加新主题，而是 **架构收敛**：先把 kids-world 稳定为主框架，再沉淀跨 board 共性能力为 shared 层，最后再扩展主题和玩法。

---

## 2. 架构健康度评估

| 维度 | 当前状态 | 评价 | 优先级 |
|------|---------|------|--------|
| 产品定位 | 清晰：5-8 岁儿童 + 家长共读 | 很好 | P0 保持 |
| 内容模型 | kids-world topic schema 已接近可复用 | 较好 | P0 固化 |
| 页面架构 | kids-world 单文件过重（799 行） | 风险高 | P0 重构 |
| 技术栈 | React x2 + 静态 JS x1 | 短期可接受 | P1 收敛 |
| 图片管线 | 有 manifest、WebP/PNG、降级链 | 方向正确 | P0 工程化 |
| i18n | 自研 overlay，存在 ID/逻辑漂移风险 | 风险高 | P0 加校验 |
| 测试 | 仅 spider-verse 有 structure test | 回归风险 | P1 补基础 |
| 可访问性 | ARIA、键盘导航不足 | 中风险 | P1 改善 |
| 性能 | spider-verse 预加载 50 张图 | 中风险 | P1 优化 |
| PWA/离线 | 未建设 | 非当前核心 | P3 后置 |

---

## 3. 关键架构问题

### 3.1 kids-world App.tsx 799 行单文件

**问题本质**：边界未分层 — 路由/页面/数据加载/互动逻辑/i18n merge/图片 fallback 全部混在一起。

**风险**：每新增一个 topic 都增加 schema 兼容压力、overlay 漂移风险、图片引用错误风险、回归成本。

**建议**：立即拆分，搬家式重构，不改功能只改结构。

目标目录：
```
boards/kids-world/src/
├── App.tsx              # < 150 行，只做装配
├── routes/              # useHashRoute
├── pages/               # HomePage / TopicPage
├── components/
│   ├── layout/          # Topbar, PageShell
│   ├── home/            # HeroSection, WorldGrid, InterestBand, SelectedWorldPanel
│   ├── topic/           # 11 个模块各独立组件
│   └── media/           # GeneratedImage
├── features/            # locale, clickTask handler
├── data/                # loaders, registry
├── types/               # Topic, World, ClickTask, Assets
└── styles/              # tokens/layout/home/topic/interactions
```

### 3.2 topic schema 应升级为"内容协议"

topic 数据结构已经不只是页面数据，而是项目的 **内容生产协议**。应增加 JSON Schema + 校验脚本。

重点校验规则：

| 校验对象 | 规则 |
|---------|------|
| topic slug | 必须与文件名一致 |
| relatedTopics | 必须存在于 topic registry |
| classificationGroups.id | 不允许重复 |
| representativeObjects.groupId | 必须指向已有 group |
| clickTasks.type | 只能是 singleChoice/findTarget/sequenceClick |
| singleChoice.correctOptionId | 必须存在于 options |
| findTarget.targetIds/decoyIds | 必须指向合法 object |
| en-US overlay | 不允许修改 id/slug/type/correctOptionId/correctSequence/targetIds/decoyIds |
| assets.path | 必须能找到 WebP 或 PNG fallback |

### 3.3 i18n overlay 是高风险点

**问题**：内容身份与可见文案没有分层，英文 overlay 可能悄悄改 ID 或任务逻辑。

**建议**：定义 TRANSLATABLE_FIELDS 白名单（title/label/hint/copy 等可见文案）和 LOCKED_FIELDS 黑名单（id/slug/type/correctOptionId 等结构字段），校验脚本阻断违规。

### 3.4 跨 board 共性能力未沉淀 shared 层

三个 board 都有双模式、图片降级、卡片 UI、响应式，但实现各异。

**短期不迁移 spider-verse 到 React**（已 90% 完成，迁移收益低风险高）。

先抽 shared 层：
- `shared/styles/` — CSS tokens, cards, responsive, print
- `shared/components/react/` — ImageWithFallback, ModeToggle, SectionHeader
- `shared/components/vanilla/` — imageFallback.js, modeToggle.js
- `shared/schemas/` — image-asset.schema.json, board-meta.schema.json

### 3.5 图片管线应升级为生产流水线

当前有 manifest + 导入脚本 + 校验脚本，应补齐：
```
manifest 编写 → prompt pack 导出 → 批量生图 → 命名检查 → 导入 → WebP 转换 → 配对检查 → 缺图报告 → 页面引用校验
```

图片命名建议：`{world}/{topic}/{topic}__{module}__{asset-id}.webp`

---

## 4. 推荐分阶段路线

### Phase 0：冻结内容扩展

冻结：新 topic、新 board、大改版、spider-verse 迁移、新互动类型。
允许：缺图审计、schema 补全、组件拆分、i18n 修正、bug 修复。

### Phase 1：kids-world 结构重构（1-2 天）

| 任务 | 优先级 | 验收标准 |
|------|--------|---------|
| 拆 App.tsx | P0 | App.tsx < 150 行 |
| 拆 TopicPage 11 个模块 | P0 | 每个组件职责单一 |
| 拆 ClickTaskCard | P0 | 三类任务行为不变 |
| 拆 GeneratedImage | P0 | 降级链正常 |
| 拆 locale loader | P0 | 中英切换不变 |
| 拆 types | P0 | 无 any 扩散 |

### Phase 2：schema 与校验脚本（1-2 天）

| 任务 | 优先级 | 验收标准 |
|------|--------|---------|
| topic.schema.json | P0 | 6 个 topic 全通过 |
| overlay 锁字段校验 | P0 | 错误 overlay 被阻断 |
| relatedTopics 死链校验 | P1 | 不存在 slug 报错 |
| asset path 校验 | P1 | 缺图生成报告 |
| npm run validate | P1 | 一键校验 |

### Phase 3：shared 层收敛（2-3 天）

提取 CSS tokens、ImageWithFallback（React + vanilla）、SectionHeader、print.css。只抽最稳定最重复的。

### Phase 4：体验与性能优化（2-4 天）

页面过渡动画、ClickTask 反馈动画、mechanism 进度动画、spider-verse 图片懒加载、ARIA live region、键盘导航。

### Phase 5：内容扩展

完成 Phase 1-4 后按标准流程扩新 topic：
```
topic brief → topic JSON → schema validate → image manifest → prompt pack → batch generation → asset import → i18n overlay → visual QA → interaction QA
```

---

## 5. 不建议现在做的事

1. **不迁移 spider-verse 到 React** — 已 90% 完成，先抽 shared 能力再评估
2. **不新增大量 topic** — schema/i18n/图片管线未固化，会把技术债固化到更多内容里
3. **不引入复杂状态管理** — React hooks 足够，真正需要的是文件结构清晰 + schema 校验严格

---

## 6. 验收标准

### 代码结构
- App.tsx < 150 行
- 11 个 topic 模块均为独立组件
- ClickTask 三种类型有独立 handler
- locale merge 不在组件内
- styles 拆成 tokens/layout/home/topic/interactions

### 内容协议
- 所有 topic JSON 通过 schema
- overlay 锁字段校验通过
- relatedTopics 无死链
- clickTask 正确答案引用合法
- representativeObjects.groupId 合法

### 图片管线
- manifest 每个 asset 有明确 status
- 缺图能生成报告
- 页面引用都能找到 WebP 或 PNG
- 构建后不含源 PNG

### 体验
- 375/768/1280 三宽度可用
- topic 切换不卡
- 互动反馈明确
- 弱网/缺图仍可理解

### 回归
- 根入口跳转正常
- kids-world 7 世界 + 6 topic 正常
- zh-CN/en-US 切换正常
- paw-patrol 8 Tab + MissionGame 正常
- spider-verse modal/模式切换/打印正常

---

## 7. 一句话建议

> 把 kids-world 从"一个能跑的 React 页面"升级成"可批量生产儿童认知主题的内容渲染系统"；把 schema、i18n、图片管线和 shared 组件先固化，再扩展更多主题。
