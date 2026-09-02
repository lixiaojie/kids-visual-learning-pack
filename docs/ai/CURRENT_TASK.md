# Current Task

## Metadata

- Updated At: 2026-09-02
- Updated By: Cursor Grok 4.6
- Status: Paused
- Branch: kids `main`；server `knowledge-pipeline-v1` @ `91b7cf3`
- Base Commit: a4047c6

## Objective

API-01-TPL：加厚 `knowledge-compile-v1`，并加强解析层对 ChatGPT 输出形态的兼容。Server 已提交 `91b7cf3`；本回合提交 kids 文档。未现网。

## Background

- 试用 ChatGPT 自造 schema（顶层 propositions + coverage.facets）。本回合归一后，同一份 /tmp 库存未改写 JSON 可不经人工映射脚本编过。
- 未新开 loopback 8765。

## Acceptance Criteria

- [x] `knowledge-compile-v1` 列出 `rabbit-real` 必填键（含 `safety_scope` 英文原文）；模板 digest 已变
- [x] 解析层：围栏外说明、无围栏 JSON、ChatGPT 自造可映射键归一到合同对象
- [x] `rabbit-real` 经 parse 后仍能 compile；散文与缺键仍失败关闭
- [x] 不从散文抽命题；不发明 claim / locator；safety 面只复用已有 claim
- [x] focused unittest 27 PASS；server 已提交 `91b7cf3`；未 release / merge / push
- [x] 未新开 8765；用库存未改写 ChatGPT JSON 验证编过

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md`
- server worktree knowledge_compile parse + knowledge-compile-v1 模板 + 其 unittest（不在 kids 仓根路径）

## Out of Scope

- `IMG-01`；生图；mapping-lock；artifact-generate
- 改四对象 schema / 生产安装 / commit
- `outputs/`、server `uv.lock`

## Constraints

- 不把 `API-01` 标 `DONE`。
- 不覆盖未提交 WB-03 加权行为。

## Verification Plan

- `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile tests.test_http_knowledge_compile -v`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md` §10.1
- `/tmp/card-os-api01/ragdoll-chatgpt.json`
