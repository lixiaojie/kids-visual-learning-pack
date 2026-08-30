# Current Task

## Metadata

- Updated At: 2026-08-30
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`（治理）；server 集成功位 `knowledge-pipeline-v1` @ `9e0c353`
- Base Commit: kids 本批治理基线；pipeline `9e0c353`（PROJ-01 + WIRE-01）；功能分支 `1facb79` / `4ca3e0e`；server main `c2a898c`

## Objective

用户已授权 HTTP/DB 受控接线。在 `knowledge-pipeline-v1` 把知识库与 Projection 选择面接到现有 loopback HTTP 与 SQLite 任务面：HTTP 适配器只调用已有 library / selector；接合 generation-input 必须对应 library current；v1 FACT 密封路径保持兼容。不 merge 进 server `main`，不 push、不现网。

## Background

- LIB-01 与 PROJ-01 已是进程内 / CLI 能力；KNOW-02 明确当时零 HTTP/DB wiring。
- 现网 `0.3.1` 与 server `main` `c2a898c` 只有锁定任务 / generation-input / compiled-jobs。
- generation-input HTTP 原先只校验 v1 FACT 密封；接合 schema 无法入库，compiled-jobs 也不核对四对象 current。
- API-01：HTTP 适配器不复制状态机；只调用现有应用服务。
- ADR-002：不新增第五个治理对象；revision 仍是文件目录，current 仍是 pointer。

## Acceptance Criteria

- [x] 独立设计已写入 `docs/superpowers/specs/2026-08-30-knowledge-library-http-db-wiring-design.md`，并登记到 `docs/README.md`
- [x] HTTP 可 accept-candidate、publish、读取 current、unlist、refresh；适配器不复制 library 写入规则
- [x] HTTP 可返回 Projection family 选择面；不持久化选择记录
- [x] 接合 generation-input 仅当 library current identity 匹配时才能存储并创建 SQLite compiled-job
- [x] v1 FACT 密封的 generation-input / compiled-jobs 行为不变
- [x] `four-card` 仍须 opt-in；不改 AUTHOR-05 默认表；不改四对象 schema
- [x] 既有 authoring、library、projection-family、generation-input、接合、contract、HTTP compiled focused 测试仍通过
- [x] 未 merge 进 server `main`；未 push、未现网；未 add `uv.lock`

## In Scope

- kids：`docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`、独立设计 Spec、`docs/README.md`
- server `knowledge-pipeline-v1`（`.worktrees/cognitive-card-server-knowledge-core`）：
  - knowledge library HTTP 适配（含 bundle 从 JSON 重建）
  - 接合 generation-input / compiled-jobs 对 library current 的门禁
  - Projection family HTTP 查询
  - KnowledgeContractError 稳定 HTTP 映射
  - focused tests 与 README 本地用法

## Out of Scope

- 把 `knowledge-pipeline-v1` 或功能分支 merge 进 server `main`
- push、deploy、现网、改生产 env 必填项
- 新 SQLite 表或把四对象 JSON 写入数据库
- Portal、Renderer、four-card converter、新 Projection family
- 改 AUTHOR-05 默认表；改 v1 FACT 密封合同
- 撤 generation-input / thin-skill worktree；add `uv.lock`

## Constraints

- 活 checkout：继续占用 knowledge-core 工位上的 `knowledge-pipeline-v1`；不新建第 4 个 server worktree。
- 不覆盖用户未提交修改；两侧未跟踪的 `uv.lock` 不纳入提交。
- HTTP 鉴权先于 body；写路径进 `PROTECTED_ROUTES`。
- library 仍为文件目录加 current pointer；SQLite 只继续存 jobs/packets/tokens。
- 不自动 push；不 merge 进 server `main`。

## Verification Plan

- 在 `knowledge-pipeline-v1` worktree：
  - `PYTHONPATH=src python3 -m unittest tests.test_http_knowledge_library tests.test_http_compiled tests.test_projection_family tests.test_knowledge_library tests.test_generation_input tests.test_generation_input_knowledge_revision tests.test_knowledge_contract_authoring tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures tests.test_knowledge_contract_model`
  - 额外 HTTP 回归：`tests.test_http_auth tests.test_http_admin tests.test_http_public tests.test_http_subscriber`
- `git merge-base --is-ancestor HEAD c2a898c` 为非 0；server `main` 仍为 `c2a898c`
- kids：`git diff --check`、`bash scripts/ai/check-handoff.sh`、`bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md` §13.2、§18.5
- `docs/superpowers/specs/2026-08-30-knowledge-library-revision-current-design.md`
- `docs/superpowers/specs/2026-08-30-projection-family-selection-design.md`
- `docs/superpowers/specs/2026-08-30-knowledge-library-http-db-wiring-design.md`
- `docs/cognitive-card-os-roadmap.md` API-01、LIB-01、PROJ-01、WIRE-01、§5 第 3 项
