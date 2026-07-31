# Latest Handoff

## Metadata

- Updated At: 2026-07-31
- Agent: Kimi Code
- Branch: codex/card-os-thin-client-v1（worktree `.worktrees/card-os-thin-client-v1`）
- Base Commit: 2d64264（Task 1 提交；main 另有 docs-only 的 995c8b6 抢救优先更新）
- Working Tree: 仅 Task 2 产物（见 Changed Files）；主工作区 `outputs/` 为用户资产未触碰
- Task Status: SKILL-02 实施中；计划 Task 1 已提交（`2d64264`)，Task 2（凭据后端）已完成 RED→GREEN→review，随本提交落地

## Summary

Task 2 由全新 implementer 子代理执行：`tests/test_card_os_client_credentials.py`（67 个测试）先 RED（全部 AttributeError，接口不存在），随后扩展 `card_os_client.py`(467→1099 行）转 GREEN。实现要点：`CredentialStore` Protocol + 三个后端——macOS Keychain(Security.framework in-process ctypes，恰好绑定冻结的五个函数，service `cognitive-card-os`,account=规范 base URL,ctypes buffer 用后 `memset` 清零，OSStatus 不含密文）、Linux `secret-tool`(argv 仅元数据，token 走 stdin,sanitized env，输出捕获不落日志）、显式 `--allow-file-store` 的文件后端（父目录 0700 属主非链接、文件 `O_EXCL|O_NOFOLLOW` 0600,canonical JSON，同目录私有临时文件 + fsync + `os.replace`；违规 `CREDENTIAL_STORE_UNSAFE`，无后端 `CREDENTIAL_STORE_UNAVAILABLE`)。`CARD_OS_TOKEN` 请求时优先、绝不持久化、错误中脱敏；`auth status` 只报后端与存在性；`auth delete` 幂等。测试通过注入 fake Security framework / fake runner / 临时目录，全程不触碰真实 Keychain 与 secret service。

独立 reviewer 子代理结论：Critical 0 / Important 0 / Minor 5。两条测试加固 Minor(token 作位置参数必为 usage error；实际绑定符号集与冻结常量集逐一相等）已在提交前修正，现 104/104 PASS（69 credentials + 35 transport)。其余三条 Minor 结转 Task 3（见 Risks)。

## Completed

- 启动协议核实（Task 1 阶段）。
- Task 1 传输层 + capability 协商：RED→GREEN→review→commit(`2d64264`,35 测试）。
- Task 2 RED:67/67 error（接口缺失）。
- Task 2 最小 GREEN:104/104 PASS。
- Task 2 独立评审：0 Critical / 0 Important / 5 Minor，两条测试 Minor 已修正。
- 回归：`tests.test_card_os_skill_release test_card_os_skill_installer test_card_os_skill_publisher` 72/72 PASS；`find skills -name __pycache__` 为空；pre-commit 密钥扫描形态自查无命中。

## Changed Files

| File | Change | Reason |
| --- | --- | --- |
| `tests/test_card_os_client_credentials.py` | 新建（~860 行，69 测试） | Task 2 RED→GREEN 契约测试 |
| `skills/cognitive-card-os/scripts/card_os_client.py` | 修改（467→1099 行） | Task 2 三个凭据后端 + `auth` CLI |
| `docs/ai/HANDOFF.md` | 修改 | 本阶段交接（随业务代码同提交，pre-commit 钩子要求） |

## Decisions Made

- Keychain `delete()` 采用 erase-to-empty（经 `SecKeychainItemModifyAttributesAndData` 置零长数据，删除后 `get()`/`status` 视为 absent)：保持计划冻结的五函数绑定集，不引入 `SecKeychainItemDelete`；评审接受。
- stdin 校验失败复用冻结码 `REQUEST_VALIDATION_FAILED`（本地冻结码表无输入校验码，不得新造）；评审接受。
- `resolve_effective_token` 增加可注入可选参数（env/store/allow_file_store)；计划只冻结 Protocol 与 `select_credential_store` 签名，均逐字符合；评审接受。
- `auth set` 单次有界读取 `MAX_TOKEN_BYTES + 2`（优于无界 `read()`)；评审接受。
- darwin 选择时 eager `dlopen` Security.framework（不触碰任何 Keychain item)，加载失败落 `CREDENTIAL_STORE_UNAVAILABLE`；评审接受。

## Verification Results

| Command | Result | Notes |
| --- | --- | --- |
| `python3 -m unittest tests.test_card_os_client_credentials -v`（对 Task 1 版本） | RED（预期） | 67/67 error |
| `python3 -m unittest tests.test_card_os_client_credentials tests.test_card_os_client_transport` | PASS | 104/104（评审 Minor 修正后） |
| `python3 -m unittest tests.test_card_os_skill_release tests.test_card_os_skill_installer tests.test_card_os_skill_publisher` | PASS | 72/72,SKILL-01 冻结契约未破坏 |
| `auth status` 本机 smoke | PASS | exit 0，`{"backend":"macos-keychain","credential":"absent"}`，未触碰 Keychain item |
| 密钥扫描形态 grep（两文件） | PASS | 无命中 |
| `git diff --check` | PASS | 提交前 |

## Known Failures

- `node boards/kids-world/structure.test.mjs` 既有 `19 !== 18`，与本任务无关，本阶段未重跑。
- 存档分支 `codex/card-os-thin-skill-v1` 自身套件 19 errors + 1 failure，属封存资产，不影响本分支。

## Risks and Caveats

- 结转 Minor（Task 3 注意）:(1) 真实 Keychain 上重复 `delete()` 恒返回 True(erase-to-empty 使 item 仍存在，效果级幂等成立、返回值语义与文件/secret-tool 后端不同）;(2) 仅用文件后端的宿主上 `auth status`/`auth delete` 无 `--allow-file-store` 口，会报 `CREDENTIAL_STORE_UNAVAILABLE`（符合 spec §9 字面，Task 3+ 如需再议）;(3) `resolve_effective_token` 把选择失败吞为 `None`,Task 3 必须明确 `None` 的语义映射（本地 auth-required 路径）;(5) 非 `ClientError` 的存储异常（如 EPERM/磁盘满）会以 traceback 逃逸，与 Task 1 `doctor` 行为一致但非规范 error JSON。
- `_SecurityFramework` 的 ctypes 调用仅经 fake 单测与 `auth status` smoke 验证，未对真实 Keychain 做过 add/modify/delete;Task 7/8 隔离安装验收将首次真实写入，需用一次性测试凭据并事后 `auth delete`。
- 生产 packets/results 链路仍零真实流量；Task 8 现网验收为首跑。
- main 领先本分支 1 个 docs-only 提交（`995c8b6`),Task 6 集成时处理。

## Remaining Work

1. Task 3:packets/jobs 命令与稳定状态处理 RED→GREEN。
2. Task 4：结果校验与自动上传（required_outputs 闭包、凭据扫描、幂等 journal)。
3. Task 5:Skill 文档改写 + pre-publish probes;Task 6：构建 0.1.0 与 provisional stable 激活（集成/push 需用户授权）;Task 7–9：双隔离安装、现网验收、文档收尾。
4. 抢救批次（SKILL-02 之后、ACCEPT-01 之前，优先于从零重建）：迁移存档 `core/` 至服务器侧可信上游；修复 package-v5 两个评审 Block、publisher fixture 与 mode pin；处置误提交的 `.superpowers` 文件、3 个未跟踪计划与 library-design 未提交修订。

## Exact Next Action

在 `.worktrees/card-os-thin-client-v1` 按计划 Task 3 新建 `tests/test_card_os_client_packets.py` 的 RED（从服务器应用提交 `c2a898c` 复制 0.3.1 packet-envelope 与错误 fixture)，验证 RED 后实现命令状态机转 GREEN。

## Recovery Notes

- 本阶段基线 `2d64264`（分支尖端，Task 1 提交）。恢复时先 `git rev-parse HEAD` 与 `git status --short`。
- 分支存档点：tag `archive/card-os-thin-skill-v1-20260717` = `7f321a6`（封存只读）。
- 未执行 push、merge、rebase、reset、删除；未修改 `outputs/`、存档分支 worktree、server worktree 与 `ops/` 冻结契约。
