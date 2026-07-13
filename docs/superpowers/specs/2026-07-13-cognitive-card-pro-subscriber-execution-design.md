# Cognitive Card OS Pro Subscriber Execution Design

## Status

Approved on 2026-07-13. This document is a normative addendum to the existing Cognitive Card Server Core
design. If the two documents differ on model execution, MCP availability, the thin Skill release boundary,
or the timing of the read-only asset portal, this document takes precedence.

The first release must work without an OpenAI API key. The owner currently generates content and images
through a ChatGPT Pro subscription and Codex clients signed in with the same ChatGPT account.

Official product constraints checked for this decision:

- ChatGPT subscriptions and OpenAI API usage are billed and managed separately:
  <https://help.openai.com/en/articles/8156019-is-api-usage-included-in-chatgpt-subscriptions-even-if-i-have-a-paid-chatgpt-account>
- Codex can be used by signing in with an eligible ChatGPT plan:
  <https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan>
- ChatGPT Pro custom MCP access does not provide a dependable full write-action surface; full MCP write
  support is currently associated with Business, Enterprise, and Edu availability:
  <https://help.openai.com/en/articles/12584461>

## 1. Decision

Use a subscriber-interactive architecture for the first release:

```text
ChatGPT Pro / Codex client
  +-- performs model reasoning, research, text generation, and available image generation
  +-- runs the locally installed thin Skill
  +-- receives a locked generation packet from the server
  +-- uploads generated artifacts and provenance
                   |
                   | authenticated HTTPS
                   v
Cognitive Card Server Core
  +-- owns classification, age/language routing, templates, facts, propositions, and content locks
  +-- owns job state, immutable asset storage, rendering, package assembly, QA, and publication
  +-- publishes versioned thin Skill releases
  +-- exposes a read-only asset portal and read-oriented MCP surface
```

The server is the system of record and deterministic production authority. The signed-in client is the
initial model executor. No ChatGPT cookie, browser session, internal access token, or unofficial endpoint is
copied to the server.

## 2. Execution Profiles

Every job records exactly one `execution_profile`:

| Profile | First release | Model executor | Intended use |
| --- | --- | --- | --- |
| `client_subscription_interactive` | Required default | Signed-in ChatGPT Pro/Codex client | Normal generation without an API key |
| `manual_upload` | Required fallback | ChatGPT or another approved interactive tool | Browser/mobile generation followed by portal upload |
| `server_api_autonomous` | Disabled by default | Server-side provider API | Future unattended generation after explicit credential and billing approval |

`client_subscription_interactive` and `manual_upload` are formal supported paths, not degraded exceptions.
They may publish packages when their uploaded artifacts pass the same content-lock, provenance, rendering,
strict-QA, and human-review gates as any future autonomous path.

The server must reject `server_api_autonomous` with `PROVIDER_CREDENTIAL_REQUIRED` while no approved server
credential exists. It must not silently substitute a browser session, client credential, or locally cached
ChatGPT authentication.

## 3. Authority Boundary

| Concern | Authority | Subscriber client responsibility |
| --- | --- | --- |
| Request normalization and classification | Server | Collect and submit explicit user inputs |
| Age and bilingual projection contract | Server | Generate only the requested projection packet |
| Facts, sources, propositions, uncertainty | Server | Return evidence or source metadata requested by the packet |
| Template family and page structure | Server | Do not invent or replace template structure |
| Content lock and generation packet | Server | Verify packet identity before generation |
| Model-generated text/image bytes | Client until accepted | Generate and upload exact artifacts with provenance |
| Artifact acceptance | Server | Retry or correct rejected uploads |
| Typesetting, print rendering, manifest, QA | Server | Download exports only |
| Published package and asset history | Server | View or export authorized revisions |

Client output is a candidate artifact until the server accepts it. Editing an accepted candidate locally does
not mutate the server record; it creates a new upload and, where required, a new content lock or package
revision.

## 4. Locked Generation Packet

Before any model-dependent work, the server produces an immutable packet with at least:

```json
{
  "schema": "cognitive-card-generation-packet-v1",
  "packet_id": "gp_...",
  "job_id": "job_...",
  "execution_profile": "client_subscription_interactive",
  "stage": "bilingual_projection",
  "content_lock_digest": "sha256:...",
  "registry_commit": "...",
  "template_fingerprint": "sha256:...",
  "age_profile": "age-5-6",
  "language_projection": "cn-observation",
  "instructions": [],
  "input_artifacts": [],
  "required_outputs": [],
  "forbidden_changes": [],
  "expires_at": "..."
}
```

Packet stages may include `source_research`, `semantic_draft`, `bilingual_projection`, and `image_generation`.
Each packet is stage-specific and contains only the minimum facts and assets necessary for that stage.

The client returns:

```json
{
  "schema": "cognitive-card-generation-result-v1",
  "packet_id": "gp_...",
  "content_lock_digest": "sha256:...",
  "client_id": "...",
  "skill_release": "...",
  "client_surface": "codex-app",
  "generated_at": "...",
  "artifacts": [],
  "source_records": [],
  "operator_notes": ""
}
```

The server rejects an expired packet, unknown packet, wrong stage, lock mismatch, undeclared artifact,
unsupported media type, or result from a revoked client. Model names and provider metadata are recorded when
the client surface exposes them; their absence must be explicit rather than fabricated.

## 5. Job State Machine

Subscriber-interactive jobs use these states:

```text
draft
  -> input_validated
  -> content_locked
  -> awaiting_client_generation
  -> client_generating
  -> awaiting_upload
  -> server_verifying
  -> rendering
  -> validating
  -> awaiting_review
  -> published
```

Rules:

- `awaiting_client_generation` is a normal durable state and may last across client restarts.
- A client claims one packet with a time-limited lease; lease expiry returns the packet to an available state
  without discarding history.
- Repeated upload uses an idempotency key and cannot create duplicate logical artifacts.
- A rejected upload records a stable error code and returns the job to `awaiting_client_generation` or
  `awaiting_upload` according to whether regeneration is required.
- Server restart must preserve every durable state and lease history.
- No job can move directly from client upload to publication.

Additional terminal states remain `failed`, `cancelled`, and `superseded`.

## 6. Client and Product Surface Matrix

| Surface | Create/claim generation work | Upload result | Search/view assets | First-release path |
| --- | --- | --- | --- | --- |
| Codex app, CLI, or IDE signed in with ChatGPT Pro | Yes | Yes | Yes | Local thin Skill calling HTTPS API |
| ChatGPT Pro web with custom MCP | Read/prepare only | Do not depend on MCP write | Yes, read/fetch only | MCP plus browser upload portal |
| Mobile or tablet browser | No model automation | Yes, manual upload | Yes | Responsive asset portal |
| Plain terminal | Yes, without model execution | Yes | Yes | Authenticated CLI/HTTPS client |
| Future server worker with provider credential | Yes | Internal | Yes | `server_api_autonomous` |

MCP is an adapter over the same application service used by HTTPS. It is not a second workflow engine. The
first MCP release is read-oriented: capabilities, active registry identity, job status, packet inspection,
asset search, package metadata, and authorized download links.

## 7. Thin Skill and Server-Hosted Releases

The server is the authoritative publication source for the thin Skill, but each Codex client still installs a
local release because Skills do not automatically execute from an arbitrary remote filesystem.

The server publishes:

```text
/skill/v1/manifest.json
/skill/v1/releases/<version>/cognitive-card-os.zip
/skill/v1/releases/<version>/sha256.txt
```

The manifest records release version, protocol range, minimum server version, archive digest, publication
state, release time, and rollback predecessor. Releases are immutable. Clients may pin a version or follow the
stable channel, but every formal request reports the installed release and protocol version.

The local Skill contains only:

- triggering and input collection;
- endpoint and protocol discovery;
- local request-shape validation;
- packet claim/download and result upload helpers;
- digest verification and explicit error mapping;
- offline limitation guidance.

It contains no mutable knowledge registry, complete template library, production asset history, provider
credential, ChatGPT session credential, or parallel production renderer.

## 8. Asset Portal

A responsive read-only portal is part of the first usable release rather than a deferred authoring studio. Its
initial route is expected under `https://www.yutou.space/card-os/`, subject to deployment confirmation.

Required first-release views:

- search and filter published and owner-visible packages;
- package revision, object, age profile, language, family, and publication status;
- four card previews, print PDF, package manifest, sources, and QA summary;
- immutable artifact digest and creation history;
- authenticated manual upload page for a claimed packet;
- clear separation of draft, quarantined, review, and published assets.

Editing facts, templates, or publication records in the browser remains outside the first release.

## 9. Authentication and Security

- Card OS uses its own scoped credentials; ChatGPT identity is not forwarded to the server.
- Initial scopes are `read`, `submit`, `review`, and `admin`.
- Browser sessions use secure, HTTP-only cookies backed by Card OS authentication.
- CLI and thin Skill tokens are stored in the local operating-system credential store or protected local
  configuration, never inside the Skill archive.
- Uploads are quarantined before verification and are limited by size, media type, decompression ratio, packet,
  and content-lock identity.
- Logs and manifests never contain ChatGPT cookies, OpenAI internal tokens, Card OS raw tokens, or unrelated
  conversation content.
- The system must not automate ChatGPT through copied browser cookies, scraped private endpoints, or credential
  replay.

## 10. Offline and Failure Behavior

- With Card OS offline, the thin Skill may collect a draft request but cannot certify or publish a package.
- With the client offline, the server preserves `awaiting_client_generation`; it does not fabricate completion.
- On ChatGPT/Codex usage limit exhaustion, return `CLIENT_PROVIDER_LIMIT_REACHED` and retain the packet for a
  later retry or manual-upload path.
- On client incompatibility, return `CLIENT_UPGRADE_REQUIRED` before packet claim.
- On server incompatibility, return `SERVER_UPGRADE_REQUIRED` before job creation.
- An unavailable optional model surface may be replaced by `manual_upload`, but the replacement is recorded as
  a profile transition and does not bypass validation.

## 11. Migration Changes to the Base Design

The base server-core design is amended as follows:

1. Make `client_subscription_interactive` the required default execution path.
2. Generalize the existing external-image handoff into locked packets for every model-dependent stage.
3. Add a server-owned Skill release registry and immutable distribution manifest.
4. Treat MCP as a read-oriented compatibility surface for ChatGPT Pro, not as the only write path.
5. Move the read-only portal and manual packet upload from the optional product phase into the first usable
   release.
6. Keep `server_api_autonomous` disabled until a separate provider credential, billing limit, secret-management
   plan, and owner approval exist.
7. Add subscriber-client states, leases, generation results, and profile transitions to the metadata model and
   audit log.

## 12. Acceptance Criteria

The subscriber-mode foundation is accepted only when:

- no OpenAI API key is required to complete the representative workflow;
- two independently installed Codex clients discover the same server and Skill release digest;
- a signed-in Codex client claims a locked packet, uploads a result, and the server accepts or rejects it
  deterministically;
- closing the client leaves the job safely resumable in `awaiting_client_generation`;
- a browser can search and view an authorized package and its PDF, sources, digest, and QA summary;
- a manual browser upload can satisfy an eligible packet without MCP write access;
- a wrong lock digest, expired packet, undeclared file, revoked client, and duplicate upload all fail with stable
  behavior;
- the full rabbit fixture completes through the subscriber-interactive path and a second mammal resolves the
  same family structure;
- no server file, log, database record, Skill release, or package contains a ChatGPT session credential;
- enabling autonomous provider execution remains impossible without an explicit server configuration change.

## 13. Implementation Decomposition

Implement this addendum through separate reviewable plans:

1. Subscriber execution contracts, job state, packet leases, and idempotent result ingestion.
2. Thin Skill remote client and server-hosted release distribution.
3. Read-only MCP adapter and cross-client compatibility tests.
4. Read-only asset portal plus authenticated manual packet upload.
5. Rendering, strict QA, package publication, and rabbit end-to-end acceptance.
6. Optional server API provider mode only after a separate approval.

The first implementation plan covers item 1 only. It must produce a testable server boundary before Skill,
MCP, portal, or live deployment work begins.
