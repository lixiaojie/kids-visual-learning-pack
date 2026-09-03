# Operator Illustration Hero Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For an already confirmed library current, expand a copyable no-text hero-illustration prompt, accept one PNG upload, and show an ops page of that image plus every `standing=active` proposition.

**Architecture:** File-backed `illustration-intent` under the injected candidate root. Pin `LibraryRevision.identity` (keys unchanged, including `final_content_lock_sha256`) as the snapshot; compare that dict on every GET/upload. Template `illustration-hero-v1` fills display name, classification, and active `safety_scope` only. HTTP reuses admin token scope. Multipart is allowed only on `POST .../ii_{hex}/image`. HTML shells stay claim-free.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, existing `KnowledgeLibrary.publish` / `require_current_identity` / `load_package`, server worktree `knowledge-pipeline-v1` @ `91b7cf3`.

**Plan size:** Medium (5 tasks, 3 phases)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md` (Approved).
- No OpenAI / ChatGPT image API, no Cookie, no Codex claim, no executor token, no new capability, no Skill `read`/`submit` access.
- Do not change four-object schema, KNOW-04 six-topic currents, PROJ-01 families, WB-02 mapping-lock, WB-03 `render_locked`, Nginx, or production knowledge-library.
- Do not write production library. HTTP/CLI take an explicit library / candidate root. Tests use tmp. Do not touch `/tmp/card-os-api01` as if it were production.
- Pin and compare `LibraryRevision.identity` as the authoritative snapshot. Copy its keys unchanged: `object_id`, `revision`, `knowledge_core_sha256`, `learning_spec_sha256`, `projection_spec_sha256`, `final_content_lock_sha256`. Do not invent `manifest_sha256` or rename `knowledge_core_sha256` to `core_sha256` on disk.
- Map core `canonical_claim` → API field `claim`. Do not call AGE-01. Do not invent a second language line.
- Display name: `scope.identity.names.cn`, else `names.en`, else `topic_slug`. Classification: `scope.classification` keys `primary_domain`, `primary_form`, `object_subtype` only. Safety lines: non-empty `safety_scope` strings from `standing=active` propositions only (document order, de-dupe). Do not use `mapping.collect_safety_texts` (it includes non-active and top-level lists).
- Allow `multipart/form-data` only for `POST /card-os/api/v1/admin/knowledge-illustration/ii_[0-9a-f]{32}/image`. Every other POST with a body stays `application/json` or `UNSUPPORTED_MEDIA_TYPE`.
- Tests use the inline `MINIMAL_PNG` bytes below. Do not add a binary fixture file.
- Do not git commit, merge server `main`, push, add `uv.lock`, reload Nginx, or install a production release.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core`. Use `.venv/bin/python` with `PYTHONPATH=src`.
- Register illustration HTML `/card-os/ops/illustration/{intent_id}` **before** `/card-os/ops/{topic}`.
- Kids docs live in `/Users/admin/projects/family/kids-visual-learning-pack`. Do not touch `outputs/`.
- Do not mark roadmap `IMG-01` `DONE`.

### Authoritative snapshot (do not reinterpret)

`LibraryRevision.identity` is produced by `knowledge_revision_record` and stored on the current pointer. Compare with `library.require_current_identity(intent["identity"], now=now)`. On `KNOWLEDGE_LIBRARY_CURRENT_NOT_FOUND`, `KNOWLEDGE_LIBRARY_REVISION_NOT_CURRENT`, or `LIBRARY_POINTER_MISMATCH`: persist `state=stale` and raise `ILLUS_CURRENT_MOVED`.

HTTP also returns `knowledge_revision` as `identity["revision"]` (int). That is a convenience field; matching is the full identity dict.

### Inline PNG (all tests)

```python
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
```

### Combined focused gate (run at the end of Task 3, 4, and 5)

Combined regression baseline on this worktree is **62 tests**:

| Module | Count | Slice |
| --- | ---: | --- |
| `tests.test_knowledge_compile` | 18 | API-01 |
| `tests.test_http_knowledge_compile` | 9 | API-01 HTTP |
| `tests.test_http_knowledge_ops` | 13 | WB-01 |
| `tests.test_knowledge_library_mapping` | 6 | WB-02 |
| `tests.test_weighted_layout` | 5 | WB-03 |
| `tests.test_http_auth` | 11 | protected-route/auth registry |

Plus new `tests.test_knowledge_illustration` and `tests.test_http_knowledge_illustration`. Expected: all PASS. Do not require full-suite real-uvicorn 502 cleanup.

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_knowledge_library_mapping tests.test_weighted_layout tests.test_http_auth tests.test_knowledge_illustration tests.test_http_knowledge_illustration
```

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_illustration/__init__.py` | Public functions |
| `src/cognitive_card_server/knowledge_illustration/prompt.py` | Template load, sha256, display name, classification, active safety, `expand_prompt`, `active_propositions` |
| `src/cognitive_card_server/knowledge_illustration/templates/illustration-hero-v1.txt` | Copyable ChatGPT image prompt |
| `src/cognitive_card_server/knowledge_illustration/store.py` | `illustration-intents/{ii_*}/meta.json` + `expanded_prompt.txt` + `hero.png` |
| `src/cognitive_card_server/knowledge_illustration/pipeline.py` | `create_intent`, `submit_image`, `cancel_intent`, `load_intent`, `read_hero_png` |
| `src/cognitive_card_server/knowledge_ops/http.py` | Admin illustration routes; HTML illustration route before `{topic}` |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Topic “主体插画” entry; illustration shell |
| `src/cognitive_card_server/http/app.py` | `PROTECTED_ROUTES`; multipart exception on the image POST only |
| `src/cognitive_card_server/http/errors.py` | `ILLUS_*` status mapping |
| `pyproject.toml` | Add `python-multipart` (install into `.venv`; do not update `uv.lock`) |
| `tests/test_knowledge_illustration.py` | Template, identity pin, PNG, stale, retry |
| `tests/test_http_knowledge_illustration.py` | Admin JSON, multipart, auth, HTML shell |

Kids (Task 5): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`.

---

## Phase 1: Prompt and intent pipeline

### Task 1: Template expand and proposition list

**Files:**
- Create: `src/cognitive_card_server/knowledge_illustration/templates/illustration-hero-v1.txt`
- Create: `src/cognitive_card_server/knowledge_illustration/prompt.py`
- Create: `src/cognitive_card_server/knowledge_illustration/__init__.py`
- Test: `tests/test_knowledge_illustration.py` (start this file here; later tasks append)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration.PromptExpandTests -v` → all pass
**Depends on:** None

**Interfaces:**
- Consumes: `examples/authoring/rabbit-real.json` via `compile_authoring_request` (in-memory core; no library write)
- Produces:

```python
TEMPLATE_ID = "illustration-hero-v1"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PNG_MAX_BYTES = 12 * 1024 * 1024

def template_path() -> Path: ...
def template_sha256() -> str:
    """Return 'sha256:' + hex of template file bytes."""

def display_name(core: Mapping[str, object], topic_slug: str) -> str:
    """scope.identity.names.cn, else names.en, else topic_slug."""

def classification_fields(core: Mapping[str, object]) -> dict[str, str]:
    """Return keys primary_domain, primary_form, object_subtype from scope.classification.
    Missing/blank values become ''."""

def active_safety_texts(core: Mapping[str, object]) -> tuple[str, ...]:
    """Non-empty safety_scope strings from standing=='active' propositions, core order, de-duped."""

def expand_prompt(*, core: Mapping[str, object], topic_slug: str) -> str:
    """Replace {{display_name}} {{primary_domain}} {{primary_form}} {{object_subtype}} {{safety_constraints}} once each.
    Raise ILLUS_SLUG_INVALID if slug is not ^[a-z][a-z0-9-]{2,63}$."""

def active_propositions(core: Mapping[str, object]) -> list[dict[str, object]]:
    """standing==active, core document order. Each item:
    {proposition_id, certainty, claim} where claim = canonical_claim.
    Skip non-dicts. Do not sort."""
```

- [ ] **Step 1: Write failing tests** in `tests/test_knowledge_illustration.py`

```python
"""Illustration-intent: copyable no-text prompt, PNG upload, identity pin."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cognitive_card_server.knowledge_contract.authoring import compile_authoring_request
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError
from cognitive_card_server.knowledge_illustration.prompt import (
    TEMPLATE_ID,
    active_propositions,
    expand_prompt,
    template_sha256,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _rabbit_core() -> dict[str, object]:
    request = json.loads(
        (REPO_ROOT / "examples" / "authoring" / "rabbit-real.json").read_text(
            encoding="utf-8"
        )
    )
    return compile_authoring_request(request).knowledge_core


class PromptExpandTests(unittest.TestCase):
    def test_expanded_prompt_has_name_class_safety_not_claims(self) -> None:
        core = _rabbit_core()
        text = expand_prompt(core=core, topic_slug="rabbit")
        self.assertIn("兔子", text)
        self.assertIn("life", text)
        self.assertIn("entity", text)
        self.assertIn("animal/mammal", text)
        self.assertIn("single subject", text.lower().replace("-", " "))
        self.assertIn("must not contain any text", text.lower())
        self.assertIn(
            "Ask a rabbit-savvy veterinarian before making significant diet changes.",
            text,
        )
        self.assertIn(
            "Children must be supervised; only adults or responsible older children should pick up rabbits.",
            text,
        )
        self.assertNotIn("{{display_name}}", text)
        for proposition in core["propositions"]:
            if proposition.get("standing") != "active":
                continue
            claim = proposition["canonical_claim"]
            self.assertNotIn(claim, text)
        self.assertTrue(template_sha256().startswith("sha256:"))
        self.assertEqual(TEMPLATE_ID, "illustration-hero-v1")

    def test_display_name_falls_back_and_skips_non_active_safety(self) -> None:
        core = copy.deepcopy(_rabbit_core())
        core["scope"]["identity"]["names"] = {"cn": "", "en": ""}
        core["propositions"].append(
            {
                "proposition_id": "prop.rabbit.ignored-safety",
                "canonical_claim": "Ignored disputed claim about fireworks.",
                "certainty": "possible",
                "standing": "disputed",
                "safety_scope": ["DO-NOT-PAINT-DISPUTED-FIREWORKS"],
            }
        )
        text = expand_prompt(core=core, topic_slug="rabbit")
        self.assertIn("rabbit", text)
        self.assertNotIn("DO-NOT-PAINT-DISPUTED-FIREWORKS", text)
        self.assertNotIn("Ignored disputed claim about fireworks.", text)
        with self.assertRaises(KnowledgeContractError) as ctx:
            expand_prompt(core=core, topic_slug="R")
        self.assertEqual(ctx.exception.code, "ILLUS_SLUG_INVALID")

    def test_active_propositions_map_canonical_claim_and_keep_order(self) -> None:
        core = _rabbit_core()
        rows = active_propositions(core)
        source = [
            item
            for item in core["propositions"]
            if isinstance(item, dict) and item.get("standing") == "active"
        ]
        self.assertEqual(len(rows), len(source))
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(
            [row["proposition_id"] for row in rows],
            [item["proposition_id"] for item in source],
        )
        for row, item in zip(rows, source, strict=True):
            self.assertEqual(set(row), {"proposition_id", "certainty", "claim"})
            self.assertEqual(row["claim"], item["canonical_claim"])
            self.assertEqual(row["certainty"], item["certainty"])
            self.assertNotIn("canonical_claim", row)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration.PromptExpandTests -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'cognitive_card_server.knowledge_illustration'`

- [ ] **Step 3: Write template + `prompt.py` + `__init__.py`**

Template `illustration-hero-v1.txt` (UTF-8). Placeholders must be exactly `{{display_name}}`, `{{primary_domain}}`, `{{primary_form}}`, `{{object_subtype}}`, `{{safety_constraints}}`:

```text
Create exactly one image. Single subject. Children's natural-history encyclopedia illustration. Natural light, clear silhouette, no collage.

The image must not contain any text, letters, numbers, titles, labels, captions, watermarks, or UI frames.

Subject display name: {{display_name}}
Classification (do not invent conflicting anatomy, clothing, props, or setting):
- primary_domain: {{primary_domain}}
- primary_form: {{primary_form}}
- object_subtype: {{object_subtype}}

If visible detail is insufficient, draw an ordinary external appearance. The page text, not this image, is the knowledge authority.

Forbidden scenes, copied verbatim from active safety_scope. Do not add new sentences. If this block is empty, invent none:
{{safety_constraints}}
```

`prompt.py`:

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from cognitive_card_server.knowledge_contract.model import (
    KnowledgeContractError,
    sha256_hex,
)

TEMPLATE_ID = "illustration-hero-v1"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PNG_MAX_BYTES = 12 * 1024 * 1024
_SLUG = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


def template_path() -> Path:
    return Path(__file__).resolve().parent / "templates" / f"{TEMPLATE_ID}.txt"


def template_sha256() -> str:
    return "sha256:" + sha256_hex(template_path().read_bytes())


def display_name(core: Mapping[str, object], topic_slug: str) -> str:
    scope = core.get("scope")
    if isinstance(scope, dict):
        identity = scope.get("identity")
        if isinstance(identity, dict):
            names = identity.get("names")
            if isinstance(names, dict):
                for key in ("cn", "en"):
                    value = names.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
    return topic_slug


def classification_fields(core: Mapping[str, object]) -> dict[str, str]:
    scope = core.get("scope")
    raw: object = None
    if isinstance(scope, dict):
        raw = scope.get("classification")
    classification = raw if isinstance(raw, dict) else {}
    fields: dict[str, str] = {}
    for key in ("primary_domain", "primary_form", "object_subtype"):
        value = classification.get(key)
        fields[key] = value.strip() if isinstance(value, str) and value.strip() else ""
    return fields


def active_safety_texts(core: Mapping[str, object]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    propositions = core.get("propositions")
    if not isinstance(propositions, list):
        return ()
    for proposition in propositions:
        if not isinstance(proposition, dict):
            continue
        if proposition.get("standing") != "active":
            continue
        safety = proposition.get("safety_scope")
        if not isinstance(safety, list):
            continue
        for item in safety:
            if isinstance(item, str) and item.strip() and item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(ordered)


def expand_prompt(*, core: Mapping[str, object], topic_slug: str) -> str:
    if not isinstance(topic_slug, str) or _SLUG.fullmatch(topic_slug) is None:
        raise KnowledgeContractError("ILLUS_SLUG_INVALID", "topic_slug")
    fields = classification_fields(core)
    safety = "\n".join(active_safety_texts(core))
    template = template_path().read_text(encoding="utf-8")
    return (
        template.replace("{{display_name}}", display_name(core, topic_slug))
        .replace("{{primary_domain}}", fields["primary_domain"])
        .replace("{{primary_form}}", fields["primary_form"])
        .replace("{{object_subtype}}", fields["object_subtype"])
        .replace("{{safety_constraints}}", safety)
    )


def active_propositions(core: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    propositions = core.get("propositions")
    if not isinstance(propositions, list):
        return rows
    for proposition in propositions:
        if not isinstance(proposition, dict):
            continue
        if proposition.get("standing") != "active":
            continue
        ident = proposition.get("proposition_id")
        certainty = proposition.get("certainty")
        claim = proposition.get("canonical_claim")
        if not isinstance(ident, str) or not isinstance(claim, str):
            continue
        rows.append(
            {
                "proposition_id": ident,
                "certainty": certainty if isinstance(certainty, str) else "",
                "claim": claim,
            }
        )
    return rows
```

`__init__.py` (Task 2 will extend exports):

```python
from .prompt import (
    PNG_MAGIC,
    PNG_MAX_BYTES,
    TEMPLATE_ID,
    active_propositions,
    expand_prompt,
    template_sha256,
)

__all__ = [
    "PNG_MAGIC",
    "PNG_MAX_BYTES",
    "TEMPLATE_ID",
    "active_propositions",
    "expand_prompt",
    "template_sha256",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration.PromptExpandTests -v`

Expected: PASS (`Ran 3 tests`)

---

### Task 2: Intent store, create, PNG, cancel, stale

**Files:**
- Create: `src/cognitive_card_server/knowledge_illustration/store.py`
- Create: `src/cognitive_card_server/knowledge_illustration/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/__init__.py`
- Test: `tests/test_knowledge_illustration.py` (append `IntentPipelineTests`)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration -v` → all pass
**Depends on:** Task 1 (`expand_prompt`, `active_propositions`, `template_sha256`, `PNG_MAGIC`, `PNG_MAX_BYTES`)

**Interfaces:**
- Consumes: `KnowledgeLibrary.get_current`, `KnowledgeLibrary.publish`, `KnowledgeLibrary.require_current_identity`, `load_package`, Task 1 functions
- Produces:

```python
INTENT_SCHEMA = "cognitive-card-illustration-intent-v1"
RESERVED_ACTORS = frozenset({"qa-01-v1", "publish-01-v1", "machine"})
# intent_id: "ii_" + secrets.token_hex(16)

def create_intent(*, library, illustration_root: Path, topic_slug: str, actor: str, now: datetime, idempotency_key: str | None = None) -> dict[str, object]:
    """Require current. Pin identity dict. State open. Returns public intent including expanded_prompt and propositions."""

def submit_image(*, library, illustration_root: Path, intent_id: str, image_bytes: bytes, content_type: str, actor: str, now: datetime) -> dict[str, object]:
    """open|failed + identity still current. Valid PNG → illustrated. Invalid → failed + ILLUS_IMAGE_INVALID returned on the intent (do not raise). Too large raises ILLUS_IMAGE_TOO_LARGE. Already illustrated raises ILLUS_ALREADY_ILLUSTRATED. Current moved → stale + raise ILLUS_CURRENT_MOVED."""

def cancel_intent(*, library, illustration_root: Path, intent_id: str, now: datetime) -> dict[str, object]:
    """open|failed|illustrated → cancelled. Keep hero.png if present."""

def load_intent(*, library, illustration_root: Path, intent_id: str, now: datetime) -> dict[str, object]:
    """Sync identity. If moved: stale + raise ILLUS_CURRENT_MOVED. Else return public intent."""

def read_hero_png(*, library, illustration_root: Path, intent_id: str, now: datetime) -> bytes:
    """illustrated + identity current only. cancelled → ILLUS_NOT_ILLUSTRATED. stale/moved → ILLUS_CURRENT_MOVED. other → ILLUS_NOT_ILLUSTRATED."""
```

Public intent dict always includes: `intent_id`, `state`, `topic_slug`, `actor`, `knowledge_revision`, `identity` (the six-key snapshot), `prompt_template_id`, `prompt_template_sha256`, `expanded_prompt`, `created_at`, `updated_at`, `hero_png_sha256` (None unless illustrated), `error`, `propositions` (active list when snapshot still matches).

Disk:

```text
{illustration_root}/{intent_id}/meta.json
{illustration_root}/{intent_id}/expanded_prompt.txt
{illustration_root}/{intent_id}/hero.png   # illustrated only
```

- [ ] **Step 1: Append failing pipeline tests** to `tests/test_knowledge_illustration.py` (same file as Task 1; keep the existing imports and `MINIMAL_PNG`)

```python
from cognitive_card_server.knowledge_illustration.pipeline import (
    cancel_intent,
    create_intent,
    load_intent,
    read_hero_png,
    submit_image,
)
from cognitive_card_server.knowledge_library.store import KnowledgeLibrary, load_package


def _publish_rabbit(library: KnowledgeLibrary):
    request = json.loads(
        (REPO_ROOT / "examples" / "authoring" / "rabbit-real.json").read_text(
            encoding="utf-8"
        )
    )
    return library.publish(compile_authoring_request(request), now=NOW)


def _publish_rabbit_revision_two(library: KnowledgeLibrary):
    request = json.loads(
        (REPO_ROOT / "examples" / "authoring" / "rabbit-real.json").read_text(
            encoding="utf-8"
        )
    )
    request["topic"]["revision"] = 2
    return library.publish(compile_authoring_request(request), now=NOW)


class IntentPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.library = KnowledgeLibrary(Path(self.temp.name) / "library")
        self.root = Path(self.temp.name) / "illustration-intents"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_no_current_and_create_pins_identity(self) -> None:
        with self.assertRaises(KnowledgeContractError) as ctx:
            create_intent(
                library=self.library,
                illustration_root=self.root,
                topic_slug="rabbit",
                actor="owner",
                now=NOW,
            )
        self.assertEqual(ctx.exception.code, "ILLUS_NO_CURRENT")
        stored = _publish_rabbit(self.library)
        created = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
        )
        core = load_package(stored.directory).knowledge_core
        expected_ids = [
            item["proposition_id"]
            for item in core["propositions"]
            if isinstance(item, dict) and item.get("standing") == "active"
        ]
        self.assertEqual(created["state"], "open")
        self.assertTrue(str(created["intent_id"]).startswith("ii_"))
        self.assertEqual(created["identity"], stored.identity)
        self.assertEqual(
            set(created["identity"]),
            {
                "object_id",
                "revision",
                "knowledge_core_sha256",
                "learning_spec_sha256",
                "projection_spec_sha256",
                "final_content_lock_sha256",
            },
        )
        self.assertEqual(created["knowledge_revision"], stored.identity["revision"])
        self.assertIn("兔子", created["expanded_prompt"])
        self.assertEqual(
            [row["proposition_id"] for row in created["propositions"]],
            expected_ids,
        )
        self.assertEqual(
            created["propositions"][0]["claim"],
            core["propositions"][0]["canonical_claim"],
        )
        self.assertNotIn("canonical_claim", created["propositions"][0])
        identity_before = dict(stored.identity)
        with self.assertRaises(KnowledgeContractError) as active:
            create_intent(
                library=self.library,
                illustration_root=self.root,
                topic_slug="rabbit",
                actor="owner",
                now=NOW,
            )
        self.assertEqual(active.exception.code, "ILLUS_INTENT_ACTIVE")
        current = self.library.get_current("rabbit", now=NOW)
        self.assertEqual(current.identity, identity_before)

    def test_idempotency_same_body_replays(self) -> None:
        _publish_rabbit(self.library)
        first = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
            idempotency_key="illus-key-1",
        )
        replay = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
            idempotency_key="illus-key-1",
        )
        self.assertEqual(first["intent_id"], replay["intent_id"])
        with self.assertRaises(KnowledgeContractError) as ctx:
            create_intent(
                library=self.library,
                illustration_root=self.root,
                topic_slug="rabbit",
                actor="other",
                now=NOW,
                idempotency_key="illus-key-1",
            )
        self.assertEqual(ctx.exception.code, "ILLUS_INTENT_ACTIVE")

    def test_invalid_png_fails_then_retry_illustrates(self) -> None:
        stored = _publish_rabbit(self.library)
        created = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
        )
        intent_id = created["intent_id"]
        failed = submit_image(
            library=self.library,
            illustration_root=self.root,
            intent_id=intent_id,
            image_bytes=b"",
            content_type="image/png",
            actor="owner",
            now=NOW,
        )
        self.assertEqual(failed["state"], "failed")
        self.assertEqual(failed["error"], "ILLUS_IMAGE_INVALID")
        self.assertEqual(
            self.library.get_current("rabbit", now=NOW).identity, stored.identity
        )
        with self.assertRaises(KnowledgeContractError) as too_big:
            submit_image(
                library=self.library,
                illustration_root=self.root,
                intent_id=intent_id,
                image_bytes=b"x" * (12 * 1024 * 1024 + 1),
                content_type="image/png",
                actor="owner",
                now=NOW,
            )
        self.assertEqual(too_big.exception.code, "ILLUS_IMAGE_TOO_LARGE")
        illustrated = submit_image(
            library=self.library,
            illustration_root=self.root,
            intent_id=intent_id,
            image_bytes=MINIMAL_PNG,
            content_type="image/png",
            actor="owner",
            now=NOW,
        )
        self.assertEqual(illustrated["state"], "illustrated")
        self.assertTrue(str(illustrated["hero_png_sha256"]).startswith("sha256:"))
        core = load_package(stored.directory).knowledge_core
        expected_ids = [
            item["proposition_id"]
            for item in core["propositions"]
            if isinstance(item, dict) and item.get("standing") == "active"
        ]
        self.assertEqual(
            [row["proposition_id"] for row in illustrated["propositions"]],
            expected_ids,
        )
        png = read_hero_png(
            library=self.library,
            illustration_root=self.root,
            intent_id=intent_id,
            now=NOW,
        )
        self.assertEqual(png, MINIMAL_PNG)
        with self.assertRaises(KnowledgeContractError) as again:
            submit_image(
                library=self.library,
                illustration_root=self.root,
                intent_id=intent_id,
                image_bytes=MINIMAL_PNG,
                content_type="image/png",
                actor="owner",
                now=NOW,
            )
        self.assertEqual(again.exception.code, "ILLUS_ALREADY_ILLUSTRATED")

    def test_current_advance_stales_then_new_intent(self) -> None:
        _publish_rabbit(self.library)
        created = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
        )
        intent_id = created["intent_id"]
        submit_image(
            library=self.library,
            illustration_root=self.root,
            intent_id=intent_id,
            image_bytes=MINIMAL_PNG,
            content_type="image/png",
            actor="owner",
            now=NOW,
        )
        _publish_rabbit_revision_two(self.library)
        with self.assertRaises(KnowledgeContractError) as moved:
            load_intent(
                library=self.library,
                illustration_root=self.root,
                intent_id=intent_id,
                now=NOW,
            )
        self.assertEqual(moved.exception.code, "ILLUS_CURRENT_MOVED")
        with self.assertRaises(KnowledgeContractError) as image_moved:
            read_hero_png(
                library=self.library,
                illustration_root=self.root,
                intent_id=intent_id,
                now=NOW,
            )
        self.assertEqual(image_moved.exception.code, "ILLUS_CURRENT_MOVED")
        with self.assertRaises(KnowledgeContractError) as cancel_moved:
            cancel_intent(
                library=self.library,
                illustration_root=self.root,
                intent_id=intent_id,
                now=NOW,
            )
        self.assertEqual(cancel_moved.exception.code, "ILLUS_CURRENT_MOVED")
        fresh = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
        )
        self.assertNotEqual(fresh["intent_id"], intent_id)
        self.assertEqual(fresh["knowledge_revision"], 2)

    def test_cancel_open_then_new_intent(self) -> None:
        _publish_rabbit(self.library)
        created = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
        )
        cancelled = cancel_intent(
            library=self.library,
            illustration_root=self.root,
            intent_id=created["intent_id"],
            now=NOW,
        )
        self.assertEqual(cancelled["state"], "cancelled")
        with self.assertRaises(KnowledgeContractError) as ctx:
            read_hero_png(
                library=self.library,
                illustration_root=self.root,
                intent_id=created["intent_id"],
                now=NOW,
            )
        self.assertEqual(ctx.exception.code, "ILLUS_NOT_ILLUSTRATED")
        second = create_intent(
            library=self.library,
            illustration_root=self.root,
            topic_slug="rabbit",
            actor="owner",
            now=NOW,
        )
        self.assertNotEqual(second["intent_id"], created["intent_id"])
        with self.assertRaises(KnowledgeContractError) as actor_err:
            create_intent(
                library=self.library,
                illustration_root=self.root,
                topic_slug="rabbit",
                actor="machine",
                now=NOW,
            )
        self.assertEqual(actor_err.exception.code, "ILLUS_UNAUTHORIZED")
```

- [ ] **Step 2: Run tests — expect FAIL** (`create_intent` missing)

Run: `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration.IntentPipelineTests -v`

Expected: FAIL with `ImportError` / `create_intent` not found

- [ ] **Step 3: Implement `store.py` and `pipeline.py`**

`store.py` (atomic `os.replace` like compile store):

```python
from __future__ import annotations

import os
import re
from pathlib import Path

from cognitive_card_server.knowledge_contract.model import (
    KnowledgeContractError,
    canonical_json,
    parse_canonical_document,
)

INTENT_SCHEMA = "cognitive-card-illustration-intent-v1"
_INTENT_ID = re.compile(r"^ii_[0-9a-f]{32}$")


def intent_id_ok(intent_id: str) -> bool:
    return isinstance(intent_id, str) and _INTENT_ID.fullmatch(intent_id) is not None


def intent_dir(root: Path, intent_id: str) -> Path:
    if not intent_id_ok(intent_id):
        raise KnowledgeContractError("ILLUS_NO_INTENT", str(intent_id))
    return Path(root) / intent_id


def read_meta(root: Path, intent_id: str) -> dict[str, object]:
    path = intent_dir(root, intent_id) / "meta.json"
    if path.is_symlink() or not path.is_file():
        raise KnowledgeContractError("ILLUS_NO_INTENT", intent_id)
    try:
        payload = parse_canonical_document(path.read_bytes(), expected_schema=INTENT_SCHEMA)
    except KnowledgeContractError as error:
        raise KnowledgeContractError("ILLUS_NO_INTENT", intent_id) from error
    if not isinstance(payload, dict) or payload.get("intent_id") != intent_id:
        raise KnowledgeContractError("ILLUS_NO_INTENT", intent_id)
    return payload


def write_meta(root: Path, intent: dict[str, object]) -> None:
    intent_id = str(intent["intent_id"])
    directory = intent_dir(root, intent_id)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "meta.json"
    temporary = directory / ".meta.json.tmp"
    try:
        temporary.write_bytes(canonical_json(intent))
        os.replace(temporary, destination)
    except Exception:
        if temporary.exists():
            temporary.unlink(missing_ok=True)
        raise


def write_prompt(root: Path, intent_id: str, text: str) -> None:
    path = intent_dir(root, intent_id) / "expanded_prompt.txt"
    path.write_text(text, encoding="utf-8")


def read_prompt(root: Path, intent_id: str) -> str:
    path = intent_dir(root, intent_id) / "expanded_prompt.txt"
    if path.is_symlink() or not path.is_file():
        raise KnowledgeContractError("ILLUS_NO_INTENT", intent_id)
    return path.read_text(encoding="utf-8")


def write_hero(root: Path, intent_id: str, payload: bytes) -> None:
    (intent_dir(root, intent_id) / "hero.png").write_bytes(payload)


def hero_path(root: Path, intent_id: str) -> Path:
    return intent_dir(root, intent_id) / "hero.png"


def list_intents(root: Path) -> list[dict[str, object]]:
    base = Path(root)
    if base.is_symlink() or not base.is_dir():
        return []
    records: list[dict[str, object]] = []
    for child in base.iterdir():
        if child.is_symlink() or not child.is_dir() or not intent_id_ok(child.name):
            continue
        try:
            records.append(read_meta(base, child.name))
        except KnowledgeContractError:
            continue
    return records
```

`pipeline.py`:

```python
from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from cognitive_card_server.knowledge_contract.model import (
    KnowledgeContractError,
    sha256_hex,
)
from cognitive_card_server.knowledge_illustration.prompt import (
    PNG_MAGIC,
    PNG_MAX_BYTES,
    TEMPLATE_ID,
    active_propositions,
    expand_prompt,
    template_sha256,
)
from cognitive_card_server.knowledge_illustration.store import (
    INTENT_SCHEMA,
    hero_path,
    list_intents,
    read_meta,
    read_prompt,
    write_hero,
    write_meta,
    write_prompt,
)
from cognitive_card_server.knowledge_library.store import KnowledgeLibrary, load_package

RESERVED_ACTORS = frozenset({"qa-01-v1", "publish-01-v1", "machine"})
_SLUG = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_NON_TERMINAL = frozenset({"open", "failed", "illustrated"})
_MOVED = frozenset(
    {
        "KNOWLEDGE_LIBRARY_CURRENT_NOT_FOUND",
        "KNOWLEDGE_LIBRARY_REVISION_NOT_CURRENT",
        "LIBRARY_POINTER_MISMATCH",
    }
)


def create_intent(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    topic_slug: str,
    actor: str,
    now: datetime,
    idempotency_key: str | None = None,
) -> dict[str, object]:
    cleaned_actor = _require_actor(actor)
    if not isinstance(topic_slug, str) or _SLUG.fullmatch(topic_slug) is None:
        raise KnowledgeContractError("ILLUS_SLUG_INVALID", "topic_slug")
    if idempotency_key:
        existing = _intent_for_idempotency(illustration_root, idempotency_key)
        if existing is not None:
            same = (
                existing.get("topic_slug") == topic_slug
                and existing.get("actor") == cleaned_actor
            )
            if same:
                return _public(illustration_root, existing, _core_if_current(library, existing, now))
            raise KnowledgeContractError("ILLUS_INTENT_ACTIVE", "idempotency_key")
    stored = library.get_current(topic_slug, now=now)
    if stored is None:
        raise KnowledgeContractError("ILLUS_NO_CURRENT", "topic_slug", topic_slug)
    for record in list_intents(illustration_root):
        if record.get("topic_slug") == topic_slug and record.get("state") in _NON_TERMINAL:
            raise KnowledgeContractError("ILLUS_INTENT_ACTIVE", "topic_slug", topic_slug)
    core = load_package(stored.directory).knowledge_core
    expanded = expand_prompt(core=core, topic_slug=topic_slug)
    intent_id = "ii_" + secrets.token_hex(16)
    stamp = _stamp(now)
    intent: dict[str, object] = {
        "schema": INTENT_SCHEMA,
        "intent_id": intent_id,
        "state": "open",
        "topic_slug": topic_slug,
        "actor": cleaned_actor,
        "identity": dict(stored.identity),
        "prompt_template_id": TEMPLATE_ID,
        "prompt_template_sha256": template_sha256(),
        "created_at": stamp,
        "updated_at": stamp,
        "idempotency_key": idempotency_key,
        "hero_png_sha256": None,
        "error": None,
        "error_path": None,
    }
    write_meta(illustration_root, intent)
    write_prompt(illustration_root, intent_id, expanded)
    return _public(illustration_root, intent, core)


def submit_image(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    intent_id: str,
    image_bytes: bytes,
    content_type: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    _require_actor(actor)
    intent = read_meta(illustration_root, intent_id)
    if intent.get("state") == "cancelled":
        raise KnowledgeContractError("ILLUS_NOT_ILLUSTRATED", intent_id)
    stored = _sync_current(library, illustration_root, intent, now)
    if intent.get("state") == "illustrated":
        raise KnowledgeContractError("ILLUS_ALREADY_ILLUSTRATED", intent_id)
    if intent.get("state") not in {"open", "failed"}:
        raise KnowledgeContractError("ILLUS_NOT_ILLUSTRATED", "state", str(intent.get("state")))
    if not isinstance(image_bytes, (bytes, bytearray)) or len(image_bytes) > PNG_MAX_BYTES:
        raise KnowledgeContractError("ILLUS_IMAGE_TOO_LARGE", "image")
    media = content_type.split(";", 1)[0].strip().lower()
    if (
        not image_bytes
        or not image_bytes.startswith(PNG_MAGIC)
        or media != "image/png"
    ):
        intent["state"] = "failed"
        intent["error"] = "ILLUS_IMAGE_INVALID"
        intent["updated_at"] = _stamp(now)
        write_meta(illustration_root, intent)
        return _public(illustration_root, intent, load_package(stored.directory).knowledge_core)
    write_hero(illustration_root, intent_id, bytes(image_bytes))
    intent["state"] = "illustrated"
    intent["error"] = None
    intent["hero_png_sha256"] = "sha256:" + sha256_hex(bytes(image_bytes))
    intent["updated_at"] = _stamp(now)
    write_meta(illustration_root, intent)
    return _public(illustration_root, intent, load_package(stored.directory).knowledge_core)


def cancel_intent(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    intent_id: str,
    now: datetime,
) -> dict[str, object]:
    intent = read_meta(illustration_root, intent_id)
    if intent.get("state") == "cancelled":
        return _public(illustration_root, intent, None)
    stored = _sync_current(library, illustration_root, intent, now)
    intent["state"] = "cancelled"
    intent["updated_at"] = _stamp(now)
    write_meta(illustration_root, intent)
    core = load_package(stored.directory).knowledge_core if stored is not None else None
    return _public(illustration_root, intent, core)


def load_intent(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    intent_id: str,
    now: datetime,
) -> dict[str, object]:
    intent = read_meta(illustration_root, intent_id)
    if intent.get("state") == "cancelled":
        return _public(illustration_root, intent, None)
    stored = _sync_current(library, illustration_root, intent, now)
    return _public(
        illustration_root, intent, load_package(stored.directory).knowledge_core
    )


def read_hero_png(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    intent_id: str,
    now: datetime,
) -> bytes:
    intent = read_meta(illustration_root, intent_id)
    if intent.get("state") == "cancelled":
        raise KnowledgeContractError("ILLUS_NOT_ILLUSTRATED", intent_id)
    _sync_current(library, illustration_root, intent, now)
    if intent.get("state") != "illustrated":
        raise KnowledgeContractError("ILLUS_NOT_ILLUSTRATED", intent_id)
    path = hero_path(illustration_root, intent_id)
    if path.is_symlink() or not path.is_file():
        raise KnowledgeContractError("ILLUS_NOT_ILLUSTRATED", intent_id)
    return path.read_bytes()


def _sync_current(
    library: KnowledgeLibrary,
    root: Path,
    intent: dict[str, object],
    now: datetime,
):
    if intent.get("state") == "stale":
        raise KnowledgeContractError("ILLUS_CURRENT_MOVED", str(intent["intent_id"]))
    identity = intent.get("identity")
    if not isinstance(identity, dict):
        raise KnowledgeContractError("ILLUS_CURRENT_MOVED", str(intent["intent_id"]))
    try:
        return library.require_current_identity(identity, now=now)
    except KnowledgeContractError as error:
        if error.code in _MOVED:
            intent["state"] = "stale"
            intent["updated_at"] = _stamp(now)
            write_meta(root, intent)
            raise KnowledgeContractError(
                "ILLUS_CURRENT_MOVED", str(intent["intent_id"])
            ) from error
        raise


def _public(
    root: Path, intent: dict[str, object], core: dict[str, object] | None
) -> dict[str, object]:
    payload = dict(intent)
    payload["expanded_prompt"] = read_prompt(root, str(intent["intent_id"]))
    identity = intent.get("identity")
    payload["knowledge_revision"] = (
        identity.get("revision") if isinstance(identity, dict) else None
    )
    payload["propositions"] = active_propositions(core) if isinstance(core, dict) else []
    return payload


def _core_if_current(library: KnowledgeLibrary, intent: dict[str, object], now: datetime):
    identity = intent.get("identity")
    if not isinstance(identity, dict):
        return None
    try:
        stored = library.require_current_identity(identity, now=now)
    except KnowledgeContractError:
        return None
    return load_package(stored.directory).knowledge_core


def _require_actor(actor: object) -> str:
    if not isinstance(actor, str) or not actor.strip():
        raise KnowledgeContractError("ILLUS_UNAUTHORIZED", "actor")
    cleaned = actor.strip()
    if cleaned in RESERVED_ACTORS:
        raise KnowledgeContractError("ILLUS_UNAUTHORIZED", "actor")
    return cleaned


def _intent_for_idempotency(root: Path, key: str) -> dict[str, object] | None:
    for record in list_intents(root):
        if record.get("idempotency_key") == key:
            return record
    return None


def _stamp(now: datetime) -> str:
    utc = now.astimezone(timezone.utc)
    if utc.microsecond:
        return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond:06d}Z"
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")
```

`submit_image` size check: `len(image_bytes) > PNG_MAX_BYTES` raises `ILLUS_IMAGE_TOO_LARGE` **before** magic/type checks. Empty `b""` is invalid PNG, not too large.

Copy `identity` with `dict(stored.identity)`. Update `__init__.py` to export `create_intent`, `submit_image`, `cancel_intent`, `load_intent`, `read_hero_png`, `INTENT_SCHEMA`, `RESERVED_ACTORS`.

- [ ] **Step 4: Run tests — expect PASS**

Run: `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration -v`

Expected: PASS (PromptExpandTests + IntentPipelineTests)

---

## Phase 2: HTTP and ops HTML

### Task 3: Admin HTTP, error map, multipart exception

**Files:**
- Modify: `src/cognitive_card_server/http/errors.py` (`_STATUS_BY_CODE`, `_CONFLICT_CODES`, `_NOT_FOUND_CODES`)
- Modify: `src/cognitive_card_server/http/app.py` (`PROTECTED_ROUTES` + `RequestSizeLimitMiddleware` JSON/multipart gate)
- Modify: `src/cognitive_card_server/knowledge_ops/http.py` (admin illustration routes)
- Modify: `pyproject.toml` (add `python-multipart>=0.0.9,<1`)
- Test: `tests/test_http_knowledge_illustration.py`

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_illustration tests.test_knowledge_illustration tests.test_http_knowledge_compile -v` → all pass
**Depends on:** Task 2 (`create_intent`, `submit_image`, `load_intent`, `cancel_intent`, `read_hero_png`)

**Interfaces:**
- Consumes: Task 2 pipeline; `knowledge_library(settings)`; `settings.candidate_root / "illustration-intents"`
- Produces: admin prefix `/card-os/api/v1/admin/knowledge-illustration`

| Method | Path | Handler |
| --- | --- | --- |
| POST | `/` | JSON `{topic_slug, actor}`; header `Idempotency-Key` optional |
| GET | `/{intent_id}` | public intent |
| POST | `/{intent_id}/image` | multipart fields `image`, `actor` |
| GET | `/{intent_id}/image` | PNG bytes, `Cache-Control: private` |
| POST | `/{intent_id}/cancel` | cancel |

Install parser (do not lock):

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && .venv/bin/pip install 'python-multipart>=0.0.9'
```

Add `"python-multipart>=0.0.9,<1"` to `pyproject.toml` `dependencies`. Do not run `uv lock`. Do not stage `uv.lock`.

- [ ] **Step 1: Write HTTP tests** in `tests/test_http_knowledge_illustration.py`

```python
"""HTTP tests for admin illustration-intent."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from cognitive_card_server.auth.model import Scope
from cognitive_card_server.auth.repository import SQLiteTokenRepository
from cognitive_card_server.auth.service import TokenService
from cognitive_card_server.http.app import create_app
from cognitive_card_server.http.config import ApiSettings
from cognitive_card_server.knowledge_contract.authoring import compile_authoring_request
from tests.test_http_knowledge_library import FixedClock, package_payload
from tests.test_knowledge_illustration import MINIMAL_PNG

REPO_ROOT = Path(__file__).resolve().parents[1]
ILLUS_URL = "/card-os/api/v1/admin/knowledge-illustration"


def _rabbit_real():
    path = REPO_ROOT / "examples" / "authoring" / "rabbit-real.json"
    return compile_authoring_request(json.loads(path.read_text(encoding="utf-8")))


class HttpKnowledgeIllustrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.settings = ApiSettings(
            database=root / "server.sqlite3",
            candidate_root=root / "private-candidates",
            repo_root=REPO_ROOT,
        )
        self.clock = FixedClock()
        self.app = create_app(self.settings, self.clock)
        self.client_context = TestClient(self.app, raise_server_exceptions=False)
        self.client = self.client_context.__enter__()
        self.admin = self._issue("admin-operator", Scope.ADMIN)
        self.reader = self._issue("read-client", Scope.READ)
        self.submitter = self._issue("submit-client", Scope.SUBMIT)
        self.headers = {
            "X-Card-OS-Protocol": "1",
            "X-Card-OS-Skill-Release": "0.1.0",
        }

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.temp.cleanup()

    def _issue(self, subject: str, scope: Scope) -> str:
        repository = SQLiteTokenRepository(self.settings.database)
        try:
            raw, _ = TokenService(repository, self.clock).issue(
                subject=subject, scopes=frozenset({scope})
            )
            return raw
        finally:
            repository.close()

    def _auth(self, token: str) -> dict[str, str]:
        return {**self.headers, "Authorization": f"Bearer {token}"}

    def _publish_rabbit(self) -> None:
        created = self.client.post(
            "/card-os/api/v1/admin/knowledge-library/publish",
            headers=self._auth(self.admin),
            json=package_payload(_rabbit_real()),
        )
        self.assertEqual(created.status_code, 201, created.text)

    def test_without_token_and_wrong_scopes(self) -> None:
        denied = self.client.post(ILLUS_URL, json={"topic_slug": "rabbit", "actor": "owner"})
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(denied.json()["error"]["code"], "AUTH_REQUIRED")
        self._publish_rabbit()
        for token in (self.reader, self.submitter):
            blocked = self.client.post(
                ILLUS_URL,
                headers=self._auth(token),
                json={"topic_slug": "rabbit", "actor": "owner"},
            )
            self.assertEqual(blocked.status_code, 403, blocked.text)
            self.assertEqual(blocked.json()["error"]["code"], "AUTH_SCOPE_REQUIRED")

    def test_no_current_conflict_then_create_upload_get_image(self) -> None:
        missing = self.client.post(
            ILLUS_URL,
            headers=self._auth(self.admin),
            json={"topic_slug": "rabbit", "actor": "owner"},
        )
        self.assertEqual(missing.status_code, 409, missing.text)
        self.assertEqual(missing.json()["error"]["code"], "ILLUS_NO_CURRENT")
        self._publish_rabbit()
        created = self.client.post(
            ILLUS_URL,
            headers=self._auth(self.admin),
            json={"topic_slug": "rabbit", "actor": "owner"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        body = created.json()
        intent_id = body["intent_id"]
        self.assertIn("final_content_lock_sha256", body["identity"])
        self.assertNotIn("canonical_claim", json.dumps(body["propositions"]))
        claim = body["propositions"][0]["claim"]
        self.assertNotIn(claim, body["expanded_prompt"])
        bad = self.client.post(
            f"{ILLUS_URL}/{intent_id}/image",
            headers=self._auth(self.admin),
            files={"image": ("x.bin", b"not-png", "image/png")},
            data={"actor": "owner"},
        )
        self.assertEqual(bad.status_code, 200, bad.text)
        self.assertEqual(bad.json()["state"], "failed")
        self.assertEqual(bad.json()["error"], "ILLUS_IMAGE_INVALID")
        uploaded = self.client.post(
            f"{ILLUS_URL}/{intent_id}/image",
            headers=self._auth(self.admin),
            files={"image": ("hero.png", MINIMAL_PNG, "image/png")},
            data={"actor": "owner"},
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        self.assertEqual(uploaded.json()["state"], "illustrated")
        image = self.client.get(
            f"{ILLUS_URL}/{intent_id}/image",
            headers=self._auth(self.admin),
        )
        self.assertEqual(image.status_code, 200, image.text)
        self.assertEqual(image.headers.get("content-type"), "image/png")
        self.assertEqual(image.headers.get("cache-control"), "private")
        self.assertEqual(image.content, MINIMAL_PNG)
        digest = "sha256:" + hashlib.sha256(image.content).hexdigest()
        self.assertEqual(uploaded.json()["hero_png_sha256"], digest)
        anon = self.client.get(f"{ILLUS_URL}/{intent_id}/image")
        self.assertEqual(anon.status_code, 401)
        self.assertEqual(anon.json()["error"]["code"], "AUTH_REQUIRED")
        json_image = self.client.post(
            f"{ILLUS_URL}/{intent_id}/image",
            headers=self._auth(self.admin),
            json={"actor": "owner"},
        )
        self.assertEqual(json_image.status_code, 415)
        self.assertEqual(json_image.json()["error"]["code"], "UNSUPPORTED_MEDIA_TYPE")

    def test_http_current_advance_stales(self) -> None:
        self._publish_rabbit()
        created = self.client.post(
            ILLUS_URL,
            headers=self._auth(self.admin),
            json={"topic_slug": "rabbit", "actor": "owner"},
        )
        self.assertEqual(created.status_code, 200, created.text)
        intent_id = created.json()["intent_id"]
        request = json.loads(
            (REPO_ROOT / "examples" / "authoring" / "rabbit-real.json").read_text(
                encoding="utf-8"
            )
        )
        request["topic"]["revision"] = 2
        republish = self.client.post(
            "/card-os/api/v1/admin/knowledge-library/publish",
            headers=self._auth(self.admin),
            json=package_payload(compile_authoring_request(request)),
        )
        self.assertEqual(republish.status_code, 201, republish.text)
        moved = self.client.get(
            f"{ILLUS_URL}/{intent_id}",
            headers=self._auth(self.admin),
        )
        self.assertEqual(moved.status_code, 409, moved.text)
        self.assertEqual(moved.json()["error"]["code"], "ILLUS_CURRENT_MOVED")

    def test_multipart_not_accepted_on_compile(self) -> None:
        compile_post = self.client.post(
            "/card-os/api/v1/admin/knowledge-compile",
            headers=self._auth(self.admin),
            files={"image": ("hero.png", MINIMAL_PNG, "image/png")},
            data={"topic_slug": "cat", "subject": "家猫", "goal": "认识猫", "actor": "owner"},
        )
        self.assertEqual(compile_post.status_code, 415)
        self.assertEqual(compile_post.json()["error"]["code"], "UNSUPPORTED_MEDIA_TYPE")
```

- [ ] **Step 2: Run — expect FAIL** (route 404 / `UNSUPPORTED_MEDIA_TYPE` on the illustration image POST)

- [ ] **Step 3: Implement errors, PROTECTED_ROUTES, middleware exception, HTTP handlers**

`errors.py` additions:

```python
_STATUS_BY_CODE = {
    # existing keys unchanged...
    "ILLUS_IMAGE_TOO_LARGE": 413,
}

_CONFLICT_CODES = {
    # existing...
    "ILLUS_NO_CURRENT",
    "ILLUS_INTENT_ACTIVE",
    "ILLUS_ALREADY_ILLUSTRATED",
    "ILLUS_CURRENT_MOVED",
    "ILLUS_NOT_ILLUSTRATED",
}

_NOT_FOUND_CODES = {
    # existing...
    "ILLUS_NO_INTENT",
}
```

Leave `ILLUS_SLUG_INVALID`, `ILLUS_IMAGE_INVALID`, `ILLUS_UNAUTHORIZED` as default 400.

`app.py` — insert these `PROTECTED_ROUTES` **immediately before** the compile `{intent_id}/reply` entry so illustration paths match first:

```python
    _protected_route(
        "POST",
        API_PREFIX + "/admin/knowledge-illustration/{intent_id}/image",
        re.escape(API_PREFIX)
        + r"/admin/knowledge-illustration/ii_[0-9a-f]{32}/image",
        Scope.ADMIN,
    ),
    _protected_route(
        "GET",
        API_PREFIX + "/admin/knowledge-illustration/{intent_id}/image",
        re.escape(API_PREFIX)
        + r"/admin/knowledge-illustration/ii_[0-9a-f]{32}/image",
        Scope.ADMIN,
    ),
    _protected_route(
        "POST",
        API_PREFIX + "/admin/knowledge-illustration/{intent_id}/cancel",
        re.escape(API_PREFIX)
        + r"/admin/knowledge-illustration/ii_[0-9a-f]{32}/cancel",
        Scope.ADMIN,
    ),
    _protected_route(
        "GET",
        API_PREFIX + "/admin/knowledge-illustration/{intent_id}",
        re.escape(API_PREFIX) + r"/admin/knowledge-illustration/ii_[0-9a-f]{32}",
        Scope.ADMIN,
    ),
    _protected_route(
        "POST",
        API_PREFIX + "/admin/knowledge-illustration",
        re.escape(API_PREFIX) + r"/admin/knowledge-illustration",
        Scope.ADMIN,
    ),
```

Replace the JSON-only check in `RequestSizeLimitMiddleware.__call__` (the block that currently rejects non-JSON when `total` is non-zero) with:

```python
        content_type = headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        path = scope.get("path")
        method = scope.get("method")
        illustration_image = (
            method == "POST"
            and isinstance(path, str)
            and re.fullmatch(
                re.escape(API_PREFIX)
                + r"/admin/knowledge-illustration/ii_[0-9a-f]{32}/image",
                path,
            )
            is not None
        )
        if total and content_type == "application/json":
            pass
        elif total and content_type == "multipart/form-data" and illustration_image:
            pass
        elif total:
            await self._reject(scope, send, code="UNSUPPORTED_MEDIA_TYPE", status=415)
            return
```

Do not use `API_PREFIX` if the class cannot see it — `RequestSizeLimitMiddleware` is in the same module, so `API_PREFIX` is in scope. Do not allow multipart on any other path.

`http.py` — import pipeline functions; add `_illustration_root`; register routes **before** `app.include_router(pages)` (API router is the one passed in). Use `File`/`Form`/`UploadFile`/`FileResponse`.

```python
from fastapi import File, Form, UploadFile
from starlette.responses import FileResponse, HTMLResponse, Response

def _illustration_root(settings: ApiSettings) -> Path:
    return settings.candidate_root / "illustration-intents"
```

Handlers (sync, matching compile):

```python
    @api_router.post("/admin/knowledge-illustration")
    def admin_create_illustration(
        request: Request,
        payload: dict[str, object] = Body(...),
        principal: TokenPrincipal = Depends(require_admin),
    ) -> dict[str, object]:
        del principal
        topic_slug = payload.get("topic_slug")
        actor = payload.get("actor")
        return create_intent(
            library=knowledge_library(settings),
            illustration_root=_illustration_root(settings),
            topic_slug=topic_slug if isinstance(topic_slug, str) else "",
            actor=actor if isinstance(actor, str) else "",
            now=clock(),
            idempotency_key=request.headers.get("Idempotency-Key"),
        )

    @api_router.get("/admin/knowledge-illustration/{intent_id}")
    def admin_get_illustration(
        intent_id: str,
        principal: TokenPrincipal = Depends(require_admin),
    ) -> dict[str, object]:
        del principal
        return load_intent(
            library=knowledge_library(settings),
            illustration_root=_illustration_root(settings),
            intent_id=intent_id,
            now=clock(),
        )

    @api_router.post("/admin/knowledge-illustration/{intent_id}/image")
    def admin_upload_illustration(
        intent_id: str,
        image: UploadFile = File(...),
        actor: str = Form(""),
        principal: TokenPrincipal = Depends(require_admin),
    ) -> dict[str, object]:
        del principal
        payload = image.file.read()
        return submit_image(
            library=knowledge_library(settings),
            illustration_root=_illustration_root(settings),
            intent_id=intent_id,
            image_bytes=payload if isinstance(payload, bytes) else b"",
            content_type=image.content_type or "",
            actor=actor,
            now=clock(),
        )

    @api_router.get("/admin/knowledge-illustration/{intent_id}/image")
    def admin_get_illustration_image(
        intent_id: str,
        principal: TokenPrincipal = Depends(require_admin),
    ) -> Response:
        del principal
        root = _illustration_root(settings)
        read_hero_png(
            library=knowledge_library(settings),
            illustration_root=root,
            intent_id=intent_id,
            now=clock(),
        )
        path = root / intent_id / "hero.png"
        try:
            resolved = path.resolve()
            base = (root / intent_id).resolve()
        except OSError as error:
            raise KnowledgeContractError("ILLUS_NOT_ILLUSTRATED", intent_id) from error
        if path.is_symlink() or not resolved.is_relative_to(base):
            raise KnowledgeContractError("ILLUS_NOT_ILLUSTRATED", intent_id)
        return FileResponse(
            path,
            media_type="image/png",
            headers={"Cache-Control": "private"},
        )

    @api_router.post("/admin/knowledge-illustration/{intent_id}/cancel")
    def admin_cancel_illustration(
        intent_id: str,
        principal: TokenPrincipal = Depends(require_admin),
    ) -> dict[str, object]:
        del principal
        return cancel_intent(
            library=knowledge_library(settings),
            illustration_root=_illustration_root(settings),
            intent_id=intent_id,
            now=clock(),
        )
```

`read_hero_png` already enforces state; FileResponse is only reached on success.

Invalid PNG HTTP status: pipeline **returns** failed intent (200), matching `submit_reply`. The test above expects 200 + `state=failed`. Do not raise `ILLUS_IMAGE_INVALID` on that path.

- [ ] **Step 4: Run HTTP + illustration + compile HTTP tests — expect PASS**

Run: `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_illustration tests.test_knowledge_illustration tests.test_http_knowledge_compile -v`

Expected: PASS

Then run the combined 62+new gate (Global Constraints). Expected: PASS, count = 62 + new tests from Tasks 1–3.

---

### Task 4: Ops HTML — topic entry and illustration page

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Modify: `src/cognitive_card_server/knowledge_ops/http.py` (HTML route before `{topic}`)
- Test: `tests/test_http_knowledge_illustration.py` (append shell tests)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_illustration tests.test_http_knowledge_ops tests.test_http_knowledge_compile -v` → all pass
**Depends on:** Task 3 (admin JSON + image GET)

**Interfaces:**
- Consumes: `GET/POST /card-os/api/v1/admin/knowledge-illustration...`
- Produces:
  - `render_illustration_html(intent_id: str) -> bytes`
  - `GET /card-os/ops/illustration/{intent_id}` HTML shell
  - Topic detail JS control `id="open-illustration"` text `主体插画` created only after current JSON loads (the label string may exist in the script source; claims and expanded prompt text must not)

- [ ] **Step 1: Write failing shell tests** (append to `HttpKnowledgeIllustrationTests`)

```python
    def test_ops_shells_have_no_prompt_or_claims(self) -> None:
        self._publish_rabbit()
        created = self.client.post(
            ILLUS_URL,
            headers=self._auth(self.admin),
            json={"topic_slug": "rabbit", "actor": "owner"},
        )
        prompt = created.json()["expanded_prompt"]
        claim = created.json()["propositions"][0]["claim"]
        intent_id = created.json()["intent_id"]
        topic = self.client.get("/card-os/ops/rabbit")
        self.assertEqual(topic.status_code, 200)
        self.assertIn("open-illustration", topic.text)
        self.assertNotIn(prompt, topic.text)
        self.assertNotIn(claim, topic.text)
        self.assertNotIn("Merck", topic.text)
        page = self.client.get(f"/card-os/ops/illustration/{intent_id}")
        self.assertEqual(page.status_code, 200)
        self.assertIn("data-intent-id", page.text)
        self.assertNotIn(prompt, page.text)
        self.assertNotIn(claim, page.text)
        self.assertNotIn("must not contain any text", page.text)
        captured = self.client.get("/card-os/ops/illustration")
        self.assertEqual(captured.status_code, 200)
        self.assertNotIn("data-intent-id", captured.text)

    def test_index_does_not_embed_png_or_prompt(self) -> None:
        index_page = self.client.get("/card-os/ops/")
        self.assertEqual(index_page.status_code, 200)
        self.assertNotIn(MINIMAL_PNG[:8].decode("latin1"), index_page.text)
        self.assertNotIn("illustration-hero-v1", index_page.text)
```

- [ ] **Step 2: Run — expect FAIL** (`/card-os/ops/illustration/{id}` captured as topic, no `data-intent-id`)

- [ ] **Step 3: Implement pages + route order**

In `attach_ops_routes`, after the compile intent HTML route and **before** `{topic}`:

```python
from cognitive_card_server.knowledge_ops.pages import (
    render_compile_html,
    render_compile_intent_html,
    render_detail_html,
    render_illustration_html,
    render_index_html,
)
```

Add `render_illustration_html` to that existing import (do not add a second import). Then:

```python
    @pages.api_route("/card-os/ops/illustration/{intent_id}", methods=["GET", "HEAD"])
    def ops_illustration_intent(intent_id: str) -> HTMLResponse:
        return HTMLResponse(render_illustration_html(intent_id))
```

Import `render_illustration_html` in `http.py` next to the compile HTML imports.

`pages.py` — add these functions next to the compile shells (regular strings, **not** inside the `_document` f-string):

```python
def render_illustration_html(intent_id: str) -> bytes:
    escaped_intent = html.escape(intent_id, quote=True)
    return _compile_shell(
        title="Hero illustration",
        heading="Hero illustration",
        body_attrs=f' data-intent-id="{escaped_intent}"',
        body='<p>Operator workbench. Prompt text and image load only after an admin token is stored locally.</p>\n<div id="panel"></div>',
        script=_ILLUSTRATION_SCRIPT,
    )
```

```javascript
_ILLUSTRATION_SCRIPT = """(function () {
  var STORAGE = "cardOsAdminToken";
  var PROTOCOL = "1";
  var SKILL = "0.1.0";
  var tokenInput = document.getElementById("token");
  var panel = document.getElementById("panel");
  var intentId = document.body.getAttribute("data-intent-id") || "";

  function headers() {
    var token = sessionStorage.getItem(STORAGE) || ""; // placeholder
    var out = {
      "X-Card-OS-Protocol": PROTOCOL,
      "X-Card-OS-Skill-Release": SKILL
    };
    if (token) out.Authorization = "Bearer " + token;
    return out;
  }

  function show(message) {
    panel.textContent = message;
  }

  function intentUrl(suffix) {
    return "/card-os/api/v1/admin/knowledge-illustration/" + encodeURIComponent(intentId) + (suffix || "");
  }

  function renderIntent(payload) {
    panel.textContent = "";
    var status = document.createElement("p");
    status.textContent = payload.state || "";
    if (payload.error) status.textContent += " — " + payload.error;
    panel.appendChild(status);

    var promptLabel = document.createElement("label");
    promptLabel.textContent = "Prompt";
    var promptBox = document.createElement("textarea");
    promptBox.id = "expanded-prompt";
    promptBox.readOnly = true;
    promptBox.value = payload.expanded_prompt || "";
    promptLabel.appendChild(promptBox);
    panel.appendChild(promptLabel);

    var copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.textContent = "Copy";
    copyBtn.addEventListener("click", function () {
      promptBox.select();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(promptBox.value);
      }
    });
    panel.appendChild(copyBtn);

    var actorLabel = document.createElement("label");
    actorLabel.textContent = "Actor ";
    var actorInput = document.createElement("input");
    actorInput.id = "actor";
    actorInput.value = "owner";
    actorLabel.appendChild(actorInput);
    panel.appendChild(actorLabel);

    if (payload.state === "open" || payload.state === "failed") {
      var file = document.createElement("input");
      file.type = "file";
      file.id = "hero-png";
      file.accept = "image/png";
      panel.appendChild(file);
      var uploadBtn = document.createElement("button");
      uploadBtn.type = "button";
      uploadBtn.textContent = "Upload PNG";
      uploadBtn.addEventListener("click", function () {
        if (!file.files || !file.files[0]) return;
        var body = new FormData();
        body.append("image", file.files[0], "hero.png");
        body.append("actor", actorInput.value || "");
        fetch(intentUrl("/image"), { method: "POST", headers: headers(), body: body })
          .then(function (response) {
            return response.json().then(function (data) {
              if (!response.ok) {
                show((data.error && data.error.code) || ("HTTP " + response.status));
                return;
              }
              load();
            });
          })
          .catch(function () { show("Request failed."); });
      });
      panel.appendChild(uploadBtn);
    }

    if (payload.state === "illustrated") {
      var image = document.createElement("img");
      image.alt = "Hero illustration";
      panel.appendChild(image);
      fetch(intentUrl("/image"), { headers: headers() })
        .then(function (response) {
          if (!response.ok) return null;
          return response.blob();
        })
        .then(function (blob) {
          if (blob) image.src = URL.createObjectURL(blob);
        });
      var list = document.createElement("ol");
      (payload.propositions || []).forEach(function (row) {
        var item = document.createElement("li");
        item.textContent = (row.proposition_id || "") + " [" + (row.certainty || "") + "] " + (row.claim || "");
        list.appendChild(item);
      });
      panel.appendChild(list);
      var cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Cancel";
      cancelBtn.addEventListener("click", function () {
        fetch(intentUrl("/cancel"), { method: "POST", headers: headers() })
          .then(function () { load(); })
          .catch(function () { show("Request failed."); });
      });
      panel.appendChild(cancelBtn);
    }
  }

  function load() {
    if (!sessionStorage.getItem(STORAGE)) {
      show("Token required.");
      return;
    }
    fetch(intentUrl(""), { headers: headers() })
      .then(function (response) {
        return response.json().then(function (body) {
          if (!response.ok) {
            show((body.error && body.error.code) || ("HTTP " + response.status));
            return;
          }
          renderIntent(body);
        });
      })
      .catch(function () { show("Load failed."); });
  }

  document.getElementById("save-token").addEventListener("click", function () {
    var value = tokenInput.value || "";
    if (!value) return;
    sessionStorage.setItem(STORAGE, value);
    tokenInput.value = "";
    load();
  });
  document.getElementById("clear-token").addEventListener("click", function () {
    sessionStorage.removeItem(STORAGE);
    show("Token required.");
  });
  if (sessionStorage.getItem(STORAGE)) load();
  else show("Token required.");
})();
"""
```

Topic detail lives inside `_document`'s f-string, so JS braces stay doubled. Insert immediately after `panel.appendChild(artifact);` (before `loadPointer();`):

```javascript
    var illustration = document.createElement("div");
    illustration.setAttribute("data-panel", "illustration");
    var illustrationHeading = document.createElement("h2");
    illustrationHeading.textContent = "Hero illustration";
    illustration.appendChild(illustrationHeading);
    var illustrationBtn = document.createElement("button");
    illustrationBtn.type = "button";
    illustrationBtn.id = "open-illustration";
    illustrationBtn.textContent = "主体插画";
    illustrationBtn.addEventListener("click", openIllustration);
    illustration.appendChild(illustrationBtn);
    panel.appendChild(illustration);
```

Add `openIllustration` next to `lockMapping` in that same f-string (doubled braces):

```javascript
  function openIllustration() {{
    var out = headers();
    out["Content-Type"] = "application/json";
    fetch("/card-os/api/v1/admin/knowledge-illustration", {{
      method: "POST",
      headers: out,
      body: JSON.stringify({{ topic_slug: topic, actor: "owner" }})
    }}).then(function (response) {{
      return response.json().then(function (body) {{
        if (!response.ok) {{
          show((body.error && body.error.code) || ("HTTP " + response.status));
          return;
        }}
        window.location = "/card-os/ops/illustration/" + body.intent_id;
      }});
    }}).catch(function () {{
      show("Request failed.");
    }});
  }}
```

Do not put `expanded_prompt`, rabbit claims, or template sentences into the static HTML strings. Button id `open-illustration` must appear in the topic-page script source so the shell test can find it.


- [ ] **Step 4: Run ops + illustration + compile HTTP — expect PASS**

Run: `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_illustration tests.test_http_knowledge_ops tests.test_http_knowledge_compile -v`

Expected: PASS

Run the combined 62+new gate. Expected: PASS.

---

## Phase 3: Kids ledger

### Task 5: Docs after green tests

**Files:**
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/ai/CURRENT_TASK.md`
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/ai/HANDOFF.md`
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/cognitive-card-os-roadmap.md`
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/README.md` (add this plan to the Plans table, Status Active)

**Verify:** from kids root: `bash scripts/ai/check-task-state.sh` PASS; `bash scripts/ai/check-handoff.sh` WARN allowed for 现网未执行; `bash scripts/ai/check-doc-governance.sh` WARN allowed for Last Reviewed; `git diff --check` PASS.

**Depends on:** Tasks 1–4 green on the server worktree

Do **not** mark roadmap `IMG-01` `DONE`. Record: server worktree implemented, uncommitted, not production. Paste the real unittest counts from the combined gate.

- [ ] **Step 1: Run the combined focused gate on the server worktree and keep the `Ran N tests` line**

Run the command in Global Constraints. Expected: `OK`. N = 62 + tests added in Tasks 1–4.

- [ ] **Step 2: Fill HANDOFF from real `git status` / `git diff` and that unittest output**

Include Isolation Map (kids vs server worktree @ `91b7cf3` plus new uncommitted server files). Exact Next Action: operator may copy a prompt in ChatGPT by hand; that is not a unittest gate. Do not start 8765 against KNOW-04.

- [ ] **Step 3: Run kids checkers**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack
bash scripts/ai/check-task-state.sh
bash scripts/ai/check-handoff.sh
bash scripts/ai/check-doc-governance.sh
git diff --check
```

Expected: task-state PASS; handoff PASS or WARN (现网); doc-governance WARN for Last Reviewed 2026-07-24 (pre-existing); `git diff --check` silent.

---

## Spec coverage

| Spec section | Task |
| --- | --- |
| §5 intent fields, human actor, idempotency, no current, active intent | 2, 3 |
| §5.1 template: one image, no text, name, classification, active safety_scope, no claims | 1 |
| Snapshot = `LibraryRevision.identity` including `final_content_lock_sha256` | 2 |
| §6 states open/failed/illustrated/cancelled/stale; invalid PNG failed; current moved stale | 2 |
| §7 ops pages, token in sessionStorage, no embed | 4 |
| §8 admin only, no executor token | 3 |
| §9 HTTP + multipart image POST + 12 MiB + PNG magic + Cache-Control private + disk layout | 2, 3 |
| Multipart only on exact image path | 3 |
| §10 active propositions, `canonical_claim`→`claim`, core order | 1, 2 |
| §11 error codes | 2, 3 (`errors.py`) |
| §12 no WB-03 / no new family | Global Constraints |
| §13 acceptance 1–7, fixture PNG, no ChatGPT in tests | 2, 3, 4, combined gate |
| Inline `MINIMAL_PNG`, no binary fixture | Global Constraints, Tasks 1–3 |

## Self-review

- Placeholders: none. `MINIMAL_PNG`, routes, identity keys, and error codes are literal.
- Interface consistency: `create_intent` / `submit_image` / `load_intent` / `cancel_intent` / `read_hero_png` names are identical in Tasks 2–4. Identity keys never renamed. API list field is `claim`.
- Scope: no image API, no claim, no mapping-lock, no Pillow render, no Nginx, no kids `outputs/`, no commit steps.
- Verify commands: each task has a concrete unittest invocation and expected FAIL/PASS. Final gate is the 62-test combined baseline plus new modules.

## Execution notes

Do not open ChatGPT in this plan. Rabbit-real in a tmp library is the unittest current. Operator live image generation stays manual after code is green, still against an injected library root, never KNOW-04 production.
