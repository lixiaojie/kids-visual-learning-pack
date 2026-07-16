# Cognitive Card OS Thin Client and Automatic Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` after the SKILL-01 whole-branch review passes. Use `superpowers:writing-skills` forward testing for the Skill behavior and fresh implementer/reviewer agents for every task.

**Goal:** 把已验证的发行基础设施填充为完整 `cognitive-card-os` `0.1.0` 薄客户端，使 Codex 在无 OpenAI API Key、仅使用登录 ChatGPT Pro 的条件下领取锁定 GenerationPacket、在本地生成候选、严格校验并自动上传，同时对自由概念失败关闭。

**Architecture:** `SKILL.md` 只描述任务边界与代理工作流；Python 3.11 标准库客户端负责 capability 协商、凭据、无重定向 API 传输、packet 状态和结果校验上传；服务器仍是事实、内容锁、候选存储和审计权威。完整源码构建为不可变 `0.1.0`，首次激活 production stable，再在两个隔离 `CODEX_HOME` 和现网短期 scoped token 上验收。

**Tech Stack:** Python 3.11+ standard library、macOS Security.framework、Linux Secret Service `secret-tool`、HTTP/JSON、SHA-256、`unittest`、Codex Skills、现有 Card OS API `0.3.1`。

## Entry Gate

- SKILL-01 全计划 Critical 0 / Important 0。
- 生产 registry 和 installer bootstrap 已部署并验证；生产 `manifest.json` 尚未被占位 release 激活。
- 当前本机完整 `/Users/admin/.codex/skills/cognitive-card-os` 未改变。
- 基线三场景证据存在于忽略的 `.superpowers/sdd/skill-baseline/`，且没有向 forward-test agents 泄露答案。

## Global Constraints

- 权威设计与 SKILL-01 plan 均为输入；本计划不得改变已冻结的 registry/installer 契约。
- `0.1.0` 只处理服务器已有、锁定、可领取的 packet；自由概念必须返回 `TRUSTED_UPSTREAM_REQUIRED`。
- 不调用 OpenAI API，不要求 `OPENAI_API_KEY`，不读取/上传 ChatGPT Cookie、会话或身份材料。
- token 不出现在 argv、stdout/stderr、日志、Skill、Git、result、测试制品或 SDD 账本。
- credential priority：macOS Keychain -> Linux Secret Service -> 显式 `--allow-file-store` 的 0600 file fallback。
- 带 Authorization 的请求禁止自动重定向；固定 HTTPS base URL；只有明确测试注入可使用 loopback HTTP。
- claim/complete 不盲重试；GET 与相同 `Idempotency-Key`/完全相同 bytes 的 submit 才允许有界重试。
- local validator 是第一道门，服务器仍必须重新验证；客户端收到 receipt 后复核 result/artifact digests。
- decoded artifacts 总计不超过 `20 MiB`，规范请求体不超过 `28 MiB`；required output 恰好一次。
- 不实现门户、浏览器上传、自由概念编译、服务器渲染、QA、正式发布或旧站替换。
- `SKILL-02` 在第二台真实 Codex 电脑安装相同摘要前保持 `IN PROGRESS`。

## Product File Map

- Modify: `skills/cognitive-card-os/SKILL.md`
- Modify: `skills/cognitive-card-os/agents/openai.yaml`
- Replace: `skills/cognitive-card-os/scripts/card_os_client.py`
- Modify: `skills/cognitive-card-os/references/protocol.md`
- Modify: `skills/cognitive-card-os/references/errors.md`
- Create: `tests/test_card_os_client_transport.py`
- Create: `tests/test_card_os_client_credentials.py`
- Create: `tests/test_card_os_client_packets.py`
- Create: `tests/test_card_os_client_results.py`
- Create: `tests/test_card_os_thin_skill.py`
- Modify: `tests/test_card_os_skill_release.py`
- Modify: `package.json`
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `README.md`

## Fixed Client Contract

```text
python3 scripts/card_os_client.py doctor
python3 scripts/card_os_client.py auth set --stdin [--allow-file-store]
python3 scripts/card_os_client.py auth status
python3 scripts/card_os_client.py auth delete
python3 scripts/card_os_client.py packets list
python3 scripts/card_os_client.py packets claim PACKET_ID
python3 scripts/card_os_client.py packets get PACKET_ID --output FILE
python3 scripts/card_os_client.py packets complete PACKET_ID
python3 scripts/card_os_client.py results submit PACKET_ID --directory DIR
python3 scripts/card_os_client.py jobs status JOB_ID
python3 scripts/card_os_client.py jobs events JOB_ID
```

Protected headers:

```text
Authorization: Bearer <token>
X-Card-OS-Protocol: 1
X-Card-OS-Skill-Release: 0.1.0
```

Idempotency key:

```python
"ccos-v1-" + hashlib.sha256(
    packet_id.encode("utf-8") + b"\n" + canonical_request_body
).hexdigest()
```

`0.3.1` client-visible server-code contract snapshot, copied from app commit `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`, is grouped as follows:

```text
auth/protocol:
  AUTH_REQUIRED AUTH_INVALID AUTH_EXPIRED AUTH_SCOPE_REQUIRED AUTH_REVOKED
  CLIENT_UPGRADE_REQUIRED SERVER_UPGRADE_REQUIRED INVALID_SKILL_RELEASE
request/http:
  REQUEST_VALIDATION_FAILED REQUEST_TOO_LARGE PAYLOAD_TOO_LARGE
  UNSUPPORTED_MEDIA_TYPE UNSUPPORTED_CONTENT_ENCODING ROUTE_NOT_FOUND
  METHOD_NOT_ALLOWED HTTP_ERROR INTERNAL_ERROR
packet/state:
  JOB_NOT_FOUND PACKET_NOT_FOUND PACKET_ALREADY_CLAIMED PACKET_EXPIRED
  LEASE_EXPIRED LEASE_OWNER_MISMATCH INVALID_STATE_TRANSITION
  INVALID_CLIENT_ID CLIENT_REVOKED INVALID_PACKET_LIMIT INVALID_LEASE_DURATION
result/artifact:
  INVALID_IDEMPOTENCY_KEY IDEMPOTENCY_CONFLICT SKILL_RELEASE_MISMATCH
  INVALID_BASE64 MISSING_ARTIFACT UNDECLARED_ARTIFACT UNSAFE_ARTIFACT_PATH
  ARTIFACT_MEDIA_TYPE_MISMATCH ARTIFACT_SIZE_MISMATCH ARTIFACT_TOO_LARGE
  ARTIFACT_DIGEST_MISMATCH UNSUPPORTED_ARTIFACT_MEDIA_TYPE
  INVALID_ARTIFACT_MEDIA UNSAFE_ARTIFACT_COMPRESSION CONTENT_LOCK_MISMATCH
  PACKET_PROFILE_MISMATCH RESULT_CLIENT_MISMATCH STAGED_METADATA_MISMATCH
server-integrity:
  CANDIDATE_DIGEST_MISMATCH CANDIDATE_STORE_CLOSED CANDIDATE_STORE_REQUIRED
  INVALID_STORAGE_KEY UNSAFE_CANDIDATE_STORE FORBIDDEN_CREDENTIAL_FIELD
  FORBIDDEN_CREDENTIAL_VALUE NON_CANONICAL_JSON DATABASE_CONSTRAINT_VIOLATION
  INVALID_UTC_CLOCK INVALID_UTC_TIMESTAMP
```

Tests freeze this set as a compatibility fixture. Each code has one of four actions: re-authenticate, refresh/reconcile state, correct local result, or stop and report server-integrity failure. An unknown syntactically safe server code is preserved in output and mapped to `SERVER_CONTRACT_DRIFT`; it is never silently treated as success or rewritten to a known code.

Production local codes are also frozen: `TRUSTED_UPSTREAM_REQUIRED`, `REDIRECT_REFUSED`, `TLS_REQUIRED`, `DIGEST_MISMATCH`, `UNSAFE_ARCHIVE`, `CREDENTIAL_IN_RESULT`, `ATTEMPT_BODY_CHANGED`, `CREDENTIAL_STORE_UNAVAILABLE`, `CREDENTIAL_STORE_UNSAFE`, and `SERVER_CONTRACT_DRIFT`. Installer-only `UNMANAGED_ACTIVE_SKILL` is documented but is not emitted by `card_os_client.py`. Skeleton-only `CLIENT_NOT_RELEASED` must disappear from the complete `0.1.0` source.

---

### Task 1: Implement Fail-Closed Transport and Capability Negotiation

**Files:**
- Create: `tests/test_card_os_client_transport.py`
- Replace: `skills/cognitive-card-os/scripts/card_os_client.py`

**Interfaces:**

```python
class ClientError(RuntimeError):
    code: str

class NoRedirectHandler(urllib.request.HTTPRedirectHandler): ...

def canonical_json(value: object) -> bytes: ...
def request_json(method: str, path: str, *, token: str | None = None,
                 body: bytes | None = None, idempotency_key: str | None = None) -> tuple[int, dict[str, object]]: ...
def doctor() -> dict[str, object]: ...
```

- [ ] **Step 1: Write failing transport tests**

Use a loopback fixture server through an explicit injected `TransportConfig`; production CLI must not expose an arbitrary base-url flag. Assert TLS/fixed-host validation, zero redirects, bounded response size, canonical JSON, timeout mapping, safe error parsing and no token leakage. Verify `doctor` calls health and capabilities unauthenticated and rejects non-intersecting protocol, server `<0.3.1`, minimum Skill `>0.1.0`, malformed unsigned-decimal protocol and wrong schema using `CLIENT_UPGRADE_REQUIRED` or `SERVER_UPGRADE_REQUIRED` as designed.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_client_transport -v
```

Expected: current skeleton returns `CLIENT_NOT_RELEASED`.

- [ ] **Step 3: Implement the smallest transport/doctor slice**

Use `urllib.request.build_opener(NoRedirectHandler)`; never reuse an Authorization request after a 3xx. Parse SemVer numerically. Safe CLI output is canonical JSON and contains `status`, compatible versions/capabilities or stable `error.code` plus non-secret action. Catch exceptions by stable category, never echo raw request objects, headers or subprocess arguments.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_client_transport -v
git add skills/cognitive-card-os/scripts/card_os_client.py tests/test_card_os_client_transport.py
git commit -m "feat(card-os): negotiate thin client capabilities"
```

---

### Task 2: Implement Non-Disclosing Credential Backends

**Files:**
- Create: `tests/test_card_os_client_credentials.py`
- Modify: `skills/cognitive-card-os/scripts/card_os_client.py`

**Interfaces:**

```python
class CredentialStore(Protocol):
    def set(self, token: bytes) -> None: ...
    def get(self) -> bytes | None: ...
    def delete(self) -> bool: ...

def select_credential_store(*, platform: str, allow_file_store: bool) -> CredentialStore: ...
```

- [ ] **Step 1: Write failing backend and leakage tests**

Assert:

- `auth set --stdin` reads once, rejects empty/newline-containing/oversized input and never includes token in args/output;
- macOS backend uses Security.framework in-process through `ctypes`, service `cognitive-card-os`, account canonical production base URL, and zeroes mutable token buffers after calls;
- Linux backend invokes `secret-tool store` with metadata only in argv and sends token through stdin; lookup/delete output is captured and never logged;
- file fallback requires explicit flag, current-user `0700` non-link parent and `0600` non-link regular file created via `O_EXCL|O_NOFOLLOW`; wrong owner/mode/link fails closed;
- `CARD_OS_TOKEN` is ephemeral, takes request-time precedence, is never persisted automatically and is redacted from every error;
- `auth status` reports backend/presence only; `auth delete` is idempotent.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_client_credentials -v
```

- [ ] **Step 3: Implement platform adapters**

For macOS bind only the required Security.framework functions (`SecKeychainFindGenericPassword`, `SecKeychainAddGenericPassword`, `SecKeychainItemModifyAttributesAndData`, `SecKeychainItemFreeContent`, `CFRelease`) and map OSStatus without including secret bytes. Linux `subprocess.run` uses a list argv, `input=token`, captured output and a sanitized environment. File JSON stores base URL plus token, is canonical and rewritten through a private same-directory temp file with fsync/replace after lstat/ownership checks.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_client_credentials -v
git add skills/cognitive-card-os/scripts/card_os_client.py tests/test_card_os_client_credentials.py
git commit -m "feat(card-os): store scoped client credentials safely"
```

---

### Task 3: Implement Packet and Job Commands With Stable State Handling

**Files:**
- Create: `tests/test_card_os_client_packets.py`
- Modify: `skills/cognitive-card-os/scripts/card_os_client.py`

- [ ] **Step 1: Write failing command tests**

Copy the `0.3.1` packet-envelope and error fixtures from exact server app commit `c2a898cba5b8a8948c06688d8c2a387353d7cbbe` into this test module so tests do not depend on a neighboring checkout. Assert exact routes/methods:

```text
GET  /card-os/api/v1/packets/available
POST /card-os/api/v1/packets/{id}/claim
GET  /card-os/api/v1/packets/{id}
POST /card-os/api/v1/packets/{id}/complete
GET  /card-os/api/v1/jobs/{id}
GET  /card-os/api/v1/jobs/{id}/events
```

Protected requests must contain the three required security/version headers with exact values; ordinary transport headers such as `Content-Type`, `Content-Length`, `Accept` and a non-secret user agent remain allowed when appropriate. Packet/job IDs are encoded as one path segment; reject empty values, controls, `/` and `\\`, but do not invent a client regex narrower than the server contract. For every packet envelope, require the closed `packet` schema and recompute `packet_digest` exactly as server `0.3.1`: `"sha256:" + sha256(json.dumps(packet, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))`; reject any mismatch before saving, generating or mutating. Validate envelope claim/lease/expiry types separately. `packets get` writes canonical JSON through `O_EXCL` or an explicit safe overwrite flag, mode `0600`, no symlink following. No visible packet and any free-concept-shaped invocation yield `TRUSTED_UPSTREAM_REQUIRED`. Map the frozen `0.3.1` error-code set without rewriting codes; claim/complete timeout must trigger a status read, not blind POST replay.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_client_packets -v
```

- [ ] **Step 3: Implement the command state machine**

Centralize route building and error envelopes. Run `doctor` compatibility checks before protected task mutation, cache only within the process, and preserve server request IDs in safe output. `packets complete` is only a state transition; it does not claim the result is accepted or published.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_client_packets -v
git add skills/cognitive-card-os/scripts/card_os_client.py tests/test_card_os_client_packets.py
git commit -m "feat(card-os): operate locked generation packets"
```

---

### Task 4: Validate and Automatically Upload Generation Results

**Files:**
- Create: `tests/test_card_os_client_results.py`
- Modify: `skills/cognitive-card-os/scripts/card_os_client.py`

**Interfaces:**

```python
def validate_result_directory(packet: dict[str, object], directory: Path) -> tuple[dict[str, object], bytes]: ...
def result_idempotency_key(packet_id: str, canonical_body: bytes) -> str: ...
def load_or_create_attempt(packet_id: str, artifacts: tuple[dict[str, object], ...],
                           body_factory: Callable[[str], bytes]) -> tuple[bytes, str]: ...
def submit_result(packet_id: str, directory: Path) -> dict[str, object]: ...
```

- [ ] **Step 1: Write failing validation/upload tests**

Use packet/result fixtures copied from exact server app commit `c2a898cba5b8a8948c06688d8c2a387353d7cbbe`, not invented field names. Recompute the packet envelope digest again before result construction. Assert each `required_outputs` path appears exactly once; reject missing/undeclared files, absolute/`..`/backslash/control paths, normalization collisions, symlinks/devices, media mismatch, declared/actual size mismatch, per-file max, digest mismatch, decoded total >20 MiB and canonical body >28 MiB. Require base64 without whitespace, deterministic artifact order, schema `cognitive-card-generation-result-v1`, exact `skill_release=0.1.0`, current claimant/lease/content-lock recheck and `complete` before submit.

Before encoding, scan every decoded artifact byte string and every recursively visited string in relative paths, media metadata, `source_records` and `operator_notes` for both the exact current raw token bytes and any complete credential matching `ccos_v1\.[0-9a-f]{32}\.[A-Za-z0-9_-]+`. A match fails locally with `CREDENTIAL_IN_RESULT`; output contains only the code/path category, never matching bytes, fingerprint or surrounding text. Also scan the final canonical request body. Safe regex/prefix source in the installed client is allowed; an actual complete token instance in result material is not.

Assert exact idempotency formula. Same packet/body replay must return the same acceptance receipt. Although changed body bytes mathematically produce a different formula key, an existing packet attempt must stop locally with `ATTEMPT_BODY_CHANGED` rather than silently starting a second logical submit; a forced same-key changed-body fixture must map the server response to `IDEMPOTENCY_CONFLICT`. Treat receipt `result_digest` as a server-generated opaque identifier: validate exact `sha256:<64 lowercase hex>` shape and equality across an exact replay, but do not compare it to canonical request body SHA. Independently validate every staged artifact relative path, digest, size and `sha256/<first-two>/<digest>` storage key against local bytes; output says `candidate_staged`, never `published`.

Freeze exact replay through `${XDG_STATE_HOME:-$HOME/.local/state}/cognitive-card-os/attempts/<packet-id>.json`. On first submit, create a current-user-owned `0600` non-link canonical `cognitive-card-submit-attempt-v1` before complete/upload, containing only packet ID, fixed generated_at, canonical body SHA-256, idempotency key and sorted artifact path/SHA-256/size. Do not store token, payload bytes/base64 or absolute directory. On another `results submit` with unchanged artifacts, rebuild using the saved generated_at and require identical body digest/key before sending. Changed artifacts/metadata return `ATTEMPT_BODY_CHANGED` without a new POST/key. Reject wrong owner/mode/schema/link, tampered state and packet-ID path attacks; attempt-state errors never echo stored content.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_client_results -v
```

- [ ] **Step 3: Implement local closure and submission**

Walk with `os.scandir`/`lstat`, sorted POSIX relative paths, no link following. Determine media type only from packet declarations and verify signature where the server contract does so. Build one canonical request body around the generated_at fixed by the private attempt state, calculate its key once, and retry only the exact immutable byte string with the same key. Before a retry, query packet/job state. Never write candidate bytes into the Skill directory or attempt state.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_client_results -v
git add skills/cognitive-card-os/scripts/card_os_client.py tests/test_card_os_client_results.py
git commit -m "feat(card-os): validate and upload generation results"
```

---

### Task 5: Write the Thin Skill Instructions and Run Pre-Publish Behavior Probes

**Files:**
- Create: `tests/test_card_os_thin_skill.py`
- Modify: `skills/cognitive-card-os/SKILL.md`
- Modify: `skills/cognitive-card-os/agents/openai.yaml`
- Modify: `skills/cognitive-card-os/references/protocol.md`
- Modify: `skills/cognitive-card-os/references/errors.md`
- Modify: `tests/test_card_os_skill_release.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing content/contract tests**

Assert `SKILL.md` remains concise, links only the two relevant references, instructs `doctor -> list/claim/get -> generate from packet -> complete/submit`, makes automatic upload primary, says ChatGPT Pro generation does not need API key, and explicitly fails free concepts with `TRUSTED_UPSTREAM_REQUIRED`. It must prohibit admin routes, direct publish, ChatGPT identity upload and claims of final publication. Protocol/errors references must enumerate exact commands, routes, headers, schemas, packet-digest algorithm, limits and every code in the frozen `0.3.1` client-visible contract snapshot above; tests assert set equality, not a loose subset. `agents/openai.yaml` must be consistent and pass the skill validator. README must identify private GitHub as source authority and the personal server as installable-release authority, document isolated `CODEX_HOME`, and include the spec's exact four-step bootstrap with `curl -q`, fixed HTTPS/TLS and zero redirects; the test rejects shortened `curl -fsSLO`, `curl | sh`, or advice to overwrite the current full Skill.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_thin_skill -v
```

Expected: skeleton still advertises `CLIENT_NOT_RELEASED` and lacks workflow.

- [ ] **Step 3: Replace skeleton with production instructions**

Keep detailed wire contracts in references so ordinary skill invocation loads only the workflow. Add a clear first-version decision table:

| Input state | Action |
| --- | --- |
| packet ID present | doctor, authenticate, fetch and verify |
| no packet ID but available packets visible | ask user to choose or claim only when explicitly authorized |
| free concept only | return `TRUSTED_UPSTREAM_REQUIRED`; do not synthesize a lock |
| generated candidate directory ready | local validation, complete, automatic submit |

After `SKILL.md` is final, regenerate UI metadata deterministically:

```bash
python3 /Users/admin/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py \
  skills/cognitive-card-os \
  --interface 'display_name=Cognitive Card OS' \
  --interface 'short_description=Run verified Card OS tasks and upload candidates' \
  --interface 'default_prompt=Use $cognitive-card-os to claim a locked task and upload its verified candidate outputs.'
```

Do not hand-edit the generated file afterward.

- [ ] **Step 4: Run fresh-agent pre-publish behavior probes**

Use two new agents, not the RED-baseline agents. Because the deterministic builder accepts only committed source and Task 5 is not committed yet, copy the exact five-file source closure directly into a fresh isolated `CODEX_HOME` for this probe; label it `unreleased-source-probe`, not a built release, and do not invoke the builder. Then give the agents original baseline prompts 2 and 3 with only that isolated Skill; do not give them the design, test expectations or baseline diagnosis. Require:

1. existing packet workflow uses ChatGPT Pro locally and selects automatic submit without asking for OpenAI API Key;
2. rabbit free-concept request stops with `TRUSTED_UPSTREAM_REQUIRED` instead of inventing a job.

Store redacted reports in `.superpowers/sdd/skill-forward-prepublish/`; compare prompt-for-prompt with baseline. This is not the final writing-skills GREEN gate because the original installation scenario cannot pass until Task 6 first-activates production stable.

- [ ] **Step 5: Verify and commit**

```bash
python3 -m unittest tests.test_card_os_thin_skill tests.test_card_os_skill_release -v
python3 /Users/admin/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/cognitive-card-os
git add skills/cognitive-card-os tests/test_card_os_thin_skill.py tests/test_card_os_skill_release.py README.md
git commit -m "feat(card-os): teach the thin skill workflow"
```

---

### Task 6: Land the Release Source, Build 0.1.0 and Provisionally Activate Stable

**Files:**
- Modify: `package.json`
- Modify ignored evidence: `.superpowers/sdd/skill-release-live/`

- [ ] **Step 1: Add the unified thin-client test entry and commit it**

Add:

```json
"test:card-os-thin-client": "python3 -m unittest tests.test_card_os_client_transport tests.test_card_os_client_credentials tests.test_card_os_client_packets tests.test_card_os_client_results tests.test_card_os_thin_skill -v"
```

Run RED for the missing script assertion if present, add the script, then all client tests. Commit before building so the archive source is a clean exact commit:

```bash
git add package.json
git commit -m "test(card-os): gate the thin client release"
```

- [ ] **Step 2: Run the pre-release code gate**

Run `npm run test:card-os-skill-registry`, `npm run test:card-os-thin-client`, full `unittest` discovery, `quick_validate.py` and `git diff --check`. Give the design, both plans, base SHA and current release-source SHA to a fresh reviewer; require Critical 0 / Important 0 for all product code that will enter the ZIP or operate the registry. A failed test or review stops before GitHub integration or production mutation.

- [ ] **Step 3: Integrate and push the source authority before publishing**

Use `superpowers:finishing-a-development-branch` to integrate the reviewed release-source commit into governance `main` and push private `origin/main`. Retain this worktree and feature branch because Tasks 7–9 and a later docs-only commit still use them; do not select branch/worktree cleanup yet. Do not publish from a commit that exists only locally or only on an unmerged feature branch. Fetch the remote ref and require `git merge-base --is-ancestor <release-source-commit> origin/main`.

Define `RELEASE_AUTHORITY_PATHS` as `skills/cognitive-card-os/`, `ops/cognitive-card-skill/`, `ops/cognitive-card-server/nginx/card-os.conf`, `tests/test_card_os_skill_release.py`, `tests/test_card_os_skill_installer.py`, `tests/test_card_os_skill_publisher.py`, `tests/test_card_os_client_transport.py`, `tests/test_card_os_client_credentials.py`, `tests/test_card_os_client_packets.py`, `tests/test_card_os_client_results.py`, `tests/test_card_os_thin_skill.py`, `tests/test_card_os_deployment_assets.py`, `package.json`, and `README.md`. Require `git diff --quiet <release-source-commit> origin/main -- <all RELEASE_AUTHORITY_PATHS>` and record the compared remote head plus each critical tree/blob ID. If integration, push or path equality fails, stop before production mutation.

- [ ] **Step 4: Build twice from the exact authoritative commit**

Fetch `origin/main` again and repeat both ancestry and `RELEASE_AUTHORITY_PATHS` equality immediately before building. From a clean checkout of that exact release-source commit, build `0.1.0` into two separate temp roots; require identical ZIP bytes, `release.json` and SHA. The builder must not emit a channel manifest. Scan release, Git diff and ignored evidence for token shapes and absolute paths. Run `quick_validate.py` on an extracted copy.

- [ ] **Step 5: Publish immutable objects and provisionally activate stable**

Fetch `origin/main` a third time and repeat release-critical ancestry/path equality immediately before production transfer. Preflight live health, existing registry digests and Nginx behavior. Record the compared remote head/tree IDs and the exact prior active manifest bytes/digest or its absence in a root-private `skill-release-gate` state that remains live through Tasks 7–9. Transfer only the exact reviewed ZIP/sha inputs to root-private staging. Server publisher must revalidate the archive, bind the already active immutable installer digest, derive the canonical manifest, create immutable release and manifest snapshot, then atomically create production `manifest.json` as the last state change. This activation is provisional: if any Task 6–9 public, install, forward-test, upload, regression or final-review gate fails, atomically restore the prior manifest bytes or prior absence, keep immutable history, and verify the restored public old stable/404 state. Restore Nginx only if it changed.

- [ ] **Step 6: Verify the provisional public release contract**

For all six path classes, verify TLS, status, GET/HEAD, exact `405` for rejected POST, content type, body SHA and cache headers. Confirm public archive matches local SHA and extracts to the exact source closure. Re-run `/`, `/kids/`, `/sync/`, `/card-os/api/`, Docker and CouchDB checks. Evidence records only public digests/status and reviewed commits, never credentials. Do not delete or mark committed the root-private prior-manifest gate state; Task 9 owns the final commit/rollback decision.

---

### Task 7: Install Two Isolated Clients and Prove Local Upgrade/Rollback

**Files:**
- Modify ignored evidence: `.superpowers/sdd/isolated-clients/`

- [ ] **Step 1: Verify the bootstrap before execution**

Download `install.sh` and `install.sh.sha256` separately from production using the exact spec command shape whose first curl argument is `-q`, protocol is fixed to HTTPS/TLS 1.2+, and redirects are followed with maximum zero; never rely on user `.curlrc`. Verify checksum with platform-native tooling, inspect that the script digest matches manifest immutable installer digest, then execute. Never pipe network bytes to a shell.

- [ ] **Step 2: Install into two fresh roots**

Use `<temp>/client-a/.codex` and `<temp>/client-b/.codex`. Install stable independently from the public registry. Require both active trees, release.json and archive history to match byte-for-byte and share the same archive SHA. Run `doctor` in both with no OpenAI API Key.

- [ ] **Step 3: Exercise check, failed upgrade and rollback**

`--check` must be read-only. A corrupted download and incompatible manifest fixture must preserve active `0.1.0`. Use a locally verified earlier fixture only in isolated test roots to exercise rollback and forward reinstall; end both roots on production `0.1.0`.

If either isolated install, check, failure-recovery or rollback gate fails, immediately invoke the cross-task release rollback: atomically restore Task 6's prior manifest bytes or remove the provisional manifest when prior state was absent, verify its digest/absence and public old stable/404 behavior, then stop. Immutable `0.1.0` history remains for diagnosis but is no longer active stable.

- [ ] **Step 4: Preserve cutover boundary**

Prove `/Users/admin/.codex/skills/cognitive-card-os` inode/tree digest is unchanged from preflight. Do not copy isolated Skill over it. Remove isolated credentials before retaining redacted evidence.

- [ ] **Step 5: Run install and boundary forward tests**

Use two new agents, distinct from both RED baseline and pre-publish probes; do not provide design text, expected answers or defect diagnosis. Agent A starts with an empty isolated `CODEX_HOME` and receives original prompt 1, proving verified download/check/execute installation without `curl | sh`. Agent C starts with a separate isolated root containing the same production archive digest and receives original prompt 3; rabbit free-concept input must return `TRUSTED_UPSTREAM_REQUIRED` without inventing a job. Store redacted prompt-for-prompt comparisons in `.superpowers/sdd/skill-forward/`. This is a partial GREEN gate; original prompt 2 requires a real scoped credential and locked packet and therefore completes only in Task 8.

Any failed or inconclusive forward test triggers the same prior-manifest rollback before stopping.

---

### Task 8: Run One Live Claim, Complete and Automatic Upload Acceptance

**Files:**
- Modify ignored evidence: `.superpowers/sdd/thin-client-live/`

- [ ] **Step 1: Issue minimum short-lived credentials without disclosure**

If no suitable locked acceptance packet is already available, a separate trusted-upstream preparation step uses a short-lived admin credential to create exactly one minimal locked job and packet, then revokes that admin credential before the thin-client run; the thin client never receives or stores admin authority. Create a 15-minute client token with exact scope `submit` (the server expands it to effective `read`) for available-packet read, claim, packet read, complete and result submit. Keep raw client token in an OS credential backend or current-user-owned `0600` non-link temporary file only long enough to pass it via stdin; do not include it in shell history/argv/evidence.

- [ ] **Step 2: Start the live upload forward test with an existing locked packet**

Use one new Agent B, distinct from all baseline/prepublish/install/boundary agents. Preconfigure its isolated production Skill root with the short-lived `submit` credential through the tested secure backend and make exactly the prepared locked packet visible; do not disclose the token, design, expected workflow or baseline diagnosis. Give it original baseline prompt 2 verbatim. Agent B runs doctor/list, claims the packet, fetches it, verifies packet digest/content lock, and generates only its declared minimal test outputs using logged-in ChatGPT Pro/Codex capabilities without an OpenAI API Key. Do not introduce rabbit/free-concept generation into this protocol acceptance unless the trusted upstream already exposes such a locked packet.

- [ ] **Step 3: Complete, submit and replay**

Agent B validates the local directory, persists private attempt state, completes the packet, automatically submits, and compares receipt/result/artifact digests with server state and audit events. It runs the same `results submit` command again against unchanged files; saved generated_at/body digest/key must yield the same accepted result with `replayed=true`. Locally change a copy of the directory and require `ATTEMPT_BODY_CHANGED` before HTTP. A direct changed-body/same-key server conflict probe, if separately exercised by the acceptance harness, must be non-destructive and stop on `IDEMPOTENCY_CONFLICT`.

- [ ] **Step 4: Revoke and prove rejection**

Revoke the token by token ID while the same raw credential still remains in the secure client backend; immediately issue one protected request with that stored credential and require exact `403 AUTH_REVOKED`. Only after the server-side rejection is proven may `auth delete` remove the local credential; then require `auth status` to report absent. A `finally` cleanup path still deletes the local credential if the rejection probe or any later check fails. Scan client/server acceptance evidence for the raw token fingerprint without printing it. Confirm candidate is staged, content-addressed and audited but not published.

- [ ] **Step 5: Close the writing-skills GREEN comparison**

Add Agent B's redacted Steps 2–4 record for original prompt 2 to `.superpowers/sdd/skill-forward/` and compare it prompt-for-prompt with the RED baseline. Confirm the record proves local ChatGPT Pro/Codex generation without an OpenAI API Key, packet/content-lock verification, automatic upload, receipt validation, exact replay through attempt state and post-run token rejection. Only when prompts 1–3 all pass may writing-skills GREEN be declared; Step 5 performs no protected request and needs no live credential or unconsumed packet.

- [ ] **Step 6: Independent review**

Reviewer must find Critical 0 / Important 0 for token handling, scope, packet ownership, receipt validation, replay semantics and publication wording. Any Important finding blocks roadmap updates.

On any Task 8 failure or Critical/Important finding, revoke/delete all temporary credentials first, then atomically restore the Task 6 prior manifest or absence and verify the public old stable/404 state. After live upload, exact replay, revocation, all three writing-skills scenarios and this task review pass, keep the release provisional and hand the intact root-private gate state to Task 9; final full regression, whole-branch review and gate commit have not happened yet.

---

### Task 9: Update Authority Docs and Finish the Branch

**Files:**
- Modify: `docs/cognitive-card-os-roadmap.md`

- [ ] **Step 1: Update truthful project state**

- Mark `SKILL-01` `DONE` only now that complete `0.1.0` production stable and rollback gates passed.
- Mark `SKILL-02` `IN PROGRESS`: local code, two isolated roots and live upload passed, but second real Codex computer is still required.
- Preserve the already-reviewed README authority and safe-install contract without editing release-critical files.
- Keep `ACCEPT-01` `BACKLOG` until rabbit/age-5-6/bilingual/print generation, display and publication chain exists.

- [ ] **Step 2: Run complete verification**

```bash
npm run test:card-os-skill-registry
npm run test:card-os-thin-client
python3 -m unittest discover -s tests -v
python3 /Users/admin/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/cognitive-card-os
git diff --check
git status --short
```

Also rerun live health/capabilities/manifest/archive/installer probes and confirm both repos remain at intended commits with no user asset changes. Fetch private `origin/main`; require the release-source commit to remain its ancestor and repeat exact `RELEASE_AUTHORITY_PATHS` equality against the current remote head. Any failure or superseding release-critical drift triggers the prior-manifest rollback before stopping.

- [ ] **Step 3: Request final whole-branch review**

Provide design, both plans, base SHA, release-source SHA, current status-doc SHA, per-task reports and test evidence to a fresh reviewer. Require Critical 0 / Important 0. Explicit review topics: credential disclosure, redirect handling, result closure, idempotency, Skill truthfulness, immutable production bytes, rollback, GitHub source authority and current-full-Skill preservation. Any failed or Important review triggers prior-manifest rollback.

- [ ] **Step 4: Commit the server release gate**

Immediately before committing, fetch `origin/main` again; revalidate release-source ancestry plus exact `RELEASE_AUTHORITY_PATHS` equality, active manifest/archive/installer digests, public route behavior and the prior-manifest backup. Atomically write a root-owned release-gate commit marker binding the compared remote head, critical tree/blob IDs and release digests; run one final read-only public probe while the prior backup still exists. If that probe fails or remote critical paths drift, remove the marker and restore prior manifest/absence. If it passes, fsync the marker and registry root, then remove the prior-manifest backup as the final irreversible gate action. No later product mutation or test may be inserted before the docs-only step.

- [ ] **Step 5: Commit authority docs and integrate the status update**

```bash
git add docs/cognitive-card-os-roadmap.md
git commit -m "docs(card-os): publish thin skill operating model"
```

Use `superpowers:finishing-a-development-branch` again for this docs-only follow-up, integrate it into `main`, and push. A docs integration failure leaves the already validated release active and the status commit available for retry; it does not invalidate immutable release bytes. Do not mark SKILL-02 `DONE` until a second physical Codex computer installs the exact production archive SHA and passes `doctor`.
