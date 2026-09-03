# Latest Handoff

## Metadata

- Updated At: 2026-09-03
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: ebf3034
- Kids HEAD: 18375cf
- Server Branch: `knowledge-pipeline-v1` @ `ec22a33`
- Working Tree: kids 仅未跟踪 `outputs/`；server 仅未跟踪 `uv.lock`
- Task Status: **Done（COMPOSE-01 已本地提交；未生产、未 push、未标 IMG-01 DONE）。**

## Summary

COMPOSE-01 已本地提交：无字主图 + 锁定四卡 → ops HTML 四段页，观察卡页顶图像带重渲。ChatGPT 不烧字。知识卡 PNG 字节不变。无图 `generate_from_mapping` 仍可用。

## Completed

- COMPOSE-01 spec / 实施计划 / 文档地图 / 路线图
- server 门禁、ops HTML、OBS 图像带、HTTP 鉴权与匿名壳测试
- focused 回归 109 tests OK（含 IMG-01 / WB-03）
- 隔离预览与本地提交；未写生产 library、未开现网 8765

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | COMPOSE-01 spec / plan / `docs/README.md` / 路线图 / `docs/ai/*` | `18375cf` |
| kids | `outputs/` | 未跟踪；未纳入 |
| server | `knowledge_compose`、OBS 图像带、ops HTML、compose 测试 | `ec22a33` |
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
| kids 治理 | `main` @ `18375cf` | 不 push |
| 知识管线 | `knowledge-pipeline-v1` @ `ec22a33` | 不 merge、不 push |
| 本机验收 | TestClient / `/tmp/compose-01-preview` | 不写生产 library、不开 8765 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server focused unittest（109 tests） | PASS | IMG-01 + WB-03 + compose |
| kids commit `18375cf` | PASS | 排除 `outputs/` |
| server commit `ec22a33` | PASS | 排除 `uv.lock` |
| `bash scripts/ai/check-task-state.sh` | PASS | 上次运行全绿 |
| `bash scripts/ai/check-handoff.sh` | WARN | Base Commit 落后 HEAD（既有） |
| `bash scripts/ai/check-doc-governance.sh` | WARN | Last Reviewed 2026-07-24 过期（既有） |

## Known Failures

- 文档地图 Last Reviewed 过期 WARN（既有，2026-07-24）。
- server 全量 discover fastapi/httpx import errors=11；与本刀无关。
- 现网应用仍 `7aaeb2b`。

## Risks and Caveats

- 不要把 `uv.lock` 或 `outputs/` 加入提交。
- 不要标 IMG-01 `DONE`。
- 打印图像带在兔子夹具上远小于 720 px；屏幕 HTML 仍展示完整 PNG。
- 不要 merge server `main`、不要 push、不要 reload Nginx。

## Remaining Work

不生产、不 merge、不 push。下一刀另开任务。

## Exact Next Action

不要 merge `main`、不要 push、不要 reload Nginx、不要标 IMG-01 `DONE`。新切片须另开 `CURRENT_TASK`。

## Recovery Notes

- 任务：COMPOSE-01 已本地提交，未生产
- Spec：`docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`
- Plan：`docs/superpowers/plans/2026-09-03-operator-composite-projection-display-implementation-plan.md`
- Kids：`18375cf`
- Server：`ec22a33`
- HTTP：`POST /card-os/api/v1/admin/knowledge-compose`；`GET .../knowledge-compose/{topic}`；ops `/card-os/ops/compose/{topic}`
- library 回滚：`knowledge-library.20260901T070549Z.pre-know04`
- 应用回滚目标仍是 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`
