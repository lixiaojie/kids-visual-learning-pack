# 芋头宇宙专题项目规划 Spec：蝉的一生 v1.1

> 修订日期：2026-05-14
> v1.0 → v1.1 修正：基于实际框架现状校正三处偏离，删除自创字段，统一用现有 schema。
> 当前状态：cicada-life 已 render-ready 落地，本文档作为后续 observation-template 模板的样板归档。

---

## 0. v1.1 修正点

| # | v1.0 提案 | 实际框架现状 | v1.1 处理 |
|---|---|---|---|
| 1 | 5 页多页结构（`pages` 数组） | 当前 TopicPage 是单页 11 模块结构，无多页路由 | **删除 `pages` 字段**，把 5 页内容映射到 11 模块 |
| 2 | `pageType: "lifecycle-observation-task"` 新值 | 渲染器不消费此字段，dead field | 改用现有 enum：`classification-compare-task` |
| 3 | clickTask types：`sequence/choose/identify/compare` | schema 标准类型：`sequenceClick/singleChoice/findTarget` | **任务类型改为标准枚举** |

不变：
- `observationContext` 新字段 — 已成功扩展 schema 接受
- `cognitiveFocus` 新字段 — 同上
- 其余 11 模块结构、内容边界、安全提示、亲子任务全部保留

---

## 1. 专题定位

### 1.1 推荐定位

```
主专题：蝉的一生
专题类型：自然观察 + 生命周期 + 变态发育 + 分类比较
核心对象：黑蚱蝉若虫 / cicada nymph
认知路径：真实发现 → 观察提问 → 生命周期 → 羽化机制 → 昆虫变化方式比较 → 亲子观察任务
```

不是百科页，是 **"真实生活触发 → 儿童认知地图"** 的观察型专题。

### 1.2 核心儿童问题

> **这只从土里爬出来的小虫，为什么急着往树上爬？**

引出：它是谁 / 它从哪里来 / 它要做什么 / 它会变成什么 / 它和蝴蝶有什么不同。

---

## 2. 科学内容边界

### 2.1 必须准确表达的科学事实

1. 蝉是昆虫
2. 蝉的一生：**卵 → 若虫 → 成虫**
3. 蝉是 **不完全变态**，没有蝴蝶那样的蛹阶段
4. 蝉若虫主要在地下生活，吸食植物根部汁液
5. 成熟若虫从土里爬出，找垂直表面进行最后一次蜕皮 / 羽化
6. 羽化时旧外骨骼裂开，新成虫从壳里出来；翅膀需展开变硬
7. 成虫鸣叫、交配、产卵，卵产在树枝内，新若虫落地入土，循环继续

### 2.2 不强调

- 黑蚱蝉具体分类学
- 不同蝉种 2/3/13/17 年生命周期差异
- 口器、木质部汁液、生态营养循环
- 蝉灾、树木损伤、寄生真菌

### 2.3 参考依据

- Smithsonian National Museum of Natural History — periodical cicadas
- Clemson Extension — cicada lifecycle
- ASU Ask A Biologist — cicada life cycle

---

## 3. 与芋头宇宙整体框架的关系

### 3.1 框架契合点

直接复用现有 11 模块结构：

```
hero / classificationGroups / representativeObjects / mechanism /
secondaryMechanism / comparePairs / clickTasks / speakTemplates /
parentTips / relatedTopics
```

### 3.2 反向推动的框架补强

#### A. `observationContext`

承载真实观察触发源：

```json
"observationContext": {
  "source": "real-world-observation",
  "scene": "mountain trail at dusk",
  "trigger": "发现一只刚从土里爬出来、正在找地方羽化的黑蚱蝉若虫",
  "season": "summer",
  "safetyNote": "保持安静观察，不要触碰，不要打扰羽化过程"
}
```

价值：让芋头宇宙区别于普通百科卡，形成"真实生活 → 认知地图"的产品特征。

#### B. `cognitiveFocus`

声明专题的认知类型：

```json
"cognitiveFocus": [
  "life-cycle",
  "metamorphosis",
  "classification",
  "field-observation",
  "comparison"
]
```

价值：后续可用于自动选择页面模板 / 任务类型 / 生图模板 / parent tips 风格。

---

## 4. 内容如何映射到 11 模块（替代 v1.0 的 pages 多页结构）

v1.0 提议 5 页结构，但当前框架是单页 11 模块。映射如下：

| v1.0 页 | v1.1 映射到 |
|---|---|
| Page 1 发现页 / Hero | **hero** + `observationContext`（真实场景触发） |
| Page 2 生命周期页 | **mechanism**（卵→若虫→成虫 6 步） |
| Page 3 羽化机制页 | **secondaryMechanism**（"为什么爬到树干"） |
| Page 4 比较页 | **comparePairs**（蝉 vs 蝴蝶 / 蝉 vs 蜻蜓 / 若虫 vs 成虫） |
| Page 5 任务页 | **clickTasks** + **parentTips** + **speakTemplates** |

`representativeObjects` 承载视觉对象清单（蝉卵 / 地下若虫 / 出土若虫 / 树干 / 蝉蜕 / 刚羽化的蝉 / 成虫），由前端按需渲染。

`classificationGroups` 承载分类骨架（昆虫层级 / 变态类型 2 类），与 `comparePairs` 配合形成完整分类对比。

---

## 5. 互动任务配置（v1.1 修正：用标准 schema 类型）

### 5.1 任务一：生命周期排序（type=`sequenceClick`）

```json
{
  "id": "cicada-sequence-01",
  "type": "sequenceClick",
  "title": "给蝉的一生排排队",
  "prompt": "把下面几个阶段按正确顺序排好",
  "options": [
    { "id": "egg",        "label": "卵" },
    { "id": "underground","label": "地下若虫" },
    { "id": "emerging",   "label": "出土若虫" },
    { "id": "molting",    "label": "羽化" },
    { "id": "adult",      "label": "成虫" }
  ],
  "correctSequence": ["egg", "underground", "emerging", "molting", "adult"],
  "successCopy": "排对啦！蝉先从卵开始，再在地下长大，最后羽化成会飞的成虫。",
  "wrongHint": "想一想：蝉会先住在地下，还是先飞起来呢？"
}
```

### 5.2 任务二：选择羽化位置（type=`singleChoice`）

```json
{
  "id": "cicada-choice-01",
  "type": "singleChoice",
  "title": "帮若虫找个好地方",
  "prompt": "若虫刚从土里出来，它最适合爬到哪里羽化？",
  "options": [
    { "id": "trunk",      "label": "树干" },
    { "id": "mud",        "label": "泥地" },
    { "id": "puddle",     "label": "水坑" },
    { "id": "leaf-back",  "label": "草叶背面" }
  ],
  "correctOptionId": "trunk",
  "successCopy": "答对了！树干这样的垂直表面更适合若虫固定身体，完成羽化。",
  "wrongHint": "想一想：羽化时它需要一个稳稳的支撑点。"
}
```

### 5.3 任务三：找蝉蜕（type=`findTarget`）

```json
{
  "id": "cicada-identify-01",
  "type": "findTarget",
  "title": "找找蝉蜕",
  "prompt": "找出树干上那个空空的外壳",
  "targetIds": ["shed-shell"],
  "decoyIds": ["live-cicada", "leaf", "bark-pattern"],
  "successCopy": "找到了！蝉蜕是若虫羽化后留下来的旧外壳。",
  "wrongHint": "蝉蜕像一只空空的小壳，常常贴在树干上。"
}
```

### 5.4 任务四：谁有蛹（type=`singleChoice`）

```json
{
  "id": "cicada-compare-01",
  "type": "singleChoice",
  "title": "谁会经过蛹",
  "prompt": "下面谁会经过\"蛹\"这个阶段？",
  "options": [
    { "id": "cicada",    "label": "蝉" },
    { "id": "butterfly", "label": "蝴蝶" },
    { "id": "dragonfly", "label": "蜻蜓" }
  ],
  "correctOptionId": "butterfly",
  "successCopy": "答对了！蝴蝶会经过蛹，蝉不会。",
  "wrongHint": "想一想毛毛虫会先变成什么，再变成蝴蝶。"
}
```

---

## 6. Topic JSON 草案（v1.1 实际可落地版）

路径：`boards/kids-world/src/data/topics/cicada-life.json`

关键字段值（不再列全文，强调与 v1.0 的差异）：

```json
{
  "slug": "cicada-life",
  "world": "life",
  "priority": "P0",
  "pageType": "classification-compare-task",
  "status": "render-ready",
  "observationContext": { /* 见 §3.2.A */ },
  "cognitiveFocus": [ /* 见 §3.2.B */ ],
  "hero": {
    "title": "昨天我们遇见了谁？",
    "kicker": "真实观察",
    "lead": "夏天傍晚的山路上，发现一只刚从土里爬出来、正在找地方羽化的小虫。",
    "sceneExplanation": "...",
    "childPrompt": "它从哪里来？要去哪里？",
    "parentPrompt": "保持安静，不要触碰羽化过程"
  },
  "classificationGroups": [
    { "id": "insect-basic",       "name": "它属于哪一类",   "childExplanation": "..." },
    { "id": "metamorphosis-type", "name": "变化方式",     "childExplanation": "..." }
  ],
  "representativeObjects": [
    /* 7 个：蝉卵 / 地下若虫 / 出土若虫 / 树干 / 蝉蜕 / 刚羽化的蝉 / 成虫
       每个含 id, name, groupId, childExplanation, visualHint */
  ],
  "mechanism": {
    "title": "蝉如何长大",
    "steps": [ /* 6 步：卵→入土→长大→爬出→羽化→成虫 */ ]
  },
  "secondaryMechanism": {
    "title": "为什么若虫要爬上树",
    "steps": [ /* 3 步：固定身体 / 翅膀展开 / 身体变硬 */ ]
  },
  "comparePairs": [
    { "id": "compare-cicada-butterfly", "title": "蝉 vs 蝴蝶",
      "a": { "name": "蝉",   "points": ["卵→若虫→成虫", "没有蛹"] },
      "b": { "name": "蝴蝶", "points": ["卵→幼虫→蛹→成虫", "有蛹"] },
      "childConclusion": "蝴蝶有蛹，蝉没有。" }
    /* + compare-cicada-dragonfly + compare-nymph-adult */
  ],
  "clickTasks": [ /* 4 个，见 §5 */ ],
  "speakTemplates": [ /* 5 条 */ ],
  "parentTips": [ /* 4 条 */ ],
  "relatedTopics": ["insects-and-spiders", "ecosystem"]
}
```

**v1.0 → v1.1 删除**：
- ❌ `pages` 数组（5 页多页结构）
- ❌ `pageType: "lifecycle-observation-task"` 自创值
- ❌ `summary` 字段（spec 提议但 schema 没有）
- ❌ `domain`/`themeType`/`difficulty`/`hero.id`/`hero.role` 等自创字段

---

## 7. en-US overlay

路径：`boards/kids-world/src/data/locales/en-US/topics/cicada-life.json`

**锁字段守卫规则**：overlay 不允许包含 `type`, `correctOptionId`, `correctSequence`, `targetIds`, `decoyIds`，只翻译可见文案（title/prompt/options[].label/successCopy/wrongHint/childExplanation 等）。

---

## 8. 资产清单

### 8.1 数据文件

```
boards/kids-world/src/data/topics/cicada-life.json
boards/kids-world/src/data/locales/en-US/topics/cicada-life.json
```

### 8.2 图片资产（建议 8 张）

```
boards/kids-world/public/assets/life/cicada-life/
├── life-cicada-life-hero-v02.webp
├── life-cicada-life-nymph-closeup-v02.webp
├── life-cicada-life-lifecycle-v02.webp
├── life-cicada-life-molting-steps-v02.webp
├── life-cicada-life-choice-place-v02.webp
├── life-cicada-life-spot-shell-v02.webp
├── life-cicada-life-compare-butterfly-v02.webp
└── life-cicada-life-task-board-v02.webp
```

### 8.3 manifest 追加

`image-generation-manifest.json` 追加 8 个 asset 条目，遵循 v2.1 词包前缀/后缀规则。

### 8.4 asset-map 映射

`packages/kids-content/src/media.ts`（或对应位置）的 `topicHeroAssetBySlug` 加：

```ts
"cicada-life": "life-cicada-life-hero",
```

### 8.5 channel-policy

`channel-policy.json` 的 `miniprogram.visibleTopics` 加 `"cicada-life"`（已 render-ready 后自动通过 alignment 校验）。

---

## 9. 视觉验证结论（保留 v1.0 的视觉决议）

### 9.1 保留方向

- 暖色夏夜 / 傍晚自然观察氛围
- 小芋头 + 弟弟陪伴探索者组合
- 弟弟"圆头圆脑、低龄、接近光头短发"
- 生命周期图和羽化步骤图作为儿童科普主模块
- 任务板形式可复用到其他自然观察主题

### 9.2 修正方向

- 降低"摄影级昆虫质感"，提高儿童友好感
- `cicada-choice-place-01` 中央对象应明确为"成熟若虫"，不是成虫
- `cicada-compare-butterfly-01` 蝉卵改为树枝/小枝内（不是叶片）
- 比较图必须确保蝉侧没有蛹，蝴蝶侧有蛹
- 所有图片禁止嵌入文字
- 信息图预留 overlay 区域

---

## 10. 实施计划

### P0：最小可上线（已完成 ✅）

- ✅ topic JSON 落库
- ✅ en-US overlay 落库
- ✅ schema 扩展支持 observationContext + cognitiveFocus
- ✅ registry 注册 + render-ready
- ✅ channel-policy 加入 miniprogram visibleTopics
- ✅ 4 个 clickTasks（含 sequenceClick / singleChoice ×2 / findTarget）
- ✅ `npm run validate` 全绿

### P1：图片补齐（待办）

- 8 张图按 v2.1 词包生成
- manifest 追加
- asset-map 映射
- 视觉验证（避开 §9.2 列出的 5 个修正点）

### P2：模板沉淀（待办）

- 抽 `topic-template-observation.md` 模板
- 沉淀字段规则：observationContext + cognitiveFocus + 11 模块结构
- 后续可复用主题：蝌蚪变青蛙 / 蜻蜓羽化 / 毛毛虫变蝴蝶 / 蜗牛 / 蚂蚁 / 蘑菇

---

## 11. 验收标准

### 11.1 内容

- 儿童能说出：这是蝉若虫
- 知道：从地下出来，准备爬到树上羽化
- 能排序：卵 → 地下若虫 → 出土若虫 → 羽化 → 成虫
- 能区分：蝉没有蛹，蝴蝶有蛹
- 家长能获得：不打扰羽化、用观察问题引导孩子表达的提示

### 11.2 视觉

- 小芋头与弟弟形象保持系列统一
- 弟弟明显更小、圆头、低龄、接近光头短发
- 昆虫结构可识别但不惊悚
- 图片无内嵌文字
- 页面有 overlay 留白
- 生命周期和羽化步骤方向清楚

### 11.3 技术

- topic JSON 通过 `validate-topics`（schema + 引用完整性）
- en-US overlay 通过 `validate-i18n`（无锁字段）
- 通过 `validate-assets`（135 → 143 个引用 0 缺失）
- 通过 `validate-alignment`（render-ready ↔ miniprogram visible 对齐）
- EdgeOne build 通过
- Mini Program build 通过

---

## 12. 后续可复用模板（v1.1 重申）

`topic-template-observation.md` 模板结构：

```
1. 真实观察入口（→ hero + observationContext）
2. 这是谁（→ classificationGroups）
3. 它在做什么（→ representativeObjects）
4. 它的一生 / 变化过程（→ mechanism + secondaryMechanism）
5. 和相似对象比较（→ comparePairs）
6. 小小观察家任务（→ clickTasks）
7. 家长引导提示（→ parentTips + speakTemplates）
```

**核心规则**（从 cicada 实施得到的经验）：

1. 不要为单个专题自创新字段——优先映射到现有 11 模块
2. clickTasks 用 schema 标准枚举（`sequenceClick`/`singleChoice`/`findTarget`），不要自创 `sequence`/`choose`/`identify`/`compare`
3. 多页内容用单页 11 模块表达，不要引入新的多页路由
4. 新增字段（如 `observationContext`/`cognitiveFocus`）必须同步更新 `topic.schema.json`

可复用主题候选：蝌蚪变青蛙 / 蜻蜓羽化 / 毛毛虫变蝴蝶 / 蜗牛身体结构 / 蚂蚁搬家 / 蘑菇从哪里冒出来。
