# Latest Handoff

## Metadata

- Updated At: 2026-07-31
- Agent: Kimi Code
- Branch: codex/card-os-thin-client-v1（worktree `.worktrees/card-os-thin-client-v1`）
- Base Commit: f2a2462（SKILL-02 任务建立提交；main 另有 docs-only 的 995c8b6 抢救优先更新）
- Working Tree: 仅 Task 1 产物（见 Changed Files）；主工作区 `outputs/` 为用户资产未触碰
- Task Status: SKILL-02 实施中，计划 Task 1（传输层与 capability 协商）已完成 RED→GREEN→review，待提交

## Summary

按计划 Task 1 由全新 implementer 子代理执行：`tests/test_card_os_client_transport.py`（34 个测试）先对 13 行骨架验证 RED（34/34 error，骨架无所需接口），随后在 `skills/cognitive-card-os/scripts/card_os_client.py` 实现最小传输/doctor 切片转 GREEN（35/35 PASS，含评审后新增 1 个 connection-refused 测试）。实现要点：`NoRedirectHandler` 禁重定向（任何 3xx 映射 `REDIRECT_REFUSED`，fixture 断言只见一个请求）；固定生产 base URL `https://www.yutou.space/card-os/`，CLI 无 base-url 覆盖口，plain HTTP 仅测试注入的 loopback config 且请求时复核 host；响应有界读取（4 MiB）；`canonical_json` 字节级精确；SemVer 数值比较；doctor 无认证读取 health/capabilities，协议不相交/服务器 <0.3.1/最低 Skill >0.1.0/畸形协议/错误 schema 分别映射 `CLIENT_UPGRADE_REQUIRED`/`SERVER_UPGRADE_REQUIRED`/`SERVER_CONTRACT_DRIFT`；57 个冻结服务器错误码集合与计划逐一相等；token 在所有失败路径不泄露。未实现 Task 2+ 任何表面。

独立 reviewer 子代理结论：Critical 0 / Important 0 / Minor 3（303/308 重定向覆盖、unknown command 断言过弱、URLError 分支未覆盖），三条 Minor 均为测试强化，已在提交前修正并复跑 35/35 PASS。网络/体积/非 JSON 错误体映射 `HTTP_ERROR`（而非 `SERVER_CONTRACT_DRIFT`）经评审确认正确：DRIFT 保留给可证明的应用层契约违反。

能力 schema（`schema`/`server_version`/`protocol`/`packet_schemas`/`result_schemas`/`minimum_skill_release`/`features`）取自 2026-07-13 auth-protocol 计划，并经 implementer 对生产 `https://www.yutou.space/card-os/api/v1/` 的只读无认证 doctor 实测逐字段一致（本阶段唯一现网接触，GET 探针，无凭据）。

## Completed

- 启动协议核实：仓库根、分支、worktree 状态、必读文档、计划/spec/ADR-001/roadmap。
- Task 1 RED：`python3 -m unittest tests.test_card_os_client_transport -v` 对骨架 34/34 error（`AttributeError: module 'card_os_client' has no attribute '_config'` 等）。
- Task 1 最小 GREEN：35/35 PASS。
- Task 1 独立评审：0 Critical / 0 Important / 3 Minor，Minor 已修正。
- 回归：`tests.test_card_os_skill_release test_card_os_skill_installer test_card_os_skill_publisher` 72/72 PASS（五文件 Skill 闭包未被破坏）。

## Changed Files

| File | Change | Reason |
| --- | --- | --- |
| `tests/test_card_os_client_transport.py` | 新建（~620 行，35 测试） | Task 1 RED→GREEN 契约测试 |
| `skills/cognitive-card-os/scripts/card_os_client.py` | 替换（13 行骨架 → ~467 行） | Task 1 传输层 + capability 协商 + doctor |
| `docs/ai/HANDOFF.md` | 修改 | 本阶段交接（随业务代码同提交，pre-commit 钩子要求） |

## Decisions Made

- 测试注入缝：模块级 `_config: TransportConfig`（frozen dataclass），测试直接赋值；不用 CLI flag（生产 CLI 不得暴露 base-url），安全性不依赖 flag——请求时复核 plain HTTP 仅限 loopback host。
- 超时/连接拒绝/超限/非 JSON 错误体 → `HTTP_ERROR`（冻结 0.3.1 集合内）；`SERVER_CONTRACT_DRIFT` 仅用于可证明的应用层契约违反（无 envelope、未知/畸形 code、非 JSON 成功体、畸形 capabilities）。
- 未知 CLI 命令：stderr 单行 usage + exit 2（无冻结码覆盖 CLI 误用）；doctor 失败一律输出规范 `{"error":{...}}` JSON + exit 1。
- 响应大小上限定为 4 MiB（读取 limit+1 字节判定）。

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| `python3 -m unittest tests.test_card_os_client_transport -v`（对骨架） | RED（预期） | 34/34 error，接口全部缺失 |
| `python3 -m unittest tests.test_card_os_client_transport` | PASS | 35/35，含评审 Minor 修正后复跑 |
| `python3 -m unittest tests.test_card_os_skill_release tests.test_card_os_skill_installer tests.test_card_os_skill_publisher` | PASS | 72/72，SKILL-01 冻结契约未破坏 |
| `python3 skills/cognitive-card-os/scripts/card_os_client.py doctor`（生产只读探针） | PASS | exit 0，capabilities 与冻结 schema 逐字段一致 |
| 关闭端口注入 config 的 doctor | PASS | exit 1，`HTTP_ERROR`，无 traceback |
| `git diff --check` | PASS | 提交前 |

## Known Failures

- `node boards/kids-world/structure.test.mjs` 既有 `19 !== 18`，与本任务无关，本阶段未重跑。
- 存档分支 `codex/card-os-thin-skill-v1` 自身套件 19 errors + 1 failure，属封存资产，不影响本分支。

## Risks and Caveats

- 生产 packets/results 链路仍零真实流量；Task 8 现网验收为首跑。
- capabilities schema 目前以 07-13 计划 + 一次现网只读探针为证；若服务器后续演进，Task 3 复制 packet envelope fixture 时需以服务器应用提交 `c2a898c` 重新核对。
- `urllib.request` 线上 header 名大小写为 `X-Card-Os-*`（RFC 9110 等价），已由现网 doctor 通过佐证。
- main 领先本分支 1 个 docs-only 提交（`995c8b6` 抢救优先 roadmap 更新），不影响业务路径；Task 6 集成时按 `finishing-a-development-branch` 处理。

## Remaining Work

1. Task 2：凭据后端（Keychain/secret-tool/显式 0600 文件）RED→GREEN。
2. Task 3–4：packets/jobs 命令、结果校验与自动上传。
3. Task 5：Skill 文档改写 + pre-publish probes；Task 6：构建 0.1.0 与 provisional stable 激活（集成/push 需用户授权）；Task 7–9：双隔离安装、现网验收、文档收尾。
4. 抢救批次（SKILL-02 之后、ACCEPT-01 之前，优先于从零重建）：迁移存档 `core/` 至服务器侧可信上游；修复 package-v5 两个评审 Block、publisher fixture 与 mode pin；处置误提交的 `.superpowers` 文件、3 个未跟踪计划与 library-design 未提交修订。

## Exact Next Action

在 `.worktrees/card-os-thin-client-v1` 按计划 Task 2 新建 `tests/test_card_os_client_credentials.py` 的 RED（凭据后端与泄露测试），验证 RED 后实现平台适配转 GREEN。

## Recovery Notes

- 本阶段基线 `f2a2462`（分支 == 任务建立提交）。恢复时先 `git rev-parse HEAD` 与 `git status --short`。
- 分支存档点：tag `archive/card-os-thin-skill-v1-20260717` = `7f321a6`（封存只读）。
- 未执行 push、merge、rebase、reset、删除；未修改 `outputs/`、存档分支 worktree、server worktree 与 `ops/` 冻结契约。
