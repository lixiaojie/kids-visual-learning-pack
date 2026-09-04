# Operator Complete Prompt Round Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On a dinosaur-entity compile-intent that already has an accepted skeleton, let the operator start round 2, copy a complete ChatGPT prompt that inlines that skeleton, paste authoring JSON, land four-object candidates, and Confirm current. Optional image_suggestions stay on the intent.

**Architecture:** Same compile-intent. `POST .../advance` snapshots the R1 prompt, expands `knowledge-compile-complete-dinosaur-entity-v1` with canonical `framework.json`, and sets `round=complete`. Reply peels `image_suggestions` before `compile_authoring_request`. `paleontology + entity + fossil-animal` becomes `enabled`. No media-plan file.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, existing compile-intent store, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium (5 tasks)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-04-operator-complete-prompt-round-design.md` (Approved). Program: `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md`.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1` (uncommitted API-01-R1 already present; do not revert it).
- Kids repo: `/Users/admin/projects/family/kids-visual-learning-pack`.
- Run tests with `PYTHONPATH=src .venv/bin/python`.
- Do not write media-plan library metadata. Do not implement GRAPH / FORM / FREEZE. Do not call OpenAI APIs. Do not add other object-type templates.
- Do not change four-object schema. Do not write `image_suggestions` into any four-object file.
- Omit/empty `object_type` must keep the current `cat` create → reply → confirm path. `advance` and `return-framework` on that path fail closed.
- Do not write production knowledge-library. Do not merge/push/release. Do not add `uv.lock` or kids `outputs/`.
- Do not git commit unless the operator asks. Skip every commit step.
- Do not mark API-01 / API-01-R1 / FLOW-01 / RENDER-02 `DONE`.
- Known combined-gate 2 FAIL on ops mapping-lock `LEGEND_ROLE_MISSING` stay untouched.

### Combined focused gate (after Task 4)

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_classification_registry tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_http_auth
```

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/classification/registry.py` | Move fossil-animal cell to `ENABLED_CELLS` |
| `src/cognitive_card_server/knowledge_compile/types.py` | `COMPLETE_DINOSAUR_TEMPLATE_ID` |
| `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-complete-dinosaur-entity-v1.txt` | Copyable R2 prompt |
| `src/cognitive_card_server/knowledge_compile/prompt.py` | `expand_complete_prompt` |
| `src/cognitive_card_server/knowledge_compile/parse.py` | `parse_complete_reply` strips and validates suggestions |
| `src/cognitive_card_server/knowledge_compile/store.py` | `image_suggestions.json` read/write/delete |
| `src/cognitive_card_server/knowledge_compile/pipeline.py` | `advance_intent`, `return_framework`, complete reply, return keeps skeleton |
| `src/cognitive_card_server/knowledge_ops/http.py` | advance / return-framework routes; GET attaches framework + suggestions |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Start round 2; Return to framework; drop R1 “not this slice” copy |
| `src/cognitive_card_server/http/errors.py` | new 409 codes |
| `tests/test_classification_registry.py` | fossil-animal enabled; evidence-record+dinosaur still review |
| `tests/test_knowledge_compile.py` | expand / parse / pipeline |
| `tests/test_http_knowledge_compile.py` | HTTP + HTML shell |

Kids (Task 5): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`, `docs/cognitive-card-os-system-design.md`.

---

## Phase 1: Classification and complete prompt

### Task 1: Enable fossil-animal and expand the complete dinosaur prompt

**Files:**
- Modify: `src/cognitive_card_server/classification/registry.py`
- Modify: `src/cognitive_card_server/knowledge_compile/types.py`
- Create: `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-complete-dinosaur-entity-v1.txt`
- Modify: `src/cognitive_card_server/knowledge_compile/prompt.py`
- Test: `tests/test_classification_registry.py`
- Test: `tests/test_knowledge_compile.py` (`PromptExpandTests`)

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_classification_registry tests.test_knowledge_compile.PromptExpandTests -v
```

Expected: all pass.

**Depends on:** API-01-R1 uncommitted framework template path.

**Interfaces:**
- Consumes: existing `expand_prompt(..., object_type="")`, `canonical_json`, `FRAMEWORK_DINOSAUR_TEMPLATE_ID`
- Produces:

```python
COMPLETE_DINOSAUR_TEMPLATE_ID = "knowledge-compile-complete-dinosaur-entity-v1"

def expand_complete_prompt(
    *,
    subject: str,
    goal: str,
    topic_slug: str,
    framework: dict[str, object],
) -> str:
    """Fill knowledge-compile-complete-dinosaur-entity-v1. framework_json is canonical UTF-8 JSON."""
```

- [ ] **Step 1: Write failing tests**

In `CoverageMatrixTests.test_enabled_and_review_overlays`, change the fossil-animal assertion to `"enabled"`.

Replace `test_fossil_animal_stays_review` with:

```python
    def test_fossil_animal_is_enabled(self) -> None:
        self.assertEqual(
            "enabled", coverage_status("paleontology", "entity", "fossil-animal")
        )
        result = validate_classification(
            _classification("paleontology", "entity", "fossil-animal")
        )
        self.assertEqual("fossil-animal", result["object_subtype"])
```

Change `test_review_cell_stops_guessing` to use the cell that stays review:

```python
    def test_review_cell_stops_guessing(self) -> None:
        with self.assertRaises(KnowledgeContractError) as raised:
            validate_classification(
                _classification("paleontology", "evidence-record", "dinosaur")
            )
        self.assertEqual("CLASSIFICATION_REVIEW", raised.exception.code)
```

In `PromptExpandTests` add:

```python
    def test_dinosaur_complete_prompt_inlines_framework(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_framework_reply
        from cognitive_card_server.knowledge_compile.prompt import expand_complete_prompt

        framework = parse_framework_reply(
            _stego_framework_reply(),
            topic_slug="stegosaurus",
            object_type="dinosaur-entity",
        )
        text = expand_complete_prompt(
            subject="剑龙",
            goal="认识骨板",
            topic_slug="stegosaurus",
            framework=framework,
        )
        self.assertIn("剑龙", text)
        self.assertIn("stegosaurus", text)
        self.assertIn("cognitive-card-authoring-request-v1", text)
        self.assertIn("cognitive-card-knowledge-framework-v1", text)
        self.assertIn("image_suggestions", text)
        self.assertIn("fossil-animal", text)
        self.assertIn("do not invent", text.lower())
        self.assertNotIn("{{subject}}", text)
        self.assertNotIn("{{framework_json}}", text)
        self.assertIn('"object_type":"dinosaur-entity"', text)
```

Keep the existing framework expand tests. `expand_prompt(..., object_type="dinosaur-entity")` must still use the **framework** template, not the complete one.

- [ ] **Step 2: Run tests** → FAIL (`expand_complete_prompt` missing; fossil-animal still `review`).

- [ ] **Step 3: Implement**

`registry.py`: move `("paleontology", "entity", "fossil-animal")` from `REVIEW_CELLS` to `ENABLED_CELLS`. Leave `("paleontology", "evidence-record", "dinosaur")` in `REVIEW_CELLS`. Keep `assert not (ENABLED_CELLS & REVIEW_CELLS)`.

`types.py` add:

```python
COMPLETE_DINOSAUR_TEMPLATE_ID = "knowledge-compile-complete-dinosaur-entity-v1"
```

Create the template file with this exact body (placeholders `{{subject}}` `{{goal}}` `{{topic_slug}}` `{{framework_json}}`):

```text
You are compiling a Knowledge Core authoring request for a children's dinosaur topic. This is ROUND 2. Obey the ROUND 1 skeleton JSON embedded below. Do not invent coverage for empty legend slots.

Topic slug (must appear in topic.slug): {{topic_slug}}
Learning object: {{subject}}
Learning goal: {{goal}}

ROUND 1 skeleton (canonical JSON, schema cognitive-card-knowledge-framework-v1):
{{framework_json}}

Output ONE JSON object only, schema "cognitive-card-authoring-request-v1".
You may wrap it in a single ```json fence. Do not output a second JSON object.
Do not invent a parallel schema.

classification MUST match the skeleton exactly: primary_domain=paleontology, secondary_domains=[], primary_form=entity, secondary_forms=[], object_subtype=fossil-animal. Do not change object_subtype to dinosaur. Do not use evidence-record.

Required top-level keys (same shape as examples/authoring/rabbit-real.json):
schema, authored_at, topic, classification, usage, identity, excluded_questions, sources, "units", "learning", projection.

Optional top-level image_suggestions: array of {proposition_id, form, note}.
proposition_id MUST be a proposition slug already present in this same JSON. form if present MUST be wordless-image (default wordless-image). Do not put suggestions into canonical_claim. Do not suggest safety, unknown_boundary, or source/clearing propositions.

Field contract:
- topic: slug, title, revision (1), topic.scope_type (single|composite|progressive)
- units[]: slug, title, coverage_facet, question, propositions[]
- each proposition: slug, claim, claim_language, certainty, evidence_locator, evidence_summary, unknowns, confusion_boundary, safety_scope, source_slug
- sources[]: intake.method=search, intake.query, intake.tool, intake.captured_at, locator. Do not invent locators.
- projection: {}

Rules:
- legend_slots with status=has_instance MUST have sourced propositions (or an explicit unresolved gap tied to that face).
- legend_slots with status=empty MUST stay unresolved. Do not fill them by inventing facts.
- Do not invent a required adult Linnaean stage, body length, body mass, three-view, or fossil GPS.
- Do not write established claims for body color, soft tissue, sound, or speed.
- Claims are age-neutral. Do not write four-card slots, COPY, font size, or page layout.
- Set "projection": {}.
- excluded_questions must contain at least one item.

Return only the authoring JSON.
```

`prompt.py` add `expand_complete_prompt`. Reuse the same subject/goal/slug checks as `expand_prompt`. `framework` must be a `dict`. Fill `{{framework_json}}` with `canonical_json(framework).decode("utf-8")` (import `canonical_json` from `knowledge_contract.model`). Do not route `expand_prompt(object_type="dinosaur-entity")` to this template.

- [ ] **Step 4: Re-run Step 1 verify command** → all pass. Skip commit.

---

## Phase 2: Suggestions parser and pipeline

### Task 2: Peel and validate image_suggestions; store sidecar

**Files:**
- Modify: `src/cognitive_card_server/knowledge_compile/parse.py`
- Modify: `src/cognitive_card_server/knowledge_compile/store.py`
- Test: `tests/test_knowledge_compile.py` (`ParseCompleteReplyTests` new class)

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile.ParseCompleteReplyTests tests.test_knowledge_compile.ParseAuthoringReplyTests tests.test_knowledge_compile.ParseFrameworkReplyTests -v
```

Expected: all pass.

**Depends on:** Task 1 (classification enabled so later compile works; this task does not compile).

**Interfaces:**
- Consumes: `_load_json_object`, `normalize_authoring_request`
- Produces:

```python
def parse_complete_reply(reply: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Return (authoring request, canonical image_suggestions). Extra suggestion keys dropped."""

def suggestions_path(compile_root: Path, intent_id: str) -> Path: ...
def write_suggestions(compile_root: Path, intent_id: str, items: list[dict[str, object]]) -> None: ...
def read_suggestions(compile_root: Path, intent_id: str) -> list[dict[str, object]] | None: ...
def delete_suggestions(compile_root: Path, intent_id: str) -> None: ...
```

Canonical suggestion item keys after validate: `proposition_id` (str), `form` (`wordless-image`), optional `note` (str).

- [ ] **Step 1: Add helper `_stego_authoring_reply` in `tests/test_knowledge_compile.py`** (used by Task 2 and Task 3):

```python
def _stego_authoring_reply(*, suggestions: list[dict[str, object]] | None = None) -> str:
    request = json.loads(
        (REPO_ROOT / "examples" / "authoring" / "tyrannosaurus-rex.json").read_text(
            encoding="utf-8"
        )
    )
    request["topic"]["slug"] = "stegosaurus"
    request["topic"]["title"] = "剑龙：骨板与化石"
    request["classification"]["object_subtype"] = "fossil-animal"
    request["identity"]["names"] = {
        "cn": "剑龙",
        "en": "Stegosaurus",
        "scientific": "Stegosaurus",
    }
    request["projection"] = {}
    for source in request["sources"]:
        source["intake"] = {
            "method": "search",
            "query": "stegosaurus fossil plates museum",
            "tool": "chatgpt-web-search",
            "captured_at": source["intake"]["captured_at"],
        }
    if suggestions is not None:
        request["image_suggestions"] = suggestions
    return json.dumps(request, ensure_ascii=False)
```

Write tests:

```python
class ParseCompleteReplyTests(unittest.TestCase):
    def test_strips_suggestions_and_keeps_authoring(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_complete_reply

        request, items = parse_complete_reply(
            _stego_authoring_reply(
                suggestions=[
                    {
                        "proposition_id": "large-theropod",
                        "form": "wordless-image",
                        "note": "plates, no glyphs",
                        "extra": "drop-me",
                    }
                ]
            )
        )
        self.assertEqual(request["topic"]["slug"], "stegosaurus")
        self.assertNotIn("image_suggestions", request)
        self.assertEqual(items[0]["proposition_id"], "large-theropod")
        self.assertEqual(items[0]["form"], "wordless-image")
        self.assertEqual(items[0]["note"], "plates, no glyphs")
        self.assertNotIn("extra", items[0])

    def test_missing_suggestions_is_empty_list(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_complete_reply

        request, items = parse_complete_reply(_stego_authoring_reply())
        self.assertEqual(items, [])
        self.assertEqual(request["classification"]["object_subtype"], "fossil-animal")

    def test_unknown_proposition_fails(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_complete_reply

        with self.assertRaises(KnowledgeContractError) as ctx:
            parse_complete_reply(
                _stego_authoring_reply(
                    suggestions=[{"proposition_id": "no-such-prop"}]
                )
            )
        self.assertEqual(ctx.exception.code, "COMPILE_IMAGE_SUGGESTION_INVALID")

    def test_safety_facet_fails(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_complete_reply

        with self.assertRaises(KnowledgeContractError) as ctx:
            parse_complete_reply(
                _stego_authoring_reply(
                    suggestions=[{"proposition_id": "museum-viewing-distance"}]
                )
            )
        self.assertEqual(ctx.exception.code, "COMPILE_IMAGE_SUGGESTION_INVALID")

    def test_unknown_boundary_fact_type_fails(self) -> None:
        from cognitive_card_server.knowledge_compile.parse import parse_complete_reply

        with self.assertRaises(KnowledgeContractError) as ctx:
            parse_complete_reply(
                _stego_authoring_reply(
                    suggestions=[{"proposition_id": "body-color-unknown"}]
                )
            )
        self.assertEqual(ctx.exception.code, "COMPILE_IMAGE_SUGGESTION_INVALID")
```

Existing `parse_authoring_reply` tests must still pass. `parse_authoring_reply` may keep dropping unknown keys including `image_suggestions` via `_KEEP_TOP`; do not add `image_suggestions` to `_KEEP_TOP`.

- [ ] **Step 2: Run ParseCompleteReplyTests** → FAIL.

- [ ] **Step 3: Implement parse + store**

`parse_complete_reply`:

1. `loaded = _load_json_object(reply)` (deepcopy before mutate).
2. `raw = loaded.pop("image_suggestions", [])`. Missing → `[]`. If present and not a list → `COMPILE_IMAGE_SUGGESTION_INVALID`.
3. `request = normalize_authoring_request(loaded)`.
4. Build allowed map from `request["units"]`: each proposition `slug` (and `proposition_id` / `id` if strings) → `{coverage_facet, fact_type}`. Facet comes from the unit.
5. For each suggestion dict: `proposition_id` required string; must be in the map; duplicates fail; `form` omit or `wordless-image`; other form fails; `note` omit or string; extra keys dropped.
6. If mapped `coverage_facet == "safety"` or mapped `fact_type` in `{"safety", "unknown_boundary"}` → `COMPILE_IMAGE_SUGGESTION_INVALID`.
7. Return `(request, canonical_items)`.

Store helpers mirror `framework.json` but the document is a JSON **array**. Use `canonical_json(items)` for write. `read_suggestions`: missing file → `None`; invalid → `None`. `delete_suggestions` unlinks like `delete_framework`.

- [ ] **Step 4: Re-run verify** → all pass. Skip commit.

---

### Task 3: Advance, complete reply, return-framework, confirm

**Files:**
- Modify: `src/cognitive_card_server/knowledge_compile/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_compile/__init__.py` (export `advance_intent`, `return_framework` if tests import from package)
- Test: `tests/test_knowledge_compile.py` (`IntentPipelineTests`)

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile.IntentPipelineTests tests.test_knowledge_compile.ParseCompleteReplyTests -v
```

Expected: all pass, including existing cat and framework tests.

**Depends on:** Tasks 1–2.

**Interfaces:**

```python
def advance_intent(
    *,
    compile_root: Path,
    intent_id: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    """framework → open/complete. Idempotent if already round=complete with complete template."""

def return_framework(
    *,
    compile_root: Path,
    intent_id: str,
) -> dict[str, object]:
    """complete → framework. Keeps framework.json. Deletes candidate and suggestions."""
```

- [ ] **Step 1: Write pipeline tests** in `IntentPipelineTests`:

```python
    def test_advance_then_complete_reply_confirm(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            advance_intent,
            confirm_current,
            create_intent,
            submit_reply,
        )
        from cognitive_card_server.knowledge_compile.store import (
            candidate_dir,
            framework_path,
            suggestions_path,
        )

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
        submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_framework_reply(),
            actor="owner",
            now=NOW,
        )
        advanced = advance_intent(
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            actor="owner",
            now=NOW,
        )
        self.assertEqual(advanced["round"], "complete")
        self.assertEqual(advanced["state"], "open")
        self.assertEqual(
            advanced["prompt_template_id"],
            "knowledge-compile-complete-dinosaur-entity-v1",
        )
        self.assertIn("cognitive-card-authoring-request-v1", advanced["expanded_prompt"])
        self.assertTrue(framework_path(self.compile_root, created["intent_id"]).is_file())
        self.assertTrue(advanced.get("framework_expanded_prompt"))
        replied = submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_authoring_reply(
                suggestions=[{"proposition_id": "large-theropod"}]
            ),
            actor="owner",
            now=NOW,
        )
        self.assertEqual(replied["state"], "compiled")
        self.assertTrue(candidate_dir(self.compile_root, created["intent_id"]).is_dir())
        self.assertTrue(suggestions_path(self.compile_root, created["intent_id"]).is_file())
        core = json.loads(
            (
                candidate_dir(self.compile_root, created["intent_id"])
                / "knowledge-core.json"
            ).read_text(encoding="utf-8")
        )
        dumped = json.dumps(core)
        self.assertNotIn("image_suggestions", dumped)
        self.assertNotIn("wordless-image", dumped)
        confirmed = confirm_current(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            actor="owner",
            now=NOW,
        )
        self.assertEqual(confirmed["state"], "current")
        self.assertIsNotNone(self.library.get_current("stegosaurus", now=NOW))
        current_core = (
            Path(self.library.root) / "stegosaurus" / confirmed["revision"] / "knowledge-core.json"
        )
        # If library layout differs, use library.get_current payload instead.
        self.assertIsNotNone(self.library.get_current("stegosaurus", now=NOW))

    def test_bad_suggestion_does_not_write_candidate(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            advance_intent,
            create_intent,
            submit_reply,
        )
        from cognitive_card_server.knowledge_compile.store import candidate_dir

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
        submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_framework_reply(),
            actor="owner",
            now=NOW,
        )
        advance_intent(
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            actor="owner",
            now=NOW,
        )
        replied = submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_authoring_reply(
                suggestions=[{"proposition_id": "no-such-prop"}]
            ),
            actor="owner",
            now=NOW,
        )
        self.assertEqual(replied["state"], "failed")
        self.assertEqual(replied["error"], "COMPILE_IMAGE_SUGGESTION_INVALID")
        self.assertFalse(candidate_dir(self.compile_root, created["intent_id"]).exists())
        self.assertIsNone(self.library.get_current("stegosaurus", now=NOW))

    def test_return_framework_restores_r1_prompt(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            advance_intent,
            confirm_current,
            create_intent,
            return_framework,
            submit_reply,
        )
        from cognitive_card_server.knowledge_compile.store import (
            candidate_dir,
            framework_path,
            suggestions_path,
        )
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
        r1_prompt = created["expanded_prompt"]
        submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_framework_reply(),
            actor="owner",
            now=NOW,
        )
        advance_intent(
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            actor="owner",
            now=NOW,
        )
        submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_authoring_reply(
                suggestions=[{"proposition_id": "large-theropod"}]
            ),
            actor="owner",
            now=NOW,
        )
        restored = return_framework(
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
        )
        self.assertEqual(restored["round"], "framework")
        self.assertEqual(restored["state"], "framework")
        self.assertEqual(restored["expanded_prompt"], r1_prompt)
        self.assertTrue(framework_path(self.compile_root, created["intent_id"]).is_file())
        self.assertFalse(candidate_dir(self.compile_root, created["intent_id"]).exists())
        self.assertFalse(suggestions_path(self.compile_root, created["intent_id"]).is_file())
        with self.assertRaises(KnowledgeContractError) as ctx:
            confirm_current(
                library=self.library,
                compile_root=self.compile_root,
                intent_id=created["intent_id"],
                actor="owner",
                now=NOW,
            )
        self.assertEqual(ctx.exception.code, "COMPILE_FRAMEWORK_NOT_CURRENT")

    def test_return_from_complete_keeps_skeleton(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            advance_intent,
            create_intent,
            return_intent,
            submit_reply,
        )
        from cognitive_card_server.knowledge_compile.store import framework_path

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
        submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_framework_reply(),
            actor="owner",
            now=NOW,
        )
        advance_intent(
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            actor="owner",
            now=NOW,
        )
        submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=_stego_authoring_reply(),
            actor="owner",
            now=NOW,
        )
        returned = return_intent(
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
        )
        self.assertEqual(returned["state"], "open")
        self.assertEqual(returned["round"], "complete")
        self.assertTrue(framework_path(self.compile_root, created["intent_id"]).is_file())

    def test_advance_on_cat_fails(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            advance_intent,
            create_intent,
        )
        from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

        created = create_intent(
            library=self.library,
            compile_root=self.compile_root,
            topic_slug="cat",
            subject="家猫",
            goal="认识猫",
            actor="owner",
            now=NOW,
        )
        with self.assertRaises(KnowledgeContractError) as ctx:
            advance_intent(
                compile_root=self.compile_root,
                intent_id=created["intent_id"],
                actor="owner",
                now=NOW,
            )
        self.assertEqual(ctx.exception.code, "COMPILE_ADVANCE_NOT_FRAMEWORK")
```

Keep `test_framework_reply_does_not_set_current`, `test_return_from_framework_reopens`, and cat confirm tests unchanged.

If `library.get_current` does not expose a revision directory, do not assert a filesystem path under `self.library.root`. Assert `get_current` is not None and that candidate `knowledge-core.json` had no `image_suggestions` before confirm.

- [ ] **Step 2: Run the new tests** → FAIL.

- [ ] **Step 3: Implement pipeline**

`advance_intent`: `_require_actor`. Load intent. If `state == "current"` → `COMPILE_ALREADY_CURRENT`. If `round == "complete"` and `prompt_template_id == COMPLETE_DINOSAUR_TEMPLATE_ID` → return intent (idempotent). If `state != "framework"` or `object_type != dinosaur-entity` or `read_framework` is None → `COMPILE_ADVANCE_NOT_FRAMEWORK`. Else copy `prompt_template_id` / `prompt_template_sha256` / `expanded_prompt` onto `framework_prompt_*` keys if missing; set current prompt from `expand_complete_prompt` + `template_sha256_for(COMPLETE_DINOSAUR_TEMPLATE_ID)`; `round="complete"`; `state="open"`; `error=None`.

`submit_reply`: if `round == "framework"` keep R1 path. Else (complete, including cat): `delete_candidate`; `delete_suggestions`; try `parse_complete_reply` when `object_type` is dinosaur-entity, else existing `parse_authoring_reply` (cat has no suggestions). For dinosaur complete: `parse_complete_reply` then existing slug check, `projection={}`, `_require_search_intake`, `compile_authoring_request(..., allow_search=True)`, legend assign if entity pack, `write_candidate`, `write_suggestions` (always write the list, even `[]`). Failures that are not `_RAISE_ON_REPLY` → `state=failed` as today.

Putting `parse_complete_reply` only on dinosaur-entity avoids changing cat if someone includes `image_suggestions`. Cat path must remain `parse_authoring_reply`.

`return_intent`: if `round == "complete"`: allow `state in {"open", "compiled", "failed"}`; `delete_candidate`; `delete_suggestions`; **do not** `delete_framework`; `state="open"`; keep complete prompt. If `round == "framework"`: existing behavior (`delete_framework`).

`return_framework`: if `state == "current"` → `COMPILE_ALREADY_CURRENT`. If `round != "complete"` or no `framework.json` or no `framework_expanded_prompt` → `COMPILE_RETURN_FRAMEWORK_INVALID`. Restore the three `framework_prompt_*` fields to current prompt fields; `round="framework"`; `state="framework"`; `error=None`; `revision=None`; `delete_candidate`; `delete_suggestions`; keep `framework.json`.

`cancel_intent`: also `delete_suggestions`.

`confirm_current`: keep R1 `COMPILE_FRAMEWORK_NOT_CURRENT` when `round=="framework"` and not compiled. Complete compiled path unchanged.

- [ ] **Step 4: Re-run IntentPipelineTests** → all pass. Skip commit.

If `_stego_authoring_reply` fails `compile_authoring_request` because of overlay/intake, fix the helper (search intake, `kind` if required) until a dinosaur fossil-animal request compiles. Do not weaken the paleontology overlay.

---

## Phase 3: HTTP and kids ledger

### Task 4: HTTP, errors, ops HTML

**Files:**
- Modify: `src/cognitive_card_server/http/errors.py`
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Test: `tests/test_http_knowledge_compile.py`

**Verify:** combined focused gate in Global Constraints. New tests pass. Do not fix `LEGEND_ROLE_MISSING`.

**Depends on:** Task 3.

**Interfaces:**
- `POST /admin/knowledge-compile/{intent_id}/advance` body `{"actor": "..."}`
- `POST /admin/knowledge-compile/{intent_id}/return-framework` no body
- GET attaches `framework` when `framework.json` exists; attaches `image_suggestions` when sidecar exists

- [ ] **Step 1: Write HTTP tests**

```python
    def test_advance_then_confirm_current(self) -> None:
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
        self.assertEqual(created.status_code, 200, created.text)
        intent_id = created.json()["intent_id"]
        self.client.post(
            f"{COMPILE_URL}/{intent_id}/reply",
            headers=headers,
            json={"reply": _stego_framework_reply(), "actor": "owner"},
        )
        advanced = self.client.post(
            f"{COMPILE_URL}/{intent_id}/advance",
            headers=headers,
            json={"actor": "owner"},
        )
        self.assertEqual(advanced.status_code, 200, advanced.text)
        self.assertEqual(advanced.json()["round"], "complete")
        got = self.client.get(f"{COMPILE_URL}/{intent_id}", headers=headers)
        self.assertIn("framework", got.json())
        replied = self.client.post(
            f"{COMPILE_URL}/{intent_id}/reply",
            headers=headers,
            json={"reply": _stego_authoring_reply(suggestions=[{"proposition_id": "large-theropod"}]), "actor": "owner"},
        )
        self.assertEqual(replied.status_code, 200, replied.text)
        self.assertEqual(replied.json()["state"], "compiled")
        got = self.client.get(f"{COMPILE_URL}/{intent_id}", headers=headers)
        suggestions = got.json()["image_suggestions"]
        self.assertEqual(suggestions[0]["proposition_id"], "large-theropod")
        self.assertEqual(suggestions[0]["form"], "wordless-image")
        confirm = self.client.post(
            f"{COMPILE_URL}/{intent_id}/confirm-current",
            headers=headers,
            json={"actor": "owner"},
        )
        self.assertEqual(confirm.status_code, 200, confirm.text)
        self.assertEqual(confirm.json()["state"], "current")

    def test_advance_on_cat_is_conflict(self) -> None:
        created = self._create_cat()
        intent_id = created["intent_id"]
        advanced = self.client.post(
            f"{COMPILE_URL}/{intent_id}/advance",
            headers=self._admin_headers(),
            json={"actor": "owner"},
        )
        self.assertEqual(advanced.status_code, 409)
        self.assertEqual(advanced.json()["error"]["code"], "COMPILE_ADVANCE_NOT_FRAMEWORK")

    def test_return_framework_on_cat_is_conflict(self) -> None:
        created = self._create_cat()
        returned = self.client.post(
            f"{COMPILE_URL}/{created['intent_id']}/return-framework",
            headers=self._admin_headers(),
        )
        self.assertEqual(returned.status_code, 409)
        self.assertEqual(returned.json()["error"]["code"], "COMPILE_RETURN_FRAMEWORK_INVALID")

    def test_ops_intent_shell_has_round_two_controls_without_prompt_text(self) -> None:
        html = self.client.get("/card-os/ops/compile/ci_deadbeef").text
        self.assertIn("/advance", html)
        self.assertIn("/return-framework", html)
        self.assertNotIn("cognitive-card-authoring-request-v1", html)
        self.assertNotIn("{{framework_json}}", html)
```

Import `_stego_authoring_reply` next to `_stego_framework_reply`. Keep `test_dinosaur_framework_confirm_is_conflict` and `test_compile_shell_has_no_prompt_text`.

- [ ] **Step 2: Run the new HTTP tests** → FAIL.

- [ ] **Step 3: Wire HTTP and pages**

`errors.py`: add `COMPILE_ADVANCE_NOT_FRAMEWORK` and `COMPILE_RETURN_FRAMEWORK_INVALID` to `_CONFLICT_CODES`. `COMPILE_IMAGE_SUGGESTION_INVALID` stays default 400.

`http.py`: import `advance_intent`, `return_framework`, `read_suggestions`. Add POST `/advance` and `/return-framework`. `_public_compile_intent`: if `read_framework` not None, set `framework`; if `read_suggestions` not None, set `image_suggestions`; keep compiled `preview`.

`pages.py` `_COMPILE_INTENT_SCRIPT` `renderIntent`:
- Remove “Round 2 complete authoring is not this slice.”
- If `payload.state === "framework"`, add button “Start round 2” → `postThenReload(intentUrl("/advance"), { actor: actorValue() })`.
- If `payload.round === "complete" && payload.state !== "current"`, add button “Return to framework” → `postThenReload(intentUrl("/return-framework"))`.
- Preview: if `payload.framework`, show it (not only when `state === "framework"`). If compiled, still show `preview`. If `payload.image_suggestions`, append a second `<pre>` with that JSON.
- Confirm stays `disabled` unless `state === "compiled"`.

HTML shell strings may contain `/advance` and `/return-framework` (tests look for those). Must not contain template placeholders or authoring schema names.

- [ ] **Step 4: Combined focused gate** → new tests pass; mapping-lock 2 FAIL unchanged. Skip commit.

---

### Task 5: Kids docs after server tests pass

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `docs/README.md` (plan row In Progress)
- Modify: `docs/cognitive-card-os-system-design.md` (R2 pointer: spec Approved, server uncommitted)

**Verify (kids repo):**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack && bash scripts/ai/check-task-state.sh && bash scripts/ai/check-handoff.sh && bash scripts/ai/check-doc-governance.sh && git diff --check
```

**Depends on:** Task 4.

Roadmap `API-01-R2` stays `IN PROGRESS`. Record that server worktree has uncommitted R2 on top of uncommitted R1. Do not mark `DONE`. Do not commit unless asked.

---

## Self-review

1. Spec coverage: §6 advance Task 3/4; §7 template Task 1; §8 return-framework Task 3/4; §9–10 suggestions Task 2–3; §11 ops Task 4; §12 errors Task 4; §13.9 classification Task 1; cat path Tasks 3–4; no media-plan Global Constraints.
2. No TBD/TODO placeholders.
3. Names: `advance_intent`, `return_framework`, `parse_complete_reply`, `COMPLETE_DINOSAUR_TEMPLATE_ID` are consistent across tasks.
