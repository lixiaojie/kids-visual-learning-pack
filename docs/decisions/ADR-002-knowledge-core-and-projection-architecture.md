# ADR-002: Knowledge Core 优先与多 Projection 架构

- Status: Accepted
- Date: 2026-08-19
- Owners: 项目所有者（2026-08-19 书面批准）
- Related Task: Knowledge Core 架构文档固化（`docs/ai/CURRENT_TASK.md`）
- Related Files: `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md`、`docs/cognitive-card-os-system-design.md`、`docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`

## Context

现行 Cognitive Card OS 以“一个事实源，四个投影”为核心：任何正式包固定包含中文观察卡、英文观察卡、中文知识卡和英文知识卡。这一模型解决了来源、双语一致、内容锁和打印规范问题，但也把知识建模、学习设计与四页产物绑定在一起。

长期目标不是只生产四卡，而是让本地知识工作流产生可由个人服务器浏览、检索、复核、更新和长期管理的知识资产。实际知识既可能是单一主题，也可能是多个知识单元构成的复合主题，或按先修关系逐步深入的学习主题；部分命题还会随时间失效。固定四卡无法自然表达所有结构，若继续以产物形态反推知识模型，会限制内容与交互扩展。

同时，直接把完整知识架构暴露为大量表单、文件和必选步骤，会让普通创作频繁选择“跳过”或“忽略”，最终破坏治理本身。因此架构完整性与日常交互复杂度必须分别控制。

## Decision

采用 Knowledge Core 优先、多 Projection 的架构：

1. Knowledge Core 由 Evidence / Source、Proposition Graph 和 Knowledge Scope 三个逻辑层构成。它表达事实、来源、关系、范围、组合方式和时效，不包含任何特定页面或平台布局。
2. Knowledge Core 之后依次是 Learning Plan、Learning Path、Projection Blueprint、Renderer Binding 和 Artifact Package。共八个逻辑层，层间必须保持引用与追踪关系。
3. 四卡降为一种 `four-card` Projection family。打印也不等于四卡；系统根据知识结构、目标人群、语言、深度、时长和使用场景选择或建议适合的 Projection。
4. MVP 不把八个逻辑层实现成八个强制文件、表单、服务或数据库表。首版只持久化四类对象：`knowledge-core`、`learning-spec`、`projection-spec`、`manifest`。
5. 普通主题默认由系统推导范围、计划、路径和 Projection，只保留两个显式确认点：合并方案确认与发布确认。歧义、冲突、高时效或高风险内容可以进入额外复核，但必须说明触发原因。
6. 验证强度按阶段递增：draft 允许不完整；candidate 必须结构闭合且显式记录未解决项；published 必须通过来源、时效、命题引用、Projection 忠实性、资产摘要和发布完整性门禁。
7. 不提供绕过关键完整性的通用“跳过验证”。非关键警告可以带理由接受；关键问题只能保留为 draft 或 rejected candidate，不能激活或发布。
8. 来源、稳定 `proposition_id`、确定性、未知项、安全边界、generation input lock、final content lock、服务器权威和不可变 revision 继续保留。新 Projection 不得新增 Knowledge Core 中不存在的事实。
9. 首阶段只用三个纵向样例验证模型：兔子复合主题、几何逐步深入主题、时效知识主题。达到复杂度收缩条件时，优先删除必填项、改进默认值或降级内部层，不为保持抽象完整而增加用户操作。

本 ADR 已通过书面复核。`docs/cognitive-card-os-system-design.md` 和 `docs/cognitive-card-os-roadmap.md` 的规范收敛仍须按独立实施计划执行；在该批次完成前，现行四卡运行合同继续有效。

## Alternatives Considered

### Option A: 保持四卡为唯一正式产品模型

优点：沿用现有分类、模板、渲染和 QA，近期实现成本最低。缺点：复合主题、渐进学习、长文、交互浏览和时效更新只能挤进固定四页；知识模型继续受打印产物反向约束。未采用：不能满足长期知识管理与多形态发布目标。

### Option B: 八层分别落成独立对象、服务和用户步骤

优点：边界最显式，理论上便于单层演进。缺点：首版会产生大量 schema、状态组合、表单和跨对象版本关系；日常创作成本高，用户容易反复跳过门禁。未采用：在没有真实样例验证前属于过度设计。

### Option C: 八层逻辑、四类物理对象、渐进门禁

优点：保留长期架构边界，同时把普通流程压缩为自动推导和两个确认点；现有四卡可作为兼容 Projection 继续使用。缺点：四个物理对象内部需要清晰区分逻辑层，未来拆分时要维持兼容。采用：它在长期扩展性和近期可用性之间成本最低。

## Consequences

### Positive

- 知识资产不再被单一页面数、纸张或平台限制。
- 单一、复合、渐进和时效主题使用同一套来源与命题治理。
- Learning Plan、Learning Path 和 Projection 可以分别演进，不修改事实层。
- 现有四卡、双语、打印和内容锁能力可作为成熟 Projection 被复用。
- 日常创作不需要理解或操作全部逻辑层。

### Negative

- 现行系统总设计、Skill 输入门禁、模板路由、production record 和 package validator 未来都需要兼容性评估。
- 同一 Knowledge Core 可能产生多个 Learning Path 与 Projection revision，长期管理需要清晰的引用和影响追踪。
- 时效策略引入复核任务与过期状态，增加服务器长期运营责任。

### Risks

- “Knowledge Core”若定义过宽，可能把学习设计再次塞回事实层。
- 自动推导质量不足会让用户频繁修改系统建议，抵消简化收益。
- Projection 为追求表现力可能偷偷新增事实，破坏来源闭包。
- 时效提醒过多会形成 warning fatigue；过少则让过期内容继续作为当前知识展示。
- 过早建设图数据库、通用调度器或多 Renderer 会重现本 ADR 试图避免的复杂度。

## Migration or Rollout

1. 用户书面复核本 ADR 与配套设计 Spec；复核前不改变现行规范。
2. 复核通过后，单独更新系统总设计和路线图，明确现行四卡合同与新模型的过渡关系。
3. 为三个代表样例建立最小数据 fixture 和人工操作基线；不先建设通用服务器面。
4. 实现最小 `knowledge-core`、`learning-spec`、`projection-spec`、`manifest` 合同及 `four-card` 兼容映射。
5. 统计确认次数、治理额外耗时、手工改写、无效字段和警告处理结果；达到收缩条件时先简化模型。
6. 只有三个样例证明边界有效后，才评估服务器存储、更新调度、Portal 浏览和更多 Renderer。

## Verification

- 三个样例都能从来源和命题追踪到最终 Artifact，Projection 不新增事实。
- 普通样例从输入到发布不超过两个显式确认点。
- 复合主题不要求被压缩为四页；渐进主题能表达先修关系；时效主题能进入复核、过期和新 revision 流程。
- 现有四卡 production record 可无事实损失地映射为 `four-card` Projection。
- 任何新增 Projection 都不要求改变 Knowledge Core schema。
- 用户书面确认后，系统总设计与路线图不存在“四卡唯一模型”和“多 Projection 模型”并列冲突。

## References

- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`
