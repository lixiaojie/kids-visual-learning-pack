# Current Task

## Metadata

- Updated At: 2026-08-01
- Updated By: Kimi Code
- Status: Done
- Branch: main
- Base Commit: 3a32cbf

## Objective

设计 API-01 可信自由请求编译与执行入口：把存档抢救回来的生产核心迁移为服务器侧内容寻址快照与 executor-neutral 生成合同。当前由登录 ChatGPT Pro 的受信 Codex 客户端按照该合同完成生成并上传；未来增加服务器 API 执行器时复用相同 snapshot、sealed input、GenerationPacket、GenerationResult 和 validator，只替换执行位置。本阶段只修订设计草案供用户书面确认，不实施。

## Background

- 2026-07-31 SKILL-02 完成（生产 stable `0.1.1`)；抢救小切片完成（`codex/card-os-salvage-v1`,386/386 转绿）。
- 用户书面决定迁移方向：可信上游编译器 + lift-and-harden;2026-08-01 进一步确认核心目标：当前客户端执行、未来服务器 API 执行，复用同一合同。
- 原草案经独立评审指出五类问题（sealed input、27/34 摘要、锁语义混用、凭据隔离、先 issue 后 verify),2026-08-01 完成修订并由 Kimi Code 增补 §8.3（执行侧代码分发）。

## Acceptance Criteria

- [x] 设计草案覆盖：服务器控制面、当前 `ClientSubscriptionPipelineExecutor` 与未来 `ServerApiPipelineExecutor` 的 compile/generate 两阶段职责和共用合同
- [x] 设计草案覆盖：34 文件完整 core snapshot manifest、服务器侧存储与内容寻址、snapshot catalog
- [x] 设计草案覆盖：generation input lock 与 final production content lock 的语义区分，以及 packet `registry_commit`/`template_fingerprint`/`content_lock_digest` 的绑定规则
- [x] 设计草案覆盖：可信上游 compiler 与 deterministic submitter 隔离、`compiler_import` 最小凭据和自由概念 → sealed input → packet → production record → upload 流程
- [x] 设计草案覆盖：core 工作流产出 → LockedJobRequest(6 字段）+ PacketIssueRequest 的权威转换表（以服务器 `c2a898c` schema 为准，无发明字段）
- [x] 设计草案明确：服务器 `0.3.1` M1 链路零改动；API-01 新增 immutable input store/read 与原子 compiled-job 创建；公开 core 浏览端点延期；执行侧代码经 governed Skill release 分发（§8.3)
- [x] 设计草案覆盖：RENDER-01/QA-01/PUBLISH-01 的 lift-and-harden 接口预留
- [x] 设计草案覆盖：安全边界、token 处理、digest 绑定、失败关闭、兔子 + 第二个哺乳动物的端到端与 executor parity 验收
- [x] 用户对设计草案给出书面确认（2026-08-01，状态 Approved)
- [x] `docs/ai/HANDOFF.md` 已更新

## In Scope

- `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`（修订设计草案，已 Approved)
- `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/README.md`（设计表状态）
- `docs/cognitive-card-os-roadmap.md`(2026-08-01 记录）

## Out of Scope

- API-01 的任何实施（编译器代码、服务器改动、core 快照导入）——按设计 §16 分批另行立项
- RENDER-01/QA-01/PUBLISH-01 的立项与实施；package-v5 评审 Block 修复的实施
- 生产任何操作、push、merge、PR（需用户另行授权）
- 存档 tag/worktree（只读）

## Constraints

- 本设计不授权任何实现、生产变更或发布；每个实施批次单独建立 CURRENT_TASK。
- 服务器拥有规范、任务、sealed input、候选与验收的控制面权威；未来 API 执行器不得建立第二套生产管线。
- 不改变已发布的薄客户端 `0.1.1` 与 SKILL-01 冻结契约；新增能力走向后兼容 release 与 capability 门禁。

## Current State

- 2026-08-01：设计修订稿（含 §8.3）获用户书面确认；本任务完成。

## Next Actions

1. 用户授权后：建立 API-01-IMPL-1(core snapshot manifest + catalog 导入）正式任务。
2. 用户授权后：push main 本地提交（`4500ab8`、`083492e`、`7e0d086`、`3a32cbf` 及本状态提交）。

## Verification Plan

- 已完成：转换表与服务器 `c2a898c` schema 逐字段核对（无发明字段）;`bash scripts/ai/check-agent-state.sh`(WARN，无 FAIL)、`git diff --check` 通过；设计表状态同步 Approved。

## Relevant References

- `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`(Approved)
- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/cognitive-card-os-roadmap.md`(API-01 条目、2026-08-01 记录）
- 抢救分支 codex/card-os-salvage-v1（仅存于该分支）:core/ 资产、抢救清单与 Block 修复方案
- 服务器应用仓 commit `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`（只读）
