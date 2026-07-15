# Cognitive Card OS 个人服务器部署设计

状态：已确认，待实施

日期：2026-07-14

目标版本：`cognitive-card-server` `0.3.0`，提交 `dc043ba4473915ebbd1a98c76dab46fcba703de3`

目标入口：`https://www.yutou.space/card-os/`

## 1. 目标与边界

本设计把已经验证的 Cognitive Card OS API 部署到个人服务器，并建立可重复发布、持久化、备份、验收和回滚能力。首版继续采用 ChatGPT Pro/Codex 登录客户端完成人工智能生成，不要求服务器持有 OpenAI API Key，也不代理 ChatGPT 身份或 Cookie。

本批次必须完成：

- 使用独立非登录用户运行应用，不以 root 身份承载业务进程；
- 以精确 Git 提交构建不可变发布包，并保留版本化 release 与快速回滚入口；
- 仅监听 `127.0.0.1:8765`，由现有 Nginx 提供 HTTPS 反向代理；
- 持久化 SQLite 数据库与候选资产，服务重启和 release 切换不得丢失；
- 建立每日在线备份、保留策略和可执行的恢复验证；
- 使用一次性管理员 token 完成受保护路径验收，随后立即撤销并验证撤销生效；
- 部署前后验证现有 `/`、`/kids/` 和 `/sync/` 不受影响。

本批次不包含：

- 自由概念输入到规范化锁定任务的服务器端编译；
- 长期保留的客户端 token、浏览器登录会话或多用户管理界面；
- 历史资产正式导入、Card OS 门户、四卡渲染和 PDF 发布；
- 替换现有 `/kids/` 静态站点；
- 迁移或改造 CouchDB、Docker、OpenClaw、MiGPT 等既有服务；
- 把 GitHub 私钥、个人访问令牌或仓库长期凭据放入服务器。

## 2. 已审计的服务器基线

以下事实来自 2026-07-14 的只读审计，实施开始前必须再次执行轻量漂移检查；若端口、站点配置、磁盘空间或证书状态发生实质变化，则停止部署并重新评估。

| 项目 | 审计结果 | 部署约束 |
| --- | --- | --- |
| 主机 | Ubuntu 24.04.4 LTS，x86_64，2 vCPU | 使用系统包和 systemd，不引入新的容器编排层 |
| 内存 | 3.8 GiB，约 2.4 GiB 可用，4 GiB swap | 首版单 Uvicorn 进程，避免无依据增加 worker |
| 根磁盘 | 40 GiB，已用约 21 GiB，可用约 18 GiB，使用率 54% | 部署前后记录空间；后续告警阈值早于 75% |
| Python | 3.12.3 | 满足应用 `>=3.11`；安装 `python3-venv` |
| Web | Nginx 1.24.0，服务活动 | 复用现有 Nginx 与证书，不另开公网应用端口 |
| 防火墙 | UFW 活动，默认拒绝入站 | 不开放 8765；只保留回环监听 |
| 现有数据服务 | CouchDB 容器绑定 `127.0.0.1:5984` | 不改变 CouchDB 容器和 `/sync/` 代理 |
| 现有站点 | 根路径和 `/kids/` 服务于 `/var/www/kids-visual-learning-pack/` | Card OS 只新增 `/card-os` 命名空间 |
| TLS | `yutou.space` 证书有效至 2026-08-23，Certbot timer 活动 | 复用域名证书并验证续期定时器；Card OS 不依赖 IP 证书 |
| IP 证书 | 审计时预计 2026-07-20 到期 | 记录为独立 OPS 风险，不纳入 Card OS 部署变更 |
| 当前 API 路径 | `/card-os/api/v1/health` 当前落入静态站 HTML fallback | Nginx 新规则必须先于静态 fallback 生效 |
| 系统工具 | 已有 `rsync`、`python3-pip`；未确认 `python3-venv`、`sqlite3` | 部署前安装缺失的 `python3-venv` 与 `sqlite3` |

## 3. 方案选择

采用方案 A：**systemd + Python venv + 版本化 release 目录 + Nginx 反向代理**。

选择理由：

- 与服务器现有 Ubuntu、systemd 和 Nginx 运维方式一致；
- 应用规模较小，单独引入 Docker Compose 会增加镜像、卷、代理和日志治理层；
- 每个 release 自带虚拟环境，依赖与代码可一起切换和回退；
- 服务器不需要 GitHub 凭据，不使用不可审计的在线 `git pull`；
- 数据目录与代码 release 分离，切换代码不会覆盖数据库或候选资产。

未采用方案 B（Docker Compose）：服务器虽已有 Docker，但 Card OS 不需要容器网络或多服务编排；首版增加容器层的收益不足以抵消卷权限、镜像构建和额外回滚路径。

未采用方案 C（服务器原地 `git pull`）：它会引入长期仓库凭据、工作树漂移和依赖不可重复问题，也不利于精确回滚。

## 4. 目标拓扑

```text
Codex / 薄 Skill
        |
        | HTTPS 443
        v
www.yutou.space (现有 Nginx)
        |
        | /card-os/api/* 保留完整 URI
        v
127.0.0.1:8765 (Uvicorn, systemd, user=cardos)
        |
        +-- SQLite: /var/lib/cognitive-card-server/card-os.sqlite3
        +-- candidates: /var/lib/cognitive-card-server/candidates/

Nginx 继续独立服务：
  /、/kids/ -> 现有静态站
  /sync/    -> 现有 CouchDB
```

公网只暴露 Nginx 的 80/443。应用端口 8765 既不加入 UFW 规则，也不绑定公网地址。

## 5. 文件系统、身份与权限

创建系统组和非登录系统用户 `cardos`。应用代码可读，运行数据和环境文件仅向 `cardos` 与 root 开放。

| 路径 | 用途 | 建议所有者与权限 |
| --- | --- | --- |
| `/opt/cognitive-card-server/releases/<commit>/` | 不可变应用代码和该 release 的 `.venv` | `root:root`，目录 `0755`，文件按需只读 |
| `/opt/cognitive-card-server/current` | 指向当前 release 的原子符号链接 | `root:root` |
| `/var/lib/cognitive-card-server/` | 持久化数据根；应用创建数据库的唯一父目录 | `cardos:cardos`，`0700` |
| `/var/lib/cognitive-card-server/card-os.sqlite3` | 持久化数据库 | `cardos:cardos`，`0600` |
| `/var/lib/cognitive-card-server/candidates/` | 候选结果隔离存储 | `cardos:cardos`，`0700` |
| `/etc/cognitive-card-server/card-os.env` | 非密钥运行配置；不得写入 machine token | `root:cardos`，`0640` |
| `/var/backups/cognitive-card-server/` | 本机备份与恢复验证工作区 | `root:root`，`0700` |

release 目录不允许应用进程写入。运行期唯一业务写路径是 `/var/lib/cognitive-card-server`。候选目录不配置 Nginx alias，也不存在公开静态下载入口。

安装器以受信任父目录 `/var/lib` 的文件描述符为起点，通过 `openat`/`mkdirat`、no-follow、`fchown` 和 `fchmod` 收敛数据根与候选目录，并在整个验证期间保持已打开的目录描述符。现有数据库仅能相对该数据根描述符做无链接的类型、所有者和模式检查。安装器分叉子进程、丢弃附加组并切换到 `cardos` uid/gid，再相对同一描述符执行不可预测名的 `O_EXCL` 私有写入探针；探针后重新比对根目录、候选目录与数据库的 device/inode 绑定，代换或竞态一律失败。

## 6. 可重复发布与激活

每次发布使用以下流程：

1. 在受信任工作站检出经过测试的精确提交；首版固定为 `dc043ba4473915ebbd1a98c76dab46fcba703de3`。
2. 从通过测试的运行环境生成精确 runtime dependency lock，并在受信任工作站从官方 `https://pypi.org/simple` 以 isolated、wheel-only 模式解析完整目标 wheelhouse；目标固定为 CPython 3.12、Linux x86_64，并同时声明 `manylinux_2_28_x86_64` 与 `manylinux_2_17_x86_64` 兼容选择器。服务器不访问任何包索引。
3. 生成包含应用 wheel、14 个精确 runtime wheels、依赖锁、单一受治理 `ops/wheel_audit.py` 和必要部署文件的 release 归档及 SHA-256 摘要；不兼容于旧格式的 wheelhouse/target 字段使用 `cognitive-card-server-release-v2` schema，manifest 逐文件绑定 wheelhouse 和审计器，并记录 implementation、Python version、ABI、platforms 与 only-binary 目标元数据。构建器与安装器共用该审计器：要求每个 ZIP 原始成员名等于其规范 POSIX 形式，拒绝别名与碰撞；检查归档/成员/数量/解压总量上限、高压缩的解压大小边界、精确 `.dist-info`、METADATA 的 Name/Version、WHEEL 的声明标签、RECORD 全覆盖的 SHA-256/大小。标签限定为 CPython 3.12/Linux x86_64：ABI `none` 允许 `py3`/`py312`/`cp312` 与 `any` 或允许的 Linux 平台组合；平台允许 `manylinux2014_x86_64`、不高于 `manylinux_2_28_x86_64` 的显式标签，并继续校验合法 `abi3` 下限。归档排除 sdist、额外/重复/版本漂移的 distribution、Git 元数据、缓存、测试临时文件、本地数据库和凭据。
4. 把归档、摘要和发布元数据上传到服务器临时目录，服务器先验证摘要。
5. 解压到 root 拥有的临时目录，先完成 manifest 字节摘要验证，再从已经 manifest 绑定的 payload 运行共享 wheel 审计器；通过后才发布到新的 `/opt/cognitive-card-server/releases/<commit>/`，不得覆盖已有同名 release。
6. 在 release 内创建 `.venv`，以 pip isolated、`--no-index` 和仅指向 release 内 `runtime-wheels/` 的 `--find-links` 离线安装 dependency lock，再以 `--no-index --no-deps` 安装本地应用 wheel；保留构建时 `release-manifest.json`，再把 `python --version`、实际 `pip freeze` 摘要、应用/运维 Git 提交、依赖锁摘要和归档摘要写入服务器侧 `install-manifest.json`，并验证实际依赖与锁一致。继承的 pip 环境变量、用户/系统配置和服务器镜像不能成为安装源。
7. 使用 `cardos` 身份运行导入探针和应用级启动探针，确认配置路径可读、数据路径可写。
8. 部署前完成数据库/候选目录备份并验证；随后原子切换 `current` 链接。
9. 重启 systemd 服务，完成本机和 HTTPS 验收；验收失败立即执行回滚。

服务器上不保存 GitHub 私钥或个人访问令牌。未来 release 继续使用“工作站构建归档 + 摘要上传”方式，或者升级为受控 CI 制品，但不切换为服务器在线拉取私有仓库。

## 7. systemd 服务设计

服务单元命名为 `cognitive-card-server.service`，核心约束如下：

- `User=cardos`、`Group=cardos`、`UMask=0077`；
- `WorkingDirectory=/opt/cognitive-card-server/current`；
- `EnvironmentFile=/etc/cognitive-card-server/card-os.env`；
- 通过当前 release 的 `.venv` 启动已安装应用；
- 固定 `CARD_OS_HOST=127.0.0.1`、`CARD_OS_PORT=8765`；
- 固定 `CARD_OS_DATABASE=/var/lib/cognitive-card-server/card-os.sqlite3`；
- 固定 `CARD_OS_CANDIDATE_ROOT=/var/lib/cognitive-card-server/candidates`；
- 固定 `CARD_OS_MAX_REQUEST_BYTES=29360128`、`CARD_OS_MAX_DECODED_PAYLOAD_BYTES=20971520`，与应用 `0.3.0` 保持一致；
- `Restart=on-failure`，设置有限重启间隔，避免故障热循环；
- `NoNewPrivileges=true`、`PrivateTmp=true`、`ProtectSystem=strict`、`ProtectHome=true`；
- `ReadWritePaths=/var/lib/cognitive-card-server`；
- 清空 Linux capability 集合，并限制为应用所需地址族；
- 日志进入 journald，不在命令行或单元文件中放置原始 token。

单元启动后必须验证监听地址为 `127.0.0.1:8765`，而非 `0.0.0.0` 或公网地址。应用自身已关闭 Uvicorn access log；认证错误和审计事件继续使用应用内脱敏日志，不记录 Authorization、原始 token 或带敏感 query 的完整 URL。

## 8. Nginx 路由与隐私

只在现有 `yutou-space` 站点中增加 Card OS 专属规则，不更改现有静态根、`/kids/`、`/sync/` 和其他服务的位置语义。

路由约定：

- 精确 `/card-os`：`308` 到 `/card-os/`；
- 精确 `/card-os/`：`307` 到 `/card-os/api/v1/capabilities`，作为首版可发现入口；
- `/card-os/api/`：代理到 `http://127.0.0.1:8765`，保留完整原始 URI，使应用继续接收 `/card-os/api/v1/...`；
- 传递 `Host`、客户端地址和 HTTPS 协议信息；
- `client_max_body_size 30m`，略高于应用 28 MiB 硬限制；应用仍是最终大小校验者；
- 连接超时 5 秒，读写超时 120 秒；
- Card OS API location 关闭 Nginx access log，避免 token 或敏感 query 因错误客户端行为进入通用访问日志；
- 不启用 CORS；首版只服务显式配置的受信任客户端；
- 不为 `/var/lib/cognitive-card-server/candidates/` 或备份目录提供静态映射。

变更前备份当前站点文件，变更后必须先通过 `nginx -t`，再执行无中断 reload。若配置测试失败，不 reload；若 reload 后现有站点回归失败，立即恢复备份配置并再次测试、reload。

## 9. 数据、备份与恢复

### 9.1 持久化边界

代码 release 是可替换制品；数据库和候选目录是持久化状态。任何发布或回滚都不得删除、覆盖或重新初始化 `/var/lib/cognitive-card-server`。安装器先拒绝 symlink 或非目录数据根，再把数据根本身收敛为 `cardos:cardos 0700`，之后才创建/验证候选目录。若数据库已存在，必须以 `lstat` 证明它是 `cardos:cardos 0600` 的非 symlink 普通文件；否则失败关闭且不改写数据。激活前由 `cardos` 以不可预测、排他创建的私有探针验证数据根可写，并只删除该探针。

首版没有上一版 Card OS 数据库，因此不存在向前 schema 迁移；仍需在首次启动前创建空数据目录，并在启动后验证应用按预期初始化。未来一旦引入 schema 迁移，每个 release 必须声明迁移兼容范围和数据库回滚条件，不能假定旧代码可读取新 schema。

### 9.2 每日备份

建立 `cognitive-card-backup.service` 与对应 systemd timer，每日执行：

备份服务是唯一保留 Linux capability 的进程：它以 root 运行，并将 `CapabilityBoundingSet` 与 `AmbientCapabilities` 都精确限制为 `CAP_DAC_READ_SEARCH`。这是因为数据库保持 `cardos:cardos 0600`、候选目录保持 `cardos:cardos 0700`；清空 capability 后，即使 UID 为 root，备份进程也无法绕过 DAC 读取数据库或遍历候选目录。`CAP_DAC_READ_SEARCH` 只提供完成只读备份所需的读取与目录搜索能力，不授予绕过 DAC 的写能力；不得加入任何其他 capability。备份服务继续通过 `ReadOnlyPaths=/var/lib/cognitive-card-server` 固定只读源，并只向 root-only 的 `/var/backups/cognitive-card-server` 和 `PrivateTmp` 提供写入空间。API 服务仍以 `cardos` 运行，`CapabilityBoundingSet=` 与 `AmbientCapabilities=` 保持为空。

1. 使用 SQLite 在线 backup 命令生成一致数据库快照，不直接复制活动中的数据库文件；
2. 对候选目录建立同一批次的文件快照；
3. 生成包含时间、数据库摘要、候选文件摘要和源 release 的 manifest；
4. 对备份数据库运行 `PRAGMA integrity_check`；
5. 在独立临时路径执行最小恢复探针，确认数据库可打开、manifest 可校验；
6. 仅在新备份完整验证后清理超过 14 天的本机备份。

备份失败必须返回非零状态并进入 journald。首版验收要求人工检查 timer 的下一次执行时间、手动触发一次备份并完成恢复探针。异地备份属于 OPS-01 后续工作；本次先建立可靠的本机恢复点，不把本机副本描述为灾难恢复完成。

## 10. 一次性 token 验收

本批次不保留长期 machine token。验收使用一次性管理员 token，流程固定如下：

1. 通过服务器本机受控命令签发带明确 `--expires-at`、用途明确的 admin token；
2. 原始 token 只进入当前验收进程的内存或权限为 `0600` 的临时文件，不回显到终端、工具输出、shell history、journald 或部署 manifest；
3. 携带 `Authorization: Bearer ...`、`X-Card-OS-Protocol: 1` 和 `X-Card-OS-Skill-Release: 0.1.0` 调用受保护但不改变业务状态的 `GET /card-os/api/v1/jobs/<nonexistent-id>`，以“已通过鉴权后的稳定 404”证明认证成功；
4. 重启应用服务，再次使用该 token 调用同一路径，证明认证状态和数据库在重启后保持；
5. 按 token ID 撤销该 token；
6. 再次请求同一路径必须得到 `403 AUTH_REVOKED`，与 `0.3.0` 的稳定错误契约一致，并证明撤销立即生效；
7. 删除原始 token 临时材料，并确认数据库和日志只保留安全标识、摘要与审计事件。

若任何步骤可能把原始 token 打印到 Codex 工具输出，必须改用服务器端脚本封装该步骤；不能用“之后清日志”替代零泄漏设计。

## 11. 部署、验收与回滚门禁

### 11.1 部署前门禁

- 当前服务器漂移检查与第 2 节关键事实一致；
- release manifest 声明精确 CPython 3.12/Linux x86_64 runtime target，`runtime-wheels/` 完整包含锁定的 14 个 wheel，且离线 dry resolution 成功；服务器安装不要求访问 PyPI 或任何镜像；
- 根磁盘使用率低于 75%，内存和 inode 无异常压力；
- `cognitive-card-server` 精确提交的完整测试仍通过；
- 发布归档摘要与 release manifest 一致；
- 当前 Nginx 站点配置、数据库和候选目录已有可验证备份；
- `nginx -t` 在变更前通过；
- `/`、`/kids/`、`/sync/` 和当前证书状态已记录基线。

### 11.2 部署后验收

- `systemctl is-active cognitive-card-server` 返回 active；
- `ss` 或同类检查证明只在 `127.0.0.1:8765` 监听，UFW 没有 8765 放行规则；
- 本机回环 health 与 capabilities 返回预期 JSON、版本和协议范围；
- `https://www.yutou.space/card-os/api/v1/health` 与 capabilities 通过正式域名证书返回预期 JSON；
- `/card-os` 与 `/card-os/` 的重定向符合第 8 节；
- 一次性 token 在服务重启前后通过受保护读取，撤销后立即变为 `403 AUTH_REVOKED`；
- 服务重启后数据库状态仍存在，候选目录仍可由 `cardos` 访问；
- Nginx 不可直接读取候选目录、数据库、环境文件或备份；
- 手动触发备份成功，数据库完整性检查和恢复探针通过；
- `/`、`/kids/`、`/sync/` 与部署前响应语义一致；
- Nginx 配置测试通过，Card OS 请求未把原始凭据写入访问日志或 journald。

任何一项关键验收失败，都不能把 DEPLOY-01 标为 DONE。

### 11.3 回滚

回滚优先恢复服务可用性，同时保护持久化数据：

1. 停止或隔离失败的 Card OS release；
2. 若故障来自 Nginx，恢复部署前站点配置，执行 `nginx -t` 后 reload；
3. 若故障来自应用，原子把 `current` 指回上一个已验收 release，再重启服务；
4. 只有确认数据库损坏且已有验证备份时才执行数据恢复；不得用旧备份覆盖健康的新数据；
5. 重新检查 `/`、`/kids/`、`/sync/` 和 Card OS 健康状态，记录故障 release、原因和处置。

首次部署没有上一个 Card OS release，应用回滚等价于停止并禁用新服务、恢复 Nginx 配置；现有静态站和 CouchDB 必须继续可用。未来 schema 发生变化后，只有 release manifest 明确声明向后兼容时才允许仅切换代码，否则必须执行该版本专属的数据恢复方案。

## 12. 风险与控制

| 风险 | 控制 |
| --- | --- |
| Nginx location 顺序导致请求继续落入静态 fallback | 使用精确和前缀规则；部署前 `nginx -t`，部署后检查 JSON content type 与版本 |
| 应用意外暴露公网端口 | 固定 loopback 配置、systemd 限制、监听检查、UFW 不开放 8765 |
| token 进入日志或 Codex 输出 | 关闭 API access log；token 不上命令行；服务器端封装签发、调用和撤销 |
| release 切换覆盖数据 | 代码与 `/var/lib` 分离；应用 release 只读；部署前备份 |
| SQLite 活动复制产生不一致备份 | 使用 SQLite 在线 backup，并执行完整性和恢复探针 |
| 本机备份随整机故障丢失 | 明确首版只完成本机恢复点；OPS-01 后续增加异地副本 |
| 现有站点或 CouchDB 被回归 | 只新增 `/card-os`；部署前后逐一验证 `/`、`/kids/`、`/sync/` |
| 证书临近到期 | 验证域名证书和 Certbot timer；IP 证书作为独立 OPS 风险跟踪 |
| 私有仓库凭据泄露 | 服务器只接收带摘要制品，不保存 GitHub 凭据 |
| 新 schema 阻断代码回滚 | 后续 release 强制声明 schema 兼容与恢复方式，不能盲目切换旧代码 |

## 13. 完成定义

只有以下条件同时满足，才能把 DEPLOY-01 标记为 `DONE`：

- 本设计经过用户审阅，并有独立实施计划；
- 精确 release 在非 root systemd 服务中稳定运行；
- 正式 HTTPS 路径、协议发现和受保护路径通过验收；
- 一次性 token 已撤销，服务器没有遗留长期 token 或原始凭据材料；
- 数据在服务重启后保持，备份和恢复探针通过；
- 现有 `/`、`/kids/`、`/sync/` 不受影响；
- 回滚流程至少完成配置级演练并留下验证记录；
- 路线图、运维记录和权威仓库版本已同步更新。
