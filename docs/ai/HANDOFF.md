# Latest Handoff

## Metadata

- Updated At: 2026-08-01
- Agent: OpenAI Codex（修订草案）+ Kimi Code（评审与 §8.3 增补）
- Branch: main
- Base Commit: 7e0d086（本地 main；`origin/main` 仍停在更早状态，未获 push 授权）
- Working Tree: API-01 修订设计、CURRENT_TASK/HANDOFF；用户既有未跟踪 `outputs/`
- Task Status: **API-01 修订草案已完成，待用户书面审阅；未进入实施**

## Summary

用户澄清本版本核心目标：以过去多轮迭代形成的生产管线为质量基线，当前没有模型 API，因此由受信 Codex + ChatGPT Pro 客户端按规范完成新任务生成并上传；服务器保留规范、任务、候选和验收的控制面权威，并为未来服务器 API 完成全部生成预留同一执行合同。

原设计经过两路独立评审后存在五类主要问题：服务器只校验摘要形状、source manifest 仅 27/34 文件带内容摘要、packet 前置输入锁与 core 最终 CONTENT LOCK 混用、sealed input 无跨执行器传递方式、LLM 工作区与提交凭据未隔离。用户要求修订。

修订设计采用方案 B：服务器保存不可变 sealed generation input，当前 `ClientSubscriptionPipelineExecutor` 与未来 `ServerApiPipelineExecutor` 共用 compile + generate 两阶段合同。API-01 增加 input store/read、原子 compiled-job、最小 `compiler_import` scope 和 executor capability 门禁；公开 core 浏览与服务器模型 API 继续延期。

## Completed

- 根据用户目标修正“服务器权威”的定义：控制面与验收权威，不等于当前执行 LLM。
- 重写 API-01 设计草案，加入三方案比较并采用服务器 sealed input store。
- 定义 `cognitive-card-core-snapshot-v1` 完整成员摘要与 root digest，修复现有 27/34 摘要缺口。
- 区分 generation input lock 与 production-record-v1 final content lock；现有 packet `content_lock_digest` 在 API-01 v1 映射前置输入锁。
- 定义客户端/未来 API 共用的 `PipelineExecutor.compile` + `PipelineExecutor.generate` 合同。
- 将首版 required output 收敛为单个规范 `production/production-record.json`，由服务器运行 production-record 关系闭包验证。
- 明确新增服务器面：immutable input store/read、原子 compiled-jobs、`compiler_import` scope、executor capability/claim 门禁。
- 明确已发布 `0.1.1` 不修改且不能 claim API-01 compiled packet；API-01 使用新增兼容客户端 capability。
- 同步 `docs/ai/CURRENT_TASK.md` 的 Objective、Acceptance Criteria、Constraints 与 Next Actions。

## Changed Files

| File | Change | Reason |
| --- | --- | --- |
| `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md` | 全面修订 | 对齐当前客户端执行、未来 API 执行的核心目标并关闭评审问题 |
| `docs/ai/CURRENT_TASK.md` | 更新 | 将修订目标、验收标准和兼容约束关联到正式任务 |
| `docs/ai/HANDOFF.md` | 更新 | 记录真实修订、验证、剩余工作与恢复入口 |

用户既有 `outputs/` 保持未跟踪，未读取、未修改、未纳入本次范围。

## Decisions Made

- 当前和未来只有一套生产管线；执行位置通过 pipeline executor 替换。
- 当前客户端同时承担 compile/free-request 与 generate/packet 两个推理阶段；确定性 submitter、resolver、validator 不属于 LLM executor。
- 服务器应用仓保存不可变 core snapshot；未来只有在 snapshot 发布节奏与应用明显脱钩时才拆独立治理仓。
- 公开 core snapshot 浏览端点可延期，但 executor 所需的 sealed input store/read 必须进入 API-01。
- `GenerationPacket v1` 字段集合保持不变；API-01 的新 capability 与任务可见性由服务器元数据和 credential 门禁承担。
- API-01 不授权任何实现、部署、生产操作、commit 或 push。

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server `c2a898c` schema 逐字段核对 | PASS | LockedJobRequest 与 PacketIssueRequest 字段、枚举和正则未被误写成已部署新字段 |
| placeholder / stale-term scan | PASS | 无占位项；已清除旧 executor 命名和旧方案陈述 |
| `git diff --check` | PASS | 修订文档无 whitespace error |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL；check-doc-governance、task-state、handoff、git diff 全部 PASS；仅既有 secret-related field-name 清单 WARN，无高置信密钥值 |

## Known Failures

- `node boards/kids-world/structure.test.mjs` 既有 `19 !== 18`，与本次纯设计文档修订无关。
- `check-agent-state.sh` 本次报告 1 项既有 secret-related field-name 清单 WARN；扫描同时确认无高置信密钥值，与本次修订无关。

## Risks and Caveats

- 修订草案仍待用户书面确认；未确认前不得建立 API-01 实施任务。
- generation-input-v1 完整 JSON Schema、compiled-jobs 幂等键、sealed input 保留期和 capability-bound credential 细节留到实施设计，但不得改变已冻结的 executor-neutral 方向。
- `content_lock_digest` 承载 generation input lock 是对现有 v1 字段的兼容映射；实施测试与日志必须始终区分 packet 输入锁和 production record 最终内容锁。
- 新 capability 门禁需要服务器与新客户端配套实现；旧 `0.1.1` 只能继续执行既有 M1 packet。

## Remaining Work

1. 用户书面审阅修订设计草案，确认或提出修改。
2. 获确认后，另行建立 API-01-IMPL-1..5 的实施任务；不得沿用当前设计任务直接编码。
3. 实施前补 generation-input-v1 JSON Schema、idempotency、retention 和 credential 细节并按批评审。
4. 本地 main 尚未 push；commit/push 均待用户另行授权。

## Kimi Code 增补记录（2026-08-01，用户指示）

Kimi Code 评审修订草案：结论为实质性进步、建议接受（sealed input store、两阶段 executor 合同、两级锁、34 成员全摘要、凭据隔离、原子 compiled-jobs、capability 门禁、单一 production record 输出均核实为正确修复；27/34 摘要缺口、stage 枚举、job_id 正则、`input_artifacts` 类型等事实陈述抽查属实）。发现一个残留缺口：§8.1 要求领取端执行 core workflow + resolver + validator，而 §10.3 延期了 core 下载端点，执行侧代码到达路径缺失。按用户指示增补：

- 设计 §8.3「执行侧代码与规范的分发」：执行侧资产（workflow 指引、resolver、production-record validator 及 references 子集）随新增 executor capability Skill release 版本化分发（复用 SKILL-01 注册表/安装器，摘要绑定、可回滚，不改 `0.1.1` 字节）；编译侧完整 snapshot 不下发；release↔snapshot 兼容由服务器 capability metadata 钉死；§8.2 的"snapshot release"对 API 执行器指服务器本地读取，§10.3 延期决定不受影响。
- §15 已冻结决定同步增加该条。
- 小点记录：`packets/available` 按 capability 过滤已在 §10.1 覆盖；`compiler_import` 新 scope（超出 `c2a898c` 冻结枚举）属服务器 auth 变更批次，§15 已挂开放项；sealed input 保留期默认值留给实施设计。

## Exact Next Action

请用户审阅修订草案（含 §8.3 增补），重点确认：方案 B、两级 lock、API-01 新增 input/control surface、旧 `0.1.1` 与新 executor capability 的兼容边界、执行侧代码经 governed release 分发。

## Recovery Notes

- 恢复时先执行 `git rev-parse HEAD`、`git branch --show-current`、`git status --short`。
- 本次基线是 main `7e0d086`；设计原提交是其父提交 `083492e`。
- 服务器 schema 只读证据位于 `.worktrees/cognitive-card-server-release-0.3.1`，HEAD `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`。
- 抢救资产来源位于分支/worktree `codex/card-os-salvage-v1`；存档 tag/worktree 未修改。
- 用户既有 `outputs/` 必须继续保留，不清理、不提交。
