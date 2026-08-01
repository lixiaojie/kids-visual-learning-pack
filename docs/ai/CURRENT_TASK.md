# Current Task

## Metadata

- Updated At: 2026-08-01
- Updated By: OpenAI Codex
- Status: In Progress
- Branch: main
- Base Commit: 4500ab8

## Objective

设计 API-01 可信自由请求编译与执行入口：把存档抢救回来的生产核心迁移为服务器侧内容寻址快照与 executor-neutral 生成合同。当前由登录 ChatGPT Pro 的受信 Codex 客户端按照该合同完成生成并上传；未来增加服务器 API 执行器时复用相同 snapshot、sealed input、GenerationPacket、GenerationResult 和 validator，只替换执行位置。本阶段只修订设计草案供用户书面确认，不实施。

## Background

- 2026-07-31 SKILL-02 完成（生产 stable `0.1.1`,release gate 已提交）;M1 领取/提交只走 packet 契约（ADR-001)。
- 2026-07-31 抢救小切片完成（`codex/card-os-salvage-v1`，套件 386/386 转绿）：抢救清单与 package-v5 评审 Block 修复方案已产出。
- 用户 2026-07-31 书面决定迁移方向：**可信上游编译器**（厚客户端历史积累迁服务器侧）；并指示渲染/QA/发布管线不新写服务器版本，**直接以厚客户端对应能力覆盖（lift-and-harden)**，但每个模块上服务器须过信任边界重审、运行时钉住、输入面重验三道。
- 关键事实：服务器应用（FastAPI）无 LLM;`core/SKILL.md` 的 CLASSIFICATION/FACT/SEMANTIC CORE 等是推理在环步骤，只能由可信上游（登录 ChatGPT Pro 的受信 Codex 终端）执行；服务器 `0.3.1` 已部署 `POST /admin/locked-jobs` 与 `POST /admin/jobs/{id}/packets`(locked_job_admin_import=true,free_form_job_creation=false)。
- 2026-08-01 用户进一步确认核心目标：以既有生产管线为基准，当前新任务在客户端遵循规范完成生成并上传；服务器预留未来接入 API 完成全部生成的方式。服务器权威是控制面与验收权威，不等于当前必须执行 LLM 生成。
- 2026-08-01 独立评审指出：原草案未提供完整 sealed input、现有 manifest 仅 27/34 文件带摘要、packet 前置输入锁与 core 最终 CONTENT LOCK 混用、提交凭据与 LLM 工作区未隔离、先 issue 后 verify 的失败关闭陈述不成立。用户要求修订。

## Acceptance Criteria

- [ ] 设计草案覆盖：服务器控制面、当前 `ClientSubscriptionPipelineExecutor` 与未来 `ServerApiPipelineExecutor` 的 compile/generate 两阶段职责和共用合同
- [ ] 设计草案覆盖：34 文件完整 core snapshot manifest、服务器侧存储与内容寻址、snapshot catalog
- [ ] 设计草案覆盖：generation input lock 与 final production content lock 的语义区分，以及 packet `registry_commit`/`template_fingerprint`/`content_lock_digest` 的绑定规则
- [ ] 设计草案覆盖：可信上游 compiler 与 deterministic submitter 隔离、`compiler_import` 最小凭据和自由概念 → sealed input → packet → production record → upload 流程
- [ ] 设计草案覆盖：core 工作流产出 → LockedJobRequest（6 字段）+ PacketIssueRequest 的权威转换表（以服务器 `c2a898c` schema 为准）
- [ ] 设计草案明确：服务器 `0.3.1` M1 链路零改动；API-01 新增 immutable input store/read 与原子 compiled-job 创建；公开 core 浏览端点延期
- [ ] 设计草案覆盖：RENDER-01/QA-01/PUBLISH-01 的 lift-and-harden 接口预留（渲染器、QA 门、package-v5 与两个评审 Block 修复的挂点）
- [ ] 设计草案覆盖：安全边界、token 处理、digest 绑定、失败关闭、兔子 + 第二个哺乳动物的端到端与 executor parity 验收
- [ ] 用户对设计草案给出书面确认或修订意见
- [ ] `docs/ai/HANDOFF.md` 已更新

## In Scope

- `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`（修订设计草案）
- `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`
- 设计所需的只读调研：服务器应用仓 `c2a898c` schema、存档/抢救分支 `core/` 内容

## Out of Scope

- API-01 的任何实施（编译器代码、服务器改动、core 快照导入）——设计获书面确认后另行立项实施
- RENDER-01/QA-01/PUBLISH-01 的立项与实施（本设计只预留接口）
- package-v5 评审 Block 修复的实施（方案已在抢救分支）
- `core/` 迁移本身（属 API-01 实施阶段）
- 生产任何操作、push、merge、PR（需用户另行授权）
- 存档 tag/worktree（只读）

## Constraints

- 设计必须保持：服务器拥有规范、任务、sealed input、候选与验收的控制面权威；当前客户端只作为生成执行器，未来 API 执行器不得建立第二套生产管线
- 自由概念只能经可信上游形成服务器可验证的 sealed generation input；不可信客户端不能选择快照、改写锁定输入或直接获得编译凭据
- 厚客户端资产复用遵循 lift-and-harden 三道：信任边界重审、运行时钉住、输入面重验
- 不改变已发布的薄客户端 `0.1.1` 与 SKILL-01 冻结契约
- API-01 如需新增客户端能力，必须用向后兼容的新 release 与服务器 capability/claim 门禁；旧 `0.1.1` 不得看到或 claim compiled packet
- 设计文档中的现有转换表必须逐项对照服务器 `c2a898c` 的 LockedJobRequest/PacketIssueRequest/GenerationPacket schema；新增服务器面必须明确标为 API-01 实施项，不伪装成已部署能力

## Current State

- 2026-08-01：用户澄清客户端当前执行、服务器 API 未来执行的核心目标；原草案经独立评审后完成修订，待用户书面审阅。

## Next Actions

1. 完成修订设计草案的项目文档验证。
2. 请用户书面审阅修订草案；未确认前不立项实施。

## Verification Plan

- 设计草案内部一致性：executor contract、两级 lock、snapshot/input store 与转换表互不矛盾
- 转换表与服务器 `c2a898c` schema 逐字段核对；新增面明确标识为未实现
- `bash scripts/ai/check-agent-state.sh`、`git diff --check`

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/cognitive-card-os-system-design.md`、`docs/cognitive-card-os-roadmap.md`(API-01 条目）
- 抢救分支 codex/card-os-salvage-v1（仅存于该分支）：抢救清单与 package-v5 评审 Block 修复方案两份 2026-07-31 文档，以及 core/ 全部资产（34 文件）
- 服务器应用仓 commit `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`（只读）
