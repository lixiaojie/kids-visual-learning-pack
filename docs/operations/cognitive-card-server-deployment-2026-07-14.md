# Cognitive Card OS 生产部署与运维记录

状态：`DEPLOY-01 DONE`；`DEPLOY-02 DONE`；`WB-01 DONE`；`KNOW-03-prod DONE`（切片 A）；`OPS-01` 单人门禁见路线图

实施日期：2026-07-14 至 2026-07-15（Asia/Shanghai）；DEPLOY-02 现网落地 2026-08-31

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
| release manifest SHA-256 | `b6dff51f456afd25dfb9ad9fbb81d369dfe9559268093201b0292a50c62f1607` |
| install manifest SHA-256 | `48f9609857e84b9e965706d72393d2294c4ee17ddda362839ee64b2a9de58021` |
| 已安装 runtime SHA-256 | `d1369f3c42e48543dfe8f910eb3a3edf99cdf8ef24abd7efd6228242b962a851` |
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
- 活动站点 SHA-256 为 `0d3810925fb1aef878fe419abbfd4d7499e9c2379ac6b4ad9e741622206525e9`，TLS server block 中恰有一个受管 include；`nginx -t` 通过。
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

SITE-01 待应用路由（仓库内 snippet 已改，**尚未** reload 生产 Nginx）：精确 `/card-os/` 与 `/card-os/packages/` GET/HEAD 反代 `127.0.0.1:8765` 画廊；`/card-os/api/v1/capabilities` 保持 API JSON；敏感非画廊路径仍 catch-all 404。上表仍是 DEPLOY-01 验收快照。DEPLOY-02（2026-08-31）已应用该路由，现网抽查见第 10 节。

SITE-02 一次部署回滚（仓库内已接线）。把知识主 CTA 交回旧站时：

1. 确认现网仍需要旧站作为主入口，而不是只关掉画廊；
2. 把 `shared/knowledge-entry.json` 的 `activeMode` 改为 `parallel`；
3. 运行 `node scripts/render-knowledge-entry.mjs --write-hub`；
4. 按既有 `scripts/deploy.sh` 做一次静态部署（含重建 kids-world，以便档案说明随模式变化）。

不要恢复根入口 `http-equiv refresh`。`parallel` 只交换主 CTA。画廊 Nginx 回滚见第 10.6 节，不要用过期的第 7.1 节 snippet SHA。

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
set -euo pipefail
umask 077

BACKUP_ROOT=/var/backups/cognitive-card-server
BATCH="$BACKUP_ROOT/20260715T080302Z-c2a898cba5b8"
LIVE_DB=/var/lib/cognitive-card-server/card-os.sqlite3
RESTORE=

cleanup_restore() {
  [[ -z "$RESTORE" ]] && return 0
  [[ "$RESTORE" == "$BACKUP_ROOT"/.restore-manual.* ]]
  [[ -d "$RESTORE" && ! -L "$RESTORE" ]]
  [[ "$(stat -Lc '%U:%G %a' "$RESTORE")" == 'root:root 700' ]]
  rm -rf -- "$RESTORE"
}
trap cleanup_restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

[[ "$(readlink -f "$BACKUP_ROOT")" == "$BACKUP_ROOT" ]]
[[ -d "$BACKUP_ROOT" && ! -L "$BACKUP_ROOT" ]]
[[ "$(stat -Lc '%U:%G %a' "$BACKUP_ROOT")" == 'root:root 700' ]]
[[ -d "$BATCH" && ! -L "$BATCH" ]]

/usr/bin/python3 \
  /opt/cognitive-card-server/current/ops/card_os_backup.py verify \
  --backup-dir "$BATCH"

RESTORE=$(mktemp -d "$BACKUP_ROOT/.restore-manual.XXXXXXXX")
[[ "$RESTORE" == "$BACKUP_ROOT"/.restore-manual.* ]]
[[ -d "$RESTORE" && ! -L "$RESTORE" ]]
[[ "$(stat -Lc '%U:%G %a' "$RESTORE")" == 'root:root 700' ]]

install -o root -g root -m 0600 \
  "$BATCH/card-os.sqlite3" "$RESTORE/card-os.sqlite3"

RESTORED_DB="$RESTORE/card-os.sqlite3"
[[ "$(sqlite3 -readonly "$RESTORED_DB" 'PRAGMA journal_mode;')" == delete ]]
[[ "$(sqlite3 -readonly "$RESTORED_DB" 'PRAGMA integrity_check;')" == ok ]]

SCHEMA_SQL="SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
COUNTS_SQL='SELECT COUNT(*) FROM card_os_tokens; SELECT COUNT(*) FROM subscriber_jobs; SELECT COUNT(*) FROM subscriber_job_events; SELECT COUNT(*) FROM generation_packets; SELECT COUNT(*) FROM generation_results;'
[[ "$(sqlite3 -readonly "$RESTORED_DB" "$SCHEMA_SQL")" == \
   "$(sqlite3 -readonly "$LIVE_DB" "$SCHEMA_SQL")" ]]
[[ "$(sqlite3 -readonly "$RESTORED_DB" "$COUNTS_SQL")" == \
   "$(sqlite3 -readonly "$LIVE_DB" "$COUNTS_SQL")" ]]

cleanup_restore
[[ ! -e "$RESTORE" ]]
RESTORE=
trap - EXIT INT TERM
unset BACKUP_ROOT BATCH LIVE_DB RESTORED_DB SCHEMA_SQL COUNTS_SQL
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

核对 builder JSON 中的应用提交、治理提交、归档路径和 SHA-256，完成独立发布审查后，上传归档、sidecar 和与该治理提交一致的安装器。以下示例固定为本次已经审查的应用提交和三个摘要；后续升级必须把 `APP_COMMIT` 与三个 `EXPECTED_*` 值一起替换为该批次独立审查记录中的完整值，不能沿用旧值、改成通用文件名或人工目测前后缀：

```bash
set -euo pipefail

APP_COMMIT=c2a898cba5b8a8948c06688d8c2a387353d7cbbe
[[ "$APP_COMMIT" =~ ^[0-9a-f]{40}$ ]]

ARCHIVE="/tmp/cognitive-card-server-${APP_COMMIT}.tar.gz"
SIDECAR="${ARCHIVE}.sha256"
INSTALLER=/tmp/install_release.sh
EXPECTED_ARCHIVE_SHA256=a8a60ca7b49287ef27c15de1d0504fc879421c0ddd7c2e63175362f306a9421d
EXPECTED_SIDECAR_SHA256=d7e995d6823ccd5ed226e810218a660f613dcca25826950027b95becca1328a4
EXPECTED_INSTALLER_SHA256=b14e87549b1233cf7dea5b795c71c62d31cdbe6e0f632fe66eccc99f44083ecc

for digest in \
  "$EXPECTED_ARCHIVE_SHA256" \
  "$EXPECTED_SIDECAR_SHA256" \
  "$EXPECTED_INSTALLER_SHA256"
do
  [[ "$digest" =~ ^[0-9a-f]{64}$ ]]
done

for file in "$ARCHIVE" "$SIDECAR" "$INSTALLER"
do
  [[ -f "$file" && ! -L "$file" ]]
done

[[ "$(sha256sum "$ARCHIVE" | awk '{print $1}')" == "$EXPECTED_ARCHIVE_SHA256" ]]
[[ "$(sha256sum "$SIDECAR" | awk '{print $1}')" == "$EXPECTED_SIDECAR_SHA256" ]]
[[ "$(sha256sum "$INSTALLER" | awk '{print $1}')" == "$EXPECTED_INSTALLER_SHA256" ]]

[[ "$(wc -l < "$SIDECAR" | tr -d ' ')" == 1 ]]
SIDECAR_LINE=$(<"$SIDECAR")
EXPECTED_SIDECAR_LINE="$EXPECTED_ARCHIVE_SHA256  $(basename "$ARCHIVE")"
[[ "$SIDECAR_LINE" == "$EXPECTED_SIDECAR_LINE" ]]

(
  cd "$(dirname "$ARCHIVE")"
  sha256sum --check "$(basename "$SIDECAR")"
)

"$INSTALLER" "$ARCHIVE" "$SIDECAR"
```

安装器校验 archive/manifest/wheels，仅从归档内 wheelhouse 离线安装，创建新的不可变 release 目录，原子切换 `current` 并在后置门禁失败时回滚激活。不得覆盖同名 release，不得删除 `/var/lib/cognitive-card-server` 或已验证备份。升级后重跑第 4 节全部检查和一次受保护 API 验收。

## 7. 回滚

### 7.1 Nginx 配置回滚

下列命令恢复本次成功激活前的站点字节，同时保留当前站点的 owner/group/mode。恢复后 `/card-os` 将回到部署前静态 fallback：

```bash
set -euo pipefail

SITE_LINK=/etc/nginx/sites-enabled/yutou-space
EXPECTED_SITE=/etc/nginx/sites-enabled/yutou-space
BACKUP=/var/backups/cognitive-card-server/nginx/yutou-space.20260715T080258Z.conf
SNIPPET=/etc/nginx/snippets/cognitive-card-server.conf
ORIGINAL_SITE_SHA256=1fd6b966fd44fee3ea2d18b5ebea99e1b1fc674838af3ed7e025bfdd1c2e02c0
ACTIVE_SNIPPET_SHA256=e8579a5deb52c71e77ae6ada0cd201fd96c07be61389f65e0e1682544dfce4a7
EXPECTED_ACTIVE_SITE_SHA256=0d3810925fb1aef878fe419abbfd4d7499e9c2379ac6b4ad9e741622206525e9

[[ "$ORIGINAL_SITE_SHA256" =~ ^[0-9a-f]{64}$ ]]
[[ "$ACTIVE_SNIPPET_SHA256" =~ ^[0-9a-f]{64}$ ]]
[[ "$EXPECTED_ACTIVE_SITE_SHA256" =~ ^[0-9a-f]{64}$ ]]

SITE=$(readlink -f -- "$SITE_LINK")
[[ "$SITE" == "$EXPECTED_SITE" ]]
[[ -f "$SITE" && ! -L "$SITE" ]]
if [[ "$(sha256sum "$SITE" | awk '{print $1}')" != "$EXPECTED_ACTIVE_SITE_SHA256" ]]; then
  printf 'error=ACTIVE_SITE_DRIFT\n' >&2
  exit 1
fi
[[ -f "$BACKUP" && ! -L "$BACKUP" ]]
[[ "$(stat -Lc '%U:%G %a' "$BACKUP")" == 'root:root 600' ]]
[[ "$(sha256sum "$BACKUP" | awk '{print $1}')" == "$ORIGINAL_SITE_SHA256" ]]

SITE_UID=$(stat -Lc %u "$SITE")
SITE_GID=$(stat -Lc %g "$SITE")
SITE_MODE=$(stat -Lc %a "$SITE")
[[ "$SITE_UID" =~ ^[0-9]+$ && "$SITE_GID" =~ ^[0-9]+$ ]]
[[ "$SITE_UID" == 0 && "$SITE_GID" == 0 ]]
[[ "$SITE_MODE" =~ ^[0-7]{3,4}$ ]]

if [[ -e "$SNIPPET" ]]; then
  [[ -f "$SNIPPET" && ! -L "$SNIPPET" ]]
  [[ "$(stat -Lc '%U:%G %a' "$SNIPPET")" == 'root:root 644' ]]
  [[ "$(sha256sum "$SNIPPET" | awk '{print $1}')" == "$ACTIVE_SNIPPET_SHA256" ]]
fi

install -o "$SITE_UID" -g "$SITE_GID" -m "$SITE_MODE" "$BACKUP" "$SITE"
[[ "$(sha256sum "$SITE" | awk '{print $1}')" == "$ORIGINAL_SITE_SHA256" ]]
rm -f -- "$SNIPPET"
nginx -t
systemctl reload nginx
[[ -f "$BACKUP" && ! -L "$BACKUP" ]]
[[ "$(sha256sum "$BACKUP" | awk '{print $1}')" == "$ORIGINAL_SITE_SHA256" ]]
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

## 8. OPS-01 / OPS-02

本次已完成本机 SQLite/候选备份、manifest 验证、隔离恢复和 14 天保留基础。按 [ADR-004](../decisions/ADR-004-single-operator-main-flow.md)，`OPS-01` 单人门禁以此为本机恢复点完成，**不把本机副本描述为完整灾难恢复**。

`OPS-02`（BACKLOG，不阻塞知识主路径）简化为：

1. 需要时把已验证的 `/var/backups/cognitive-card-server` 拷到第二块盘或另一台机器，并抽查一次隔离恢复；不设计加密复制服务或告警栈。
2. 后期可选：根分区在 `75%` 之前的容量/inode/备份新鲜度提醒；证书、Certbot 与公开 health/capabilities 失败的可投递告警。

审计时还记录了一张与 Card OS 域名证书无关的 IP 证书预计于 `2026-07-20` 到期；它是独立 OPS 风险，不影响本次 `www.yutou.space` 证书验收，但应单独确认使用方并处理。

## 9. 脱敏声明

本文不包含原始 token、真实 Authorization/Cookie 值、环境文件内容、数据库行内容、候选文件内容、私钥、GitHub 凭据或 ChatGPT 身份材料。示例中的 `<CARD_OS_TOKEN>` 是占位符，不是有效凭据。

## 10. DEPLOY-02 现网落地试点（2026-08-31）

本节追加现网终态，**不改写**第 1 节与第 2.2 节的 0.3.1 历史证据表。DEPLOY-01 归档 `c2a898cba5b8a8948c06688d8c2a387353d7cbbe` 仍留在 `/opt/cognitive-card-server/releases/`。

### 10.1 不可变身份（本批）

| 对象 | 已验证值 |
| --- | --- |
| 应用版本 | `0.3.1`（`pyproject` 未升版） |
| 应用提交 | `fd696c2a8cab5400a5d78669031a501390ab5318`（`knowledge-pipeline-v1`，未 merge `main`） |
| 治理/运维提交 | `3432e8381dfd6797d0f173b5149118bb70348124` |
| release schema | `cognitive-card-server-release-v2` |
| 发布归档 SHA-256 | `6a3b8cd2bf336f65da454003ca135904613880af9410dfce2ce4b7eb295ca9ed` |
| 摘要 sidecar SHA-256 | `f1573a4f1a9132c897da68e56bebe374cc6faaf89136762ffb8de2338fa7383c` |
| 安装器 SHA-256 | `e34e0b91c6378dc294347337befb3e7c263957fd764aae381067143927474803` |
| release manifest SHA-256 | `b1089c21c83978c9f7e90b36005e385484f03181c0a61fef653c41cf30525a55` |
| install manifest SHA-256 | `449ae5d21aaa9ed043cab40b9493edab6af4a1ec52a3ae93bd43665291727a6a` |
| 已安装 runtime SHA-256 | `d1369f3c42e48543dfe8f910eb3a3edf99cdf8ef24abd7efd6228242b962a851` |
| 服务器 Python | `3.12.3` |
| 安装时间 | `2026-08-31T08:04:40Z` |

后续升级必须把第 6 节示例中的 `APP_COMMIT` 与三个 `EXPECTED_*` 换成**该批次**完整值，不能沿用 DEPLOY-01 的 `c2a898c` 摘要。

第二次对同一 `fd696c2` 调用安装器得到 `RELEASE_EXISTS`（fail-closed，未覆盖）。`current` 已指向该 release。不要删除未标记的旧 release 目录。

### 10.2 进程、网络与第 4 节复查

- `cognitive-card-server.service` active，`Result=success`，`NRestarts=0`，`ExecMainStatus=0`。
- 监听仍是唯一 `127.0.0.1:8765`；UFW 无 8765 放行。
- `nginx` 与 `cognitive-card-backup.timer` active；Certbot timer enabled。
- 回环与公网 `GET /card-os/api/v1/health` 均为 `200`，`server_version=0.3.1`。
- 公网 capabilities：schema v1，protocol `1..1`，minimum Skill `0.1.0`；`free_form_job_creation=false`。
- SQLite `PRAGMA integrity_check` 为 `ok`。
- 根分区约 `63%` / inode `22%`，未到 75% 门禁。

### 10.3 Nginx 画廊路由

替换前生产 snippet SHA-256 为 `f734b0e93c94405ab2e44910dc9d95d08a78d3358a6f0950ed1ddc3b378f9446`（相对第 2.2 节 `e8579a5…` 已含 Skill 注册表 location；§7.1 里的 `ACTIVE_SNIPPET_SHA256` 因此已经对不上，不能当画廊回滚脚本原样执行）。

- 字节保真备份：`/var/backups/cognitive-card-server/nginx/cognitive-card-server.20260831T083618Z.pre-deploy-02.conf`，SHA-256 与替换前一致。
- 现网 snippet：仓库 `ops/cognitive-card-server/nginx/card-os.conf`，`root:root 0644`，SHA-256 `d3d38a36f1fa488cad89b125a7180661e0151d335f22e79d5e8c9e49bc1649b0`。
- `nginx -t` 通过后 `systemctl reload nginx`。

| 路径 | DEPLOY-02 验收 |
| --- | --- |
| `/card-os/` | `200 text/html`，标题 `Published artifacts`，列出 `rabbit` |
| `/card-os/api/v1/health` | `200` JSON，`status=ok`，`0.3.1` |
| `/card-os/api/v1/capabilities` | `200` JSON，protocol `1..1` |
| `/card-os/packages/rabbit/revisions/0001/files/print.pdf` | `200`，1,728,853 bytes |
| `/card-os/skill/v1/manifest.json` | `200` |
| `/card-os/api/v1/admin/portal/packages` | `401`（无 token） |
| `/card-os/jobs` | 通用 `404` |
| `/` 与 `/kids/` | `200 text/html`，2708 bytes，主 CTA `aria-label="打开 Card OS 知识画廊"`，HTML 不含 `spider-verse` / `paw-patrol` 链接 |

### 10.4 公开包

- catalog 根：`/var/lib/cognitive-card-server/candidates/package-catalog`（`cardos:cardos`）。
- 种子：ACCEPT-01 `rabbit` `revision-0001`；`visibility` 缺省为 public。
- `content_lock_sha256=sha256:f53f4e03863cd56fee560f85bcb2974ff4dbd2e4bd8b447f8fdb214338695f37`
- `package_sha256=sha256:c56a29475a585a1bf33a35beb306d64e2157e83910647ec0368f19c111c9b69f`
- 未改 `candidates/sha256/` 既有候选对象。

### 10.5 根入口与 stub

`scripts/deploy.sh` 上传根 `index.html`、`shared/`、`docs/`、kids-world dist、13 个 `boards/{slug}/` stub。stub 的 rsync **没有** `--delete`。`activeMode` 保持 `card-os`。

浏览器抽查：`/kids/` 主 CTA 进入画廊；`/kids/boards/kids-world/#dinosaurs` 打开「恐龙与化石侦探站」；`/kids/boards/dinosaurs/` 为替代说明页（非 404）。

### 10.6 回滚（本批）

只把画廊路由退回 capabilities 307（保留 Skill 注册表）时，**不要**跑第 7.1 节（它会按过期 snippet SHA fail-closed，且会删掉 include）：

```bash
set -euo pipefail
SNIPPET=/etc/nginx/snippets/cognitive-card-server.conf
BACKUP=/var/backups/cognitive-card-server/nginx/cognitive-card-server.20260831T083618Z.pre-deploy-02.conf
EXPECTED_ACTIVE=d3d38a36f1fa488cad89b125a7180661e0151d335f22e79d5e8c9e49bc1649b0
EXPECTED_BACKUP=f734b0e93c94405ab2e44910dc9d95d08a78d3358a6f0950ed1ddc3b378f9446
[[ "$(sha256sum "$SNIPPET" | awk '{print $1}')" == "$EXPECTED_ACTIVE" ]]
[[ "$(sha256sum "$BACKUP" | awk '{print $1}')" == "$EXPECTED_BACKUP" ]]
install -o root -g root -m 0644 "$BACKUP" "$SNIPPET"
nginx -t
systemctl reload nginx
```

把知识主 CTA 交回旧站时：把 `shared/knowledge-entry.json` 的 `activeMode` 改为 `parallel`，运行 `node scripts/render-knowledge-entry.mjs --write-hub`，再一次 `scripts/deploy.sh`。不要恢复 `http-equiv refresh`。

应用 release 仍可通过 `current` 指回 `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`；本批未演练该切换。未授权 merge server `main`。

## 11. WB-01 操作台（2026-08-31 现网）

日期：2026-08-31。不改写第 1–10 节历史表。

### 11.1 不可变身份（本批）

| 对象 | 已验证值 |
| --- | --- |
| 应用版本 | `0.3.1`（`pyproject` 未升版） |
| 应用提交 | `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`（`knowledge-pipeline-v1`，未 merge `main`） |
| 治理/运维提交 | `bbefb9f4343f2ecd9d569192c2348008735d9c75` |
| release schema | `cognitive-card-server-release-v2` |
| 发布归档 SHA-256 | `539e52aedf503603b7fda8a02817025cb473be843c74f2a603e134ddde3eac52` |
| 摘要 sidecar SHA-256 | `de2477abfe6a0e3925ad686102b049a4d8ae4e77378f4566a97ac3dcdd614946` |
| 安装器 SHA-256 | `e34e0b91c6378dc294347337befb3e7c263957fd764aae381067143927474803` |
| release manifest SHA-256 | `fcf24d164d1af14680b53bffcd9156f8a849a1280b96ea2d27b2029ab96b9680` |
| install manifest SHA-256 | `b28e1b69c41e7b474c9e4237257a79bc981b1f0f059852277b561bb45da2ef0b` |
| 已安装 runtime SHA-256 | `d1369f3c42e48543dfe8f910eb3a3edf99cdf8ef24abd7efd6228242b962a851` |
| 服务器 Python | `3.12.3` |
| 安装时间 | `2026-08-31T10:21:37Z` |

`current` 已从 `fd696c2` 指到 `115377b`。旧 release 目录保留。不要删除未标记的旧 release。

### 11.2 知识库种子

- library 根：`/var/lib/cognitive-card-server/candidates/knowledge-library`（`cardos:cardos` `0700`）。
- 输入：AUTHOR-02 `examples/authoring/rabbit-real.json`，`projection: {}`，**没有** `family=four-card` 覆盖。
- `rabbit` revision-0001 为 current（reason `publish`）：4 `knowledge_units` / 8 `propositions` / 4 `sources`。
- 对 current 目录重算选择面：chosen `chaptered-guide`，`source=default`；`four-card` `fit=discouraged`，`COMPRESSES_COMPOSITE`。
- 画廊 catalog 未改：`package_sha256=sha256:c56a29475a585a1bf33a35beb306d64e2157e83910647ec0368f19c111c9b69f`；PDF 仍 1,728,853 bytes。

本批未签发新的生产 admin token。操作员用既有 admin Bearer 打开 `/card-os/ops/`。

### 11.3 Nginx ops 路由

替换前 snippet SHA-256 为 `d3d38a36f1fa488cad89b125a7180661e0151d335f22e79d5e8c9e49bc1649b0`（DEPLOY-02 画廊 snippet）。

- 字节保真备份：`/var/backups/cognitive-card-server/nginx/cognitive-card-server.20260831T104513Z.pre-wb-01.conf`。
- 现网 snippet：仓库 `ops/cognitive-card-server/nginx/card-os.conf`，`root:root 0644`，SHA-256 `0ed25814ed84a8b5b242f8994ca2303f04a61b83f0a5f4927c912ac58a0060a1`。
- `nginx -t` 通过后 `systemctl reload nginx`。

| 路径 | WB-01 验收 |
| --- | --- |
| `/card-os/` | `200 text/html`，标题 `Published artifacts`，列出 `rabbit` |
| `/card-os/ops/` | `200 text/html`；无 token 页面不含 Merck / `canonical_claim` / `src.rabbit` / `chaptered-guide` |
| `/card-os/ops/rabbit` | `200 text/html`，同样无命题正文 |
| `/card-os/api/v1/admin/knowledge-library` | `401`（无 token） |
| `/card-os/packages/rabbit/revisions/0001/files/print.pdf` | `200`，1,728,853 bytes |
| `/card-os/api/v1/health` | `200`，`0.3.1` |
| `/card-os/jobs` | 通用 `404` |
| 监听 | 唯一 `127.0.0.1:8765`；`NRestarts=0`；SQLite integrity `ok` |

### 11.4 回滚（本批）

只把 ops 路由退回 DEPLOY-02 画廊 snippet 时：

```bash
set -euo pipefail
SNIPPET=/etc/nginx/snippets/cognitive-card-server.conf
BACKUP=/var/backups/cognitive-card-server/nginx/cognitive-card-server.20260831T104513Z.pre-wb-01.conf
EXPECTED_ACTIVE=0ed25814ed84a8b5b242f8994ca2303f04a61b83f0a5f4927c912ac58a0060a1
EXPECTED_BACKUP=d3d38a36f1fa488cad89b125a7180661e0151d335f22e79d5e8c9e49bc1649b0
[[ "$(sha256sum "$SNIPPET" | awk '{print $1}')" == "$EXPECTED_ACTIVE" ]]
[[ "$(sha256sum "$BACKUP" | awk '{print $1}')" == "$EXPECTED_BACKUP" ]]
install -o root -g root -m 0644 "$BACKUP" "$SNIPPET"
nginx -t
systemctl reload nginx
```

不要删除 knowledge-library 种子。应用 `current` 仍可通过指回 `fd696c2a8cab5400a5d78669031a501390ab5318` 退回画廊-only 应用；本批未演练该切换。未授权 merge server `main`。

## 12. KNOW-03-prod 只换应用（2026-09-01）

日期：2026-09-01。切片 A：只把应用 `current` 从 WB-01 `115377b` 换到 KNOW-03 `7aaeb2b`。不改写第 1–11 节历史表。不 reload Nginx。不重种 knowledge-library。未 merge server `main`。未 push。

### 12.1 不可变身份（本批）

| 对象 | 已验证值 |
| --- | --- |
| 应用版本 | `0.3.1`（`pyproject` 未升版） |
| 应用提交 | `7aaeb2b80e591f348c54eb35fb18793e213c5122`（`knowledge-pipeline-v1`，未 merge `main`） |
| 治理/运维提交 | `da45e4f3ce8ca31f0ab1edd117ed711a1cb504fb`（打 release 时 kids HEAD；本批证据文档其后提交） |
| release schema | `cognitive-card-server-release-v2` |
| 发布归档 SHA-256 | `cf16a42b62078c1970853f40b38bb80b5698b6d84f248852c634fd9de90d534d` |
| 摘要 sidecar SHA-256 | `13df7ee9dade0f5f9cb82a549e4aac3042283727fc911e445f7de5f2785d9b13` |
| 安装器 SHA-256 | `e34e0b91c6378dc294347337befb3e7c263957fd764aae381067143927474803` |
| release manifest SHA-256 | `bee9ee82d5f666fe6b242975cc86f4df6ae1de6eb4a8cd9d06ece5cc749d50ae` |
| install manifest SHA-256 | `993599e643f5e3e1849b00e844f3a788d53bab9602605f40ecefbd062ee61092` |
| 已安装 runtime SHA-256 | `d1369f3c42e48543dfe8f910eb3a3edf99cdf8ef24abd7efd6228242b962a851`（与 WB-01 锁定 wheels 相同） |
| 服务器 Python | `3.12.3` |
| 安装时间 | `2026-09-01T06:35:56Z` |

`current` 已从 `115377b` 指到 `7aaeb2b`。旧 release 目录保留，包括 `115377b`。不要删除未标记的旧 release。

### 12.2 知识库与画廊未改

安装前后下列摘要相同：

| 对象 | SHA-256 |
| --- | --- |
| `rabbit/current.json` | `c1375f3e50dd3773879fe675f506503345aa85966aa857cb6e7540a1003c5ee3` |
| `rabbit/revision-0001/knowledge-core.json` | `615a4d727295a932227300645edcc59f59e86f9bd6abaca5905c940d5989af1e` |
| `rabbit/revision-0001/manifest.json` | `de82ec8f5fbf1b3d62c3f64b54b1ceba7c5947a5abd765ed3e1f243b96091c7e` |

- library 根仍是 `/var/lib/cognitive-card-server/candidates/knowledge-library`（`cardos:cardos` `0700`）。
- 仅主题 `rabbit`；`revision-0001` current：4 `knowledge_units` / 8 `propositions` / 4 `sources`（AUTHOR-02）。
- 无格温 / Spider-Verse 路径。
- 画廊 catalog 未改：`/card-os/` 标题 `Published artifacts`，列出 `rabbit`；PDF `200`，1,728,853 bytes。

### 12.3 进程、Nginx 与抽查

- `cognitive-card-server.service` active，`Result=success`，`NRestarts=0`，`ExecMainStatus=0`。
- 监听仍是唯一 `127.0.0.1:8765`；UFW 无 8765 放行。
- Nginx snippet SHA-256 仍为 `0ed25814ed84a8b5b242f8994ca2303f04a61b83f0a5f4927c912ac58a0060a1`（WB-01）。本刀未 `systemctl reload nginx`。
- 回环与公网 `GET /card-os/api/v1/health` 均为 `200`，`server_version=0.3.1`。
- 公网 capabilities：`free_form_job_creation=false`；protocol `1..1`；minimum Skill `0.1.0`。
- SQLite `PRAGMA integrity_check` 为 `ok`。
- `/card-os/ops/` 与 `/card-os/ops/rabbit` 无 token 为 `200 text/html`，页面不含 Merck / `canonical_claim` / `src.rabbit` / `chaptered-guide` / gwen。
- `/card-os/api/v1/admin/knowledge-library` 无 token 为 `401`。
- `/card-os/jobs` 通用 `404`。
- 根分区约 `63%` / inode `22%`。

本批未签发新的生产 admin token。

### 12.4 回滚（本批）

只把应用退回 WB-01 时：将 `/opt/cognitive-card-server/current` 指回 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd` 并重启 `cognitive-card-server.service`。本批未演练该切换。不要 reload Nginx。不要删除 knowledge-library 种子或旧 release。未授权 merge server `main`。
