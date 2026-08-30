# Current Task

## Metadata

- Updated At: 2026-08-30
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`（治理）；server 集成功位 `knowledge-pipeline-v1` @ `b672949` + 未提交 PROJ-01
- Base Commit: kids `b7b08e4`；pipeline `b672949`（LIB-01）；功能分支 `1facb79` / `4ca3e0e`；server main `c2a898c`

## Objective

用户已授权 Projection family 选择面。在 `knowledge-pipeline-v1` 上增加确定性的 family 推荐、备选与不推荐理由，并让 authoring 用该选择面决定 `blueprint.family`。不改 AUTHOR-05 默认表结果，不 merge 进 server `main`，不 push、不现网。

## Background

- Spec §9.3：Planner 根据 Path、密度、受众、时长、场景给出建议；默认只展示推荐方案和关键理由；其他方案作为可选项。
- ADR-002：四卡是一种 family，不是知识模型；系统按结构与学习目标选择或建议 Projection。
- ADR-003：服务器负责 Projection 选择；不是第五个治理对象。
- AUTHOR-05：`single`/`composite` → `chaptered-guide`，`progressive` → `progressive-exploration`；`four-card` 必须显式 opt-in；时效主题才显式 `time-sensitive-brief`。三次试产未证明要改默认表。
- 现网 authoring 只有一张 scope→family 默认表，没有推荐理由，也没有备选列表。

## Acceptance Criteria

- [x] 独立设计已写入 `docs/superpowers/specs/2026-08-30-projection-family-selection-design.md`，并登记到 `docs/README.md`
- [x] 选择面返回唯一 recommended、chosen（default 或 explicit）、options（eligible / discouraged）和稳定 reason codes
- [x] 省略 `projection.family` 时，三类试产编译出的 family 与 AUTHOR-05 默认表相同
- [x] `four-card` 不会被自动选中；显式请求仍可编译
- [x] 未知 family fail closed；不新增 family；不改四对象 schema
- [x] authoring 预览展示 chosen / recommended / options，不增加第五个治理对象或新 package 文件
- [x] 既有 authoring、library、generation-input、接合、contract focused 测试仍通过
- [x] 未 merge 进 server `main`；未 push、未现网；未 add `uv.lock`

## In Scope

- kids：`docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`、独立设计 Spec、`docs/README.md`
- server `knowledge-pipeline-v1`（`.worktrees/cognitive-card-server-knowledge-core`）：
  - `projection_family` 模块（selector + CLI）
  - authoring 使用选择面决定 family，并在 HTML 预览展示
  - focused tests
  - README 中该模块的本地用法

## Out of Scope

- 把 `knowledge-pipeline-v1` 或功能分支 merge 进 server `main`
- push、deploy、现网
- HTTP route、SQLite、Portal、Renderer、four-card converter
- 新 Projection family、改四对象 schema、改 validator 的 family 枚举集合
- 改 AUTHOR-05 默认表，使兔子/几何在省略 family 时换 family
- 第三个用户确认点；把选择面做成交互 UI
- 撤 generation-input / thin-skill worktree；add `uv.lock`

## Constraints

- 活 checkout：继续占用 knowledge-core 工位上的 `knowledge-pipeline-v1`；不新建第 4 个 server worktree。
- current pointer 与四对象 identity 本批不改。
- 选择记录不是治理对象；不得写入 `knowledge-core` / `learning-spec` / `projection-spec` / `manifest` 新字段。
- 不覆盖未提交修改；两侧未跟踪的 `uv.lock` 不纳入提交。
- 不自动 push；不 merge 进 server `main`。

## Verification Plan

- 在 `knowledge-pipeline-v1` worktree：
  - `PYTHONPATH=src python3 -m unittest tests.test_projection_family`
  - `PYTHONPATH=src python3 -m unittest tests.test_knowledge_library tests.test_generation_input tests.test_generation_input_knowledge_revision tests.test_knowledge_contract_authoring tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures tests.test_knowledge_contract_model`
- `git merge-base --is-ancestor HEAD c2a898c` 为非 0；server `main` 仍为 `c2a898c`
- kids：`git diff --check`、`bash scripts/ai/check-handoff.sh`、`bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md` §3.6、§9.3、§11.1、§16
- `docs/superpowers/specs/2026-08-30-knowledge-library-revision-current-design.md`
- `docs/superpowers/specs/2026-08-30-projection-family-selection-design.md`
- `docs/cognitive-card-os-roadmap.md` AUTHOR-05、§5 第 3 项
