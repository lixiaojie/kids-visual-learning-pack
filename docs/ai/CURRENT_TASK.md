# Current Task

## Metadata

- Updated At: 2026-09-01
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`；server `knowledge-pipeline-v1` 只读编译，默认不 merge `main`、不打新 release
- Base Commit: 8bcf645

## Objective

**KNOW-04 已完成。** 现网应用仍为 `7aaeb2b`。生产 knowledge-library 现有六主题 current（不含格温）。`rabbit` current=`revision-0002`，AUTHOR-02 `0001` 保留。画廊 / Nginx snippet 未改。未 merge server `main`、未 push。

## Background

- KNOW-03-prod 切片 A 已把现网应用换到 coverage 代码；本刀只上库。
- 操作者点名上一轮菜单项「新知识源切片」。
- 兔子 topic.revision=2 只在编译副本上发生，未改已提交的兔子夹具。

## Acceptance Criteria

- [x] 路线图含 `KNOW-04`；范围锁定为生产 library 种子（6 主题，不含格温）
- [x] 本机编译并通过 coverage 门：鹅掌藤、霸王龙、故宫、四渡赤水、牛顿第一定律（均为 revision 1）以及 KNOW-03 修订兔子夹具以 revision 2
- [x] 生产 library 六主题均有 current；`rabbit` current=`revision-0002`，`revision-0001` 仍在
- [x] 生产无 `spider-gwen` 路径
- [x] 公开画廊仍只列 `rabbit`；PDF 仍 1,728,853 bytes
- [x] `/card-os/ops/` 无 token 仍不泄露命题；Nginx snippet SHA 未变、未 reload
- [x] 应用 `current` 仍为 `7aaeb2b`；未 merge server `main`、未 push、未 add `outputs/` 或 server `uv.lock`

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-01-knowledge-suite-library-seed-design.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- 用 server worktree `7aaeb2b` 本机编译并写入生产 knowledge-library（不改 server Git 历史）

## Out of Scope

- 格温上库 / 画廊 / 小程序
- 新打应用 release 或改 `/opt/cognitive-card-server/current`
- reload 生产 Nginx 或改 snippet
- merge server `main`、push、`outputs/`、`uv.lock`
- WB-02 / WB-03 / API-01 实现
- kids-world / 四卡生成

## Constraints

- Card OS 任务账本只在 `docs/cognitive-card-os-roadmap.md` 更新。
- 工作区继续按 ADR-003 三角色；kids 与 server 分开提交。
- 不覆盖已有 `rabbit/revision-0001`；新兔子必须是 `revision-0002`。
- 安装器不得覆盖同名 release；不得删除 `/var/lib/cognitive-card-server` 或已验证备份。

## Verification Plan

- `bash scripts/ai/check-doc-governance.sh`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `git diff --check`
- 本机六主题 compile + library publish
- 生产 library 目录抽查 + 画廊/ops 只读抽查

## Relevant References

- `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md`
- `docs/superpowers/specs/2026-09-01-knowledge-suite-library-seed-design.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/cognitive-card-os-roadmap.md`
