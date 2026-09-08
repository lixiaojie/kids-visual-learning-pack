# Operator Locked Projection Gallery Publish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After IMG-03 has locked a composed projection (`QA approved`), the operator can explicitly publish it as a PUBLISH-01 package on the local gallery; freeze-bound topics can no longer one-click approve-and-publish.

**Architecture:** Add `publish_locked_projection` next to `publish_from_artifact`. It reuses `require_frozen_media_plan`, compose identity (`load_compose` / `read_meta`), and `publish_approved`. Do not call `record_review`. When a media-plan pointer exists, `publish_from_artifact` and POST `artifact-publish` raise `PUBLISH_LOCKED_PATH_REQUIRED`. Package bytes stay the PUBLISH-01 set. PORTAL-01 is read-only.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, `PackageCatalog`, existing compose/lock helpers, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium (4 tasks)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-07-operator-locked-projection-gallery-publish-design.md` (Approved). Program: `docs/superpowers/specs/2026-09-04-operator-iterative-workflow-design.md` §5.4.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1` @ `629144c`.
- Kids repo: `/Users/admin/projects/family/kids-visual-learning-pack`.
- Run tests with `PYTHONPATH=src .venv/bin/python`.
- Do not call OpenAI / image APIs. Do not write Skill claims.
- Do not call `publish_approved` from `lock_composed_projection`.
- Do not change PUBLISH-01 identity closure or PORTAL-01 allowlist / HTML renderer.
- Do not copy compose HTML, node PNGs, hero sources, intents, media-plan, or Core into the revision directory.
- Do not change `lock_mapping`, Confirm current, or four-object schema.
- Do not write production knowledge-library or production package catalog. Do not merge/push/release. Do not add `uv.lock` or kids `outputs/`.
- Do not git commit unless the operator asks. Skip every commit step.
- Do not mark IMG-03 / COMPOSE-01 / FLOW-01 / GRAPH-01 / FORM-01 / FREEZE-01 / PUBLISH-02 `DONE`.
- Known combined-gate 2 FAIL on ops mapping-lock `LEGEND_ROLE_MISSING` stay untouched. Do not use `rabbit-composite` as the happy-path fixture.
- Real function name is `publish_from_artifact` (IMG-03 prose said `publish_from_work`). Real HTTP is `/admin/knowledge-library/{topic}/artifact-publish`.
- Task 1 accepted exception: `compose_projection` re-runs `run_machine_qa` after overlay. Later tasks must not revert `knowledge_compose/pipeline.py`.

### Combined focused gate (after Task 3)

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_classification_registry tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_http_auth tests.test_knowledge_library_mapping tests.test_knowledge_layout tests.test_http_knowledge_layout tests.test_knowledge_illustration tests.test_http_knowledge_illustration tests.test_knowledge_compose tests.test_http_knowledge_compose tests.test_artifact_pipeline tests.test_four_card_publish
```

Expected: new tests pass; existing no-pointer `publish_from_artifact` tests pass; the two known `LEGEND_ROLE_MISSING` mapping-lock ops fails remain.

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/four_card_artifact/pipeline.py` | `publish_locked_projection`; pointer blocks `publish_from_artifact` |
| `src/cognitive_card_server/four_card_artifact/__init__.py` | Export `publish_locked_projection` |
| `src/cognitive_card_server/knowledge_ops/http.py` | POST compose publish; block artifact-publish; GET artifact `media_plan` |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Compose「上架画廊」; hide「批准并上架」when pointer |
| `src/cognitive_card_server/http/app.py` | `PROTECTED_ROUTES` +1 |
| `src/cognitive_card_server/http/errors.py` | 409 for `PUBLISH_LOCKED_PATH_REQUIRED` and `PUBLISH_NOT_APPROVED` |
| `tests/test_knowledge_compose.py` | Frozen lock-then-publish cases |
| `tests/test_artifact_pipeline.py` | Pointer blocks old publish; no-pointer regression |
| `tests/test_http_knowledge_compose.py` | POST publish, portal list, auth |
| `tests/test_http_knowledge_ops.py` | artifact-publish 409 when pointer; GET `media_plan`; HTML hide |
| `tests/test_http_auth.py` | `PROTECTED_ROUTES` length 59 |

Kids (Task 4): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`, `docs/cognitive-card-os-system-design.md`.

---

## Phase 1: Publish function and old-path gate

### Task 1: `publish_locked_projection` + block `publish_from_artifact`

**Files:**
- Modify: `src/cognitive_card_server/four_card_artifact/pipeline.py`
- Modify: `src/cognitive_card_server/four_card_artifact/__init__.py`
- Test: `tests/test_knowledge_compose.py`
- Test: `tests/test_artifact_pipeline.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose tests.test_artifact_pipeline tests.test_four_card_publish -v
```

Expected: new tests PASS; existing no-pointer `test_approve_and_publish_sets_revision_0001` / `test_second_publish_is_idempotent` still PASS.

**Depends on:** none.

**Interfaces:**
- Consumes: `require_frozen_media_plan`, `load_compose`, `read_meta`, `publish_approved`, `_load_work_record`, `_qa_status`
- Produces:

```python
def publish_locked_projection(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    work_root: Path,
    compose_root: Path,
    catalog_root: Path,
    topic_slug: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    """Publish an already-approved composed projection. Does not record_review."""
```

Return value is `PackageRevision.as_dict()` (`package_slug`, `revision`, `directory`, `identity`, `supersedes`).

- [ ] **Step 1: Write failing tests**

In `tests/test_artifact_pipeline.py`, keep `_publish` **without** `library=` and **without** `get_layout` so no-pointer tests stay green.

Add:

```python
def test_publish_from_artifact_with_media_plan_pointer_is_blocked(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        library = self._library_ready(root)
        from cognitive_card_server.knowledge_layout.pipeline import get_layout
        from tests.test_four_card_converter import NOW as LAYOUT_NOW
        compile_root = root / "compile-intents"
        get_layout(library=library, compile_root=compile_root, topic_slug="rabbit", now=NOW)
        work_root = root / "artifact-work"
        catalog_root = root / "package-catalog"
        self._generate(library, work_root)
        from cognitive_card_server.knowledge_contract.model import KnowledgeContractError
        with self.assertRaises(KnowledgeContractError) as raised:
            publish_from_artifact(
                topic="rabbit",
                actor="owner",
                work_root=work_root,
                catalog_root=catalog_root,
                now=NOW,
                library=library,
            )
        self.assertEqual("PUBLISH_LOCKED_PATH_REQUIRED", raised.exception.code)
        self.assertFalse((catalog_root / "rabbit" / "current.json").exists())
```

In `tests/test_knowledge_compose.py`, import `publish_locked_projection` from `four_card_artifact`. Add helper:

```python
def _publish_locked(self, library, illustration_root, work_root, compose_root, catalog_root, actor="owner"):
    from cognitive_card_server.four_card_artifact import publish_locked_projection
    return publish_locked_projection(
        library=library,
        illustration_root=illustration_root,
        work_root=work_root,
        compose_root=compose_root,
        catalog_root=catalog_root,
        topic_slug="rabbit",
        actor=actor,
        now=COMPOSE_NOW,
    )
```

Tests (reuse `_generate`, `_bound_illustrate`, `_compose`, `_lock`):

```python
def test_publish_locked_draft_pointer_fails(self) -> None:
    # get_layout only (draft); generate+illustrate+compose without freeze
    # assert_code MEDIA_PLAN_NOT_FROZEN on publish_locked_projection
    # catalog has no rabbit/current.json

def test_publish_locked_awaiting_review_fails(self) -> None:
    # bound illustrate + compose, do NOT lock
    # assert_code PUBLISH_NOT_APPROVED
    # catalog empty

def test_publish_locked_without_compose_fails(self) -> None:
    # bound illustrate, no compose
    # assert_code COMPOSE_NO_COMPOSE

def test_publish_locked_stale_after_lock_fails(self) -> None:
    # bound + compose + lock, then library.lock_mapping("rabbit", family="four-card", now=COMPOSE_NOW)
    # assert_code MEDIA_PLAN_STALE
    # catalog empty

def test_publish_locked_writes_publish01_package(self) -> None:
    # bound + compose (hero only, no node PNG) + lock
    current_bytes = (library.root / "rabbit" / "current.json").read_bytes()
    mapping_bytes = (library.root / "rabbit" / "mapping.json").read_bytes()
    result = self._publish_locked(...)
    self.assertEqual("rabbit", result["package_slug"])
    self.assertEqual(1, result["revision"])
    rev = Path(result["directory"])
    self.assertTrue((rev / "cards" / "cn-observe.png").is_file())
    self.assertTrue((rev / "cards" / "en-observe.png").is_file())
    self.assertTrue((rev / "cards" / "cn-know.png").is_file())
    self.assertTrue((rev / "cards" / "en-know.png").is_file())
    self.assertTrue((rev / "print.pdf").is_file())
    self.assertTrue((rev / "manifest.json").is_file())
    self.assertTrue((rev / "qa-report.json").is_file())
    self.assertTrue((rev / "sources.json").is_file())
    names = [p.name for p in rev.rglob("*") if p.is_file()]
    self.assertNotIn("meta.json", names)
    self.assertFalse(any("compose" in str(p) for p in rev.rglob("*")))
    self.assertEqual(current_bytes, (library.root / "rabbit" / "current.json").read_bytes())
    self.assertEqual(mapping_bytes, (library.root / "rabbit" / "mapping.json").read_bytes())
    from cognitive_card_server.four_card_portal.gallery import select_packages, VIEWER_PUBLIC
    from cognitive_card_server.four_card_publish.publish import PackageCatalog
    catalog = PackageCatalog(catalog_root)
    slugs = [row.package_slug for row in select_packages(catalog, viewer=VIEWER_PUBLIC)]
    self.assertIn("rabbit", slugs)

def test_publish_locked_idempotent(self) -> None:
    first = self._publish_locked(...)
    snapshot = (Path(first["directory"]) / "manifest.json").read_bytes()
    second = self._publish_locked(...)
    self.assertEqual(first["revision"], second["revision"])
    self.assertEqual(1, len(list((catalog_root / "rabbit").glob("revision-*"))))
    self.assertEqual(snapshot, (Path(first["directory"]) / "manifest.json").read_bytes())

def test_publish_locked_does_not_record_review_again(self) -> None:
    self._lock(...)
    with patch("cognitive_card_server.four_card_qa.qa.record_review") as review:
        self._publish_locked(...)
        review.assert_not_called()
```

Also assert unfrozen / no-pointer `publish_locked_projection` → `MEDIA_PLAN_NOT_FROZEN`.

- [ ] **Step 2: Run tests to verify they fail**

Expected: `publish_locked_projection` ImportError / not defined; pointer `publish_from_artifact` still publishes (FAIL the new blocked test).

- [ ] **Step 3: Implement**

At the top of `publish_from_artifact`, after resolving `topic_dir`:

```python
    if library is not None and library.get_media_plan(topic) is not None:
        raise KnowledgeContractError("PUBLISH_LOCKED_PATH_REQUIRED", topic)
```

Do not change the no-`library` path.

Add `publish_locked_projection` in the same module:

```python
from datetime import datetime

from cognitive_card_server.knowledge_compose.pipeline import load_compose
from cognitive_card_server.knowledge_compose.store import read_meta
from cognitive_card_server.knowledge_layout.pipeline import require_frozen_media_plan


def publish_locked_projection(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    work_root: Path,
    compose_root: Path,
    catalog_root: Path,
    topic_slug: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    bound = require_frozen_media_plan(
        library=library, topic_slug=topic_slug, now=now
    )
    if bound is None:
        raise KnowledgeContractError("MEDIA_PLAN_NOT_FROZEN", topic_slug)
    try:
        read_meta(compose_root, topic_slug)
        load_compose(
            library=library,
            illustration_root=illustration_root,
            work_root=work_root,
            compose_root=compose_root,
            topic_slug=topic_slug,
            now=now,
        )
    except KnowledgeContractError as error:
        if error.code == "COMPOSE_NO_ARTIFACT":
            raise KnowledgeContractError("COMPOSE_NO_COMPOSE", topic_slug) from error
        raise
    topic_dir = Path(work_root) / topic_slug
    status = _qa_status(topic_dir / "qa" / "qa-report.json")
    if status != "approved":
        raise KnowledgeContractError("PUBLISH_NOT_APPROVED", "status", str(status))
    record = _load_work_record(topic_dir / "record" / "locked-record.json")
    stored = publish_approved(
        record,
        topic_dir / "qa",
        topic_dir / "render",
        catalog_root,
        slug=topic_slug,
        actor=actor,
        now=now,
    )
    return stored.as_dict()
```

Export from `four_card_artifact/__init__.py`.

Do not copy extra files into the catalog; `publish_approved` already writes the PUBLISH-01 set.

- [ ] **Step 4: Re-run Task 1 tests — PASS**

- [ ] **Step 5: Commit** — skip unless the operator asks.

---

## Phase 2: HTTP and ops

### Task 2: Compose POST publish + block artifact-publish HTTP

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/http/app.py`
- Modify: `src/cognitive_card_server/http/errors.py`
- Test: `tests/test_http_knowledge_compose.py`
- Test: `tests/test_http_knowledge_ops.py`
- Test: `tests/test_http_auth.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_compose tests.test_http_knowledge_ops tests.test_http_auth tests.test_artifact_pipeline -v
```

**Depends on:** Task 1.

**Interfaces:**
- Consumes: `publish_locked_projection`
- Produces: POST `/card-os/api/v1/admin/knowledge-compose/{topic}/publish`; GET artifact includes `media_plan: bool` from `library.get_media_plan` (never `get_layout`)

- [ ] **Step 1: Write failing tests**

`tests/test_http_auth.py`:
- Add `("POST", "/card-os/api/v1/admin/knowledge-compose/{topic}/publish", Scope.ADMIN)` to the expected set.
- Change `len(PROTECTED_ROUTES)` from `58` to `59`.

`tests/test_http_knowledge_compose.py`:

```python
PUBLISH_URL = f"{COMPOSE_URL}/rabbit/publish"

def test_publish_without_token_is_not_200(self) -> None:
    denied = self.client.post(PUBLISH_URL, json={"actor": "owner"})
    self.assertEqual(denied.status_code, 401)
    self.assertEqual(denied.json()["error"]["code"], "AUTH_REQUIRED")

def test_publish_before_lock_is_not_approved(self) -> None:
    self._publish_lock_generate()
    self._freeze_wordless()
    self._illustrate()
    self.client.post(COMPOSE_URL, headers=self._auth(self.admin), json={"topic_slug": "rabbit", "actor": "owner"})
    denied = self.client.post(PUBLISH_URL, headers=self._auth(self.admin), json={"actor": "owner"})
    self.assertEqual(denied.status_code, 409)
    self.assertEqual(denied.json()["error"]["code"], "PUBLISH_NOT_APPROVED")
    self.assertFalse(
        (Path(self.settings.candidate_root) / "package-catalog" / "rabbit" / "current.json").exists()
    )

def test_lock_then_publish_lists_on_portal(self) -> None:
    self._publish_lock_generate()
    self._freeze_wordless()
    intent_id = self._illustrate()
    composed = self.client.post(
        COMPOSE_URL,
        headers=self._auth(self.admin),
        json={"topic_slug": "rabbit", "actor": "owner"},
    )
    self.assertEqual(composed.status_code, 200, composed.text)
    locked = self.client.post(
        f"{COMPOSE_URL}/rabbit/lock",
        headers=self._auth(self.admin),
        json={"actor": "owner"},
    )
    self.assertEqual(locked.status_code, 200, locked.text)
    current_path = Path(self.settings.candidate_root) / "knowledge-library" / "rabbit" / "current.json"
    before = current_path.read_bytes()
    listed_before = self.client.get("/card-os/api/v1/portal/packages")
    self.assertEqual(listed_before.status_code, 200)
    slugs_before = [row["package_slug"] for row in listed_before.json()["packages"]]
    self.assertNotIn("rabbit", slugs_before)
    published = self.client.post(
        PUBLISH_URL,
        headers=self._auth(self.admin),
        json={"actor": "owner"},
    )
    self.assertEqual(published.status_code, 200, published.text)
    self.assertEqual("rabbit", published.json()["package_slug"])
    self.assertEqual(1, published.json()["revision"])
    self.assertEqual(before, current_path.read_bytes())
    listed = self.client.get("/card-os/api/v1/portal/packages")
    slugs = [row["package_slug"] for row in listed.json()["packages"]]
    self.assertIn("rabbit", slugs)
    html = self.client.get("/card-os/packages/rabbit")
    self.assertEqual(html.status_code, 200)
    png = self.client.get("/card-os/packages/rabbit/revisions/0001/files/cards/cn-observe.png")
    self.assertEqual(png.status_code, 200)
    disk = (
        Path(self.settings.candidate_root)
        / "package-catalog"
        / "rabbit"
        / "revision-0001"
        / "cards"
        / "cn-observe.png"
    )
    self.assertEqual(png.content, disk.read_bytes())
    missing_compose = self.client.get("/card-os/packages/rabbit/revisions/0001/files/meta.json")
    self.assertNotEqual(missing_compose.status_code, 200)

def test_artifact_publish_with_pointer_is_blocked(self) -> None:
    self._publish_lock_generate()
    self._freeze_wordless()
    blocked = self.client.post(
        f"{LIBRARY}/rabbit/artifact-publish",
        headers=self._auth(self.admin),
        json={"actor": "owner"},
    )
    self.assertEqual(blocked.status_code, 409, blocked.text)
    self.assertEqual(blocked.json()["error"]["code"], "PUBLISH_LOCKED_PATH_REQUIRED")
```

`tests/test_http_knowledge_ops.py`:
- Existing rabbit generate+`artifact-publish` **must still 200** (no layout GET → no pointer).
- Add a test that after GET layout (draft pointer), `artifact-publish` is 409 `PUBLISH_LOCKED_PATH_REQUIRED`.
- GET `/artifact` includes `"media_plan": false` on that no-pointer rabbit; after GET layout, `"media_plan": true`.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement**

`errors.py` `_CONFLICT_CODES` add `"PUBLISH_LOCKED_PATH_REQUIRED"` and `"PUBLISH_NOT_APPROVED"` (spec: 409; actor-empty still uses existing `PUBLISH_ACTOR_REQUIRED` / `QA_REVIEW_ACTOR_REQUIRED` mapping).

`app.py` insert next to the compose lock route:

```python
    _protected_route(
        "POST",
        API_PREFIX + "/admin/knowledge-compose/{topic}/publish",
        re.escape(API_PREFIX)
        + r"/admin/knowledge-compose/[a-z][a-z0-9-]{2,63}/publish",
        Scope.ADMIN,
    ),
```

`http.py` `admin_publish_artifact`: immediately after `_require_slug`, if `knowledge_library(settings).get_media_plan(slug) is not None`, raise `PUBLISH_LOCKED_PATH_REQUIRED`. Do this **before** `_matching_work`.

GET artifact: always set `"media_plan": knowledge_library(settings).get_media_plan(slug) is not None`. Never call `get_layout` here.

New handler next to lock:

```python
    @api_router.post("/admin/knowledge-compose/{topic}/publish")
    def admin_publish_compose(
        topic: str,
        payload: dict[str, object] = Body(...),
        principal: TokenPrincipal = Depends(require_admin),
    ) -> dict[str, object]:
        del principal
        slug = _require_slug(topic)
        actor = payload.get("actor")
        return publish_locked_projection(
            library=knowledge_library(settings),
            illustration_root=_illustration_root(settings),
            work_root=settings.candidate_root / "artifact-work",
            compose_root=_compose_root(settings),
            catalog_root=settings.candidate_root / "package-catalog",
            topic_slug=slug,
            actor=actor if isinstance(actor, str) else "",
            now=clock(),
        )
```

Import `publish_locked_projection` from `four_card_artifact`.

- [ ] **Step 4: Re-run Task 2 tests — PASS**

- [ ] **Step 5: Commit** — skip unless the operator asks.

### Task 3: Ops compose「上架画廊」and hide artifact publish

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Test: `tests/test_http_knowledge_compose.py`
- Test: `tests/test_http_knowledge_ops.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_compose tests.test_http_knowledge_ops tests.test_http_auth -v
```

Then run the combined focused gate in Global Constraints.

**Depends on:** Task 2.

**Interfaces:**
- Consumes: GET artifact `media_plan`; POST compose publish; public `/card-os/packages/{slug}`
- Produces: compose page button/link; artifact fourth panel hides「批准并上架」when `media_plan` is true

- [ ] **Step 1: Write failing tests**

Anonymous compose HTML (`GET /card-os/ops/compose/rabbit` without token):
- Keep: no `canonical_claim`, no `prop.rabbit.`, no filesystem `package-catalog` / `candidate_root` paths.
- Add: `上架画廊` and `已上架` appear in the JS shell (same pattern as existing `锁定投影` / `已锁定`).

Topic detail HTML without token: still contains `批准并上架` in the builder (button is created then removed after token load). After a tokened GET layout, a **tokened** detail page fetch cannot easily execute JS. Instead assert:
- GET artifact JSON `media_plan` is true after layout.
- The detail page JS contains `if (body.media_plan)` (or equivalent) that removes `#artifact-publish`.
- Give the artifact publish button `id="artifact-publish"`.

Compose page JS:
- `renderLockControls`: if `qaStatus === "approved"`, show `已锁定`, then GET `/card-os/api/v1/portal/packages/` + topic; if 200, show `已上架` plus `<a href="/card-os/packages/{topic}">`; else show button `上架画廊` POSTing compose publish with `{actor:"owner"}` then `load()`.
- Do not embed `settings.candidate_root` or `package-catalog` filesystem strings.

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement pages.py**

Artifact builder: `publishBtn.id = "artifact-publish";`

`loadArtifact` success branch:

```javascript
          box.textContent = JSON.stringify(body, null, 2);
          var publishBtn = document.getElementById("artifact-publish");
          if (publishBtn && body.media_plan) {
            publishBtn.remove();
          }
```

Compose `renderLockControls(qaStatus)`: keep awaiting_review lock button. For `approved`:

```javascript
    if (qaStatus === "approved") {
      box.textContent = "已锁定";
      var link = document.createElement("a");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "上架画廊";
      btn.addEventListener("click", function () {
        var out = headers();
        out["Content-Type"] = "application/json";
        fetch("/card-os/api/v1/admin/knowledge-compose/" + encodeURIComponent(topic) + "/publish", {
          method: "POST",
          headers: out,
          body: JSON.stringify({ actor: "owner" })
        }).then(function (response) {
          return response.json().then(function (body) {
            if (!response.ok) {
              show((body.error && body.error.code) || ("HTTP " + response.status));
              return;
            }
            load();
          });
        }).catch(function () { show("Request failed."); });
      });
      fetch("/card-os/api/v1/portal/packages/" + encodeURIComponent(topic), { headers: headers() })
        .then(function (response) {
          if (response.ok) {
            btn.remove();
            link.href = "/card-os/packages/" + encodeURIComponent(topic);
            link.textContent = "已上架";
            box.appendChild(document.createTextNode(" "));
            box.appendChild(link);
            return;
          }
          box.appendChild(document.createTextNode(" "));
          box.appendChild(btn);
        })
        .catch(function () {
          box.appendChild(document.createTextNode(" "));
          box.appendChild(btn);
        });
      panel.insertBefore(box, panel.firstChild);
      return;
    }
```

Do not change mapping-lock third-block markup.

- [ ] **Step 4: Re-run Task 3 tests + combined focused gate**

Expected: new tests PASS; two known `LEGEND_ROLE_MISSING` ops mapping-lock FAILs remain.

- [ ] **Step 5: Commit** — skip unless the operator asks.

---

## Phase 3: Kids ledger

### Task 4: Kids governance docs

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `docs/cognitive-card-os-system-design.md`
- Modify: `docs/README.md`

**Verify (kids repo):**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack && bash scripts/ai/check-task-state.sh && bash scripts/ai/check-handoff.sh && bash scripts/ai/check-doc-governance.sh && git diff --check
```

**Depends on:** Tasks 1–3 (record the actual server SHA only if the operator asked to commit; otherwise record worktree dirty vs `629144c`).

**Interfaces:** none.

- [ ] **Step 1: Roadmap** — PUBLISH-02 `IN PROGRESS` with spec+plan paths; do not mark `DONE`; FLOW-01 still program-not-complete; IMG-03 still `IN PROGRESS`.
- [ ] **Step 2: System design** one bullet: locked projection → `publish_approved`; not identity/PORTAL change; not DONE.
- [ ] **Step 3: CURRENT_TASK / HANDOFF / docs/README** from real `git status` and the commands above.
- [ ] **Step 4: Commit** — skip unless the operator asks.

Do not add `outputs/` or server `uv.lock`.

---

## Self-review

1. **Spec coverage:** §5 old path Task 1–2; §6 function Task 1; §7 package files Task 1; §8 PORTAL list/download Task 2; §9 HTTP Task 2; §10 ops Task 3; §11 new code Task 1–2; §12.1 no-pointer Task 1–2; §12.2 draft Task 1; §12.3 stale Task 1; §12.4 awaiting_review Task 1–2; §12.5–7 package/idempotent/missing node Task 1; §12.8 different identity covered by existing `tests.test_four_card_publish` plus this slice’s idempotent test leaving old bytes; §12.9–11 portal/auth/production Task 2–4; §12.12 pixels not in tests. Kids ledger Task 4.
2. **Placeholder scan:** none.
3. **Type consistency:** `publish_locked_projection` keyword-only; returns `PackageRevision.as_dict()`; HTTP actor string; `media_plan` bool on GET artifact.
