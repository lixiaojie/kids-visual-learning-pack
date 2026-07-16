---
name: cognitive-card-os
description: Inspect the verified Cognitive Card OS client release boundary. Use when Codex is asked to install, inspect, or invoke the governed thin client before its first complete release.
---

# Cognitive Card OS

Fail closed: the governed thin client is not released in this source skeleton.

Run `scripts/card_os_client.py` only to obtain the stable boundary error. Treat
`CLIENT_NOT_RELEASED` as final for this version. Do not claim, execute, complete,
or upload a Card OS task, and do not infer those capabilities from the presence
of this Skill.

Read `references/protocol.md` for the declared version constants. Read
`references/errors.md` when explaining the boundary error.
