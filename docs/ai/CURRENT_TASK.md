# Current Task

## Metadata

- Updated At: 2026-07-31
- Updated By: Kimi Code
- Status: In Progress
- Branch: main
- Base Commit: 4500ab8

## Objective

设计 API-01 可信自由请求编译入口：把存档抢救回来的生产核心（`core/` 知识规范、模板族、确定性脚本与工作流）迁移为**服务器侧内容寻址权威快照 + 可信上游编译器**，使任何 Codex 终端的薄客户端都能领取由同一套规范编译出的锁定 GenerationPacket 并按同一机制生成高质量结果。本阶段只产出**设计草案**供用户书面确认，不实施。

## Background

- 2026-07-31 SKILL-02 完成（生产 stable `0.1.1`,release gate 已提交）;M1 领取/提交只走 packet 契约（ADR-001)。
- 2026-07-31 抢救小切片完成（`codex/card-os-salvage-v1`，套件 386/386 转绿）：抢救清单与 package-v5 评审 Block 修复方案已产出。
- 用户 2026-07-31 书面决定迁移方向：**可信上游编译器**（厚客户端历史积累迁服务器侧）；并指示渲染/QA/发布管线不新写服务器版本，**直接以厚客户端对应能力覆盖（lift-and-harden)**，但每个模块上服务器须过信任边界重审、运行时钉住、输入面重验三道。
- 关键事实：服务器应用（FastAPI）无 LLM;`core/SKILL.md` 的 CLASSIFICATION/FACT/SEMANTIC CORE 等是推理在环步骤，只能由可信上游（登录 ChatGPT Pro 的受信 Codex 终端）执行；服务器 `0.3.1` 已部署 `POST /admin/locked-jobs` 与 `POST /admin/jobs/{id}/packets`(locked_job_admin_import=true,free_form_job_creation=false)。

## Acceptance Criteria

- [ ] 设计草案覆盖：core 快照的服务器侧存储与内容寻址形态、快照版本与 packet `registry_commit`/`template_fingerprint`/`content_lock_digest` 的绑定规则
- [ ] 设计草案覆盖：可信上游编译器的运行位置、凭据模型（短期 admin scope)、编译流程（自由概念 → core 工作流 → admin 导入）
- [ ] 设计草案覆盖：core 工作流产出 → LockedJobRequest(6 字段）+ PacketIssueRequest 的权威转换表（以服务器 `c2a898c` schema 为准）
- [ ] 设计草案明确：服务器 `0.3.1` M1 链路零改动的边界；如需要服务器新增面（快照存储/读取端点），列为显式选项并给出推荐
- [ ] 设计草案覆盖：RENDER-01/QA-01/PUBLISH-01 的 lift-and-harden 接口预留（渲染器、QA 门、package-v5 与两个评审 Block 修复的挂点）
- [ ] 设计草案覆盖：安全边界（薄客户端零权威、token 处理、digest 绑定、失败关闭）与验收方案（兔子自由概念端到端）
- [ ] 用户对设计草案给出书面确认或修订意见
- [ ] `docs/ai/HANDOFF.md` 已更新

## In Scope

- `docs/superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md`（新建，设计草案）
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

- 设计必须保持：服务器统一权威、薄客户端零权威、自由概念只能经可信上游编译为锁定 packet、不可信客户端失败关闭
- 厚客户端资产复用遵循 lift-and-harden 三道：信任边界重审、运行时钉住、输入面重验
- 不改变已发布的薄客户端 `0.1.1` 与 SKILL-01 冻结契约
- 设计文档中的转换表必须逐项对照服务器 `c2a898c` 的 LockedJobRequest/PacketIssueRequest/GenerationPacket schema，不得发明字段

## Current State

- 2026-07-31：任务建立；设计草案编写中。

## Next Actions

1. 编写设计草案并提交 main（本地，push 待授权）。
2. 请用户书面审阅设计草案。

## Verification Plan

- 设计草案内部一致性：转换表与服务器 `c2a898c` schema 逐字段核对（grep 验证无发明字段）
- `bash scripts/ai/check-agent-state.sh`、`git diff --check`

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/cognitive-card-os-system-design.md`、`docs/cognitive-card-os-roadmap.md`(API-01 条目）
- 抢救分支 codex/card-os-salvage-v1（仅存于该分支）：抢救清单与 package-v5 评审 Block 修复方案两份 2026-07-31 文档，以及 core/ 全部资产（34 文件）
- 服务器应用仓 commit `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`（只读）
