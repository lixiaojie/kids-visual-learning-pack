# Current Task

## Metadata

- Updated At: 2026-09-09
- Updated By: Cursor Grok 4.6
- Status: In Progress
- Branch: kids `main`；server `main` / `knowledge-pipeline-v1` @ `7ff8369`
- Base Commit: a108b18

## Objective

操作者已授权 merge/push。server `origin/main` 已 fast-forward 到 `7ff8369`。本回合提交隔离走通与 merge/push 记录并 push kids `main`。不标 DONE、不写现网 catalog、不 reload Nginx、不打 release。

## Background

Spec：`docs/superpowers/specs/2026-09-08-operator-pack-layout-dual-gallery-design.md`。
Plan：`docs/superpowers/plans/2026-09-08-operator-pack-layout-dual-gallery-implementation-plan.md`。
执行工位：`.worktrees/cognitive-card-server-knowledge-core`。不得还原该树上已有未提交对照表/compose 补丁。不得动 `uv.lock`。不得覆盖 `AGENTS.md`。

## Acceptance Criteria

- [x] spec 与计划落盘
- [x] Task 1 catalog / GET draft / PATCH selected
- [x] Task 2 PATCH placement
- [x] Task 3 print sample + lock_pack_layout + compose-lock 409
- [x] Task 4 HTTP + ops pack
- [x] Task 5 numbered package + PORTAL + kids docs
- [x] `dino-walk.local` 隔离走通 pack-layout 上架（剑龙 `revision-0002`）
- [x] server `main` 已 fast-forward 到 `7ff8369` 并 push `origin/main`
- [ ] kids `main` 已 push 到 origin（本提交之后）
- [ ] 不标 FLOW-01 / PUBLISH-02 / IMG-03 / PACK-01 `DONE`
- [ ] 未写现网 catalog、未 reload Nginx

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- kids `git push origin main`（不含 `AGENTS.md`、`outputs/`）

## Out of Scope

- OpenAI / 图像 API、Skill claim
- 改四对象 schema；现网 catalog；reload Nginx；打 release
- `outputs/`、server `uv.lock`、`AGENTS.md`
- 还原 server 树上已有未提交对照表与 age 补丁
- 修 ops mapping-lock `LEGEND_ROLE_MISSING`
- 删除 `knowledge-pipeline-v1` worktree
- 标 PACK-01 `DONE`

## Constraints

- 不覆盖 `AGENTS.md` 未提交修改。
- 不把 admin token 写入聊天或仓库。
- 不 force-push。

## Verification Plan

- 合并前 combined focused gate（311 ran / 309 ok / 2 FAIL 已知 `LEGEND_ROLE_MISSING`）
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `git diff --check`
- `origin/main` SHA 核对

## Relevant References

- `docs/superpowers/specs/2026-09-08-operator-pack-layout-dual-gallery-design.md`
- `docs/superpowers/plans/2026-09-08-operator-pack-layout-dual-gallery-implementation-plan.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
