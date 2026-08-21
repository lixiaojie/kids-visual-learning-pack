# Latest Handoff

## Metadata

- Updated At: 2026-08-21
- Agent: OpenAI Codex
- Branch: main
- Base Commit: 0257a86
- Server Worktree Branch: `codex/knowledge-core-contract-v1`
- Server Worktree Base Commit: `9c1b82be69df2da8348f66970a993e9c1984ce6d`
- Server Worktree HEAD: `120e5fcc48e4e6cabb1a28678379f687553c0788`
- Working Tree: kids 保留本轮批准的 canonical docs、ADR、Spec、Plan、evidence 与 AUTHOR-01 closure，以及用户既有未跟踪 `outputs/`；server 状态与 commit identity 见下方验证表，`.venv` 被忽略。
- Task Status: **AUTHOR-01 local authoring vertical slice is DONE, verified, and committed on the isolated server branch. The next product step is one real-topic authoring trial, not more framework work. No push, merge, deploy, current switch, service start, or second-computer verification is authorized.**

## Summary

`AUTHOR-01` 已在现有 `KNOW-02` 四对象合同上形成第一条可用闭环。server 分支 `codex/knowledge-core-contract-v1` 已从 base `9c1b82b` 前移到实现 commit `120e5fc`；标准库 CLI `knowledge_contract.authoring` 把已经提供来源、证据和命题的结构化 request 确定性编译为 `knowledge-core.json`、`learning-spec.json`、`projection-spec.json`、`manifest.json`、`validation.json` 和 `artifacts/index.html`，通过 Publish validation 后才原子写入 `<topic>/revision-NNNN/`。

CLI 对 `single/composite` 默认选 `chaptered-guide`，对 `progressive` 默认选 `progressive-exploration`，只有显式 request 才选 `four-card`。浏览页完整 HTML escape 输入，并明确标注仅为结构化 authoring preview、不是最终儿童 Renderer。重复 revision、缺失证据和合同校验失败均返回稳定 JSON 错误；测试证明不会覆盖历史 revision 或留下 topic 半成品。

实现遵守本轮最小边界：不联网、不调用 LLM、不发明事实，不接 HTTP、DB、subscriber、auth、Portal、正式 Renderer 或部署。没有修改既有 API-01 worktree，也没有读取、修改、删除或纳入用户既有 `outputs/`。

本批先记录真实文件系统 RED：5 项测试均因 authoring module 尚不存在而失败；随后最小实现转为 5/5 GREEN。新 synthetic rabbit request 与 README 命令使用同一真实 CLI。当前成功包只物化零 issue 的 Publish 结果；任何 validation issue 会作为 `AUTHORING_CONTRACT_INVALID` 交还上层，不在 CLI 内追问或自动降级。

## Changed Files

| Repository | File set | State |
| --- | --- | --- |
| kids | `docs/knowledge-core-contract-pilot-evidence.md` | 新建；记录真实 identity、fixture、boundary、复杂度边界与验证结果 |
| kids | `docs/cognitive-card-os-roadmap.md`, `docs/README.md`, `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md` | 更新；`KNOW-02` DONE、证据地图、复审终态与本交接 |
| server | `README.md`, `examples/authoring/rabbit-composite.json`, `src/cognitive_card_server/knowledge_contract/{__init__.py,authoring.py,model.py,validator.py}`, `tests/{test_knowledge_contract_authoring.py,test_knowledge_contract_fixtures.py,test_knowledge_contract_model.py,test_knowledge_contract_validation.py}` | 已提交为 `120e5fc`；未 push/merge |

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| server identity/status and changed-file union | PASS | branch `codex/knowledge-core-contract-v1`; `HEAD` `120e5fc`; worktree clean；commit 相对 `9c1b82b` 为上表 10 个路径 |
| `PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_authoring -v` | PASS | 2026-08-21 fresh run: `Ran 5 tests`, `OK` |
| contract + authoring focused suite | PASS | 2026-08-21 fresh run: `Ran 133 tests`, `OK` |
| `UV_CACHE_DIR=/tmp/cognitive-card-uv-cache uv run --extra test python -m unittest discover -s tests -v` | PASS | 2026-08-21 fresh run with declared test dependencies: `Ran 444 tests`, `OK` |
| `python3 -m py_compile ...authoring.py ...test_knowledge_contract_authoring.py` | PASS | 新模块与测试语法编译通过 |
| documented rabbit example CLI smoke | PASS | 临时目录生成预期 6 个文件；validation 为 Publish valid，浏览页包含非最终 Renderer 声明 |
| server `git diff --check` | PASS | 无空白错误 |
| `bash scripts/ai/check-doc-governance.sh` | PASS | 文档地图、链接和 review 日期均通过 |
| `bash scripts/ai/check-agent-state.sh` | WARN | 0 failure；仅既有 secret-related field-name scan warning，未压制、未发现高置信 secret value |
| kids `git diff --check` | PASS | 无空白错误 |

## Known Failures

- 先前系统 Python 无 test dependencies 时出现的 5 个 HTTP import errors 已通过项目声明依赖环境重跑澄清；完整 suite 当前没有已知失败。
- `node boards/kids-world/structure.test.mjs` 的既有 `19 !== 18` 断言失败未在本纯合同/文档批次重跑。

## Risks and Caveats

- 当前 request 只支持一个 source，且所有新命题按 `timeless/fresh` 编译；多来源、定期更新和事件触发字段应由真实主题试产暴露需求后再加，不能把当前 synthetic 示例当成完整知识生产能力。
- 当前只有每个 revision 内的结构化 `artifacts/index.html`，还没有跨主题 library 首页或正式儿童 Renderer。
- CLI 成功路径零交互；本批没有测量真实主题的人工治理时间，也没有实现 warning 后二次确认 UI。合同 issue 会 fail closed 并交还上层。
- server commit `120e5fc` 尚未 push/merge；任何 push、merge、deployment 或 runtime wiring 都需要新的明确授权。

## Remaining Work

1. 选择一个真实且范围可控的主题，基于可信来源填写 authoring request，生成首个非 synthetic revision。
2. 直接检查本地浏览页与 JSON 产物，记录“内容填写、学习路径、Projection 默认、更新属性”四类实际摩擦，再只修阻断闭环的缺陷。

## Exact Next Action

In the server worktree, copy `examples/authoring/rabbit-composite.json` to a temporary request for one real topic, replace all synthetic source/evidence/propositions with verified material, run the documented CLI into a new temporary library root, and inspect the generated `artifacts/index.html`; do not add another framework layer first.

## Recovery Notes

- kids：在仓库根目录运行 `git status --short`、`bash scripts/ai/check-agent-state.sh`、`git diff --check`；保留用户 `outputs/` 不动。
- server：进入 `.worktrees/cognitive-card-server-knowledge-core`，先运行 `git branch --show-current`、`git rev-parse HEAD`、`git status --short`、`git diff --name-only` 与 `git ls-files --others --exclude-standard`；不要修改 `.worktrees/cognitive-card-server-api-01`。
- 真实合同细节及 full-suite 基线限制见 [Pilot Evidence](../knowledge-core-contract-pilot-evidence.md)。
