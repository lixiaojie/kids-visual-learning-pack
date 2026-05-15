# 芋头宇宙 IA / 内容 / 图片编排 / 学习流程 / 交互证据联动主跟踪 Spec v1.2

> 日期：2026-05-15  
> 适用范围：芋头宇宙 EdgeOne H5 + Taro 微信小程序  
> 文档定位：v1.1 的实施后修订版，用于后续唯一主跟踪与外部模型审阅校验  
> 状态：Draft for implementation review  
> v1.2 更新重点：在 v1.1「模块级图片展示」基础上，补齐「交互选项状态与图片证据联动」缺口。

---

## 0. 当前实现基线

本轮 v1.1 P0 已完成以下能力：

1. 13 个 render-ready topics 均已补齐 `visualSlots`，不再只有 `cicada-life` 绑定图片。
2. `@yutou/kids-content` 已提供共享 visual slot 与学习流程 API：
   - `getTopicVisualSlots(topic)`
   - `getVisualSlotForTarget(topic, target)`
   - `getVisualSlotsForRole(topic, role)`
   - `getTopicLearningFlow(topic, locale)`
3. Web TopicPage 已渲染 `LearningFlowRail`，并在 hero / representativeObjects / mechanism / secondaryMechanism / comparePairs / clickTasks / parentTips 等模块附近展示对应图片。
4. 小程序 TopicPage 已渲染轻量学习流程 chips，并展示模块级图片。
5. `npm run validate` 已校验：
   - 13 个 topic schema 合法。
   - visualSlots assetId 指向 manifest。
   - required visual slot 图片文件存在。
   - Web / 小程序 TopicPage 接入学习流程与 visual slot 渲染路径。
6. `cicada-life` 当前可见 8 张学习图片、7 个学习流程阶段。

当前实现解决了「图片只在 hero 出现」的问题，但还没有解决「交互选项状态和图片证据之间没有联动」的问题。

---

## 1. v1.2 新暴露问题

### 1.1 问题描述

当前页面中，图片已经从“仓库资产”进入了各学习模块，但仍然主要是静态列示：

```text
用户点击分类 / 对象 / 步骤 / 比较 / 任务选项
        ↓
文字卡片状态变化
        ↓
图片区域基本不变
```

这会造成新的体验问题：

1. 孩子看到图片，但不知道当前选择对应图片里的哪条证据。
2. 点击任务像是在操作文字按钮，而不是在观察图片线索。
3. `LearningFlowRail` 提供了宏观流程，但模块内部仍缺少「当前看哪张图、哪条线索、为什么选对/选错」的反馈。
4. visualSlots 只解决了「图片放在哪个模块」，没有解决「图片如何响应模块状态」。

### 1.2 v1.2 核心修正原则

```text
图片不只是模块配图，而是当前交互状态的证据面板。
点击选项必须改变图片附近的状态提示、证据说明或视觉强调。
没有真实局部热点数据时，不伪装成可点图片热点。
P0 先做外部证据联动，P1 再做图片内部局部标注或热点。
```

---

## 2. 术语更新

### 2.1 VisualSlot

`visualSlots` 表示图片资产属于哪个模块或 item。

示例：

```json
{
  "id": "lifecycle",
  "assetId": "life-cicada-life-lifecycle",
  "target": "mechanism",
  "role": "process",
  "required": true
}
```

这只说明图片「出现位置」，不代表图片已经和交互状态联动。

### 2.2 VisualEvidenceState

v1.2 新增概念：`VisualEvidenceState` 表示当前交互状态在图片证据区的外部表达。

P0 不要求修改图片像素或真实局部高亮，只要求图片旁边或图片上方/下方显示当前证据状态。

最低结构：

```ts
type VisualEvidenceState = {
  source: "classificationGroups" | "representativeObjects" | "mechanism" | "secondaryMechanism" | "comparePairs" | "clickTasks";
  sourceId: string;
  visualSlotId: string;
  status?: "idle" | "selected" | "correct" | "wrong" | "partial";
  evidenceTitle: string;
  evidenceCopy: string;
  selectedLabels?: string[];
};
```

P0 可由 renderer 根据现有 topic 字段推导，不强制落库。

### 2.3 VisualStateBinding

P1 可新增显式配置，用于无法从现有字段推导的复杂联动。

```ts
type VisualStateBinding = {
  id: string;
  source:
    | `classificationGroups.${string}`
    | `representativeObjects.${string}`
    | `mechanism.${string}`
    | `secondaryMechanism.${string}`
    | `comparePairs.${string}`
    | `clickTasks.${string}`
    | `clickTasks.${string}.options.${string}`;
  visualSlotId: string;
  evidenceTitle: string;
  evidenceCopy: string;
  markerLabel?: string;
};
```

P1 之前不要求所有 topic 补该字段。

---

## 3. P0 交互证据联动规则

### 3.1 分类模块

当前允许行为：

- 点击 classification group。
- 高亮该 group。
- 自动选择或提示 representativeObjects 中属于该 group 的对象。
- 图片证据区显示：
  - 当前 group 名称。
  - 该 group 的 `childExplanation`。
  - 属于该 group 的对象数量或对象名称列表。

不允许行为：

- 分类点击改变 mechanism steps。
- 图片区域完全无反馈。
- 分类卡看起来像筛选器，但对象区和图片证据区都不响应。

验收：

```text
点击「它属于昆虫」后，representativeObjects 区域和观察图附近必须出现“它属于昆虫”的证据提示。
```

### 3.2 对象卡模块

当前允许行为：

- 点击 representative object。
- 展开对象说明。
- 高亮所属 group。
- observation visual slot 继续显示同一张观察图也可以，但图片附近必须切换证据说明。

证据说明来源：

| 字段 | 用途 |
|---|---|
| `object.name` | evidenceTitle |
| `object.childExplanation` | evidenceCopy |
| `object.visualHint` | 图片观察提示 |
| `object.commonMisread` | 可作为误读提示 |

验收：

```text
点击「出土若虫」后，观察图片附近必须显示“出土洞、粗壮前足、朝树干爬”等 visualHint。
```

### 3.3 机制步骤模块

当前允许行为：

- mechanism steps 有自己的 active step。
- 点击 step 后只影响 mechanism 证据区。
- process visual slot 可以保持同一张图，但必须切换当前步骤 caption/legend。

证据说明来源：

| 字段 | 用途 |
|---|---|
| `step.shortTitle` | evidenceTitle |
| `step.childExplanation` | evidenceCopy |
| `step.parentNote` | 可折叠家长补充 |

验收：

```text
点击「在树干上羽化」后，生命周期图或羽化图旁必须显示该步骤说明，而不是仍然只显示静态图片。
```

### 3.4 secondaryMechanism 模块

规则同 mechanism，但状态独立。

验收：

```text
点击「翅膀展开变硬」后，不应改变 classificationGroups 或 main mechanism 的 active state，只改变 secondaryMechanism 证据区。
```

### 3.5 比较模块

当前允许行为：

- comparePairs 可以静态全部展示。
- 若 comparePairs 可点击，则点击 pair 后图片证据区必须切换到该 pair。
- 如果只有模块级 compare visual slot，没有 pair 级图片，则复用同一张图，但证据标题和说明必须切换。

证据说明来源：

| 字段 | 用途 |
|---|---|
| `pair.title` | evidenceTitle |
| `pair.a.name + pair.a.points[]` | A 侧证据 |
| `pair.b.name + pair.b.points[]` | B 侧证据 |
| `pair.childConclusion` | evidenceCopy |

验收：

```text
点击「蝉 vs 蝴蝶」后，对比图旁必须显示“蝉没有蛹，蝴蝶有蛹”的当前证据结论。
```

### 3.6 ClickTask 模块

ClickTask 是 v1.2 最关键修复点。每个任务卡的选项操作必须联动图片证据区。

#### singleChoice

点击选项后：

- 选项按钮显示 selected。
- 图片证据区显示当前选择。
- 正确时显示 `successCopy`。
- 错误时显示对应 `wrongHints[optionId]` 或 `wrongHint`。
- 视觉状态为 `correct` 或 `wrong`。

验收：

```text
点击「树干」后，choice-place 图片附近必须显示“树干这样的垂直表面更适合若虫固定身体”。
点击「水坑」后，图片附近必须显示“水坑不适合羽化，想想哪里能抓牢”。
```

#### findTarget

没有图片坐标数据时，不允许伪装成真实图片热点。

P0 做法：

- 在图片下方显示 target/decoy 选项 chips。
- 点击 target 时，图片证据区显示 `correct` 或 `partial`。
- 点击 decoy 时，图片证据区显示 `wrong` 和 wrongHint。
- 已找到 target 必须在图片证据区留下状态。

P1 做法：

- 可新增 hotspots 坐标，再在图片内部点击。

验收：

```text
点击「cicadaShell」后，spot-shell 图片附近必须显示“找到了！蝉蜕是若虫羽化后留下来的旧外壳。”
点击 decoy 后，图片附近必须提示“蝉蜕像一只空空的小壳，常常贴在树干上。”
```

#### sequenceClick

点击顺序选项后：

- 图片证据区显示当前已选择顺序。
- 每点一步，显示“当前第 N 步”。
- 点错后清空或标记错误，并显示 wrongHint。
- 完成后显示 successCopy。

验收：

```text
依次点击「卵 -> 地下若虫 -> 出土若虫」后，lifecycle 或 task-board 图片附近必须显示当前顺序进度。
点错时，图片附近必须显示重试提示。
```

---

## 4. 组件要求

### 4.1 Web TopicVisual

当前 `TopicVisual` 需要从静态图片组件升级为 evidence panel。

建议 props：

```ts
type TopicVisualProps = {
  slot?: VisualSlot | null;
  fallbackAlt?: string;
  evidence?: VisualEvidenceState | null;
};
```

渲染规则：

- 始终显示图片。
- 若 `evidence` 存在，在图片附近显示：
  - `evidence.evidenceTitle`
  - `evidence.evidenceCopy`
  - `evidence.selectedLabels`
  - `evidence.status`
- `status` 必须影响视觉样式，但不得遮挡图片主体。

### 4.2 小程序 TopicVisual

小程序同样需要接收 evidence。

简化规则：

- 不要求 sticky。
- 不要求图片内部 overlay。
- 必须在图片下方显示当前证据标题和说明。
- 状态样式至少区分 correct / wrong / selected。

### 4.3 ClickTaskCard

`ClickTaskCard` 不应只在卡片内部显示反馈；必须把同一反馈传给图片证据区。

建议 Web / 小程序统一内部状态：

```ts
type TaskEvidenceState = {
  result: "idle" | "correct" | "wrong" | "partial";
  selectedIds: string[];
  message: string;
};
```

如果 `ClickTaskCard` 自己持有状态，则 `TopicVisual` 必须在卡片内部和选项共处，不要把图片放在任务区顶部后失去具体任务语义。

推荐结构：

```text
TaskCard
├── task title / prompt
├── task visual evidence panel
├── options
└── feedback
```

---

## 5. 数据模型策略

### 5.1 P0：不新增 topic 字段

优先使用现有字段推导 evidence：

| 模块 | 当前状态 | evidence 来源 |
|---|---|---|
| classificationGroups | activeGroupId | group.name / group.childExplanation |
| representativeObjects | activeObjectId | object.name / childExplanation / visualHint |
| mechanism | activeStepId | step.shortTitle / childExplanation |
| secondaryMechanism | activeStepId | step.shortTitle / childExplanation |
| comparePairs | activePairId | pair.title / A-B points / conclusion |
| clickTasks | selectedIds + result | selected option label / successCopy / wrongHint |

优点：

- 不需要 13 个 topic 立即补复杂绑定。
- 可以先让当前所有专题具备基础联动。
- 校验重点放在 renderer 行为。

### 5.2 P1：新增 `visualStateBindings`

当需要更精确的图片证据文案、marker label、或一个选项绑定不同图片时，再新增字段。

示例：

```json
{
  "visualStateBindings": [
    {
      "id": "cicada-choice-tree-trunk",
      "source": "clickTasks.cicada-choice-01.options.treeTrunk",
      "visualSlotId": "choice-place",
      "evidenceTitle": "树干更稳",
      "evidenceCopy": "树干这样的垂直表面能让若虫抓牢身体，适合完成羽化。",
      "markerLabel": "抓牢"
    }
  ]
}
```

P1 schema 要求：

- `source` 必须指向合法模块 / item / task option。
- `visualSlotId` 必须存在于同 topic 的 `visualSlots`。
- overlay 只允许翻译 `evidenceTitle` / `evidenceCopy` / `markerLabel`，不得改 `source` / `visualSlotId`。

---

## 6. 校验要求

### 6.1 validate-content-alignment

新增静态校验：

1. Web `ClickTaskCard` 必须把 task feedback 与 `TopicVisual` 同卡渲染，不能只在任务区顶部展示通用 task image。
2. 小程序 `ClickTaskCard` 必须把 task feedback 与 `TopicVisual` 同卡渲染。
3. `MechanismSteps` 必须包含 active step state，并把 active step 文案传给 visual evidence panel。
4. `RepresentativeObjects` 必须把 active object 文案传给 visual evidence panel。
5. 若 `visualStateBindings` 存在，校验 source 和 visualSlotId 引用合法。

### 6.2 行为验收

至少用 `cicada-life` 做端到端验收：

| 操作 | 预期图片证据联动 |
|---|---|
| 点击「出土若虫」对象卡 | observation 图附近显示出土若虫 visualHint |
| 点击「在树干上羽化」步骤 | lifecycle/molting 图附近显示当前步骤说明 |
| 点击「蝉 vs 蝴蝶」比较 | compare 图附近显示双方差异与结论 |
| 任务选择「树干」 | choice-place 图附近显示 correct 状态和 successCopy |
| 任务选择「水坑」 | choice-place 图附近显示 wrong 状态和 wrongHint |
| findTarget 点击「cicadaShell」 | spot-shell 图附近显示找到了蝉蜕 |
| sequenceClick 点到第三步 | lifecycle/task-board 图附近显示当前已选顺序 |

---

## 7. 下一轮实施任务包

## Wave I0：图片证据与交互状态联动（P0）

### I0.1 升级 Web TopicVisual 为 Evidence Panel

涉及文件：

```text
boards/kids-world/src/components/topic/TopicVisual.tsx
boards/kids-world/src/styles/styles.css
```

任务：

- 增加 `evidence` prop。
- 支持 selected / correct / wrong / partial 样式。
- 显示 evidenceTitle / evidenceCopy / selectedLabels。

验收：

- 图片区域不再只是图片。
- 交互状态变化时，图片附近文字同步变化。

### I0.2 RepresentativeObjects 绑定 active object evidence

涉及文件：

```text
boards/kids-world/src/components/topic/RepresentativeObjects.tsx
boards/kids-world/src/pages/TopicPage.tsx
```

任务：

- activeObject 改变时，TopicVisual evidence 同步切换。
- evidenceCopy 使用 `childExplanation` 和 `visualHint`。

验收：

- 点击不同对象时，观察图片旁说明跟着变。

### I0.3 MechanismSteps 绑定 active step evidence

涉及文件：

```text
boards/kids-world/src/components/topic/MechanismSteps.tsx
```

任务：

- active mechanism step 传给 process visual。
- active secondary step 传给 secondary visual。

验收：

- 点击步骤时，图片证据说明切换。
- main / secondary 状态互不干扰。

### I0.4 ComparePairs 绑定 active pair evidence

涉及文件：

```text
boards/kids-world/src/components/topic/ComparePairs.tsx
```

任务：

- compare card 可选择。
- 图片证据区显示当前 pair 的 A/B points 和 conclusion。
- 有 pair 级 visual slot 时优先使用 pair 图；否则复用模块图。

验收：

- 点击不同 compare pair 时，图片附近证据说明切换。

### I0.5 ClickTaskCard 绑定 task evidence

涉及文件：

```text
boards/kids-world/src/components/topic/ClickTaskCard.tsx
apps/miniprogram/src/components/topic/ClickTaskCard.tsx
```

任务：

- task visual 移入每个任务卡内部。
- selectedIds / result / message 同步传入 TopicVisual。
- singleChoice / findTarget / sequenceClick 三类都更新图片证据区。

验收：

- 任务选项点击后，图片证据区显示当前选择与正确/错误反馈。

### I0.6 小程序同步 Evidence Panel

涉及文件：

```text
apps/miniprogram/src/components/topic/TopicVisual.tsx
apps/miniprogram/src/components/topic/TopicVisual.scss
apps/miniprogram/src/pages/topic/index.tsx
apps/miniprogram/src/components/topic/ComparePairCard.tsx
```

任务：

- 小程序 TopicVisual 支持 evidence。
- 对象 / 机制 / 比较 / 任务模块同步 evidence。
- 不要求复杂 active viewport detection。

验收：

- 小程序中点击任务选项时，图片下方反馈同步变化。

### I0.7 扩展校验脚本

涉及文件：

```text
scripts/validate-content-alignment.mjs
scripts/validate-miniprogram-scaffold.mjs
```

任务：

- 校验 `TopicVisual` 支持 evidence prop。
- 校验 Web / 小程序 ClickTaskCard 内部使用 TopicVisual。
- 校验 MechanismSteps / RepresentativeObjects 使用 evidence。

验收：

- 移除 evidence 联动代码后 validate 会失败。

---

## 8. 非目标

本轮不要求：

1. 图片内部真实坐标热点。
2. 根据图片内容自动识别目标区域。
3. 重新生成所有图片。
4. 每个 topic 手写 `visualStateBindings`。
5. 多页 topic 路由。

---

## 9. 外部模型审阅提示

请重点审查：

1. 当前 v1.1 实现是否只是「图片展示完整」，而非「交互证据联动完整」。
2. v1.2 的 P0 是否能在不新增大量数据字段的情况下，让 13 个专题获得基础状态联动。
3. ClickTask 三种类型的 evidence 规则是否足够明确。
4. 是否应把 `visualStateBindings` 提前到 P0，还是保留 P1。
5. 校验脚本能否有效防止回退到“图片静态列示”。

