# Multi-View Wordless Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On the knowledge-pipeline worktree, extend IMG-01 `illustration-intent` so optional wordless PNGs can be stored per legend pixel key, without replacing `hero.png` or feeding COMPOSE extra files.

**Architecture:** Snapshot `allowed_view_keys` from `assign_legend` at intent create. Extra keys are only `observe.three_view|section|exploded` and `setting.in_situ|interaction` when that role has instances. Upload extras only after `illustrated`. Inject `detect_burn_in` on extra uploads. COMPOSE still calls `read_hero_png` only.

**Tech Stack:** Python 3 unittest, existing `KnowledgeContractError`, FastAPI admin routes, ops HTML.

**Plan size:** Medium (7 tasks, 3 phases)

---

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md`
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1`
- Run tests with `PYTHONPATH=src .venv/bin/python`
- Do not change four-object schema, KNOW-03 facet ids, or IMG-01 `illustration-hero-v1` byte contract
- Do not implement RENDER-02 chrome or put extra PNGs into compose `assets`
- Do not merge/push/release, do not write production library, do not add `uv.lock` or kids `outputs/`
- Do not git commit unless the operator asks
- Old intents without `allowed_view_keys` behave as empty extras (pure IMG-01)

### Combined focused gate

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration tests.test_http_knowledge_illustration tests.test_knowledge_compose tests.test_http_knowledge_compose tests.test_http_knowledge_ops tests.test_http_auth tests.test_projection_legend tests.test_mapping_preview
```

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_illustration/views.py` | `PIXEL_VIEW_KEYS`, `parse_view_key`, `allowed_view_keys` |
| `src/cognitive_card_server/knowledge_illustration/templates/illustration-view-v1.txt` | Extra-key prompt template |
| `src/cognitive_card_server/knowledge_illustration/prompt.py` | `expand_view_prompt`, `VIEW_TEMPLATE_ID`, `detect_burn_in` |
| `src/cognitive_card_server/knowledge_illustration/store.py` | `views/` prompt+png read/write |
| `src/cognitive_card_server/knowledge_illustration/pipeline.py` | Snapshot keys at create; `submit_view_image`; `read_view_png`; `_public` views block |
| `src/cognitive_card_server/knowledge_ops/http.py` | POST/GET `.../views/{view_key}/image` |
| `src/cognitive_card_server/http/app.py` | Protected routes + multipart allowlist for views upload |
| `src/cognitive_card_server/knowledge_ops/pages.py` | `_ILLUSTRATION_SCRIPT` extra-views UI |
| `tests/test_knowledge_illustration.py` | Keys, prompts, upload, burn-in, learning_place |
| `tests/test_http_knowledge_illustration.py` | HTTP extras |
| `tests/test_knowledge_compose.py` | Compose still hero-only |
| `tests/test_http_auth.py` | New protected paths |

Kids docs (after server tests pass): spec already Approved; README plan row; roadmap IMG-02.

---

## Phase 1: Keys and prompts

### Task 1.1: Allowed pixel keys

**Files:**
- Create: `src/cognitive_card_server/knowledge_illustration/views.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/__init__.py` (export `allowed_view_keys`, `PIXEL_VIEW_KEYS`)
- Test: `tests/test_knowledge_illustration.py`

**Verify:** `cd .worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration.AllowedViewKeyTests -v` → all pass

**Depends on:** None

**Interface contract:**

```python
PIXEL_VIEW_KEYS = (
    "observe.three_view",
    "observe.section",
    "observe.exploded",
    "setting.in_situ",
    "setting.interaction",
)
HABITAT_BAN = "Do not draw the child's learning place as this subject's home or habitat."

def parse_view_key(key: str) -> tuple[str, str]:
    """Return (role, view). Raise KnowledgeContractError."""

def allowed_view_keys(core: Mapping[str, object]) -> tuple[str, ...]:
    """If assign_legend fails, return (). Else PIXEL_VIEW_KEYS filtered by role instances."""
```

`parse_view_key` order:

1. not `role.view` with both non-empty → `ILLUS_SLOT_NOT_ALLOWED`
2. `view` not in `OBSERVE_VIEWS | SETTING_VIEWS` → `LEGEND_VIEW_UNKNOWN`
3. otherwise return `(role, view)` — caller decides if the full key is in `PIXEL_VIEW_KEYS` / allowed set

- [ ] **Step 1: Write failing tests**

```python
class AllowedViewKeyTests(unittest.TestCase):
    def test_rabbit_observe_and_setting_keys(self) -> None:
        from cognitive_card_server.knowledge_illustration.views import allowed_view_keys, PIXEL_VIEW_KEYS
        keys = allowed_view_keys(_rabbit_core())
        self.assertEqual(keys, PIXEL_VIEW_KEYS)  # rabbit-real has appearance + environment

    def test_no_setting_omits_setting_keys(self) -> None:
        from cognitive_card_server.knowledge_illustration.views import allowed_view_keys
        core = copy.deepcopy(_rabbit_core())
        for unit in core["knowledge_units"]:
            if unit.get("coverage_facet") == "environment":
                unit["coverage_facet"] = "appearance"
                unit["legend_role"] = "observe"
        keys = allowed_view_keys(core)
        self.assertTrue(all(k.startswith("observe.") for k in keys))
        self.assertFalse(any(k.startswith("setting.") for k in keys))

    def test_assign_legend_failure_yields_empty(self) -> None:
        from cognitive_card_server.knowledge_illustration.views import allowed_view_keys
        core = {"propositions": [{"proposition_id": "p1", "standing": "active", "certainty": "established", "canonical_claim": "x"}], "knowledge_units": []}
        self.assertEqual(allowed_view_keys(core), ())

    def test_learning_place_and_unknown_view(self) -> None:
        from cognitive_card_server.knowledge_illustration.views import parse_view_key
        role, view = parse_view_key("learning_place.isolate")
        self.assertEqual((role, view), ("learning_place", "isolate"))
        with self.assertRaises(KnowledgeContractError) as ctx:
            parse_view_key("observe.not_a_view")
        self.assertEqual(ctx.exception.code, "LEGEND_VIEW_UNKNOWN")
```

If rabbit-real does **not** actually alias `environment`→`setting` (check `assign_legend(_rabbit_core())["roles"]` first), assert the real subset instead of `PIXEL_VIEW_KEYS`. Do not invent facets.

- [ ] **Step 2: Run tests — expect FAIL** (`allowed_view_keys` missing)

- [ ] **Step 3: Implement `views.py`**

```python
def allowed_view_keys(core: Mapping[str, object]) -> tuple[str, ...]:
    try:
        assigned = assign_legend(core)
    except KnowledgeContractError:
        return ()
    roles = assigned.get("roles") if isinstance(assigned, dict) else None
    present = set(roles) if isinstance(roles, dict) else set()
    out: list[str] = []
    for key in PIXEL_VIEW_KEYS:
        role, _view = key.split(".", 1)
        if role in present and roles.get(role):
            out.append(key)
    return tuple(out)
```

- [ ] **Step 4: Re-run AllowedViewKeyTests → PASS**

---

### Task 1.2: `illustration-view-v1` prompts

**Files:**
- Create: `src/cognitive_card_server/knowledge_illustration/templates/illustration-view-v1.txt`
- Modify: `src/cognitive_card_server/knowledge_illustration/prompt.py`
- Test: `tests/test_knowledge_illustration.py`

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration.ViewPromptTests tests.test_knowledge_illustration.PromptExpandTests -v` → all pass (hero tests still pass)

**Depends on:** Task 1.1

Hero template `illustration-hero-v1.txt` must not change. Add:

```text
Create exactly one image. Single subject. Children's natural-history encyclopedia illustration. Natural light, clear silhouette, no collage.

The image must not contain any text, letters, numbers, titles, labels, captions, watermarks, or UI frames.

View key: {{view_key}}
{{view_instruction}}

Subject display name: {{display_name}}
Classification (do not invent conflicting anatomy, clothing, props, or setting):
- primary_domain: {{primary_domain}}
- primary_form: {{primary_form}}
- object_subtype: {{object_subtype}}

If visible detail is insufficient, draw an ordinary external appearance. The page text, not this image, is the knowledge authority.

Forbidden scenes, copied verbatim from active safety_scope. Do not add new sentences. If this block is empty, invent none:
{{safety_constraints}}
{{habitat_ban}}
```

`VIEW_INSTRUCTIONS` (exact strings; tests `assertIn`):

| key | instruction |
| --- | --- |
| `observe.three_view` | Show the same subject in front, side, and top views in one image. Same pose and appearance. Not three separate files and no text labels. |
| `observe.section` | Show interior structure not visible from outside. Do not draw unlocked internal parts as established fact. |
| `observe.exploded` | Show how parts fit together. Do not invent unlocked parts. |
| `setting.in_situ` | Show the subject in its living or discovery environment. |
| `setting.interaction` | Show the subject interacting with its environment. |

`{{habitat_ban}}` is `HABITAT_BAN` plus a trailing newline for `setting.*`, else empty string.

Also add:

```python
def detect_burn_in(png_bytes: bytes) -> bool:
    del png_bytes
    return False
```

- [ ] **Step 1: Failing `ViewPromptTests`**

```python
class ViewPromptTests(unittest.TestCase):
    def test_three_view_has_grammar_not_claims(self) -> None:
        from cognitive_card_server.knowledge_illustration.prompt import expand_view_prompt, VIEW_TEMPLATE_ID
        core = _rabbit_core()
        text = expand_view_prompt(core=core, topic_slug="rabbit", view_key="observe.three_view")
        self.assertEqual(VIEW_TEMPLATE_ID, "illustration-view-v1")
        self.assertIn("must not contain any text", text.lower())
        self.assertIn("front, side, and top", text.lower())
        self.assertNotIn("{{view_key}}", text)
        for proposition in core["propositions"]:
            if proposition.get("standing") == "active":
                self.assertNotIn(proposition["canonical_claim"], text)

    def test_setting_prompt_bans_learning_place_as_habitat(self) -> None:
        from cognitive_card_server.knowledge_illustration.prompt import expand_view_prompt
        from cognitive_card_server.knowledge_illustration.views import HABITAT_BAN
        text = expand_view_prompt(core=_rabbit_core(), topic_slug="rabbit", view_key="setting.in_situ")
        self.assertIn(HABITAT_BAN, text)

    def test_observe_prompt_omits_habitat_ban(self) -> None:
        from cognitive_card_server.knowledge_illustration.prompt import expand_view_prompt
        from cognitive_card_server.knowledge_illustration.views import HABITAT_BAN
        text = expand_view_prompt(core=_rabbit_core(), topic_slug="rabbit", view_key="observe.section")
        self.assertNotIn(HABITAT_BAN, text)

    def test_hero_template_id_unchanged(self) -> None:
        from cognitive_card_server.knowledge_illustration.prompt import TEMPLATE_ID, expand_prompt
        self.assertEqual(TEMPLATE_ID, "illustration-hero-v1")
        self.assertIn("exactly one image", expand_prompt(core=_rabbit_core(), topic_slug="rabbit").lower())
```

- [ ] **Step 2: Run ViewPromptTests — FAIL**

- [ ] **Step 3: Implement `expand_view_prompt`**; reuse `display_name` / `classification_fields` / `active_safety_texts`

Unknown key not in `PIXEL_VIEW_KEYS` → `ILLUS_SLOT_NOT_ALLOWED` (after `parse_view_key`).

- [ ] **Step 4: ViewPromptTests + PromptExpandTests → PASS**

---

## Phase 2: Store and pipeline

### Task 2.1: Disk layout for extra views

**Files:**
- Modify: `src/cognitive_card_server/knowledge_illustration/store.py`
- Test: `tests/test_knowledge_illustration.py`

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration.ViewStoreTests -v` → all pass

**Depends on:** Task 1.2

```python
def view_prompt_path(root: Path, intent_id: str, key: str) -> Path:
    return intent_dir(root, intent_id) / "views" / f"{key}.prompt.txt"

def view_png_path(root: Path, intent_id: str, key: str) -> Path:
    return intent_dir(root, intent_id) / "views" / f"{key}.png"
```

Write via temp + `os.replace`, reject symlinks (same as `write_hero`). Creating `views/` only when writing an allowed key.

- [ ] **Step 1: Failing store round-trip test** (write prompt+png, read bytes, sha)

- [ ] **Step 2: Implement store helpers**

- [ ] **Step 3: ViewStoreTests → PASS**

---

### Task 2.2: Create snapshot + extra upload

**Files:**
- Modify: `src/cognitive_card_server/knowledge_illustration/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_illustration/__init__.py` (export `submit_view_image`, `read_view_png`)
- Test: `tests/test_knowledge_illustration.py`

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_illustration -v` → all pass

**Depends on:** Task 2.1

`create_intent` additions after expanding hero prompt:

```python
keys = allowed_view_keys(core)
intent["allowed_view_keys"] = list(keys)
intent["view_prompt_template_id"] = VIEW_TEMPLATE_ID
intent["view_prompt_template_sha256"] = view_template_sha256()
intent["views"] = {key: {"png_sha256": None} for key in keys}
for key in keys:
    write_view_prompt(root, intent_id, key, expand_view_prompt(core=core, topic_slug=topic_slug, view_key=key))
```

`_public` must include `allowed_view_keys` and `views` where each allowed key has `png_sha256` (null if missing) and `expanded_prompt` from disk. Missing meta field → `allowed_view_keys: []`, `views: {}`.

`submit_view_image(...)` and `read_view_png(...)`:

- cancelled → `ILLUS_NOT_ILLUSTRATED`
- `_sync_current` first (stale → `ILLUS_CURRENT_MOVED`)
- state != `illustrated` → `ILLUS_NOT_ILLUSTRATED`
- `parse_view_key(key)`; if `key not in PIXEL_VIEW_KEYS` or `key not in intent["allowed_view_keys"]` → `ILLUS_SLOT_NOT_ALLOWED`
- PNG magic/size same as hero; invalid extra PNG does **not** move intent to `failed` (stay `illustrated`, raise `ILLUS_IMAGE_INVALID` without writing)
- `detect_burn_in(bytes)` true → `LEGEND_BURN_IN`; keep old png if any
- success: write png, set `intent["views"][key]["png_sha256"]`, keep state `illustrated` (overwrite allowed)

`POST learning_place.isolate` after parse: view is registered, key not in PIXEL_VIEW_KEYS → `ILLUS_SLOT_NOT_ALLOWED`.

- [ ] **Step 1: Failing pipeline tests**

```python
class ExtraViewPipelineTests(unittest.TestCase):
    def test_create_lists_allowed_keys_without_png(self) -> None:
        # create_intent on published rabbit; load_intent has allowed keys; all png_sha256 None

    def test_open_rejects_extra_upload(self) -> None:
        # submit_view_image before hero → ILLUS_NOT_ILLUSTRATED

    def test_optional_skip_exploded(self) -> None:
        # illustrate hero; do not upload exploded; state illustrated; that sha None

    def test_setting_missing_slot_not_allowed(self) -> None:
        # fixture with no setting instances; POST setting.in_situ → ILLUS_SLOT_NOT_ALLOWED; no file

    def test_learning_place_key_rejected(self) -> None:
        # illustrated; submit_view_image key="learning_place.isolate" → ILLUS_SLOT_NOT_ALLOWED

    def test_overwrite_extra_keeps_illustrated(self) -> None:
        # upload three_view twice; state illustrated; sha updates

    def test_burn_in_keeps_old_bytes(self) -> None:
        from unittest.mock import patch
        # upload three_view MINIMAL_PNG; patch detect_burn_in True; second upload raises LEGEND_BURN_IN; file still first sha

    def test_current_moved_rejects_extra(self) -> None:
        # publish revision 2; submit_view_image → ILLUS_CURRENT_MOVED
```

Reuse `_publish_rabbit` / `submit_image` / `MINIMAL_PNG` already in the file. For no-setting fixture, publish a deepcopy of rabbit-real with environment units retargeted as in Task 1.1 **before** `library.publish`.

- [ ] **Step 2: Run ExtraViewPipelineTests — FAIL**

- [ ] **Step 3: Implement pipeline + `_public`**

- [ ] **Step 4: Full `tests.test_knowledge_illustration` → PASS**

---

## Phase 3: HTTP, ops, compose, docs

### Task 3.1: HTTP routes

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/http/app.py` (protected routes **and** multipart allowlist around the `illustration_image` regex — extra POST is also multipart)
- Modify: `tests/test_http_knowledge_illustration.py`
- Modify: `tests/test_http_auth.py` (route table must include the two new paths or the existing auth enumeration test fails)

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_illustration tests.test_http_auth -v` → all pass

**Depends on:** Task 2.2

Routes (same admin prefix):

- `POST /admin/knowledge-illustration/{intent_id}/views/{view_key}/image`
- `GET /admin/knowledge-illustration/{intent_id}/views/{view_key}/image`

`view_key` examples: `observe.three_view`. Regex:

```text
ii_[0-9a-f]{32}/views/(observe|setting)\.[a-z_]+/image
```

GET returns `FileResponse` like hero, `Cache-Control: private`. Reader/submit tokens 403. No token 401.

Multipart allowlist in `app.py` must match **both** `/image` and `/views/.../image` POSTs or extra uploads are rejected as oversized/wrong type.

- [ ] **Step 1: Failing HTTP tests** (create+upload hero+GET allowed keys; POST extra; GET extra sha; POST setting when absent 4xx SLOT_NOT_ALLOWED; no token GET extra 401)

- [ ] **Step 2: Register routes + allowlist**

- [ ] **Step 3: HTTP + auth tests → PASS**

---

### Task 3.2: Ops extra-views UI

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py` (`_ILLUSTRATION_SCRIPT` inside `state === "illustrated"` after hero image, before propositions list)
- Test: `tests/test_http_knowledge_ops.py` (or illustration HTTP if ops tests already fetch the illustration HTML)

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_ops -v` → all pass

**Depends on:** Task 3.1

UI rules:

- Only iterate `payload.allowed_view_keys`
- Each key: readonly textarea of `payload.views[key].expanded_prompt`, Copy, file+Upload posting to `/views/{key}/image`
- Missing png: no error text, empty img
- Do not render chrome roles or disallowed keys
- Unauthenticated shell must not embed extra prompts (same as hero: prompts arrive via authenticated GET)

If `test_http_knowledge_ops.py` has no illustration page test, add one: GET `/card-os/ops/illustration/{id}` without token has no `allowed_view_keys` JSON and no prompt text from rabbit claims; with token, HTML/JS contains `views/` and `allowed_view_keys`.

- [ ] **Step 1: Failing assertion on script containing `views/`**

- [ ] **Step 2: Render extra-views block**

- [ ] **Step 3: ops tests → PASS**

---

### Task 3.3: Compose hero-only + combined gate + kids docs

**Files:**
- Modify: `tests/test_knowledge_compose.py` — after illustrate, write a dummy `views/observe.three_view.png` on disk and assert `compose_projection` `assets` still only hero (inspect render inputs or assert compose meta has no view sha fields; simplest: patch/spy is unnecessary if you assert `compose` meta keys == existing set and OBS PNG bytes equal hero, not the dummy extra)
- Kids: `docs/cognitive-card-os-roadmap.md` IMG-02 next-action after this plan exists; `docs/ai/CURRENT_TASK.md`; `docs/ai/HANDOFF.md`
- Do **not** change `compose_projection` to read `views/` — test proves it does not

**Verify:** combined focused gate (see header) → all pass; from kids root `bash scripts/ai/check-task-state.sh` and `git diff --check`

**Depends on:** Task 3.2

```python
def test_compose_ignores_extra_view_png(self) -> None:
    # illustrate rabbit; write extra png with different bytes under views/
    # compose_projection
    # OBS band / hero sha still MINIMAL_PNG sha; compose meta has no views dict
```

If writing different bytes is awkward, `self.assertFalse(any(path.name.endswith(".png") and path.parent.name == "views" for path in used))` is too internal. Prefer: extra file larger/different; OBS output file sha256 equals `sha256(MINIMAL_PNG)` (already how compose stores hero).

- [ ] **Step 1: Failing compose test if someone accidentally reads views/**

- [ ] **Step 2: Leave compose pipeline unchanged unless the test already passes**

- [ ] **Step 3: Combined focused gate**

- [ ] **Step 4: Kids checker**

No server `uv.lock`. No kids `outputs/`. No commit unless asked.

---

## Spec coverage

| Spec | Task |
| --- | --- |
| §4 IMG-01 coexistence / optional extras / same intent | 2.2 (hero tests remain) |
| §5 allowed set / empty on assign_legend fail | 1.1 |
| §5 learning_place not a pixel key | 2.2 |
| §6 view prompts / habitat ban / no claims | 1.2 |
| §7 illustrated-only extras / overwrite | 2.2 |
| §8 disk `views/` | 2.1–2.2 |
| §9 HTTP | 3.1 |
| §10 burn-in hook | 2.2 |
| §11 ops extra zone | 3.2 |
| §12 error codes | 1.1, 2.2, 3.1 |
| §13 compose ignores views | 3.3 |
| §14 acceptance 1–10 | 1.1–3.3 |
| RENDER-02 / image API / production | out of plan |

## Placeholder scan

No TBD. Commit steps omitted (operator-gated). Production OCR explicitly not shipped (`detect_burn_in` default false).
