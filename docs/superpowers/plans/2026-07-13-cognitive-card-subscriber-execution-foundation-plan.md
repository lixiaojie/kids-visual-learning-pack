# Cognitive Card Subscriber Execution Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a durable, API-independent server domain that can pause a Cognitive Card job for ChatGPT Pro/Codex client generation, lease a locked packet, verify an idempotent result upload, and resume after client or server interruption without requiring an OpenAI API key.

**Architecture:** Extend the existing Python server project with immutable subscriber-execution contracts, an explicit state-transition policy, a transactional SQLite repository, expiring client leases, and digest-verified candidate ingestion. Keep this layer independent from HTTP, MCP, the thin Skill, rendering, and provider APIs so every later adapter shares one tested application service.

**Tech Stack:** Python 3.11+ standard library, `sqlite3`, `dataclasses`, `enum`, `hashlib`, `json`, `unittest`, Git.

## Global Constraints

- Source specification: `/Users/admin/Documents/kids-visual-learning-pack/docs/superpowers/specs/2026-07-13-cognitive-card-pro-subscriber-execution-design.md`.
- Implementation repository: `/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server`.
- Default execution profile is exactly `client_subscription_interactive`.
- No OpenAI API key, ChatGPT cookie, browser session, or internal OpenAI token may be read, stored, accepted, or required.
- This plan performs no live SSH, server deployment, DNS, TLS, Nginx, firewall, systemd, Docker, or production-database changes.
- Keep the package dependency-free; do not add FastAPI, an MCP SDK, a queue, or an ORM in this slice.
- SQLite writes use explicit transactions, foreign keys, WAL mode, and UTC timestamps.
- Verified candidate bytes are durably staged on the server before their database acceptance record commits.
- Immutable packet and result schemas are `cognitive-card-generation-packet-v1` and `cognitive-card-generation-result-v1`.
- Every state change and profile change writes an append-only audit event.
- Run the full suite before every commit: `PYTHONPATH=src python3 -m unittest discover -s tests -v`.

---

## File Map

- Create `src/cognitive_card_server/subscriber/__init__.py` — public subscriber-domain exports.
- Create `src/cognitive_card_server/subscriber/errors.py` — stable domain error codes and exception type.
- Create `src/cognitive_card_server/subscriber/model.py` — enums and immutable packet/result/job records.
- Create `src/cognitive_card_server/subscriber/policy.py` — allowed job-state transitions.
- Create `src/cognitive_card_server/subscriber/repository.py` — transactional SQLite schema and persistence.
- Create `src/cognitive_card_server/subscriber/service.py` — packet issue/claim/lease/result application service.
- Create `src/cognitive_card_server/subscriber/ingestion.py` — path, media type, size, and SHA-256 verification.
- Create `src/cognitive_card_server/subscriber/candidate_store.py` — durable content-addressed candidate staging.
- Create `tests/test_subscriber_model.py` — contract serialization tests.
- Create `tests/test_subscriber_policy.py` — transition-policy tests.
- Create `tests/test_subscriber_repository.py` — migration, persistence, audit, and uniqueness tests.
- Create `tests/test_subscriber_service.py` — lease expiry and resumability tests.
- Create `tests/test_subscriber_ingestion.py` — digest, path, and idempotency tests.
- Create `tests/test_subscriber_integration.py` — complete no-API-key subscriber fixture.

### Task 1: Define Immutable Contracts and State Policy

**Files:**
- Create: `src/cognitive_card_server/subscriber/__init__.py`
- Create: `src/cognitive_card_server/subscriber/errors.py`
- Create: `src/cognitive_card_server/subscriber/model.py`
- Create: `src/cognitive_card_server/subscriber/policy.py`
- Test: `tests/test_subscriber_model.py`
- Test: `tests/test_subscriber_policy.py`

**Interfaces:**
- Produces: `ExecutionProfile`, `JobState`, `GenerationStage`, `JobRecord`, `GenerationPacket`, `ArtifactDeclaration`, `ArtifactSubmission`, `GenerationResult`, `DomainError`, and `require_transition(current, target)`.
- Consumed later by: repository, service, ingestion, HTTP adapter, MCP adapter, and thin Skill client.

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_subscriber_model.py`:

```python
import json
import unittest

from cognitive_card_server.subscriber.model import (
    ArtifactDeclaration,
    ExecutionProfile,
    GenerationPacket,
    GenerationStage,
    JobState,
)


class SubscriberModelTests(unittest.TestCase):
    def test_packet_serializes_with_stable_machine_values(self) -> None:
        packet = GenerationPacket(
            packet_id="gp_rabbit_cn_obs",
            job_id="job_rabbit_v02",
            execution_profile=ExecutionProfile.CLIENT_SUBSCRIPTION_INTERACTIVE,
            stage=GenerationStage.BILINGUAL_PROJECTION,
            content_lock_digest="sha256:" + "a" * 64,
            registry_commit="0123456789abcdef",
            template_fingerprint="sha256:" + "b" * 64,
            age_profile="age-5-6",
            language_projection="cn-observation",
            instructions=("Use only declared propositions.",),
            required_outputs=(
                ArtifactDeclaration(
                    relative_path="cards/cn-observation.json",
                    media_type="application/json",
                    max_bytes=65536,
                ),
            ),
            forbidden_changes=("facts", "certainty", "template-family"),
            issued_at="2026-07-13T10:00:00Z",
            expires_at="2026-07-13T11:00:00Z",
        )
        payload = json.loads(packet.to_json())
        self.assertEqual(payload["schema"], "cognitive-card-generation-packet-v1")
        self.assertEqual(payload["execution_profile"], "client_subscription_interactive")
        self.assertEqual(payload["stage"], "bilingual_projection")
        self.assertNotIn("openai_api_key", payload)
        self.assertNotIn("chatgpt_cookie", payload)

    def test_first_release_profiles_are_explicit(self) -> None:
        self.assertEqual(
            {profile.value for profile in ExecutionProfile},
            {
                "client_subscription_interactive",
                "manual_upload",
                "server_api_autonomous",
            },
        )

    def test_subscriber_states_match_the_approved_state_machine(self) -> None:
        expected = {
            "draft", "input_validated", "content_locked",
            "awaiting_client_generation", "client_generating", "awaiting_upload",
            "server_verifying", "rendering", "validating", "awaiting_review",
            "published", "failed", "cancelled", "superseded",
        }
        self.assertEqual({state.value for state in JobState}, expected)
```

Create `tests/test_subscriber_policy.py`:

```python
import unittest

from cognitive_card_server.subscriber.errors import DomainError
from cognitive_card_server.subscriber.model import JobState
from cognitive_card_server.subscriber.policy import require_transition


class SubscriberPolicyTests(unittest.TestCase):
    def test_approved_subscriber_path_is_allowed(self) -> None:
        path = (
            JobState.CONTENT_LOCKED,
            JobState.AWAITING_CLIENT_GENERATION,
            JobState.CLIENT_GENERATING,
            JobState.AWAITING_UPLOAD,
            JobState.SERVER_VERIFYING,
            JobState.RENDERING,
        )
        for current, target in zip(path, path[1:]):
            require_transition(current, target)

    def test_client_upload_cannot_publish_directly(self) -> None:
        with self.assertRaisesRegex(DomainError, "INVALID_STATE_TRANSITION"):
            require_transition(JobState.SERVER_VERIFYING, JobState.PUBLISHED)

    def test_expired_lease_can_return_to_waiting(self) -> None:
        require_transition(JobState.CLIENT_GENERATING, JobState.AWAITING_CLIENT_GENERATION)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_subscriber_model tests.test_subscriber_policy -v
```

Expected: both modules fail to import because `cognitive_card_server.subscriber` does not exist.

- [ ] **Step 3: Implement the minimal contracts**

Create `errors.py`:

```python
class DomainError(ValueError):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message
        super().__init__(code if not message else f"{code}: {message}")
```

Create `model.py` with string enums using exactly these values:

```python
class ExecutionProfile(str, Enum):
    CLIENT_SUBSCRIPTION_INTERACTIVE = "client_subscription_interactive"
    MANUAL_UPLOAD = "manual_upload"
    SERVER_API_AUTONOMOUS = "server_api_autonomous"


class GenerationStage(str, Enum):
    SOURCE_RESEARCH = "source_research"
    SEMANTIC_DRAFT = "semantic_draft"
    BILINGUAL_PROJECTION = "bilingual_projection"
    IMAGE_GENERATION = "image_generation"


class JobState(str, Enum):
    DRAFT = "draft"
    INPUT_VALIDATED = "input_validated"
    CONTENT_LOCKED = "content_locked"
    AWAITING_CLIENT_GENERATION = "awaiting_client_generation"
    CLIENT_GENERATING = "client_generating"
    AWAITING_UPLOAD = "awaiting_upload"
    SERVER_VERIFYING = "server_verifying"
    RENDERING = "rendering"
    VALIDATING = "validating"
    AWAITING_REVIEW = "awaiting_review"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
```

Use frozen dataclasses. `GenerationPacket.to_dict()` must convert enums to `.value`, tuples to JSON arrays,
and required outputs to dictionaries; `to_json()` must use
`json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"`. Define result schema and
artifact fields exactly as follows:

```python
@dataclass(frozen=True)
class ArtifactDeclaration:
    relative_path: str
    media_type: str
    max_bytes: int


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    execution_profile: ExecutionProfile
    state: JobState
    content_lock_digest: str
    registry_commit: str
    template_fingerprint: str
    age_profile: str
    created_at: str
    updated_at: str
```

`GenerationPacket` uses the required fields shown in the test constructor in that order, followed by
`input_artifacts: tuple[str, ...] = ()` and
`schema: str = "cognitive-card-generation-packet-v1"`. Serialize `input_artifacts` as a JSON array.

```python
@dataclass(frozen=True)
class ArtifactSubmission:
    relative_path: str
    media_type: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class GenerationResult:
    packet_id: str
    content_lock_digest: str
    client_id: str
    skill_release: str
    client_surface: str
    generated_at: str
    artifacts: tuple[ArtifactSubmission, ...]
    source_records: tuple[dict[str, str], ...] = ()
    operator_notes: str = ""
    schema: str = "cognitive-card-generation-result-v1"
```

`policy.py` must define an explicit `ALLOWED_TRANSITIONS: dict[JobState, frozenset[JobState]]`. Include the
approved forward path, lease-expiry return, rejection return from `server_verifying` to
`awaiting_client_generation` or `awaiting_upload`, and transitions from every non-terminal state to `failed`,
`cancelled`, or `superseded`. Terminal states have no outgoing transitions. Raise
`DomainError("INVALID_STATE_TRANSITION", f"{current.value}->{target.value}")` on rejection.

Export the public types from `subscriber/__init__.py`.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_subscriber_model tests.test_subscriber_policy -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/subscriber tests/test_subscriber_model.py tests/test_subscriber_policy.py
git commit -m "feat: define subscriber execution contracts"
```

Expected: all tests pass and the commit contains no secret-shaped fields.

### Task 2: Persist Jobs, Packets, Leases, Results, and Audit Events

**Files:**
- Create: `src/cognitive_card_server/subscriber/repository.py`
- Test: `tests/test_subscriber_repository.py`

**Interfaces:**
- Consumes: Task 1 models and `require_transition`.
- Produces: `SQLiteSubscriberRepository` with `migrate()`, `create_locked_job()`, `get_job()`, `get_packet()`, `issue_packet_and_transition()`, `claim_packet_and_transition()`, `mark_awaiting_upload_and_transition()`, `accept_result_and_transition()`, `change_execution_profile()`, `find_result_by_idempotency_key()`, `release_expired_leases_and_transition()`, and `list_events()`.

Use these exact repository records and public signatures:

```python
@dataclass(frozen=True)
class PacketRecord:
    packet: GenerationPacket
    packet_digest: str
    claimed_by: str | None
    lease_expires_at: str | None
    created_at: str


@dataclass(frozen=True)
class AuditEvent:
    event_id: int
    job_id: str
    event_type: str
    actor: str
    reason: str
    details: dict[str, object]
    occurred_at: str


@dataclass(frozen=True)
class StoredResult:
    result_id: int
    result: GenerationResult
    idempotency_key: str
    request_digest: str
    staged_artifacts: tuple[dict[str, object], ...]
    accepted_at: str
    replayed: bool
```

```python
create_locked_job(*, job_id, content_lock_digest, registry_commit,
                  template_fingerprint, age_profile, now,
                  execution_profile=ExecutionProfile.CLIENT_SUBSCRIPTION_INTERACTIVE) -> JobRecord
get_job(job_id: str) -> JobRecord
get_packet(packet_id: str) -> PacketRecord
issue_packet_and_transition(packet: GenerationPacket, *, actor: str, reason: str, now: str) -> PacketRecord
claim_packet_and_transition(packet_id: str, client_id: str, lease_expires_at: str, *,
                            actor: str, reason: str, now: str) -> PacketRecord
mark_awaiting_upload_and_transition(packet_id: str, client_id: str, *,
                                    actor: str, reason: str, now: str) -> PacketRecord
accept_result_and_transition(result: GenerationResult, idempotency_key: str,
                             staged_artifacts: tuple[dict[str, object], ...], now: str) -> StoredResult
change_execution_profile(job_id: str, target: ExecutionProfile, *,
                         actor: str, reason: str, now: str) -> JobRecord
find_result_by_idempotency_key(idempotency_key: str) -> StoredResult | None
release_expired_leases_and_transition(now: str) -> tuple[str, ...]
list_events(job_id: str) -> tuple[AuditEvent, ...]
```

- [ ] **Step 1: Write failing repository tests**

Create `tests/test_subscriber_repository.py` using a temporary database and a fixed `now` value. Require:

```python
class SubscriberRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "subscriber.sqlite3"
        self.repo = SQLiteSubscriberRepository(self.db)
        self.repo.migrate()

    def tearDown(self) -> None:
        self.repo.close()
        self.temp.cleanup()

    def test_create_locked_job_uses_subscriber_profile(self) -> None:
        job = self.repo.create_locked_job(
            job_id="job_rabbit_v02",
            content_lock_digest="sha256:" + "a" * 64,
            registry_commit="0123456789abcdef",
            template_fingerprint="sha256:" + "b" * 64,
            age_profile="age-5-6",
            now="2026-07-13T10:00:00Z",
        )
        self.assertEqual(job.state, JobState.CONTENT_LOCKED)
        self.assertEqual(
            job.execution_profile,
            ExecutionProfile.CLIENT_SUBSCRIPTION_INTERACTIVE,
        )

    def test_packet_issue_and_state_change_are_audited_atomically(self) -> None:
        self._create_job()
        self.repo.issue_packet_and_transition(
            self._packet(),
            actor="server",
            reason="packet-issued",
            now="2026-07-13T10:01:00Z",
        )
        events = self.repo.list_events("job_rabbit_v02")
        self.assertEqual(
            [event.event_type for event in events],
            ["job.created", "packet.issued", "job.transitioned"],
        )
        self.assertEqual(self.repo.get_job("job_rabbit_v02").state, JobState.AWAITING_CLIENT_GENERATION)

    def test_duplicate_idempotency_key_is_unique(self) -> None:
        self._prepare_packet_and_claim()
        self.repo.accept_result_and_transition(
            self._result(), "idem-rabbit-1", (), "2026-07-13T10:05:00Z"
        )
        with self.assertRaisesRegex(DomainError, "IDEMPOTENCY_CONFLICT"):
            self.repo.accept_result_and_transition(
                self._different_result(), "idem-rabbit-1", (), "2026-07-13T10:06:00Z"
            )

    def test_profile_change_is_audited_and_autonomous_mode_is_blocked(self) -> None:
        self._create_job()
        self.repo.change_execution_profile(
            "job_rabbit_v02",
            ExecutionProfile.MANUAL_UPLOAD,
            actor="owner",
            reason="browser-fallback",
            now="2026-07-13T10:03:00Z",
        )
        self.assertEqual(
            self.repo.get_job("job_rabbit_v02").execution_profile,
            ExecutionProfile.MANUAL_UPLOAD,
        )
        self.assertEqual(self.repo.list_events("job_rabbit_v02")[-1].event_type, "profile.changed")
        with self.assertRaisesRegex(DomainError, "PROVIDER_CREDENTIAL_REQUIRED"):
            self.repo.change_execution_profile(
                "job_rabbit_v02",
                ExecutionProfile.SERVER_API_AUTONOMOUS,
                actor="owner",
                reason="not-configured",
                now="2026-07-13T10:04:00Z",
            )
```

The helper methods create one job, packet, and claim using concrete rabbit IDs and the Task 1 dataclasses.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH=src python3 -m unittest tests.test_subscriber_repository -v`.

Expected: import failure for `subscriber.repository`.

- [ ] **Step 3: Implement the SQLite schema and transaction boundary**

`migrate()` creates these tables and indexes in one transaction:

```sql
CREATE TABLE IF NOT EXISTS subscriber_jobs (
  job_id TEXT PRIMARY KEY,
  execution_profile TEXT NOT NULL,
  state TEXT NOT NULL,
  content_lock_digest TEXT NOT NULL,
  registry_commit TEXT NOT NULL,
  template_fingerprint TEXT NOT NULL,
  age_profile TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generation_packets (
  packet_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES subscriber_jobs(job_id),
  payload_json TEXT NOT NULL,
  packet_digest TEXT NOT NULL UNIQUE,
  claimed_by TEXT,
  lease_expires_at TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generation_results (
  result_id INTEGER PRIMARY KEY AUTOINCREMENT,
  packet_id TEXT NOT NULL REFERENCES generation_packets(packet_id),
  idempotency_key TEXT NOT NULL UNIQUE,
  request_digest TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  staged_artifacts_json TEXT NOT NULL,
  accepted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriber_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL REFERENCES subscriber_jobs(job_id),
  event_type TEXT NOT NULL,
  actor TEXT NOT NULL,
  reason TEXT NOT NULL,
  details_json TEXT NOT NULL,
  occurred_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_packets_job ON generation_packets(job_id);
CREATE INDEX IF NOT EXISTS idx_events_job_order ON subscriber_events(job_id, event_id);
```

Open connections with `isolation_level=None`, execute `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL`, and
wrap writes in `BEGIN IMMEDIATE` / `COMMIT`, rolling back on any exception. Serialize JSON with stable key
ordering and compute packet/request digests from UTF-8 encoded canonical JSON.

`create_locked_job()` defaults only to `CLIENT_SUBSCRIPTION_INTERACTIVE`; attempting
`SERVER_API_AUTONOMOUS` raises `DomainError("PROVIDER_CREDENTIAL_REQUIRED")` in this release.

The compound methods named `*_and_transition` execute their record write, allowed state transition, and audit
events in one `BEGIN IMMEDIATE` transaction. Adapters and services must not compose those three operations from
separate public calls.

`accept_result_and_transition()` handles an existing idempotency key as follows:

- same request digest: return the existing result with `replayed=True`;
- different request digest: raise `DomainError("IDEMPOTENCY_CONFLICT")`.

Do not store any supplied dictionary key whose lowercase name contains `cookie`, `authorization`,
`openai_api_key`, or `chatgpt_token`; inspect nested dictionaries and lists recursively and reject them with
`DomainError("FORBIDDEN_CREDENTIAL_FIELD")`.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_subscriber_repository -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/subscriber/repository.py tests/test_subscriber_repository.py
git commit -m "feat: persist subscriber jobs and audit history"
```

Expected: repository tests pass against a real temporary SQLite database and previous preflight tests remain
green.

### Task 3: Implement Packet Issue, Claim, Lease Expiry, and Resume

**Files:**
- Create: `src/cognitive_card_server/subscriber/service.py`
- Test: `tests/test_subscriber_service.py`

**Interfaces:**
- Consumes: `SQLiteSubscriberRepository`, Task 1 dataclasses, and an injected UTC clock.
- Produces: `SubscriberExecutionService.issue_packet()`, `claim_packet()`, `mark_generation_complete()`, `release_expired_leases()`, and `get_job()`.

Use these exact public signatures:

```python
issue_packet(job_id: str, *, packet_id: str, stage: GenerationStage,
             language_projection: str, instructions: tuple[str, ...],
             required_outputs: tuple[ArtifactDeclaration, ...],
             forbidden_changes: tuple[str, ...],
             input_artifacts: tuple[str, ...] = ()) -> GenerationPacket
claim_packet(packet_id: str, client_id: str, *, lease_seconds: int = 900) -> PacketRecord
mark_generation_complete(packet_id: str, client_id: str) -> PacketRecord
release_expired_leases() -> tuple[str, ...]
get_job(job_id: str) -> JobRecord
```

`issue_packet()` uses the injected current time as `issued_at`, sets `expires_at` to exactly one hour later,
and copies execution profile, content-lock digest, registry commit, template fingerprint, and age profile from
the stored job rather than accepting those identities from the caller. It uses actor `server` and reason
`packet-issued`. Claim uses actor `client_id` and reason `packet-claimed`; generation completion uses actor
`client_id` and reason `generation-completed`.

- [ ] **Step 1: Write failing lease tests**

Create `tests/test_subscriber_service.py` with a mutable fixed clock and require these behaviors:

```python
class SubscriberServiceTests(unittest.TestCase):
    def test_claim_moves_job_and_sets_bounded_lease(self) -> None:
        packet = self._issue_packet()
        claim = self.service.claim_packet(packet.packet_id, "client-macbook", lease_seconds=900)
        self.assertEqual(claim.packet.packet_id, packet.packet_id)
        self.assertEqual(claim.claimed_by, "client-macbook")
        self.assertEqual(claim.lease_expires_at, "2026-07-13T10:15:00Z")
        self.assertEqual(self.service.get_job("job_rabbit_v02").state, JobState.CLIENT_GENERATING)

    def test_second_client_cannot_steal_active_lease(self) -> None:
        packet = self._issue_packet()
        self.service.claim_packet(packet.packet_id, "client-macbook", lease_seconds=900)
        with self.assertRaisesRegex(DomainError, "PACKET_ALREADY_CLAIMED"):
            self.service.claim_packet(packet.packet_id, "client-ipad", lease_seconds=900)

    def test_expired_lease_returns_job_to_durable_waiting_state(self) -> None:
        packet = self._issue_packet()
        self.service.claim_packet(packet.packet_id, "client-macbook", lease_seconds=60)
        self.clock.set("2026-07-13T10:02:00Z")
        released = self.service.release_expired_leases()
        self.assertEqual(released, (packet.packet_id,))
        self.assertEqual(
            self.service.get_job("job_rabbit_v02").state,
            JobState.AWAITING_CLIENT_GENERATION,
        )
```

Also test lease durations below 60 or above 3600 seconds fail with `INVALID_LEASE_DURATION`, packet expiry
fails with `PACKET_EXPIRED`, a revoked client ID fails with `CLIENT_REVOKED`, and
`mark_generation_complete()` changes `client_generating` to `awaiting_upload` only for the active claimant.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH=src python3 -m unittest tests.test_subscriber_service -v`.

Expected: import failure for `subscriber.service`.

- [ ] **Step 3: Implement the application service**

Use constructor injection:

```python
class SubscriberExecutionService:
    def __init__(
        self,
        repository: SQLiteSubscriberRepository,
        now: Callable[[], datetime],
        revoked_clients: frozenset[str] = frozenset(),
    ) -> None:
        self._repository = repository
        self._now = now
        self._revoked_clients = revoked_clients
```

Use timezone-aware UTC datetimes internally and RFC 3339 `Z` strings at persistence boundaries.
If the injected clock returns a naive or non-UTC datetime, raise `DomainError("INVALID_UTC_CLOCK")` before a
repository mutation.

`issue_packet()` requires a job in `content_locked`, creates one packet with all required immutable identities,
saves it, and transitions to `awaiting_client_generation` in the same repository transaction.

`claim_packet()` must:

1. reject revoked or empty client IDs;
2. enforce `60 <= lease_seconds <= 3600`;
3. reject an expired packet;
4. reject another active claimant;
5. allow the same client to read its current claim without extending it;
6. set claimant and lease expiry atomically;
7. call `claim_packet_and_transition()` so the claim, transition to `client_generating`, and
   `packet.claimed`/`job.transitioned` events commit atomically.

`release_expired_leases()` delegates to `release_expired_leases_and_transition()`, which clears expired claims,
transitions associated `client_generating` jobs back to `awaiting_client_generation`, appends
`packet.lease_expired` and `job.transitioned`, and returns packet IDs sorted lexically in one transaction.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_subscriber_service -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/subscriber/service.py tests/test_subscriber_service.py
git commit -m "feat: lease subscriber generation packets"
```

Expected: lease and restart-safe state tests pass without sleeps or network access.

### Task 4: Verify and Ingest Client-Generated Candidate Artifacts

**Files:**
- Create: `src/cognitive_card_server/subscriber/candidate_store.py`
- Create: `src/cognitive_card_server/subscriber/ingestion.py`
- Modify: `src/cognitive_card_server/subscriber/service.py`
- Test: `tests/test_subscriber_ingestion.py`

**Interfaces:**
- Consumes: a claimed packet, `GenerationResult`, `Mapping[str, bytes]`, an idempotency key, and a server-owned staging root.
- Produces: `CandidateStore`, `verify_candidate_artifacts()`, and `SubscriberExecutionService.submit_result()` returning `ResultReceipt`.

Use these exact records and signatures:

```python
@dataclass(frozen=True)
class VerifiedArtifact:
    relative_path: str
    media_type: str
    sha256: str
    size_bytes: int
    payload: bytes


@dataclass(frozen=True)
class StagedCandidate:
    storage_key: str
    sha256: str
    size_bytes: int


verify_candidate_artifacts(
    packet: GenerationPacket,
    result: GenerationResult,
    payloads: Mapping[str, bytes],
) -> tuple[VerifiedArtifact, ...]

CandidateStore(root: Path)
CandidateStore.stage(payload: bytes) -> StagedCandidate
CandidateStore.read(storage_key: str) -> bytes

SubscriberExecutionService.submit_result(
    result: GenerationResult,
    payloads: Mapping[str, bytes],
    *,
    idempotency_key: str,
    client_id: str,
) -> ResultReceipt
```

Extend the service constructor with
`candidate_store: CandidateStore | None = None` after `revoked_clients`; existing Task 3 callers remain valid.
Calling `submit_result()` without a configured store raises `DomainError("CANDIDATE_STORE_REQUIRED")` before
any repository mutation.

- [ ] **Step 1: Write failing ingestion tests**

Create `tests/test_subscriber_ingestion.py`. Build one packet declaring
`cards/cn-observation.json` as `application/json` with maximum 65,536 bytes. Require:

```python
class SubscriberIngestionTests(unittest.TestCase):
    def test_valid_result_is_digest_verified_and_idempotent(self) -> None:
        body = b'{"proposition_ids":["rabbit.appearance.ears"]}\n'
        result = self._result(body)
        first = self.service.submit_result(
            result,
            {"cards/cn-observation.json": body},
            idempotency_key="idem-rabbit-cn-obs-1",
            client_id="client-macbook",
        )
        second = self.service.submit_result(
            result,
            {"cards/cn-observation.json": body},
            idempotency_key="idem-rabbit-cn-obs-1",
            client_id="client-macbook",
        )
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.result_digest, second.result_digest)
        self.assertEqual(self.service.get_job("job_rabbit_v02").state, JobState.SERVER_VERIFYING)
        self.assertEqual(
            self.candidate_store.read(first.staged_artifacts[0].storage_key),
            body,
        )

    def test_wrong_content_lock_is_rejected(self) -> None:
        with self.assertRaisesRegex(DomainError, "CONTENT_LOCK_MISMATCH"):
            self.service.submit_result(
                replace(self._result(b"{}"), content_lock_digest="sha256:" + "f" * 64),
                {"cards/cn-observation.json": b"{}"},
                idempotency_key="idem-wrong-lock",
                client_id="client-macbook",
            )

    def test_path_traversal_and_undeclared_file_are_rejected(self) -> None:
        for path, code in (
            ("../escape.json", "UNSAFE_ARTIFACT_PATH"),
            ("cards/extra.json", "UNDECLARED_ARTIFACT"),
        ):
            with self.subTest(path=path):
                with self.assertRaisesRegex(DomainError, code):
                    verify_candidate_artifacts(self.packet, self._result_for_path(path), {path: b"{}"})
```

Also cover `ARTIFACT_DIGEST_MISMATCH`, `ARTIFACT_SIZE_MISMATCH`, `ARTIFACT_TOO_LARGE`,
`ARTIFACT_MEDIA_TYPE_MISMATCH`, `MISSING_ARTIFACT`, `RESULT_CLIENT_MISMATCH`, `PACKET_EXPIRED`, and an
idempotency-key replay with different bytes producing `IDEMPOTENCY_CONFLICT`. Close and reopen both the
repository and `CandidateStore`, then prove accepted bytes are still readable by their storage key.

- [ ] **Step 2: Verify RED**

Run `PYTHONPATH=src python3 -m unittest tests.test_subscriber_ingestion -v`.

Expected: import failure for `subscriber.ingestion` or missing `submit_result`.

- [ ] **Step 3: Implement deterministic artifact verification**

`verify_candidate_artifacts(packet, result, payloads)` must:

- require exact equality between declared output paths, result paths, and payload keys;
- accept only POSIX relative paths with no empty segment, `.`, `..`, leading slash, backslash, NUL, or symlink
  interpretation;
- compare declared and submitted media type exactly;
- compare `size_bytes` to `len(payload)` and the declaration maximum;
- compare lowercase hexadecimal SHA-256 to `hashlib.sha256(payload).hexdigest()` using
  `hmac.compare_digest`;
- return artifacts sorted by relative path;
- never write bytes to the final asset tree in this slice.

Implement `CandidateStore(root: Path)` with storage keys
`sha256/<first-two-hex>/<64-hex-digest>`. `stage(payload)` must write to a same-directory random temporary file,
flush and `os.fsync()` the file, publish with an atomic no-clobber operation such as `os.link()`, fsync the
containing directory, and return a frozen `StagedCandidate(storage_key, sha256, size_bytes)`. If the digest
path already exists or wins a concurrent publication race, verify its size and digest and reuse it; never
overwrite an existing regular target. Reject symlinks and any resolved path outside `root`.
`read(storage_key)` re-verifies the digest before returning bytes.

Eliminate validation/use races by opening the configured root and shard directories with
`O_DIRECTORY | O_NOFOLLOW`, checking the opened root device/inode against the constructor identity, and
performing temporary creation, link, stat, open, unlink, and read relative to retained directory descriptors.
Do not reopen a validated shard through an absolute pathname. Open the accepted target with `O_NOFOLLOW`,
require a regular file, verify its size/digest, fsync that actual target inode, and fsync the shard directory
before returning on both new-publication and reuse/concurrent-winner paths.

Use stable store errors: `INVALID_STORAGE_KEY` for a key outside the exact digest-key grammar,
`UNSAFE_CANDIDATE_STORE` for root/prefix/target symlinks or root escape, and
`CANDIDATE_DIGEST_MISMATCH` when existing or read bytes do not match their key. Store construction may create a
missing real directory, but must reject a pre-existing symlink root. Temporary files must be removed on every
failed publication path.

`submit_result()` must require the active claimant, the matching packet and lock digest, an unexpired packet,
and job state `awaiting_upload`. It calls `accept_result_and_transition()` so the transition to
`server_verifying`, result metadata, verified candidate digests, idempotency identity, and audit events commit
transactionally. Stage every verified payload before opening the database acceptance transaction. A database
failure may leave an unreferenced content-addressed candidate, which is safe and is removed only by a later
garbage-collection plan. Never commit a result record before every declared byte payload is durably staged.
Return:

```python
@dataclass(frozen=True)
class ResultReceipt:
    packet_id: str
    result_digest: str
    staged_artifacts: tuple[StagedCandidate, ...]
    accepted_at: str
    replayed: bool
```

Candidate staging is durable but not published. The later immutable-asset-store plan will link accepted
candidates into logical artifacts and packages without changing their content digests.

Persist staged metadata sorted by logical relative path, with each dictionary containing exactly
`relative_path`, `storage_key`, `sha256`, and `size_bytes`. Set `ResultReceipt.result_digest` to the repository's
canonical accepted-request digest. An exact idempotency replay returns the original receipt identities with
`replayed=True` even though the job is already `server_verifying`; a different request under the same key still
raises `IDEMPOTENCY_CONFLICT`.

Look up the idempotency key before applying claimant, lease, packet-expiry, or `awaiting_upload` gates. If the
key does not exist, all first-acceptance gates apply before staging. If the key exists, deterministic packet,
lock, result, payload, digest, and staging verification still run, then the repository decides exact replay
versus `IDEMPOTENCY_CONFLICT`; current claimant, lease, packet expiry, and job state do not block that replay
decision.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_subscriber_ingestion -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
git add src/cognitive_card_server/subscriber/candidate_store.py src/cognitive_card_server/subscriber/ingestion.py src/cognitive_card_server/subscriber/service.py tests/test_subscriber_ingestion.py
git commit -m "feat: verify subscriber-generated artifacts"
```

Expected: all candidate validation and replay tests pass; no file is written outside temporary test
directories.

### Task 5: Prove the Complete No-API-Key Subscriber Flow

**Files:**
- Create: `tests/test_subscriber_integration.py`
- Modify: `src/cognitive_card_server/subscriber/__init__.py`
- Modify: `src/cognitive_card_server/subscriber/repository.py`
- Modify: `pyproject.toml`
- Modify: `tests/test_package.py`
- Modify: `tests/test_subscriber_service.py`

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: a stable public import surface and one executable integration fixture for later HTTP and thin Skill adapters.

- [ ] **Step 1: Write the end-to-end integration test**

Create `tests/test_subscriber_integration.py` that:

1. migrates a fresh SQLite database;
2. creates `job_rabbit_v02` in `content_locked` with `client_subscription_interactive`;
3. issues a bilingual-projection packet;
4. claims it as `client-macbook`;
5. marks generation complete;
6. submits one digest-correct JSON candidate;
7. closes and reopens the repository and candidate store;
8. reads the accepted candidate bytes back by the receipt storage key;
9. confirms state `server_verifying`, one accepted result, and ordered append-only audit events;
10. confirms serialized records contain none of `openai_api_key`, `chatgpt_cookie`, `authorization`, or
   `chatgpt_token`.

The expected audit sequence is exactly:

```python
[
    "job.created",
    "packet.issued",
    "job.transitioned",
    "packet.claimed",
    "job.transitioned",
    "generation.completed",
    "job.transitioned",
    "result.accepted",
    "job.transitioned",
]
```

- [ ] **Step 2: Verify RED for the final public contract**

Import every application-facing symbol from `cognitive_card_server.subscriber` in the integration test.

Run `PYTHONPATH=src python3 -m unittest tests.test_subscriber_integration -v`.

Expected: failure because one or more new public symbols are not yet exported.

- [ ] **Step 3: Finalize exports and package metadata**

Change the audit event written by `mark_awaiting_upload_and_transition()` from `packet.awaiting_upload` to
`generation.completed`, preserving actor, reason, details, state transition, and transaction order. Update the
focused service assertion to lock the final event sequence.

Export only these public names from `subscriber/__init__.py`:

```python
__all__ = [
    "ArtifactDeclaration",
    "ArtifactSubmission",
    "CandidateStore",
    "DomainError",
    "ExecutionProfile",
    "GenerationPacket",
    "GenerationResult",
    "GenerationStage",
    "JobRecord",
    "JobState",
    "ResultReceipt",
    "SQLiteSubscriberRepository",
    "SubscriberExecutionService",
    "StagedCandidate",
]
```

Increment the project version in `pyproject.toml` from `0.1.0` to `0.2.0`. Do not add runtime dependencies or
console scripts. Update `tests/test_package.py` to expect `0.2.0` so the package-version contract and full suite
remain aligned.

- [ ] **Step 4: Run final verification**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_subscriber_integration -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
if rg -n "os\.environ|getenv\(|Authorization: Bearer|sk-[A-Za-z0-9_-]{20,}" \
  src/cognitive_card_server/subscriber; then exit 1; fi
git status --short
```

Expected:

- all integration and full-suite tests pass;
- `compileall` exits zero;
- the credential-use scan prints no environment reads, bearer headers, or key-shaped literals;
- Git status contains only the subscriber foundation changes.

- [ ] **Step 5: Commit the accepted foundation**

```bash
git add pyproject.toml src/cognitive_card_server/subscriber tests/test_subscriber_integration.py
git commit -m "feat: complete subscriber execution foundation"
```

Expected: clean feature worktree with the reviewed task commits preserved.

## Plan Completion Gate

Do not begin the thin Skill, HTTP, MCP, portal, immutable blob store, rendering, or live-server plans until all
of these are true:

- the full existing preflight suite and new subscriber suite pass together;
- the representative flow completes without an OpenAI API credential;
- lease expiry and repository reopen tests prove resumability;
- duplicate upload, wrong lock, unsafe path, wrong digest, expired packet, and revoked client failures are
  covered;
- audit events reconstruct the job history without reading mutable application logs;
- a reviewer confirms no client or ChatGPT credential field entered the domain model.

The next plan should add an authenticated `/api/v1` adapter and thin Skill release manifest over this service,
without duplicating its transition, lease, or ingestion logic.
