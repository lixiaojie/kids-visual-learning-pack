# Latest Handoff

## Metadata

- Updated At: 2026-09-03
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: ebf3034
- Kids HEAD: ea7658d
- Server Branch: `knowledge-pipeline-v1` @ `54092cb`
- Working Tree: kids 未提交 COMPOSE-01 文档；未跟踪 `outputs/`。server 未提交 compose 实现；未跟踪 `uv.lock`
- Task Status: **Done（COMPOSE-01 本机实施与 focused 测试已过；未 commit、未生产、未标 IMG-01 DONE）。**

## Summary

COMPOSE-01 已在隔离 candidate 根落地：无字主图 + 锁定四卡 → ops HTML 四段页，观察卡页顶图像带重渲。ChatGPT 不烧字。知识卡 PNG 字节不变。无图 `generate_from_mapping` 仍可用。

## Completed

- COMPOSE-01 spec / 实施计划 / 文档地图 / 路线图
- server 门禁、ops HTML、OBS 图像带、HTTP 鉴权与匿名壳测试
- focused 回归 109 tests OK（含 IMG-01 / WB-03）
- 隔离 TestClient；未写生产 library、未开现网 8765

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md` | 未提交 |
| kids | `docs/superpowers/plans/2026-09-03-operator-composite-projection-display-implementation-plan.md` | 未提交 |
| kids | `docs/README.md` / `docs/cognitive-card-os-roadmap.md` / `docs/ai/*` | 未提交 |
| kids | `outputs/` | 未跟踪；未纳入 |
| server | `src/cognitive_card_server/knowledge_compose/` | 未提交 |
| server | `src/cognitive_card_server/four_card_render/{weighted_layout.py,render.py}` | 未提交 |
| server | `src/cognitive_card_server/knowledge_ops/{http.py,pages.py}` | 未提交 |
| server | `src/cognitive_card_server/http/{app.py,errors.py}` | 未提交 |
| server | `tests/test_knowledge_compose.py` / `tests/test_http_knowledge_compose.py` / `tests/test_weighted_layout.py` / `tests/test_http_auth.py` | 未提交 |
| server | `uv.lock` | 未跟踪；未纳入 |

## Decisions Made

- 屏幕 HTML + 打印 OBS 图像带；不烧字。
- 输入门禁：`illustrated` + `awaiting_review`。插画六键等于 knowledge current；工作区 mapping-identity 等于现活 pointer。
- 主图只进 `CN_OBS:band` / `EN_OBS:band`。打印带上限 720 px，实际高度取 look 剩余减 gap。
- `PROTECTED_ROUTES` 现为 49（新增 POST/GET compose；ops HTML 不是受保护 API）。
- 无图 generate 保持可用。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `main` @ `ea7658d` | 不 push |
| 知识管线 | `knowledge-pipeline-v1` @ `54092cb`+ 未提交 | 不 merge、不 push |
| 本机验收 | TestClient 临时 `database` / `candidate_root` | 不写生产 library、不开 8765 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server focused unittest（109 tests） | PASS | IMG-01 + WB-03 + compose；37.8s |
| kids `git diff --check` | PASS | 无空白错误 |
| server `git diff --check` | PASS | 无空白错误 |
| `bash scripts/ai/check-task-state.sh` | PASS | Status Done，验收全勾选 |
| `bash scripts/ai/check-handoff.sh` | WARN | Base Commit `ebf3034` 落后 HEAD `ea7658d`（既有） |
| `bash scripts/ai/check-doc-governance.sh` | WARN | Last Reviewed 2026-07-24 过期（既有） |

## Known Failures

- 文档地图 Last Reviewed 过期 WARN（既有，2026-07-24）。
- server 全量 discover fastapi/httpx import errors=11；与本刀无关。
- 现网应用仍 `7aaeb2b`。

## Risks and Caveats

- 不要把 `uv.lock` 或 `outputs/` 加入提交。
- 不要标 IMG-01 `DONE`。
- 打印图像带在兔子夹具上远小于 720 px；屏幕 HTML 仍展示完整 PNG。
- ops `/card-os/ops/compose` 无 topic 会落到主题详情（slug=`compose`），真正合成页是 `/card-os/ops/compose/{topic}`。

## Remaining Work

操作者决定是否 commit；视觉看一眼 HTML 合成页（可选）。不 merge、不 push、不 reload Nginx、不写生产 library。

## Exact Next Action

若要把本刀写入 Git：先在 kids `main` 提交 COMPOSE-01 文档（排除 `outputs/`），再在 server worktree `knowledge-pipeline-v1` 提交 `knowledge_compose` 与相关测试（排除 `uv.lock`）。不要 merge `main`、不要 push、不要 reload Nginx、不要标 IMG-01 `DONE`。

## Recovery Notes

- 任务：COMPOSE-01 本机实施完成，未生产
- Spec：`docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`
- Plan：`docs/superpowers/plans/2026-09-03-operator-composite-projection-display-implementation-plan.md`
- Kids HEAD：`ea7658d`
- Server Git：`54092cb`（工作区另有未提交 compose）
- HTTP：`POST /card-os/api/v1/admin/knowledge-compose`；`GET .../knowledge-compose/{topic}`；ops `/card-os/ops/compose/{topic}`
- library 回滚：`knowledge-library.20260901T070549Z.pre-know04`
- 应用回滚目标仍是 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`
