# Latest Handoff

## Metadata

- Updated At: 2026-07-31
- Agent: Kimi Code
- Branch: main
- Base Commit: 4500ab8（抢救任务建立，本地未 push)
- Working Tree: API-01 任务建立与设计草案（见 Changed Files)，随本提交落地；用户既有未跟踪 `outputs/`
- Task Status: **API-01 已立项（Status: In Progress)，设计草案已产出，待用户书面审阅**

## Summary

SKILL-02 与抢救小切片完成后，用户书面确认迁移方向：厚客户端历史积累迁服务器侧（可信上游编译器）,RENDER/QA/PUBLISH 管线不新写、直接以厚客户端能力覆盖（lift-and-harden，过信任边界重审/运行时钉住/输入面重验三道）。据此：

1. 评估并排除了全量合入与 cherry-pick 方案（冲突面：已发布 0.1.1 源码闭包、SKILL-01 冻结契约）;A+B 策略（分支保留资产 + 文档结论上 main）已报告。
2. 向用户阐明两版本核心差异（薄 = 已发布的 packet 契约 M1 通道；厚 = 权威位置错误的完整生产线，为原料）。
3. 产出迁移评估：历史积累分四类（知识规范/模板族 = 内容寻址迁移；确定性脚本 = 服务器模块；推理工作流 = 只能可信上游执行，这是方案关键）;"同一机制"由 core 快照唯一权威 + packet digest 绑定保证，而非终端本地副本。
4. 按用户选定建立 API-01 正式任务（CURRENT_TASK.md，目标 = 本阶段只产设计草案供书面确认，不实施）。

**设计草案** `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md` 已产出，要点：可信上游编译器（受信终端 + 短期 admin token，复用 Task 8 已验证的 admin 导入路径）;core 快照选项 A（服务器应用仓受治理资产，零新端点）为推荐、选项 B（只读端点）留待 RENDER-01 前重评；三个绑定字段规则（`registry_commit`/`template_fingerprint`/`content_lock_digest`);core 工作流 → LockedJobRequest/PacketIssueRequest 逐字段权威转换表（已对照 `c2a898c` 核实无发明字段）；服务器 M1 链路零改动；RENDER/QA/PUBLISH 接口预留；兔子端到端验收方案；实施分解三子批（快照导入 → 编译器确定性部分 → 人工在环校准 + 现网验收）。

## Completed

- 合入方案评估（全量/cherry-pick 排除，A+B 推荐）与两版本核心差异分析（用户要求）。
- 迁移方向评估（可信上游编译器；lift-and-harden 映射表）; 用户书面确认方向并选定"立项先出设计草案"。
- API-01 任务建立（CURRENT_TASK.md,7 条验收标准）。
- 设计草案 + `docs/README.md` 设计表登记（状态 Draft)。

## Changed Files

| File | Change | Reason |
| --- | --- | --- |
| `docs/ai/CURRENT_TASK.md` | 重写 | 建立 API-01 正式任务（设计先行） |
| `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md` | 新建 | API-01 设计草案 |
| `docs/README.md` | 修改 | 设计表登记新草案 |
| `docs/ai/HANDOFF.md` | 修改 | 本阶段交接 |

## Decisions Made

- 用户书面：迁移方向 = 可信上游编译器；RENDER/QA/PUBLISH 采用 lift-and-harden（厚客户端能力覆盖，不新写服务器管线）。
- 设计草案推荐 core 快照选项 A（服务器应用仓受治理资产，零新 HTTP 端点）;B（只读端点）留作开放问题。
- 抢救分支与 worktree 保留为资产来源；不合入 main（代码）。

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| 转换表字段对照 `c2a898c` schema | PASS | LockedJobRequest/PacketIssueRequest/GenerationPacket/stage 枚举/正则逐项核实，无发明字段 |
| `bash scripts/ai/check-agent-state.sh` | 待提交后复跑 | — |

## Known Failures

- `node boards/kids-world/structure.test.mjs` 既有 `19 !== 18`，与本任务无关。
- `check-agent-state.sh` 的 2 项 WARN（交接格式类，非阻塞）。

## Risks and Caveats

- 设计草案状态为 Draft，未获用户书面确认前 API-01 不得实施。
- core 工作流 → packet 的转换规则首次正确性风险已记录（实施时先人工在环校准 2–3 个概念）。
- 快照存放仓（服务器应用仓 vs 治理仓分发）与选项 B 是否提前，是草案中的显式开放问题，需用户定夺。

## Remaining Work

1. 用户书面审阅设计草案（确认或修订）。
2. 获确认后立项实施 API-01-IMPL-1/2/3（快照导入、编译器、人工在环校准 + 现网验收）。
3. main 侧未 push 提交（`4500ab8`、本阶段 docs）的 push 待用户授权；抢救成果是否集成 main 待定。
4. 后续批次：RENDER-01、QA-01、PUBLISH-01（先修 Block)、ACCEPT-01;SKILL-02 DONE 条件（第二台 Codex 电脑）仍为用户侧动作。

## Exact Next Action

请用户审阅 `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md` 并给出书面确认或修订意见。

## Recovery Notes

- 本阶段基线 `4500ab8`(main，本地未 push)。恢复时先 `git rev-parse HEAD` 与 `git status --short`。
- 生产 stable `0.1.1`;release gate marker 在服务器 root 私有目录；抢救分支 `codex/card-os-salvage-v1` 尖端 `4d5ffe4`。
- 存档 tag（附注标签 `d172dcd` → `7f321a6c…`）与存档 worktree 封存零修改。
