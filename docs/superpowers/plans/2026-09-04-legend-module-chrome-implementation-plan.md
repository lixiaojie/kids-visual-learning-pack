# Legend Module Chrome Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle COMPOSE-01 screen HTML so locked AGE sentences on each four-card page are grouped by `legend_role`, while print PNG bytes stay identical to today's compose re-render.

**Architecture:** Add a pure `page_modules` helper that reads locked-card `proposition_ids` plus `assign_legend`. `_public` attaches `pages[].modules`. Ops compose JS renders modules when present and otherwise keeps the zone stack. `compose_projection` still passes only `CN_OBS:band` / `EN_OBS:band` into `render_locked`.

**Tech Stack:** Python 3 unittest, existing `KnowledgeContractError`, FastAPI admin compose routes, ops HTML/JS.

**Plan size:** Medium (6 tasks, 3 phases)

---

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-04-legend-module-chrome-design.md`
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1`
- Run tests with `PYTHONPATH=src .venv/bin/python`
- Do not change four-object schema, illustration prompt templates, or print image-band geometry
- Do not put extra view PNGs into compose `assets`
- Do not merge/push/release, do not write production library, do not add `uv.lock` or kids `outputs/`
- Do not git commit unless the operator asks
- Known combined-gate 2 FAIL on `_short_authoring()` / rabbit-composite `LEGEND_ROLE_MISSING` stay untouched

### Combined focused gate

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose tests.test_http_knowledge_compose tests.test_knowledge_illustration tests.test_http_knowledge_illustration tests.test_http_knowledge_ops tests.test_http_auth tests.test_projection_legend tests.test_mapping_preview
```

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_compose/chrome.py` | `ROLE_ORDER`, titles, `page_modules` |
| `src/cognitive_card_server/knowledge_compose/pipeline.py` | Attach modules in `_public`; print assets unchanged |
| `src/cognitive_card_server/knowledge_compose/__init__.py` | Export `page_modules` if tests import it |
| `src/cognitive_card_server/knowledge_ops/pages.py` | `_COMPOSE_SCRIPT` module rendering |
| `tests/test_knowledge_compose.py` | Grouping, print sha, extra-view JSON vs assets |
| `tests/test_http_knowledge_compose.py` | HTML shell, KNOW no img, optional three_view |

Kids docs after server tests: spec already Approved; README plan row; roadmap RENDER-02 next action.

---

## Phase 1: Grouping

### Task 1.1: `page_modules` groups AGE lines by role

**Files:**
- Create: `src/cognitive_card_server/knowledge_compose/chrome.py`
- Modify: `src/cognitive_card_server/knowledge_compose/__init__.py`
- Test: `tests/test_knowledge_compose.py` (new class `ComposeChromeTests`)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose.ComposeChromeTests -v` → all pass

**Depends on:** None

**Interface contract:**

```python
ROLE_ORDER = (
    "observe",
    "compare",
    "evidence",
    "time",
    "place",
    "learning_place",
    "habit",
    "kind",
    "sequence",
    "setting",
    "uncertain",
)
PLACE_MARKERS = {"place": "discovery", "learning_place": "learning"}
MODULE_TITLES = {
    "cn": {
        "observe": "外形",
        "compare": "比较",
        "evidence": "证据",
        "time": "时间",
        "place": "发现地",
        "learning_place": "学习地",
        "habit": "习性",
        "kind": "类别",
        "sequence": "步骤",
        "setting": "环境",
        "uncertain": "未知",
    },
    "en": {
        "observe": "Observe",
        "compare": "Compare",
        "evidence": "Evidence",
        "time": "Time",
        "place": "Place",
        "learning_place": "Learning place",
        "habit": "Habits",
        "kind": "Kind",
        "sequence": "Sequence",
        "setting": "Setting",
        "uncertain": "Uncertain",
    },
}

def page_modules(
    *,
    page_id: str,
    zones: dict[str, dict[str, object]],
    fact_by_id: dict[str, dict[str, object]],
    assigned: dict[str, object] | None,
    view_shas: dict[str, str],
) -> list[dict[str, object]]:
    """Return modules for one page. Empty list if assigned is None."""
```

**Key decisions:**
- Content pids: OBS from `look`; KNOW from `appearance` then `uncertainty`. Ignore `record` / `trace` / `copy` / `safety` / `sources`.
- Language: `CN_*` → `cn`, `EN_*` → `en`. Each module `texts` is that language's AGE line per pid, page pid order, skip missing/blank.
- Skip roles with zero pids on this page. Do not emit title-only shells.
- OBS `observe` module is emitted whenever `page_id` is `CN_OBS` or `EN_OBS`, even with empty `texts`, with `hero: True`. KNOW never has `hero: True`.
- Attach `views` only on OBS: `observe.*` extra keys onto `observe`, `setting.*` onto `setting`, and only keys present in `view_shas`. KNOW `views` always `[]`.
- `place` marker `discovery`, `learning_place` marker `learning`. If both modules exist and markers are equal → `LEGEND_PLACE_COLLAPSE`.
- `uncertain` modules get `tone: "uncertain"`; any other role `tone: "fact"`. If role is `uncertain` and tone would be `fact` → `LEGEND_UNCERTAIN_AS_FACT`.

- [ ] **Step 1: Write failing tests**

```python
class ComposeChromeTests(unittest.TestCase):
    def test_empty_time_is_omitted(self) -> None:
        from cognitive_card_server.knowledge_compose.chrome import page_modules

        modules = page_modules(
            page_id="CN_KNOW",
            zones={
                "appearance": {
                    "visible_text": "白毛",
                    "proposition_ids": ["p-obs"],
                },
                "uncertainty": {"visible_text": "", "proposition_ids": []},
                "safety": {"visible_text": "别抓", "proposition_ids": []},
                "sources": {"visible_text": "NHM", "proposition_ids": []},
            },
            fact_by_id={"p-obs": {"cn": "白毛", "en": "White fur"}},
            assigned={"roles": {"observe": ["p-obs"]}, "empty_roles": ["time"]},
            view_shas={},
        )
        roles = [item["role"] for item in modules]
        self.assertEqual(["observe"], roles)
        self.assertNotIn("时间", [item["title"] for item in modules])
        self.assertEqual([], modules[0]["views"])
        self.assertFalse(modules[0]["hero"])

    def test_obs_keeps_hero_without_observe_lines(self) -> None:
        from cognitive_card_server.knowledge_compose.chrome import page_modules

        modules = page_modules(
            page_id="CN_OBS",
            zones={
                "look": {
                    "visible_text": "四条腿",
                    "proposition_ids": ["p-cmp"],
                },
                "record": {"visible_text": "", "proposition_ids": []},
            },
            fact_by_id={"p-cmp": {"cn": "四条腿", "en": "Four legs"}},
            assigned={"roles": {"compare": ["p-cmp"]}},
            view_shas={"observe.three_view": "sha256:" + ("ab" * 32)},
        )
        by_role = {item["role"]: item for item in modules}
        self.assertTrue(by_role["observe"]["hero"])
        self.assertEqual([], by_role["observe"]["texts"])
        self.assertEqual(
            [{"key": "observe.three_view", "png_sha256": "sha256:" + ("ab" * 32)}],
            by_role["observe"]["views"],
        )
        self.assertEqual(["四条腿"], by_role["compare"]["texts"])
        self.assertEqual("比较", by_role["compare"]["title"])

    def test_know_drops_view_shas(self) -> None:
        from cognitive_card_server.knowledge_compose.chrome import page_modules

        modules = page_modules(
            page_id="CN_KNOW",
            zones={
                "appearance": {
                    "visible_text": "草地",
                    "proposition_ids": ["p-set"],
                },
                "uncertainty": {"visible_text": "", "proposition_ids": []},
            },
            fact_by_id={"p-set": {"cn": "草地", "en": "Grass"}},
            assigned={"roles": {"setting": ["p-set"]}},
            view_shas={"setting.in_situ": "sha256:" + ("cd" * 32)},
        )
        self.assertEqual(["setting"], [item["role"] for item in modules])
        self.assertEqual([], modules[0]["views"])
        self.assertFalse(modules[0]["hero"])

    def test_none_assigned_returns_empty(self) -> None:
        from cognitive_card_server.knowledge_compose.chrome import page_modules

        self.assertEqual(
            [],
            page_modules(
                page_id="CN_OBS",
                zones={"look": {"visible_text": "x", "proposition_ids": ["p"]}},
                fact_by_id={"p": {"cn": "x", "en": "x"}},
                assigned=None,
                view_shas={},
            ),
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose.ComposeChromeTests -v`

Expected: FAIL with `ModuleNotFoundError` or `cannot import page_modules`

- [ ] **Step 3: Implement `chrome.py`**

```python
from __future__ import annotations

from typing import Mapping

from cognitive_card_server.knowledge_contract.model import KnowledgeContractError
from cognitive_card_server.knowledge_illustration.views import PIXEL_VIEW_KEYS

OBS_PAGES = frozenset({"CN_OBS", "EN_OBS"})
CONTENT_ZONES = {
    "CN_OBS": ("look",),
    "EN_OBS": ("look",),
    "CN_KNOW": ("appearance", "uncertainty"),
    "EN_KNOW": ("appearance", "uncertainty"),
}
# ROLE_ORDER, PLACE_MARKERS, MODULE_TITLES as in the contract above

def page_modules(...):
    if assigned is None:
        return []
    language = "cn" if page_id.startswith("CN_") else "en"
    titles = MODULE_TITLES[language]
    roles_map = assigned.get("roles") if isinstance(assigned.get("roles"), dict) else {}
    pid_order: list[str] = []
    seen: set[str] = set()
    for zone_id in CONTENT_ZONES.get(page_id, ()):
        zone = zones.get(zone_id) if isinstance(zones, dict) else None
        raw = zone.get("proposition_ids") if isinstance(zone, dict) else None
        if not isinstance(raw, list):
            continue
        for item in raw:
            if isinstance(item, str) and item and item not in seen:
                seen.add(item)
                pid_order.append(item)
    pid_to_role = {}
    for role, ids in roles_map.items():
        if not isinstance(ids, list):
            continue
        for pid in ids:
            if isinstance(pid, str):
                pid_to_role[pid] = role
    grouped: dict[str, list[str]] = {role: [] for role in ROLE_ORDER}
    for pid in pid_order:
        role = pid_to_role.get(pid)
        if role not in grouped:
            continue
        record = fact_by_id.get(pid)
        line = ""
        if isinstance(record, dict):
            line = str(record.get(language) or "")
        if line:
            grouped[role].append(line)
    is_obs = page_id in OBS_PAGES
    modules: list[dict[str, object]] = []
    markers: dict[str, str] = {}
    for role in ROLE_ORDER:
        texts = grouped[role]
        hero = bool(is_obs and role == "observe")
        if not texts and not hero:
            continue
        if role == "uncertain":
            tone = "uncertain"
        else:
            tone = "fact"
        if role == "uncertain" and tone != "uncertain":
            raise KnowledgeContractError("LEGEND_UNCERTAIN_AS_FACT", role)
        views: list[dict[str, str]] = []
        if is_obs:
            for key in PIXEL_VIEW_KEYS:
                if not key.startswith(role + "."):
                    continue
                sha = view_shas.get(key)
                if isinstance(sha, str) and sha:
                    views.append({"key": key, "png_sha256": sha})
        marker = PLACE_MARKERS.get(role)
        if marker:
            markers[role] = marker
        modules.append(
            {
                "role": role,
                "title": titles[role],
                "texts": texts,
                "hero": hero,
                "views": views,
                "tone": tone,
                "marker": marker,
            }
        )
    if "place" in markers and "learning_place" in markers:
        if markers["place"] == markers["learning_place"]:
            raise KnowledgeContractError("LEGEND_PLACE_COLLAPSE", "place")
    return modules
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose.ComposeChromeTests -v`

Expected: PASS

- [ ] **Step 5: Do not commit unless the operator asks**

---

## Phase 2: Compose JSON (depends on Phase 1)

### Task 2.1: `_public` attaches `pages[].modules`

**Files:**
- Modify: `src/cognitive_card_server/knowledge_compose/pipeline.py`
- Test: `tests/test_knowledge_compose.py`

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose.ComposeProjectionTests.test_compose_writes_pages_and_keeps_knowledge_pngs tests.test_knowledge_compose.ComposeProjectionTests.test_rabbit_modules_omit_time tests.test_knowledge_compose.ComposeProjectionTests.test_assign_legend_failure_omits_modules -v` → all pass

**Depends on:** Task 1.1

Change `_require_inputs` to also return `core` (`current.knowledge_core` from `library.get_current`). Thread `core` into `_public`.

```python
from cognitive_card_server.knowledge_compose.chrome import page_modules
from cognitive_card_server.projection_legend import assign_legend

def _view_shas(intent: Mapping[str, object]) -> dict[str, str]:
    raw = intent.get("views")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key, slot in raw.items():
        if not isinstance(key, str) or not isinstance(slot, dict):
            continue
        sha = slot.get("png_sha256")
        if isinstance(sha, str) and sha:
            out[key] = sha
    return out

def _assigned(core: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(core, dict):
        return None
    try:
        return assign_legend(core)
    except KnowledgeContractError:
        return None

def _fact_index(record: Mapping[str, object]) -> dict[str, dict[str, object]]:
    fact = record.get("fact")
    propositions = fact.get("propositions") if isinstance(fact, dict) else None
    index: dict[str, dict[str, object]] = {}
    if not isinstance(propositions, list):
        return index
    for item in propositions:
        if not isinstance(item, dict):
            continue
        pid = item.get("proposition_id")
        if isinstance(pid, str) and pid:
            index[pid] = item
    return index

def _card_zones(record: Mapping[str, object], page_id: str) -> dict[str, dict[str, object]]:
    cards = record.get("cards")
    page = cards.get(page_id) if isinstance(cards, dict) else None
    zones = page.get("zones") if isinstance(page, dict) else None
    return zones if isinstance(zones, dict) else {}
```

In `_public`, after building each page's `zones` list:

```python
assigned = _assigned(core)
fact_by_id = _fact_index(record)
view_shas = _view_shas(intent)
modules = page_modules(
    page_id=page_id,
    zones=_card_zones(record, page_id),
    fact_by_id=fact_by_id,
    assigned=assigned,
    view_shas=view_shas,
)
page_payload = {
    "page": page_id,
    "has_hero": page_id in OBS_PAGES,
    "zones": zones,
    "modules": modules,
}
```

- [ ] **Step 1: Write failing tests on rabbit compose**

```python
    def test_rabbit_modules_omit_time(self) -> None:
        # same setup as test_compose_writes_pages_and_keeps_knowledge_pngs
        result = self._compose(...)
        obs_roles = [item["role"] for item in result["pages"][0]["modules"]]
        know_roles = [item["role"] for item in result["pages"][2]["modules"]]
        self.assertNotIn("time", obs_roles)
        self.assertNotIn("time", know_roles)
        self.assertTrue(any(item["hero"] for item in result["pages"][0]["modules"] if item["role"] == "observe"))
        self.assertFalse(any(item.get("hero") for item in result["pages"][2]["modules"]))
        self.assertTrue(all(item["views"] == [] for item in result["pages"][2]["modules"]))

    def test_assign_legend_failure_omits_modules(self) -> None:
        from unittest.mock import patch
        with patch(
            "cognitive_card_server.knowledge_compose.pipeline.assign_legend",
            side_effect=KnowledgeContractError("LEGEND_ROLE_MISSING", "legend_role"),
        ):
            result = self._compose(...)
        for page in result["pages"]:
            self.assertEqual([], page["modules"])
```

- [ ] **Step 2: Run to see FAIL** (pages lack `modules`)

- [ ] **Step 3: Wire `_public` as above.** `compose_projection` / `load_compose` must pass `core`.

- [ ] **Step 4: Tests PASS.** Existing `test_compose_writes_pages_and_keeps_knowledge_pngs` still PASS.

- [ ] **Step 5: Do not commit unless asked**

### Task 2.2: Print path still hero-only

**Files:**
- Modify: `tests/test_knowledge_compose.py` only, unless `compose_projection` accidentally reads `views/` (it must not)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose.ComposeProjectionTests.test_compose_ignores_extra_view_png tests.test_knowledge_compose.ComposeProjectionTests.test_modules_see_extra_sha_print_does_not -v` → all pass

**Depends on:** Task 2.1

`compose_projection` must keep:

```python
assets = {"CN_OBS:band": hero, "EN_OBS:band": hero}
render_locked(record, render_dir, assets=assets)
```

Extend the extra-view test: JSON `modules` may list `observe.three_view` when meta `views` has sha, but `render_locked` `assets` keys stay exactly those two band keys.

Use `submit_view_image` after `illustrated` rather than writing a raw file, so intent `views` sha is real:

```python
    def test_modules_see_extra_sha_print_does_not(self) -> None:
        from cognitive_card_server.knowledge_illustration.pipeline import submit_view_image

        # generate + illustrate rabbit
        illustrated = self._illustrate(...)
        extra = _png_variant(b"observe.three_view-not-hero")
        submit_view_image(
            library=library,
            illustration_root=illustration_root,
            intent_id=str(illustrated["intent_id"]),
            view_key="observe.three_view",
            image_bytes=extra,
            content_type="image/png",
            actor="owner",
            now=COMPOSE_NOW,
        )
        captured = {}
        def _capture(record, render_dir, assets=None):
            captured["assets"] = dict(assets or {})
            return render_locked(record, render_dir, assets=assets)
        with patch("cognitive_card_server.knowledge_compose.pipeline.render_locked", side_effect=_capture):
            result = self._compose(...)
        self.assertEqual(set(captured["assets"]), {"CN_OBS:band", "EN_OBS:band"})
        obs = result["pages"][0]
        observe = next(item for item in obs["modules"] if item["role"] == "observe")
        self.assertEqual("observe.three_view", observe["views"][0]["key"])
        know = result["pages"][2]
        self.assertTrue(all(item["views"] == [] for item in know["modules"]))
```

If rabbit `allowed_view_keys` lacks `observe.three_view`, skip upload and instead patch `_view_shas` in this test only after confirming `allowed_view_keys(_rabbit_real()["knowledge_core"])` in a one-line debug. Rabbit has `observe` instances, so the three observe extra keys should be allowed.

Keep `test_compose_ignores_extra_view_png` green: print still ignores a raw `views/` file that is **not** in intent meta. That file must not appear in `assets`. JSON `views` on modules should be empty in that test because meta has no sha.

- [ ] **Step 1: Write `test_modules_see_extra_sha_print_does_not`**

- [ ] **Step 2: FAIL if `_public` does not read intent view shas**

- [ ] **Step 3: Implement `_view_shas(intent)` only; do not change `assets`**

- [ ] **Step 4: Both extra-view tests PASS; knowledge PNG bytes still unchanged**

- [ ] **Step 5: Do not commit unless asked**

---

## Phase 3: Ops HTML (depends on Phase 2)

### Task 3.1: Compose page renders modules

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py` (`_COMPOSE_SCRIPT`, optional extra CSS in `render_compose_html`)

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_compose.HttpKnowledgeComposeTests.test_compose_then_get_and_anonymous_html_has_no_lock_text -v` → PASS

**Depends on:** Task 2.1

Replace the per-page body of `renderCompose` so:

1. If `page.modules && page.modules.length`, render each module as `<article data-legend-role>` with `h3` from `mod.title`, `p` per `mod.texts`, class `legend-module` plus `legend-uncertain` when `mod.tone === "uncertain"`, plus `data-marker` when `mod.marker` is set.
2. `img.hero` only when `mod.hero` is true (not `page.has_hero` at section top). Collect those images for the existing hero blob fetch.
3. For each `mod.views[]`, create `<img data-view-key>` and fetch `/card-os/api/v1/admin/knowledge-illustration/{intentId}/views/{key}/image` with the same headers. Revoke object URLs on reload like hero.
4. After modules, still render zones whose `id` is in `record`, `trace`, `copy`, `safety`, `sources` (clear/footer). Do not re-render `look` / `appearance` / `uncertainty` when modules are non-empty.
5. If `modules` is missing or empty, keep today's full zone stack, including `page.has_hero` at the section top.
6. Time module: add `<div class="legend-time"></div>` inside the article. No extra heading if `texts` already carry the locked sentence.
7. KNOW sections must never create `<img>`.

CSS (in the existing `<style>` of `render_compose_html`):

```css
article.legend-module{border:1px solid #c9b99a;margin:0.6rem 0;padding:0.6rem}
article.legend-uncertain{border-style:dashed}
div.legend-time{height:0.6rem;background:linear-gradient(90deg,#c9b99a,#5c6b3a)}
article.legend-module[data-marker="discovery"] h3::before{content:"⌖ "}
article.legend-module[data-marker="learning"] h3::before{content:"📍 "}
```

Do not put AGE sentences or MODULE_TITLES Chinese strings into the unauthenticated shell except as JS property names (`data-legend-role`, `legend-time`). Titles come from JSON.

- [ ] **Step 1: Change `_COMPOSE_SCRIPT` `renderCompose` as specified**

- [ ] **Step 2: Anonymous compose HTML GET still has no rabbit look sentence** (existing test)

- [ ] **Step 3: Do not commit unless asked**

### Task 3.2: HTTP assertions for chrome contract

**Files:**
- Modify: `tests/test_http_knowledge_compose.py`

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_compose -v` → all pass

**Depends on:** Task 3.1, Task 2.2

```python
    def test_anonymous_html_has_no_module_titles_from_json(self) -> None:
        html = self.client.get("/card-os/ops/compose/rabbit")
        self.assertEqual(html.status_code, 200)
        body = html.text
        self.assertNotIn("白毛", body)
        self.assertIn("Token", body)

    def test_modules_and_know_have_no_hero_flag(self) -> None:
        self._publish_lock_generate()
        self._illustrate()
        composed = self.client.post(
            COMPOSE_URL,
            headers=self._auth(self.admin),
            json={"topic_slug": "rabbit", "actor": "owner"},
        )
        self.assertEqual(composed.status_code, 200, composed.text)
        pages = composed.json()["pages"]
        know = pages[2]["modules"]
        self.assertTrue(know)
        self.assertNotIn("time", [item["role"] for item in know])
        self.assertTrue(all(item["hero"] is False for item in know))
        self.assertTrue(all(item["views"] == [] for item in know))
        obs_html_script = self.client.get("/card-os/ops/compose/rabbit").text
        self.assertIn("data-legend-role", obs_html_script)
        self.assertNotIn("src=\"data:", obs_html_script)
```

Add a three_view upload then GET compose: OBS observe module `views` non-empty; KNOW still `[]`.

Existing `test_compose_then_get_and_anonymous_html_has_no_lock_text` must still assert knowledge PNG bytes unchanged.

- [ ] **Step 1: Write the HTTP tests**

- [ ] **Step 2: FAIL if modules missing or KNOW hero true**

- [ ] **Step 3: Fix HTML/JSON until PASS**

- [ ] **Step 4: Combined focused gate.** The two `test_http_knowledge_ops` mapping-lock FAIL remain; do not change `assign_legend` to make them pass.

- [ ] **Step 5: Do not commit unless asked**

### Task 3.3: Kids documentation

**Files:**
- Modify: `docs/README.md` (plan row)
- Modify: `docs/cognitive-card-os-roadmap.md` (RENDER-02 next action points at this plan)
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`

**Verify:** from kids root `bash scripts/ai/check-task-state.sh` → PASS; `bash scripts/ai/check-handoff.sh` → PASS; `git diff --check` → PASS

**Depends on:** Task 3.2

- [ ] **Step 1:** README plans table includes this file as In Progress
- [ ] **Step 2:** Roadmap RENDER-02 next action: implement this plan in the server worktree; do not merge/push/release
- [ ] **Step 3:** CURRENT_TASK acceptance: spec Approved; plan on disk; server not yet implemented until execution
- [ ] **Step 4:** HANDOFF Exact Next Action: execute Task 1.1 in the server worktree
- [ ] **Step 5:** Do not commit unless asked. Do not add `outputs/`

---

## Spec coverage

| Spec | Task |
| --- | --- |
| §4 HTML regroup / print unchanged / same compose path | 2.1, 2.2, 3.1 |
| §5 page-local grouping, OBS hero slot, clear zones not in modules | 1.1, 3.1 |
| §6 IMG prompts untouched; extra PNG by sha only | 2.2, 3.2 |
| §7 role chrome / empty skip / two markers | 1.1, 3.1 |
| §8 GET `modules` shape / unauthenticated shell | 2.1, 3.2 |
| §9 `COMPOSE_ASSET_IN_CLEAR_ZONE` / place collapse / uncertain | 1.1 (JSON); HTML has no KNOW/clear `<img>` in 3.1 |
| §10 acceptance 1–9 | 1.1, 2.1, 2.2, 3.2 |
| No illustration generate path | existing compose tests; do not regress |

## Out of plan

- Illustration / compile prompt changes (IMG)
- Print chrome
- ACCEPT-01 equal split
- Production install, merge, push, release
- Fixing rabbit-composite `LEGEND_ROLE_MISSING`
