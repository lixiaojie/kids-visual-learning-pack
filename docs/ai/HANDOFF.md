# Latest Handoff

## Metadata

- Updated At: 2026-09-03
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 8c7c2d8
- Kids HEAD: 8c7c2d8
- Server Branch: `knowledge-pipeline-v1` @ `8710914`（本地提交；未 push）
- Working Tree: IMG-02 kids `8c7c2d8`、server `8710914` 已本地提交；`outputs/` 未跟踪未纳入。server `uv.lock` 未跟踪未纳入。
- Task Status: **In Progress（IMG-02 kids `8c7c2d8`、server `8710914` 已本地提交；未 push、未生产、不标 DONE）。**

## Summary

IMG-02：可选额外无字像素视图已在 server `knowledge-pipeline-v1` 提交为 `8710914`。同一 illustration-intent；`hero.png` 仍是 `observe.isolate`；compose 仍只读 hero。kids spec/plan/路线图对齐。未 merge/push/release。RENDER-02 仍 BACKLOG。

## Completed

- server `8710914`：`views.py` 允许像素键、`illustration-view-v1` 提示词、`views/` 磁盘槽、额外上传 HTTP/ops UI；compose 仍只读 `hero.png`
- spec Approved：`docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`
- 计划：`docs/superpowers/plans/2026-09-03-multi-view-wordless-assets-implementation-plan.md`（Medium，7 tasks / 3 phases）
- 文档地图、系统总设计 §11、路线图 IMG-02
- `test_compose_ignores_extra_view_png` GREEN
- combined focused gate 99 ran：97 PASS，2 FAIL（见 Known Failures）

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md` | `8c7c2d8` 已本地提交 |
| kids | `docs/superpowers/plans/2026-09-03-multi-view-wordless-assets-implementation-plan.md` | `8c7c2d8` 已本地提交 |
| kids | `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md` | `8c7c2d8` 已本地提交 |
| kids | `docs/README.md` | `8c7c2d8` 已本地提交 |
| kids | `docs/cognitive-card-os-roadmap.md` | SHA 记录待本提交纳入 |
| kids | `docs/cognitive-card-os-system-design.md` | `8c7c2d8` 已本地提交 |
| kids | `docs/ai/CURRENT_TASK.md` | SHA 记录待本提交纳入 |
| kids | `docs/ai/HANDOFF.md` | SHA 记录待本提交纳入 |
| kids | `outputs/` | 未跟踪；不纳入 |
| server | illustration / HTTP / ops / compose 测试 | `8710914` 已本地提交 |
| server | `uv.lock` | 未跟踪；不纳入 |

## Decisions Made

- IMG-01 单主图路径**并存**。
- 额外画法**可选子集**。
- 同一 `illustration-intent`；允许键从 current `assign_legend` 来，不经 mapping-lock。
- 须先 `illustrated` 才传额外槽；额外槽可覆盖重传。
- 烧字：额外槽可注入检测器；不交付生产 OCR。
- COMPOSE 仍只消费 `hero.png`；磁盘 `views/` 不得进入 compose `assets`。
- compose 测试里需要 mapping-lock 的夹具改用 `_rabbit_real()`；不把 rabbit-composite 的 `LEGEND_ROLE_MISSING` 当成 IMG-02 去改图例门禁。
- RENDER-02 仍 BACKLOG。不标 IMG-01 / COMPOSE-01 / LEGEND-01 / API-01 / IMG-02 `DONE`。
- 不 merge/push/release；不把 `outputs/` 或 `uv.lock` 纳入。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `main` @ `8c7c2d8` | 不 push；不提交 `outputs/` |
| 知识管线 | `.worktrees/cognitive-card-server-knowledge-core` `knowledge-pipeline-v1` @ `8710914` | 已本地提交；不 push；不改 `uv.lock` |
| 本机验收 | 文档 checker + server combined focused | 不开 8765 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git diff --check` | PASS | kids 根 |
| `bash scripts/ai/check-task-state.sh` | PASS | In Scope 路径均存在 |
| `bash scripts/ai/check-handoff.sh` | PASS | Base Commit 对齐 HEAD `8c7c2d8` |
| `bash scripts/ai/check-doc-governance.sh` | WARN | Last Reviewed 2026-07-24 过期（既有；3 warnings） |
| combined focused gate（server worktree） | FAIL | 99 ran；97 PASS；2 FAIL（见 Known Failures） |

## Known Failures

- 文档地图 Last Reviewed 过期 WARN（既有，2026-07-24）：`PROJECT_CONTEXT.md`、`docs/README.md`、`docs/knowledge/codex-memory/README.md`。与本次修改无关。
- 现网应用仍 `7aaeb2b`。与本次修改无关。
- `tests.test_http_knowledge_ops.HttpKnowledgeOpsTests.test_generate_keeps_current_and_publish_requires_actor`：mapping-lock 返回 `LEGEND_ROLE_MISSING`。夹具 `_short_authoring()` / `rabbit-composite.json`。LEGEND-01 图例门禁，不是 IMG-02。不放宽 `assign_legend`，不为该夹具补 IMG-02 覆盖。
- `tests.test_http_knowledge_ops.HttpKnowledgeOpsTests.test_publish_refuses_stale_work_after_relock`：同上，mapping-lock `LEGEND_ROLE_MISSING` on `_short_authoring()` / rabbit-composite。非 IMG-02。

## Risks and Caveats

- `app.py` 的 multipart 白名单必须同时允许 `/views/.../image`，否则额外上传会被中间件挡掉。
- rabbit-real 的 `allowed_view_keys` 以 `assign_legend` 实测为准，不要硬填满五键。
- 不要把 IMG-02 做成 RENDER-02。
- 不要把 `outputs/` 或 server `uv.lock` 加入提交。
- combined gate 的 2 FAIL 是 LEGEND-01 夹具，不要在 IMG-02 里“修”掉。

## Remaining Work

不要开始 RENDER-02。不要 merge/push/release。不要标 DONE。

## Exact Next Action

不要 push/merge/release。不要开始 RENDER-02。不要标 IMG-02 `DONE`。下一位若要继续，先读 kids `8c7c2d8` 与 server `8710914`，再等操作者授权下一刀（RENDER-02 仍 BACKLOG）。

## Recovery Notes

- Spec：`docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`
- Plan：`docs/superpowers/plans/2026-09-03-multi-view-wordless-assets-implementation-plan.md`
- Server：`.worktrees/cognitive-card-server-knowledge-core` @ `8710914`
- Combined gate：99 ran；97 PASS；2 FAIL（ops mapping-lock `LEGEND_ROLE_MISSING`）
