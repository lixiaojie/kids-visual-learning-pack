# Cognitive Card OS 薄 Skill 发布与客户端设计

状态：设计已确认并完成自审，待用户书面复核

日期：2026-07-15

目标版本：`cognitive-card-os` `0.1.0`

发布入口：`https://www.yutou.space/card-os/skill/v1/`

## 1. 目标

本设计把 Cognitive Card OS 从单机完整 Skill 逐步收敛为“私有 Git 源码权威 + 个人服务器发行权威 + 多终端薄客户端”。首版让安装了薄 Skill 的 Codex 客户端从服务器发现兼容版本，领取已经规范化并内容锁定的 GenerationPacket，使用登录的 ChatGPT Pro 在本地生成文本或图片候选，并由 Skill 自动校验、上传到服务器隔离候选区。

本批次包含两个顺序子项目：

1. `SKILL-01`：确定性构建、不可变 release、公开只读注册表、stable 指针、跨平台安装器、服务器发布与回滚。
2. `SKILL-02`：协议发现、凭据读取、任务领取、包校验、生成结果收集、自动上传、幂等和稳定错误解释。

本批次不要求 OpenAI API Key，不上传 ChatGPT Cookie、会话或身份材料，也不把完整知识注册表、模板库、生产资产或服务器渲染器放入薄 Skill。

## 2. 已确认的关键决策

- 采用静态不可变注册表，不为 Skill 发布新增 FastAPI/SQLite 业务模型。
- `kids-visual-learning-pack` 私有治理仓是薄 Skill 源码与构建规则的权威来源。
- `www.yutou.space` 是可安装 release、摘要、stable 指针和历史版本的发行权威。
- Skill 发行物公开只读；Card OS 任务 API 继续要求 scoped token。
- 安装器必须先下载、校验，再执行；不提供 `curl | sh` 用法。
- Codex 客户端以 Skill 自动上传为主；浏览器手动上传只作为后续备用通道。
- `0.1.0` 只执行服务器已存在的锁定任务。自由概念请求必须明确返回可信上游尚未编译，不能伪装为已创建任务。
- 首版先在隔离 `CODEX_HOME` 中验证，不覆盖当前本机完整 `cognitive-card-os`。正式切换等待 `ACCEPT-01` 通过。
- 在第二台真实 Codex 电脑安装同一摘要前，`SKILL-02` 保持 `IN PROGRESS`。

## 3. 权威边界与仓库布局

治理仓新增权威源码目录：

```text
skills/cognitive-card-os/
  SKILL.md
  agents/openai.yaml
  scripts/card_os_client.py
  references/protocol.md
  references/errors.md
```

Skill 目录不增加 README、安装指南、变更日志或项目过程文档。构建、发布、服务器运维和用户安装说明保留在治理仓的 `ops/`、`docs/` 和测试目录，不进入 Skill 上下文。

服务器应用仓 `cognitive-card-server` 继续拥有任务、协议、认证、候选存储和审计实现，但不成为薄 Skill 源码仓。个人服务器只保存经过摘要绑定的发行物和运行状态，不保存 GitHub 私钥、个人访问令牌或仓库工作树。

## 4. 薄 Skill 内容边界

`cognitive-card-os` `0.1.0` 发行包只包含：

- `SKILL.md`：触发条件、首版能力边界、领取/生成/上传流程和失败关闭规则；
- `agents/openai.yaml`：与 `SKILL.md` 一致的 Codex 展示元数据；
- `scripts/card_os_client.py`：Python 3.11+ 标准库客户端；
- `references/protocol.md`：协议头、命令、GenerationPacket 和 GenerationResult 契约；
- `references/errors.md`：服务器与本地稳定错误码的用户解释；
- `release.json`：由构建器生成的版本、兼容范围、源码提交和文件摘要。

`release.json` 不对自身做循环摘要。它声明除自身外的全部 Skill 文件；归档外层摘要再绑定包含 `release.json` 的完整 ZIP。归档中出现未声明文件、符号链接、硬链接、设备、绝对路径、`..`、重复规范路径、macOS 元数据、凭据形状文件或超限成员时，构建和安装均失败。

薄 Skill 不包含：

- 分类枚举、完整模板、知识注册表和事实来源库；
- 现有生产资产、历史 package、候选文件和数据库；
- ChatGPT、OpenAI、Card OS 或 GitHub 凭据；
- 服务端渲染、正式发布和门户实现；
- 把自由概念编译为 FACT、SEMANTIC CORE、模板和 CONTENT LOCK 的权威逻辑。

## 5. 版本与注册表契约

首版 Skill 版本固定为 SemVer `0.1.0`。服务器协议固定为无符号十进制 `1`，服务端最低版本为 `0.3.1`。版本比较必须按 SemVer 数值组件完成，不能按字符串字典序比较。

公开路径固定为：

```text
/card-os/skill/v1/manifest.json
/card-os/skill/v1/install.sh
/card-os/skill/v1/install.sh.sha256
/card-os/skill/v1/installers/<installer-sha256>/install.sh
/card-os/skill/v1/installers/<installer-sha256>/install.sh.sha256
/card-os/skill/v1/manifests/<manifest-sha256>.json
/card-os/skill/v1/releases/<version>/cognitive-card-os.zip
/card-os/skill/v1/releases/<version>/sha256.txt
```

`manifest.json` 使用 `cognitive-card-skill-registry-v1`，至少包含：

```json
{
  "schema": "cognitive-card-skill-registry-v1",
  "channel": "stable",
  "version": "0.1.0",
  "source_commit": "<40 lowercase hex>",
  "archive_url": "https://www.yutou.space/card-os/skill/v1/releases/0.1.0/cognitive-card-os.zip",
  "archive_sha256": "<64 lowercase hex>",
  "archive_size_bytes": 1,
  "protocol": {"minimum": 1, "maximum": 1},
  "minimum_server_version": "0.3.1",
  "published_at": "<RFC 3339 UTC Z>",
  "installer": {
    "url": "https://www.yutou.space/card-os/skill/v1/install.sh",
    "sha256": "<64 lowercase hex>"
  }
}
```

尖括号内容是字段格式元变量，不是待定设计项。示例中的 `archive_size_bytes` 仅说明字段类型；正式 manifest 必须记录真实正整数。JSON 使用 UTF-8、LF、排序键、紧凑分隔符和末尾单个换行。`sha256.txt` 精确为 `<archive-sha256>  cognitive-card-os.zip\n`；`install.sh.sha256` 精确为 `<installer-sha256>  install.sh\n`。

每次 stable 变化都先把新规范 manifest 发布为 `manifests/<其完整 SHA-256>.json`，再原子替换 `manifest.json`。历史 snapshot 和 release 永不覆盖。stable 回滚生成一个新的 manifest snapshot，指回已存在且重新验证的旧 release；不删除失败版本或改写历史 bytes。

## 6. 确定性构建

构建只能从干净、精确的治理仓提交运行。构建器从 Git 索引读取 Skill 声明文件，不把未跟踪文件、工作树漂移、Git 元数据或本机绝对路径带入归档。

ZIP 规则固定如下：

- 根目录精确为 `cognitive-card-os/`；
- 成员按 UTF-8 POSIX 相对路径排序；
- 普通文件模式规范为 `0644`，脚本规范为 `0755`；
- 目录模式规范为 `0755`；
- 时间戳来自源码提交时间并规范到 ZIP 可表示范围；
- 所有文件使用 `ZIP_STORED`，避免不同 zlib 实现产生跨平台字节漂移；
- 只允许普通文件和目录；
- 同一提交、同一输入在 macOS/Linux 上生成相同 ZIP bytes 和 SHA-256；
- 构建后重新打开 ZIP，验证闭合集、大小、模式、摘要和 `release.json`，不能只信写入过程。

构建器输出到忽略的 staging 目录，完成全部验证后才原子发布到本地 `dist/cognitive-card-skill/<version>/`。若最终目录已存在，只允许逐字节和逐摘要相同的幂等复核；任何差异都返回版本已存在错误。

## 7. 服务器静态注册表

服务器发行根固定为：

```text
/var/www/cognitive-card-skill-registry/v1/
```

发行根及内容由 `root:root` 拥有；目录为 `0755`，公开文件为 `0644`。发布脚本以 root 私有 staging 接收构建产物，重新计算所有摘要、解析规范 JSON、验证版本目录不存在并验证 stable 兼容性。通过后先原子发布 immutable release、installer snapshot 和 manifest snapshot，最后只原子更新 `manifest.json`。失败不得改变当前 stable。

顶层 `install.sh` 与 `install.sh.sha256` 是 v1 bootstrap 入口，不随普通 Skill stable 变化。manifest 的 `installer.url` 指向 `installers/<installer-sha256>/install.sh` immutable snapshot。bootstrap 只有在单独构建、摘要复核、两个隔离安装和回滚测试完成后才允许激活；普通 Skill 发布不能改写它。这避免 release stable 更新同时改写多个可变文件形成不一致窗口。

服务器用一个原子替换的 `installer-current` 目录符号链接选择已验证 installer snapshot；Nginx 两个精确顶层 installer URL 都经该同一链接读取文件。激活时只替换一个链接，因此脚本与 checksum 不会跨版本配对。链接目标必须是发行根内 `installers/<installer-sha256>/` 的 root-owned 非链接目录，发布脚本在切换前后都复核目标和两个文件摘要。

Nginx 在现有 Card OS deny-only catch-all 之前增加更长的只读 location：

```text
^~ /card-os/skill/v1/
```

该 location 仅映射发行根，允许 `GET` 和 `HEAD`，其他方法返回 `405`；关闭目录索引，不回退到站点 HTML，不代理到 Uvicorn，不暴露候选、数据库、备份或上传 staging。release 和 manifest snapshot 返回 `Cache-Control: public, max-age=31536000, immutable`；活动 `manifest.json`、`install.sh` 和 `install.sh.sha256` 返回 `Cache-Control: no-cache`。现有 `/`、`/kids/`、`/sync/` 和 `/card-os/api/` 语义保持不变。

## 8. 安装器

用户采用三步安装，不使用管道执行：

```bash
curl -fsSLO https://www.yutou.space/card-os/skill/v1/install.sh
curl -fsSLO https://www.yutou.space/card-os/skill/v1/install.sh.sha256
shasum -a 256 -c install.sh.sha256
bash install.sh --channel stable
```

Linux 可使用 `sha256sum --check install.sh.sha256`。安装器支持 macOS 和 Linux，使用 `${CODEX_HOME:-$HOME/.codex}`，并提供：

- `--channel stable`：安装活动 stable；
- `--version <semver>`：安装 manifest 已声明或服务器 immutable 路径上已验证的精确版本；
- `--check`：只验证远端、缓存和活动版本，不修改；
- `--rollback`：切换到本地已验证的前一版本；
- `--install-root <path>`：测试和隔离 `CODEX_HOME` 使用，正式文档不以它绕过默认权限边界。

安装器固定 HTTPS scheme、host `www.yutou.space` 和 `/card-os/skill/v1/` 路径前缀，拒绝所有重定向、降级、跨主机 URL、userinfo、query 和 fragment。它先限制 manifest、ZIP 和成员大小，再计算摘要；随后用安全解析器拒绝路径穿越、链接、设备、重复路径和未声明文件。验证 `release.json`、协议范围、服务器最低版本和闭合文件集后，才进入安装阶段。

活动目录固定为：

```text
${CODEX_HOME:-$HOME/.codex}/skills/cognitive-card-os
```

历史缓存固定为：

```text
${CODEX_HOME:-$HOME/.codex}/skill-releases/cognitive-card-os/<version>-<archive-sha256>/
```

安装器在同一父文件系统的私有临时目录完成解压和复核，再以重命名方式替换活动真实目录；不依赖 Codex 是否跟随符号链接。已有活动目录先移入已验证历史缓存。失败时恢复原活动目录；首次安装失败不得留下半安装目录。`--rollback` 只接受缓存中摘要和 `release.json` 仍一致的版本。安装或回滚成功后提示重启 Codex。

## 9. 凭据边界

Card OS token 永不进入 Skill 目录、release、GenerationResult、日志、命令参数、Git 或服务器静态注册表。客户端接受标准输入和临时环境变量 `CARD_OS_TOKEN`，但不得回显其值。

持久化优先级：

1. macOS Keychain，service 固定为 `cognitive-card-os`，account 绑定规范 base URL；
2. Linux Secret Service，通过可用的 `secret-tool` 存取同一 service/base URL；
3. 只有显式 `--allow-file-store` 才使用 `$XDG_CONFIG_HOME/cognitive-card-os/credentials.json`，缺省为 `$HOME/.config/cognitive-card-os/credentials.json`；父目录必须是当前用户拥有的 `0700` 非链接目录，文件必须是当前用户拥有的 `0600` 非链接普通文件。

没有可用凭据存储且未显式允许文件存储时，配置失败关闭。客户端不提供把 token 写入 Skill 配置或 shell profile 的便利选项。首版长期 token 的正式轮换仍属于 `AUTH-01`；现场验收使用短期、最小 `read+submit` token，并在验收后撤销。

## 10. 薄客户端命令与协议

`scripts/card_os_client.py` 只使用 Python 3.11+ 标准库，默认 base URL 固定为 `https://www.yutou.space/card-os/`。它提供：

- `doctor`：无认证读取 `/card-os/api/v1/health` 和 `/card-os/api/v1/capabilities`，检查 server version、protocol intersection 和 minimum Skill release；
- `auth set --stdin`、`auth status`、`auth delete`：配置、检查和删除客户端凭据，状态输出不含 token；
- `packets list`：读取 `/card-os/api/v1/packets/available`；
- `packets claim <packet-id>`：调用 `/packets/<packet-id>/claim`；
- `packets get <packet-id>`：读取并保存规范 GenerationPacket；
- `packets complete <packet-id>`：生成结束后调用 `/packets/<packet-id>/complete`；
- `results submit <packet-id> --directory <path>`：校验声明结果并调用 `/packets/<packet-id>/results`；
- `jobs status <job-id>` 和 `jobs events <job-id>`：读取服务器持久化状态和审计事件。

所有受保护请求精确携带：

```text
Authorization: Bearer <token>
X-Card-OS-Protocol: 1
X-Card-OS-Skill-Release: 0.1.0
```

结果提交的 `Idempotency-Key` 精确为 `ccos-v1-` 加 `SHA-256(packet_id + "\n" + canonical_request_body)` 的 64 位小写十六进制，因此同一 packet 和完全相同请求可安全重放，不同 packet 不会因结果 bytes 相同而碰撞。任何带 Authorization 的请求都使用禁用自动重定向的传输器；收到任意 `3xx` 即失败，不能把 bearer 发送到第二个地址。

客户端不调用 `/admin/locked-jobs` 或 `/admin/jobs/<job-id>/packets`，也不持有 admin token。自由概念输入、缺少 packet ID 或没有可见 packet 时，Skill 返回 `TRUSTED_UPSTREAM_REQUIRED`，并说明首版不能创建自由任务。

## 11. 本地生成与自动上传

GenerationPacket 是本地生成的唯一事实与输出边界。Skill 指导 Codex 使用登录的 ChatGPT Pro 和可用图像生成工具创建 packet 声明的文本或图片；脚本不调用 OpenAI API，也不保存 ChatGPT 会话。

生成文件先写入 packet 专属私有工作目录。提交前客户端必须：

1. 验证当前客户端仍是有效 claimant，packet 未过期且 content lock 未变；
2. 要求每个 `required_outputs` 恰好出现一次；
3. 拒绝绝对路径、`..`、链接、设备、未声明文件和路径规范碰撞；
4. 验证声明 media type、单文件 `max_bytes`、SHA-256 和实际大小；
5. 验证全部 decoded bytes 不超过 20 MiB，规范 JSON 请求体不超过 28 MiB；
6. 生成 `cognitive-card-generation-result-v1`，其中 `skill_release` 精确为 `0.1.0`；
7. 先调用 complete，再以稳定幂等键上传结果。

服务器重新解码、复算摘要并把通过的文件保存到内容寻址隔离候选区。客户端收到 acceptance receipt 后比对 result digest 和 staged artifact 摘要；不把“上传成功”描述为“正式发布”。图片预览、搜索、四卡/PDF 展示和正式发布属于 `PORTAL-01`、`RENDER-01`、`QA-01` 与 `PUBLISH-01`。

纯 ChatGPT 网页或手机没有本地 Skill 执行能力时，未来可使用 `UPLOAD-01` 浏览器手动上传；该备用表面不进入本批次。

## 12. 错误与恢复

客户端把本地和服务器错误映射为稳定代码，并给出可执行但不泄密的说明。至少覆盖：

- `CLIENT_UPGRADE_REQUIRED`：安装 manifest 的 stable 或指定兼容版本；
- `SERVER_UPGRADE_REQUIRED`：停止领取，等待服务器升级；
- `TRUSTED_UPSTREAM_REQUIRED`：需要已有锁定任务；
- `AUTH_REQUIRED`、`AUTH_REVOKED`、`AUTH_EXPIRED`、`AUTH_SCOPE_REQUIRED`：重新配置或轮换 scoped token；
- `PACKET_ALREADY_CLAIMED`、`PACKET_EXPIRED`、`LEASE_EXPIRED`、`LEASE_OWNER_MISMATCH`：刷新列表或等待重新签发；
- `MISSING_ARTIFACT`、`UNDECLARED_ARTIFACT`、`ARTIFACT_DIGEST_MISMATCH`、`ARTIFACT_MEDIA_TYPE_MISMATCH`、`ARTIFACT_SIZE_MISMATCH`、`ARTIFACT_TOO_LARGE`、`PAYLOAD_TOO_LARGE`、`UNSUPPORTED_ARTIFACT_MEDIA_TYPE`：在本地修正后使用同一逻辑提交意图；
- `IDEMPOTENCY_CONFLICT`：停止自动重试并要求人工检查；
- 客户端本地 `TRUSTED_UPSTREAM_REQUIRED`、`REDIRECT_REFUSED`、`TLS_REQUIRED`、`DIGEST_MISMATCH`、`UNSAFE_ARCHIVE`：失败关闭，不降级。

网络超时只允许对 GET、幂等检查和已绑定 `Idempotency-Key` 的完全相同结果请求做有界重试。claim、complete 或改变请求 bytes 的 submit 不能盲目重试；必须先读取服务器状态。

## 13. 安全切换

当前 `/Users/admin/.codex/skills/cognitive-card-os` 是完整知识卡生产 Skill。`0.1.0` 尚不能从“兔子，5～6岁”等自由请求生成锁定任务，因此本批次不得直接覆盖该活动目录。

验收先使用两个全新隔离根：

```text
<temp>/client-a/.codex
<temp>/client-b/.codex
```

两者必须从服务器安装同一 archive SHA-256，并分别证明全新安装、`doctor`、升级检查和本地回滚。一个隔离客户端再使用短期 `read+submit` token 完成现网领取与自动上传；token 随后撤销并验证拒绝。隔离根只含测试发行物和无密钥证据，原始 token 在验收结束前清除。

`SKILL-01` 可在服务器注册表通过全部门禁后标记 `DONE`。`SKILL-02` 在代码、隔离安装和现网候选上传通过后标记 `IN PROGRESS`；只有第二台真实 Codex 电脑安装相同摘要并通过兼容检查后才标记 `DONE`。`ACCEPT-01` 打通可信上游、兔子端到端生成、服务器验收和展示前，不切换本机活动 Skill。

## 14. 测试与验收

### 14.1 Skill TDD 基线

修改 Skill 前，使用不加载薄 Skill 的新鲜代理和空 `CODEX_HOME` 运行至少三个真实场景，记录失败行为：

1. 从服务器安装一个可验证 Skill；
2. 在无 OpenAI API Key 条件下领取已有图片任务并准备上传；
3. 面对自由概念请求时判断首版能力边界。

基线必须证明现状至少缺少确定性安装、自动上传或明确边界中的一项。随后才编写薄 Skill，并用相同场景做绿色 forward test；不得向测试代理泄露预期答案或缺陷诊断。

### 14.2 自动化测试

- 同一提交在 macOS/Linux 生成相同归档 bytes 和摘要；
- 脏工作树、错误提交、未声明文件和不可重复元数据被拒绝；
- manifest、release、installer 和每个文件的闭合摘要通过；
- 路径穿越、绝对路径、链接、设备、重复路径、压缩炸弹和篡改被拒绝；
- release 重复发布只有完全相同 bytes 才幂等；
- stable 发布失败不改变旧 manifest，回滚生成新 snapshot；
- 安装器在首次安装、升级中断、摘要失败和回滚失败时保持原活动版本；
- macOS/Linux 凭据后端与显式 `0600` fallback 权限门禁通过；
- token 不出现在 argv、stdout/stderr、日志、Skill、result、Git diff 或测试制品；
- capability、版本协商、禁重定向、超时和稳定错误映射通过；
- required outputs、media type、大小、摘要、总 decoded bytes、请求体和幂等通过；
- 自动上传成功、精确重放和冲突拒绝通过；
- 全量治理仓和服务器应用测试保持通过。

### 14.3 线上验收

- 六类公开路径通过有效 TLS 返回预期内容、状态码和缓存头；
- `GET`/`HEAD` 可用，其他静态方法 `405`，目录索引和 HTML fallback 关闭；
- immutable release 与本地构建摘要一致；
- 两个隔离客户端安装同一摘要，活动 Skill 文件逐字节一致；
- stable 回滚后新安装解析到旧 release，历史 release bytes 不变；
- 现有 `/`、`/kids/`、`/sync/`、`/card-os/api/`、Docker 和 CouchDB 无回归；
- 短期最小权限 token 完成一次已有 packet 的 claim、complete、自动 result upload 和幂等 replay；
- receipt、候选存储和审计一致，客户端不能直接发布；
- token 撤销后请求精确拒绝，服务器和客户端证据中无原始 token。

## 15. 发布失败与回滚

发布前记录当前 Nginx 站点摘要、注册表 manifest 摘要和 stable version。服务器发布失败只清理本次 root 私有 staging，不删除 immutable 历史。若 Nginx 配置测试失败，不 reload；若公开验收失败，恢复精确 Nginx 备份、验证后 reload，并把活动 manifest 原子恢复为发布前 bytes。

Skill stable 回滚不需要修改服务器应用或数据库。客户端安装失败恢复原活动目录；本地回滚失败保留活动版本、缓存和错误证据，不用未验证目录覆盖当前 Skill。任何摘要不一致都要求重新下载或人工检查，不能通过关闭验证继续。

## 16. 实施分解

本设计拆成两个独立实施计划并顺序执行：

1. `SKILL-01` 计划：Skill 源码骨架、RED 基线、确定性 builder、manifest/release validator、安装器、服务器 publisher、Nginx 静态注册表、服务器部署与 stable rollback 验收。
2. `SKILL-02` 计划：thin client、凭据后端、协议与错误文档、GREEN forward tests、两个隔离安装、现网领取与自动上传、路线图状态更新。

`SKILL-02` 依赖已经发布并验证的 `SKILL-01` release。不得把两者并行实现，也不得在 `SKILL-01` 评审未通过时开始客户端代码。门户、浏览器上传、自由概念编译、渲染、QA、正式发布和旧站替换不进入这两个计划。
