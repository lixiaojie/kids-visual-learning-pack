# Latest Handoff

## Metadata

- Updated At: 2026-09-01
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: da45e4f
- Kids HEAD: da45e4f `docs(ai): record KNOW-03 DONE kids commit SHA`
- Server Branch: `knowledge-pipeline-v1` @ `7aaeb2b80e591f348c54eb35fb18793e213c5122`
- Working Tree: 干净（除既有未跟踪 `outputs/`）；server `uv.lock` 未纳入
- Task Status: **Done（KNOW-03-prod 切片 A：现网 `current`=`7aaeb2b`；library / Nginx 未改）。** 下一刀须新 CURRENT_TASK。

## Summary

操作者选择切片 A。已从 `7aaeb2b` 打 release 并安装：生产 `current` 从 `115377b` 指到 `7aaeb2b`。library 三个文件哈希与安装前相同；Nginx snippet SHA 未变，未 reload。画廊 PDF 仍 1,728,853 bytes。未 merge server `main`、未 push、未种子格温。

## Completed

- 账本登记 `KNOW-03-prod` 并完成切片 A。
- release：归档 `cf16a42b…d534d`；sidecar `13df7ee9…d9b13`；安装器 `e34e0b91…47803`（与 WB-01 相同）。
- 现网 `status=installed release=7aaeb2b`；旧 `115377b` 目录保留。
- 第 4 节 + 画廊/ops/library 抽查通过。运维记录第 12 节已写。

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md` | 本提交：KNOW-03-prod Done |
| kids | `docs/cognitive-card-os-roadmap.md`、`docs/cognitive-card-os-system-design.md` | 本提交：登记 ID 并标 DONE |
| kids | `docs/operations/cognitive-card-server-deployment-2026-07-14.md` | 本提交：第 12 节 |
| server | 无 Git 改动 | 仍 `7aaeb2b`；仅生产 release 目录 |

## Decisions Made

- 切片 A only。B（重种兔子）与 C（只打制品）未做。
- 操作者 2026-09-01 明确：先不走切片 B，回到知识主路径；默认仍不实施 WB-02。
- 不实施 WB-02。不 reload Nginx。不 merge server `main`。不 push。
- 格温不上画廊 / 生产 library / 小程序。
- kids 与 server 分开提交。server 本刀无新 commit。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `main` @ `da45e4f` + 本提交 | 不改 server 提交 |
| 知识管线 | knowledge-core worktree @ `7aaeb2b` | 已打生产 release；未 merge `main` |

三角色划分与活 checkout 上限见 ADR-003。

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `bash scripts/ai/check-task-state.sh` | PASS | Status Done；验收项全部勾选 |
| `bash scripts/ai/check-handoff.sh` | PASS | Base Commit `da45e4f` 与 HEAD 一致 |
| `bash scripts/ai/check-doc-governance.sh` | WARN | 3× Last Reviewed 过期（既有，2026-07-24） |
| `git diff --check` | PASS | |
| 生产 `current`=`7aaeb2b`；health `0.3.1`；`NRestarts=0` | PASS | 安装器 `status=installed` |
| library 三文件 SHA 安装前后相同 | PASS | AUTHOR-02 4/8/4；无格温 |
| Nginx snippet SHA 仍 `0ed25814…`；未 reload | PASS | |
| 画廊 PDF 1,728,853；ops 无 token 无命题泄漏；admin `401` | PASS | |
| 未 merge server `main` / 未 push | PASS | |

## Known Failures

- 文档地图 Last Reviewed 过期 WARN（既有，2026-07-24）。
- server 全量 discover errors=11：10×缺 `fastapi`，1×缺 `httpx`；与本刀无关。
- 安装器 apt update 曾 `Timeout was reached`，随后 `python3-venv`/`sqlite3` 已是最新；安装仍完成。

## Risks and Caveats

- 现网跑 KNOW-03 代码，但 library 仍是 AUTHOR-02 兔子（coverage legacy skip）。要看见修订后的兔子知识源须另授权切片 B。
- 应用回滚是把 `current` 指回 `115377b` 并重启 API unit；本批未演练。
- release `operations_commit` 封印为 `da45e4f`；证据文档提交后 kids HEAD 会前移，不改归档。

## Remaining Work

无 KNOW-03-prod 实现剩余。切片 B 已搁下。编号队列下一格是 WB-02（Parked），不能 silently skip 后做 WB-03。下一刀须操作者点名一个路线图 ID。

## Exact Next Action

**停止实现。** 等操作者点名一个主线路线图 ID，先改写 `docs/ai/CURRENT_TASK.md` 再动手。不要实施 WB-02、不要做切片 B、不要 reload Nginx、不要 merge server `main`，除非该会话明确授权。

## Recovery Notes

- 任务：KNOW-03-prod 切片 A DONE；现网 `7aaeb2b`。
- Kids HEAD：`da45e4f`；工作区有未提交证据。
- Server Git：`7aaeb2b80e591f348c54eb35fb18793e213c5122` on `knowledge-pipeline-v1`。
- 回滚目标：`115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`。
- 证据：运维记录第 12 节。
