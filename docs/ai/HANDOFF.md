# Latest Handoff

## Metadata

- Updated At: 2026-09-02
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 2238377
- Kids HEAD: 2238377 `docs(ai): record WB-02 kids commit SHA`
- Server Branch: `knowledge-pipeline-v1` @ `91b7cf31ad47a7faf7b239af2f0aa198cf838e55`
- Working Tree: kids 待提交 Card OS 文档（不含 `outputs/`）；server 仅余未跟踪 `uv.lock`
- Task Status: **Paused（API-01-TPL 已随 server `91b7cf3` 提交；kids 文档本回合提交；未现网）。**

## Summary

Server `91b7cf3` 提交 compile-intent、ChatGPT JSON 归一、mapping-artifact 与加权版式。库存未改写 `ragdoll-chatgpt.json` 可编过。未打 release、未 merge `main`、未 push、未开 8765。`uv.lock` 与 `outputs/` 未纳入。

## Completed

- Server commit `91b7cf3` `feat(knowledge): compile ChatGPT replies into library current`
- 加厚 `knowledge-compile-v1` + parse 归一（§10.1）
- 试用 JSON 7 units 无需人工映射脚本

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| server | compile + artifact + weighted + tests | **committed** `91b7cf3` |
| server | `uv.lock` | 未跟踪；未纳入 |
| kids | `docs/ai/*`、路线图、compile/WB-03 spec/plan、`docs/README.md` | 本回合提交 |
| kids | `outputs/` | 未纳入 |

## Decisions Made

- ops 文件与 WB-03 缠在一起，server 一次提交 compile + mapping-artifact，不拆。
- 不提交 `uv.lock`、`outputs/`。
- 不把 `API-01` 标路线图 `DONE`（未现网）。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `main`；本回合提交文档 | 不 push 除非另授权 |
| 知识管线 | `knowledge-pipeline-v1` @ `91b7cf3` | 不 merge `main`、不 push、不打 release |

三角色划分见 ADR-003。

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| server focused compile tests | PASS | 27 tests（提交前） |
| 库存 ragdoll ChatGPT JSON compile | PASS | 7 units |
| kids `check-task-state` | PASS | Paused |
| kids `check-handoff` | PASS | 提交前复核 |
| `git diff --check` | PASS | 无 whitespace 错误 |

## Known Failures

- 文档地图 Last Reviewed 过期 WARN（既有，2026-07-24）。
- server 全量 discover fastapi/httpx import errors=11；与本刀无关。
- 打印样式未验收：有意后置。
- 现网应用仍 `7aaeb2b`。

## Risks and Caveats

- `/tmp/card-os-api01` 仍含试用数据；不要当生产。
- 归一只覆盖 mammal 分类学与试用见到的键。
- 不要把 `uv.lock` 或 `outputs/` 加入提交。

## Remaining Work

可选授权 push / 生产安装。其后 **IMG-01** 设计。不要开 `IMG-01` 实施，除非写入 CURRENT_TASK。

## Exact Next Action

不要 push、不要安装生产，除非该会话明确要求。下一产品切片：把 `IMG-01` 写入 CURRENT_TASK 后再写生图提示词 spec。

## Recovery Notes

- 任务：API-01-TPL 已随 `91b7cf3` 提交；未现网
- Spec：`docs/superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md` §10.1
- Kids HEAD：本回合文档提交后更新
- Server Git：`91b7cf31ad47a7faf7b239af2f0aa198cf838e55`
- 试用数据：`/tmp/card-os-api01`（服务已停）
- library 回滚：`knowledge-library.20260901T070549Z.pre-know04`
- 应用回滚目标仍是 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`
