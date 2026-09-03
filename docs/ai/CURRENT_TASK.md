# Current Task

## Metadata

- Updated At: 2026-09-03
- Updated By: Cursor Grok 4.6
- Status: Paused
- Branch: kids `main` @ `efc75aa`；server `knowledge-pipeline-v1` @ `54092cb`
- Base Commit: ebf3034

## Objective

IMG-01 本机 loopback（含 ChatGPT 真图）已验收；kids `efc75aa`、server `54092cb` 已本地提交。不生产、不标 DONE。

## Background

- Spec：`docs/superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md`
- 知识源锁定内容；生图策略由投影意图决定。首刀：一张无字主图 + 操作台一页（主图 + active 命题）。不经 mapping-lock / Pillow / 图像 API。

## Acceptance Criteria

- [x] 设计经操作者批准后写入 spec
- [x] spec 锁定：入口、模板、回传合同、与 WB-03 文字渲染边界
- [x] 明确非范围：不把「图装得下」写成知识源准入；不改 KNOW-04 六主题 current；不写实施代码；不生产安装
- [x] `docs/README.md` 地图收录该 spec
- [x] 路线图 `IMG-01` 下一动作改为待复核 spec / 待计划；状态不标 DONE
- [x] 操作者批准实施
- [x] 实施计划落盘并通过自检
- [x] server 以 TDD 完成 intent、PNG、HTTP 与操作台页面
- [x] focused baseline + IMG-01 测试通过（82 PASS）
- [x] 独立全量变更复审 READY
- [x] 本机隔离 library：操作台扩提示词、上传 PNG、演示页可见主图 + active 命题
- [x] ChatGPT 真实外形：操作者 2026-09-03 确认复制提示词 → 生图 → 上传 → 演示页无误

## In Scope

- 本机隔离 library 与 loopback HTTP（显式 `--database` / `--candidate-root`，不写生产 library）
- `docs/ai/CURRENT_TASK.md`
- `docs/ai/HANDOFF.md`
- `docs/cognitive-card-os-roadmap.md`
- `docs/README.md`
- `docs/superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md`
- `docs/superpowers/plans/2026-09-02-operator-illustration-hero-page-implementation-plan.md`
- server worktree `src/cognitive_card_server/knowledge_illustration/**`
- server worktree `src/cognitive_card_server/knowledge_ops/{http.py,pages.py}`
- server worktree `src/cognitive_card_server/http/{app.py,errors.py}`
- server worktree dependency manifest（pyproject）
- server worktree protected-route auth regression test
- server worktree illustration domain tests
- server worktree illustration HTTP tests

## Out of Scope

- OpenAI / ChatGPT 图像 API、Cookie、claim 执行器
- 改四对象 schema；改 KNOW-04 current
- 把装箱/装图写成知识源准入
- merge `main`、push、release、现网、Nginx reload、KNOW-04 生产 library
- 把 `/tmp/card-os-api01` 当生产；把本机 loopback 绑到非 127.0.0.1
- `outputs/`、server `uv.lock`

## Constraints

- 权威仓库：产品规范在 kids；实现（以后）在 server。
- 按 TDD：每批生产代码前先看对应测试因缺功能正确失败。
- 复用既有 server 隔离 worktree；不纳入其未跟踪 `uv.lock`。
- 不覆盖未提交 `outputs/`。

## Verification Plan

- server: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_knowledge_library_mapping tests.test_weighted_layout tests.test_http_auth tests.test_knowledge_illustration tests.test_http_knowledge_illustration`
- `bash scripts/ai/check-task-state.sh`
- `bash scripts/ai/check-handoff.sh`
- `bash scripts/ai/check-doc-governance.sh`
- `git diff --check`

## Relevant References

- `docs/superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md`
- `docs/superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md`
- `docs/cognitive-card-os-roadmap.md` § IMG-01
