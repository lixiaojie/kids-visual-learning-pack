# Latest Handoff

## Metadata

- Updated At: 2026-09-01
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 42b3522
- Kids HEAD: 42b3522 `docs(ai): record KNOW-04 kids commit SHA`（本提交记录 WB-02）
- Server Branch: `knowledge-pipeline-v1` @ `5c1188074846acbf8652ccb888792080697d140e`
- Working Tree: kids 本提交后仅余既有未跟踪 `outputs/`；server 仅余未跟踪 `uv.lock`
- Task Status: **Done（WB-02 已分别提交；未现网）。**

## Summary

WB-02 已提交。server `5c11880` 实现映射预览/锁定，不移动 knowledge current。kids 本提交收录批准 spec、实施计划与路线图 Done。未打 release、未 reload Nginx、未改画廊。

## Completed

- server：`5c1188074846acbf8652ccb888792080697d140e` `feat(knowledge): lock projection mapping without moving current`
- kids：WB-02 spec / plan / 路线图 / 任务与交接（本提交）
- 未纳入 `outputs/`、server `uv.lock`

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| server | mapping / safety registry / ops HTTP+第三块 / focused tests | 已提交 `5c11880` |
| kids | `docs/superpowers/specs/2026-09-01-operator-mapping-scheme-design.md` | 本提交：Approved spec |
| kids | `docs/superpowers/plans/2026-09-01-operator-mapping-scheme-implementation-plan.md` | 本提交 |
| kids | `docs/superpowers/specs/2026-08-31-four-card-text-mature-projection-design.md` | 本提交：Parked 注记 |
| kids | `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、路线图、系统设计、`docs/README.md` | 本提交 |
| kids | `outputs/` | 未跟踪；未纳入 |
| server | `uv.lock` | 未跟踪；未纳入 |

## Decisions Made

- WB-02 = 映射确认，不是四卡排版填满。
- `lock_mapping` 写新 revision + `mapping.json`，不调用会移动 current 的 `publish`。
- 新 mapping 包必须抬四对象 `revision`；事实载荷对齐后与 current 相等。
- 像素溢出进 sources 明确禁止。
- 安全中文走登记表；GAP 时不得锁定 four-card。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `main` 本提交 | 不改 server |
| 知识管线 | knowledge-core worktree @ `5c11880` | 不 merge `main`、不 push、不打 release |

三角色划分与活 checkout 上限见 ADR-003。

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server focused unittest（40 项，含 library / ops / safety） | PASS | 提交前已跑 |
| `bash scripts/ai/check-task-state.sh` | PASS | 以本回合重跑为准 |
| `bash scripts/ai/check-handoff.sh` | PASS | Base Commit `42b3522` |
| `bash scripts/ai/check-doc-governance.sh` | WARN | 3× Last Reviewed 过期（既有） |
| kids `git diff --check` | PASS | |
| 现网 / Nginx / 画廊 | 未执行 | 本刀不改 |

## Known Failures

- 文档地图 Last Reviewed 过期 WARN（既有，2026-07-24）。
- server 全量 discover errors=11：fastapi/httpx；与本刀无关。

## Risks and Caveats

- 现网应用仍为 `7aaeb2b`；画廊仍是 ACCEPT-01。本刀提交 ≠ 安装。
- 现网 `publish` 若被误用会抢走兔子 chaptered-guide current。

## Remaining Work

WB-03 另立设计后再实施。不要 merge server `main`、不要 push、不要打 release、不要 reload Nginx。

## Exact Next Action

另立会话写 **WB-03** 设计（按映射 revision 生成并上架画廊）。不要 merge server `main`、不要 push、不要打 release、不要 reload Nginx、不要把 `uv.lock` 或 `outputs/` 加入提交。

## Recovery Notes

- 任务：WB-02 Done；server `5c11880`；kids 本提交。
- Kids HEAD：见本提交后 `git rev-parse HEAD`。
- Server Git：`5c1188074846acbf8652ccb888792080697d140e`。
- library 回滚：`knowledge-library.20260901T070549Z.pre-know04`。
- 应用回滚目标仍是 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`。
