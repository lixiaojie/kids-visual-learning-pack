# ADR-001: Card OS 客户端契约与生产核心归属

- Status: Accepted
- Date: 2026-07-31
- Owners: 项目所有者（用户书面选定调和方案）
- Related Task: SKILL-02（`docs/ai/CURRENT_TASK.md`）
- Related Files: `docs/superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md`、`docs/superpowers/plans/2026-07-15-cognitive-card-thin-client-plan.md`、`docs/cognitive-card-os-roadmap.md`、tag `archive/card-os-thin-skill-v1-20260717`
- Amended: 2026-08-30 [ADR-004](ADR-004-single-operator-main-flow.md) 取代本文件 Verification 中「两台独立 Codex 客户端才可标记 SKILL-02 DONE」；packet 契约与生产核心归属不变。

## Context

2026-07-31 对 `codex/card-os-thin-skill-v1`（领先 main 29 个提交）的审计发现该分支在 2026-07-16 一天内偏离了已确认的 2026-07-15 薄客户端设计：

- SKILL-02 薄客户端计划 Task 1–9 均未执行；分支的 `card_os_client.py` 是另一套 package-v4/v5 厚客户端契约，没有 packet 领取/提交层（无 `doctor`/`auth`/`packets`/`results`/`jobs`)，`governed upload` 未实现。
- 分支把约 5000 行"生产核心"（分类、模板族、production-record 验证、内容锁、渲染）放入 `skills/cognitive-card-os/core/`，与 `AGENTS.md` §6"服务器统一负责协议、任务状态、候选、资产、排版、QA 和发布"及 07-15 设计 §4 薄 Skill 边界直接冲突。
- 承载该方向的 `2026-07-16-cognitive-card-client-production-library-design.md` 仍标"待用户书面审阅"且与实现脱节；接受 package-v5 的服务端提交 `e78c2fa` 未合并，并被独立评审 Block(authority 闭包可伪造、gallery revision 资产未绑定）。
- 分支尖端未通过自身测试套件（386 项 = 19 errors + 1 failure)。
- 同时存在两份经用户确认但互相排斥的设计（07-15 薄 Skill 边界 vs 07-16 核心进 Skill 包），仓库没有 ADR 调和。

M1（可远程领取与提交）的完成条件是"两台独立 Codex 客户端安装相同摘要并完成同一服务器上的任务领取与结果上传"。已部署服务器 `0.3.1` 已具备完整 packet API，支持该目标的客户端契约只能是 packet 契约。

## Decision

采用调和方案，四层各自归位：

1. **M1 领取/提交层只属于 packet 契约。** SKILL-02 按 `2026-07-15-cognitive-card-thin-client-plan.md` 实现薄客户端 `0.1.0`；服务器应用零改动。
2. **生产核心权威保留在服务器侧。** 薄 Skill 不包含分类枚举、完整模板、知识注册表、事实来源库与自由概念编译权威；客户端对自由概念失败关闭（`TRUSTED_UPSTREAM_REQUIRED`)。
3. **分支的 package-v5 上传面重新定位为 PUBLISH-01 的正式发布通道**，不进入 M1 批次；其服务器接纳面（`e78c2fa`）必须先关闭评审 Block(authority 闭包复算、revision 资产绑定）并完成生产硬化后才可合并。
4. **分支资产存档抢救而非合入。** 分支以 tag `archive/card-os-thin-skill-v1-20260717` 存档；production core、受治理 renderer、package-v5 与审计工具（367 项通过测试）作为 RENDER-01/QA-01/PUBLISH-01/ACCEPT-01 的候选资产，在对应任务立项时按批评审抢救，抢救前须修复 publisher fixture 失同步与过时 mode pin 使套件转绿。

## Alternatives Considered

### Option A: 纯 07-15 薄客户端，弃置分支全部资产

优点：边界最干净，与既定设计字面一致。缺点：浪费约 4600 行脚本 + 3600 行测试、367 项通过的实质资产（renderer、package-v5、production record QA)，后续 RENDER/QA/PUBLISH/ACCEPT 需从零重做。未采用：资产对后续批次有直接价值，弃置代价大于存档成本。

### Option B: 采纳分支方向，packet 契约让位

优点：自由概念编译、渲染、打包一步到位，ACCEPT-01 路径最短。缺点：废弃已部署并验收的 packet API 与 07-15 设计；客户端自编译自由概念破坏"不可信客户端只能执行锁定任务"的安全模型；凭据模型退化（无 Keychain/secret-tool、任意 `--endpoint`)；服务器侧欠 1–2 周硬化且当前可接受伪造权威链；架构上从"服务器权威"倒退为"客户端权威"。未采用：安全模型与既定架构约束是硬边界。

### Option C: 两套客户端契约并存

优点：短期不用取舍。缺点：协议文档、测试矩阵、token scope、错误码表全部双写，维护成本长期最高，且边界模糊会重复本次的方向漂移。未采用。

## Consequences

### Positive

- M1 路径回到已部署、已验收的服务器契约，服务器零改动，风险面最小。
- 分支资产以存档 tag 保留全部挽救价值，后续批次有明确抢救入口。
- 两份冲突设计的关系被正式调和，后续工作不再依赖会话记忆判断方向。

### Negative

- SKILL-02 客户端需从零实现（约千行脚本 + 5 个契约测试文件），分支的 2344 行客户端代码不可直接复用。
- package-v5 发布面与生产核心资产的变现推迟到 PUBLISH-01 及以后批次。

### Risks

- packets/results 在生产零真实流量，SKILL-02 Task 8 现网验收是首跑，可能暴露测试未覆盖的部署漂移。
- 存档分支若长期不抢救，`core/` 资产可能与服务器演进再次漂移；每个抢救批次必须重新以 ADR 与当时的设计为准。
- 分支 worktree 仍有未提交修改与未跟踪计划文档，处置决策尚未完成。

## Migration or Rollout

1. 本 ADR 与 SKILL-02 任务范围（`docs/ai/CURRENT_TASK.md`）同时落地；roadmap 2026-07-31 记录同步更新。
2. 从 main 新建 SKILL-02 任务分支与 worktree，按 2026-07-15 thin-client 计划 Task 1–9 顺序执行。
3. SKILL-02 完成生产 stable 首次激活后，SKILL-01 方可标记 DONE。
4. PUBLISH-01 立项时评审 `e78c2fa` 与 package-v5 资产，先修评审 Block 与测试 fixture，再谈合并；RENDER-01/QA-01/ACCEPT-01 同理按批抢救。
5. 分支 worktree 未提交修改（library-design 修订、3 个未跟踪计划）由用户在抢救批次前另行决定；存档 tag 保证即使 worktree 删除也不丢失已提交成果。

## Verification

- `docs/ai/CURRENT_TASK.md` 的 SKILL-02 范围与本 ADR 一致；实施产物只含 packet 契约客户端。
- SKILL-02 单人完成条件（本机代码、隔离安装、现网领取/上传）由 [ADR-004](ADR-004-single-operator-main-flow.md) 关闭；第二台电脑改为 `SKILL-03`，不再作为本 ADR 的 DONE 门禁。
- 后续任何把 `core/` 资产引入 main 的提交必须引用对应批次任务的 CURRENT_TASK 范围与本 ADR。

## References

- `docs/superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md`
- `docs/superpowers/plans/2026-07-15-cognitive-card-thin-client-plan.md`
- `docs/superpowers/plans/2026-07-15-cognitive-card-skill-registry-plan.md`
- `docs/cognitive-card-os-roadmap.md`(2026-07-31 更新记录）
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- tag `archive/card-os-thin-skill-v1-20260717`（分支尖端 `7f321a6`,merge-base `b13ea1e`)
