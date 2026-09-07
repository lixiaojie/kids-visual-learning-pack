# Operator Frozen Node Illustration and Compose Lock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After a media-plan freeze, the operator gets per-`wordless-image` node prompts, optionally uploads PNGs, composes without failing on missing slots, and locks the projection with QA-01 `approve` without publishing.

**Architecture:** Reuse `is_stale` via `require_frozen_media_plan`. Bind illustration-intent to the freeze when a pointer exists; keep isolate create unchanged when there is no pointer. Store node prompts/PNGs under `illustration-intents/{id}/nodes/`. Compose print still uses only `hero.png`. Screen chrome adds `node_images` on observe modules. `lock_composed_projection` calls `record_review(approve)` only.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, existing `KnowledgeLibrary`, illustration-intent, compose, QA-01, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium (5 tasks)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-07-operator-frozen-node-illustration-compose-lock-design.md` (Approved). Program: `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md` §5.3.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1` @ `28ec476`.
- Kids repo: `/Users/admin/projects/family/kids-visual-learning-pack`.
- Run tests with `PYTHONPATH=src .venv/bin/python`.
- Do not call OpenAI / image APIs. Do not write Skill claims.
- Do not call `publish_approved` or `publish_from_work` from the lock path.
- Do not change `lock_mapping`, Confirm current, four-object schema, or print band formula.
- Do not add a fifth governed object. Do not write node files into `media-plans/` or four-object revisions.
- Do not write production knowledge-library. Do not merge/push/release. Do not add `uv.lock` or kids `outputs/`.
- Do not git commit unless the operator asks. Skip every commit step.
- Do not mark IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`.
- Known combined-gate 2 FAIL on ops mapping-lock `LEGEND_ROLE_MISSING` stay untouched. Do not use `rabbit-composite` as the happy-path fixture.

### Combined focused gate (after Task 4)

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_classification_registry tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_http_auth tests.test_knowledge_library_mapping tests.test_knowledge_layout tests.test_http_knowledge_layout tests.test_knowledge_illustration tests.test_http_knowledge_illustration tests.test_knowledge_compose tests.test_http_knowledge_compose
```

Expected: new tests pass; the two known `LEGEND_ROLE_MISSING` mapping-lock ops fails remain.

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_layout/pipeline.py` | `require_frozen_media_plan` |
| `src/cognitive_card_server/knowledge_layout/__init__.py` | Export the helper |
| `src/cognitive_card_server/knowledge_illustration/prompt.py` | `illustration-node-v1` expand |
| `src/cognitive_card_server/knowledge_illustration/templates/illustration-node-v1.txt` | Node prompt template |
| `src/cognitive_card_server/knowledge_illustration/store.py` | `nodes/{pid}.txt` / `.png` IO |
| `src/cognitive_card_server/knowledge_illustration/pipeline.py` | Bind on create; submit/read node PNG |
| `src/cognitive_card_server/knowledge_illustration/__init__.py` | Export new functions |
| `src/cognitive_card_server/knowledge_compose/chrome.py` | `node_images` on OBS modules |
| `src/cognitive_card_server/knowledge_compose/pipeline.py` | Freeze/bind gate; GET allows `approved`; lock |
| `src/cognitive_card_server/knowledge_compose/__init__.py` | Export `lock_composed_projection` |
| `src/cognitive_card_server/knowledge_ops/http.py` | Node image routes + compose lock |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Layout 请图; illustration nodes; compose 锁定 |
| `src/cognitive_card_server/http/app.py` | `PROTECTED_ROUTES` +3 |
| `src/cognitive_card_server/http/errors.py` | New 409/404 codes |
| `tests/test_knowledge_illustration.py` | Bind / node prompt / node PNG |
| `tests/test_knowledge_compose.py` | Freeze gate, missing slots, lock |
| `tests/test_http_knowledge_illustration.py` | Node HTTP |
| `tests/test_http_knowledge_compose.py` | Lock HTTP + shell |
| `tests/test_http_auth.py` | `PROTECTED_ROUTES` length 58 |

Kids (Task 5): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`, `docs/cognitive-card-os-system-design.md`.

---

## Phase 1: Freeze gate and bound create

### Task 1: `require_frozen_media_plan` + node prompt + bound `create_intent`

**Files:**
- Modify: `src/cognitive_card_server/knowledge_layout/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_layout/__init__.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/prompt.py`
- Create: `src/cognitive_card_server/knowledge_illustration/templates/illustration-node-v1.txt`
- Modify: `src/cognitive_card_server/knowledge_illustration/store.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/__init__.py`
- Test: `tests/test_knowledge_illustration.py`
- Test: `tests/test_knowledge_layout.py` (one helper test for `require_frozen_media_plan`)

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_layout tests.test_knowledge_illustration -v
```

Expected: all pass (including existing isolate tests that never create a media-plan pointer).

**Depends on:** None.

**Interfaces:**
- Consumes: `is_stale`, `KnowledgeLibrary.get_media_plan` / `read_media_plan_revision` / `get_current` / `get_mapping`, `assign_legend` / `resolve_legend_role`, existing `create_intent`
- Produces:
  - `require_frozen_media_plan(*, library, topic_slug, now) -> tuple[dict, dict] | None`
  - `expand_node_prompt(*, core, topic_slug, proposition_id, legend_role) -> str`
  - `create_intent` writes `media_plan_revision` / `media_plan_identity` / `nodes` only when a freeze is present

- [ ] **Step 1: Write failing tests**

In `tests/test_knowledge_layout.py` add:

```python
def test_require_frozen_none_without_pointer(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        library = KnowledgeLibrary(Path(tmp) / "library")
        _publish_rabbit(library)
        self.assertIsNone(
            require_frozen_media_plan(library=library, topic_slug="rabbit", now=NOW)
        )

def test_require_frozen_rejects_draft(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        library = KnowledgeLibrary(Path(tmp) / "library")
        _publish_rabbit(library)
        get_layout(library=library, topic_slug="rabbit", actor="owner", now=NOW)
        with self.assertRaises(KnowledgeContractError) as caught:
            require_frozen_media_plan(library=library, topic_slug="rabbit", now=NOW)
        self.assertEqual(caught.exception.code, "MEDIA_PLAN_NOT_FROZEN")
```

In `tests/test_knowledge_illustration.py` add helpers that lock mapping, GET layout, PATCH one safe appearance id to `wordless-image`, freeze, then:

```python
def test_create_without_pointer_has_no_nodes_key(self) -> None:
    # existing rabbit publish + create_intent
    self.assertNotIn("nodes", intent)
    self.assertNotIn("media_plan_revision", intent)

def test_create_with_draft_pointer_fails(self) -> None:
    # get_layout only, no freeze
    self.assert_code("MEDIA_PLAN_NOT_FROZEN", create_intent, ...)

def test_create_bound_expands_node_prompts(self) -> None:
    intent = create_intent(...)  # after freeze with one wordless-image node
    self.assertEqual(intent["media_plan_revision"], pointer["revision"])
    self.assertEqual(intent["media_plan_identity"], pointer["identity"])
    self.assertIn(pid, intent["nodes"])
    prompt = read_node_prompt(root, intent["intent_id"], pid)
    self.assertIn("must not contain any text", prompt.lower())
    self.assertNotIn(claim_text, prompt)
    self.assertEqual(intent["prompt_template_id"], "illustration-hero-v1")

def test_learning_place_and_setting_include_habitat_ban(self) -> None:
    # freeze those roles as wordless-image when the rabbit core has them
    self.assertIn("learning place", prompt.lower())
```

Pick `pid` from `active_proposition_ids` whose `form_forbidden(..., "wordless-image")` is False.

- [ ] **Step 2: Run tests to verify they fail**

Run the verify command. Expected: FAIL with `require_frozen_media_plan` / `nodes` missing.

- [ ] **Step 3: Implement**

Add to `knowledge_layout/pipeline.py`:

```python
def require_frozen_media_plan(
    *,
    library: KnowledgeLibrary,
    topic_slug: str,
    now: datetime,
) -> tuple[dict[str, object], dict[str, object]] | None:
    pointer = library.get_media_plan(topic_slug)
    if pointer is None:
        return None
    if pointer.get("status") != "frozen":
        raise KnowledgeContractError("MEDIA_PLAN_NOT_FROZEN", topic_slug)
    current = library.get_current(topic_slug, now=now)
    identity = current.identity if current is not None else None
    mapping = library.get_mapping(topic_slug)
    if is_stale(pointer=pointer, current_identity=identity, mapping=mapping):
        raise KnowledgeContractError("MEDIA_PLAN_STALE", topic_slug)
    revision = int(pointer["revision"])
    plan = library.read_media_plan_revision(topic_slug, revision)
    return pointer, plan
```

Export it from `knowledge_layout/__init__.py`.

Create `illustration-node-v1.txt` mirroring `illustration-view-v1.txt` with placeholders `{{legend_role}}`, `{{role_instruction}}`, `{{habitat_ban}}`. Wordless ban sentence must match hero/view.

In `prompt.py`:

```python
NODE_TEMPLATE_ID = "illustration-node-v1"
NODE_INSTRUCTIONS = {
    "observe": "Recognizable external appearance or pose of the same subject as the isolate hero. Not a second collage.",
    "compare": "Parts side by side. No name labels on the image.",
    "evidence": "Fossil, skeleton, model, or institutional record as evidence. Do not draw evidence as a living animal unless the classification is a living animal.",
    "time": "Geological setting or era atmosphere. No years, numerals, or letters.",
    "place": "Living or discovery landscape. No map labels.",
    "learning_place": "The child's learning place.",
    "habit": "Behavior or function happening.",
    "kind": "Visual grouping cue for kind. No taxonomic rank text.",
    "sequence": "An ordered process. No step numbers.",
    "setting": "In situ or interaction.",
}
DEFAULT_NODE_INSTRUCTION = (
    "Ordinary external appearance. Do not invent organs when visible detail is insufficient."
)

def expand_node_prompt(*, core, topic_slug, proposition_id, legend_role) -> str:
    # same slug/classification/safety fill as expand_view_prompt
    # role_instruction from NODE_INSTRUCTIONS.get(legend_role, DEFAULT)
    # habitat_ban = HABITAT_BAN + newline if legend_role in {"learning_place", "setting"} else ""
```

`store.py`: `_NODE_ID = re.compile(r"^[A-Za-z0-9_-]+$")`; `node_prompt_path` / `node_png_path` under `nodes/{pid}.txt` and `nodes/{pid}.png`; reject `..` and extra slashes via the regex; `write_node_prompt` / `read_node_prompt`.

`create_intent`: after current exists, call `require_frozen_media_plan`. If tuple, set the three meta fields and write each wordless-image node's prompt. If None, do not add those keys. `form=text` / `interactive` skipped.

`_public`: if `nodes` is a dict, attach each id's `png_sha256` and `expanded_prompt` (empty string if file missing).

- [ ] **Step 4: Run tests to verify they pass**

Same verify command. Expected: PASS.

- [ ] **Step 5: Skip commit**

---

## Phase 2: Node PNG and compose/lock

### Task 2: Node PNG upload/read

**Files:**
- Modify: `src/cognitive_card_server/knowledge_illustration/store.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/__init__.py`
- Test: `tests/test_knowledge_illustration.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration -v
```

Expected: all pass.

**Depends on:** Task 1.

**Interfaces:**
- Consumes: bound intent `nodes`, `require_frozen_media_plan`, existing PNG magic/size checks
- Produces: `submit_node_image(...)`, `read_node_png(...)`

- [ ] **Step 1: Write failing tests**

```python
def test_node_upload_before_illustrated_fails(self) -> None:
    self.assert_code("ILLUS_NOT_ILLUSTRATED", submit_node_image, ...)

def test_node_upload_unknown_id_fails(self) -> None:
    # illustrated bound intent
    self.assert_code("ILLUS_NODE_UNKNOWN", submit_node_image, ..., proposition_id="nope")

def test_node_upload_unbound_fails(self) -> None:
    # isolate intent then freeze another way: create isolate first, then get_layout+freeze
    # submit_node_image → ILLUS_PLAN_UNBOUND
    ...

def test_node_upload_stale_fails(self) -> None:
    # bound + illustrated, then relock mapping
    self.assert_code("MEDIA_PLAN_STALE", submit_node_image, ...)

def test_node_upload_success_keeps_illustrated(self) -> None:
    out = submit_node_image(...)
    self.assertEqual(out["state"], "illustrated")
    self.assertTrue(str(out["nodes"][pid]["png_sha256"]).startswith("sha256:"))
    self.assertEqual(read_node_png(...), MINIMAL_PNG)
```

Add `require_intent_bound(intent, pointer)` in pipeline: `media_plan_revision` equals pointer `revision` and `media_plan_identity` equals pointer `identity`; else `ILLUS_PLAN_UNBOUND`.

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL `submit_node_image` not defined.

- [ ] **Step 3: Implement**

Mirror `submit_view_image` / `read_view_png`. Require `illustrated`, `_sync_current`, `require_frozen_media_plan` not None, `require_intent_bound`, id in `intent["nodes"]`. PNG checks same as hero. Overwrite allowed. Missing node file is not `failed`.

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Skip commit**

---

### Task 3: Compose freeze gate, chrome `node_images`, lock function

**Files:**
- Modify: `src/cognitive_card_server/knowledge_compose/chrome.py`
- Modify: `src/cognitive_card_server/knowledge_compose/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_compose/__init__.py`
- Test: `tests/test_knowledge_compose.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose tests.test_knowledge_illustration -v
```

Expected: all pass. Existing rabbit compose tests (no media-plan pointer) still compose with isolate hero.

**Depends on:** Task 2.

**Interfaces:**
- Consumes: `require_frozen_media_plan`, `require_intent_bound`, `record_review`, `read_node_png`
- Produces: `lock_composed_projection(*, library, illustration_root, work_root, compose_root, topic_slug, actor, now)`; `page_modules(..., node_shas=None)`; compose POST gated; compose GET allows QA `approved`

- [ ] **Step 1: Write failing tests**

Keep `_illustrate` on rabbit **without** `get_layout` so old compose tests stay green.

Add a bound helper: lock_mapping, get_layout, patch one allowed id to `wordless-image`, freeze, then create_intent+submit_image.

```python
def test_compose_draft_pointer_fails(self) -> None:
    get_layout(...)
    self.assert_code("MEDIA_PLAN_NOT_FROZEN", compose_projection, ...)

def test_compose_unbound_intent_fails(self) -> None:
    # illustrate first (no pointer), then get_layout+freeze
    self.assert_code("ILLUS_PLAN_UNBOUND", compose_projection, ...)

def test_compose_without_node_png_succeeds(self) -> None:
    # bound + hero only
    view = compose_projection(...)
    obs = next(p for p in view["pages"] if p["page"] == "CN_OBS")
    self.assertTrue(obs["has_hero"])
    for mod in obs["modules"]:
        self.assertEqual(mod.get("node_images") or [], [])

def test_compose_print_assets_still_hero_only(self) -> None:
    # spy/assert render_locked assets keys == {"CN_OBS:band", "EN_OBS:band"}
    ...

def test_lock_without_compose_fails(self) -> None:
    self.assert_code("COMPOSE_NO_COMPOSE", lock_composed_projection, ...)

def test_lock_approve_does_not_publish(self) -> None:
    compose_projection(...)
    with patch("cognitive_card_server.four_card_publish.publish.publish_approved") as pub:
        out = lock_composed_projection(...)
        pub.assert_not_called()
    report = json.loads((work_root / "rabbit" / "qa" / "qa-report.json").read_text())
    self.assertEqual(report["status"], "approved")
    self.assertEqual(report["review"]["decision"], "approve")
    current = library.get_current("rabbit", now=COMPOSE_NOW)
    # identity unchanged vs pre-lock

def test_load_compose_after_lock(self) -> None:
    compose_projection(...)
    lock_composed_projection(...)
    view = load_compose(...)
    self.assertEqual(view["intent_id"], ...)
```

For knowledge-card-only roles: if you can patch a `kind` id that mapping puts on KNOW, upload node PNG, compose, assert CN_KNOW modules have no `node_images` / no img keys. If rabbit mapping never puts that id on OBS, that is the spec §15.6 case.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement**

`chrome.page_modules`: add `node_shas: dict[str, str] | None = None`. Keep pid lists per role, not only texts. On OBS pages, for each pid in the module with a sha, append `{"proposition_id": pid, "png_sha256": sha}` to `node_images`. KNOW pages: `node_images` always `[]`.

`compose_projection` / `_require_inputs`:
- After current exists, `plan = require_frozen_media_plan(...)`.
- If not None: `require_intent_bound(intent, pointer)`.
- `compose_projection` still requires QA `awaiting_review`.
- `load_compose` uses `_require_inputs(..., allow_approved=True)` so status in `{awaiting_review, approved}`.
- Print `assets` unchanged: hero only.
- Pass node sha map from `intent["nodes"]` into `page_modules`.

`lock_composed_projection`:
- `require_frozen_media_plan` must not be None (no pointer → `MEDIA_PLAN_NOT_FROZEN`).
- `read_meta(compose_root, topic)` missing → `COMPOSE_NO_COMPOSE`.
- `_require_inputs(..., allow_approved=False)` so still `awaiting_review`, plus bind check.
- Compose meta intent_id / identity must match.
- `record_review(topic_dir / "qa", actor=..., decision="approve", now=now)`.
- Do not import or call `publish_approved`.

- [ ] **Step 4: Run tests to verify they pass**

- [ ] **Step 5: Skip commit**

---

## Phase 3: HTTP, ops, ledger

### Task 4: HTTP, errors, ops HTML

**Files:**
- Modify: `src/cognitive_card_server/http/errors.py`
- Modify: `src/cognitive_card_server/http/app.py`
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Test: `tests/test_http_knowledge_illustration.py`
- Test: `tests/test_http_knowledge_compose.py`
- Test: `tests/test_http_auth.py` — `len(PROTECTED_ROUTES)` from 55 to 58
- Test: `tests/test_http_knowledge_ops.py` — layout/compose shells still claim-free

**Verify:** Task 4 unittest files plus the combined focused gate in Global Constraints.

Expected: new tests pass; 2 known `LEGEND_ROLE_MISSING` remain.

**Depends on:** Task 3.

**Interfaces:**
- Consumes: Task 1–3 functions
- Produces: HTTP routes in spec §12; ops UI in spec §13

- [ ] **Step 1: Write failing HTTP tests**

Routes:

- `POST/GET /admin/knowledge-illustration/{intent_id}/nodes/{proposition_id}/image`
- `POST /admin/knowledge-compose/{topic}/lock` body `{"actor": "..."}`

Assert:

- no token → not 200
- GET node PNG after upload matches sha; 404 `ILLUS_NODE_UNKNOWN`
- lock 409 `COMPOSE_NO_COMPOSE` before compose
- lock 200/JSON with QA approved and catalog unchanged
- unauthenticated compose/illustration HTML has no `claim`, no node prompt, no `proposition_id` list of claims

`PROTECTED_ROUTES`: add GET+POST node image and POST lock **before** the generic `GET .../knowledge-compose/{topic}` and `GET .../knowledge-illustration/{intent_id}` entries (same pattern as views/image vs intent GET).

Regex for node id: `[A-Za-z0-9_-]+`. Path traversal tests: `../x` → 404/400, not file read.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement**

`errors.py`: add `ILLUS_PLAN_UNBOUND`, `COMPOSE_NO_COMPOSE` to `_CONFLICT_CODES`; `ILLUS_NODE_UNKNOWN` to `_NOT_FOUND_CODES`.

`http.py`: copy the views/image handlers, swap view_key for proposition_id, call `submit_node_image` / `read_node_png`. Resolve path under `intent_dir / "nodes"` with `is_relative_to`. Lock handler calls `lock_composed_projection`.

`pages.py`:

- Layout frozen+not stale: link 「请图」 to `/card-os/ops/illustration/{intent_id}` if a bound illustrated/open intent exists for the topic, else keep creating via existing illustration entry. Do not add an export-prompt freeze button.
- Illustration page: if `payload.nodes`, list each id with copy prompt + file input posting to `/nodes/{id}/image`. Empty slot is not an error banner. Existing isolate UI unchanged when `nodes` absent.
- Compose `renderCompose`: for OBS modules, for each `mod.node_images`, fetch `/nodes/{proposition_id}/image` (not `/views/`). KNOW pages must not create those `<img>` tags. After lock (`qa` approved or lock POST success), hide 「锁定投影」 / show 已锁定. Button only when compose GET works and status is awaiting_review.
- Tokenless shells: do not embed expanded node prompts or claims.

- [ ] **Step 4: HTTP tests PASS + combined focused gate** (2 known mapping FAIL only)

- [ ] **Step 5: Skip commit**

---

### Task 5: Kids ledger (no DONE)

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`
- Modify: `docs/cognitive-card-os-roadmap.md` — IMG-03 `IN PROGRESS`; record server SHA after Tasks 1–4; do not mark `DONE`; FLOW-01 still program not complete; PUBLISH-02 still BACKLOG
- Modify: `docs/README.md` — this plan In Progress
- Modify: `docs/cognitive-card-os-system-design.md` §11 IMG-03 pointer: implemented locally, not DONE

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack && bash scripts/ai/check-task-state.sh && bash scripts/ai/check-handoff.sh && bash scripts/ai/check-doc-governance.sh && git diff --check
```

Expected: task-state PASS; handoff PASS; doc-governance WARN only on Last Reviewed 2026-07-24; diff --check PASS.

**Depends on:** Task 4.

- [ ] **Step 1: Roadmap** — IMG-03 IN PROGRESS with spec+plan paths and server SHA; 非范围 still PUBLISH-02 / production / merge.
- [ ] **Step 2: System design** one bullet: frozen node prompts + compose lock; not PUBLISH-02; not DONE.
- [ ] **Step 3: CURRENT_TASK / HANDOFF** from real `git status` and the combined gate output. Isolation map: kids docs + server worktree. Exact Next Action: do not merge/push/release; do not mark DONE.
- [ ] **Step 4: Run verification commands** and paste real PASS/WARN/FAIL into HANDOFF.
- [ ] **Step 5: Skip commit** unless asked.

---

## Self-review

1. **Spec coverage:** §5–6 Task 1; §7–9 Task 1–2; §10–11 Task 3; §12–14 Task 4; §15.1 old path Tasks 1 and 3; §15.5–7 lock Task 3; §15.8–9 HTML/print Task 4; kids ledger Task 5; no PUBLISH-02.
2. **Placeholders:** none.
3. **Types:** `require_frozen_media_plan` / `submit_node_image` / `read_node_png` / `lock_composed_projection` names stable across tasks.
4. **Verify commands:** each task has a runnable unittest or bash line.
5. **Depends on:** Task 1 → 2 → 3 → 4 → 5.

Do not implement this plan until the operator picks Subagent-Driven or Inline Execution.
