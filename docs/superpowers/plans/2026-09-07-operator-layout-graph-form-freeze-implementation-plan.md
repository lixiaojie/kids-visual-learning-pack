# Operator Layout Graph Form Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After Confirm current, the operator opens `/ops/layout/{topic}`, sees a legend-role outline of active propositions, edits text / wordless-image / interactive forms on a media-plan draft, and freezes only when a mapping-lock exists, pinning Core identity.

**Architecture:** Library metadata sibling to mapping: `media-plan.json` pointer plus immutable `media-plans/revision-NNNN.json`. First GET layout creates a draft from current propositions and the last Confirm intent’s `image_suggestions.json`. PATCH updates the draft in place. Freeze writes the next frozen revision. Unfreeze copies to a new draft. Outline is derived from current via per-proposition `resolve_legend_role` (failures become `legend_role=null`; do not fail GET). `lock_mapping` and Confirm stay unchanged.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, existing `KnowledgeLibrary`, compile-intent store, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium (5 tasks)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-07-operator-layout-graph-form-freeze-design.md` (Approved). Program: `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md`.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1` @ `4f76aca`.
- Kids repo: `/Users/admin/projects/family/kids-visual-learning-pack`.
- Run tests with `PYTHONPATH=src .venv/bin/python`.
- Do not implement IMG-03 prompt export or PNG upload. Do not call OpenAI APIs.
- Do not change `lock_mapping`, mapping preview, or mapping-lock third-panel JS.
- Do not write media-plan inside Confirm current. Do not write suggestions into four-object files.
- Do not change four-object schema. Do not add a fifth governed object.
- Do not write production knowledge-library. Do not merge/push/release. Do not add `uv.lock` or kids `outputs/`.
- Do not git commit unless the operator asks. Skip every commit step.
- Do not mark GRAPH-01 / FORM-01 / FREEZE-01 / FLOW-01 / API-01 / IMG-03 `DONE`.
- Known combined-gate 2 FAIL on ops mapping-lock `LEGEND_ROLE_MISSING` stay untouched. Do not use `rabbit-composite` as the happy-path fixture.

### Combined focused gate (after Task 4)

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_classification_registry tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_http_auth tests.test_knowledge_library_mapping tests.test_knowledge_layout tests.test_http_knowledge_layout
```

Expected: new tests pass; the two known `LEGEND_ROLE_MISSING` mapping-lock ops fails remain.

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_layout/__init__.py` | Package export |
| `src/cognitive_card_server/knowledge_layout/outline.py` | `build_layout_outline(core)` |
| `src/cognitive_card_server/knowledge_layout/plan.py` | Default nodes, suggestions, form validation, materialize, stale |
| `src/cognitive_card_server/knowledge_layout/pipeline.py` | `get_layout`, `patch_media_plan`, `freeze_media_plan`, `unfreeze_media_plan` |
| `src/cognitive_card_server/knowledge_library/store.py` | Pointer / revision / audit IO for media-plan |
| `src/cognitive_card_server/knowledge_ops/http.py` | GET layout, PATCH media-plan, freeze, unfreeze; ops HTML route |
| `src/cognitive_card_server/knowledge_ops/pages.py` | `render_layout_html`; compile Open layout; detail text link |
| `src/cognitive_card_server/http/errors.py` | New 409/400 codes |
| `tests/test_knowledge_layout.py` | Outline + library pipeline |
| `tests/test_http_knowledge_layout.py` | HTTP + HTML shell |
| `tests/test_http_knowledge_ops.py` | Detail page still claim-free; add layout href without mapping JS rewrite |

Kids (Task 5): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`, `docs/cognitive-card-os-system-design.md`.

---

## Phase 1: Outline and plan functions

### Task 1: Outline builder and media-plan pure functions

**Files:**
- Create: `src/cognitive_card_server/knowledge_layout/__init__.py`
- Create: `src/cognitive_card_server/knowledge_layout/outline.py`
- Create: `src/cognitive_card_server/knowledge_layout/plan.py`
- Test: `tests/test_knowledge_layout.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_layout -v
```

Expected: all pass.

**Depends on:** None.

**Interfaces:**
- Consumes: `resolve_legend_role`, `CONTENT_ROLES` order via this tuple, `KnowledgeContractError`, rabbit-real bundle
- Produces:

```python
ROLE_ORDER = (
    "observe", "compare", "evidence", "time", "place", "learning_place",
    "habit", "kind", "sequence", "setting", "uncertain", "safety",
)
FORMS = frozenset({"text", "wordless-image", "interactive"})
FORBIDDEN_FACETS = frozenset({"safety", "unknown"})
FORBIDDEN_FACT_TYPES = frozenset({"safety", "unknown_boundary"})

def build_layout_outline(core: Mapping[str, object]) -> dict[str, object]:
    """Group active propositions by legend_role. Empty roles omitted.
    resolve_legend_role failures → legend_role None, still listed under unit.
    Units with no active propositions appear as groups with propositions=[].
    """

def active_proposition_ids(core: Mapping[str, object]) -> list[str]: ...

def default_nodes(core: Mapping[str, object]) -> list[dict[str, str]]:
    """Every active id, form=text, stable core proposition order."""

def apply_suggestions(
    nodes: list[dict[str, str]],
    suggestions: list[dict[str, object]] | None,
) -> list[dict[str, str]]:
    """Set form=wordless-image for suggestion ids that exist in nodes. Ignore unknown ids."""

def form_forbidden(core: Mapping[str, object], proposition_id: str, form: str) -> bool: ...

def materialize_nodes(
    core: Mapping[str, object],
    draft_nodes: list[dict[str, object]],
) -> list[dict[str, str]]:
    """One row per active id; form from draft or text. Drop draft ids not on current."""

def is_stale(
    *,
    pointer: Mapping[str, object],
    current_identity: Mapping[str, object] | None,
    mapping: Mapping[str, object] | None,
) -> bool:
    """True when pointer status is frozen and identity or mapping_revision drifted or mapping missing."""
```

- [ ] **Step 1: Write failing tests** in `tests/test_knowledge_layout.py`

```python
"""Layout outline and media-plan pure functions."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from cognitive_card_server.knowledge_contract.authoring import compile_authoring_request
from cognitive_card_server.knowledge_layout.outline import build_layout_outline
from cognitive_card_server.knowledge_layout.plan import (
    apply_suggestions,
    default_nodes,
    form_forbidden,
    is_stale,
    materialize_nodes,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _rabbit():
    path = REPO_ROOT / "examples" / "authoring" / "rabbit-real.json"
    return compile_authoring_request(json.loads(path.read_text(encoding="utf-8")))


class OutlineTests(unittest.TestCase):
    def test_empty_roles_absent_and_units_group(self) -> None:
        core = _rabbit().knowledge_core
        outline = build_layout_outline(core)
        roles = [group["legend_role"] for group in outline["groups"]]
        self.assertNotIn("source", roles)
        self.assertEqual(roles, sorted(roles, key=lambda role: (
            ["observe", "compare", "evidence", "time", "place", "learning_place",
             "habit", "kind", "sequence", "setting", "uncertain", "safety"].index(role)
            if role in {
                "observe", "compare", "evidence", "time", "place", "learning_place",
                "habit", "kind", "sequence", "setting", "uncertain", "safety",
            }
            else 99
        )))
        self.assertTrue(outline["groups"])
        first = outline["groups"][0]
        self.assertIn("units", first)
        prop = first["units"][0]["propositions"][0]
        self.assertIn("proposition_id", prop)
        self.assertIn("claim", prop)
        self.assertIn("coverage_facet", prop)
        self.assertIn("legend_role", prop)
        self.assertIn("related", prop)

    def test_superseded_omitted(self) -> None:
        core = dict(_rabbit().knowledge_core)
        props = list(core["propositions"])
        first = dict(props[0])
        first["standing"] = "superseded"
        core["propositions"] = [first, *props[1:]]
        ids = {
            row["proposition_id"]
            for group in build_layout_outline(core)["groups"]
            for unit in group["units"]
            for row in unit["propositions"]
        }
        self.assertNotIn(first["proposition_id"], ids)


class PlanFunctionTests(unittest.TestCase):
    def test_defaults_all_text_then_suggestions(self) -> None:
        core = _rabbit().knowledge_core
        nodes = default_nodes(core)
        self.assertTrue(nodes)
        self.assertTrue(all(item["form"] == "text" for item in nodes))
        target = nodes[0]["proposition_id"]
        applied = apply_suggestions(
            nodes,
            [{"proposition_id": target, "form": "wordless-image"}],
        )
        matching = next(item for item in applied if item["proposition_id"] == target)
        self.assertEqual("wordless-image", matching["form"])
        ignored = apply_suggestions(nodes, [{"proposition_id": "nope"}])
        self.assertEqual(nodes, ignored)

    def test_safety_wordless_forbidden(self) -> None:
        core = _rabbit().knowledge_core
        safety_id = None
        for unit in core["knowledge_units"]:
            if unit.get("coverage_facet") == "safety":
                ids = unit.get("proposition_ids") or []
                if ids:
                    safety_id = ids[0]
                    break
        if safety_id is None:
            for prop in core["propositions"]:
                if prop.get("fact_type") == "safety":
                    safety_id = prop["proposition_id"]
                    break
        self.assertIsNotNone(safety_id)
        self.assertTrue(form_forbidden(core, safety_id, "wordless-image"))
        self.assertTrue(form_forbidden(core, safety_id, "interactive"))

    def test_materialize_drops_unknown_and_fills_missing(self) -> None:
        core = _rabbit().knowledge_core
        nodes = default_nodes(core)
        extra = nodes + [{"proposition_id": "gone", "form": "text"}]
        extra[0] = {**extra[0], "form": "wordless-image"}
        result = materialize_nodes(core, extra)
        ids = [item["proposition_id"] for item in result]
        self.assertNotIn("gone", ids)
        self.assertEqual(len(ids), len(nodes))
        self.assertEqual("wordless-image", result[0]["form"])

    def test_stale_when_identity_or_mapping_drifts(self) -> None:
        identity = {
            "object_id": "core.rabbit",
            "revision": 1,
            "knowledge_core_sha256": "a",
            "learning_spec_sha256": "b",
            "projection_spec_sha256": "c",
            "final_content_lock_sha256": "sha256:d",
        }
        pointer = {
            "status": "frozen",
            "identity": identity,
            "mapping_revision": 2,
        }
        self.assertFalse(is_stale(pointer=pointer, current_identity=identity, mapping={"revision": 2, "listed": True}))
        drifted = dict(identity)
        drifted["revision"] = 2
        self.assertTrue(is_stale(pointer=pointer, current_identity=drifted, mapping={"revision": 2}))
        self.assertTrue(is_stale(pointer=pointer, current_identity=identity, mapping={"revision": 3}))
        self.assertTrue(is_stale(pointer=pointer, current_identity=identity, mapping=None))
        draft = {"status": "draft", "identity": None, "mapping_revision": None}
        self.assertFalse(is_stale(pointer=draft, current_identity=drifted, mapping=None))
```

- [ ] **Step 2: Run tests — expect FAIL** (`build_layout_outline` not defined)

- [ ] **Step 3: Implement `outline.py` and `plan.py`**

`outline.py`: walk `knowledge_units` then leftover active propositions not in any unit. For each active proposition (`standing` missing or `active`), call `resolve_legend_role` with unit facet / unit `legend_role` / prop `fact_type` / `certainty` / `coverage.coverage_pack_id`. Catch `KnowledgeContractError` → `legend_role=None`. Claim field is `canonical_claim`. `related` = other proposition ids from `relations` where `from_id` or `to_id` is this id. Group by `ROLE_ORDER`; skip empty roles; `legend_role=None` nodes go in a final group only if you attach them under their unit inside an existing role group — put unresolved nodes under their unit still nested in the role `None` group **omitted from `groups`**; instead keep them inside the unit of the nearest resolved sibling’s group, or if the whole unit is unresolved, attach the unit under the first group that exists after a second pass: simpler rule **required by spec**: unresolved props still appear in **their unit**. Place that unit under a group whose `legend_role` is the unit’s resolved role if any child resolved, else skip creating a role group named null — list those units inside `groups` entry `{"legend_role": None, ...}` **only when at least one such prop exists**, and put that entry **last**. Spec said empty roles omitted; `None` is not a LEGEND role so it may appear last as unassigned. Do that.

`plan.py`: implement the signatures above. `form_forbidden` is True when `form != "text"` and facet/fact_type matches forbidden sets. Unknown proposition_id → treat as forbidden True so PATCH can reject via `MEDIA_PLAN_NODE_UNKNOWN` at pipeline layer (pipeline checks membership first).

- [ ] **Step 4: Re-run Task 1 tests — expect PASS**

- [ ] **Step 5: Skip commit** unless the operator asked.

---

## Phase 2: Library IO and writes

### Task 2: Draft GET and PATCH on KnowledgeLibrary

**Files:**
- Create: `src/cognitive_card_server/knowledge_layout/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_library/store.py` (add media-plan pointer/revision/audit next to mapping helpers; do not change `lock_mapping`)
- Modify: `tests/test_knowledge_layout.py` (add pipeline tests)
- Test also: confirm-current still has no `media-plan.json` — add one test using existing compile confirm **or** `library.publish` then `get_layout` as the first write.

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_layout -v
```

**Depends on:** Task 1.

**Interfaces:**
- Consumes: Task 1 functions, `list_intents`, `read_suggestions`, `KnowledgeLibrary.publish`, `get_current`, `get_mapping`
- Produces:

```python
POINTER_SCHEMA = "cognitive-card-knowledge-library-media-plan-v1"
PLAN_SCHEMA = "cognitive-card-media-plan-revision-v1"
RESERVED_ACTORS = frozenset({"qa-01-v1", "publish-01-v1", "machine"})

def get_layout(
    *,
    library: KnowledgeLibrary,
    compile_root: Path,
    topic_slug: str,
    now: datetime,
) -> dict[str, object]:
    """If no current: {"listed": False, "topic_slug": slug}.
    If no pointer: create revision-0001 draft then return view.
    If pointer exists: do not recreate. Always rebuild outline from today's current.
    """

def patch_media_plan(
    *,
    library: KnowledgeLibrary,
    topic_slug: str,
    actor: str,
    nodes: list[dict[str, object]],
    now: datetime,
) -> dict[str, object]: ...
```

Library methods (same atomic `os.replace` as `_write_mapping_pointer`; no symlink follow):

```python
def get_media_plan(self, topic_slug: str) -> dict[str, object] | None: ...
def read_media_plan_revision(self, topic_slug: str, revision: int) -> dict[str, object]: ...
```

- [ ] **Step 1: Write failing pipeline tests** (same test module)

```python
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cognitive_card_server.knowledge_compile.store import write_intent, write_suggestions
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError
from cognitive_card_server.knowledge_layout.pipeline import get_layout, patch_media_plan
from cognitive_card_server.knowledge_library.store import KnowledgeLibrary

NOW = datetime(2026, 9, 7, tzinfo=timezone.utc)

class LayoutDraftTests(unittest.TestCase):
    def test_publish_does_not_write_media_plan(self) -> None:
        rabbit = _rabbit()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            library.publish(rabbit, now=NOW)
            self.assertFalse((library.root / "rabbit" / "media-plan.json").exists())

    def test_first_get_creates_all_text_draft(self) -> None:
        rabbit = _rabbit()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            library.publish(rabbit, now=NOW)
            view = get_layout(
                library=library,
                compile_root=root / "compile-intents",
                topic_slug="rabbit",
                now=NOW,
            )
            self.assertTrue(view["listed"])
            self.assertEqual("draft", view["status"])
            self.assertFalse(view["mapping_listed"])
            self.assertFalse(view["can_freeze"])
            self.assertFalse(view["can_unfreeze"])
            pointer = json.loads((library.root / "rabbit" / "media-plan.json").read_text())
            self.assertEqual(1, pointer["revision"])
            self.assertEqual("create_draft", pointer["reason"])
            plan = json.loads((library.root / "rabbit" / "media-plans" / "revision-0001.json").read_text())
            self.assertTrue(all(node["form"] == "text" for node in plan["nodes"]))
            again = get_layout(
                library=library,
                compile_root=root / "compile-intents",
                topic_slug="rabbit",
                now=NOW,
            )
            self.assertEqual(1, again["revision"])

    def test_suggestions_from_last_confirm_intent(self) -> None:
        rabbit = _rabbit()
        core = rabbit.knowledge_core
        pid = core["propositions"][0]["proposition_id"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            stored = library.publish(rabbit, now=NOW)
            compile_root = root / "compile-intents"
            intent_id = "ci_" + ("ab" * 16)
            intent = {
                "schema": "cognitive-card-compile-intent-v1",
                "intent_id": intent_id,
                "state": "current",
                "round": "complete",
                "topic_slug": "rabbit",
                "subject": "rabbit",
                "goal": "goal",
                "actor": "owner",
                "object_type": "",
                "prompt_template_id": "knowledge-compile-v1",
                "prompt_template_sha256": "0" * 64,
                "expanded_prompt": "x",
                "created_at": "2026-09-07T00:00:00Z",
                "updated_at": "2026-09-07T00:00:00Z",
                "idempotency_key": None,
                "error": None,
                "error_path": None,
                "revision": stored.revision,
            }
            write_intent(compile_root, intent)
            write_suggestions(compile_root, intent_id, [{"proposition_id": pid, "form": "wordless-image"}])
            view = get_layout(library=library, compile_root=compile_root, topic_slug="rabbit", now=NOW)
            plan = json.loads((library.root / "rabbit" / "media-plans" / "revision-0001.json").read_text())
            matching = next(node for node in plan["nodes"] if node["proposition_id"] == pid)
            self.assertEqual("wordless-image", matching["form"])
            self.assertEqual(intent_id, view["source_compile_intent_id"])

    def test_no_current_listed_false(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            view = get_layout(
                library=library,
                compile_root=root / "compile-intents",
                topic_slug="rabbit",
                now=NOW,
            )
            self.assertEqual({"listed": False, "topic_slug": "rabbit"}, view)
            self.assertFalse((library.root / "rabbit" / "media-plan.json").exists())

    def test_patch_draft_and_reject_safety(self) -> None:
        rabbit = _rabbit()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            library.publish(rabbit, now=NOW)
            get_layout(library=library, compile_root=root / "ci", topic_slug="rabbit", now=NOW)
            pid = default_nodes(rabbit.knowledge_core)[0]["proposition_id"]
            patched = patch_media_plan(
                library=library,
                topic_slug="rabbit",
                actor="owner",
                nodes=[{"proposition_id": pid, "form": "wordless-image"}],
                now=NOW,
            )
            self.assertEqual("draft", patched["status"])
            safety_id = None
            for unit in rabbit.knowledge_core["knowledge_units"]:
                if unit.get("coverage_facet") == "safety" and unit.get("proposition_ids"):
                    safety_id = unit["proposition_ids"][0]
                    break
            if safety_id:
                with self.assertRaises(KnowledgeContractError) as raised:
                    patch_media_plan(
                        library=library,
                        topic_slug="rabbit",
                        actor="owner",
                        nodes=[{"proposition_id": safety_id, "form": "wordless-image"}],
                        now=NOW,
                    )
                self.assertEqual("MEDIA_PLAN_FORM_FORBIDDEN", raised.exception.code)
            with self.assertRaises(KnowledgeContractError) as raised:
                patch_media_plan(
                    library=library,
                    topic_slug="rabbit",
                    actor="owner",
                    nodes=[{"proposition_id": "nope", "form": "text"}],
                    now=NOW,
                )
            self.assertEqual("MEDIA_PLAN_NODE_UNKNOWN", raised.exception.code)
```

If `write_intent` rejects the stub dict, open `read_intent` / `write_intent` and include every key they require (copy from `create_intent` return in `tests/test_knowledge_compile.py`).

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement store IO + pipeline get/patch**

Pointer file keys from spec §5.1. Draft `identity` and `mapping_revision` JSON `null`. `source_compile_intent_id` from the chosen intent or `null`.

Find last Confirm intent: `list_intents(compile_root)` → filter `topic_slug == slug` and `state == "current"` → max `(int(revision or 0), str(set_at or ""), intent_id)`.

`get_layout` view keys: `listed`, `topic_slug`, `status` (`draft` or computed `stale`/`frozen`), `revision`, `mapping_listed`, `mapping_revision`, `can_freeze`, `can_unfreeze`, `identity`, `source_compile_intent_id`, `outline` (from `build_layout_outline` with each proposition `form` filled from the pointed plan; extra plan ids omitted from outline; missing current props shown as `text` in outline only).

`_require_actor`: same as compile (`LAYOUT_UNAUTHORIZED`).

PATCH: require current else `LAYOUT_NO_CURRENT`; pointer draft else `MEDIA_PLAN_NOT_DRAFT`; replace only listed ids in the draft file in place (same revision number); `reason=patch`; append `media-plan-audit.jsonl`.

- [ ] **Step 4: Tests PASS**

- [ ] **Step 5: Skip commit**

---

### Task 3: Freeze, unfreeze, stale

**Files:**
- Modify: `src/cognitive_card_server/knowledge_layout/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_library/store.py` (next revision number; refuse overwrite of frozen files)
- Modify: `tests/test_knowledge_layout.py`

**Verify:** same unittest module.

**Depends on:** Task 2.

**Interfaces:**

```python
def freeze_media_plan(
    *,
    library: KnowledgeLibrary,
    topic_slug: str,
    actor: str,
    now: datetime,
) -> dict[str, object]: ...

def unfreeze_media_plan(
    *,
    library: KnowledgeLibrary,
    topic_slug: str,
    actor: str,
    now: datetime,
) -> dict[str, object]: ...
```

- [ ] **Step 1: Failing tests**

```python
class FreezeTests(unittest.TestCase):
    def test_freeze_requires_mapping_and_pins_identity(self) -> None:
        rabbit = _rabbit()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            published = library.publish(rabbit, now=NOW)
            get_layout(library=library, compile_root=root / "ci", topic_slug="rabbit", now=NOW)
            current_bytes = (library.root / "rabbit" / "current.json").read_bytes()
            with self.assertRaises(KnowledgeContractError) as raised:
                freeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
            self.assertEqual("MEDIA_PLAN_MAPPING_REQUIRED", raised.exception.code)
            mapping = library.lock_mapping("rabbit", family="four-card", now=NOW)
            mapping_bytes = (library.root / "rabbit" / "mapping.json").read_bytes()
            view = freeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
            self.assertEqual("frozen", view["status"])
            self.assertEqual(published.identity, view["identity"])
            self.assertEqual(mapping.revision, view["mapping_revision"])
            self.assertEqual(current_bytes, (library.root / "rabbit" / "current.json").read_bytes())
            self.assertEqual(mapping_bytes, (library.root / "rabbit" / "mapping.json").read_bytes())
            self.assertTrue((library.root / "rabbit" / "media-plans" / "revision-0002.json").is_file())
            frozen = json.loads((library.root / "rabbit" / "media-plans" / "revision-0002.json").read_text())
            self.assertEqual("frozen", frozen["status"])
            with self.assertRaises(KnowledgeContractError) as patch_raised:
                patch_media_plan(
                    library=library,
                    topic_slug="rabbit",
                    actor="owner",
                    nodes=[{"proposition_id": frozen["nodes"][0]["proposition_id"], "form": "text"}],
                    now=NOW,
                )
            self.assertEqual("MEDIA_PLAN_NOT_DRAFT", patch_raised.exception.code)

    def test_unfreeze_then_refreeze_keeps_old_file(self) -> None:
        rabbit = _rabbit()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            library.publish(rabbit, now=NOW)
            get_layout(library=library, compile_root=root / "ci", topic_slug="rabbit", now=NOW)
            library.lock_mapping("rabbit", family="four-card", now=NOW)
            freeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
            view = unfreeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
            self.assertEqual("draft", view["status"])
            self.assertTrue((library.root / "rabbit" / "media-plans" / "revision-0002.json").is_file())
            self.assertTrue((library.root / "rabbit" / "media-plans" / "revision-0003.json").is_file())
            freeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
            self.assertTrue((library.root / "rabbit" / "media-plans" / "revision-0004.json").is_file())

    def test_relock_mapping_makes_get_stale(self) -> None:
        rabbit = _rabbit()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = KnowledgeLibrary(root / "library")
            library.publish(rabbit, now=NOW)
            get_layout(library=library, compile_root=root / "ci", topic_slug="rabbit", now=NOW)
            library.lock_mapping("rabbit", family="four-card", now=NOW)
            freeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
            library.lock_mapping("rabbit", family="four-card", now=NOW)
            view = get_layout(library=library, compile_root=root / "ci", topic_slug="rabbit", now=NOW)
            self.assertEqual("stale", view["status"])
            self.assertFalse(view["can_freeze"])
            self.assertTrue(view["can_unfreeze"])
            with self.assertRaises(KnowledgeContractError) as raised:
                freeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
            self.assertEqual("MEDIA_PLAN_NOT_DRAFT", raised.exception.code)
            unfreeze_media_plan(library=library, topic_slug="rabbit", actor="owner", now=NOW)
```

- [ ] **Step 2: FAIL** then **Step 3: implement freeze/unfreeze**

Freeze: actor; current; pointer `draft`; `get_mapping` listed; materialize nodes from current+draft; `form_forbidden` any non-text → `MEDIA_PLAN_FORM_FORBIDDEN`; write **next** revision file `status=frozen` (never overwrite existing frozen); pointer `status=frozen`, `identity=current.identity`, `mapping_revision=mapping.json revision`, `reason=freeze`. `can_freeze` on GET = listed current + draft pointer + mapping listed.

Unfreeze: disk frozen (including stale); copy nodes to next draft revision; pointer draft; identity/mapping_revision null.

Do not rewrite pointer to `stale` on GET.

- [ ] **Step 4: PASS** — **Step 5: Skip commit**

---

## Phase 3: HTTP, ops, kids ledger

### Task 4: HTTP routes and ops HTML

**Files:**
- Modify: `src/cognitive_card_server/http/errors.py` — add to `_CONFLICT_CODES`: `LAYOUT_NO_CURRENT`, `MEDIA_PLAN_NOT_DRAFT`, `MEDIA_PLAN_NOT_FROZEN`, `MEDIA_PLAN_MAPPING_REQUIRED`, `MEDIA_PLAN_STALE`
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Create: `tests/test_http_knowledge_layout.py`
- Modify: `tests/test_http_knowledge_ops.py` — `test_html_shell_has_no_claims_without_token` still passes; detail HTML may contain `/card-os/ops/layout/rabbit` path **without claims**

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_layout tests.test_http_knowledge_ops tests.test_http_knowledge_compile tests.test_http_auth -v
```

Then the combined focused gate listed in Global Constraints.

**Depends on:** Task 3.

**Interfaces:**
- Consumes: pipeline functions, `_compile_root`, `knowledge_library`, `clock`, `require_admin`
- Produces: routes and `render_layout_html(topic)`

| Method | Path |
| --- | --- |
| GET | `/admin/knowledge-library/{topic}/layout` |
| PATCH | `/admin/knowledge-library/{topic}/media-plan` |
| POST | `/admin/knowledge-library/{topic}/media-plan-freeze` |
| POST | `/admin/knowledge-library/{topic}/media-plan-unfreeze` |
| GET/HEAD | `/card-os/ops/layout/{topic}` |

Register `/card-os/ops/layout/{topic}` **before** `/{topic}` if the generic topic route would swallow `layout`. Check `attach_ops_routes` order: compile is already before `/{topic}`; add layout next to compile.

- [ ] **Step 1: HTTP tests** in `tests/test_http_knowledge_layout.py`

Copy the TestClient / admin token fixture pattern from `tests/test_http_knowledge_ops.py` (`_auth`, temp candidate_root, publish rabbit). Cover:

1. GET layout without token → not 200 empty success (401).
2. GET `/card-os/ops/layout/rabbit` without token: 200 HTML, no `canonical_claim`, no Merck, no proposition ids from rabbit-real.
3. Admin GET layout after publish: 200, creates draft, `mapping_listed` false.
4. PATCH then freeze without mapping → 409 `MEDIA_PLAN_MAPPING_REQUIRED`.
5. mapping-lock then freeze → 201 or 200 frozen (use 200 for freeze/unfreeze, 200 for GET; PATCH 200). Spec does not require 201 for freeze — **use 200**.
6. Compile intent HTML: add test that `render_compile_intent_html("ci_" + "ab"*16)` source contains neither prompt text nor claims; after implementing JS, the **static** shell still has no claims. Assert `Open layout` string is **not** in the no-token shell unless it is a JS string that only runs after fetch — prefer creating the anchor in JS when `payload.state === "current"` so the HTML file has no topic claims. A literal `Open layout` in JS is allowed; do not embed a topic slug with claims.

Detail page: in `render_detail_html`, add a claim-free link:

```python
f'<p><a href="/card-os/ops/layout/{html.escape(slug, quote=True)}">Open layout</a></p>'
```

only when `slug` is non-empty. Do **not** edit the mapping-lock `fetch(.../mapping-lock` block.

Layout page: token shell like compile intent; JS loads GET layout, renders groups as nested lists, `<select>` per proposition for draft, Freeze/Unfreeze buttons, link 补知识点 `/card-os/ops/compile`. Selects disabled when not draft. Do not put any fixture claim in the Python HTML template.

Compile intent `renderIntent`: if `payload.state === "current"`, append `<a href="/card-os/ops/layout/"+encodeURIComponent(payload.topic_slug)+">Open layout</a>`.

- [ ] **Step 2: FAIL** (routes missing)

- [ ] **Step 3: Wire HTTP + pages**

GET no current returns `{"listed": false, "topic_slug": slug}` 200 (like mapping). Writes raise `LAYOUT_NO_CURRENT`.

- [ ] **Step 4: HTTP tests PASS + combined focused gate** (2 known mapping FAIL only)

- [ ] **Step 5: Skip commit**

---

### Task 5: Kids ledger (no DONE)

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`
- Modify: `docs/cognitive-card-os-roadmap.md` — GRAPH-01 / FORM-01 / FREEZE-01 `IN PROGRESS`; do not mark `DONE`; FLOW-01 still program not complete
- Modify: `docs/README.md` — plan status In Progress
- Modify: `docs/cognitive-card-os-system-design.md` §11 pointer for this slice

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack && bash scripts/ai/check-task-state.sh && bash scripts/ai/check-handoff.sh && bash scripts/ai/check-doc-governance.sh && git diff --check
```

Expected: task-state PASS; handoff PASS; doc-governance WARN only on Last Reviewed 2026-07-24; diff --check PASS.

**Depends on:** Task 4.

- [ ] **Step 1: Roadmap** — three rows IN PROGRESS, spec+plan paths, server SHA after Tasks 1–4 exist; 非范围 still IMG-03 / production / merge.
- [ ] **Step 2: System design** one bullet: layout outline + media-plan freeze; not IMG-03; not DONE.
- [ ] **Step 3: CURRENT_TASK / HANDOFF** from real `git status` and the combined gate output. Isolation map: kids docs + server worktree. Exact Next Action: do not merge/push/release; do not mark DONE.
- [ ] **Step 4: Run verification commands** and paste real PASS/WARN/FAIL into HANDOFF.
- [ ] **Step 5: Skip commit** unless asked.

---

## Self-review

1. **Spec coverage:** §7 outline Task 1; §8 draft GET Task 2; §9 PATCH Task 2; §10–11 freeze/unfreeze/stale Task 3; §12–13 HTTP/ops Task 4; §14 errors Tasks 3–4; §15 confirm writes no media-plan Task 2; cat compile unchanged Task 4 gate; kids ledger Task 5; no IMG-03.
2. **Placeholders:** none.
3. **Types:** `get_layout` / `patch_media_plan` / `freeze_media_plan` / `unfreeze_media_plan` names stable across tasks.
4. **Verify commands:** each task has a runnable unittest or bash line.
5. **Depends on:** Task 1 → 2 → 3 → 4 → 5.

Do not implement this plan until the operator picks Subagent-Driven or Inline Execution.
