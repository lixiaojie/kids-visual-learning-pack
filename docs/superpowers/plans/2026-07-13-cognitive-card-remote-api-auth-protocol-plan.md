# Cognitive Card Remote API, Auth, and Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the tested subscriber-execution core through a versioned HTTPS-ready API so a trusted Codex client can discover compatibility, authenticate with a Card OS token, find and claim an already locked generation packet, upload a digest-verified result, and resume after interruption without an OpenAI API key.

**Architecture:** Add three adapters around the existing subscriber application service: a pure protocol/capability module, an opaque scoped-token subsystem backed by the same SQLite database, and a FastAPI transport. Keep SQLite repositories request-scoped, derive every client identity from the bearer token, and translate stable domain errors at the HTTP boundary. The first release intentionally accepts only trusted, already content-locked jobs through an admin endpoint; free-form concept requests remain blocked until the classification, template, knowledge, and age registries are server-side.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic, HTTPX `TestClient`, SQLite, Python standard-library `secrets`/`hashlib`/`hmac`, `unittest`, Git.

## Global Constraints

- Source specifications:
  - `/Users/admin/Documents/kids-visual-learning-pack/docs/cognitive-card-os-system-design.md`
  - `/Users/admin/Documents/kids-visual-learning-pack/docs/cognitive-card-os-roadmap.md`
  - `/Users/admin/Documents/kids-visual-learning-pack/docs/superpowers/specs/2026-07-13-cognitive-card-pro-subscriber-execution-design.md`
- Implementation repository: `/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server`.
- Start from version `0.2.0` at commit `b74c401bd8f04aa5e765cd4d1e8cdccf8f0bf596`; finish this slice as `0.3.0`.
- Do not read, accept, proxy, or store ChatGPT cookies, ChatGPT identity, OpenAI API keys, or internal OpenAI tokens.
- Do not add a free-form `topic`/`concept` creation endpoint in this slice. `POST /admin/locked-jobs` requires exact lock identities produced by a trusted upstream operator.
- Do not implement browser cookie sessions, portal pages, MCP, rendering, publication, registry compilation, or live deployment in this slice.
- Public endpoints are limited to health and capabilities. Every other endpoint requires a Card OS bearer token and protocol headers.
- Token subject is the authoritative `client_id`; request bodies may not override it.
- Raw tokens are printed exactly once at issue time and are never stored or logged.
- Every protected response carries `X-Request-ID`; every error uses the stable envelope `{"error":{"code":"...","message":"...","request_id":"..."}}`.
- Request limits: maximum encoded request body 28 MiB, maximum decoded candidate payload total 20 MiB, maximum 16 artifacts, and existing per-artifact packet limits remain authoritative.
- Accepted artifact media types are exactly `application/json`, `text/markdown`, `text/plain`, `image/png`, `image/jpeg`, and `image/webp`. Client-uploaded PDF and archive/compressed media are rejected in this slice; print PDFs are produced later by the server renderer. Non-identity HTTP `Content-Encoding` is rejected. Images are structurally inspected before staging with limits of 8192 pixels per dimension, 40,000,000 total pixels, 100 MiB estimated decoded bytes, and 250:1 estimated decoded-to-uploaded byte ratio.
- Run the complete suite before every commit:

```bash
python3 -m unittest discover -s tests -v
```

---

## Protocol and Authorization Contract

### Public capability document

`GET /card-os/api/v1/capabilities` returns:

```json
{
  "schema": "cognitive-card-capabilities-v1",
  "server_version": "0.3.0",
  "protocol": {"minimum": 1, "maximum": 1},
  "packet_schemas": ["cognitive-card-generation-packet-v1"],
  "result_schemas": ["cognitive-card-generation-result-v1"],
  "minimum_skill_release": "0.1.0",
  "features": {
    "locked_job_admin_import": true,
    "subscriber_packet_exchange": true,
    "free_form_job_creation": false,
    "browser_session": false,
    "review": false
  }
}
```

Protected requests must send:

```http
Authorization: Bearer ccos_v1.<token_id>.<secret>
X-Card-OS-Protocol: 1
X-Card-OS-Skill-Release: 0.1.0
```

Missing or unsupported protocol is rejected before claim or submission. Protocol below the server minimum or Skill below `minimum_skill_release` returns HTTP 426 and `CLIENT_UPGRADE_REQUIRED`; protocol above the server maximum returns HTTP 426 and `SERVER_UPGRADE_REQUIRED`.

### Scopes

| Scope | Allowed operations |
| --- | --- |
| `read` | Read jobs, packets, packet availability, and job events |
| `submit` | All `read` operations plus claim, complete, and result submission |
| `review` | Reserved for the later review API; no route in this slice |
| `admin` | All operations plus locked-job creation and packet issuance |

### Endpoints

| Method and path | Scope | Purpose |
| --- | --- | --- |
| `GET /card-os/api/v1/health` | public | Liveness and server version |
| `GET /card-os/api/v1/capabilities` | public | Compatibility discovery |
| `POST /card-os/api/v1/admin/locked-jobs` | `admin` | Persist a trusted content lock identity |
| `POST /card-os/api/v1/admin/jobs/{job_id}/packets` | `admin` | Issue one immutable generation packet |
| `GET /card-os/api/v1/jobs/{job_id}` | `read` | Read state and immutable identity |
| `GET /card-os/api/v1/jobs/{job_id}/events` | `read` | Read ordered audit events |
| `GET /card-os/api/v1/packets/available?limit=20` | `read` | List unclaimed, unexpired packets |
| `GET /card-os/api/v1/packets/{packet_id}` | `read` | Download packet and lease metadata |
| `POST /card-os/api/v1/packets/{packet_id}/claim` | `submit` | Atomically claim with a bounded lease |
| `POST /card-os/api/v1/packets/{packet_id}/complete` | `submit` | Move owned packet to `awaiting_upload` |
| `POST /card-os/api/v1/packets/{packet_id}/results` | `submit` | Strictly decode, verify, stage, and accept a result |

---

## File Map

- Modify `pyproject.toml` — runtime/test dependencies, CLI entry points, and version `0.3.0`.
- Create `src/cognitive_card_server/protocol.py` — capability document and compatibility checks.
- Create `src/cognitive_card_server/auth/__init__.py` — public auth exports.
- Create `src/cognitive_card_server/auth/model.py` — `Scope`, token record, and principal.
- Create `src/cognitive_card_server/auth/repository.py` — token migrations and persistence.
- Create `src/cognitive_card_server/auth/service.py` — issue/authenticate/revoke logic.
- Create `src/cognitive_card_server/auth/cli.py` — issue/list/revoke operator commands.
- Modify `src/cognitive_card_server/subscriber/policy.py` — recoverable lease/packet-expiry transitions.
- Modify `src/cognitive_card_server/subscriber/repository.py` — stale-work recovery, duplicate-ID translation, event existence, and available-packet query.
- Modify `src/cognitive_card_server/subscriber/service.py` — stale-work recovery and available-packet application methods.
- Create `src/cognitive_card_server/http/__init__.py` — HTTP package marker.
- Create `src/cognitive_card_server/http/config.py` — immutable API settings from environment.
- Create `src/cognitive_card_server/http/schemas.py` — Pydantic request/response models.
- Create `src/cognitive_card_server/http/serialization.py` — domain-to-JSON and strict base64 conversion.
- Create `src/cognitive_card_server/http/errors.py` — stable status mapping and error handlers.
- Create `src/cognitive_card_server/http/app.py` — app factory, dependencies, middleware, and routes.
- Create `src/cognitive_card_server/http/cli.py` — Uvicorn launcher.
- Create `tests/test_protocol.py` — capability and compatibility tests.
- Create `tests/test_auth_repository.py` — token persistence tests.
- Create `tests/test_auth_service.py` — secret, scope, expiry, and revocation tests.
- Create `tests/test_auth_cli.py` — one-time token output and safe listing tests.
- Modify `tests/test_subscriber_repository.py` — available-packet query tests.
- Modify `tests/test_subscriber_service.py` — lease release/list orchestration tests.
- Create `tests/test_http_public.py` — health, capability, request ID, and body-limit tests.
- Create `tests/test_http_auth.py` — bearer/scope/protocol boundary tests.
- Create `tests/test_http_admin.py` — locked job and packet routes.
- Create `tests/test_http_subscriber.py` — list/claim/complete/result routes.
- Create `tests/test_http_integration.py` — restart and idempotent end-to-end fixture.
- Modify `README.md` — local launch, token issue, capability, and remote-flow examples.

### Task 1: Add the Capability and Compatibility Contract

**Files:**
- Modify: `pyproject.toml`
- Create: `src/cognitive_card_server/protocol.py`
- Test: `tests/test_protocol.py`

- [ ] **Step 1: Write failing capability tests**

Create `tests/test_protocol.py` with tests that assert:

```python
import unittest

from cognitive_card_server.protocol import (
    CapabilityDocument,
    ProtocolError,
    require_compatible_client,
)


class ProtocolTests(unittest.TestCase):
    def test_capability_document_is_stable(self) -> None:
        payload = CapabilityDocument.current().to_dict()
        self.assertEqual(payload["schema"], "cognitive-card-capabilities-v1")
        self.assertEqual(payload["protocol"], {"minimum": 1, "maximum": 1})
        self.assertFalse(payload["features"]["free_form_job_creation"])

    def test_old_skill_is_rejected_before_work(self) -> None:
        with self.assertRaisesRegex(ProtocolError, "CLIENT_UPGRADE_REQUIRED"):
            require_compatible_client(protocol=1, skill_release="0.0.9")

    def test_newer_protocol_requires_server_upgrade(self) -> None:
        with self.assertRaisesRegex(ProtocolError, "SERVER_UPGRADE_REQUIRED"):
            require_compatible_client(protocol=2, skill_release="0.1.0")
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python3 -m unittest tests.test_protocol -v
```

Expected: import failure because `cognitive_card_server.protocol` does not exist.

- [ ] **Step 3: Implement the immutable protocol module**

Use frozen dataclasses and constants:

```python
SERVER_VERSION = "0.3.0"
PROTOCOL_MINIMUM = 1
PROTOCOL_MAXIMUM = 1
MINIMUM_SKILL_RELEASE = "0.1.0"
PACKET_SCHEMAS = ("cognitive-card-generation-packet-v1",)
RESULT_SCHEMAS = ("cognitive-card-generation-result-v1",)
```

Implement `CapabilityDocument.current()`, deterministic `to_dict()`, and `ProtocolError(code, message="")`. Implement semantic-version comparison without a packaging dependency: accept only `MAJOR.MINOR.PATCH` numeric strings; malformed versions raise `INVALID_SKILL_RELEASE`. Check protocol before Skill release and return the exact upgrade codes above.

Set the project version in `pyproject.toml` to `0.3.0` in the same commit so package and capability versions cannot diverge.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_protocol -v
python3 -m unittest discover -s tests -v
git add pyproject.toml src/cognitive_card_server/protocol.py tests/test_protocol.py
git commit -m "feat(protocol): add capability and compatibility contract"
```

### Task 2: Add Opaque Scoped Token Persistence

**Files:**
- Create: `src/cognitive_card_server/auth/__init__.py`
- Create: `src/cognitive_card_server/auth/model.py`
- Create: `src/cognitive_card_server/auth/repository.py`
- Test: `tests/test_auth_repository.py`

**Interfaces:**

```python
class Scope(str, Enum):
    READ = "read"
    SUBMIT = "submit"
    REVIEW = "review"
    ADMIN = "admin"

@dataclass(frozen=True)
class TokenRecord:
    token_id: str
    subject: str
    scopes: tuple[Scope, ...]
    secret_digest: str
    created_at: str
    expires_at: str | None
    revoked_at: str | None

@dataclass(frozen=True)
class TokenPrincipal:
    token_id: str
    subject: str
    scopes: frozenset[Scope]
```

- [ ] **Step 1: Write failing repository tests**

Cover migration idempotency, insert/read, deterministic sorted scopes, revocation timestamp, duplicate token ID rejection, and confirm a SQL dump contains only the digest—not a raw token or secret.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_auth_repository -v
```

Expected: import failure because the auth package does not exist.

- [ ] **Step 3: Implement the schema and repository**

Migration must create:

```sql
CREATE TABLE IF NOT EXISTS card_os_tokens (
  token_id TEXT PRIMARY KEY,
  subject TEXT NOT NULL,
  scopes_json TEXT NOT NULL,
  secret_digest TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT,
  revoked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_card_os_tokens_subject
  ON card_os_tokens(subject);
```

`SQLiteTokenRepository(database)` must use foreign keys, WAL, explicit write transactions, and expose `migrate()`, `insert(record)`, `get(token_id)`, `list_tokens()`, `revoke(token_id, revoked_at)`, and `close()`. Never accept a raw secret in any repository method.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_auth_repository -v
python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/auth tests/test_auth_repository.py
git commit -m "feat(auth): persist scoped Card OS tokens"
```

### Task 3: Add Token Issue, Authentication, Revocation, and CLI

**Files:**
- Create: `src/cognitive_card_server/auth/service.py`
- Create: `src/cognitive_card_server/auth/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_auth_service.py`
- Test: `tests/test_auth_cli.py`

- [ ] **Step 1: Write failing service and CLI tests**

Tests must prove:

- issued token matches `ccos_v1.<32 lowercase hex token_id>.<urlsafe secret>`;
- secret has at least 256 bits of randomness (`secrets.token_urlsafe(32)`);
- stored digest is `sha256(secret).hexdigest()` and raw token is absent from SQLite;
- `hmac.compare_digest` is used for digest comparison;
- invalid format, wrong secret, expiry, and revocation fail with `AUTH_INVALID`, `AUTH_EXPIRED`, and `AUTH_REVOKED`;
- `admin` implies all scopes, `submit` implies `read`, and `review` implies `read`;
- `issue` prints the raw token once; `list` never prints secret/digest; `revoke` does not accept a raw token.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_auth_service tests.test_auth_cli -v
```

Expected: missing service and CLI interfaces.

- [ ] **Step 3: Implement exact service behavior**

Expose:

```python
class TokenService:
    def issue(
        self,
        *,
        subject: str,
        scopes: frozenset[Scope],
        expires_at: str | None = None,
    ) -> tuple[str, TokenRecord]: ...

    def authenticate(self, raw_token: str, *, required: Scope) -> TokenPrincipal: ...
    def revoke(self, token_id: str) -> TokenRecord: ...
```

Reject blank/whitespace subjects, empty scopes, malformed RFC3339 UTC expiry, and expiry at or before issue time. Parse tokens with `raw_token.split(".", 2)`. Hash only the secret component. Apply scope implication before authorization but store only explicitly issued scopes.

CLI commands:

```bash
cognitive-card-auth --database /path/card-os.db issue --subject codex-macbook --scope submit --expires-at 2027-01-01T00:00:00Z
cognitive-card-auth --database /path/card-os.db list
cognitive-card-auth --database /path/card-os.db revoke --token-id <id>
```

Use JSON output for `list` and `revoke`. `issue` outputs one JSON object containing `token`, `token_id`, `subject`, `scopes`, and `expires_at`; send operator errors to stderr and return non-zero.

- [ ] **Step 4: Register the CLI and dependencies**

Add only the auth entry point in `pyproject.toml`:

```toml
[project.scripts]
cognitive-card-preflight = "cognitive_card_server.preflight.cli:main"
cognitive-card-auth = "cognitive_card_server.auth.cli:main"
```

- [ ] **Step 5: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_auth_service tests.test_auth_cli -v
python3 -m unittest discover -s tests -v
git add pyproject.toml src/cognitive_card_server/auth tests/test_auth_service.py tests/test_auth_cli.py
git commit -m "feat(auth): issue and revoke opaque Card OS tokens"
```

### Task 4: Add Durable Expiry Recovery and a Claimable Packet Query

**Files:**
- Modify: `src/cognitive_card_server/subscriber/policy.py`
- Modify: `src/cognitive_card_server/subscriber/repository.py`
- Modify: `src/cognitive_card_server/subscriber/service.py`
- Modify: `tests/test_subscriber_policy.py`
- Modify: `tests/test_subscriber_repository.py`
- Modify: `tests/test_subscriber_service.py`

- [ ] **Step 1: Write failing recovery-policy and repository tests**

Add exact recovery transitions:

```python
JobState.AWAITING_CLIENT_GENERATION -> JobState.CONTENT_LOCKED
JobState.CLIENT_GENERATING -> JobState.CONTENT_LOCKED
JobState.AWAITING_UPLOAD -> JobState.AWAITING_CLIENT_GENERATION
JobState.AWAITING_UPLOAD -> JobState.CONTENT_LOCKED
```

Extend `release_expired_leases_and_transition(now)` to recover both `client_generating` and `awaiting_upload`: clear claim/lease, transition to `awaiting_client_generation`, and append one `packet.lease_expired` audit event containing the previous client and previous job state.

Add:

```python
def expire_packets_and_transition(self, now: str) -> tuple[str, ...]: ...
```

Migrate `generation_packets` with nullable `expired_at TEXT` and add `expired_at: str | None = None` to the end of `PacketRecord`. For packets with `expired_at IS NULL` whose immutable `packet.expires_at <= now` while the job is `awaiting_client_generation`, `client_generating`, or `awaiting_upload`, set `expired_at=now`, clear claim/lease, transition the job to `content_locked`, and append one `packet.expired` event. The expired packet row remains immutable and cannot be claimed again; an admin must issue a new packet ID. Re-running recovery is idempotent, and an old expired row must never expire a newer active packet for the same job.

Tests must cover unclaimed expiry, expiry while generating, expiry after completion/while awaiting upload, restart before recovery, audit preservation, and rejection of any transition from later states such as `server_verifying`.

- [ ] **Step 2: Write failing query and service tests**

Add tests for this exact interface:

```python
def list_claimable_packets(
    self, *, now: str, limit: int = 20
) -> tuple[PacketRecord, ...]: ...
```

Assert the query returns only packets whose job is `awaiting_client_generation`, `claimed_by IS NULL`, `expired_at IS NULL`, and `packet.expires_at > now`; ordering is `(created_at, packet_id)`; limit accepts 1–100 and rejects other values with `INVALID_PACKET_LIMIT`.

At the service layer add:

```python
def recover_stale_work(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
    now = self._format_rfc3339(self._utc_now())
    expired_packets = self._repository.expire_packets_and_transition(now)
    expired_leases = self._repository.release_expired_leases_and_transition(now)
    return expired_packets, expired_leases

def list_available_packets(self, *, limit: int = 20) -> tuple[PacketRecord, ...]:
    self.recover_stale_work()
    return self._repository.list_claimable_packets(
        now=self._format_rfc3339(self._utc_now()), limit=limit
    )
```

`issue_packet(...)` must call `recover_stale_work()` before reading the job so an expired packet returns the job to `content_locked` and can be replaced with a new packet ID. `claim_packet(...)` must recover stale work before claim; the expired packet still returns `PACKET_EXPIRED` while the job is left usable for reissue.

Test that a client can complete, crash, exceed its lease, and another client can reclaim; that an expired unclaimed packet can be replaced by an admin; and that both recovery paths work after reconstructing repository/service objects against the same database.

- [ ] **Step 3: Verify RED**

```bash
python3 -m unittest tests.test_subscriber_policy tests.test_subscriber_repository tests.test_subscriber_service -v
```

Expected: missing recovery transitions/methods and query methods.

- [ ] **Step 4: Implement recovery and the minimal join query**

Use one read-only join between `generation_packets` and `subscriber_jobs`, ordered by `(created_at, packet_id)`. Because `expires_at` currently lives inside `payload_json`, decode rows through the existing `_packet_from_row`, parse expiry in Python, filter expired packets, and apply `limit` after filtering. Do not depend on SQLite JSON extensions and do not reimplement packet JSON parsing or state transitions.

- [ ] **Step 5: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_subscriber_policy tests.test_subscriber_repository tests.test_subscriber_service -v
python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/subscriber tests/test_subscriber_policy.py tests/test_subscriber_repository.py tests/test_subscriber_service.py
git commit -m "feat(subscriber): recover stale generation work"
```

### Task 5: Build the HTTP Boundary, Settings, and Public Routes

**Files:**
- Create: `src/cognitive_card_server/http/__init__.py`
- Create: `src/cognitive_card_server/http/config.py`
- Create: `src/cognitive_card_server/http/schemas.py`
- Create: `src/cognitive_card_server/http/serialization.py`
- Create: `src/cognitive_card_server/http/errors.py`
- Create: `src/cognitive_card_server/http/app.py`
- Create: `src/cognitive_card_server/http/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_http_public.py`
- Test: `tests/test_http_auth.py`

**Settings:**

```python
@dataclass(frozen=True)
class ApiSettings:
    database: Path
    candidate_root: Path
    host: str = "127.0.0.1"
    port: int = 8765
    max_request_bytes: int = 28 * 1024 * 1024
    max_decoded_payload_bytes: int = 20 * 1024 * 1024
```

`build_parser()` performs no environment access so `--help` works with an empty environment. `parse_settings(namespace, environ)` applies CLI values first and environment fallbacks second; `database` and `candidate_root` are required only after both sources are merged. Environment names are `CARD_OS_DATABASE`, `CARD_OS_CANDIDATE_ROOT`, `CARD_OS_HOST`, `CARD_OS_PORT`, `CARD_OS_MAX_REQUEST_BYTES`, and `CARD_OS_MAX_DECODED_PAYLOAD_BYTES`. Reject relative paths and invalid integer ranges. Do not create directories while parsing settings.

- [ ] **Step 1: Install the declared transport test dependencies**

Add the runtime, test extra, and API entry point to `pyproject.toml` now:

```toml
[project]
dependencies = [
  "fastapi>=0.115,<1",
  "Pillow>=11,<13",
  "uvicorn>=0.30,<1",
]

[project.optional-dependencies]
test = ["httpx>=0.27,<1"]

[project.scripts]
cognitive-card-preflight = "cognitive_card_server.preflight.cli:main"
cognitive-card-auth = "cognitive_card_server.auth.cli:main"
cognitive-card-api = "cognitive_card_server.http.cli:main"
```

Install the project before importing the HTTP tests:

```bash
python3 -m pip install -e '.[test]'
```

- [ ] **Step 2: Write failing public and boundary tests**

Use `fastapi.testclient.TestClient` with a temporary database and candidate root. Assert:

- health and capabilities are public and deterministic;
- protected route without bearer token returns 401 `AUTH_REQUIRED`;
- bad token returns 401 `AUTH_INVALID`;
- missing scope returns 403 `AUTH_SCOPE_REQUIRED`;
- revoked token returns 403 `AUTH_REVOKED` immediately;
- expired token returns 401 `AUTH_EXPIRED` with `WWW-Authenticate: Bearer`;
- missing protocol headers return 426 `CLIENT_UPGRADE_REQUIRED`;
- all responses echo a valid supplied `X-Request-ID` or generate one;
- `Content-Length` above the configured limit returns 413 `REQUEST_TOO_LARGE` before JSON parsing;
- a direct ASGI harness sends multiple `http.request` frames without `Content-Length`, crosses the configured limit, and receives one 413 stable envelope before route parsing;
- no response contains traceback, raw token, token-secret digest, database path, or candidate-root path; public contract digests such as content-lock, packet, and result digests remain present where specified.
- unknown routes, wrong methods, disabled documentation routes, request-validation failures, and middleware 413 responses all use the stable error envelope and request ID.
- `cognitive-card-api --help` exits 0 when all `CARD_OS_*` variables are absent.

A caller request ID is accepted only when it matches `^[A-Za-z0-9._-]{8,64}$`; otherwise generate a 32-character lowercase UUID hex value. All 401 responses include `WWW-Authenticate: Bearer`.

- [ ] **Step 3: Verify RED**

```bash
python3 -m unittest tests.test_http_public tests.test_http_auth -v
```

Expected: HTTP package imports fail.

- [ ] **Step 4: Implement request-scoped dependencies**

Create `create_app(settings: ApiSettings, now: Callable[[], datetime] | None = None) -> FastAPI`. On startup, run subscriber and token migrations once. For every protected request:

1. open a new `SQLiteTokenRepository` and authenticate the bearer token;
2. run protocol compatibility before route logic;
3. open a new `SQLiteSubscriberRepository` and `CandidateStore` only when required;
4. close every repository/store in dependency `finally` blocks.

Never share the existing SQLite connection object across TestClient/Uvicorn threads.

Implement a pure ASGI `RequestSizeLimitMiddleware`: reject an oversized valid `Content-Length` before route dispatch, wrap `receive`, count every `http.request` body chunk, and emit 413 as soon as cumulative bytes exceed the configured limit. Add Pydantic `max_length` constraints for every base64 string and enforce the decoded-payload limit after strict decoding. This combination must cover both declared-length and chunked bodies.

Construct FastAPI with `docs_url=None`, `redoc_url=None`, and `openapi_url=None`; health and capabilities are the only public routes in this slice. Tests may inspect `app.openapi()` in process, but the schema is not served anonymously.

- [ ] **Step 5: Implement stable error translation**

Map exact classes/codes:

| Condition | HTTP | Code |
| --- | ---: | --- |
| Missing/invalid bearer | 401 | `AUTH_REQUIRED` / `AUTH_INVALID` |
| Expired bearer | 401 | `AUTH_EXPIRED` |
| Missing scope/revoked | 403 | `AUTH_SCOPE_REQUIRED` / `AUTH_REVOKED` |
| Missing job/packet/token | 404 | existing `*_NOT_FOUND` |
| Lease/state/claim/idempotency conflict | 409 | existing domain code |
| Packet expired | 410 | `PACKET_EXPIRED` |
| Bad shape/base64/media/size | 400 | stable validation code |
| Body/decoded payload too large | 413 | `REQUEST_TOO_LARGE` / `PAYLOAD_TOO_LARGE` |
| Unsupported JSON media type | 415 | `UNSUPPORTED_MEDIA_TYPE` |
| Client/server incompatibility | 426 | protocol error code |
| Unexpected exception | 500 | `INTERNAL_ERROR` |

Register handlers for `DomainError`, `ProtocolError`, `starlette.exceptions.HTTPException`, FastAPI request validation, and unexpected exceptions. Translate framework 404 and 405 to `ROUTE_NOT_FOUND` and `METHOD_NOT_ALLOWED`. Middleware-generated 413 must call the same envelope serializer. Log only request ID, route, status, stable code, token ID, and subject; never log authorization headers or request bodies.

- [ ] **Step 6: Add public routes and the launcher**

Router-relative `GET /health` and `GET /capabilities` are mounted under `/card-os/api/v1`, producing the full paths in the endpoint table. Health returns `{"status":"ok","server_version":"0.3.0"}` and capabilities returns `CapabilityDocument.current().to_dict()`.

The launcher uses `argparse`, supports `--host`, `--port`, `--database`, and `--candidate-root` overrides, and exits after ordinary `--help` before reading the environment. After merging CLI overrides with environment settings, it calls:

```python
def main() -> int:
    namespace = build_parser().parse_args()
    settings = parse_settings(namespace, os.environ)
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1",
    )
    return 0
```

TLS terminates at the later Nginx deployment; Uvicorn binds `127.0.0.1` by default.

- [ ] **Step 7: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_http_public tests.test_http_auth -v
python3 -m unittest discover -s tests -v
git add pyproject.toml src/cognitive_card_server/http tests/test_http_public.py tests/test_http_auth.py
git commit -m "feat(http): add versioned API boundary and public discovery"
```

### Task 6: Add Admin Import and Read Routes

**Files:**
- Modify: `src/cognitive_card_server/http/schemas.py`
- Modify: `src/cognitive_card_server/http/serialization.py`
- Modify: `src/cognitive_card_server/http/app.py`
- Test: `tests/test_http_admin.py`
- Modify: `tests/test_subscriber_repository.py`
- Modify: `tests/test_subscriber_service.py`

**Locked job body:**

```json
{
  "job_id": "job_rabbit_v02",
  "content_lock_digest": "sha256:<64 lowercase hex>",
  "registry_commit": "<7-64 lowercase hex>",
  "template_fingerprint": "sha256:<64 lowercase hex>",
  "age_profile": "age-5-6",
  "execution_profile": "client_subscription_interactive"
}
```

**Packet body:**

```json
{
  "packet_id": "gp_rabbit_cn_obs",
  "stage": "bilingual_projection",
  "language_projection": "cn-observation",
  "instructions": ["Use only declared propositions."],
  "required_outputs": [
    {"relative_path":"cards/cn-observation.json","media_type":"application/json","max_bytes":65536}
  ],
  "forbidden_changes": ["facts","certainty","template-family"],
  "input_artifacts": []
}
```

- [ ] **Step 1: Write failing admin/read tests**

Cover admin success, exact field validation, duplicate IDs as 409, non-admin denial, public denial, job read, ordered event read, packet read, and response serialization with no internal storage paths.

Every Pydantic request model uses `ConfigDict(extra="forbid", strict=True)`. Schema fields use `Literal[...]`, enum fields reject unknown values, and tests prove extra `client_id`, `packet_id`, credentials, and unknown fields fail with 400 rather than being silently ignored.

Add direct subscriber tests for repository/service actor defaults and authenticated actor propagation. Translate SQLite uniqueness violations inside repository methods to `JOB_ALREADY_EXISTS` and `PACKET_ALREADY_EXISTS`; no raw `sqlite3.IntegrityError` may cross the repository boundary. Make `list_events(job_id)` call `get_job(job_id)` first so a nonexistent job returns `JOB_NOT_FOUND`, not an empty successful list.

Packet issuance rejects required-output media types outside the global allowlist with `UNSUPPORTED_ARTIFACT_MEDIA_TYPE`; no invalid packet may enter the database even from an admin route.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_http_admin tests.test_subscriber_repository tests.test_subscriber_service -v
```

Expected: routes return 404.

- [ ] **Step 3: Implement routes only through existing domain methods**

Create locked jobs with `repository.create_locked_job(...)`; issue packets with `SubscriberExecutionService.issue_packet(...)`; retrieve jobs/events/packets with repository/service methods. Do not reproduce transition checks in route handlers. Add keyword-only `actor: str = "server"` to `create_locked_job(...)` and `issue_packet(...)`, pass it through every created audit event, and have admin routes pass `principal.subject`. Preserve the default so existing direct callers and tests stay compatible.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_http_admin tests.test_subscriber_repository tests.test_subscriber_service -v
python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/http src/cognitive_card_server/subscriber tests/test_http_admin.py tests/test_subscriber_repository.py tests/test_subscriber_service.py
git commit -m "feat(api): expose locked job and packet administration"
```

### Task 7: Add Subscriber List, Claim, Complete, and Result Routes

**Files:**
- Modify: `src/cognitive_card_server/http/schemas.py`
- Modify: `src/cognitive_card_server/http/serialization.py`
- Modify: `src/cognitive_card_server/http/app.py`
- Create: `src/cognitive_card_server/subscriber/media.py`
- Modify: `src/cognitive_card_server/subscriber/candidate_store.py`
- Modify: `src/cognitive_card_server/subscriber/repository.py`
- Modify: `src/cognitive_card_server/subscriber/service.py`
- Test: `tests/test_http_subscriber.py`
- Create: `tests/test_subscriber_media.py`
- Modify: `tests/test_subscriber_candidate_store.py`
- Modify: `tests/test_subscriber_repository.py`
- Modify: `tests/test_subscriber_service.py`

**Result body:**

```json
{
  "schema": "cognitive-card-generation-result-v1",
  "content_lock_digest": "sha256:<64 lowercase hex>",
  "skill_release": "0.1.0",
  "client_surface": "codex",
  "generated_at": "2026-07-13T10:30:00Z",
  "artifacts": [
    {
      "relative_path": "cards/cn-observation.json",
      "media_type": "application/json",
      "sha256": "<64 lowercase hex>",
      "size_bytes": 123,
      "payload_base64": "ey4uLn0="
    }
  ],
  "source_records": [],
  "operator_notes": ""
}
```

`packet_id` comes from the URL and `client_id` comes from the authenticated principal; neither appears as caller-controlled body identity.

- [ ] **Step 1: Write failing route tests**

Cover:

- sorted available list and `limit` validation;
- same-client claim replay and competing-client conflict;
- lease duration bounds 60–3600 seconds;
- completion by lease owner only;
- strict `base64.b64decode(value, validate=True)`;
- every result model forbids extra fields and requires `schema=Literal["cognitive-card-generation-result-v1"]`;
- declared size/digest/media/path verification through the existing ingestion service;
- total decoded size and 16-artifact limits;
- `Idempotency-Key` required, 8–128 visible ASCII characters;
- same idempotency key/same request returns the original receipt with `replayed=true`;
- same key/different request returns 409;
- token subject/result identity cannot be forged;
- result `skill_release` must equal the already validated `X-Card-OS-Skill-Release`; server stores the validated header value and rejects mismatch with `SKILL_RELEASE_MISMATCH`;
- non-identity `Content-Encoding`, archive/compressed artifact declarations, and media types outside the global allowlist are rejected before candidate staging;
- images exceeding any dimension, pixel, estimated decoded-byte, or 250:1 ratio limit are rejected with `UNSAFE_ARTIFACT_COMPRESSION`; malformed or format-mismatched images are rejected with `INVALID_ARTIFACT_MEDIA`; ordinary bounded PNG/JPEG/WebP fixtures pass;
- idempotency, packet ownership, packet/lease expiry, content-lock identity, job state, and transition guards are all checked inside the repository write transaction before the candidate-staging callback runs; conflicting or concurrently losing requests leave candidate-store contents byte-for-byte unchanged;
- revoked token cannot claim, complete, or submit.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_http_subscriber tests.test_subscriber_media tests.test_subscriber_candidate_store tests.test_subscriber_repository tests.test_subscriber_service -v
```

Expected: subscriber routes return 404.

- [ ] **Step 3: Implement serialization and route orchestration**

Convert decoded artifacts into the existing `ArtifactSubmission` and `GenerationResult`, then call `SubscriberExecutionService.submit_result`. Return a receipt with packet ID, result digest, staged artifact metadata, accepted timestamp, and replay flag. Do not return candidate-root paths or raw bytes.

Validate the request header release once, compare the body field to it, and construct `GenerationResult.skill_release` from that validated header. Reject `Content-Encoding` other than absent or `identity`, client PDF, and archive/compressed media.

Implement `require_safe_artifact_media(media_type: str, payload: bytes)`: text/JSON return after existing byte limits; images open from `BytesIO` with Pillow, reject `DecompressionBombWarning`/`DecompressionBombError`, validate observed format against declared media type, compute estimated decoded bytes from dimensions and band count, enforce all global image limits, then call `Image.verify()`. Do not render or transcode the image.

Add pure `CandidateStore.describe(payload) -> StagedCandidate`, returning deterministic content-addressed metadata without writing. Extend repository acceptance to receive expected staged metadata plus a staging callback. Inside one `BEGIN IMMEDIATE` transaction, in this order: calculate the request digest; resolve idempotency replay/conflict; reload packet/job; require `expired_at IS NULL`, packet and lease later than `now`, matching claim owner/content lock, job state `awaiting_upload`, and an allowed `server_verifying` transition; only then invoke the staging callback; require its returned metadata to equal the expected metadata; insert the result; transition the job. The service verifies artifacts/media, calls `describe`, and supplies the callback that performs actual `stage`. Tests synchronize two submissions with different idempotency keys against the same packet: the winner commits, the loser gets a stable state conflict, and the loser's unique payload never appears in candidate storage. This preserves durable bytes before database commit while preventing all known conflict/state failures from writing unreferenced candidate objects.

Available/packet responses include the immutable packet document, `packet_digest`, `claimed_by`, `lease_expires_at`, and `created_at`. A `submit` principal may see only its own active claim or an unclaimed packet; an `admin` principal may inspect all packets.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_http_subscriber tests.test_subscriber_media tests.test_subscriber_candidate_store tests.test_subscriber_repository tests.test_subscriber_service -v
python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/http src/cognitive_card_server/subscriber tests/test_http_subscriber.py tests/test_subscriber_media.py tests/test_subscriber_candidate_store.py tests/test_subscriber_repository.py tests/test_subscriber_service.py
git commit -m "feat(api): expose subscriber packet exchange"
```

### Task 8: Prove Restart Recovery, Packaging, and Operator Documentation

**Files:**
- Create: `tests/test_http_integration.py`
- Modify: `README.md`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the end-to-end restart test**

The fixture must:

1. issue admin and submit tokens;
2. create a locked job and packet over HTTP;
3. list and claim as the subscriber;
4. close the first TestClient;
5. construct a new app/TestClient against the same database and candidate root;
6. complete and submit a valid artifact;
7. replay the same idempotency key after another restart;
8. assert one result row, one staged content object, stable receipt digest, ordered audit events, and no credential material in database or logs.
9. repeat the flow with a completed generation whose lease expires across restart, proving another client can reclaim and submit;
10. expire an unclaimed packet across restart, prove the job returns to `content_locked`, and issue a replacement packet with a new ID.

Add a real loopback Uvicorn concurrency test using two independent `httpx.Client` instances and a `threading.Barrier`: both clients claim the same available packet simultaneously; assert exactly one 200, exactly one 409 `PACKET_ALREADY_CLAIMED`, one lease owner, and one `packet.claimed` audit event. Start on an OS-assigned loopback port and shut the server down in `finally`.

- [ ] **Step 2: Verify RED or missing documentation**

```bash
python3 -m unittest tests.test_http_integration -v
```

Expected before completion: missing integration fixture or failed restart assertions.

- [ ] **Step 3: Add operator documentation**

README must include:

- virtual environment install with `pip install -e '.[test]'`;
- required environment variables;
- token issue/revoke examples;
- local `cognitive-card-api` launch;
- `curl` examples for capabilities, locked-job import, packet issue/list/claim/complete/result;
- explicit statement that free-form concept compilation is unavailable in `0.3.0`;
- explicit statement that Nginx/TLS/systemd deployment is a later plan.

- [ ] **Step 4: Verify package entry points and full suite**

```bash
python3 -m pip install -e '.[test]'
cognitive-card-auth --help
env -u CARD_OS_DATABASE -u CARD_OS_CANDIDATE_ROOT cognitive-card-api --help
python3 -m unittest discover -s tests -v
git diff --check
```

Expected: all commands exit 0; API `--help` must not start the server.

- [ ] **Step 5: Commit the completed slice**

```bash
git add README.md pyproject.toml tests/test_http_integration.py
git commit -m "docs(api): document remote subscriber workflow"
```

---

## Final Verification Gate

- [ ] Run `python3 -m unittest discover -s tests -v` twice from a clean process.
- [ ] Run `git diff --check` and confirm `git status --short` is empty.
- [ ] Confirm package version and capability `server_version` are both `0.3.0`.
- [ ] Confirm no endpoint accepts `topic`, `concept`, ChatGPT identity, OpenAI credential, or caller-controlled `client_id`.
- [ ] Confirm raw issued tokens appear only in the CLI issue response and nowhere in SQLite, tests, logs, or committed fixtures.
- [ ] Confirm `/docs`, `/redoc`, and `/openapi.json` return 404, and in-process `app.openapi()` contains only the routes listed in this plan.
- [ ] Run a focused code review for auth bypass, request-size bypass, SQLite connection sharing, state-machine duplication, result idempotency, and secret disclosure.
- [ ] Update `/Users/admin/Documents/kids-visual-learning-pack/docs/cognitive-card-os-roadmap.md` only after evidence exists: mark `PROTO-01` `DONE`; keep `API-01` `IN PROGRESS` because free-form normalized task creation is absent; keep `AUTH-01` `IN PROGRESS` because browser sessions are absent; record the completed locked-job API and machine-token slices, and keep `SKILL-02` blocked until the thin client is implemented.
