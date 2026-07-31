---
name: cognitive-card-os
description: Run locked Cognitive Card OS tasks end to end. Claim a server-issued packet, generate its declared outputs with ChatGPT Pro, and upload the verified candidate with the governed thin client. Use when a Card OS packet ID or knowledge-card task is involved.
---

# Cognitive Card OS

Thin client for the personal Card OS server. `scripts/card_os_client.py` is the
only execution path. Generation is done by you, the logged-in ChatGPT Pro
session, with the local text and image tools — no OpenAI API key is needed at
any point, and the client never calls an AI API.

## First-version boundary

- Only server-issued, locked, claimable packets are processed. A free concept
  (any input that is not a packet ID) fails closed with
  `TRUSTED_UPSTREAM_REQUIRED`; do not synthesize a lock and do not invent a
  job, packet, or upload for it.
- Do not call admin routes, do not publish directly, and do not upload under the ChatGPT identity.
  Uploads go only through the client with its scoped Card OS token.
- A successful upload stages a candidate (`candidate_staged`): it is
  never a publication. Never claim a task was published.

## Decision table

| Input state | Action |
| --- | --- |
| packet ID present | run `doctor`, authenticate, fetch and verify the packet |
| no packet ID but available packets visible | ask the user to choose; claim only when explicitly authorized |
| free concept only | return `TRUSTED_UPSTREAM_REQUIRED`; do not synthesize a lock |
| generated candidate directory ready | local validation, `packets complete`, automatic submit |

## Workflow

1. `doctor` — confirm server health, protocol intersection, and release
   compatibility.
2. `auth status` — confirm a scoped credential exists; configure one with
   `auth set --stdin` if the operator supplies a token.
3. `packets list`, then `packets claim PACKET_ID` (only when authorized), then
   `packets get PACKET_ID --output FILE`. The fetched packet is the sole fact
   and output boundary; verify its digest before generating.
4. Generate exactly the declared `required_outputs` with ChatGPT Pro into a
   private per-packet working directory, respecting every `forbidden_changes`
   entry and the content lock.
5. `packets complete PACKET_ID`, then `results submit PACKET_ID --directory
   DIR`. Automatic submit is the primary path: the client validates the
   directory locally, then uploads with its frozen idempotency key.

## Fail-closed rules

- Any stable error code stops the workflow; act on it with
  [references/errors.md](references/errors.md).
- Never blindly retry a mutation. After a timeout, read packet/job state
  first; only the exact same submit bytes may be replayed.
- Wire details (routes, headers, schemas, digest, limits) live in
  [references/protocol.md](references/protocol.md).
