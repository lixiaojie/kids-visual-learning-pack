# Current Task

## Metadata

- Updated At: 2026-09-01
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`；server `knowledge-pipeline-v1` 只打生产 release，默认不 merge `main`
- Base Commit: da45e4f

## Objective

**KNOW-03-prod 切片 A 已完成。** 现网 `current` 从 WB-01 `115377b` 指到 KNOW-03 `7aaeb2b80e591f348c54eb35fb18793e213c5122`。library / 画廊 / Nginx snippet 未改。未 merge server `main`、未 push、未 reload Nginx、未种子格温。

## Background

- KNOW-03 本机已 DONE。操作者点名 `KNOW-03-prod` 并选择切片 A（只换应用）。切片 B/C 未授权。
- 打 release 时 kids HEAD 为 `da45e4f`（写入 release `operations_commit`）。本批证据随后提交，不改归档。

## Acceptance Criteria

- [x] 路线图含 `KNOW-03-prod`；范围锁定为切片 A
- [x] 从干净 `knowledge-pipeline-v1` @ `7aaeb2b` 构建 release；builder JSON 的应用提交与三个 SHA-256 已记录
- [x] 生产 `current` 指向 `7aaeb2b` release 目录；旧 `115377b` 目录保留
- [x] 第 4 节健康检查：health/capabilities `0.3.1`、唯一 `127.0.0.1:8765`、`NRestarts=0`、SQLite integrity `ok`
- [x] 公开画廊 `/card-os/` 仍列出 `rabbit`；PDF 字节与 WB-01 记录一致（1,728,853）
- [x] `/card-os/ops/` 无 token 仍不泄露命题；Nginx snippet SHA 仍为 WB-01 值（本刀未 reload）
- [x] 生产 library `rabbit` current 仍为 AUTHOR-02（4 单元 / 8 命题）；无格温路径
- [x] 未 merge server `main`、未 push、未 add `outputs/` 或 server `uv.lock`
- [x] 运维记录新增第 12 节不可变身份与回滚（指回 `115377b`）

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- 从 server worktree `7aaeb2b` 构建并安装生产 release（不改 server Git 历史）

## Out of Scope

- 重种生产 knowledge-library（切片 B，KNOW-03 修订后的兔子夹具）
- 只打本机制品不上现网（切片 C）
- reload 生产 Nginx 或改 snippet
- merge server `main`、push、`outputs/`、`uv.lock`
- 格温 / 画廊新包 / kids-world / 小程序
- WB-02 / WB-03 / API-01 实现

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 工作区继续按 ADR-003 三角色；kids 与 server 分开提交。
- 升级走 `docs/operations/cognitive-card-server-deployment-2026-07-14.md` 第 6 节；本批 `APP_COMMIT` 与 `EXPECTED_*` 不得沿用 WB-01 的 `115377b` 摘要。
- 安装器不得覆盖同名 release；不得删除 `/var/lib/cognitive-card-server` 或已验证备份。

## Verification Plan

- `bash scripts/ai/check-doc-governance.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `git diff --check`
- 生产第 4 节只读健康检查 + 画廊/ops/library 抽查（见验收项）

## Relevant References

- `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/cognitive-card-os-roadmap.md`
