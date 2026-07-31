# Cognitive Card OS Error Codes

Every client failure carries one stable code. Each code maps to exactly one of
four actions: re-authenticate, refresh/reconcile state, correct the local
result, or stop and report a server-integrity failure. An unknown
syntactically safe server code is preserved in the output and mapped to
`SERVER_CONTRACT_DRIFT`; it is never treated as success and never rewritten
to a known code.

## Server error codes (frozen 0.3.1 snapshot)

### auth/protocol

- `AUTH_REQUIRED` — re-authenticate: no usable credential was presented.
- `AUTH_INVALID` — re-authenticate: the credential was rejected; store a fresh scoped token.
- `AUTH_EXPIRED` — re-authenticate: the token expired; rotate to a fresh scoped token.
- `AUTH_SCOPE_REQUIRED` — re-authenticate: the token lacks the needed scope; mint a correctly scoped token.
- `AUTH_REVOKED` — re-authenticate: the token was revoked; rotate and store a new one.
- `CLIENT_UPGRADE_REQUIRED` — install the manifest stable or a compatible Skill release before continuing.
- `SERVER_UPGRADE_REQUIRED` — stop claiming work and wait for the server upgrade.
- `INVALID_SKILL_RELEASE` — install a Skill release the server accepts; do not patch headers by hand.

### request/http

- `REQUEST_VALIDATION_FAILED` — correct the request: a field, id, or argument failed validation.
- `REQUEST_TOO_LARGE` — correct the local result: shrink the request below the server limit.
- `PAYLOAD_TOO_LARGE` — correct the local result: shrink the payload and keep the same submit intent.
- `UNSUPPORTED_MEDIA_TYPE` — correct the local result: declare only media types the packet allows.
- `UNSUPPORTED_CONTENT_ENCODING` — correct the request: send the encoding the contract specifies.
- `ROUTE_NOT_FOUND` — stop and report: the called route does not exist on this server.
- `METHOD_NOT_ALLOWED` — stop and report: the verb is not allowed on this route.
- `HTTP_ERROR` — refresh/reconcile state: a transport or timeout left the outcome ambiguous; read packet or job state before any exact replay.
- `INTERNAL_ERROR` — stop and report a server-side failure; do not retry blindly.

### packet/state

- `JOB_NOT_FOUND` — refresh/reconcile state: the job is unknown; re-read available packets.
- `PACKET_NOT_FOUND` — refresh/reconcile state: the packet is not visible. After server acceptance a packet becomes invisible to the claimant; a cross-invocation results submit with a valid attempt journal and unchanged files then replays the recorded bytes with the recorded key (replayed=true), while one without a journal fails closed with this code.
- `PACKET_ALREADY_CLAIMED` — refresh/reconcile state: another claimant holds the packet; list again and pick a visible one.
- `PACKET_EXPIRED` — refresh/reconcile state: the packet expired; wait for reissue or choose another.
- `LEASE_EXPIRED` — refresh/reconcile state: the claim lease lapsed; claim again if the packet is still visible.
- `LEASE_OWNER_MISMATCH` — refresh/reconcile state: this client is not the lease owner; do not mutate the packet.
- `INVALID_STATE_TRANSITION` — refresh/reconcile state: the requested transition is not legal from the current state.
- `INVALID_CLIENT_ID` — stop and report: the client identity is not recognized.
- `CLIENT_REVOKED` — stop and report: this client identity was revoked on the server.
- `INVALID_PACKET_LIMIT` — correct the request: the list limit is outside the accepted range.
- `INVALID_LEASE_DURATION` — correct the request: the lease duration is outside the accepted range.

### result/artifact

- `INVALID_IDEMPOTENCY_KEY` — stop and report: the key does not match the frozen client formula.
- `IDEMPOTENCY_CONFLICT` — stop and require manual inspection; the same key arrived with different bytes.
- `SKILL_RELEASE_MISMATCH` — install the Skill release the packet was issued for.
- `INVALID_BASE64` — correct the local result: an artifact payload is not valid base64.
- `MISSING_ARTIFACT` — correct the local result: a declared required output is absent.
- `UNDECLARED_ARTIFACT` — correct the local result: an uploaded file is not declared by the packet.
- `UNSAFE_ARTIFACT_PATH` — correct the local result: every file needs a safe relative POSIX path.
- `ARTIFACT_MEDIA_TYPE_MISMATCH` — correct the local result: the media type differs from the declaration.
- `ARTIFACT_SIZE_MISMATCH` — correct the local result: the size differs from the declaration.
- `ARTIFACT_TOO_LARGE` — correct the local result: a file exceeds its declared budget.
- `ARTIFACT_DIGEST_MISMATCH` — correct the local result: the SHA-256 differs from the declaration.
- `UNSUPPORTED_ARTIFACT_MEDIA_TYPE` — correct the local result: the media type is outside the allowed set.
- `INVALID_ARTIFACT_MEDIA` — correct the local result: the server image decode rejected the content; the server check is authoritative over the client magic-byte check.
- `UNSAFE_ARTIFACT_COMPRESSION` — correct the local result: the archive or compression shape is unsafe.
- `CONTENT_LOCK_MISMATCH` — refresh/reconcile state: the content lock changed; stop generating and re-read the packet.
- `PACKET_PROFILE_MISMATCH` — refresh/reconcile state: the execution profile no longer matches.
- `RESULT_CLIENT_MISMATCH` — refresh/reconcile state: the submitting client is not the claimant.
- `STAGED_METADATA_MISMATCH` — refresh/reconcile state: staged artifact metadata disagrees with the upload.

### server-integrity

- `CANDIDATE_DIGEST_MISMATCH` — stop and report a server-integrity failure.
- `CANDIDATE_STORE_CLOSED` — stop and report a server-integrity failure.
- `CANDIDATE_STORE_REQUIRED` — stop and report a server-integrity failure.
- `INVALID_STORAGE_KEY` — stop and report a server-integrity failure.
- `UNSAFE_CANDIDATE_STORE` — stop and report a server-integrity failure.
- `FORBIDDEN_CREDENTIAL_FIELD` — stop and report a server-integrity failure.
- `FORBIDDEN_CREDENTIAL_VALUE` — stop and report a server-integrity failure.
- `NON_CANONICAL_JSON` — stop and report a server-integrity failure.
- `DATABASE_CONSTRAINT_VIOLATION` — stop and report a server-integrity failure.
- `INVALID_UTC_CLOCK` — stop and report a server-integrity failure.
- `INVALID_UTC_TIMESTAMP` — stop and report a server-integrity failure.

## Local client codes

- `TRUSTED_UPSTREAM_REQUIRED` — the input is a free concept or names no visible packet; this Skill cannot create a task. List available packets and use a locked one.
- `REDIRECT_REFUSED` — the server answered with a redirect; the client never follows one while carrying credentials. Report the drift.
- `TLS_REQUIRED` — the endpoint is not the fixed TLS host; refuse to proceed.
- `DIGEST_MISMATCH` — the recomputed packet digest differs from the envelope; do not save, generate, or mutate.
- `UNSAFE_ARCHIVE` — a downloaded archive failed the safe-extraction checks; do not install it.
- `CREDENTIAL_IN_RESULT` — credential-shaped content was found in the result; regenerate the files without secrets. The matched bytes are never echoed.
- `ATTEMPT_BODY_CHANGED` — the result files or metadata changed since the frozen attempt; do not submit under a new key.
- `CREDENTIAL_STORE_UNAVAILABLE` — no system credential store is reachable; pass a token per invocation or explicitly allow the file store.
- `CREDENTIAL_STORE_UNSAFE` — the credential store failed ownership, mode, or link checks; fix permissions before storing.
- `SERVER_CONTRACT_DRIFT` — the server answered outside the frozen contract (including an unknown but syntactically safe code); stop and report instead of guessing.

## Installer-only codes

- `UNMANAGED_ACTIVE_SKILL` — installer-only, documented here for completeness and not emitted by card_os_client.py: an existing active Skill directory does not match any managed, verified cache entry, so the installer stops instead of taking it over.
