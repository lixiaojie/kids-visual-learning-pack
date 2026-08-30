# Current Task

## Metadata

- Updated At: 2026-08-30
- Updated By: Cursor Grok 4.6
- Status: Done
- Branch: kids `main`（治理）；server 实现工位 `codex/api-01-generation-input-v1` @ `4ca3e0e`（接合代码已本地提交）
- Base Commit: kids `c6973ef`；knowledge-core `1facb79`；IMPL-2 `4ca3e0e`；server main `c2a898c`

## Objective

落地 ADR-003 接合合同：generation-input lock 必须摘要四对象精确 revision，禁止把平行 FACT 当作知识源。本批在四卡执行工位增加接合 assemble/validate 与测试；不 merge 两条 server 功能分支，不创建 `knowledge-pipeline-v1`，不 push、不现网。

## Background

- 用户 2026-08-30 确认知识管线为工作区轴线；治理与分支收敛已提交（kids `c6973ef`）。
- 路线图近期顺序第 2 项与 HANDOFF Exact Next Action：先更新本文件再实施接合。
- 两套模型仍隔离：knowledge-core 的 `generation_input_lock_sha256` 目前摘要 authoring request；generation-input-v1 的 lock 摘要 FACT 密封包。接合必须证明执行锁绑定四对象 revision identity（与 `final_content_lock` 同算法）。
- 既有 generation-input-v1 密封包与 IMPL-3/4 存储面保持可校验；本批新增接合路径，不改 v1 `assemble_generation_input` 的 FACT 密封合同。

## Acceptance Criteria

- [x] 接合 assemble 在缺少四对象文档时 fail closed
- [x] 接合 lock 包含 `final_content_lock_sha256` 与三份对象文档 sha256；算法与 knowledge-core `final_content_lock` 一致（可用 AUTHOR 产出的 manifest 对照）
- [x] 同一 FACT、不同四对象 revision → 接合 lock 不同
- [x] FACT 出现 knowledge-core 中不存在的 `proposition_id` 时 fail closed
- [x] 既有 generation-input v1 测试仍通过（FACT 密封合同未破）
- [x] 未 merge `codex/knowledge-core-contract-v1` 与 `codex/api-01-generation-input-v1`；未创建 `knowledge-pipeline-v1`；未 push/deploy/现网
- [x] kids `docs/ai/HANDOFF.md` 与 `docs/cognitive-card-os-roadmap.md` 用真实命令结果更新

## In Scope

- kids：`docs/ai/CURRENT_TASK.md`、`docs/ai/HANDOFF.md`、`docs/cognitive-card-os-roadmap.md`
- server 四卡执行 worktree（`.worktrees/cognitive-card-server-api-01-impl-2`）：
  - 新增 `knowledge_revision` 接合模块与对照 fixture；不改 knowledge-core 代码

## Out of Scope

- 新建或 merge `knowledge-pipeline-v1`；把两条功能分支合成一次提交
- 修改 generation-input-v1 `assemble_generation_input` / `_SEALED_KEYS` 使旧密封包失效
- 把 knowledge-core 的 `generation_input_lock_sha256=sha256_ref(request)` 改为接合 lock（须等集成分支）
- HTTP/DB/sealed-input store 接线、现网、push
- KNOW-01、AGE-01、current pointer、Portal、Renderer、完整 four-card production-record converter
- `--force` 删除 thin-skill worktree；处理其未提交文档

## Constraints

- 活 checkout 上限：本批代码只写 generation-input 工位；knowledge-core worktree 只读。
- 四对象 identity 的 canonical JSON 必须与 knowledge-core `canonical_json`（`ensure_ascii=False`）一致，不得误用 snapshot `canonical_json`。
- catalog `registry_commit` 仍不改。
- 不覆盖未提交修改；server 两侧未跟踪的 `uv.lock` 不纳入本批。

## Verification Plan

- 在 generation-input worktree：`PYTHONPATH=src python3 -m unittest tests.test_generation_input tests.test_generation_input_knowledge_revision`
- `git -C <server-main> merge-base --is-ancestor 1facb79 4ca3e0e` 应为非 0（两条功能分支仍未互相包含）
- kids：`git diff --check`、`bash scripts/ai/check-handoff.sh`、`bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md`
- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md` §13.3、§18
- `docs/cognitive-card-os-roadmap.md` §5 第 2 项
