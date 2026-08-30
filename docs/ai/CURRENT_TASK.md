# Current Task

## Metadata

- Updated At: 2026-08-30
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: main（kids 任务治理）；codex/knowledge-core-contract-v1（AUTHOR）；codex/api-01-generation-input-v1（IMPL-2）
- Base Commit: kids 5986d8d；knowledge-core `1facb79`；IMPL-2 `878a28d`

## Objective

用户已授权：三个工作区分别提交，互不混入。knowledge-core 单独 commit AUTHOR-02/03/04；IMPL-2 单独 commit IMPL-2/3/4 + snapshot compat + catalog 新条目；kids `main` 单独 commit 三份任务文档。IMPL-2 commit 后在交接层补记 ae563e 的真实 introducing commit，不改 catalog 的 `registry_commit`。不 push、不 merge、不 deploy、不打现网 HTTPS。

## Background

- 上一任务（兔子 generate A→B→C）已在本机 loopback 验收 Done。
- Exact Next Action 要求授权后再分工作区提交。用户于 2026-08-30 明确授权三个工作区分别提交。

## Acceptance Criteria

- [x] knowledge-core worktree 单独一次 commit，不含 IMPL 文件
- [x] IMPL-2 worktree 单独一次 commit，不含 AUTHOR 文件；catalog 的 `registry_commit` 未改
- [x] 交接层记录 ae563e 的真实 introducing commit
- [x] kids `main` 单独一次 commit：仅 `docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`；`outputs/` 排除
- [x] 各工作区提交前 focused tests 与 `git diff --check` 通过
- [x] 未 `--no-verify`；未 push/merge/deploy；未打现网 HTTPS

## In Scope

- knowledge-core worktree（`.worktrees/cognitive-card-server-knowledge-core`）：authoring 模块、authoring 测试、README、四份 examples/authoring 试产 JSON（提交，不改代码）
- IMPL-2 worktree（`.worktrees/cognitive-card-server-api-01-impl-2`）：已有 IMPL-2/3/4、snapshot compat、catalog 新条目与 ae563e snapshot 目录（提交，不改代码；不改 catalog `registry_commit`）
- kids：`docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`

## Out of Scope

- 改任何实现代码或 catalog 字段
- 纳入 `uv.lock`、`outputs/`、token 文件
- 覆盖 knowledge-core 与 IMPL-2 之外的其他 worktree
- push / merge / deploy / 现网 HTTPS
- 新 Skill release、ACCEPT-01、Portal、Renderer

## Constraints

- 三个 commit 分属三个工作区，一次一个，不混暂存。
- 不要 `--no-verify`。
- catalog 只增不改；`registry_commit` 保持 `9c1b82be69df2da8348f66970a993e9c1984ce6d`，introducing commit 只写交接层。

## Verification Plan

- knowledge-core：authoring unittest 模块 + `git diff --check`
- IMPL-2：generation-input / pipeline / snapshot-compat / http-compiled / auth focused unittest + `git diff --check`
- kids：`git diff --check`、`bash scripts/ai/check-handoff.sh`、`bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/ai/HANDOFF.md` Exact Next Action
- `docs/cognitive-card-os-roadmap.md`
