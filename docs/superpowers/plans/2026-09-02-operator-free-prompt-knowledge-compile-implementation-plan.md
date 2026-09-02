# Operator Free-Prompt Knowledge Compile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the token workbench expand a short subject+goal into a copyable ChatGPT prompt, ingest the pasted reply into a four-object knowledge current, without an API executor or Codex claim.

**Architecture:** File-backed `compile-intent` under the injected candidate root. A versioned prompt template fills `expanded_prompt`. `POST reply` parses one authoring JSON, compiles with `allow_search=True`, then `confirm-current` calls `KnowledgeLibrary.publish`. HTML shells stay claim-free; ChatGPT stays in the operator's membership browser.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, existing `compile_authoring_request` / `KnowledgeLibrary.publish`, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium (5 tasks, 3 phases)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md` (Approved).
- No OpenAI API, no Codex claim, no `knowledge_compile` scope, no `GenerationPacket`, no generation-input.
- Do not change four-object schema, v1 FACT keys, AUTHOR-05 defaults, or packet contract.
- Do not flip `source-intake-search.v1.json` `"enabled"` to true (CLI authoring must still raise `INTAKE_METHOD_DISABLED`).
- Do not write production knowledge-library. HTTP/CLI must take an explicit library / candidate root (tests use tmp).
- Do not touch KNOW-04 six-topic currents in any real production path. Tests seed rabbit only in tmp libraries.
- `spider-gwen` is always `COMPILE_SLUG_FORBIDDEN`.
- Do not git commit, merge server `main`, push, add `uv.lock`, reload Nginx, or install a production release.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core`. Use `.venv/bin/python` with `PYTHONPATH=src`.
- Do not modify uncommitted WB-03 weighted-layout behavior except to attach new routes/pages.
- Kids docs live in `/Users/admin/projects/family/kids-visual-learning-pack`. Do not touch `outputs/`.
- Register compile HTML routes **before** `/card-os/ops/{topic}` so `compile` is not captured as a slug.

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_compile/__init__.py` | Public CLI-facing functions |
| `src/cognitive_card_server/knowledge_compile/prompt.py` | Load template, sha256, `expand_prompt` |
| `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-v1.txt` | Copyable ChatGPT prompt template |
| `src/cognitive_card_server/knowledge_compile/store.py` | Intent JSON + candidate dir under `compile-intents/` |
| `src/cognitive_card_server/knowledge_compile/parse.py` | Extract one authoring object from a pasted reply |
| `src/cognitive_card_server/knowledge_compile/pipeline.py` | `create_intent`, `submit_reply`, `confirm_current`, `return_intent`, `cancel_intent` |
| `src/cognitive_card_server/coverage/accuracy.py` | `allow_search` on `apply_accuracy_kernel` |
| `src/cognitive_card_server/knowledge_contract/authoring.py` | `compile_authoring_request(..., allow_search=False)` |
| `src/cognitive_card_server/knowledge_ops/http.py` | Admin compile routes; HTML compile routes before `{topic}` |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Compile form / intent shells; index link |
| `src/cognitive_card_server/http/app.py` | `PROTECTED_ROUTES` for compile admin paths |
| `src/cognitive_card_server/http/errors.py` | Conflict/not-found codes for `COMPILE_*` |
| `tests/test_knowledge_compile.py` | Template, intent, reply, confirm, retry |
| `tests/test_http_knowledge_compile.py` | Admin JSON + HTML shell + scope |
| `examples/authoring/cat-compile-reply.json` | Optional; tests may synthesize from `rabbit-real.json` instead |

Kids (Task 5): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`.

---

## Phase 1: Prompt, intent, reply pipeline

### Task 1: Prompt template and expand

**Files:**
- Create: `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-v1.txt`
- Create: `src/cognitive_card_server/knowledge_compile/prompt.py`
- Create: `src/cognitive_card_server/knowledge_compile/__init__.py`
- Test: `tests/test_knowledge_compile.py` (start this file here; later tasks append)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile.PromptExpandTests -v` → all pass
**Depends on:** None

**Interfaces:**
- Consumes: none
- Produces:

```python
TEMPLATE_ID = "knowledge-compile-v1"
SUBJECT_MAX = 200
GOAL_MAX_BYTES = 2048

def template_path() -> Path: ...
def template_sha256() -> str:
    """Return 'sha256:' + hex of template file bytes."""

def expand_prompt(*, subject: str, goal: str, topic_slug: str) -> str:
    """Replace {{subject}} {{goal}} {{topic_slug}} exactly once each.
    Raise KnowledgeContractError COMPILE_BRIEF_TOO_LARGE or COMPILE_SLUG_INVALID."""
```

- [ ] **Step 1: Write failing tests** in `tests/test_knowledge_compile.py`

```python
"""Compile-intent: copyable prompt, reply pipeline, confirm current."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cognitive_card_server.knowledge_compile.prompt import (
    TEMPLATE_ID,
    expand_prompt,
    template_sha256,
)
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


class PromptExpandTests(unittest.TestCase):
    def test_expanded_prompt_contains_brief_and_rules(self) -> None:
        text = expand_prompt(
            subject="家猫",
            goal="深圳5–6岁认识猫的身体、生活与照护，不讲治病。",
            topic_slug="cat",
        )
        self.assertIn("家猫", text)
        self.assertIn("深圳5–6岁认识猫的身体、生活与照护，不讲治病。", text)
        self.assertIn("cat", text)
        self.assertIn("cognitive-card-authoring-request-v1", text)
        self.assertIn("intake.method=search", text)
        self.assertIn("coverage_facet", text)
        self.assertNotIn("{{subject}}", text)

    def test_subject_too_long(self) -> None:
        with self.assertRaises(KnowledgeContractError) as ctx:
            expand_prompt(subject="猫" * 201, goal="认识猫", topic_slug="cat")
        self.assertEqual(ctx.exception.code, "COMPILE_BRIEF_TOO_LARGE")
```

- [ ] **Step 2: Run tests — expect FAIL** (`expand_prompt` missing)

- [ ] **Step 3: Implement template + `prompt.py`**

Template file `knowledge-compile-v1.txt` (UTF-8). Placeholders must be exactly `{{subject}}`, `{{goal}}`, `{{topic_slug}}`:

```text
You are compiling a Knowledge Core authoring request for a children's learning topic.

Topic slug (must appear in topic.slug): {{topic_slug}}
Learning object: {{subject}}
Learning goal: {{goal}}

Output ONE JSON object only, schema "cognitive-card-authoring-request-v1".
You may wrap it in a single ```json fence. Do not output a second JSON object.

Rules:
- Claims are age-neutral. Do not write four-card slots, COPY, font size, or page layout.
- Set "projection": {}.
- Use web search to find institutional pages. Each source must include locator, intake.method=search, intake.query, intake.tool, and retrieved_at. Do not invent locators. Do not use a search snippet as canonical_claim without a Source record.
- Default entity mammal coverage: every required coverage_facet (recognition, appearance, physical_features, habits, environment, safety, care) has sourced propositions or an explicit unresolved gap.
- excluded_questions must contain at least one item.
- topic.revision is 1.

Return only the authoring JSON.
```

`prompt.py`:

```python
from pathlib import Path

from cognitive_card_server.knowledge_contract.model import (
    KnowledgeContractError,
    sha256_hex,
)

TEMPLATE_ID = "knowledge-compile-v1"
SUBJECT_MAX = 200
GOAL_MAX_BYTES = 2048
_SLUG = __import__("re").compile(r"^[a-z][a-z0-9-]{2,63}$")


def template_path() -> Path:
    return Path(__file__).resolve().parent / "templates" / f"{TEMPLATE_ID}.txt"


def template_sha256() -> str:
    return "sha256:" + sha256_hex(template_path().read_bytes())


def expand_prompt(*, subject: str, goal: str, topic_slug: str) -> str:
    if not isinstance(subject, str) or not subject.strip():
        raise KnowledgeContractError("COMPILE_BRIEF_TOO_LARGE", "subject")
    if len(subject) > SUBJECT_MAX:
        raise KnowledgeContractError("COMPILE_BRIEF_TOO_LARGE", "subject")
    if not isinstance(goal, str) or not goal.strip():
        raise KnowledgeContractError("COMPILE_BRIEF_TOO_LARGE", "goal")
    if len(goal.encode("utf-8")) > GOAL_MAX_BYTES:
        raise KnowledgeContractError("COMPILE_BRIEF_TOO_LARGE", "goal")
    if not isinstance(topic_slug, str) or _SLUG.fullmatch(topic_slug) is None:
        raise KnowledgeContractError("COMPILE_SLUG_INVALID", "topic_slug")
    template = template_path().read_text(encoding="utf-8")
    return (
        template.replace("{{subject}}", subject.strip())
        .replace("{{goal}}", goal.strip())
        .replace("{{topic_slug}}", topic_slug)
    )
```

`__init__.py` can be empty until Task 2 re-exports pipeline functions.

- [ ] **Step 4: Re-run PromptExpandTests — expect PASS**

---

### Task 2: Intent store, reply compile, confirm

**Files:**
- Create: `src/cognitive_card_server/knowledge_compile/store.py`
- Create: `src/cognitive_card_server/knowledge_compile/parse.py`
- Create: `src/cognitive_card_server/knowledge_compile/pipeline.py`
- Modify: `src/cognitive_card_server/coverage/accuracy.py` (`apply_accuracy_kernel` grows `*, allow_search: bool = False`)
- Modify: `src/cognitive_card_server/knowledge_contract/authoring.py` (`compile_authoring_request` grows `*, allow_search: bool = False` and passes it to `apply_accuracy_kernel`)
- Modify: `src/cognitive_card_server/knowledge_compile/__init__.py` (export pipeline)
- Modify: `tests/test_knowledge_compile.py` (add classes below)

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile -v` → all pass
Also run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_coverage_compile tests.test_coverage_host -v`. CLI search must still fail.

**Depends on:** Task 1

**Interfaces:**
- Consumes: `expand_prompt`, `template_sha256`, `TEMPLATE_ID`, `KnowledgeLibrary.publish`, `compile_authoring_request`
- Produces:

```python
FORBIDDEN_SLUGS = frozenset({"spider-gwen"})
RESERVED_ACTORS = frozenset({"qa-01-v1", "publish-01-v1", "machine"})
REPLY_MAX_BYTES = 256 * 1024
INTENT_SCHEMA = "cognitive-card-compile-intent-v1"

def create_intent(
    *,
    library: KnowledgeLibrary,
    compile_root: Path,
    topic_slug: str,
    subject: str,
    goal: str,
    actor: str,
    now: datetime,
    idempotency_key: str | None = None,
) -> dict[str, object]:
    """State open. Returns intent dict including expanded_prompt."""

def submit_reply(
    *,
    library: KnowledgeLibrary,
    compile_root: Path,
    intent_id: str,
    reply: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    """open|failed → compiled or failed. Writes candidate four files. Does not publish."""

def confirm_current(
    *,
    library: KnowledgeLibrary,
    compile_root: Path,
    intent_id: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    """compiled → current via KnowledgeLibrary.publish. Sets intent.state=current and revision."""

def return_intent(*, compile_root: Path, intent_id: str) -> dict[str, object]: ...
def cancel_intent(*, compile_root: Path, intent_id: str) -> dict[str, object]: ...
def load_intent(compile_root: Path, intent_id: str) -> dict[str, object]: ...

def parse_authoring_reply(reply: str) -> dict[str, object]:
    """One JSON object; optional single ```json fence. Else COMPILE_REPLY_INVALID."""
```

`allow_search` implementation in `apply_accuracy_kernel`:

```python
enabled_methods = _enabled_intake_methods(catalog)
if allow_search:
    enabled_methods = set(enabled_methods)
    enabled_methods.add("search")
```

Do **not** edit `source-intake-search.v1.json`.

`submit_reply` must, before `compile_authoring_request`:
1. `request = parse_authoring_reply(reply)`
2. If `request["topic"]["slug"] != intent["topic_slug"]` → `COMPILE_REPLY_INVALID`
3. `request["projection"] = {}` (drop any family/slots from the model)
4. `request["topic"]["slug"] = intent["topic_slug"]` already matched
5. `compile_authoring_request(request, allow_search=True)`
6. For each source with `intake.method == "search"`, require `intake.query` and `intake.tool` strings; missing → `COMPILE_REPLY_INVALID` (or `CORE_ACCURACY_GAP` if you prefer one code; spec lists both — use `COMPILE_REPLY_INVALID` for missing query/tool, kernel for unsourced claims)
7. Write four JSON files under `compile_root / intent_id / candidate/` using `canonical_json`
8. Set state `compiled`. Do not call `library.publish`.

`create_intent` slug gates:
- `spider-gwen` → `COMPILE_SLUG_FORBIDDEN`
- `library.get_current(slug, now=now)` not None → `COMPILE_SLUG_EXISTS`
- any non-terminal intent with same slug under `compile_root` → `COMPILE_INTENT_ACTIVE`
- actor in `RESERVED_ACTORS` or empty → `COMPILE_UNAUTHORIZED`

Intent id: `"ci_" + secrets.token_hex(16)`.

Storage: `compile_root / intent_id / intent.json` (atomic replace via temp file in the same directory). Candidate dir deleted on retry (`submit_reply` from `failed`, or `return_intent`).

`confirm_current` loads candidate files into `KnowledgeBundle` via `load_package` / `bundle_from_documents` (use the same helper HTTP publish uses — `bundle_from_documents` in `knowledge_library.store` if that is how `/admin/knowledge-library/publish` works; otherwise `load_package(candidate_dir)`). Then `library.publish(bundle, now=now)`.

If candidate missing or state != `compiled` → `COMPILE_NOT_COMPILED`. If state == `current` → `COMPILE_ALREADY_CURRENT`. If `library.get_current(slug)` now exists → `COMPILE_SLUG_EXISTS`.

- [ ] **Step 1: Write failing tests** (append to `tests/test_knowledge_compile.py`)

Use a helper that starts from `examples/authoring/rabbit-real.json`:

```python
def _cat_reply() -> dict[str, object]:
    request = json.loads(
        (REPO_ROOT / "examples" / "authoring" / "rabbit-real.json").read_text(
            encoding="utf-8"
        )
    )
    request["topic"]["slug"] = "cat"
    request["topic"]["title"] = "猫：身体、生活与照护"
    request["identity"]["names"] = {
        "cn": "猫",
        "en": "cat",
        "scientific": "Felis catus",
    }
    request["projection"] = {}
    for source in request["sources"]:
        source["intake"] = {
            "method": "search",
            "query": "cat physical characteristics veterinary",
            "tool": "chatgpt-web-search",
            "captured_at": source["intake"]["captured_at"],
        }
    return request


def _compile_root(temp: tempfile.TemporaryDirectory) -> Path:
    root = Path(temp.name)
    return root / "compile-intents"


class IntentPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.library = KnowledgeLibrary(Path(self.temp.name) / "library")
        self.compile_root = _compile_root(self.temp)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_create_expand_and_slug_gates(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import create_intent

        created = create_intent(
            library=self.library,
            compile_root=self.compile_root,
            topic_slug="cat",
            subject="家猫",
            goal="认识猫",
            actor="owner",
            now=NOW,
        )
        self.assertEqual(created["state"], "open")
        self.assertIn("家猫", created["expanded_prompt"])
        with self.assertRaises(KnowledgeContractError) as ctx:
            create_intent(
                library=self.library,
                compile_root=self.compile_root,
                topic_slug="spider-gwen",
                subject="格温",
                goal="认识格温",
                actor="owner",
                now=NOW,
            )
        self.assertEqual(ctx.exception.code, "COMPILE_SLUG_FORBIDDEN")

    def test_reply_compiled_then_confirm(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            confirm_current,
            create_intent,
            submit_reply,
        )

        created = create_intent(
            library=self.library,
            compile_root=self.compile_root,
            topic_slug="cat",
            subject="家猫",
            goal="认识猫",
            actor="owner",
            now=NOW,
        )
        fenced = "```json\n" + json.dumps(_cat_reply(), ensure_ascii=False) + "\n```\n"
        compiled = submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=fenced,
            actor="owner",
            now=NOW,
        )
        self.assertEqual(compiled["state"], "compiled")
        self.assertIsNone(self.library.get_current("cat", now=NOW))
        confirmed = confirm_current(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            actor="owner",
            now=NOW,
        )
        self.assertEqual(confirmed["state"], "current")
        current = self.library.get_current("cat", now=NOW)
        self.assertIsNotNone(current)
        mapping = self.library.get_mapping("cat")
        self.assertIsNone(mapping)

    def test_invalid_reply_failed_retry(self) -> None:
        from cognitive_card_server.knowledge_compile.pipeline import (
            create_intent,
            submit_reply,
        )

        created = create_intent(
            library=self.library,
            compile_root=self.compile_root,
            topic_slug="cat",
            subject="家猫",
            goal="认识猫",
            actor="owner",
            now=NOW,
        )
        failed = submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply="not json",
            actor="owner",
            now=NOW,
        )
        self.assertEqual(failed["state"], "failed")
        again = submit_reply(
            library=self.library,
            compile_root=self.compile_root,
            intent_id=created["intent_id"],
            reply=json.dumps(_cat_reply(), ensure_ascii=False),
            actor="owner",
            now=NOW,
        )
        self.assertEqual(again["state"], "compiled")

    def test_cli_authoring_still_rejects_search(self) -> None:
        from cognitive_card_server.knowledge_contract.authoring import (
            compile_authoring_request,
        )

        with self.assertRaises(KnowledgeContractError) as ctx:
            compile_authoring_request(_cat_reply())
        self.assertEqual(ctx.exception.code, "INTAKE_METHOD_DISABLED")
```

Also add `test_existing_current_slug` that `library.publish(_rabbit_bundle())` then `create_intent(..., topic_slug="rabbit")` → `COMPILE_SLUG_EXISTS`. Reuse `compile_authoring_request` on unmodified rabbit-real (manual intake) for that publish.

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement parse/store/pipeline + `allow_search`**

`parse.py` algorithm:
- Strip; if starts with ` ``` ` find first fence, take inner until closing fence; reject if another `{` JSON object remains outside after strip.
- `json.loads`; must be `dict`.
- Size: `len(reply.encode("utf-8")) > REPLY_MAX_BYTES` → `COMPILE_REPLY_TOO_LARGE` in `submit_reply` before parse.

`submit_reply` on `KnowledgeContractError` from compile: set state `failed`, store `error` code on intent, return intent dict (do not raise to HTTP as 500). Pipeline **does** raise for `COMPILE_NO_INTENT` / `COMPILE_REPLY_TOO_LARGE` / wrong state (`compiled` cannot reply until return). Invalid JSON: catch, set `failed` + `COMPILE_REPLY_INVALID`.

- [ ] **Step 4: Re-run `tests.test_knowledge_compile` — expect PASS** including CLI search still disabled

---

## Phase 2: HTTP and ops pages

### Task 3: Admin HTTP

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/http/app.py` (`PROTECTED_ROUTES`)
- Modify: `src/cognitive_card_server/http/errors.py` (`_CONFLICT_CODES` / `_NOT_FOUND_CODES`)
- Test: `tests/test_http_knowledge_compile.py`

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_compile tests.test_http_knowledge_ops -v` → all pass
**Depends on:** Task 2

**Interfaces:**
- Consumes: pipeline functions from Task 2
- Produces: routes under `/card-os/api/v1/admin/knowledge-compile`

Add to `_CONFLICT_CODES`: `COMPILE_SLUG_EXISTS`, `COMPILE_INTENT_ACTIVE`, `COMPILE_ALREADY_CURRENT`, `COMPILE_SLUG_FORBIDDEN`.
Add to `_NOT_FOUND_CODES`: `COMPILE_NO_INTENT`.

`PROTECTED_ROUTES` (all `Scope.ADMIN`):

| method | pattern suffix |
| --- | --- |
| POST | `/admin/knowledge-compile` |
| GET | `/admin/knowledge-compile/{intent_id}` where intent_id is `ci_[0-9a-f]{32}` |
| POST | `/admin/knowledge-compile/{intent_id}/reply` |
| POST | `/admin/knowledge-compile/{intent_id}/confirm-current` |
| POST | `/admin/knowledge-compile/{intent_id}/return` |
| POST | `/admin/knowledge-compile/{intent_id}/cancel` |

`compile_root = settings.candidate_root / "compile-intents"`
`library = knowledge_library(settings)` (already defined)

POST `/` body: `topic_slug`, `subject`, `goal`, `actor`. Optional header `Idempotency-Key` passed through.

GET returns intent; include `preview` (unit count, proposition ids, source titles) only when `state == "compiled"` by reading candidate `knowledge-core.json`.

- [ ] **Step 1: Write `tests/test_http_knowledge_compile.py`**

Mirror `tests/test_http_knowledge_ops.py` setUp (tmp `ApiSettings`, admin/read/submit tokens). Assertions:

1. POST without token → not 200.
2. `read` / `submit` token POST compile → 403 `AUTH_SCOPE_REQUIRED` (or existing auth code).
3. Admin POST `{topic_slug:cat, subject, goal, actor:owner}` → 200, `expanded_prompt` present, body/HTML of `GET /card-os/ops/` does not contain `家猫` (that GET is the shell; JSON GET of intent does contain it).
4. Admin POST reply with `_cat_reply()` JSON → `compiled`; GET library current for cat listed false.
5. Admin POST confirm-current `{actor:owner}` → library current exists.
6. Rabbit published via existing publish helper; POST compile rabbit → `COMPILE_SLUG_EXISTS`.

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Wire routes in `attach_ops_routes`** calling pipeline. Do not add executor routes.

- [ ] **Step 4: Re-run HTTP tests plus `tests.test_http_knowledge_ops` — expect PASS**

---

### Task 4: Ops HTML copy/paste

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Modify: `src/cognitive_card_server/knowledge_ops/http.py` (register `/card-os/ops/compile` and `/card-os/ops/compile/{intent_id}` **before** `/{topic}`)
- Modify: `src/cognitive_card_server/knowledge_ops/__init__.py` if new render helpers are exported
- Modify: `tests/test_http_knowledge_compile.py` (HTML assertions)

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_compile tests.test_http_knowledge_ops -v` → all pass
**Depends on:** Task 3

**Interfaces:**
- Consumes: same admin JSON
- Produces: `render_compile_html()`, `render_compile_intent_html(intent_id)`

Rules:
- Initial HTML must not contain `{{subject}}` values, `Merck`, `Felis`, `canonical_claim`, or any expanded prompt text.
- Index `renderList`: add a JS-created link `Compile a topic` → `/card-os/ops/compile` (link text is fine; do not embed briefs).
- Compile page: JS form fields slug/subject/goal/actor; POST admin compile; on success `location = "/card-os/ops/compile/" + intent_id`.
- Intent page: JS GET intent; put `expanded_prompt` into a textarea created at runtime; Copy button; reply textarea; submit reply; if compiled, show preview JSON via `textContent` (not `innerHTML`); Confirm / Return / Cancel buttons.

- [ ] **Step 1: Tests**

```python
def test_compile_shell_has_no_prompt_text(self) -> None:
    page = self.client.get("/card-os/ops/compile")
    self.assertEqual(page.status_code, 200)
    self.assertNotIn("{{subject}}", page.text)
    self.assertNotIn("家猫", page.text)
    self.assertNotIn("cognitive-card-authoring-request-v1", page.text)
    intent_page = self.client.get("/card-os/ops/compile/ci_deadbeef")
    self.assertEqual(intent_page.status_code, 200)
    self.assertNotIn("canonical_claim", intent_page.text)
```

Also: `GET /card-os/ops/compile` must not be handled as topic `compile` (would still 200 HTML, so assert the compile form marker `id="compile-form"` exists, and `GET /card-os/ops/compile/ci_ab` uses `data-intent-id`).

- [ ] **Step 2: Run — expect FAIL** (`/card-os/ops/compile` currently matches `{topic}`)

- [ ] **Step 3: Implement pages + route order**

- [ ] **Step 4: Re-run HTTP ops + compile tests — expect PASS**

---

## Phase 3: Kids ledger

### Task 5: Docs after green tests

**Files:**
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/ai/CURRENT_TASK.md`
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/ai/HANDOFF.md`
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/cognitive-card-os-roadmap.md`
- Modify: `/Users/admin/projects/family/kids-visual-learning-pack/docs/README.md` (plan status)

**Verify:** `bash scripts/ai/check-task-state.sh` PASS; `bash scripts/ai/check-handoff.sh` WARN allowed for 现网未执行; `bash scripts/ai/check-doc-governance.sh` WARN allowed for Last Reviewed; `git diff --check` PASS.

Do **not** mark roadmap `API-01` `DONE`. Record: server worktree implemented, uncommitted, not production, tests listed with counts.

- [ ] **Step 1: Fill HANDOFF from real `git status` and unittest output**
- [ ] **Step 2: Run kids checkers**

---

## Spec coverage

| Spec section | Task |
| --- | --- |
| §5 prompt template + expand | 1 |
| §5 slug gates, actor, idempotency | 2, 3 |
| §6 states / retry | 2 |
| §8 admin-only, no executor token | 3 |
| §9 HTTP | 3 |
| §7 / §8 HTML no embed | 4 |
| §10 parse + allow_search + drop reply projection | 2 |
| §11 confirm publish | 2, 3 |
| §14 cat fixture path, no ChatGPT in tests | 2, 3 |
| §13 no packet salvage | Global Constraints |

## Execution notes

Do not run a live ChatGPT session in this plan. `cat` acceptance in tests is the fenced rabbit-derived reply. Operator live copy/paste is manual after code is green, still against a tmp or explicitly injected library, never KNOW-04 production root unless a later session authorizes it.
