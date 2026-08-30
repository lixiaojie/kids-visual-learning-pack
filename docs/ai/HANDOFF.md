# Latest Handoff

## Metadata

- Updated At: 2026-08-30
- Agent: Cursor Grok 4.6
- Branch: main
- Base Commit: 5986d8d64bdde940b449ad54ea68cbe19a383c39
- Kids HEAD: `5986d8d64bdde940b449ad54ea68cbe19a383c39` plus this docs commit
- Server Branch: `codex/api-01-generation-input-v1`
- Server Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-01-impl-2`
- Server Base: `878a28d08e951a6985f429e69acbbe74ac5088a0`
- Server Knowledge-Core Worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core`
- Knowledge-Core Branch: `codex/knowledge-core-contract-v1`
- Knowledge-Core HEAD: `1facb79be751e7251fe5b06e6fc8444236069ae1`
- Working Tree: kids 三份任务文档待本 commit；`outputs/` 仍排除；两 server worktree 仅剩未跟踪 `uv.lock`
- Task Status: **Done。用户授权后三个工作区已分别本地提交，未混提交、未 push/merge/deploy。ae563e introducing commit 为 `878a28d08e951a6985f429e69acbbe74ac5088a0`；catalog `registry_commit` 仍为 `9c1b82be69df2da8348f66970a993e9c1984ce6d`。**

## Summary

三个隔离工作区按授权分别提交。knowledge-core `codex/knowledge-core-contract-v1` commit `1facb79be751e7251fe5b06e6fc8444236069ae1`（AUTHOR-02/03/04 真实兔子、几何渐进、时效替代试产）。IMPL-2 `codex/api-01-generation-input-v1` commit `878a28d08e951a6985f429e69acbbe74ac5088a0`（generation-input、pipeline、snapshot compat、catalog 新条目；`47d2` retained、`ae563e` active）。kids `main` 本批只提交三份任务文档，排除 `outputs/`。两侧 `uv.lock` 未纳入。未 `--no-verify`，未访问现网。

## Changed Files

| Repository | File | State |
| --- | --- | --- |
| knowledge-core | commit `1facb79`：authoring.py、authoring tests、README、四份 examples | committed, not pushed |
| IMPL-2 | commit `878a28d`：generation_input/、pipeline/、HTTP/auth、snapshot `ae563e…/`、catalog 新条目、compat tests | committed, not pushed |
| kids | `docs/ai/CURRENT_TASK.md` | 本批授权提交任务标 Done |
| kids | `docs/cognitive-card-os-roadmap.md` | 记录本地 commit 与 introducing hash |
| kids | `docs/ai/HANDOFF.md` | 本交接 |

## Isolation Map

| 角色 | 路径 | 规则 |
| --- | --- | --- |
| kids 治理 | `/Users/admin/projects/family/kids-visual-learning-pack` 的 `main` | 只改任务三文档；不动 `outputs/`；不改 `skills/cognitive-card-os/` |
| generate / loopback | server IMPL-2 worktree @ `878a28d` | 已本地提交；产物仍在 `/tmp`；凭据 `/tmp/card-os-tokens/` |
| AUTHOR | knowledge-core worktree @ `1facb79` | 已本地提交；勿与 IMPL 混 push |

## Verification Results

| Command / Check | Result | Notes |
| --- | --- | --- |
| knowledge-core `tests.test_knowledge_contract_authoring` | PASS | 17 tests, 0.930s, OK；`git diff --check` 退出 0 |
| IMPL-2 focused unittest | PASS | `test_generation_input` / `test_pipeline` / `test_snapshot_compat` / `test_http_compiled` / `test_auth_service` / `test_http_auth` 共 53 tests OK；`git diff --check` 退出 0 |
| knowledge-core commit | PASS | `1facb79`；暂存 7 文件；`uv.lock` 未纳入 |
| IMPL-2 commit | PASS | `878a28d`；68 文件；`uv.lock` 未纳入；catalog `registry_commit` 仍为 `9c1b82b` |
| ae563e introducing commit | PASS | 交接层记录 `878a28d08e951a6985f429e69acbbe74ac5088a0`；未改 catalog 字段 |
| kids `skills/cognitive-card-os/` | PASS | `git status --short` 无该路径 |
| `git diff --check` (kids) | PASS | 文档更新后退出 0 |
| `bash scripts/ai/check-handoff.sh` | PASS | 见本批 kids 验证 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 fail；既有 secret 字段名 WARN 与文档复核到期 WARN，与本批无关 |
| 未 push/merge/deploy | PASS | 三仓均仍本地；未打现网 HTTPS |

## Known Failures

- full suite 2 项 real-uvicorn 502 与 kids-world `19 !== 18` 仍在，与本批无关。
- catalog 新条目 `registry_commit=9c1b82be69df2da8348f66970a993e9c1984ce6d` 指向不含本次 snapshot 文件的 worktree base。catalog 只增不改；真实 introducing commit 现为 `878a28d08e951a6985f429e69acbbe74ac5088a0`，只记在交接层。

## Risks and Caveats

- 本机 loopback 不是现网；`--base-url` 不得指向 `https://www.yutou.space`。
- 两 server 分支仅本地 commit，未 push；合并前需各自 review。
- 两侧未跟踪 `uv.lock` 仍在工作区，不要误加。
- 新 snapshot 的 safety 文本是全局的：用 ae563e 跑恐龙 generate 时 FACT 也必须用 `只看、不抓。`；旧博物馆长句只存在于 retained 47d2。
- 先前 job-bound token 已撤销；0600 文件仍可能在 `/tmp/card-os-tokens/`，不可再用于认证。

## Remaining Work

1. 未授权前不要 push/merge/deploy，不要打现网 HTTPS。
2. 下一产品工作未立项：不要自动开始 KNOW-01 / AGE-01 / ACCEPT-01。

## Exact Next Action

在用户明确授权 push 之前不要推送。若继续产品工作，先更新 `CURRENT_TASK.md` 再实施。推荐下一动作（需用户点名）：

1. 分别 push `codex/knowledge-core-contract-v1` 与 `codex/api-01-generation-input-v1`，不要混成一次 push。
2. 或另开任务：恐龙 generate（ae563e safety 必须用 `只看、不抓。`）、KNOW-01、AGE-01，或 ACCEPT-01 前置评审。
3. kids `outputs/` 仍排除；两侧 `uv.lock` 仍不要提交。

## Recovery Notes

- kids：`/Users/admin/projects/family/kids-visual-learning-pack`；任务三文档。
- IMPL-2：`.worktrees/cognitive-card-server-api-01-impl-2` @ `878a28d`。
- AUTHOR：`.worktrees/cognitive-card-server-knowledge-core` @ `1facb79`。
- generate 产物：`/tmp/card-os-impl4-rabbit-ae563e.aPwNww`；凭据目录 `/tmp/card-os-tokens/`（已撤销）。
- 启动：`docs/ai/START_PROMPTS.md` 第 1 节。
