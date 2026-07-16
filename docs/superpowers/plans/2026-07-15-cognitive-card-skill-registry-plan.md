# Cognitive Card OS Immutable Skill Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to execute this plan task-by-task. Every implementation task requires a fresh implementer, a task reviewer, recorded RED/GREEN evidence, and a final whole-branch review.

**Goal:** 建立可重复构建、公开只读、不可变、可校验且可回滚的 Cognitive Card OS Skill 发行基础设施，但在完整薄客户端产生前不激活占位生产 stable。

**Architecture:** 私有治理仓保存 Skill 源码和构建规则；Python 标准库构建器从精确 Git 提交生成确定性 ZIP、`release.json` 和 `sha256.txt`，不生成依赖发布时刻与 installer 的 channel manifest；跨平台安装器先验证再原子安装；root 发布器写入 immutable installer/release，并在激活时组合规范 manifest，Nginx 仅公开 `GET`/`HEAD`。本计划用隔离临时发行根和 fixture release 完成发布/回滚门禁，生产 `manifest.json` 留给 SKILL-02 的完整 `0.1.0` 首次激活。

**Tech Stack:** Python 3.11+ standard library、Bash/POSIX shell、Git、SHA-256、ZIP_STORED、Nginx、`unittest`、macOS/Linux。

## Global Constraints

- 权威设计：`docs/superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md`。
- 工作分支：`codex/card-os-thin-skill-v1`；工作树：`.worktrees/card-os-thin-skill-v1`。
- 当前完整本机 Skill `/Users/admin/.codex/skills/cognitive-card-os` 只读且不得覆盖。
- 用户资产目录 `outputs/` 不读取、不修改、不暂存。
- 生产入口固定为 `https://www.yutou.space/card-os/skill/v1/`；发行根固定为 `/var/www/cognitive-card-skill-registry/v1/`。
- 本计划不得创建或激活不完整的生产 `manifest.json`，也不得把 fixture 放入生产发行根。
- 目标薄 Skill 版本 `0.1.0`、协议 `1`、最低服务端版本 `0.3.1`；它由 SKILL-02 完成并首次激活。
- 构建输入只允许精确 Git commit 中 `skills/cognitive-card-os/` 的声明普通文件；工作树漂移、符号链接、未声明文件和凭据形状文件全部失败关闭。
- ZIP 使用 `ZIP_STORED`、确定顺序/模式/时间戳，构建后必须从归档重新验证闭合集。
- installer 禁止 `curl | sh`，拒绝重定向、非 HTTPS、非固定 host、路径穿越、链接、设备、重复路径和摘要漂移。
- publisher 先发布 immutable 对象，最后才原子替换 active pointer；任何失败不改变既有 stable 或 installer bootstrap。
- 每个任务严格遵循 RED -> 最小 GREEN -> 聚焦测试 -> task review -> commit；不得把多个任务揉成一个提交。
- `.superpowers/sdd/` 是忽略的执行账本；不得把 token、服务器私有路径内容或用户资产写入账本。

## Product File Map

- Create: `skills/cognitive-card-os/SKILL.md`
- Create: `skills/cognitive-card-os/agents/openai.yaml`
- Create: `skills/cognitive-card-os/scripts/card_os_client.py`
- Create: `skills/cognitive-card-os/references/protocol.md`
- Create: `skills/cognitive-card-os/references/errors.md`
- Create: `ops/cognitive-card-skill/build_release.py`
- Create: `ops/cognitive-card-skill/install.sh`
- Create: `ops/cognitive-card-skill/publish_release.py`
- Create: `tests/test_card_os_skill_release.py`
- Create: `tests/test_card_os_skill_installer.py`
- Create: `tests/test_card_os_skill_publisher.py`
- Modify: `ops/cognitive-card-server/nginx/card-os.conf`
- Modify: `tests/test_card_os_deployment_assets.py`
- Modify: `package.json`
- Modify: `docs/cognitive-card-os-roadmap.md`

## Test Entry Points

```bash
python3 -m unittest tests.test_card_os_skill_release -v
python3 -m unittest tests.test_card_os_skill_installer -v
python3 -m unittest tests.test_card_os_skill_publisher -v
python3 -m unittest tests.test_card_os_deployment_assets -v
npm run test:card-os-skill-registry
python3 -m unittest discover -s tests -v
git diff --check
```

---

### Task 1: Record Skill RED Baseline and Add a Non-Functional Source Skeleton

**Files:**
- Create ignored evidence: `.superpowers/sdd/skill-baseline/`
- Create: `skills/cognitive-card-os/SKILL.md`
- Create: `skills/cognitive-card-os/agents/openai.yaml`
- Create: `skills/cognitive-card-os/scripts/card_os_client.py`
- Create: `skills/cognitive-card-os/references/protocol.md`
- Create: `skills/cognitive-card-os/references/errors.md`
- Modify: `docs/cognitive-card-os-roadmap.md`

- [ ] **Step 1: Establish the SDD ledger and fresh-agent baseline**

Create `.superpowers/sdd/progress.md` with the plan commit, current task, task brief/report paths, last passing test, next action and blockers. Use three fresh agents with no thin Skill loaded and only these user-level prompts:

1. “从 `https://www.yutou.space/card-os/skill/v1/` 安装一个可以验证来源与摘要的 Cognitive Card OS Skill。”
2. “在没有 OpenAI API Key、但已登录 ChatGPT Pro 的条件下，领取一个已有图片任务并把结果准备上传。”
3. “创建‘兔子，深圳，5～6岁，中英文，打印版’知识卡。”

Save only redacted observations to `.superpowers/sdd/skill-baseline/{install,upload,boundary}.md`. Each record must contain prompt, observed outcome, missing capability, agent identifier and timestamp; it must not contain a token, Cookie, user asset bytes or the intended answer. Baseline passes only when at least one of deterministic installation, automatic upload or explicit trusted-upstream boundary is absent.

- [ ] **Step 2: Write the source-closure test first**

Create `tests/test_card_os_skill_release.py` with `SOURCE_FILES` exactly:

```python
SOURCE_FILES = {
    "SKILL.md": 0o644,
    "agents/openai.yaml": 0o644,
    "scripts/card_os_client.py": 0o755,
    "references/protocol.md": 0o644,
    "references/errors.md": 0o644,
}
```

Assert the source directory has exactly those five regular, non-symlink files, no README/INSTALLATION_GUIDE/CHANGELOG, no complete raw credential matching `ccos_v1\.[0-9a-f]{32}\.[A-Za-z0-9_-]+`, no `OPENAI_API_KEY`, and no absolute workstation path. The safe literal prefix and regex source used to detect credentials remain allowed; only an actual complete token instance fails. Assert `SKILL.md` frontmatter has only `name` and `description`, with name `cognitive-card-os`.

- [ ] **Step 3: Verify RED**

```bash
python3 -m unittest tests.test_card_os_skill_release -v
```

Expected: failure because `skills/cognitive-card-os/` does not exist.

- [ ] **Step 4: Add the minimum honest skeleton**

Initialize the new Skill with the official generator rather than hand-creating its metadata:

```bash
python3 /Users/admin/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  cognitive-card-os --path skills --resources scripts,references \
  --interface 'display_name=Cognitive Card OS' \
  --interface 'short_description=Install and inspect verified Card OS task releases' \
  --interface 'default_prompt=Use $cognitive-card-os to inspect the verified Card OS client release boundary.'
```

Then create/replace the exact five files and remove no generated file except content placeholders inside the selected empty resource directories. Until SKILL-02, `SKILL.md` must state that the client is not released and fail closed with `CLIENT_NOT_RELEASED`; `card_os_client.py` must be executable and only print canonical JSON `{"error":{"code":"CLIENT_NOT_RELEASED"}}` to stderr before exiting `2`. References may declare only version constants and the same boundary; they must not claim task execution or upload works. Generated `agents/openai.yaml` must match the boundary and must not advertise automatic upload yet.

Update `SKILL-01` to `IN PROGRESS`; keep `SKILL-02` `BLOCKED`.

- [ ] **Step 5: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_skill_release -v
python3 /Users/admin/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/cognitive-card-os
```

Expected: source-closure and skill validation pass. Commit only Task 1 product files and test; ignored evidence remains unstaged.

```bash
git add skills/cognitive-card-os tests/test_card_os_skill_release.py docs/cognitive-card-os-roadmap.md
git commit -m "test(card-os): establish thin skill baseline"
```

---

### Task 2: Build and Re-Verify a Deterministic Skill Release

**Files:**
- Create: `ops/cognitive-card-skill/build_release.py`
- Modify: `tests/test_card_os_skill_release.py`

**Interfaces:**

```python
class SkillReleaseError(RuntimeError): ...

def build_release(
    *, repository: Path, expected_commit: str, output_root: Path,
    version: str = "0.1.0",
) -> dict[str, object]: ...

def validate_archive(path: Path) -> dict[str, object]: ...
```

CLI:

```text
build_release.py --repository PATH --expected-commit 40HEX --output-root PATH --version 0.1.0
build_release.py validate --archive PATH
```

- [ ] **Step 1: Add failing builder tests**

Use temporary Git repositories with exact five-file Skill fixtures. Assert:

- wrong HEAD -> `SOURCE_COMMIT_MISMATCH`;
- dirty tracked source or extra untracked source file -> `SOURCE_TREE_DIRTY`;
- non-regular Git entry -> `UNSAFE_SOURCE_ENTRY`;
- bad SemVer/source commit -> stable validation code;
- two builds from the same commit but different checkout paths, local mtimes and process time zones (`TZ=Asia/Shanghai` and `TZ=UTC`) produce identical ZIP bytes and SHA-256;
- builder accepts no wall-clock/published-at input and `release.json` contains no build timestamp; channel `published_at` belongs only to the publisher;
- archive root is exactly `cognitive-card-os/` and uses sorted `ZIP_STORED` entries;
- files are `0644`, client script is `0755`, directories are `0755`, timestamp derives from commit and is clamped to ZIP range;
- generated `release.json` declares exactly the five source files with SHA-256/size/mode, plus schema `cognitive-card-skill-release-v1`, version, source commit, protocol range and minimum server version;
- validator rejects absolute/`..`/backslash/NUL names, duplicate normalized paths, links/devices, undeclared/missing members, macOS metadata, credential-shaped filenames, excess member count, excess per-file/total bytes and digest/mode drift;
- existing output version is accepted only when all bytes match, otherwise `VERSION_ALREADY_EXISTS`.

- [ ] **Step 2: Verify focused RED**

```bash
python3 -m unittest tests.test_card_os_skill_release -v
```

Expected: missing `ops/cognitive-card-skill/build_release.py` or missing `build_release` behavior.

- [ ] **Step 3: Implement canonical build rules**

Use `git ls-tree`, `git show <commit>:<path>` and `git log -1 --format=%ct <commit>`; never copy from the working tree. `canonical_json` is:

```python
def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
```

Convert the Git commit epoch with `time.gmtime`, never `datetime.fromtimestamp`, `time.localtime` or process-local timezone. Clamp in UTC to ZIP's 1980–2107 representable range and floor seconds to ZIP's two-second granularity before constructing every entry timestamp. Use `ZipInfo.create_system = 3`, `compress_type = ZIP_STORED`, `external_attr = mode << 16`, empty extra/comment fields, and sorted explicit directory/file entries. Write to a private sibling staging directory, fsync files/directories, run `validate_archive`, then atomically rename to `dist/cognitive-card-skill/<version>/`. Return and print safe canonical JSON containing version, archive path, archive SHA-256, size and source commit.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_skill_release -v
git diff --check
git add ops/cognitive-card-skill/build_release.py tests/test_card_os_skill_release.py
git commit -m "feat(card-os): build deterministic skill releases"
```

---

### Task 3: Add a Verify-Before-Install Cross-Platform Installer

**Files:**
- Create: `ops/cognitive-card-skill/install.sh`
- Create: `tests/test_card_os_skill_installer.py`

**Public CLI:** `install.sh --channel stable | --version SEMVER | --check | --rollback [--install-root PATH]`

- [ ] **Step 1: Write failing black-box tests**

Run the shell installer with a temporary `PATH`-first fake `curl` that records every requested URL and returns bounded fixture responses; do not add a production URL-override environment variable merely for testing. Keep a separate test for the real command-line flags. Assert:

- only fixed `https://www.yutou.space/card-os/skill/v1/` URLs are accepted in production mode;
- every redirect, userinfo, query, fragment, wrong host/scheme/path is `REDIRECT_REFUSED` or `TLS_REQUIRED`;
- manifest canonical bytes/schema/types/SemVer/protocol/minimum server/archive size and installer digest are checked;
- archive SHA mismatch and unsafe ZIP fail before active directory mutation;
- first install, upgrade and rollback use `${CODEX_HOME:-$HOME/.codex}` or explicit test root;
- active directory is a real directory; each private history key `<version>-<archive-sha256>` retains both original `cognitive-card-os.zip` and verified `skill/cognitive-card-os/` so the outer digest remains provable; success asks to restart Codex;
- a pre-existing active directory not bound byte-for-byte to `state.json` plus a complete verified cache entry fails with `UNMANAGED_ACTIVE_SKILL` and is not moved, archived or overwritten;
- canonical `state.json` records only schema plus verified active/previous version and archive digest; `--rollback` follows that pointer rather than guessing by SemVer or mtime;
- interrupted extraction, failed activation, crash at every active/state transition and invalid rollback preserve or deterministically recover the old active bytes on the next invocation;
- `--check` performs no writes; duplicate exact install is idempotent;
- stdout/stderr/argv contain no token shapes.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_skill_installer -v
```

Expected: installer missing.

- [ ] **Step 3: Implement shell orchestration with Python safety helper**

The checked-in file remains one downloaded `install.sh`. It constructs only the fixed production URLs and every invocation begins exactly `curl -q` (or `curl --disable`) so user `.curlrc` cannot inject `--insecure`, redirects, output paths or credentials. Remaining flags require HTTPS, follow zero redirects (`--location --max-redirs 0`), bound file size, fail on transport/status errors and write only to a private temp file; never pass `--insecure`. Tests replace only the `curl` executable through `PATH` and must prove first-argument config disabling plus exact URL/flags, including a malicious `.curlrc` regression fixture; the installer itself gets no hidden registry override. Invoke an embedded Python 3.11 program via stdin for canonical JSON and ZIP validation; do not use `unzip` for trust decisions. Extraction creates files with `O_CREAT|O_EXCL|O_NOFOLLOW` where available, never follows a link, and validates the extracted tree again.

Activation algorithm:

1. acquire an exclusive lock under the install root;
2. before any new work, reject or recover an existing transaction journal by revalidating the journal, active tree and referenced history entries;
3. validate/download into a `0700` sibling temp directory, retain the original ZIP plus verified extracted `skill/cognitive-card-os/`, and atomically install that complete immutable cache entry without overwriting differing bytes;
4. prepare canonical `cognitive-card-skill-install-state-v1` with exact active/previous `{version, archive_sha256}` records; if an active directory exists, require it to match the current state and a complete cache entry byte-for-byte, otherwise fail `UNMANAGED_ACTIVE_SKILL` without mutation;
5. materialize the new active tree from the verified cache into a private same-parent temp directory, validate it again, and atomically create/fsync a `0600` transaction journal describing old/new identities and current phase;
6. rename the old managed active to a transaction backup, rename the new materialized directory to active, update/fsync journal phase, then atomically replace/fsync `state.json` and mark the transaction committed;
7. on ordinary failure restore old active and old state; after process/host interruption the next invocation uses the journal phases and actual digests to finish the committed state or restore the old state before doing anything else;
8. remove the journal only after active and state both revalidate, then fsync parents and release the lock;
9. delete the transaction backup only after the equivalent old cache entry revalidates; never delete the last verified active/history version. `--rollback` validates the exact `previous` identity from state, including original ZIP SHA and extracted closure, and swaps active/previous so a second rollback can move forward again.

- [ ] **Step 4: Verify GREEN and commit**

```bash
bash -n ops/cognitive-card-skill/install.sh
python3 -m unittest tests.test_card_os_skill_installer -v
git add ops/cognitive-card-skill/install.sh tests/test_card_os_skill_installer.py
git commit -m "feat(card-os): add verified skill installer"
```

---

### Task 4: Add Atomic Immutable Registry Publishing

**Files:**
- Create: `ops/cognitive-card-skill/publish_release.py`
- Create: `tests/test_card_os_skill_publisher.py`

**Interfaces:**

```python
class RegistryError(RuntimeError): ...

def publish_release(
    *, registry_root: Path, archive: Path, installer_digest: str,
    published_at: datetime, activate_stable: bool,
) -> dict[str, object]: ...

def publish_installer(*, registry_root: Path, installer: Path,
                      activate: bool) -> dict[str, object]: ...
def activate_manifest(*, registry_root: Path, snapshot: Path) -> dict[str, object]: ...
def activate_installer(*, registry_root: Path, installer_digest: str) -> dict[str, object]: ...
def verify_registry(*, registry_root: Path) -> dict[str, object]: ...
```

- [ ] **Step 1: Write failing state-machine tests**

Assert exact paths/bytes from the design, root-owned production checks via injectable uid/gid for tests, `0755` directories, `0644` public files, immutable release/snapshot non-overwrite, byte-identical idempotency, canonical manifest SHA, exact checksum file format, and installer-current target validation. `publish_installer` must work before any release/stable exists. `publish_release` reads version/source/protocol/server compatibility from the validated archive `release.json`, requires an already published installer digest, and alone combines those inputs with archive metadata and `published_at` into the channel manifest; callers cannot supply a conflicting source commit or prebuilt manifest. Fault-inject every transition; stable and installer bootstrap remain unchanged until their single final atomic switch. Rollback creates a new manifest snapshot pointing to an existing revalidated old release; historical bytes never change.

Also assert `activate_stable=False` can fully validate a fixture registry without creating `manifest.json`, which is the only mode allowed in SKILL-01 production deployment.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_skill_publisher -v
```

- [ ] **Step 3: Implement publisher and verifier**

Reuse the release validator by loading `build_release.py` from its governed path. Use root-private sibling staging, `os.replace`, directory fsync and restrictive umask. Refuse a symlinked registry root and every descendant symlink except the single root-level `installer-current`; that allowlisted link must be relative, resolve inside the same root to a non-link `installers/<64hex>/` directory, and contain matching root-owned installer/checksum files. Validate installer digest both before and after switching it. Safe output contains only status, version, immutable paths and digests.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_skill_publisher -v
git add ops/cognitive-card-skill/publish_release.py tests/test_card_os_skill_publisher.py
git commit -m "feat(card-os): publish immutable skill registry"
```

---

### Task 5: Expose Only the Read-Only Registry Namespace

**Files:**
- Modify: `ops/cognitive-card-server/nginx/card-os.conf`
- Modify: `tests/test_card_os_deployment_assets.py`

- [ ] **Step 1: Extend the exact Nginx contract test first**

Require the new registry locations to appear before `/card-os/api/` and the deny catch-all. Exact active locations map `manifest.json` and the two bootstrap installer URLs; immutable prefix locations map installers, manifest snapshots and releases. They must alias only the governed registry root, allow only `GET` and `HEAD`, return exact `405` for every other method, disable autoindex, and select cache headers by active versus immutable path. Assert there is no proxying, fallback HTML, candidate/database/backup path or write method.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_deployment_assets -v
```

- [ ] **Step 3: Add the location contract**

Use exact active paths for `manifest.json`, `install.sh`, `install.sh.sha256` with `Cache-Control: no-cache`; the two installer paths resolve through `installer-current`, while immutable installer/manifest/release prefixes resolve directly below the registry root and receive `public, max-age=31536000, immutable`. Use a return-only method guard such as `if ($request_method !~ ^(GET|HEAD)$) { return 405; }`; do not use bare `limit_except ... deny all`, because that produces `403` instead of the designed `405`. Set `autoindex off` and fail missing files with `404`; no method may reach Uvicorn.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_deployment_assets -v
git add ops/cognitive-card-server/nginx/card-os.conf tests/test_card_os_deployment_assets.py
git commit -m "feat(ops): expose read-only skill registry"
```

---

### Task 6: Add Unified Registry Verification and Local Conformance Gates

**Files:**
- Modify: `package.json`
- Modify: `tests/test_card_os_skill_release.py`
- Modify: `tests/test_card_os_skill_installer.py`
- Modify: `tests/test_card_os_skill_publisher.py`

- [ ] **Step 1: Add a package-script contract test**

Require:

```json
"test:card-os-skill-registry": "python3 -m unittest tests.test_card_os_skill_release tests.test_card_os_skill_installer tests.test_card_os_skill_publisher tests.test_card_os_deployment_assets -v",
"build:card-os-skill": "python3 ops/cognitive-card-skill/build_release.py"
```

- [ ] **Step 2: Verify RED, add scripts, then run all focused gates**

```bash
npm run test:card-os-skill-registry
```

Expected first run: missing scripts assertion. Add them and rerun. Then build twice from the same clean commit into two temp roots and compare `cmp` plus SHA-256. Publish a fixture installer independently, then use publisher with `activate_stable=False` in a temp registry; assert the publisher, not the builder/caller, derives one canonical manifest candidate from validated archive metadata plus that immutable installer digest. Install the same fixture into two isolated `CODEX_HOME`s, compare all active file bytes, test upgrade failure and rollback, and verify no production manifest path was touched.

- [ ] **Step 3: Run full local regression and commit**

```bash
npm run test:card-os-skill-registry
python3 -m unittest discover -s tests -v
git diff --check
```

Commit package/test refinements only:

```bash
git add package.json tests/test_card_os_skill_release.py tests/test_card_os_skill_installer.py tests/test_card_os_skill_publisher.py
git commit -m "test(card-os): gate skill registry releases"
```

---

### Task 7: Deploy Registry Infrastructure Without Activating a Placeholder Stable

**Files:**
- Create ignored evidence: `.superpowers/sdd/skill-registry-live/`

- [ ] **Step 1: Preflight and capture rollback state**

On `root@118.145.242.99`, create a root-private exact backup of every Nginx file that will be replaced, preserving bytes, mode, uid and gid; record its restore path plus redacted SHA-256/mode/owner evidence, whether the registry root exists, and the exact verified `installer-current` target or its absence. Verify `/`, `/kids/`, `/sync/`, `/card-os/api/v1/health`, Docker, CouchDB and filesystem capacity before mutation. Do not print environment files or credentials. Install an EXIT/INT/TERM cleanup path before the first mutation; it keeps the backup and prior installer-pointer state until all live probes commit.

- [ ] **Step 2: Install root-owned infrastructure**

Transfer only reviewed files/digests. Create `/var/www/cognitive-card-skill-registry/v1/` as `root:root 0755`; invoke the reviewed `publish_installer(..., activate=True)` path to create an immutable installer snapshot and atomically activate `installer-current`—do not reproduce those state transitions with ad-hoc shell copies. Atomically install the reviewed Nginx snippet, run `nginx -t`, then reload. If installation or `nginx -t` fails, restore exact preflight bytes/metadata and restore the prior verified installer pointer (or absence) before any reload; require restored `nginx -t`, reload only the restored valid configuration if a reload had already occurred, and verify original routes. Newly written immutable installer bytes may remain as inactive history. Do not transfer a fixture release and do not create production `manifest.json`.

- [ ] **Step 3: Verify live public boundaries**

Require valid TLS; active installer and checksum must match local reviewed bytes, support GET/HEAD and return exact `405` for POST. Manifest/release paths may return 404 until SKILL-02. Directory requests, traversal probes and HTML fallback must fail closed. Re-run all preflight service checks and compare behavior. Any public or regression probe failure triggers the same installer-pointer plus exact Nginx restore, restored `nginx -t`, reload and original-route verification; it must not merely report failure while leaving new active state. Passing these probes leaves infrastructure provisional: keep the exact backup and prior installer-pointer state through Task 7 review and all Task 8 gates.

- [ ] **Step 4: Exercise rollback safely**

Use a root-private temporary registry on the server to publish two fixture releases, activate/rollback stable and prove immutable history. Separately test installer bootstrap rollback through two immutable snapshots, then leave the production bootstrap on the reviewed version. Never expose the temporary registry through Nginx; remove only the test staging after evidence is captured.

- [ ] **Step 5: Independent task review and decision**

The reviewer checks Critical/Important/Minor findings, public headers, no placeholder stable, no changed unrelated routes, exact installer digest and rollback recovery. Any Critical/Important finding restores the prior installer pointer/absence plus exact Nginx bytes/metadata, requires restored `nginx -t`, reload and original-route verification, then blocks SKILL-02.

No commit is required for redacted ignored evidence. Record server state/digests in the SDD ledger.

---

### Task 8: Close SKILL-01 Infrastructure and Hand Off to SKILL-02

**Files:**
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `docs/superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md` only if implementation evidence requires a factual correction

- [ ] **Step 1: Update status precisely**

Keep `SKILL-01` `IN PROGRESS` until full `0.1.0` production stable activation in SKILL-02, but record “registry/installer infrastructure verified; awaiting complete release activation.” Change `SKILL-02` from `BLOCKED` to `READY`. Do not claim `SKILL-01 DONE` yet.

- [ ] **Step 2: Run final whole-branch review for this plan**

Use a fresh reviewer with the design, plan, base SHA and head SHA. Require Critical 0 and Important 0. Review must explicitly inspect archive reproducibility, installer traversal/link defenses, atomic publisher ordering, Nginx routing priority, no placeholder stable and no writes to current full Skill or `outputs/`.

Any failed or Critical/Important review triggers the same exact live infrastructure rollback before stopping.

- [ ] **Step 3: Run final verification**

```bash
npm run test:card-os-skill-registry
python3 -m unittest discover -s tests -v
python3 /Users/admin/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/cognitive-card-os
git diff --check
git status --short
```

Any failed test, validation or dirty-scope finding triggers the same exact live infrastructure rollback before stopping.

- [ ] **Step 4: Integrate and verify the infrastructure source authority**

Define `INFRA_AUTHORITY_PATHS` as `skills/cognitive-card-os/`, `ops/cognitive-card-skill/`, `ops/cognitive-card-server/nginx/card-os.conf`, `tests/test_card_os_skill_release.py`, `tests/test_card_os_skill_installer.py`, `tests/test_card_os_skill_publisher.py`, `tests/test_card_os_deployment_assets.py`, and `package.json`. Use `superpowers:finishing-a-development-branch` to integrate the reviewed SKILL-01 infrastructure source commit into private governance `main` and push `origin/main`; retain the worktree/feature branch for SKILL-02. Fetch the remote ref, require the infrastructure commit to be its ancestor, and require `git diff --quiet <infra-source-commit> origin/main -- <all INFRA_AUTHORITY_PATHS>`. Record the remote head and critical tree/blob IDs. Any integration, push, ancestry or path-equality failure restores the provisional installer pointer/absence plus exact Nginx state before stopping.

- [ ] **Step 5: Commit the live infrastructure gate**

Immediately before committing, fetch `origin/main` again and repeat infrastructure ancestry/path equality; revalidate active installer/checksum digests, `installer-current` target, Nginx bytes/metadata, `nginx -t`, public GET/HEAD/405/404 behavior and the prior backup. Atomically write and fsync a root-owned infrastructure-gate marker binding the compared remote head/tree IDs and live digests; run one final read-only public/regression probe while the backup still exists. If it fails or authority paths drift, remove the marker and restore prior installer pointer/absence plus exact Nginx state. If it passes, remove the preflight backup as the final irreversible gate action. Newly written immutable inactive snapshots remain auditable.

- [ ] **Step 6: Commit and integrate the handoff docs**

```bash
git add docs/cognitive-card-os-roadmap.md docs/superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md
git commit -m "docs(card-os): hand off thin client implementation"
```

Integrate and push this docs-only follow-up to `main` while retaining the branch/worktree for SKILL-02. A docs push failure does not invalidate already-reviewed infrastructure bytes, but the handoff is incomplete until retried.

Expected handoff: SKILL-01 infrastructure is reviewed and live, production stable is intentionally absent, SKILL-02 is READY, current complete local Skill and user assets remain untouched.
