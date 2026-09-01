# Latest Handoff

## Metadata

- Updated At: 2026-09-01
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 8bcf645
- Kids HEAD: 8bcf645 `docs(card-os): record KNOW-04 suite library seed evidence`
- Server Branch: `knowledge-pipeline-v1` @ `7aaeb2b80e591f348c54eb35fb18793e213c5122`
- Working Tree: 本提交收录 KNOW-04 治理/运维证据；既有未跟踪 `outputs/`；server `uv.lock` 未纳入
- Task Status: **Done（KNOW-04：生产 library 六主题 current；应用仍 `7aaeb2b`；Nginx / 画廊未改）。** 下一刀须新 CURRENT_TASK。

## Summary

操作者点名「新知识源切片」。已把 KNOW-03 兼容套件里允许上库的六主题写入生产 knowledge-library。`rabbit` current 现为 KNOW-03 修订 `revision-0002`；AUTHOR-02 `0001` 保留。无格温。应用、Nginx、画廊 PDF 未改。未 merge server `main`、未 push。

## Completed

- 账本登记 `KNOW-04` 并完成上库。
- 本机编译六主题过 coverage 门；生产 `publish` 六个包。
- 预写备份：`knowledge-library.20260901T070549Z.pre-know04`。
- 第 4 节健康 + 画廊/ops 抽查通过。运维记录第 13 节已写。

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md` | 本提交：KNOW-04 Done |
| kids | `docs/cognitive-card-os-roadmap.md`、`docs/cognitive-card-os-system-design.md`、`docs/README.md` | 本提交：登记并标 DONE |
| kids | `docs/superpowers/specs/2026-09-01-knowledge-suite-library-seed-design.md` | 本提交：新建 |
| kids | `docs/operations/cognitive-card-server-deployment-2026-07-14.md` | 本提交：第 13 节 |
| server | 无 Git 改动 | 仍 `7aaeb2b`；仅生产 library 目录 |

## Decisions Made

- 新 ID `KNOW-04`，不是 KNOW-03-prod 切片 B 的名义，但包含修订兔子 current。
- 格温不上库。不 reload Nginx。不换应用。不实施 WB-02。
- 兔子 `topic.revision=2` 只在编译副本上发生。
- kids 与 server 分开提交。server 本刀无新 commit。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `main` @ `8bcf645` | 不改 server 提交 |
| 知识管线 | knowledge-core worktree @ `7aaeb2b` | 只读编译；未 merge `main` |

三角色划分与活 checkout 上限见 ADR-003。

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| 本机六主题 compile + publish | PASS | 无格温；兔子 rev=2 |
| 生产 `publish` 六包 | PASS | `rabbit` current=2；`0001` 摘要未变 |
| 生产 `current`=`7aaeb2b`；health `0.3.1`；`NRestarts=0` | PASS | |
| 画廊 PDF 1,728,853；只列 `rabbit` | PASS | |
| ops 无 token 无命题泄漏；admin `401` | PASS | Nginx SHA 未变 |
| 未 merge server `main` / 未 push | PASS | |
| `bash scripts/ai/check-task-state.sh` | PASS | Status Done；验收项全部勾选 |
| `bash scripts/ai/check-handoff.sh` | PASS | Base Commit `8bcf645` 与证据提交一致 |
| `bash scripts/ai/check-doc-governance.sh` | WARN | 3× Last Reviewed 过期（既有，2026-07-24） |
| `git diff --check` | PASS | |

## Known Failures

- 文档地图 Last Reviewed 过期 WARN（既有，2026-07-24）。
- server 全量 discover errors=11：fastapi/httpx；与本刀无关。

## Risks and Caveats

- 操作台现在能列出六个知识源；公网四卡仍只有 ACCEPT-01 兔子包。
- library 回滚是换回 `knowledge-library.20260901T070549Z.pre-know04`；本批未演练。
- 证据文档提交后 kids HEAD 会前移，不改应用归档。

## Remaining Work

无 KNOW-04 实现剩余。编号队列下一格是 WB-02（Parked），不能 silently skip 后做 WB-03。下一刀须操作者点名一个路线图 ID。

## Exact Next Action

**停止实现。** 等操作者点名一个主线路线图 ID，先改写 `docs/ai/CURRENT_TASK.md` 再动手。不要实施 WB-02、不要 reload Nginx、不要 merge server `main`，除非该会话明确授权。可将本批 7 个治理/运维文件入库。

## Recovery Notes

- 任务：KNOW-04 DONE；现网应用 `7aaeb2b`；library 六主题。
- Kids HEAD：`8bcf645` `docs(card-os): record KNOW-04 suite library seed evidence`。
- Server Git：`7aaeb2b80e591f348c54eb35fb18793e213c5122`。
- library 回滚：`/var/backups/cognitive-card-server/knowledge-library.20260901T070549Z.pre-know04`。
- 应用回滚目标仍是 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`。
- 证据：运维记录第 13 节。
