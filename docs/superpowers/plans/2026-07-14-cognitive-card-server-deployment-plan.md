# Cognitive Card OS Personal Server Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把已验证的 `cognitive-card-server` `0.3.0` 精确提交部署到 `www.yutou.space`，建立非 root 运行、不可变 release、HTTPS 代理、持久化、备份恢复、一次性 token 验收和可执行回滚。

**Architecture:** 治理仓库保存版本化运维工具、systemd/Nginx 配置和构建逻辑；应用制品来自私有服务仓库的精确提交 `dc043ba4473915ebbd1a98c76dab46fcba703de3`。服务器使用 `cardos` 用户、每 release 独立 venv、`current` 原子链接和回环 Uvicorn，现有 Nginx 只在 TLS server block 中包含受管 `/card-os` snippet，业务数据独立放在 `/var/lib/cognitive-card-server`。

**Tech Stack:** Ubuntu 24.04、Python 3.12、Python standard library、SQLite、systemd、Nginx 1.24、UFW、Bash、Git、SHA-256、`unittest`。

## Global Constraints

- 权威设计：`docs/superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md`。
- 治理与运维实现仓库：`/Users/admin/Documents/kids-visual-learning-pack`。
- 应用源码仓库：`/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server`。
- 应用 release 固定为版本 `0.3.0`、提交 `dc043ba4473915ebbd1a98c76dab46fcba703de3`；本批次不修改该应用提交。
- 目标服务器：`root@118.145.242.99`；正式域名：`https://www.yutou.space`。
- 应用只监听 `127.0.0.1:8765`；不得添加 UFW 8765 放行规则。
- `CARD_OS_DATABASE=/var/lib/cognitive-card-server/card-os.sqlite3`。
- `CARD_OS_CANDIDATE_ROOT=/var/lib/cognitive-card-server/candidates`。
- 数据根 `/var/lib/cognitive-card-server` 本身以及 `candidates/` 都必须是 `cardos:cardos 0700`；已有数据库只接受非 symlink 普通文件 `cardos:cardos 0600`，不得重建或修复其内容。
- release 必须携带与 lock 一一对应的 14 个 `runtime-wheels/*.whl`；受信任工作站只从官方 PyPI 以 CPython 3.12/Linux x86_64 target selectors 构建 wheelhouse，服务器以 `--no-index --find-links` 离线安装且不需要 package-index 出站访问。
- `CARD_OS_MAX_REQUEST_BYTES=29360128`；`CARD_OS_MAX_DECODED_PAYLOAD_BYTES=20971520`；Nginx `client_max_body_size 30m`。
- 现有 `/`、`/kids/`、`/sync/`、CouchDB、Docker 和其他服务不得改变行为。
- 服务器不保存 GitHub 私钥、个人访问令牌、OpenAI API Key、ChatGPT Cookie 或 ChatGPT 身份材料。
- 首批不保留长期 Card OS token；验收 token 带 15 分钟到期时间，验收结束立即撤销并删除原始 token 临时文件。
- 候选目录、数据库、环境文件和备份目录没有 Nginx 静态映射。
- release 安装不得覆盖已有同名目录；数据目录与 release 生命周期分离。
- 每个本地实现任务先写失败测试，再写最小实现；Tasks 1–3 运行各自聚焦测试，Task 4 创建总测试入口后，所有本地任务都运行 `npm run test:card-os-deploy`。
- 远程变更必须先记录漂移基线和回滚材料；任一关键门禁失败立即停止，不继续执行下一远程步骤。

---

## File Map

### 治理仓库新文件

- `ops/cognitive-card-server/card_os_backup.py`：SQLite 在线备份、候选文件快照、manifest、完整性与恢复验证、14 天保留。
- `ops/cognitive-card-server/card_os_acceptance.py`：不回显原始 token 的 begin/finish/cleanup 验收状态机。
- `ops/cognitive-card-server/build_release.py`：校验应用精确提交、构建 wheel、组装 release、写逐文件摘要和归档摘要。
- `ops/cognitive-card-server/install_release.sh`：服务器端创建身份/目录、安装精确依赖、激活 release 和 systemd 服务。
- `ops/cognitive-card-server/install_nginx_include.py`：只向目标 TLS server block 插入一次受管 include，并保留原文件备份。
- `ops/cognitive-card-server/runtime-requirements.lock`：经过测试的精确 runtime 依赖版本。
- `ops/cognitive-card-server/env/card-os.env`：非密钥生产环境配置模板。
- `ops/cognitive-card-server/systemd/cognitive-card-server.service`：回环 API 服务与 systemd hardening。
- `ops/cognitive-card-server/systemd/cognitive-card-backup.service`：只读应用数据、写备份目录的一次性备份服务。
- `ops/cognitive-card-server/systemd/cognitive-card-backup.timer`：每日备份定时器。
- `ops/cognitive-card-server/nginx/card-os.conf`：`/card-os` 重定向和 `/card-os/api/` 反向代理 snippet。
- `tests/test_card_os_backup.py`：备份成功、摘要、symlink 拒绝、失败不清理旧备份和保留策略测试。
- `tests/test_card_os_acceptance.py`：token 零回显、0600 状态文件、重启两阶段、撤销和 cleanup 测试。
- `tests/test_card_os_deployment_assets.py`：systemd、Nginx、环境文件和 Nginx include 安装器契约测试。
- `tests/test_card_os_release.py`：精确 commit、脏仓库拒绝、manifest、归档摘要和同名 release 防覆盖测试。

测试模块使用 `importlib.util.spec_from_file_location` 从上述受管路径加载独立 Python 工具；不要因为目录名含连字符而复制一份实现到测试目录。

### 治理仓库修改文件

- `package.json`：增加 `test:card-os-deploy` 和 `build:card-os-release` 命令。
- `README.md`：增加部署计划和运维入口。
- `docs/cognitive-card-os-roadmap.md`：执行开始时把 DEPLOY-01/OPS-01 置为 `IN PROGRESS`，验收完成后按证据更新。
- `docs/superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md`：把撤销后的预期状态与现有稳定 API 契约对齐为 `403 AUTH_REVOKED`。

### 服务器受管路径

- `/opt/cognitive-card-server/releases/dc043ba4473915ebbd1a98c76dab46fcba703de3/`
- `/opt/cognitive-card-server/current`
- `/var/lib/cognitive-card-server/`
- `/var/lib/cognitive-card-server/card-os.sqlite3`
- `/var/lib/cognitive-card-server/candidates/`
- `/etc/cognitive-card-server/card-os.env`
- `/etc/systemd/system/cognitive-card-server.service`
- `/etc/systemd/system/cognitive-card-backup.service`
- `/etc/systemd/system/cognitive-card-backup.timer`
- `/etc/nginx/snippets/cognitive-card-server.conf`
- `/var/backups/cognitive-card-server/`
- `/run/cognitive-card-server/acceptance.json`

| 持久化路径 | 所有者 | 模式 | 安装器处理 |
| --- | --- | --- | --- |
| `/var/lib/cognitive-card-server/` | `cardos:cardos` | `0700` | 先拒绝 symlink/非目录，再收敛目录元数据；不得删除已有内容 |
| `/var/lib/cognitive-card-server/candidates/` | `cardos:cardos` | `0700` | 数据根安全后才创建/验证；不得删除已有候选文件 |
| `/var/lib/cognitive-card-server/card-os.sqlite3` | `cardos:cardos` | `0600` | 不存在时留给应用初始化；存在时以 `lstat` 严格验证，否则失败关闭 |
| `/var/backups/cognitive-card-server/` | `root:root` | `0700` | 保持现有 root-only 备份边界 |

---

### Task 1: Add Verified Online Backup and Restore Probe

**Files:**
- Create: `ops/cognitive-card-server/card_os_backup.py`
- Create: `tests/test_card_os_backup.py`

**Interfaces:**
- Produces: `create_backup(database: Path, candidate_root: Path, backup_root: Path, current_release: Path, now: datetime, retention_days: int = 14) -> BackupResult`
- Produces: `verify_backup(backup_dir: Path) -> dict[str, object]`
- CLI: `card_os_backup.py create --database ... --candidate-root ... --backup-root ... --current-release ... --retention-days 14`
- CLI: `card_os_backup.py verify --backup-dir ...`

- [ ] **Step 1: Write failing backup tests**

Create `tests/test_card_os_backup.py` with fixtures that create a SQLite database containing one row and a candidate tree containing `packet/result.json`. Assert:

```python
result = create_backup(
    database=db,
    candidate_root=candidates,
    backup_root=backups,
    current_release=current,
    now=datetime(2026, 7, 14, 3, 0, tzinfo=timezone.utc),
)
self.assertEqual(result.backup_dir.name, "20260714T030000Z-dc043ba44739")
self.assertEqual(verify_backup(result.backup_dir)["status"], "ok")
self.assertEqual(
    sqlite3.connect(result.backup_dir / "card-os.sqlite3")
    .execute("SELECT value FROM probe")
    .fetchone()[0],
    "rabbit",
)
self.assertEqual(
    (result.backup_dir / "candidates/packet/result.json").read_text(),
    '{"ok":true}',
)
```

Also assert all of the following in separate tests:

- a symlink anywhere under candidates raises `BackupError("UNSAFE_CANDIDATE_ENTRY")`;
- a forced integrity failure leaves no final batch directory and does not delete an existing 20-day-old backup;
- after one verified new backup, verified batch directories older than 14 days are removed while unrelated files and recent batches remain;
- `manifest.json` contains `schema`, UTC timestamp, release commit, database SHA-256, sorted candidate relative paths/SHA-256/size, and no absolute source paths.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest tests.test_card_os_backup -v
```

Expected: file-load failure because `ops/cognitive-card-server/card_os_backup.py` does not exist; the failure must come from the missing implementation rather than a test syntax error.

- [ ] **Step 3: Implement the backup state machine**

Implement these exact types and invariants:

```python
@dataclass(frozen=True)
class BackupResult:
    backup_dir: Path
    manifest_path: Path


class BackupError(RuntimeError):
    pass
```

`create_backup` must:

1. resolve and validate all four input paths;
2. derive the release ID from `current_release.resolve().name`, require 40 lowercase hexadecimal characters, and use its first 12 characters in the batch directory name;
3. create a hidden staging directory by concatenating `.`, the computed batch ID, and `.staging`; set mode `0700` and fail if the staging or final path exists;
4. open the source SQLite URI with `mode=ro`, call `source.backup(destination)`, close both connections, then require `PRAGMA integrity_check` to return exactly `ok`;
5. walk candidates in sorted relative-path order using `os.scandir`, reject symlinks and non-regular files, copy each file with `shutil.copyfile`, set copied files to `0600`, and hash copied bytes rather than trusting source metadata;
6. write canonical UTF-8 JSON with `sort_keys=True`, `separators=(",", ":")`, a final newline, and mode `0600`;
7. call `verify_backup` against the staging directory;
8. atomically rename staging to final;
9. delete only directories whose names match regular expression `^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}$`, whose manifest verifies, and whose timestamp is older than `now - retention_days`;
10. print only canonical JSON containing `status`, `backup_dir`, `manifest_sha256`, and `release_id`.

`verify_backup` must recalculate every declared digest, reject undeclared files, run SQLite `PRAGMA integrity_check`, and open the restored database read-only. It returns `{"status": "ok", "release_id": ..., "file_count": ...}` and never mutates the batch.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
python3 -m unittest tests.test_card_os_backup -v
```

Expected: backup tests pass. Commit only the Task 1 files:

```bash
git add ops/cognitive-card-server/card_os_backup.py tests/test_card_os_backup.py
git commit -m "feat(ops): add verified Card OS backups"
```

---

### Task 2: Add Zero-Disclosure One-Time Token Acceptance

**Files:**
- Create: `ops/cognitive-card-server/card_os_acceptance.py`
- Create: `tests/test_card_os_acceptance.py`

**Interfaces:**
- CLI begin: `card_os_acceptance.py begin --database PATH --base-url URL --state-file PATH --auth-command PATH --expires-minutes 15`
- CLI finish: `card_os_acceptance.py finish --database PATH --base-url URL --state-file PATH --auth-command PATH`
- CLI cleanup: `card_os_acceptance.py cleanup --database PATH --state-file PATH --auth-command PATH`
- `begin` creates a `0600` JSON state file containing raw token and token ID but prints only safe metadata.
- `finish` validates the token after service restart, revokes it, confirms `403 AUTH_REVOKED`, and unlinks state.
- `cleanup` revokes by token ID and unlinks state after an interrupted acceptance run.

- [ ] **Step 1: Write failing acceptance tests**

Create a fake auth runner that returns this captured JSON from the issue command without writing it to test stdout:

```python
ISSUED = {
    "token": "ccos_v1." + "a" * 32 + ".rabbit-secret",
    "token_id": "a" * 32,
    "subject": "deploy-acceptance-20260714T030000Z",
    "scopes": ["admin"],
    "expires_at": "2026-07-14T03:15:00Z",
}
```

Assert:

- `begin` calls `GET https://www.yutou.space/card-os/api/v1/jobs/deploy-acceptance-missing` with Bearer token, `X-Card-OS-Protocol: 1`, and `X-Card-OS-Skill-Release: 0.1.0` in the production invocation; tests use an injected fixture base URL;
- the first response must be `404` with error code `JOB_NOT_FOUND`;
- state mode is exactly `0600`, the parent mode is `0700`, and stdout/stderr do not contain `rabbit-secret` or the raw token;
- a second `begin` refuses to overwrite an existing state file;
- `finish` first observes the same authenticated 404, invokes revoke with token ID only, then requires `403` and `AUTH_REVOKED` from the same request;
- `finish` and `cleanup` delete state only after revoke succeeds;
- cleanup never passes the raw token on a subprocess argument and never prints it.

- [ ] **Step 2: Run the focused test and verify RED**

```bash
python3 -m unittest tests.test_card_os_acceptance -v
```

Expected: import failure because the acceptance module does not exist.

- [ ] **Step 3: Implement the three-phase CLI**

Use `subprocess.run(..., capture_output=True, text=True, check=False)` for `cognitive-card-auth`; parse the issue JSON in memory. Use `urllib.request.Request` for HTTP so the token remains an in-process header and is never a process argument. Use these constants exactly:

```python
PROTOCOL = "1"
SKILL_RELEASE = "0.1.0"
MISSING_JOB = "deploy-acceptance-missing"
SUBJECT_PREFIX = "deploy-acceptance-"
```

Create the state file with:

```python
descriptor = os.open(
    state_file,
    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
    0o600,
)
```

The state payload is canonical JSON containing exactly `schema`, `token`, `token_id`, `subject`, `expires_at`, and `base_url`. Safe CLI output may contain only `status`, `phase`, `token_id`, `subject`, and HTTP status. Never catch an exception by printing its raw text because `urllib` or subprocess messages may include arguments or headers; map failures to stable codes such as `ISSUE_FAILED`, `AUTHENTICATED_READ_FAILED`, `REVOKE_FAILED`, and `REVOCATION_NOT_ENFORCED`.

`finish` uses `try/finally`: once the state has been parsed, it always attempts revoke; it removes the state file only when revoke succeeds. The post-revoke request must receive `403` with `error.code == "AUTH_REVOKED"`. `cleanup` skips HTTP checks, revokes by `token_id`, and removes the state file.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_acceptance -v
git add ops/cognitive-card-server/card_os_acceptance.py tests/test_card_os_acceptance.py
git commit -m "feat(ops): add one-time deployment acceptance"
```

---

### Task 3: Add Hardened systemd and Nginx Assets

**Files:**
- Create: `ops/cognitive-card-server/env/card-os.env`
- Create: `ops/cognitive-card-server/systemd/cognitive-card-server.service`
- Create: `ops/cognitive-card-server/systemd/cognitive-card-backup.service`
- Create: `ops/cognitive-card-server/systemd/cognitive-card-backup.timer`
- Create: `ops/cognitive-card-server/nginx/card-os.conf`
- Create: `ops/cognitive-card-server/install_nginx_include.py`
- Create: `tests/test_card_os_deployment_assets.py`

**Interfaces:**
- Nginx installer: `install_nginx_include.py --site-file PATH --include-line "include /etc/nginx/snippets/cognitive-card-server.conf;" --backup-dir PATH`
- It selects exactly one TLS server block containing both `listen 443 ssl` and `server_name yutou.space www.yutou.space`, inserts the include once, writes atomically, and emits the backup path.

- [ ] **Step 1: Write failing asset contract tests**

Assert the API unit contains every required directive, places both `StartLimit` directives in `[Unit]`, contains `RuntimeDirectoryPreserve=restart`, keeps both `CapabilityBoundingSet=` and `AmbientCapabilities=` empty, and contains none of `0.0.0.0`, `root@`, `Authorization`, or a token-shaped `ccos_v1.` string. Assert the backup unit is root-run, has read-only access to `/var/lib/cognitive-card-server`, has write access only to `/var/backups/cognitive-card-server` plus its private temporary directory, and sets both `CapabilityBoundingSet` and `AmbientCapabilities` to exactly `CAP_DAC_READ_SEARCH` with no additional capabilities. Assert the Nginx snippet:

```python
self.assertIn("location = /card-os", nginx)
self.assertIn("return 308 /card-os/", nginx)
self.assertIn("location = /card-os/", nginx)
self.assertIn("return 307 /card-os/api/v1/capabilities", nginx)
self.assertIn("location ^~ /card-os/api/", nginx)
self.assertIn("proxy_pass http://127.0.0.1:8765;", nginx)
self.assertIn("client_max_body_size 30m", nginx)
self.assertIn("access_log off", nginx)
self.assertNotIn("/var/lib/cognitive-card-server/candidates", nginx)
```

Use an Nginx fixture containing separate port 80 and port 443 server blocks. Assert `install_nginx_include.py` modifies only the TLS block, creates one byte-identical backup, is idempotent, and fails without writing if zero or two TLS blocks match.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_deployment_assets -v
```

Expected: missing asset failures.

- [ ] **Step 3: Create the production environment file**

Write exactly:

```dotenv
CARD_OS_DATABASE=/var/lib/cognitive-card-server/card-os.sqlite3
CARD_OS_CANDIDATE_ROOT=/var/lib/cognitive-card-server/candidates
CARD_OS_HOST=127.0.0.1
CARD_OS_PORT=8765
CARD_OS_MAX_REQUEST_BYTES=29360128
CARD_OS_MAX_DECODED_PAYLOAD_BYTES=20971520
```

No token or external service credential belongs in this file.

- [ ] **Step 4: Create the API systemd unit**

Use this complete unit:

```ini
[Unit]
Description=Cognitive Card OS API
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60s
StartLimitBurst=5

[Service]
Type=simple
User=cardos
Group=cardos
UMask=0077
WorkingDirectory=/opt/cognitive-card-server/current
EnvironmentFile=/etc/cognitive-card-server/card-os.env
ExecStartPre=/usr/bin/test -d /var/lib/cognitive-card-server/candidates
ExecStart=/opt/cognitive-card-server/current/.venv/bin/cognitive-card-api
Restart=on-failure
RestartSec=5s
RuntimeDirectory=cognitive-card-server
RuntimeDirectoryMode=0700
RuntimeDirectoryPreserve=restart
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/cognitive-card-server /run/cognitive-card-server
CapabilityBoundingSet=
AmbientCapabilities=
RestrictAddressFamilies=AF_INET AF_INET6
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 5: Create backup service and timer**

`cognitive-card-backup.service`:

```ini
[Unit]
Description=Verified Cognitive Card OS backup
After=cognitive-card-server.service

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/bin/python3 /opt/cognitive-card-server/current/ops/card_os_backup.py create --database /var/lib/cognitive-card-server/card-os.sqlite3 --candidate-root /var/lib/cognitive-card-server/candidates --backup-root /var/backups/cognitive-card-server --current-release /opt/cognitive-card-server/current --retention-days 14
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/var/lib/cognitive-card-server
ReadWritePaths=/var/backups/cognitive-card-server
CapabilityBoundingSet=CAP_DAC_READ_SEARCH
AmbientCapabilities=CAP_DAC_READ_SEARCH

[Install]
WantedBy=multi-user.target
```

`cognitive-card-backup.timer`:

```ini
[Unit]
Description=Daily verified Cognitive Card OS backup

[Timer]
OnCalendar=*-*-* 03:20:00 Asia/Shanghai
Persistent=true
RandomizedDelaySec=10m
Unit=cognitive-card-backup.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 6: Create the Nginx snippet and safe include installer**

Write the snippet:

```nginx
location = /card-os {
    return 308 /card-os/;
}

location = /card-os/ {
    return 307 /card-os/api/v1/capabilities;
}

location ^~ /card-os/api/ {
    access_log off;
    client_max_body_size 30m;
    proxy_connect_timeout 5s;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

The Python installer must tokenize braces after stripping `#` comments, find complete top-level `server { ... }` spans, select the unique span containing both required TLS/server-name strings, and insert the include immediately after the matching `server_name` line. Before the atomic replacement, write a name such as `yutou-space.20260714T030000Z.conf`, using the actual current UTC timestamp, under the supplied backup directory with mode `0600`. If the include already exists exactly once in the selected block, return `status=unchanged` without a second backup.

- [ ] **Step 7: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_deployment_assets -v
git add ops/cognitive-card-server/env ops/cognitive-card-server/systemd ops/cognitive-card-server/nginx ops/cognitive-card-server/install_nginx_include.py tests/test_card_os_deployment_assets.py
git commit -m "feat(ops): add hardened Card OS service assets"
```

---

### Task 4: Build and Install an Immutable Release

**Files:**
- Create: `ops/cognitive-card-server/runtime-requirements.lock`
- Create: `ops/cognitive-card-server/build_release.py`
- Create: `ops/cognitive-card-server/install_release.sh`
- Create: `tests/test_card_os_release.py`
- Modify: `package.json`

**Interfaces:**
- Builder: `build_release.py --server-repo PATH --expected-commit 40HEX --output-dir PATH --python PATH`
- Output: `cognitive-card-server-dc043ba4473915ebbd1a98c76dab46fcba703de3.tar.gz`, matching `.sha256`, and safe summary JSON for this batch.
- Installer: `install_release.sh ARCHIVE SHA256_FILE`; it never overwrites an existing release directory.

- [ ] **Step 1: Commit the exact runtime lock**

Add the aggregate test entry to `package.json`:

```json
"test:card-os-deploy": "python3 -m unittest tests.test_card_os_backup tests.test_card_os_acceptance tests.test_card_os_deployment_assets tests.test_card_os_release -v",
"build:card-os-release": "python3 ops/cognitive-card-server/build_release.py"
```

Write exactly these runtime packages, excluding test-only HTTPX and the application wheel:

```text
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.14.2
click==8.4.2
fastapi==0.139.0
h11==0.16.0
idna==3.18
pillow==12.3.0
pydantic==2.13.4
pydantic_core==2.46.4
starlette==1.3.1
typing_extensions==4.16.0
typing-inspection==0.4.2
uvicorn==0.51.0
```

- [ ] **Step 2: Write failing builder and installer tests**

Tests must prove:

- wrong HEAD returns `SOURCE_COMMIT_MISMATCH` before invoking wheel build;
- non-empty `git status --porcelain` returns `SOURCE_WORKTREE_DIRTY`;
- the builder resolves exactly the 14 locked runtime distributions as wheels from official PyPI with isolated CPython 3.12, x86_64, `manylinux_2_28`/`manylinux_2_17`, wheel-only selectors; missing, duplicate, unexpected, wrong-version, sdist, unsafe-name, or incompatible output fails closed;
- one governed `ops/wheel_audit.py`, used by both builder and installer, validates the application wheel and all runtime wheels: bounded regular ZIP entries, safe unique paths, exact `.dist-info`, METADATA Name/Version, expanded WHEEL tags against the bounded CPython 3.12/Linux x86_64 policy, and complete RECORD hashes/sizes; structurally corrupt, mislabeled, unsafe, duplicate, symlink-mode, future-manylinux, invalid-abi3-floor, and RECORD mismatch fixtures fail closed;
- the archive contains exactly one application wheel, the closed `runtime-wheels/*.whl` subtree, runtime lock, the governed wheel audit, backup/acceptance scripts, env, three systemd files, Nginx snippet, include installer, and `release-manifest.json`;
- manifest uses the incompatible-format bump `cognitive-card-server-release-v2` and contains full application commit, full governance operations commit, application version `0.3.0`, Python version, exact target runtime metadata, build timestamp, lock SHA-256, wheel SHA-256, and sorted SHA-256/size for every payload file;
- archive path traversal members are impossible because all names are generated from a closed allowlist;
- `install_release.sh` passes `bash -n`, verifies archive digest before extraction, rejects an existing release, creates `.venv`, installs the lock before the app wheel with `--no-deps`, runs `pip check`, verifies and persists installed freeze, writes a server-side install manifest containing the archive digest, and atomically switches `current` only after all checks pass.

- [ ] **Step 3: Verify RED**

```bash
python3 -m unittest tests.test_card_os_release -v
```

Expected: missing builder/installer failures.

- [ ] **Step 4: Implement the builder**

The builder must execute these checks in order:

```python
head = git("rev-parse", "HEAD")
if head != expected_commit:
    raise ReleaseError("SOURCE_COMMIT_MISMATCH")
if git("status", "--porcelain"):
    raise ReleaseError("SOURCE_WORKTREE_DIRTY")
```

Resolve the governance repository from the builder file location, require `git status --porcelain --untracked-files=no` to be empty, and record `git rev-parse HEAD` as `operations_commit`; this intentionally ignores the known user-owned untracked `outputs/` while rejecting every tracked operations change. First remove inherited pip source variables, force `PIP_CONFIG_FILE=/dev/null`, and run the equivalent of:

```bash
"$PYTHON" -m pip --isolated --disable-pip-version-check download --no-input \
  --only-binary=:all: --index-url https://pypi.org/simple \
  --platform manylinux_2_28_x86_64 --platform manylinux_2_17_x86_64 \
  --implementation cp --python-version 312 --abi cp312 \
  --dest "$STAGING/runtime-wheels" --requirement runtime-requirements.lock
```

Require exactly one compatible wheel for each lock entry and no other entry. Run every downloaded wheel through the governed structural/content/tag audit. Then build the application wheel from the isolated exact-commit source snapshot as:

```bash
"$PYTHON" -m pip wheel --no-deps --wheel-dir "$STAGING/wheel" "$SERVER_REPO"
```

Require one wheel named `cognitive_card_server-0.3.0-*.whl` and pass it through the same governed audit. Copy the closed allowlist, including `ops/wheel_audit.py`, into the `release` child of the staging directory, calculate SHA-256 from final copied bytes, write canonical `release-manifest.json`, create the tarball with normalized uid/gid/mtime/mode, and write a `.sha256` line containing the calculated lowercase digest, two spaces, and the archive basename. Stdout is safe JSON and never contains environment variables.

- [ ] **Step 5: Implement the root installer**

`install_release.sh` must use `set -euo pipefail` and perform these operations in order:

```bash
sha256sum --check "$SHA256_FILE"
apt-get update
apt-get install -y python3-venv sqlite3
id cardos >/dev/null 2>&1 || useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin cardos
install -d -o root -g root -m 0755 /opt/cognitive-card-server/releases
open-trusted-parent-fd /var/lib
openat-or-mkdirat-no-follow cognitive-card-server; fchown-and-fchmod-fd cardos cardos 0700
openat-or-mkdirat-no-follow candidates; fchown-and-fchmod-fd cardos cardos 0700
validate-existing-db-relative-to-data-fd card-os.sqlite3 cardos cardos 0600
fork-drop-to-cardos-and-run-unpredictable-exclusive-private-write-probe-relative-to-data-fd
verify-root-candidate-and-database-device-inode-bindings
install -d -o root -g cardos -m 0750 /etc/cognitive-card-server
install -d -o root -g root -m 0700 /var/backups/cognitive-card-server
```

Before extraction, inspect every tar member with Python and reject absolute paths, `..`, symlinks, hardlinks, devices and any name outside the fixed assets, the governed wheel audit, one application wheel, and the closed `runtime-wheels/*.whl` subtree. Extract into a root-owned temporary directory and verify the canonical manifest plus every payload size/digest. Only after that digest binding succeeds, execute that manifest-bound `ops/wheel_audit.py` against both the application wheel and complete runtime wheelhouse. Parse the release ID from the manifest, require it to equal the 40-hex application commit, and fail if `/opt/cognitive-card-server/releases/$RELEASE_ID` exists. Move payload into that release, create `.venv`, install the lock with pip isolated `--no-index --find-links "$RELEASE_DIR/runtime-wheels"`, install the local application wheel with isolated `--no-index --no-deps`, run `pip check`, and compare normalized `pip freeze` runtime lines with the committed lock. Force `PIP_CONFIG_FILE=/dev/null` and remove inherited `PIP_INDEX_URL`/`PIP_EXTRA_INDEX_URL`; an executable real-pip regression with hostile config and `find-links` proves that no server config or mirror can supplement the governed source. Persist normalized freeze as `installed-runtime.txt`; write canonical `install-manifest.json` containing schema, application commit, operations commit, archive SHA-256, server Python version, installed-runtime SHA-256 and UTC install time. Set both files `root:root 0644` before activation. Install `card-os.env` as `root:cardos 0640` only if absent; otherwise compare its non-secret keys and stop on mismatch. Install systemd units as `root:root 0644`, call `systemctl daemon-reload`, atomically switch `current` using a temporary symlink plus `mv -T`, enable/start the API, and enable the timer. Do not install or edit Nginx in this script.

- [ ] **Step 6: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_release -v
npm run test:card-os-deploy
bash -n ops/cognitive-card-server/install_release.sh
git add package.json ops/cognitive-card-server/runtime-requirements.lock ops/cognitive-card-server/build_release.py ops/cognitive-card-server/install_release.sh ops/cognitive-card-server/wheel_audit.py tests/test_card_os_release.py
git commit -m "feat(ops): build immutable Card OS releases"
```

Expected: all four deployment test modules pass.

---

### Task 5: Build and Verify the Exact 0.3.0 Release Locally

**Files:**
- Generated, ignored: `dist/card-os-release/cognitive-card-server-dc043ba4473915ebbd1a98c76dab46fcba703de3.tar.gz`
- Generated, ignored: matching `.sha256`
- Modify: `README.md`
- Modify: `docs/cognitive-card-os-roadmap.md`

- [ ] **Step 1: Mark the implementation batch active**

Change DEPLOY-01 and OPS-01 from `READY` to `IN PROGRESS`. Add the implementation-plan link to README and the roadmap task detail. Do not mark either task done.

Commit this state before building so the release can record a clean, reachable governance operations commit:

```bash
git add README.md docs/cognitive-card-os-roadmap.md
git commit -m "docs(deploy): start Card OS deployment batch"
```

- [ ] **Step 2: Re-run the application suite at the exact source commit**

```bash
git -C /Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server rev-parse HEAD
git -C /Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server status --porcelain
/Users/admin/Documents/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-v03/.venv/bin/python -m unittest discover -s /Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server/tests -v
```

Expected: exact commit `dc043ba4473915ebbd1a98c76dab46fcba703de3`, empty status, 273 passing tests.

- [ ] **Step 3: Verify, integrate, and push the reviewed operations source**

```bash
npm run test:card-os-deploy
git diff --check
git status --short
```

Expected: deployment tests pass; tracked worktree is clean; only the user-owned `outputs/` remains untracked. Run the branch completion workflow, merge the reviewed task commits into governance `main` without squashing away their source identities, push `main`, and verify local `main` equals `origin/main`.

- [ ] **Step 4: Build the release from clean governance main**

```bash
python3 ops/cognitive-card-server/build_release.py \
  --server-repo /Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server \
  --expected-commit dc043ba4473915ebbd1a98c76dab46fcba703de3 \
  --output-dir dist/card-os-release \
  --python /Users/admin/Documents/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-v03/.venv/bin/python
```

Expected: safe JSON with `status=ok`, full application commit, full governance operations commit, archive path, and archive SHA-256.

- [ ] **Step 5: Verify the release in a clean temporary venv**

```bash
python3 -m venv /tmp/card-os-release-verify
mkdir -p dist/card-os-release/unpacked
tar -xzf dist/card-os-release/cognitive-card-server-dc043ba4473915ebbd1a98c76dab46fcba703de3.tar.gz -C dist/card-os-release/unpacked
/tmp/card-os-release-verify/bin/python -m pip --isolated install --no-index --find-links dist/card-os-release/unpacked/runtime-wheels -r ops/cognitive-card-server/runtime-requirements.lock
/tmp/card-os-release-verify/bin/python -m pip --isolated install --no-index --no-deps dist/card-os-release/unpacked/cognitive_card_server-0.3.0-py3-none-any.whl
/tmp/card-os-release-verify/bin/python -m pip check
CARD_OS_DATABASE=/tmp/card-os-release-verify.sqlite3 CARD_OS_CANDIDATE_ROOT=/tmp/card-os-release-candidates /tmp/card-os-release-verify/bin/cognitive-card-api --help
```

Expected: `pip check` reports no broken requirements and the API help exits zero without starting a server. Remove only these `/tmp/card-os-release-*` paths after verification.

---

### Task 6: Run Server Drift Gate and Install the Loopback Service

**Files:**
- Remote create: `/opt/cognitive-card-server/releases/dc043ba4473915ebbd1a98c76dab46fcba703de3/`
- Remote create: `/etc/cognitive-card-server/card-os.env`
- Remote create: three `/etc/systemd/system/cognitive-card-*.{service,timer}` files
- Remote create: `/var/lib/cognitive-card-server/`
- Remote create: `/var/backups/cognitive-card-server/`

- [ ] **Step 1: Re-audit non-mutating baseline**

Run read-only commands over SSH for OS, disk/inodes, memory, `ss -lntup`, UFW status, enabled Nginx sites, `nginx -T`, domain certificate dates, Certbot timer, existing `/`, `/kids/`, `/sync/`, and current `/card-os/api/v1/health`. Save sanitized output locally under ignored `dist/card-os-release/audit-before.txt`.

Required gate:

- root disk usage below 75%;
- 8765 not publicly listening and not allowed by UFW;
- `/`, `/kids/`, `/sync/` return their established success behavior;
- target DNS still resolves to `118.145.242.99`;
- domain certificate is valid at deployment time;
- existing Nginx configuration passes `nginx -t`;
- the TLS site file and target TLS server block can be selected uniquely by `install_nginx_include.py`.
- the local release manifest binds exactly the 14 locked runtime wheels and target metadata, and a clean CPython 3.12 venv resolves the complete lock with `--no-index --find-links` only; no server package index or mirror is required.

Stop without mutations if any requirement fails.

- [ ] **Step 2: Upload only the release, digest, and installer**

```bash
scp dist/card-os-release/cognitive-card-server-dc043ba4473915ebbd1a98c76dab46fcba703de3.tar.gz root@118.145.242.99:/tmp/
scp dist/card-os-release/cognitive-card-server-dc043ba4473915ebbd1a98c76dab46fcba703de3.tar.gz.sha256 root@118.145.242.99:/tmp/
scp ops/cognitive-card-server/install_release.sh root@118.145.242.99:/tmp/install-card-os-release.sh
```

Expected: uploaded archive digest matches the local digest when checked on the server.

- [ ] **Step 3: Run the installer and verify loopback only**

Run the installer as root with archive and digest paths. Then verify:

```bash
systemd-analyze verify /etc/systemd/system/cognitive-card-server.service /etc/systemd/system/cognitive-card-backup.service /etc/systemd/system/cognitive-card-backup.timer
systemctl is-active cognitive-card-server
systemctl is-enabled cognitive-card-server
systemctl is-enabled cognitive-card-backup.timer
ss -lntp | grep '127.0.0.1:8765'
curl --fail-with-body --silent --show-error http://127.0.0.1:8765/card-os/api/v1/health
curl --fail-with-body --silent --show-error http://127.0.0.1:8765/card-os/api/v1/capabilities
```

Expected: service is active/enabled, timer enabled, exactly loopback listener, health reports `0.3.0`, and capabilities report protocol 1. Confirm `ufw status` still has no 8765 rule.

- [ ] **Step 4: Verify service hardening and persistence permissions**

```bash
systemd-analyze security cognitive-card-server.service
namei -l /var/lib/cognitive-card-server
namei -l /var/lib/cognitive-card-server/card-os.sqlite3
namei -l /var/lib/cognitive-card-server/candidates
readlink -f /opt/cognitive-card-server/current
journalctl -u cognitive-card-server --since '10 minutes ago' --no-pager
```

Expected: current resolves to the exact commit; database/candidates are owned by `cardos`; logs contain no `Authorization`, `ccos_v1.`, token secret, traceback, or unexpected restart loop.

---

### Task 7: Activate HTTPS, Exercise Backup/Restore, and Revoke Acceptance Token

**Files:**
- Remote create: `/etc/nginx/snippets/cognitive-card-server.conf`
- Remote modify: canonical `yutou-space` TLS site file, after timestamped backup
- Remote transient: `/run/cognitive-card-server/acceptance.json`

- [ ] **Step 1: Install the Nginx snippet without reload**

Copy the snippet and include installer from the active release into their server locations. Run the include installer against `readlink -f /etc/nginx/sites-enabled/yutou-space` with backup directory `/var/backups/cognitive-card-server/nginx`. Require a safe JSON result with exactly one backup or `status=unchanged`.

- [ ] **Step 2: Validate Nginx and reload atomically**

```bash
nginx -t
systemctl reload nginx
systemctl is-active nginx
```

If `nginx -t` fails, do not reload. If reload or regression fails, restore the timestamped site file, run `nginx -t`, and reload the restored configuration.

- [ ] **Step 3: Verify public and protected namespace boundaries**

From an external client, check:

```bash
curl --silent --show-error --head https://www.yutou.space/card-os
curl --silent --show-error --head https://www.yutou.space/card-os/
curl --fail-with-body --silent --show-error https://www.yutou.space/card-os/api/v1/health
curl --fail-with-body --silent --show-error https://www.yutou.space/card-os/api/v1/capabilities
```

Expected: `308`, `307`, then JSON health/capabilities over the valid domain certificate. Probe guessed URLs for `card-os.sqlite3`, `candidates/`, `card-os.env`, and backups; every probe must be non-success and must not return file content.

- [ ] **Step 4: Begin the zero-disclosure token acceptance**

Run as `cardos` without shell tracing:

```bash
runuser -u cardos -- /usr/bin/python3 /opt/cognitive-card-server/current/ops/card_os_acceptance.py begin \
  --database /var/lib/cognitive-card-server/card-os.sqlite3 \
  --base-url https://www.yutou.space \
  --state-file /run/cognitive-card-server/acceptance.json \
  --auth-command /opt/cognitive-card-server/current/.venv/bin/cognitive-card-auth \
  --expires-minutes 15
```

Expected: safe metadata reports authenticated 404; terminal and journal contain no raw token. Confirm the state file is `cardos:cardos 0600` without reading its contents.

- [ ] **Step 5: Restart and finish acceptance**

```bash
systemctl restart cognitive-card-server
systemctl is-active cognitive-card-server
runuser -u cardos -- /usr/bin/python3 /opt/cognitive-card-server/current/ops/card_os_acceptance.py finish \
  --database /var/lib/cognitive-card-server/card-os.sqlite3 \
  --base-url https://www.yutou.space \
  --state-file /run/cognitive-card-server/acceptance.json \
  --auth-command /opt/cognitive-card-server/current/.venv/bin/cognitive-card-auth
```

Expected: token authenticates after restart, revoke succeeds, repeated request returns `403 AUTH_REVOKED`, and state file no longer exists. Query safe token metadata with `cognitive-card-auth list` and confirm the acceptance subject has `revoked_at` populated. If finish is interrupted, run the cleanup subcommand before any other deployment action.

- [ ] **Step 6: Trigger and verify backup/restore**

```bash
systemctl start cognitive-card-backup.service
systemctl show cognitive-card-backup.service -p Result --value
systemctl list-timers cognitive-card-backup.timer --no-pager
```

Expected: service result is `success`; timer shows a next run. Run `card_os_backup.py verify` against the newly created batch, copy the batch database into a private temporary restore directory, open it read-only, and compare its integrity result and safe table counts with the live database. Delete only the temporary restore directory after verification.

- [ ] **Step 7: Run regression and rollback drill**

Recheck `/`, `/kids/`, `/sync/`, Card OS health/capabilities, loopback-only binding, UFW, Nginx config, service/timer status, disk use and recent logs. For the configuration rollback drill, verify the timestamped Nginx backup SHA-256 equals the pre-change site SHA-256, run `nginx -t` against the current configuration, and record the exact `install`、`nginx -t`、`systemctl reload nginx` restore sequence without replacing the successful live configuration. Record the commands that stop/disable the first Card OS service and timer because there is no previous Card OS release.

---

### Task 8: Record Evidence, Close the Deployment Slice, and Push

**Files:**
- Create: `docs/operations/cognitive-card-server-deployment-2026-07-14.md`
- Modify: `README.md`
- Modify: `docs/cognitive-card-os-roadmap.md`

- [ ] **Step 1: Write a sanitized deployment record**

Record:

- application commit, governance operations commit and archive SHA-256;
- server install-manifest SHA-256, Python version and installed-runtime SHA-256;
- server OS/Python/Nginx versions and post-deploy disk use;
- service/timer state and loopback binding;
- public endpoint status and capability version;
- Nginx backup filename and rollback commands;
- backup batch ID, manifest SHA-256, integrity/restore result and next timer time;
- acceptance token ID only, issued subject, expiry, revoked timestamp, authenticated-before/rejected-after results;
- `/`、`/kids/`、`/sync/` regression results;
- IP-certificate expiry warning as an independent OPS item.

Do not record raw token, environment dump, Authorization header, candidate content, database content, SSH private material, or GitHub credential.

- [ ] **Step 2: Update roadmap status from evidence**

Set `DEPLOY-01` to `DONE` only if every Task 6–7 gate passed. Keep `API-01` and `AUTH-01` `IN PROGRESS` because free-form compilation, browser session, formal rotation and long-lived client installation remain outside this slice. Set `OPS-01` to `IN PROGRESS`: local verified backup is complete, while off-server copy, automated capacity alerting and certificate/health alert delivery remain unfinished.

- [ ] **Step 3: Run final verification**

```bash
npm run test:card-os-deploy
git diff --check
git status --short
```

Expected: all deployment tests pass; no whitespace errors; only intentional documentation changes plus the user-owned untracked `outputs/` are present.

- [ ] **Step 4: Commit and push governance evidence**

```bash
git add README.md docs/cognitive-card-os-roadmap.md docs/operations/cognitive-card-server-deployment-2026-07-14.md
git commit -m "docs(ops): record Card OS production deployment"
git push origin main
```

After push, verify local `main`, remote `origin/main`, the deployment record commit, and the server release manifest all identify the expected governed sources. Do not delete release or backup directories during closeout.

---

## Rollback Stop Conditions

Stop the batch and execute the applicable rollback when any of these occurs:

- server drift invalidates the audited Nginx site, domain, disk or port assumptions;
- archive digest, release manifest, exact application commit or dependency lock does not match;
- service binds anything except `127.0.0.1:8765`;
- Nginx syntax fails or `/`、`/kids/`、`/sync/` regress;
- health/capabilities do not report application `0.3.0` and protocol 1;
- token secret appears in terminal, journald, Nginx logs or deployment record;
- token remains usable after revoke, or acceptance state remains after finish/cleanup;
- database/candidate ownership changes away from `cardos`;
- backup integrity, manifest verification or restore probe fails.

First-deployment rollback is: restore the timestamped Nginx site file, validate and reload Nginx, stop/disable `cognitive-card-server.service` and `cognitive-card-backup.timer`, leave `/var/lib/cognitive-card-server` and `/var/backups/cognitive-card-server` intact, and record the failed release. Future release rollback may repoint `current` only when its release manifest declares database compatibility.
