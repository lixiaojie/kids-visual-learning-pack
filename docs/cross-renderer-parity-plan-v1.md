# 跨渲染器完整度对齐方案 v1

> 日期：2026-05-14
> 适用：芋头宇宙 EdgeOne H5 + Taro 微信小程序
> 决策：13 个 render-ready topic 在两端对齐，spider-verse + paw-patrol 仅 EdgeOne 保留
> 基线：`packages/kids-content` 已成为唯一内容源（alignment v1 P0 完成）

---

## 1. 对齐原则

```
内容源对齐（topic 数据）→ 渲染完整度对齐（每个模块都渲染）→ 交互完整度对齐（每个模块的体验深度）
```

| 层 | 对齐策略 |
|---|---|
| **内容对齐** | 13 个 render-ready topic 两端可见；spider-verse / paw-patrol 仅 web |
| **渲染完整度** | 11 个模块两端均渲染，无 slice 限制 |
| **交互完整度** | Web 是基线，小程序简化但不丢失核心教育内容 |

---

## 2. Topic 渠道矩阵

| 类别 | EdgeOne H5 | 小程序 | 说明 |
|---|:---:|:---:|---|
| 13 render-ready topics | ✅ | ✅ | 两端对齐 |
| spider-verse | ✅ | ❌ | IP 风险，仅 web preview/production |
| paw-patrol | ✅ | ❌ | IP 风险，仅 web preview/production |
| 5 planned topics | preview only | ❌ | 待 render-ready 后再开放 |

**channel-policy.json 当前状态**（已对齐）：

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
      "animal-classification-tree", "blood-cells-3d", "cicada-life",
      "digestion", "dinosaurs", "earth-climate-cities", "ecosystem",
      "insects-and-spiders", "llm-kids-basics", "moon-phases",
      "robots", "solar-system-overview", "water-cycle"
    ]
  }
}
```

---

## 3. 当前实际渲染完整度（2026-05-14 verified）

读 `apps/miniprogram/src/pages/topic/index.tsx` 实际状态：**全部 11 模块已渲染，无 slice 限制**。alignment spec v1 section 6.2 描述的"前 5 / 前 4 / 前 3"已被 codex 修正掉。

| Topic 模块 | EdgeOne 渲染方式 | 小程序渲染方式 | 渲染完整度 | 交互完整度 |
|---|---|---|:---:|:---:|
| TopicHero | 独立组件 + PlaceholderScene | View + 4 个 Text + GeneratedImage | ✅ | ✅ |
| Scene Explanation | SectionHeader + 文字 | section + section-body | ✅ | ✅ |
| ClassificationGroups | **独立组件**，2 列卡片，与 RepresentativeObjects 联动高亮 | InfoList 静态卡 | ✅ | ⚠️ 缺联动 |
| RepresentativeObjects | **独立组件**，4 列卡片 + 点击展开 detail（受控状态） | InfoList 静态卡 | ✅ | ⚠️ 缺点击展开 |
| MechanismSteps | step-card 4 列编号圆圈 | step + step-title + body 列表 | ✅ | ✅ |
| SecondaryMechanism | 同 MechanismSteps（条件渲染） | 同上 | ✅ | ✅ |
| ComparePairs | compare-card 3 列 A vs B + childConclusion | InfoList 仅显示 title + childConclusion | ✅ | ⚠️ 丢 a/b points |
| ClickTaskCard | **完整三类型** handler | 需确认三类型在小程序的实现 | ✅ | ❓ 待验证 |
| SpeakTemplates | 独立组件 | 通过 TopicSummary 渲染 | ✅ | ✅ |
| ParentTips | 独立组件 + 列表 | InfoList 渲染 | ✅ | ✅ |
| RelatedTopics | 标签条 + StatusPill | Navigator 列表 | ✅ | ✅ |

---

## 4. 待对齐工作（按优先级）

### P0：交互核心保真

#### P0-1 验证 ClickTaskCard 三类型在小程序的实现

`apps/miniprogram/src/components/topic/ClickTaskCard.tsx` 必须正确处理：
- `singleChoice` — 选项点击 + correct/wrong 反馈
- `findTarget` — 多 target 收集 + decoy 拒绝
- `sequenceClick` — 顺序匹配，错一步重置

**验收**：cicada-life 的 4 个任务在微信开发者工具中完整可玩。

#### P0-2 ComparePairs 补齐 a / b 的 points 列表

当前小程序只渲染 `pair.title` + `pair.childConclusion`，丢失了 `a.points[]` / `b.points[]`（具体差异点）。

**修复**：把 InfoList 替换为专用 ComparePairCard 组件，或扩展 InfoList 支持双栏。

**影响 topic**：所有有 comparePairs 的 13 个 topic（如 blood-cells-3d 红细胞 vs 白细胞、cicada-life 蝉 vs 蝴蝶）。

### P1：交互体验提升

#### P1-1 RepresentativeObjects 加点击展开 detail

Web 端：点击对象卡 → 展开 `childExplanation` + `commonMisread` 详细文案。
小程序当前：直接全显示在 InfoList 中。

**决策选项**：
- A. 保持小程序全显示（无交互成本，但信息密度高）
- B. 加点击展开（与 web 对齐，但需要新组件）

**推荐 A**：移动端纵向滑动天然支持长列表，点击展开反而增加操作成本。在 spec 文档中**正式记录这个决策**：representativeObjects 的小程序简化为静态全展开，不视为交互降级。

#### P1-2 ClassificationGroups 加 active 联动高亮

Web 端：当前 active 的 representativeObject 的 groupId 会在 ClassificationGroups 高亮。
小程序当前：两个组件独立 InfoList，无联动。

**决策**：与 P1-1 同步处理。如果选 A（小程序静态展开），联动高亮自然不需要。如果选 B（点击展开），则补上联动。

### P2：视觉一致性

#### P2-1 11 模块视觉调性对齐

小程序当前用 InfoList 统一样式，Web 11 个模块各有独特视觉（compare-card 双栏 / step-card 编号圆圈 / object-card DNA 图标）。

**目标**：小程序保持简化但不平庸——至少 mechanism step 加编号、compare 加双栏、object 加图标。

**不在本期**：完全的视觉对齐（CSS 拆分 + design token 共享）需要 P3 工程化阶段。

---

## 5. 实施任务包

### Wave 1：P0（必做，本期）

| Task | 文件 | 验收 |
|---|---|---|
| W1.1 验证 ClickTaskCard 小程序三类型 | `apps/miniprogram/src/components/topic/ClickTaskCard.tsx` | 微信开发者工具手动跑 cicada-life 4 任务全过 |
| W1.2 ComparePairs 补 a/b points | 新增 `apps/miniprogram/src/components/topic/ComparePairCard.tsx`，替换 topic page 的 InfoList | a/b name + points + childConclusion 全部渲染 |
| W1.3 alignment 校验脚本扩展 | `scripts/validate-content-alignment.mjs` 增加：comparePairs.a/b.points 在小程序渲染路径中存在 | npm run validate 全绿 |

### Wave 2：P1（决策后做）

| Task | 决策依赖 |
|---|---|
| W2.1 RepresentativeObjects 交互方案 | 用户决策 A/B 后实施 |
| W2.2 ClassificationGroups 联动 | 跟随 W2.1 |
| W2.3 决策结果写入 cross-renderer-decisions.md | 文档归档 |

### Wave 3：P2（后续）

| Task | 时机 |
|---|---|
| W3.1 mechanism step 编号圆圈 | 视觉提升期 |
| W3.2 object card DNA 图标 | 视觉提升期 |
| W3.3 compare 双栏样式 | 跟随 W1.2 |

---

## 6. alignment 校验脚本扩展

当前 `scripts/validate-content-alignment.mjs` 检查：
- render-ready ↔ miniprogram.visibleTopics 一致
- topic 在 packages/kids-content 中有 import
- 图片 manifest 引用合法

**本期新增**：

```javascript
// 渲染完整度检查
const RENDERED_FIELDS_IN_MINIPROGRAM = [
  "hero.title", "hero.kicker", "hero.lead", "hero.sceneExplanation",
  "classificationGroups[].name", "classificationGroups[].childExplanation",
  "representativeObjects[].name", "representativeObjects[].childExplanation",
  "mechanism.steps[].shortTitle", "mechanism.steps[].childExplanation",
  "secondaryMechanism.steps[].shortTitle",
  "comparePairs[].title", "comparePairs[].a.name", "comparePairs[].a.points",
  "comparePairs[].b.name", "comparePairs[].b.points", "comparePairs[].childConclusion",
  "clickTasks[].title", "clickTasks[].prompt", "clickTasks[].options",
  "speakTemplates", "parentTips", "relatedTopics"
];

// 对每个 render-ready topic：
//   读 topic JSON
//   读 apps/miniprogram/src/pages/topic/index.tsx
//   静态分析：每个 RENDERED_FIELDS_IN_MINIPROGRAM 是否有渲染路径
//   缺失则报错
```

**降低实现成本的版本**：先做"组件覆盖检查"——topic page 必须 import 并使用：
- `<ClickTaskCard>` for clickTasks
- `<ComparePairCard>` for comparePairs（W1.2 引入）
- `<MechanismSteps>` for mechanism / secondaryMechanism
- `<InfoList>` for classificationGroups / representativeObjects / parentTips

如果有 topic 引用了字段但页面里没有对应组件，报错。

---

## 7. 验收标准

### 7.1 内容渠道对齐

- [x] 13 个 render-ready topic 在 web-production 和 miniprogram 都可见
- [x] spider-verse / paw-patrol 不在 miniprogram visibleTopics
- [x] channel-policy 单一数据源，渲染器都从 packages 读取
- [x] `npm run validate` 含 alignment check

### 7.2 渲染完整度

- [x] 11 模块在小程序全部有渲染路径，无 `.slice(...)` 限制
- [ ] **W1.2** ComparePairs 的 a.points / b.points 在小程序渲染
- [ ] **W1.3** alignment 校验脚本捕获渲染丢失

### 7.3 交互完整度

- [ ] **W1.1** 三种 ClickTask 类型在小程序完整可玩（cicada-life 4 任务为样板）
- [ ] **W2** 决策：RepresentativeObjects/ClassificationGroups 是否需要点击交互（A/B 选择）
- [ ] 决策结果归档为 `docs/cross-renderer-decisions.md`

---

## 8. 当前实际状态（基线）

| 项 | 状态 | 备注 |
|---|---|---|
| 13 render-ready topics | ✅ | 含 cicada-life |
| 内容渠道对齐 | ✅ | channel-policy 单源 |
| 11 模块小程序渲染 | ✅ | 已无 slice 限制 |
| ComparePairs 完整 a/b | ❌ | InfoList 仅渲染 title + childConclusion |
| ClickTask 三类型小程序 | ❓ | 待 W1.1 验证 |
| RepresentativeObjects 交互 | 简化（静态全展开） | 待 W2 决策是否补齐 |
| ClassificationGroups 联动 | 简化（静态独立） | 跟随 W2 |
| Validate suite | ✅ | 7 个子检查全绿 |

---

## 9. 下一步建议

1. **本期立即做**：W1.1（验证）+ W1.2（ComparePairs 补齐）+ W1.3（校验脚本）
2. **决策**：W2 的 RepresentativeObjects 交互方案，推荐 A（移动端静态全展开）
3. **归档**：决策写入 `docs/cross-renderer-decisions.md`，作为后续 topic 的渲染规范
4. **远期**：P2 视觉一致性 + P3 工程化（design token 跨端共享）

不阻塞本期发布的内容扩展（剩余 5 planned topic 可继续按 cicada-life 模板生产）。
