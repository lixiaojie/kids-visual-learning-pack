# Current Task

## Metadata

- Updated At: 2026-09-03
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main` @ `ea7658d`；server `knowledge-pipeline-v1` @ `54092cb`
- Base Commit: ebf3034

## Objective

COMPOSE-01：把 IMG-01 无字主图与 WB-03 锁定四卡文案合成屏幕 HTML + 观察卡带图打印。本机隔离 library。不生产、不标 IMG-01 DONE。

## Background

- Spec：`docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`
- ChatGPT 不烧字。缺图或缺四卡失败关闭。主图只进中英文观察卡页顶图像带。

## Acceptance Criteria

- [x] 设计写入 spec（操作者已批准计划并授权实施）
- [x] spec 收录文档地图与路线图 `COMPOSE-01`
- [x] 实施计划落盘
- [x] server TDD：门禁、HTML、OBS 图像带、兔子夹具不溢出
- [x] focused 回归含 IMG-01 / WB-03（109 tests OK）
- [x] 本机隔离 candidate 根验证；不写生产 library

## In Scope

- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`
- `docs/superpowers/plans/2026-09-03-operator-composite-projection-display-implementation-plan.md`
- server worktree `src/cognitive_card_server/knowledge_compose/**`
- server worktree `src/cognitive_card_server/four_card_render/{weighted_layout.py,render.py}`
- server worktree `src/cognitive_card_server/knowledge_ops/{http.py,pages.py}`
- server worktree `src/cognitive_card_server/http/{app.py,errors.py}`
- server worktree compose / render / HTTP / ops 测试

## Out of Scope

- OpenAI / ChatGPT 图像 API、Cookie、claim 执行器、可交互烧字页
- 改四对象 schema；改 KNOW-04 current；知识卡插图
- 把装箱/装图写成知识源准入
- merge `main`、push、release、现网、Nginx reload
- `outputs/`、server `uv.lock`
- 标 IMG-01 `DONE`

## Constraints

- 权威仓库：产品规范在 kids；实现在 server `knowledge-pipeline-v1`。
- 按 TDD：每批生产代码前先看对应测试因缺功能正确失败。
- 不覆盖未提交 `outputs/`。
- WB-03 `generate_from_mapping` 无图路径保持可用。

## Verification Plan

- server: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_knowledge_library_mapping tests.test_weighted_layout tests.test_http_auth tests.test_knowledge_illustration tests.test_http_knowledge_illustration tests.test_knowledge_compose tests.test_http_knowledge_compose tests.test_artifact_pipeline`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md`
- `docs/superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md`
- `docs/superpowers/specs/2026-09-01-operator-mapping-artifact-publish-design.md`
- `docs/cognitive-card-os-roadmap.md` § COMPOSE-01
