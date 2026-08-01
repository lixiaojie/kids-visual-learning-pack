# Latest Handoff

## Metadata

- Updated At: 2026-08-01
- Agent: Kimi Code
- Branch: main(kids);服务器仓分支 codex/api-01-core-snapshot
- Base Commit: b5b202c(IMPL-1 任务建立，已 push)
- Working Tree: roadmap IMPL-1 记录（待提交）；用户既有未跟踪 `outputs/`
- Task Status: **API-01-IMPL-1 完成**（快照工具 + 导入 + catalog，评审修复全部落地）；服务器仓分支待 push（需授权）;IMPL-2 待立项

## Summary

API-01-IMPL-1 完成（服务器应用仓 worktree `.worktrees/cognitive-card-server-api-01`，分支 `codex/api-01-core-snapshot`):

1. **RED→GREEN**:33 项测试先 RED（模块不存在），新增 `src/cognitive_card_server/core_snapshot/`(model/builder/validator/catalog/cli，共 710 行）转 GREEN；零既有文件改动。
2. **真实快照**：从抢救分支 `4d5ffe4` 的 core/(34 文件，detached worktree 用后已删）生成 `cognitive-card-core-snapshot-v1`,snapshot_id `sha256:47d2cb6534f9b20b082d984d2d4fe04f8a00ef825b6de7ca793c1a33fdb6d4c1`；导入 `core-snapshots/47d2cb65…/`(manifest + 全部成员，3 个脚本 0755 余 0644)；固定测试向量（fixture → root `f0f48af6…`）经评审独立复算一致；与抢救源逐字节核对零偏差。
3. **catalog**：两阶段提交解决自引用——先提交导入（`2837c8b`)，再 `catalog-add` 激活（registry_commit=`2837c8b`,`9c1b82b`);catalog 只增不改、单 active。
4. **独立评审**:1 Important(`git status --untracked-files=all` 不报告忽略文件，忽略文件可进入快照且不可从 origin_commit 恢复——已实证绕过）+ 3 Minor(validator 对符号链接目录失明、凭据 regex 漏复数形式、若干记录项）。全部已修：`_verify_git_state` 增加 prefix 级 `--ignored=matching` 检查（`IGNORED_SOURCE_ENTRY`)、validator 显式拒绝符号链接目录、regex 增加 `credentials?`/`secrets?`（保持 `style_tokens.yaml` 通过）；补 3 个回归测试，35/35 转绿。
5. **回归**:fastapi/httpx 经隔离 venv(`/tmp/ccos-server-venv`）补齐后全量 309 项中 307 通过；2 项 real-uvicorn 集成测试 502，**在未改动基线 `c2a898c` 同样失败**（本地环境问题，与本次无关）。

## Completed

- IMPL-1 任务建立与 push(kids `b5b202c`)。
- core_snapshot 子包 + 35 项测试；真实 34 成员快照导入与 catalog 激活（`2837c8b`、`9c1b82b`，服务器仓本地）。
- 独立评审 + 1I/3M 修复 + 回归测试。

## Changed Files

| File | Change | Reason |
| --- | --- | --- |
| （服务器仓）`src/cognitive_card_server/core_snapshot/` | 新建 5 文件（710 行） | 快照生成/校验/catalog/CLI |
| （服务器仓）`tests/test_core_snapshot.py` | 新建（~550 行，35 测试） | 固定向量 + 闭包/负向/回归 |
| （服务器仓）`core-snapshots/47d2cb65…/`(35 文件）+ `catalog.json` | 新建 | 真实快照导入与激活 |
| `docs/cognitive-card-os-roadmap.md` | 修改（待提交） | IMPL-1 完成记录 |
| `docs/ai/HANDOFF.md` | 修改 | 本阶段交接 |

## Decisions Made

- 凭据扫描 regex 采用分隔符边界 + `credentials?`/`secrets?` 复数（`style_tokens.yaml` 为合法 core 成员）;`token` 保持单数形式。
- catalog 采用"先导入提交、后 catalog-add"两阶段，registry_commit 指向导入提交（`2837c8b`)。
- 评审 Important 修复选择"拒绝前缀内任何忽略文件"（而非静默排除），与设计"clean committed checkout"语义一致。

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| `tests.test_core_snapshot` | PASS | 35/35（含固定向量与 3 个评审回归） |
| 真实快照 `verify` CLI | PASS | 盘上独立复算 |
| 快照与抢救源逐字节核对（评审） | PASS | 34 文件零偏差 |
| 固定向量独立复算（评审） | PASS | 与钉住值一致 |
| 全量（隔离 venv) | 307/309 | 2 项 real-uvicorn 502 在基线同现，环境性 |
| 抢救源忽略文件检查 | PASS | core/ 下无忽略文件 |

## Known Failures

- 服务器仓 `tests/test_http_integration.py` 2 项 real-uvicorn 测试在本机环境 502（基线 `c2a898c` 同现，与 IMPL-1 无关；生产 3.12 venv 无此问题）。
- `node boards/kids-world/structure.test.mjs` 既有失败，与本任务无关。

## Risks and Caveats

- 服务器仓分支 `codex/api-01-core-snapshot`（含快照资产）尚未 push;IMPL-2 依赖其存在。
- 评审 M-3 记录项：路径替换测试目前只覆盖 size pin(inode pin 理论残存，威胁模型内可接受）;`import_snapshot` 并发 rename 竞态以 OSError 逃逸（CLI 已映射 exit 3)。
- 快照部署到生产 `/opt/cognitive-card-server/` 属后续批次（与 IMPL-3 服务器面一起），本批不部署。

## Remaining Work

1. 用户授权后：push 服务器仓分支 `codex/api-01-core-snapshot`。
2. 立项 IMPL-2(input contract:generation-input-v1 schema、resolver/validator、template composite、固定向量）。
3. 后续：IMPL-3..5、RENDER-01、QA-01、PUBLISH-01、ACCEPT-01。

## Exact Next Action

向用户报告 IMPL-1 完成并请求 push 服务器仓分支；随后按设计 §16 建立 API-01-IMPL-2 任务。

## Recovery Notes

- kids 仓基线 `b5b202c`(== origin/main 前状态）；服务器仓基线 `c2a898c`。
- 快照：snapshot_id `sha256:47d2cb65…d4c1`,registry_commit `2837c8b`；抢救分支 `4d5ffe4`；存档 tag 封存。
- 生产 stable `0.1.1`，本批零现网接触。
