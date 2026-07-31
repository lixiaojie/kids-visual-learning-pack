# Cognitive Card OS Thin Client Protocol

Skill release `0.1.1` talks to the personal Card OS server only. The base URL
is fixed to `https://www.yutou.space/card-os/`; the client refuses redirects,
requires TLS, and caps every response at 4 MiB. Protocol version is the
unsigned decimal `1`; the minimum server version is `0.3.1`.

## Command surface

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

## Routes

```text
GET /card-os/api/v1/health (unauthenticated)
GET /card-os/api/v1/capabilities (unauthenticated)
GET /card-os/api/v1/packets/available
POST /card-os/api/v1/packets/<packet_id>/claim
GET /card-os/api/v1/packets/<packet_id>
POST /card-os/api/v1/packets/<packet_id>/complete
POST /card-os/api/v1/packets/<packet_id>/results
GET /card-os/api/v1/jobs/<job_id>
GET /card-os/api/v1/jobs/<job_id>/events
```

The client never calls admin routes and holds no admin token. Packet and job
IDs are sent as exactly one percent-encoded path segment; the client rejects
empty values, control characters, and path separators.

## Protected headers

Every authenticated request carries exactly:

```text
Authorization: Bearer <token>
X-Card-OS-Protocol: 1
X-Card-OS-Skill-Release: 0.1.1
```

Result uploads additionally carry `Idempotency-Key`. The token comes from the
operating-system credential store (macOS Keychain or Linux Secret Service) or,
only with `--allow-file-store`, from a private `0600` credentials file under
the user config directory. For a single run, the ephemeral CARD_OS_TOKEN
environment variable takes request-time precedence and is never persisted. A
token never enters the Skill directory, logs, command arguments, or any
uploaded result.

## Schemas

- Capabilities document: `cognitive-card-capabilities-v1`.
- GenerationPacket: `cognitive-card-generation-packet-v1` — closed object with
  `packet_id`, `job_id`, `execution_profile`, `stage`, `content_lock_digest`,
  `registry_commit`, `template_fingerprint`, `age_profile`,
  `language_projection`, `issued_at`, `expires_at`, `schema`, `instructions`,
  `forbidden_changes`, `input_artifacts`, and `required_outputs` (each entry:
  `relative_path`, `media_type`, `max_bytes`). The envelope adds
  `packet_digest`, `claimed_by`, `lease_expires_at`, `created_at`, and
  `expired_at`.
- GenerationResult: `cognitive-card-generation-result-v1` with
  `skill_release` exactly `0.1.1` and CLIENT_SURFACE exactly `codex-cli`.
- Attempt journal: `cognitive-card-submit-attempt-v1`, a private `0600`
  non-link file at
  `${XDG_STATE_HOME:-$HOME/.local/state}/cognitive-card-os/attempts/<packet-id>.json`
  holding only the packet ID, the fixed `generated_at`, the canonical body
  SHA-256, the idempotency key, the content lock digest, and the sorted
  artifact path/media type/SHA-256/size list — never tokens or payloads.

## Packet digest

The client recomputes `packet_digest` exactly as server `0.3.1` and rejects any
mismatch (`DIGEST_MISMATCH`) before saving, generating, or mutating:

```python
packet_digest = "sha256:" + sha256(
    json.dumps(packet, allow_nan=False, ensure_ascii=False,
               sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
```

## Idempotency key

`results submit` freezes one canonical request body and computes the key once:

```python
Idempotency-Key = "ccos-v1-" + sha256(packet_id + "\n" + canonical_request_body)
```

Only the exact same byte string with the same key may be replayed, at most
once, after a status read. Any changed file or metadata yields
`ATTEMPT_BODY_CHANGED` instead of a silently new key. After acceptance the
packet becomes invisible to the claimant; a later `results submit` with
unchanged files then replays the recorded body and key through the attempt
journal and the server answers with the stored receipt (replayed=true).

## Limits and media policy

- Decoded artifact bytes in one result: at most 20 MiB total and per file.
- Canonical JSON request body: at most 28 MiB.
- Allowed media types: `application/json`, `text/markdown`, `text/plain`,
  `image/png`, `image/jpeg`, `image/webp`.
- Client image checks are magic-byte only (PNG, JPEG, RIFF/WEBP signatures).
  The server PIL decode remains authoritative and rejects bad image content
  with `INVALID_ARTIFACT_MEDIA`.
- Every decoded payload, path/media metadata string, and the final canonical
  body are scanned for the raw token and any complete credential shape; a hit
  fails with `CREDENTIAL_IN_RESULT` without echoing the matched bytes.

## Free-concept classification

Where a packet ID is expected, free text — anything containing whitespace or
non-ASCII characters — is classified as a free concept and fails closed with
`TRUSTED_UPSTREAM_REQUIRED`. This Skill cannot turn a concept into a job; only
a locked server packet starts work.

## Acceptance is not publication

A successful upload returns an acceptance receipt whose `result_digest` is an
opaque server identifier of the form `sha256:<64 lowercase hex>`; the client
verifies its shape and, on exact replay, its byte stability, but does not
recompute it. The staged candidate is `candidate_staged` and remains invisible
to the claimant afterwards; review, rendering, QA, and final publication are
server-side steps outside this Skill.
