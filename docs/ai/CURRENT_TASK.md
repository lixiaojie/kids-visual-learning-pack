# Current Task

## Metadata

- Updated At: 2026-07-31
- Updated By: Kimi Code
- Status: In Progress
- Branch: main（实施前新建 SKILL-02 任务分支与 worktree）
- Base Commit: c54c825

## Objective

按 `docs/superpowers/plans/2026-07-15-cognitive-card-thin-client-plan.md` 实现 SKILL-02 薄客户端：把已验证的发行基础设施填充为完整 `cognitive-card-os` `0.1.0`，使受信任 Codex 客户端在无 OpenAI API Key、仅使用登录 ChatGPT Pro 的条件下，通过 packet 契约领取锁定 GenerationPacket、本地生成候选、严格校验并自动上传；完成不可变 `0.1.0` 构建与生产 stable 首次激活、两个隔离 `CODEX_HOME` 安装验收和现网短期 scoped token 领取/上传/replay/撤销验收。

客户端契约归属已由 `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md` 固化：M1 领取/提交只走 packet 契约；生产核心权威保留在服务器；package-v5 上传面归入 PUBLISH-01 后续批次。

## Background

2026-07-31 分支审计确认：SKILL-01 registry/installer 基础设施已完成本地与生产 provisional 门禁（installer 200/no-cache、manifest 按设计 404）；`codex/card-os-thin-skill-v1` 的 29 个提交未执行 SKILL-02 计划且方向越序，已用 tag `archive/card-os-thin-skill-v1-20260717` 存档，不整体合入。用户已书面选定 ADR-001 调和方案，并授权从 main 另起新支实施 SKILL-02。

SKILL-02 计划 Entry Gate 已满足：SKILL-01 全计划评审通过、生产 registry 已部署且 stable 未被占位激活、本机完整 Skill 未改变、RED 基线三场景证据存在于分支 worktree 的 `.superpowers/sdd/skill-baseline/`（新分支需按计划在自有忽略目录重建或引用该证据，且不得向 forward-test agents 泄露答案）。

## Acceptance Criteria

- [ ] `skills/cognitive-card-os/scripts/card_os_client.py` 实现固定 CLI 契约：`doctor`、`auth set/status/delete`、`packets list/claim/get/complete`、`results submit`、`jobs status/events`（计划 Fixed Client Contract 全量）
- [ ] 凭据三级后端按优先级实现并失败关闭：macOS Keychain → Linux `secret-tool` → 显式 `--allow-file-store` 的 0600 文件；token 不出现在 argv/stdout/stderr/日志/Skill/Git/result/测试制品
- [ ] 传输层固定 HTTPS base URL、带 Authorization 禁重定向、canonical JSON、capability 协商与 `CLIENT_UPGRADE_REQUIRED`/`SERVER_UPGRADE_REQUIRED` 前置拒绝
- [ ] 结果提交实现 required_outputs 闭包、20/28 MiB 上限、凭据扫描（`CREDENTIAL_IN_RESULT`)、`ccos-v1-` 幂等键、`cognitive-card-submit-attempt-v1` journal 与 `ATTEMPT_BODY_CHANGED` 防漂移
- [ ] 自由概念请求稳定返回 `TRUSTED_UPSTREAM_REQUIRED`，不伪装为已创建任务
- [ ] 新建 5 个契约测试文件（transport/credentials/packets/results/thin_skill）并先 RED 后 GREEN；`tests/test_card_os_skill_release.py` 同步更新
- [ ] `skills/cognitive-card-os/SKILL.md`、`skills/cognitive-card-os/agents/openai.yaml`、`skills/cognitive-card-os/references/protocol.md`、`skills/cognitive-card-os/references/errors.md` 改写为 packet 工作流，通过 Skill 校验
- [ ] `package.json` 增加 `test:card-os-thin-client`；`npm run test:card-os-skill-registry` 与 `python3 -m unittest discover -s tests` 全绿
- [ ] 同一提交双构建字节一致；不可变 `0.1.0` 经 provisional gate 首次激活生产 stable，失败可原子恢复原 absence
- [ ] 两个隔离 `CODEX_HOME` 安装相同 archive SHA-256，`doctor`、升级失败与回滚演练通过
- [ ] 现网短期精确 `submit` scope token 完成一次 claim → get → 生成 → complete → submit → 同键 replay(`replayed=true`)→ `ATTEMPT_BODY_CHANGED` 反例 → 撤销后 403 `AUTH_REVOKED`，证据中无原始 token
- [ ] writing-skills GREEN forward tests 三场景通过且不向测试代理泄露答案
- [ ] roadmap 更新：SKILL-01 标记 DONE（stable 激活后）、SKILL-02 状态如实记录；第二台真实 Codex 电脑安装相同摘要前 SKILL-02 保持 IN PROGRESS（该硬条件超出本任务可控范围，须显式记录）
- [ ] `docs/ai/HANDOFF.md` 基于实际修改与验证结果更新

## In Scope

- `skills/cognitive-card-os/SKILL.md`、`skills/cognitive-card-os/agents/openai.yaml`、`skills/cognitive-card-os/scripts/card_os_client.py`、`skills/cognitive-card-os/references/protocol.md`、`skills/cognitive-card-os/references/errors.md`（仅这 5 个发布文件）
- `tests/` 下新建 5 个客户端契约测试文件，命名按计划 Product File Map:test_card_os_client_transport / test_card_os_client_credentials / test_card_os_client_packets / test_card_os_client_results / test_card_os_thin_skill（尚未创建，故不以反引号路径引用）
- `tests/test_card_os_skill_release.py`（按新 Skill 内容同步）
- `package.json`（仅增加 `test:card-os-thin-client` 入口）
- `README.md`（仅按计划 Task 5/9 的最小入口更新）
- `docs/cognitive-card-os-roadmap.md`（状态与验收记录）
- `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`
- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`、`docs/README.md`（本任务建立阶段的决策登记，已完成）
- 忽略的 `.superpowers/sdd/` 证据目录（forward tests、隔离安装、现网验收）
- 生产 registry 的 stable 激活操作（使用既有 `ops/cognitive-card-skill/publish_release.py` 已冻结契约，不修改其实现）

## Out of Scope

- `codex/card-os-thin-skill-v1` 分支资产抢救、cherry-pick 或合入；存档分支上的 package-v5、renderer、production core、恐龙模板族与 card-library 看板
- 服务器应用任何改动（`ops/cognitive-card-server/` 应用、Nginx、systemd、env)；服务器仓 worktree 的 `e78c2fa`
- `ops/cognitive-card-skill/build_release.py`、`ops/cognitive-card-skill/install.sh`、`ops/cognitive-card-skill/publish_release.py` 的契约修改（SKILL-01 已冻结）；仅允许按已验证用法调用
- 门户、浏览器上传、自由概念编译、服务器渲染、QA、正式发布、旧站替换、MCP
- `outputs/`、分支 worktree 未提交修改、用户级 `~/.codex/` 配置
- 第二台真实 Codex 电脑的DONE 条件本身（只记录状态，不伪造证据）
- CI、PR、push、merge（需用户另行授权）

## Constraints

- `0.1.0` 只处理服务器已有、锁定、可领取的 packet；自由概念失败关闭
- 不调用 OpenAI API，不要求 `OPENAI_API_KEY`，不读取/上传 ChatGPT Cookie、会话或身份材料
- claim/complete 不盲重试；只有 GET 与相同幂等键/完全相同 bytes 的 submit 允许有界重试
- 本地校验是第一道门，服务器仍为权威；客户端收到 receipt 后复核 result/artifact digests，不把"上传成功"描述为"正式发布"
- 不提前激活不完整 release；stable 首次激活走 provisional gate，任一失败原子恢复旧 absence
- 当前本机完整 `/Users/admin/.codex/skills/cognitive-card-os` 只读，验收使用隔离 `CODEX_HOME`
- 每个计划任务严格 RED → 最小 GREEN → 聚焦测试 → review → commit，不揉提交
- 实施分支与 worktree 按仓库惯例建于 `.worktrees/`（已被忽略）；main 工作区不直接改业务代码

## Current State

- 2026-07-31：分支审计完成；存档 tag `archive/card-os-thin-skill-v1-20260717` 已建立；roadmap 事实修正已提交（`c54c825`)。
- ADR-001 已按用户书面选定记录调和方案；本任务范围据此建立。
- 实施尚未开始；任务分支与 worktree 未创建。

## Next Actions

1. 用户授权后：提交本任务建立文档（ADR-001、本文件、roadmap、docs/README、HANDOFF)，从 main 新建 SKILL-02 任务分支与 worktree。
2. 按计划 Task 1 开始 RED：传输层与 capability 协商（新建 test_card_os_client_transport 测试）。

## Verification Plan

- Unit Tests: `python3 -m unittest tests.test_card_os_client_transport tests.test_card_os_client_credentials tests.test_card_os_client_packets tests.test_card_os_client_results tests.test_card_os_thin_skill -v`（新建，先 RED 后 GREEN）
- Registry Regression: `npm run test:card-os-skill-registry`（不得破坏 SKILL-01 已冻结契约）
- Full Suite: `python3 -m unittest discover -s tests`
- Build: 同一提交双构建 `cmp` + SHA-256 一致；`npm run build`（如触及静态构建链路）
- Live Acceptance: 生产 stable 激活探针（manifest 200、release 摘要一致、回滚恢复）、两个隔离 `CODEX_HOME` 安装比对、现网 scoped token 领取/上传/replay/撤销
- Governance: `bash scripts/ai/check-agent-state.sh`、`git diff --check`
- Lint: 仓库未确认通用 lint 命令

## Relevant References

- `docs/decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md`
- `docs/superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md`
- `docs/superpowers/plans/2026-07-15-cognitive-card-thin-client-plan.md`
- `docs/superpowers/plans/2026-07-15-cognitive-card-skill-registry-plan.md`
- `docs/cognitive-card-os-roadmap.md`（SKILL-01/SKILL-02 条目与 2026-07-31 记录）
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- tag `archive/card-os-thin-skill-v1-20260717`（存档分支，仅作挽救参考）
