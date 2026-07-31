# Latest Handoff

## Metadata

- Updated At: 2026-07-31
- Agent: Kimi Code
- Branch: codex/card-os-thin-client-v1（worktree `.worktrees/card-os-thin-client-v1`）
- Base Commit: 7cf9714（Task 7 交接；origin/main = `05bced3`)
- Working Tree: 干净；生产 stable 已回滚至 absence(provisional gate 触发）
- Task Status: **BLOCKED（待用户决策 0.1.1 路径）**——Task 8 现网验收主流程全部通过，但发现 0.1.0 发布字节中 `auth delete` 在 macOS 失效（Important)，已按计划执行 provisional 回滚

## Summary

Task 8 现网验收（用户已授权）按计划执行：

- Step 1：短期 admin token(10 分钟）创建最小锁定 job `job_thin_client_acceptance_v1` + packet `gp_a854945e94c842b5936e65eafd40e420`(bilingual_projection，两个 required_outputs)，随后撤销 admin token(token_id `b0312d0e…`,revoked_at 已写）；签发 15 分钟 submit scope token(id `469fb93e…`)，原始 token 只经 0600 文件传递，未入日志/证据。
- Step 2–3：全新 Agent B（隔离根 `/tmp/ccos-agent-b/.codex`，预装生产归档，凭据经 Keychain 后端预配置，未向其泄露 token/packet）以原始 prompt 2 执行：doctor → auth status → list → claim → get(digest 校验）→ 本地生成两个文件（无 OpenAI API Key)→ complete → submit → `candidate_staged`(replayed=false,result_digest `sha256:0c87ca12…`);**跨调用重跑 submit → `replayed=true`、同一 result_digest(I-1 journal 重放路径现网成立）**；变更副本 → 本地 `ATTEMPT_BODY_CHANGED`（零新逻辑提交）。
- Step 4：服务器按 token ID 撤销（revoked_at 17:07:57Z)；用仍存储的凭据发受保护请求 → 精确 `403 AUTH_REVOKED`;`auth delete` 返回 deleted:true。

**发现的 Important 缺陷**:`auth delete` 后 `auth status` 仍报 present——真实 Keychain 上 `SecKeychainItemModifyAttributesAndData(item, NULL, 0, NULL)` 是 no-op(erase-to-empty 假设在真实后端不成立，fake 测试未能暴露；Task 2 评审 Minor 1 预警的风险坐实）。即 0.1.0 发布字节中 `auth delete` 在 macOS 实际不删除凭据数据。已实测确认修复路径：零长度非空 buffer(`create_string_buffer(0)`）可将数据截断为空，`get()` 视为 absent，且不突破计划冻结的五函数绑定集。

处置（已完成）:

1. 凭据卫生：手动零长度 modify 清空数据 + `security delete-generic-password` 移除 item 壳；`auth status` 确认 absent;token 已撤销，无任何可用凭据残留。
2. **provisional 回滚**（计划 Task 8 失败门禁）:`manifest.json` 原子移至 root 私有 quarantine(`/root/card-os-release-0.1.0/rollback-quarantine/`)，公网复验 404(prior absence 恢复）;immutable `0.1.0` release 与 manifest snapshot 保留为不可激活历史。
3. Agent B 服务器侧 token 文件与本地 token 文件均已删除。

后续路径（待用户确认）:**修复必须产生新字节，而不可变 `0.1.0` 已存在于 registry，故修复版本只能是 `0.1.1`**(SKILL_RELEASE/header/docs 同步；服务器 minimum_skill_release=0.1.0 兼容）。随后：修复+测试（fake 语义修正为真实后端语义）→ 门禁 → 0C/0I 评审 → 集成 push（需授权）→ 双构建 0.1.1 → 发布激活 provisional → Task 7 关键项与 Task 8 全流程在 0.1.1 上重跑。

## Completed

- Task 8 Step 1–4 主流程：锁定 packet 创建/admin 撤销、Agent B 全流程、exact replay(`replayed=true`)、`ATTEMPT_BODY_CHANGED` 反例、token 撤销 + 403 `AUTH_REVOKED`。
- 凭据卫生清理（Keychain item、服务器/本地 token 文件）。
- provisional stable 回滚至 absence，公网 404 复验。

## Changed Files

| File | Change | Reason |
| --- | --- | --- |
| `docs/ai/HANDOFF.md` | 修改 | 本阶段交接 |

## Decisions Made

- Task 8 Step 4 的 `auth status` absent 要求未达成即视为 Important，触发 provisional 回滚（不做"修复后继续"的变通）。
- 修复方向：保持五函数绑定集，`delete()` 改传零长度非空 buffer（实测有效）;fake 测试语义同步修正为真实后端语义（None=no-op，零长度非空=截断）。
- 版本路径：不可变约束下修复版只能为 `0.1.0`→**`0.1.1`**（待用户确认）。

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| Agent B 全流程（claim→submit) | PASS | `candidate_staged`,replayed=false |
| 跨调用 `results submit` 重跑 | PASS | `replayed=true`，同 result_digest |
| 变更副本 submit | PASS | 本地 `ATTEMPT_BODY_CHANGED` |
| 撤销后受保护请求 | PASS | 精确 403 `AUTH_REVOKED` |
| `auth delete` 后 `auth status` | **FAIL** | 仍报 present（缺陷） |
| 缺陷修复路径实测（零长度 buffer) | PASS | 数据截断为空，`get()`→absent |
| manifest 回滚 + 公网 404 | PASS | absence 恢复 |

## Known Failures

- **0.1.0 发布字节缺陷**:`KeychainCredentialStore.delete()` 在真实 macOS Keychain 上不删除数据（erase-to-empty 为 no-op)。已在本地实测确认修复方案；待修复发布。
- `node boards/kids-world/structure.test.mjs` 既有 `19 !== 18`，与本任务无关。
- 存档分支自身套件 19 errors + 1 failure，属封存资产。

## Risks and Caveats

- 生产 registry 当前无 stable(404);immutable `0.1.0`（含缺陷）仍为不激活历史，publish 同版本不同字节会被 publisher 拒绝，故必须 0.1.1。
- 该缺陷暴露 fake 与 Security.framework 真实语义的偏差：复审须要求 fake 语义修正 + 0.1.1 验收时在真实 Keychain 上重做 set/delete 验证。
- 已接受的候选（`gp_a854945e…`）在服务器候选区 staged 未发布，属验收预期产物。
- Task 8 的 packet 已消耗（accepted);0.1.1 重跑需新建锁定 packet 与 token。

## Remaining Work

1. 用户确认 0.1.1 路径后：修复 `delete()` + fake 语义 + SKILL_RELEASE/docs 版本同步；RED→GREEN→review→commit。
2. 门禁 + 集成 push（需授权）→ 双构建 0.1.1 → 发布 + provisional 激活 → 公开探针。
3. Task 7 关键项（隔离安装 0.1.1、doctor、check）与 Task 8 全流程在 0.1.1 上重跑（新 packet/token，含真实 Keychain set/delete 验证）。
4. Task 9:roadmap + 全量验证 + whole-branch 评审 + release gate。
5. 抢救批次（SKILL-02 之后、ACCEPT-01 之前）。

## Exact Next Action

向用户报告 Task 8 结果与 0.1.0 缺陷，确认 0.1.1 修复发布路径；确认后在 worktree 修复 `KeychainCredentialStore.delete()`（零长度 buffer）并同步 fake 语义与版本号，按 RED→GREEN→review→commit 执行。

## Recovery Notes

- 生产 stable = absence(404),quarantine 保存 provisional manifest bytes(`/root/card-os-release-0.1.0/rollback-quarantine/`)。
- release-source `6f06d7a`;origin/main `05bced3`；分支存档 tag `archive/card-os-thin-skill-v1-20260717`=`7f321a6`。
- 无凭据残留：admin/client token 均已撤销，Keychain item 已移除，token 文件均已删除。
