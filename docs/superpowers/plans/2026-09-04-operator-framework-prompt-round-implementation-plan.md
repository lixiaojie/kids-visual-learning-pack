# Operator Framework Prompt Round Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On the existing compile-intent, let the operator pick `dinosaur-entity`, copy a framework ChatGPT prompt, paste a skeleton JSON, and land in `state=framework` without setting knowledge current.

**Architecture:** Add a closed `object_type` map. Missing type keeps `knowledge-compile-v1` and the one-shot authoring path. `dinosaur-entity` snapshots `knowledge-compile-framework-dinosaur-entity-v1`, parses `cognitive-card-knowledge-framework-v1` into `framework.json`, and refuses `confirm-current`.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, existing `compile-intent` store, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium (5 tasks)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-04-operator-framework-prompt-round-design.md` (Approved). Program: `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md`.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1`.
- Run tests with `PYTHONPATH=src .venv/bin/python`.
- Do not implement R2, media-plan, image_suggestions, OpenAI API, or other object-type templates.
- Do not change four-object schema. Do not call `compile_authoring_request` on the framework path. Do not write `candidate/` four objects for `round=framework`.
- Omit/empty `object_type` must keep the current `cat` create → reply → confirm path.
- Do not write production knowledge-library. Do not merge/push/release. Do not add `uv.lock` or kids `outputs/`.
- Do not git commit unless the operator asks.
- Do not mark API-01 / FLOW-01 / RENDER-02 `DONE`.
- Known combined-gate 2 FAIL on ops mapping-lock `LEGEND_ROLE_MISSING` stay untouched.

### Combined focused gate (after Task 4)

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_http_auth
```

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_compile/types.py` | Closed `OBJECT_TYPES`, dinosaur classification, required legend roles |
| `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-framework-dinosaur-entity-v1.txt` | Copyable R1 prompt |
| `src/cognitive_card_server/knowledge_compile/prompt.py` | `expand_prompt(..., object_type="")` dispatches templates |
| `src/cognitive_card_server/knowledge_compile/parse.py` | `parse_framework_reply` |
| `src/cognitive_card_server/knowledge_compile/store.py` | `framework.json` read/write/delete |
| `src/cognitive_card_server/knowledge_compile/pipeline.py` | `round`, framework reply, confirm refusal |
| `src/cognitive_card_server/knowledge_compile/__init__.py` | Export new helpers if tests import them |
| `src/cognitive_card_server/knowledge_ops/http.py` | Pass `object_type`; GET attaches `framework` |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Type select; framework preview; Confirm stays off |
| `src/cognitive_card_server/http/errors.py` | `COMPILE_OBJECT_TYPE_UNKNOWN`, `COMPILE_FRAMEWORK_NOT_CURRENT` |
| `tests/test_knowledge_compile.py` | Framework expand/parse/pipeline |
| `tests/test_http_knowledge_compile.py` | Create type, confirm 409, HTML shell |

Kids (Task 5): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`.

---

## Phase 1: Template and skeleton parser

### Task 1: Object type map and dinosaur framework prompt

**Files:**
- Create: `src/cognitive_card_server/knowledge_compile/types.py`
- Create: `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-framework-dinosaur-entity-v1.txt`
- Modify: `src/cognitive_card_server/knowledge_compile/prompt.py`
- Test: `tests/test_knowledge_compile.py` (`PromptExpandTests`)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile.PromptExpandTests -v` → all pass

**Depends on:** None

**Interfaces:**
- Consumes: existing `expand_prompt(subject, goal, topic_slug)`
- Produces:

```python
FRAMEWORK_DINOSAUR_TEMPLATE_ID = "knowledge-compile-framework-dinosaur-entity-v1"
DINOSAUR_ENTITY = "dinosaur-entity"
DINOSAUR_CLASSIFICATION = {
    "primary_domain": "paleontology",
    "secondary_domains": [],
    "primary_form": "entity",
    "secondary_forms": [],
    "object_subtype": "fossil-animal",
}
DINOSAUR_LEGEND_ROLES = (
    "observe",
    "compare",
    "evidence",
    "time",
    "place",
    "learning_place",
    "habit",
    "kind",
    "uncertain",
)

def normalize_object_type(value: object) -> str:
    """'' or missing → ''. dinosaur-entity → that key. else COMPILE_OBJECT_TYPE_UNKNOWN."""

def expand_prompt(*, subject: str, goal: str, topic_slug: str, object_type: str = "") -> str:
    """object_type '' uses knowledge-compile-v1. dinosaur-entity uses the framework template."""
```

- [ ] **Step 1: Write failing tests** in `PromptExpandTests`:

```python
    def test_default_expand_unchanged(self) -> None:
        from cognitive_card_server.knowledge_compile.prompt import TEMPLATE_ID, expand_prompt

        text = expand_prompt(subject="家猫", goal="认识猫", topic_slug="cat")
        self.assertIn("家猫", text)
        self.assertIn("cognitive-card-authoring-request-v1", text)
        self.assertNotIn("{{subject}}", text)

    def test_dinosaur_framework_prompt(self) -> None:
        from cognitive_card_server.knowledge_compile.prompt import expand_prompt
        from cognitive_card_server.knowledge_compile.types import FRAMEWORK_DINOSAUR_TEMPLATE_ID

        text = expand_prompt(
            subject="剑龙",
            goal="认识骨板",
            topic_slug="stegosaurus",
            object_type="dinosaur-entity",
        )
        self.assertIn("剑龙", text)
        self.assertIn("stegosaurus", text)
        self.assertIn("cognitive-card-knowledge-framework-v1", text)
        self.assertIn("learning_place", text)
        self.assertIn("do not invent", text.lower())
        self.assertIn("adult", text.lower())
        self.assertNotIn("{{subject}}", text)
        self.assertNotIn("cognitive-card-authoring-request-v1", text)

    def test_unknown_object_type(self) -> None:
        from cognitive_card_server.knowledge_compile.prompt import expand_prompt
        from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

        with self.assertRaises(KnowledgeContractError) as ctx:
            expand_prompt(
                subject="剑龙",
                goal="认识骨板",
                topic_slug="stegosaurus",
                object_type="mammal-entity",
            )
        self.assertEqual(ctx.exception.code, "COMPILE_OBJECT_TYPE_UNKNOWN")
```

Keep the existing `test_expanded_prompt_contains_brief_and_rules` and `test_subject_too_long`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile.PromptExpandTests.test_dinosaur_framework_prompt tests.test_knowledge_compile.PromptExpandTests.test_unknown_object_type -v`

Expected: FAIL (`object_type` unexpected / types missing).

- [ ] **Step 3: Implement types, template, dispatch**

`types.py`:

```python
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

FRAMEWORK_DINOSAUR_TEMPLATE_ID = "knowledge-compile-framework-dinosaur-entity-v1"
DINOSAUR_ENTITY = "dinosaur-entity"
FRAMEWORK_SCHEMA = "cognitive-card-knowledge-framework-v1"

DINOSAUR_CLASSIFICATION = {
    "primary_domain": "paleontology",
    "secondary_domains": [],
    "primary_form": "entity",
    "secondary_forms": [],
    "object_subtype": "fossil-animal",
}
DINOSAUR_LEGEND_ROLES = (
    "observe",
    "compare",
    "evidence",
    "time",
    "place",
    "learning_place",
    "habit",
    "kind",
    "uncertain",
)
OBJECT_TYPES = frozenset({DINOSAUR_ENTITY})


def normalize_object_type(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise KnowledgeContractError("COMPILE_OBJECT_TYPE_UNKNOWN", "object_type")
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned not in OBJECT_TYPES:
        raise KnowledgeContractError("COMPILE_OBJECT_TYPE_UNKNOWN", "object_type", cleaned)
    return cleaned
```

Template file `knowledge-compile-framework-dinosaur-entity-v1.txt` (exact body):

```text
You are drafting a coverage skeleton for a children's dinosaur learning topic. This is ROUND 1. Do not write a full Knowledge Core.

Topic slug (must appear in topic.slug): {{topic_slug}}
Learning object: {{subject}}
Learning goal: {{goal}}

Output ONE JSON object only, schema "cognitive-card-knowledge-framework-v1".
You may wrap it in a single ```json fence. Do not output a second JSON object.
Do not output schema "cognitive-card-authoring-request-v1". Do not emit propositions, claims, four-card slots, COPY, font size, or image_suggestions.

Required top-level keys: schema, topic, object_type, classification, proposed_units, legend_slots, gaps.

Field contract:
- topic: slug, title
- object_type: dinosaur-entity
- classification: primary_domain=paleontology, secondary_domains=[], primary_form=entity, secondary_forms=[], object_subtype=fossil-animal
- proposed_units[]: slug, title, optional coverage_facet. No propositions. Empty list allowed.
- legend_slots[]: exactly these legend_role values, each once: observe, compare, evidence, time, place, learning_place, habit, kind, uncertain.
  Each slot: legend_role, status (has_instance|empty), optional note.
- gaps: unknown, safety, sources — arrays of short strings. Empty arrays allowed.

Rules:
- Ask whether each module has a real instance. If not, status=empty. Do not fill empty modules by inventing facts.
- Do not invent a required adult Linnaean stage, body length, body mass, three-view, or fossil GPS.
- learning_place is empty unless the reply has a real child learning-place instance.
- Uncertain facts go in gaps.unknown or an uncertain slot with status=has_instance and a note that it is not a claim.
- Do not invent locators.

Return only the framework JSON.
```

`prompt.py`: add `object_type: str = ""` to `expand_prompt`. After slug checks:

```python
    from cognitive_card_server.knowledge_compile.types import (
        FRAMEWORK_DINOSAUR_TEMPLATE_ID,
        DINOSAUR_ENTITY,
        normalize_object_type,
    )

    cleaned_type = normalize_object_type(object_type)
    if cleaned_type == DINOSAUR_ENTITY:
        path = Path(__file__).resolve().parent / "templates" / f"{FRAMEWORK_DINOSAUR_TEMPLATE_ID}.txt"
    else:
        path = template_path()
    template = path.read_text(encoding="utf-8")
    return (
        template.replace("{{subject}}", subject.strip())
        .replace("{{goal}}", goal.strip())
        .replace("{{topic_slug}}", topic_slug)
    )
```

Add `def template_sha256_for(template_id: str) -> str` that reads `templates/{id}.txt`. Keep `template_sha256()` as the complete-path default.

- [ ] **Step 4: Re-run PromptExpandTests** → all pass.

---

### Task 2: Parse framework reply and store `framework.json`

**Files:**
- Modify: `src/cognitive_card_server/knowledge_compile/parse.py`
- Modify: `src/cognitive_card_server/knowledge_compile/store.py`
- Modify: `src/cognitive_card_server/knowledge_compile/__init__.py`
- Test: `tests/test_knowledge_compile.py` (new `ParseFrameworkReplyTests`)

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile.ParseFrameworkReplyTests tests.test_knowledge_compile.ParseAuthoringReplyTests -v` → all pass

**Depends on:** Task 1

**Interfaces:**
- Consumes: `_load_json_object`
- Produces:

```python
def parse_framework_reply(reply: str, *, topic_slug: str, object_type: str) -> dict[str, object]: ...
def framework_path(compile_root: Path, intent_id: str) -> Path: ...
def write_framework(compile_root: Path, intent_id: str, payload: dict[str, object]) -> None: ...
def read_framework(compile_root: Path, intent_id: str) -> dict[str, object] | None: ...
def delete_framework(compile_root: Path, intent_id: str) -> None: ...
```

- [ ] **Step 1: Write failing tests**

```python
class ParseFrameworkReplyTests(unittest.TestCase):
    def test_parse_valid_skeleton(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_framework_reply

        payload = parse_framework_reply(_stego_framework_reply(), topic_slug="stegosaurus", object_type="dinosaur-entity")
        self.assertEqual(payload["schema"], "cognitive-card-knowledge-framework-v1")
        self.assertEqual(len(payload["legend_slots"]), 9)

    def test_parse_rejects_authoring_schema(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_framework_reply
        from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

        with self.assertRaises(KnowledgeContractError) as ctx:
            parse_framework_reply(_cat_reply(), topic_slug="stegosaurus", object_type="dinosaur-entity")
        self.assertEqual(ctx.exception.code, "COMPILE_REPLY_INVALID")

    def test_parse_rejects_claim_units(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_framework_reply
        from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

        raw = _stego_framework_reply().replace(
            '"proposed_units": []',
            '"proposed_units": [{"slug":"x","title":"x","propositions":[{"claim":"no"}]}]',
        )
        with self.assertRaises(KnowledgeContractError) as ctx:
            parse_framework_reply(raw, topic_slug="stegosaurus", object_type="dinosaur-entity")
        self.assertEqual(ctx.exception.code, "COMPILE_REPLY_INVALID")

    def test_parse_rejects_missing_slot(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_framework_reply
        from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

        raw = _stego_framework_reply().replace(
            '{"legend_role": "uncertain", "status": "has_instance", "note": ""}',
            '{"legend_role": "observe", "status": "empty", "note": ""}',
        )
        with self.assertRaises(KnowledgeContractError) as ctx:
            parse_framework_reply(raw, topic_slug="stegosaurus", object_type="dinosaur-entity")
        self.assertEqual(ctx.exception.code, "COMPILE_REPLY_INVALID")
```

Add helper `_stego_framework_reply()` at the bottom of the test module: a fenced JSON matching spec §8 with `proposed_units: []` and all nine slots (time and learning_place `empty`).

- [ ] **Step 2: Run ParseFrameworkReplyTests** → FAIL (`parse_framework_reply` missing).

- [ ] **Step 3: Implement parser and store**

`parse_framework_reply`: `_load_json_object`, then require `schema == FRAMEWORK_SCHEMA`, `object_type` match, `topic.slug` match, classification deep-equal to `DINOSAUR_CLASSIFICATION`, `proposed_units` list of dicts with `slug`+`title` strings and **no** `propositions`/`claim`, `legend_slots` list whose `legend_role` set equals `DINOSAUR_LEGEND_ROLES` (len 9, no dupes), each `status` in `{has_instance, empty}`, `gaps` dict of three lists of strings. Drop unknown top-level keys. Any miss → `COMPILE_REPLY_INVALID`.

`store.py`: `framework.json` beside `intent.json`. `write_framework` uses canonical_json + replace. `read_framework` returns None if missing. `delete_framework` unlinks. `delete_candidate` stays as-is; `return`/`cancel` in Task 3 will also `delete_framework`.

- [ ] **Step 4: Re-run parse tests** → all pass.

---

## Phase 2: Pipeline and HTTP

### Task 3: Intent round, framework reply, confirm refusal

**Files:**
- Modify: `src/cognitive_card_server/knowledge_compile/pipeline.py`
- Test: `tests/test_knowledge_compile.py` (`IntentPipelineTests`)

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile.IntentPipelineTests -v` → all pass

**Depends on:** Task 2

**Interfaces:**
- Consumes: `expand_prompt(..., object_type=)`, `parse_framework_reply`, `write_framework`
- Produces: `create_intent(..., object_type: str = "")`; `submit_reply` branches on `round`; `confirm_current` raises `COMPILE_FRAMEWORK_NOT_CURRENT`

- [ ] **Step 1: Write failing pipeline tests**

```python
    def test_framework_reply_does_not_set_current(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            confirm_current,
            create_intent,
            submit_reply,
        )
        from cognitive_card_server.knowledge_compile.store import candidate_dir, framework_path
        from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

        created = create_intent(
            library=self.library,
            compile_root=self.compile_root,
            topic_slug="stegosaurus",
            subject="剑龙",
            goal="认识骨板",
            actor="owner",
            now=NOW,
            object_type="dinosaur-entity",
        )
        self.assertEqual(created["state"], "open")
        self.assertEqual(created["round"], "framework")
        self.assertEqual(created["prompt_template_id"], "knowledge-compile-framework-dinosaur-entity-v1")
        replied = submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_framework_reply(),
            actor="owner",
            now=NOW,
        )
        self.assertEqual(replied["state"], "framework")
        self.assertTrue(framework_path(self.compile_root, created["intent_id"]).is_file())
        self.assertFalse(candidate_dir(self.compile_root, created["intent_id"]).exists())
        self.assertIsNone(self.library.get_current("stegosaurus", now=NOW))
        with self.assertRaises(KnowledgeContractError) as ctx:
            confirm_current(
                library=self.library,
                compile_root=self.compile_root,
                intent_id=created["intent_id"],
                actor="owner",
                now=NOW,
            )
        self.assertEqual(ctx.exception.code, "COMPILE_FRAMEWORK_NOT_CURRENT")
        self.assertIsNone(self.library.get_current("stegosaurus", now=NOW))
```

Also: `test_framework_blocks_second_intent` (active `framework` → `COMPILE_INTENT_ACTIVE`); `test_return_from_framework_reopens` (return deletes framework.json, state `open`).

Existing `test_create_expand_and_slug_gates` / `test_reply_compiled_then_confirm` must still pass without `object_type`.

- [ ] **Step 2: Run the new tests** → FAIL.

- [ ] **Step 3: Implement pipeline**

`create_intent`: add `object_type: str = ""`. `cleaned_type = normalize_object_type(object_type)`. Expand with that type. Idempotency `same_body` also compares `object_type` (treat missing as `""`). Intent fields: `"object_type": cleaned_type`, `"round": "framework" if cleaned_type else "complete"`, `prompt_template_id` / sha from the chosen template. `_NON_TERMINAL` adds `"framework"`.

`submit_reply`: if `intent.get("round") == "framework"`: require `_REPLYABLE`; `parse_framework_reply`; `delete_candidate`; `delete_framework`; `write_framework`; `state="framework"`. Do not compile authoring. Else existing path.

`confirm_current`: if `intent.get("round") == "framework"` and `intent.get("state") != "compiled"`: raise `COMPILE_FRAMEWORK_NOT_CURRENT`. (R1 never reaches compiled.)

`return_intent`: allow `state in {"compiled", "failed", "framework"}` → `open`; `delete_candidate`; `delete_framework`.

`cancel_intent`: also `delete_framework`.

- [ ] **Step 4: Re-run IntentPipelineTests** → all pass.

---

### Task 4: HTTP, errors, ops HTML

**Files:**
- Modify: `src/cognitive_card_server/http/errors.py`
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Test: `tests/test_http_knowledge_compile.py`

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_http_auth -v` → all pass (do not fix `LEGEND_ROLE_MISSING` in mapping-lock tests)

**Depends on:** Task 3

**Interfaces:**
- Create JSON body may include `object_type`
- GET `state=framework` includes `framework` from disk
- Confirm on framework intent → 409 `COMPILE_FRAMEWORK_NOT_CURRENT`

- [ ] **Step 1: Write HTTP tests**

```python
    def test_dinosaur_framework_confirm_is_conflict(self) -> None:
        headers = self._admin_headers()
        created = self.client.post(
            COMPILE_URL,
            headers=headers,
            json={
                "topic_slug": "stegosaurus",
                "subject": "剑龙",
                "goal": "认识骨板",
                "actor": "owner",
                "object_type": "dinosaur-entity",
            },
        )
        self.assertEqual(created.status_code, 200)
        intent_id = created.json()["intent_id"]
        replied = self.client.post(
            f"{COMPILE_URL}/{intent_id}/reply",
            headers=headers,
            json={"reply": _stego_framework_reply(), "actor": "owner"},
        )
        self.assertEqual(replied.status_code, 200)
        self.assertEqual(replied.json()["state"], "framework")
        self.assertIn("legend_slots", replied.json().get("framework") or self.client.get(f"{COMPILE_URL}/{intent_id}", headers=headers).json()["framework"])
        confirm = self.client.post(
            f"{COMPILE_URL}/{intent_id}/confirm-current",
            headers=headers,
            json={"actor": "owner"},
        )
        self.assertEqual(confirm.status_code, 409)
        self.assertEqual(confirm.json()["error"]["code"], "COMPILE_FRAMEWORK_NOT_CURRENT")

    def test_unknown_object_type_is_bad_request(self) -> None:
        created = self.client.post(
            COMPILE_URL,
            headers=self._admin_headers(),
            json={
                "topic_slug": "stegosaurus",
                "subject": "剑龙",
                "goal": "认识骨板",
                "actor": "owner",
                "object_type": "plant-entity",
            },
        )
        self.assertEqual(created.status_code, 400)
        self.assertEqual(created.json()["error"]["code"], "COMPILE_OBJECT_TYPE_UNKNOWN")

    def test_compile_form_lists_dinosaur_type(self) -> None:
        html = self.client.get("/card-os/ops/compile").text
        self.assertIn("object-type", html)
        self.assertIn("dinosaur-entity", html)
        self.assertNotIn("cognitive-card-knowledge-framework-v1", html)
```

If `_admin_headers` is not a helper, copy the existing test's header construction from `test_admin_create_prompt_is_not_in_ops_html`. Import `_stego_framework_reply` from `tests.test_knowledge_compile`. GET after reply must include `framework`. Either have `submit_reply` return public intent with framework attached, or only attach on GET — spec requires GET. Prefer GET attach; reply JSON may omit `framework` but GET must include it. The first test should GET after reply.

`submit_reply` returning intent without `framework` is OK; HTTP GET loads it.

- [ ] **Step 2: Run the new HTTP tests** → FAIL.

- [ ] **Step 3: Wire HTTP and pages**

`errors.py`: add `"COMPILE_FRAMEWORK_NOT_CURRENT"` to `_CONFLICT_CODES`. Leave `COMPILE_OBJECT_TYPE_UNKNOWN` as default 400.

`admin_create_compile_intent`: pass `object_type=payload.get("object_type") if isinstance(payload.get("object_type"), str) else ""`.

`admin_get_compile_intent`: if `state == "framework"`, `read_framework` and set `intent["framework"]` when not None.

`pages.py` `render_compile_html` form: after Goal, add

```html
<p><label>Object type <select id="object-type" name="object_type"><option value="">One-shot complete (existing)</option><option value="dinosaur-entity">Dinosaur entity (framework)</option></select></label></p>
```

`_COMPILE_FORM_SCRIPT` JSON body adds `object_type: document.getElementById("object-type").value || ""`.

`_COMPILE_INTENT_SCRIPT` `renderIntent`: if `payload.state === "framework" && payload.framework`, put that JSON in `previewBox`. Confirm stays `payload.state !== "compiled"` (framework keeps it disabled). After status line, if `payload.round === "framework"`, add a paragraph: `Round 2 complete authoring is not this slice.`

Keep HTML shell free of prompt/skeleton text.

- [ ] **Step 4: Run HTTP tests + combined focused compile/ops/auth gate** → new tests pass; do not touch mapping-lock failures.

- [ ] **Step 5: Optional reply public shape** — if tests want `framework` on POST reply, attach in HTTP reply handler the same way as GET. Prefer attaching in a small `_public_compile_intent(compile_root, intent)` used by GET and reply.

---

## Phase 3: Kids ledger

### Task 5: Kids docs after server tests pass

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `docs/README.md` (plan row already added if present; set In Progress)

**Verify (kids repo):**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack && bash scripts/ai/check-task-state.sh && bash scripts/ai/check-handoff.sh && bash scripts/ai/check-doc-governance.sh && git diff --check
```

**Depends on:** Task 4 if implementing; if this plan is only being landed, skip server edits and record that implementation has not started.

When implementing: roadmap `API-01-R1` stays `IN PROGRESS` until production; do not mark `DONE`. Record server SHA only after a local commit the operator requested.

Do not commit unless asked.

---

## Self-review

1. **Spec coverage:** §5 create/object_type → Task 1+3. §6 template → Task 1. §7 reply/framework.json/no candidate → Task 2+3. §8 schema → Task 2. §9 ops HTML → Task 4. §10 errors → Task 4. §11 cat unchanged → existing tests kept. Confirm refusal → Task 3+4. Unknown type → Task 1+4.
2. **Out of spec:** no R2 prompt, no media-plan, no other types, no production library.
3. **Types:** `dinosaur-entity`, `cognitive-card-knowledge-framework-v1`, `COMPILE_FRAMEWORK_NOT_CURRENT`, `COMPILE_OBJECT_TYPE_UNKNOWN` used consistently.
4. **Placeholders:** none.
