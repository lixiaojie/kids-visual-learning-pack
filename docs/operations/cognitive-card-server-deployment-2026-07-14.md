# Cognitive Card OS 生产部署与运维记录

状态：`DEPLOY-01 DONE`；`OPS-01 IN PROGRESS`

实施日期：2026-07-14 至 2026-07-15（Asia/Shanghai）

生产入口：`https://www.yutou.space/card-os/`

本文是本次生产部署的脱敏证据和日常运维入口。动态任务状态仍以 [Cognitive Card OS 路线图](../cognitive-card-os-roadmap.md) 为准，架构边界以 [整体设计](../cognitive-card-os-system-design.md) 和 [个人服务器部署设计](../superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md) 为准。

## 1. 已部署的不可变身份

| 对象 | 已验证值 |
| --- | --- |
| 应用版本 | `0.3.1` |
| 应用提交 | `c2a898cba5b8a8948c06688d8c2a387353d7cbbe` |
| 治理/运维提交 | `404fdd31594300ab07ff0e087b62ccd0c59f982b` |
| release schema | `cognitive-card-server-release-v2` |
| 发布归档 SHA-256 | `a8a60ca7b49287ef27c15de1d0504fc879421c0ddd7c2e63175362f306a9421d` |
| 摘要 sidecar SHA-256 | `d7e995d6823ccd5ed226e810218a660f613dcca25826950027b95becca1328a4` |
| 独立审核安装器 SHA-256 | `b14e87549b1233cf7dea5b795c71c62d31cdbe6e0f632fe66eccc99f44083ecc` |
| release manifest SHA-256 | `b6dff51f...f1607`（服务器验收记录的缩写） |
| install manifest SHA-256 | `48f96098...58021`（服务器验收记录的缩写） |
| 已安装 runtime SHA-256 | `d1369f3c...2a851`（服务器验收记录的缩写） |
| 服务器 Python | `3.12.3` |

服务器离线安装 14 个锁定 runtime wheels 和应用 `0.3.1`；`pip check` 通过，安装后 freeze 只含受控 `name==version`，不含 URL 或直接引用。

## 2. 生产终态证据

### 2.1 主机、进程与网络

- Ubuntu `24.04` / `x86_64`，Nginx `1.24.0`。
- 根分区块使用率 `55%`，inode 使用率 `21%`；部署结束时无容量门禁异常。
- `cognitive-card-server.service` 已启用且活动，以 `cardos:cardos` 运行，`NRestarts=0`。
- API 只有一个 `127.0.0.1:8765` 监听，UFW 没有 8765 放行规则。
- `cognitive-card-backup.timer` 已启用且活动；验收时记录的下次运行为 `Thu 2026-07-16 03:26:09 CST`。
- Nginx、Certbot timer 和 Docker 活动；既有 CouchDB 仍只在 `127.0.0.1:5984` 监听。
- `www.yutou.space` 证书验收时有效期至 `2026-08-23T01:00:09Z`，Certbot timer 已启用且活动。

### 2.2 Nginx 与公开路由

- 活动站点：`/etc/nginx/sites-enabled/yutou-space`；该路径在验收时的 `readlink -f` 结果仍是它本身。
- 受管 snippet：`/etc/nginx/snippets/cognitive-card-server.conf`，`root:root 0644`，SHA-256 `e8579a5deb52c71e77ae6ada0cd201fd96c07be61389f65e0e1682544dfce4a7`。
- 活动站点 SHA-256 缩写为 `0d381092...25e9`，TLS server block 中恰有一个受管 include；`nginx -t` 通过。
- 成功激活前的字节保真备份：`/var/backups/cognitive-card-server/nginx/yutou-space.20260715T080258Z.conf`，`root:root 0600`。
- 共保留 9 份 `root:root 0600` Nginx 备份：6 份历史备份、2 次失败关闭尝试的备份和 1 份成功激活备份；不得将它们当作临时文件删除。

| 路径 | 验收结果 |
| --- | --- |
| `/card-os` | `308` 到同域 `/card-os/` |
| `/card-os/` | `307` 到同域 capabilities |
| `/card-os/api/v1/health` | `200` JSON，`status=ok`，`server_version=0.3.1` |
| `/card-os/api/v1/capabilities` | `200` JSON，schema v1，protocol `1..1`，minimum Skill release `0.1.0` |
| 10 个敏感外观/非 API `/card-os/` 路径 | 统一的通用 `404`，不返回应用 SPA 或受保护内容 |
| `/` | `200 text/html`，2725 bytes |
| `/kids/` | `200 text/html`，2725 bytes |
| `/sync/` | `401 application/json`，61 bytes |

### 2.3 一次性 token 验收（仅安全元数据）

- token ID：`972f366b71db85801f504cc12360568d`。
- subject：`deploy-acceptance-20260715T080300Z`。
- TTL：15 分钟；按受治理 helper 的“subject UTC 时间 + TTL”规则可推导 expiry 为 `2026-07-15T08:18:00Z`，但该字段没有作为直接观测值留存。
- 重启前后均经过鉴权并返回稳定 `404 JOB_NOT_FOUND`；撤销后立即返回 `403 AUTH_REVOKED`。
- 精确 `revoked_at` 未写入脱敏持久证据，不予推测。可验证终态为：验收 token 总数 4、活动 0、已撤销 4，`acceptance.json` 不存在。

### 2.4 备份与隔离恢复

- `cognitive-card-backup.service` 手动验收为 `Result=success`、`ExecMainStatus=0`，历史 failed 状态已清除。
- 服务器恰有一个规范批次：`/var/backups/cognitive-card-server/20260715T080302Z-c2a898cba5b8`。
- manifest SHA-256：`d031ee6a6717fd1b667b5126fd04a747fa4e0626ffda9ef90674740006cf9ed9`。
- 批次只包含 `manifest.json` 和自包含 `card-os.sqlite3`；当时候选文件为 0，没有备份 `-wal`/`-shm`。
- 备份库精确为 `journal_mode=delete`，integrity 为 `ok`，manifest 声明的大小、摘要、owner 和 mode 全部通过。
- 不可预测的 root-only 恢复目录只复制已验证批次，不向 live data path 写入；完整性、schema、安全计数和候选摘要与 live 状态一致，验证后恢复目录已删除。

## 3. 调用方式和 ChatGPT Pro 边界

公开发现端点不需要 token：

```bash
BASE=https://www.yutou.space/card-os
curl --fail-with-body --silent --show-error "$BASE/api/v1/health"
curl --fail-with-body --silent --show-error "$BASE/api/v1/capabilities"
```

受保护 API 必须携带 Card OS 自有 token 和协议头。下例只使用占位符；不要把真实 token 写入文档、命令历史或代码仓库。生产客户端应从操作系统凭据存储读取 `CARD_OS_TOKEN`。

```bash
BASE=https://www.yutou.space/card-os
CARD_OS_TOKEN='<CARD_OS_TOKEN>'
curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer ${CARD_OS_TOKEN}" \
  -H 'X-Card-OS-Protocol: 1' \
  -H 'X-Card-OS-Skill-Release: 0.1.0' \
  "$BASE/api/v1/jobs/<job-id>"
unset CARD_OS_TOKEN
```

当前运行模式与 ChatGPT Pro 兼容：

- Codex/ChatGPT Pro 仅在登录客户端内执行模型生成；个人服务器不代理模型请求。
- 服务器统一保存协议、任务、生成包、候选、审计和备份；客户端以薄 Skill 领取和提交。
- 这一模式不需要 OpenAI API Key，也不允许把 ChatGPT Cookie、会话、内部 Token 或身份材料上传到服务器。
- 当前已部署 API 只接受可验证的规范化锁定任务，不是“自由主题直接生成”接口。自由请求必须先由受信上游编译成内容锁定任务。

## 4. Day-2 只读健康检查

以 root 执行下列命令。它们不读取环境文件内容，不输出 token，不修改数据：

```bash
systemctl is-active cognitive-card-server nginx cognitive-card-backup.timer
systemctl is-enabled cognitive-card-server cognitive-card-backup.timer certbot.timer
systemctl show cognitive-card-server.service -p Result -p ExecMainStatus -p NRestarts
systemctl show cognitive-card-backup.service -p Result -p ExecMainStatus
systemctl list-timers cognitive-card-backup.timer --no-pager

readlink -f /opt/cognitive-card-server/current
ss -ltn '( sport = :8765 )'
ufw status | grep 8765
nginx -t

curl --fail-with-body --silent --show-error \
  http://127.0.0.1:8765/card-os/api/v1/health
curl --fail-with-body --silent --show-error \
  https://www.yutou.space/card-os/api/v1/health
curl --fail-with-body --silent --show-error \
  https://www.yutou.space/card-os/api/v1/capabilities

sqlite3 -readonly /var/lib/cognitive-card-server/card-os.sqlite3 \
  'PRAGMA integrity_check;'
df -h /
df -ih /
journalctl -u cognitive-card-server.service --since '24 hours ago' --no-pager \
  | grep -Eic 'Authorization|Cookie|ccos_v1\.|traceback|exception|error|failed'
```

预期：API/Nginx/timer 为 active，API/timer 为 enabled，`NRestarts=0`，恰有回环 8765 监听，`ufw ... | grep 8765` 没有输出且返回非零，health/capabilities 版本与协议匹配，SQLite 返回 `ok`，日志检查计数为 0。若根分区达到 `75%` 或证书进入预警窗口，按 OPS-01 升级处理。

## 5. 备份验证与隔离恢复演练

手动创建新备份只能通过受管 systemd service：

```bash
systemctl start cognitive-card-backup.service
systemctl show cognitive-card-backup.service -p Result -p ExecMainStatus
systemctl list-timers cognitive-card-backup.timer --no-pager
```

选择一个已发布批次后，先用受管 verifier 校验完整闭包：

```bash
BATCH=/var/backups/cognitive-card-server/20260715T080302Z-c2a898cba5b8
/usr/bin/python3 \
  /opt/cognitive-card-server/current/ops/card_os_backup.py verify \
  --backup-dir "$BATCH"
sha256sum "$BATCH/manifest.json"
```

隔离恢复不得把备份写回 `/var/lib/cognitive-card-server`：

```bash
RESTORE=$(mktemp -d /var/backups/cognitive-card-server/.restore-manual.XXXXXX)
chmod 0700 "$RESTORE"
install -o root -g root -m 0600 \
  "$BATCH/card-os.sqlite3" "$RESTORE/card-os.sqlite3"
sqlite3 -readonly "$RESTORE/card-os.sqlite3" 'PRAGMA journal_mode; PRAGMA integrity_check;'
sqlite3 -readonly "$RESTORE/card-os.sqlite3" \
  "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
sqlite3 -readonly "$RESTORE/card-os.sqlite3" \
  'SELECT COUNT(*) FROM card_os_tokens; SELECT COUNT(*) FROM subscriber_jobs; SELECT COUNT(*) FROM subscriber_job_events; SELECT COUNT(*) FROM generation_packets; SELECT COUNT(*) FROM generation_results;'
rm -rf -- "$RESTORE"
unset RESTORE BATCH
```

预期 journal mode 为 `delete`，integrity 为 `ok`，schema 与安全计数与 live 只读查询一致，演练后不留 `.restore-*` 目录。候选文件摘要已由 `card_os_backup.py verify` 按 manifest 全量重算，不用人工打开候选内容。

## 6. 受治理升级流程

只在受信工作站从精确、干净的应用提交构建制品；服务器不 `git pull`、不保存 GitHub 凭据、不访问 PyPI：

```bash
APP_REPO=/absolute/path/to/cognitive-card-server
APP_COMMIT=<reviewed-40-hex-application-commit>
OUT=/absolute/path/to/private-release-output
BUILD_PYTHON=/absolute/path/to/reviewed-build-venv/bin/python

git -C "$APP_REPO" status --porcelain
git -C "$APP_REPO" rev-parse HEAD
git status --porcelain --untracked-files=no
python3 ops/cognitive-card-server/build_release.py \
  --server-repo "$APP_REPO" \
  --expected-commit "$APP_COMMIT" \
  --output-dir "$OUT" \
  --python "$BUILD_PYTHON"
```

核对 builder JSON 中的应用提交、治理提交、归档路径和 SHA-256，完成独立发布审查后，上传归档、sidecar 和与该治理提交一致的安装器。在服务器先比对预期安装器摘要，再执行：

```bash
sha256sum /tmp/cognitive-card-server-release.tar.gz
sha256sum /tmp/cognitive-card-server-release.tar.gz.sha256
sha256sum /tmp/install_release.sh
/tmp/install_release.sh \
  /tmp/cognitive-card-server-release.tar.gz \
  /tmp/cognitive-card-server-release.tar.gz.sha256
```

安装器校验 archive/manifest/wheels，仅从归档内 wheelhouse 离线安装，创建新的不可变 release 目录，原子切换 `current` 并在后置门禁失败时回滚激活。不得覆盖同名 release，不得删除 `/var/lib/cognitive-card-server` 或已验证备份。升级后重跑第 4 节全部检查和一次受保护 API 验收。

## 7. 回滚

### 7.1 Nginx 配置回滚

下列命令恢复本次成功激活前的站点字节，同时保留当前站点的 owner/group/mode。恢复后 `/card-os` 将回到部署前静态 fallback：

```bash
SITE=$(readlink -f /etc/nginx/sites-enabled/yutou-space)
BACKUP=/var/backups/cognitive-card-server/nginx/yutou-space.20260715T080258Z.conf
SITE_UID=$(stat -Lc %u "$SITE")
SITE_GID=$(stat -Lc %g "$SITE")
SITE_MODE=$(stat -Lc %a "$SITE")
install -o "$SITE_UID" -g "$SITE_GID" -m "$SITE_MODE" "$BACKUP" "$SITE"
rm -f /etc/nginx/snippets/cognitive-card-server.conf
nginx -t
systemctl reload nginx
```

然后有界轮询 `/`、`/kids/`、`/sync/` 和旧 `/card-os/api/v1/health` baseline，不用一次即时请求判定 graceful reload 失败。不删除 `BACKUP` 或其他 Nginx 备份。

### 7.2 首次安装回滚

首次部署没有上一个 Card OS release 时，先执行第 7.1 节，再停止并禁用新服务和 timer：

```bash
systemctl disable --now cognitive-card-backup.timer
systemctl disable --now cognitive-card-server.service
systemctl is-active cognitive-card-server.service
systemctl is-enabled cognitive-card-backup.timer
```

保留 `/var/lib/cognitive-card-server`、`/var/backups/cognitive-card-server`、`/opt/cognitive-card-server/releases/` 和所有摘要/安装 manifest；首次回滚不等于删数据。只有证明数据损坏且选定了已验证备份时，才可制定单独数据恢复方案。

## 8. OPS-01 剩余工作

本次已完成本机 SQLite/候选备份、manifest 验证、隔离恢复和 14 天保留基础，但不能把它描述为完整灾难恢复。`OPS-01` 继续保持 `IN PROGRESS`，剩余项为：

1. 建立加密、可校验、可恢复的异地备份副本及失败告警；
2. 对根分区在 `75%` 之前告警，并监控 inode、备份新鲜度和保留清理；
3. 建立域名证书到期、Certbot 失败和公开 health/capabilities 失败的可投递告警。

审计时还记录了一张与 Card OS 域名证书无关的 IP 证书预计于 `2026-07-20` 到期；它是独立 OPS 风险，不影响本次 `www.yutou.space` 证书验收，但应单独确认使用方并处理。

## 9. 脱敏声明

本文不包含原始 token、真实 Authorization/Cookie 值、环境文件内容、数据库行内容、候选文件内容、私钥、GitHub 凭据或 ChatGPT 身份材料。示例中的 `<CARD_OS_TOKEN>` 是占位符，不是有效凭据。
