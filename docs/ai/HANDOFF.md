# Latest Handoff

## Metadata

- Updated At: 2026-08-31
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 83888dd
- Kids HEAD: 本提交记录 PUBLISH-01
- Server Branch: `knowledge-pipeline-v1` @ `7a127b4`
- Server Worktree: `.worktrees/cognitive-card-server-knowledge-core` 现为 `knowledge-pipeline-v1`
- Server Generation-Input Worktree: `.worktrees/cognitive-card-server-api-01-impl-2` @ `4ca3e0e`
- Server main checkout: Documents Codex `cognitive-card-server` @ `c2a898c`
- Working Tree: kids 本提交后仅 `outputs/` 未跟踪；server 仅 `uv.lock` 未跟踪
- Task Status: **Done（PUBLISH-01 已本地提交 server `7a127b4`）。** 未 merge server `main`；未 push；未现网。

## Summary

PUBLISH-01 把 QA-01 `approved` 的锁定四卡写成服务器权威不可变 package：`revision-NNNN` 只写一次，current 只是 pointer。撤回清空 pointer、历史目录保留；替代写入新 revision 并记录 `supersedes`。相同内容对 current 幂等；撤回后再发同一包只恢复 pointer。抢救了 package-v5 的不可变/历史合同，没有合入 `e78c2fa` 或客户端打包器。不扩 PORTAL，不新增 HTTP。本机 revision 目录即本批次下载句柄。server 已本地提交 `7a127b4`；未 add `uv.lock`。

## Completed

- 设计：`docs/superpowers/specs/2026-08-31-immutable-package-publish-design.md`
- 实现：`four_card_publish`（catalog / CLI）；只消费 approved QA
- 测试：发布进 current、拒绝未批准、空 actor、幂等、替代保留旧字节、占用目录不覆盖、篡改 fail closed、撤回/恢复 pointer、CLI
- server 本地提交：PUBLISH-01 `7a127b4`（QA-01 `37a5927`；RENDER-01 `1ef6edc`；AGE-01 `4e0ea52`；RUN-01 `c55f51b`）
- 未改四对象 schema、未 merge、未现网

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| kids | `docs/ai/CURRENT_TASK.md` | 本提交：PUBLISH-01 Done |
| kids | `docs/ai/HANDOFF.md` | 本提交：记录 server `7a127b4` |
| kids | `docs/cognitive-card-os-roadmap.md` | 本提交：PUBLISH-01 / `7a127b4` |
| kids | `docs/cognitive-card-os-system-design.md` | 本提交：交付阶段第 9 条 |
| kids | `docs/README.md` | 本提交：PUBLISH-01 设计条目 |
| kids | `docs/superpowers/specs/2026-08-31-immutable-package-publish-design.md` | 本提交 |
| kids | `outputs/` | 未跟踪；不纳入 |
| server | `src/cognitive_card_server/four_card_publish/` | 已提交 `7a127b4` |
| server | `tests/test_four_card_publish.py` | 已提交 `7a127b4` |
| server | `uv.lock` | 未跟踪；不要 add |

## Decisions Made

- Package 是独立 CLI Artifact 层，不接线 subscriber `JobState` / HTTP / SQLite。
- 只消费 `status=approved` 且 `review.decision=approve`；人类 actor 不得为 `publish-01-v1` / `qa-01-v1` / `machine`。
- 内容身份不含 revision 号：相同锁/渲染/QA 对 current 幂等；撤回后再发只恢复 pointer。
- 占用已有 `revision-NNNN` 目录时改写下一序号，不 `os.replace` 进已存在路径。
- 授权下载本批次等于本机目录路径；PORTAL-01 再挂 URL。
- 不 merge、不 push、不现网。本批仅本地提交。

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `kids-visual-learning-pack` `main` | 任务账本与 PUBLISH-01 设计本提交 |
| 知识管线集成 | `.worktrees/cognitive-card-server-knowledge-core` @ `7a127b4` | 不 merge `main` |
| 现网对应 | Documents Codex `cognitive-card-server` `main` @ `c2a898c` | 0.3.1；不在本批改 |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| `.venv/bin/python -m unittest tests.test_four_card_publish` | PASS | 12 项 |
| `.venv/bin/python -m unittest tests.test_four_card_publish tests.test_four_card_qa tests.test_four_card_render tests.test_age_language_adapter tests.test_four_card_converter tests.test_knowledge_library tests.test_knowledge_browse tests.test_http_knowledge_library tests.test_joined_executor tests.test_knowledge_contract_authoring` | PASS | 109 项 |
| `.venv/bin/python -m unittest discover -s tests` | WARN | 596 项中 594 PASS；2 项 real-uvicorn 502 既有 |
| `git diff --check` | PASS | kids 文档 + server publish |
| `bash scripts/ai/check-handoff.sh` | WARN | Base Commit 对齐 `83888dd` 后应消除落后 HEAD |
| `bash scripts/ai/check-task-state.sh` | PASS | Status Done，验收全勾 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 FAIL；既有 secret 字段名 WARN + 文档复核到期 |
| 未 merge server `main` / 未 push / 未现网 | PASS | server 尖端 `7a127b4`；仅 `uv.lock` 未跟踪 |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog `registry_commit=9c1b82b` 诚实性缺口仍只记在交接层。
- kids `.worktrees/card-os-thin-skill-v1` 未撤：未提交文档仍在。
- 文档地图 Last Reviewed `2026-07-24` / Next Review Due `2026-08-24` 已过期，属既有治理 WARN。

## Risks and Caveats

- 公网画廊、下载 URL、容量门禁仍属 PORTAL / 运维，本批次只有本机目录。
- 未授权不要 merge `knowledge-pipeline-v1`、不要 push/deploy。
- `uv.lock` 与 `outputs/` 不要混入提交。

## Remaining Work

1. 下一实现会话：ACCEPT-01。
2. 其后按路线图 §5 编号 7–10。
3. thin-skill 脏文档与 generation-input 功能分支 worktree 仍待用户选择。

## Exact Next Action

新开会话，把 `ACCEPT-01` 写入 `CURRENT_TASK.md`：兔子端到端（输入到四卡、PDF、QA、复核和不可变 package）。不扩 PORTAL，不 merge、不现网。活 server 尖端为 `knowledge-pipeline-v1` @ `7a127b4`。

## Recovery Notes

- kids：`kids-visual-learning-pack` `main` 本提交记录 PUBLISH-01；基线 `83888dd`。
- 活 server：`knowledge-pipeline-v1` @ `7a127b4`（PUBLISH-01）；QA-01 `37a5927`；RENDER-01 `1ef6edc`；AGE-01 `4e0ea52`；RUN-01 `c55f51b`；main `c2a898c`。
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
- 规范：ADR-001/002/004、系统总设计 §4.4 / §10、PUBLISH-01 设计、QA-01 批准报告。
