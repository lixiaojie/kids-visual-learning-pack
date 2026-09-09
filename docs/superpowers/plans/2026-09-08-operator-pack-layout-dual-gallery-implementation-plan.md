# Operator Pack Layout Dual Gallery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After compose, the operator selects projection sub-blocks, auto-paginates onto A4 with CN/EN pairing, drags to reorder, refreshes a print sample, locks that layout, and publishes one gallery package with two renderings (scrollable full projection and paginated A4).

**Architecture:** Add a library-side `pack-layout` pointer (same layer as `media-plan.json`, not a fifth governed object). Candidate `pack-work/` holds A4 PNGs, PDF, and selected-only projection HTML. `lock_pack_layout` freezes the draft and QA-approves; `publish_locked_projection` copies those artifacts into the package. Topics with a media-plan pointer can no longer treat `lock_composed_projection` as the shelf lock. Old four-file packages without this pointer stay byte-stable.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, Pillow A4 render, existing compose `page_modules`, `PackageCatalog`, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium-large (5 tasks)

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-08-operator-pack-layout-dual-gallery-design.md` (Approved). Program: FLOW-01; this tranche is PACK-01 only.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1` @ `a0c8081` (plus any uncommitted stegosaurus/compose patches already in that tree — do not revert them).
- Kids repo: `/Users/admin/projects/family/kids-visual-learning-pack`.
- Run tests with `PYTHONPATH=src .venv/bin/python`.
- Do not call OpenAI / image APIs. Do not write Skill claims. Do not read cookies.
- Do not change four-object schema, Confirm current, `lock_mapping`, or Knowledge Core.
- Do not write pack-layout into `revision-NNNN/` four-object directories.
- Do not shrink fonts, crop hero to fit, or split one image across two A4 pages.
- Do not add an Unfreeze button. After lock, the only way to change selection is re-compose (stale) then GET pack for a new draft.
- Do not call `publish_approved` from `lock_pack_layout` or `lock_composed_projection`.
- Do not copy ops full compose HTML or unselected image bytes into the package.
- Do not change the no-media-plan `publish_from_artifact` four-file contract.
- Do not write production knowledge-library or production package catalog. Do not merge/push/release. Do not add `uv.lock` or kids `outputs/`. Do not touch `AGENTS.md`.
- Do not git commit unless the operator asks. Skip every commit step.
- Do not mark FLOW-01 / IMG-03 / PUBLISH-02 / PACK-01 `DONE`.
- Known combined-gate FAIL on ops mapping-lock `LEGEND_ROLE_MISSING` stay untouched. Do not use `rabbit-composite` as the happy-path fixture.
- Drag and auto-pagination are in the contract. Do not ship “delete blocks only” or “gallery = hero band”.
- Sub-block ids must not contain page numbers, coordinates, or random values.

### Combined focused gate (after Task 5)

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_classification_registry tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_http_auth tests.test_knowledge_library_mapping tests.test_knowledge_layout tests.test_http_knowledge_layout tests.test_knowledge_illustration tests.test_http_knowledge_illustration tests.test_knowledge_compose tests.test_http_knowledge_compose tests.test_artifact_pipeline tests.test_four_card_publish tests.test_four_card_portal tests.test_knowledge_pack tests.test_http_knowledge_pack
```

Expected: new tests pass; no-pointer four-file publish tests still pass; the two known `LEGEND_ROLE_MISSING` mapping-lock ops fails remain.

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_pack/ids.py` | Sub-block id parse, `pair_key`, face/page helpers |
| `src/cognitive_card_server/knowledge_pack/catalog.py` | Build selectable catalog from compose modules + chrome slots |
| `src/cognitive_card_server/knowledge_pack/paginate.py` | Deterministic auto-pagination + height estimates |
| `src/cognitive_card_server/knowledge_pack/placement.py` | Drag within FACE; mirror CN/EN `page_index` |
| `src/cognitive_card_server/knowledge_pack/stale.py` | Response-only stale vs current / mapping / media-plan / compose lock |
| `src/cognitive_card_server/knowledge_pack/pipeline.py` | `get_pack`, `patch_pack`, `print_pack_sample`, `lock_pack_layout` |
| `src/cognitive_card_server/knowledge_pack/print_sample.py` | A4 PNG + PDF + `pack_sample_digest` |
| `src/cognitive_card_server/knowledge_pack/projection.py` | Selected-only screen HTML + copy assets by sha |
| `src/cognitive_card_server/knowledge_pack/__init__.py` | Public exports |
| `src/cognitive_card_server/knowledge_library/store.py` | Pointer + revision IO beside media-plan |
| `src/cognitive_card_server/knowledge_compose/pipeline.py` | `lock_composed_projection` → `PACK_LAYOUT_LOCK_REQUIRED` when media-plan pointer exists |
| `src/cognitive_card_server/four_card_artifact/pipeline.py` | `publish_locked_projection` requires frozen pack-layout; pack-work as render input |
| `src/cognitive_card_server/four_card_publish/publish.py` | Numbered cards + projection artifacts; pack digest |
| `src/cognitive_card_server/four_card_portal/gallery.py` | Manifest-path allowlist; A4 default + full-projection switch; thumb `cn-observe-01` |
| `src/cognitive_card_server/knowledge_ops/http.py` | Admin pack routes + `/ops/pack/{topic}` |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Pack HTML; compose「进入排版」 |
| `src/cognitive_card_server/http/app.py` | `PROTECTED_ROUTES` +4 |
| `src/cognitive_card_server/http/errors.py` | 409 for PACK_* except `PACK_UNKNOWN_BLOCK` → 404 |
| `tests/test_knowledge_pack.py` | Catalog, pairing, paginate, placement, lock, publish |
| `tests/test_http_knowledge_pack.py` | HTTP + ops HTML + auth |
| `tests/test_knowledge_compose.py` | Compose lock 409 when pointer |
| `tests/test_artifact_pipeline.py` | Pack publish path; old four-file regression |
| `tests/test_four_card_portal.py` | Dual gallery + old allowlist |
| `tests/test_http_auth.py` | Protected route count +4 |

Kids (Task 5): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`, `docs/cognitive-card-os-system-design.md`.

---

## Shared names (all tasks)

```python
POINTER_SCHEMA = "cognitive-card-knowledge-library-pack-layout-v1"
REVISION_SCHEMA = "cognitive-card-pack-layout-revision-v1"
PAGE_IDS = ("CN_OBS", "EN_OBS", "CN_KNOW", "EN_KNOW")
FACE_OF = {"CN_OBS": "OBS", "EN_OBS": "OBS", "CN_KNOW": "KNOW", "EN_KNOW": "KNOW"}
PAIR_PAGE = {"CN_OBS": "EN_OBS", "EN_OBS": "CN_OBS", "CN_KNOW": "EN_KNOW", "EN_KNOW": "CN_KNOW"}
OBS_PAGES = frozenset({"CN_OBS", "EN_OBS"})
FILE_STEM = {
    "CN_OBS": "cn-observe",
    "EN_OBS": "en-observe",
    "CN_KNOW": "cn-know",
    "EN_KNOW": "en-know",
}

def card_filename(page_id: str, page_index: int) -> str:
    return f"{FILE_STEM[page_id]}-{page_index:02d}.png"

# Every pack pipeline test uses this after `_composed(root)`:
# get_pack(library=library, illustration_root=root/"illus", work_root=root/"work",
#          compose_root=root/"compose", topic_slug="rabbit", now=COMPOSE_NOW)
# print_pack_sample / lock_pack_layout add pack_root=root/"pack-work", actor="owner".
```

Height model (do not shrink fonts):

```python
from cognitive_card_server.four_card_render.pdf import a4_pixels
from cognitive_card_server.four_card_render.render import DPI, SAFE_MARGIN_PX, DEFAULT_FONT_SIZE_PX

A4_W, A4_H = a4_pixels(DPI)
PAGE_CONTENT_PX = A4_H - 2 * SAFE_MARGIN_PX  # ~3224
IMAGE_BLOCK_PX = 720
CHROME_BLOCK_PX = 220
TEXT_LINE_PX = DEFAULT_FONT_SIZE_PX + 24
```

`pack_sample_digest(root: Path) -> str` hashes canonical JSON of sorted `{path, sha256}` for every regular file under `print/` and `projection/` (no symlinks, no `..`). That string is `print_sample_sha256` and, for pack packages, `render_output_sha256`.

Pointer keys (exact set; extra/missing → `LIBRARY_POINTER_INVALID`):

```python
_PACK_POINTER_KEYS = frozenset({
    "schema", "topic_slug", "revision", "status", "identity",
    "compose_content_lock_sha256", "media_plan_revision", "mapping_revision",
    "print_sample_sha256", "source_current_revision", "set_at", "reason",
})
_PACK_REVISION_KEYS = frozenset({
    "schema", "topic_slug", "revision", "status", "selected", "pages",
    "source_compose", "created_at", "actor",
})
```

`pages` on disk:

```json
{
  "CN_OBS": [{"page_index": 1, "block_ids": ["image:hero:CN_OBS", "text:CN_OBS:prop.x"]}],
  "EN_OBS": [{"page_index": 1, "block_ids": ["image:hero:EN_OBS", "text:EN_OBS:prop.x"]}],
  "CN_KNOW": [{"page_index": 1, "block_ids": ["text:CN_KNOW:prop.y"]}],
  "EN_KNOW": [{"page_index": 1, "block_ids": ["text:EN_KNOW:prop.y"]}]
}
```

GET may add `overflow: bool` per page in the **response** only; do not persist overflow on disk.

---

## Phase 1: Catalog, draft, auto-paginate, select

### Task 1: Selectable catalog, pairing, GET draft, PATCH selected

**Files:**
- Create: `src/cognitive_card_server/knowledge_pack/ids.py`
- Create: `src/cognitive_card_server/knowledge_pack/catalog.py`
- Create: `src/cognitive_card_server/knowledge_pack/paginate.py`
- Create: `src/cognitive_card_server/knowledge_pack/stale.py`
- Create: `src/cognitive_card_server/knowledge_pack/pipeline.py`
- Create: `src/cognitive_card_server/knowledge_pack/__init__.py`
- Modify: `src/cognitive_card_server/knowledge_library/store.py` (copy the media-plan pointer/revision pattern at `get_media_plan` / `write_media_plan_pointer`; add `get_pack_layout`, `read_pack_layout_revision`, `write_pack_layout_revision`, `write_pack_layout_pointer`, `next_pack_layout_revision`)
- Test: `tests/test_knowledge_pack.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_pack tests.test_knowledge_layout -v
```

Expected: new tests PASS; media-plan tests still PASS.

**Depends on:** none.

**Interfaces:**
- Consumes: `page_modules`, `load_compose`, `read_meta`, `KnowledgeLibrary.get_current` / `get_mapping` / `get_media_plan`, `require_frozen_media_plan`, `ROLE_ORDER` from `knowledge_compose.chrome`, `PIXEL_VIEW_KEYS`
- Produces:

```python
def pair_key(block_id: str) -> str: ...

def catalog_blocks(*, compose_pages: list[dict[str, object]], record: Mapping[str, object]) -> list[dict[str, str]]:
    """Each item: id, kind, role, pair_key, page_id. Images omitted when png sha empty."""

def auto_paginate(
    selected: list[str],
    catalog: list[dict[str, str]],
    *,
    page_content_px: int = PAGE_CONTENT_PX,
) -> dict[str, list[dict[str, object]]]:
    """Deterministic pages dict. Raises PACK_BLOCK_TOO_LARGE / PACK_UNKNOWN_BLOCK."""

def get_pack(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    work_root: Path,
    compose_root: Path,
    topic_slug: str,
    now: datetime,
    actor: str = "owner",
) -> dict[str, object]:
    """No pointer → create revision-0001 draft, selected=all selectable, auto_paginate. Existing pointer → do not recreate."""

def patch_pack(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    work_root: Path,
    compose_root: Path,
    topic_slug: str,
    actor: str,
    now: datetime,
    selected: list[str] | None = None,
    placement: dict[str, object] | None = None,
) -> dict[str, object]:
    """Task 1 implements selected only. If both selected and placement: 400 REQUEST_VALIDATION_FAILED at HTTP; here raise PACK_UNKNOWN_BLOCK only for bad ids. Task 2 fills placement."""
```

- [ ] **Step 1: Write failing tests** in `tests/test_knowledge_pack.py`

Reuse compose fixtures from `tests/test_knowledge_compose.py` (`_library`, `_generate`, `_illustrate`, `compose_projection`). Topic slug in those helpers is `rabbit`.

```python
"""Pack-layout catalog, pagination, lock, and publish."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cognitive_card_server.knowledge_compose.pipeline import compose_projection
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError
from cognitive_card_server.knowledge_pack.ids import face_of, pair_key
from cognitive_card_server.knowledge_pack.paginate import auto_paginate, PAGE_CONTENT_PX
from cognitive_card_server.knowledge_pack.pipeline import get_pack, patch_pack
from tests.test_knowledge_compose import COMPOSE_NOW, ComposeProjectionTests


class PackIdTests(unittest.TestCase):
    def test_pair_key_strips_language(self) -> None:
        self.assertEqual("text:OBS:prop.x", pair_key("text:CN_OBS:prop.x"))
        self.assertEqual("text:OBS:prop.x", pair_key("text:EN_OBS:prop.x"))
        self.assertEqual("image:hero:OBS", pair_key("image:hero:CN_OBS"))
        self.assertEqual("image:view:OBS:observe.three_view", pair_key("image:view:EN_OBS:observe.three_view"))
        self.assertEqual("image:node:OBS:prop.x", pair_key("image:node:CN_OBS:prop.x"))
        self.assertEqual("chrome:OBS:record", pair_key("chrome:CN_OBS:record"))
        self.assertEqual("chrome:KNOW:safety", pair_key("chrome:CN_KNOW:safety"))


class PackDraftTests(ComposeProjectionTests):
    def test_get_pack_creates_full_select_draft(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, intent = self._composed(root)
            view = get_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                now=COMPOSE_NOW,
            )
            self.assertEqual("draft", view["status"])
            self.assertFalse(view["stale"])
            self.assertIsNone(view["print_sample_sha256"])
            selected = set(view["selected"])
            self.assertIn("image:hero:CN_OBS", selected)
            self.assertIn("image:hero:EN_OBS", selected)
            self.assertIn("chrome:CN_OBS:record", selected)
            self.assertIn("chrome:CN_KNOW:safety", selected)
            self.assertEqual(len(view["pages"]["CN_OBS"]), len(view["pages"]["EN_OBS"]))
            self.assertEqual(len(view["pages"]["CN_KNOW"]), len(view["pages"]["EN_KNOW"]))
            pointer = library.root / "rabbit" / "pack-layout.json"
            self.assertTrue(pointer.is_file())
            current_before = (library.root / "rabbit" / "current.json").read_bytes()
            get_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                now=COMPOSE_NOW,
            )
            self.assertEqual(current_before, (library.root / "rabbit" / "current.json").read_bytes())
            self.assertEqual(1, view["revision"])

    def test_deselect_mirrors_pair_and_repaginates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            view = get_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                now=COMPOSE_NOW,
            )
            remaining = [bid for bid in view["selected"] if bid != "image:hero:CN_OBS"]
            patched = patch_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                actor="owner",
                now=COMPOSE_NOW,
                selected=remaining,
            )
            self.assertNotIn("image:hero:CN_OBS", patched["selected"])
            self.assertNotIn("image:hero:EN_OBS", patched["selected"])
            self.assertIsNone(patched["print_sample_sha256"])

    def test_empty_observe_face_rejected_on_patch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            view = get_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                now=COMPOSE_NOW,
            )
            know_only = [bid for bid in view["selected"] if face_of(bid) == "KNOW"]
            with self.assertRaises(KnowledgeContractError) as raised:
                patch_pack(
                    library=library,
                    illustration_root=root / "illus",
                    work_root=root / "work",
                    compose_root=root / "compose",
                    topic_slug="rabbit",
                    actor="owner",
                    now=COMPOSE_NOW,
                    selected=know_only,
                )
            self.assertEqual("PACK_FACE_EMPTY", raised.exception.code)

    def test_unknown_block_is_404_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            get_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                now=COMPOSE_NOW,
            )
            with self.assertRaises(KnowledgeContractError) as raised:
                patch_pack(
                    library=library,
                    illustration_root=root / "illus",
                    work_root=root / "work",
                    compose_root=root / "compose",
                    topic_slug="rabbit",
                    actor="owner",
                    now=COMPOSE_NOW,
                    selected=["text:CN_OBS:not-a-real-prop"],
                )
            self.assertEqual("PACK_UNKNOWN_BLOCK", raised.exception.code)

    def test_auto_paginate_continues_when_images_exceed_page(self) -> None:
        catalog = [
            {"id": "image:hero:CN_OBS", "kind": "image", "role": "observe", "pair_key": "image:hero:OBS", "page_id": "CN_OBS"},
            {"id": "image:hero:EN_OBS", "kind": "image", "role": "observe", "pair_key": "image:hero:OBS", "page_id": "EN_OBS"},
            {"id": "image:view:CN_OBS:observe.three_view", "kind": "image", "role": "observe", "pair_key": "image:view:OBS:observe.three_view", "page_id": "CN_OBS"},
            {"id": "image:view:EN_OBS:observe.three_view", "kind": "image", "role": "observe", "pair_key": "image:view:OBS:observe.three_view", "page_id": "EN_OBS"},
            {"id": "text:CN_KNOW:p1", "kind": "text", "role": "observe", "pair_key": "text:KNOW:p1", "page_id": "CN_KNOW"},
            {"id": "text:EN_KNOW:p1", "kind": "text", "role": "observe", "pair_key": "text:KNOW:p1", "page_id": "EN_KNOW"},
        ]
        selected = [row["id"] for row in catalog]
        pages = auto_paginate(selected, catalog, page_content_px=800)
        self.assertGreaterEqual(len(pages["CN_OBS"]), 2)
        self.assertEqual(len(pages["CN_OBS"]), len(pages["EN_OBS"]))
        self.assertEqual(
            [pair_key(b) for b in pages["CN_OBS"][1]["block_ids"]],
            [pair_key(b) for b in pages["EN_OBS"][1]["block_ids"]],
        )


```

Add helper `_composed(self, root: Path) -> tuple[KnowledgeLibrary, dict[str, object]]` on `PackDraftTests` that copies the freeze + illustrate + `compose_projection` sequence from `ComposeProjectionTests.test_lock_composed_projection_approves` in `tests/test_knowledge_compose.py`. Return `(library, intent)`. Do not invent a new topic slug; stay on `rabbit`.

Also add:

```python
def test_block_taller_than_page_raises(self) -> None:
    catalog = [{
        "id": "image:hero:CN_OBS", "kind": "image", "role": "observe",
        "pair_key": "image:hero:OBS", "page_id": "CN_OBS",
    }, {
        "id": "image:hero:EN_OBS", "kind": "image", "role": "observe",
        "pair_key": "image:hero:OBS", "page_id": "EN_OBS",
    }, {
        "id": "text:CN_KNOW:p1", "kind": "text", "role": "observe",
        "pair_key": "text:KNOW:p1", "page_id": "CN_KNOW",
    }, {
        "id": "text:EN_KNOW:p1", "kind": "text", "role": "observe",
        "pair_key": "text:KNOW:p1", "page_id": "EN_KNOW",
    }]
    with self.assertRaises(KnowledgeContractError) as raised:
        auto_paginate([row["id"] for row in catalog], catalog, page_content_px=100)
    self.assertEqual("PACK_BLOCK_TOO_LARGE", raised.exception.code)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: the Verify command above.
Expected: FAIL with `ModuleNotFoundError: knowledge_pack` or `cannot import get_pack`.

- [ ] **Step 3: Implement ids, catalog, paginate, store, get_pack, patch selected**

`ids.py`:

```python
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError

FACE_OF = {"CN_OBS": "OBS", "EN_OBS": "OBS", "CN_KNOW": "KNOW", "EN_KNOW": "KNOW"}
PAGE_IDS = frozenset(FACE_OF)

def parse_block_id(block_id: str) -> dict[str, str]:
    if not isinstance(block_id, str) or not block_id:
        raise KnowledgeContractError("PACK_UNKNOWN_BLOCK", str(block_id))
    parts = block_id.split(":")
    if parts[0] == "text" and len(parts) == 3 and parts[1] in PAGE_IDS:
        return {"kind": "text", "page_id": parts[1], "proposition_id": parts[2]}
    if parts[0] == "image" and len(parts) == 3 and parts[1] == "hero" and parts[2] in PAGE_IDS:
        return {"kind": "image", "subtype": "hero", "page_id": parts[2]}
    if parts[0] == "image" and len(parts) == 4 and parts[1] == "view" and parts[2] in PAGE_IDS:
        return {"kind": "image", "subtype": "view", "page_id": parts[2], "view_key": parts[3]}
    if parts[0] == "image" and len(parts) == 4 and parts[1] == "node" and parts[2] in PAGE_IDS:
        return {"kind": "image", "subtype": "node", "page_id": parts[2], "proposition_id": parts[3]}
    if parts[0] == "chrome" and len(parts) == 3 and parts[1] in PAGE_IDS:
        return {"kind": "chrome", "page_id": parts[1], "slot": parts[2]}
    raise KnowledgeContractError("PACK_UNKNOWN_BLOCK", block_id)

def pair_key(block_id: str) -> str:
    parsed = parse_block_id(block_id)
    face = FACE_OF[parsed["page_id"]]
    if parsed["kind"] == "text":
        return f"text:{face}:{parsed['proposition_id']}"
    if parsed.get("subtype") == "hero":
        return f"image:hero:{face}"
    if parsed.get("subtype") == "view":
        return f"image:view:{face}:{parsed['view_key']}"
    if parsed.get("subtype") == "node":
        return f"image:node:{face}:{parsed['proposition_id']}"
    return f"chrome:{face}:{parsed['slot']}"

def face_of(block_id: str) -> str:
    return FACE_OF[parse_block_id(block_id)["page_id"]]

def swap_page(block_id: str, page_id: str) -> str:
    parsed = parse_block_id(block_id)
    kind = parsed["kind"]
    if kind == "text":
        return f"text:{page_id}:{parsed['proposition_id']}"
    if parsed.get("subtype") == "hero":
        return f"image:hero:{page_id}"
    if parsed.get("subtype") == "view":
        return f"image:view:{page_id}:{parsed['view_key']}"
    if parsed.get("subtype") == "node":
        return f"image:node:{page_id}:{parsed['proposition_id']}"
    return f"chrome:{page_id}:{parsed['slot']}"
```

`catalog.py`: walk `compose` public `pages[].modules` (same structure `load_compose` / `_public` returns). For each OBS module: if `hero` and intent has hero sha → `image:hero:{page_id}`; each view with sha → `image:view:{page_id}:{key}`; each node_image with sha → `image:node:{page_id}:{pid}`; each AGE pid with non-empty language text → `text:{page_id}:{pid}`. After modules, if OBS: add `chrome:{page_id}:record|trace|copy`. If KNOW: add `chrome:{page_id}:uncertainty|safety|source`. Knowledge pages never emit `image:*`. Empty sha → skip image id.

`paginate.py`: estimate height: image=`IMAGE_BLOCK_PX`, chrome=`CHROME_BLOCK_PX`, text=`TEXT_LINE_PX`. Order selected OBS blocks by `ROLE_ORDER`, then within role hero → views → nodes → texts, then chrome record/trace/copy last. KNOW: texts by role, then uncertainty/safety/source last. Place CN first; after placing a CN block on page `k`, place the EN pair-key block on EN page `k` (create empty EN pages if needed). If `height > page_content_px` → `PACK_BLOCK_TOO_LARGE`. If remaining < height, increment `page_index` on **both** paired pages. Chrome reserved: when a chrome slot is selected, subtract `CHROME_BLOCK_PX` from the last page of that face before placing body blocks (do not shrink type).

`stale.py`:

```python
def is_pack_stale(
    *,
    pointer: Mapping[str, object],
    current_identity: Mapping[str, object] | None,
    mapping_revision: int | None,
    media_plan_revision: int | None,
    compose_lock: str | None,
) -> bool:
    if current_identity is None:
        return True
    if pointer.get("identity") not in (None, current_identity):
        return True
    if pointer.get("mapping_revision") not in (None, mapping_revision):
        return True
    if pointer.get("media_plan_revision") not in (None, media_plan_revision):
        return True
    stored_lock = pointer.get("compose_content_lock_sha256")
    if stored_lock not in (None, compose_lock):
        return True
    return False
```

Draft pointers store the identity/lock/revisions **at create time** so later compose/current drift is visible. Frozen pointers store the six-key identity (same as media-plan freeze). GET **must not** rewrite `status` to `stale` on disk.

`get_pack`: require current; require compose (`read_meta` / `load_compose`); if no pack pointer, write revision-0001 with `selected` = all catalog ids, `pages` = `auto_paginate(...)`, pointer status `draft`, `print_sample_sha256` null, `source_current_revision` = current.revision, mapping/media-plan/compose lock filled from today. If pointer exists, read that revision, compute `stale` for the response, return catalog + selected + pages. GET of a draft after compose lock change is stale but still returns the old selected list.

`patch_pack` (selected): require draft and not stale (`PACK_LAYOUT_NOT_DRAFT` / `PACK_LAYOUT_STALE` / `PACK_LAYOUT_NO_DRAFT`). Expand selection: if the body lists a CN id, include/exclude the EN pair (and vice versa). Unknown id → `PACK_UNKNOWN_BLOCK`. After filter, if any of the four faces has zero selected ids → `PACK_FACE_EMPTY`. Re-run `auto_paginate`. Set `print_sample_sha256` null on the pointer (do not delete pack-work files yet; lock must not accept them). `replace=True` on the same draft revision. Append `pack-layout-audit.jsonl`.

Store writes: temp file + `os.replace`; refuse symlink; refuse overwrite frozen revision (`LIBRARY_REVISION_EXISTS` or `PACK_LAYOUT_NOT_DRAFT`).

- [ ] **Step 4: Re-run Task 1 tests**

Expected: PASS.

- [ ] **Step 5: Commit** — skip unless the operator asks.

---

## Phase 2: Drag / placement

### Task 2: PATCH placement (drag)

**Files:**
- Create: `src/cognitive_card_server/knowledge_pack/placement.py`
- Modify: `src/cognitive_card_server/knowledge_pack/pipeline.py` (`patch_pack` placement branch)
- Test: `tests/test_knowledge_pack.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_pack -v
```

**Depends on:** Task 1.

**Interfaces:**
- Consumes: `pair_key`, `swap_page`, `FACE_OF`, `PAIR_PAGE`, `parse_block_id`
- Produces:

```python
def apply_placement(
    pages: dict[str, list[dict[str, object]]],
    *,
    block_id: str,
    target_page_id: str,
    target_page_index: int,
    target_index_in_page: int,
) -> dict[str, list[dict[str, object]]]:
    """Move block_id. Mirror pair to the paired page at the same page_index.
    Cross FACE or image onto KNOW → PACK_CROSS_FACE.
    Missing target page → append empty pages on both paired faces until index exists.
    Does not auto_paginate. Overflow is allowed on disk; print-sample/lock reject it.
    """
```

Placement body (HTTP later):

```json
{
  "actor": "owner",
  "placement": {
    "block_id": "text:CN_OBS:prop.x",
    "page_id": "CN_OBS",
    "page_index": 2,
    "index_in_page": 0
  }
}
```

- [ ] **Step 1: Write failing tests**

```python
class PackPlacementTests(ComposeProjectionTests):
    def test_drag_cn_mirrors_en_page_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            view = get_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                now=COMPOSE_NOW,
            )
            cn_text = next(bid for bid in view["selected"] if bid.startswith("text:CN_OBS:"))
            patched = patch_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                actor="owner",
                now=COMPOSE_NOW,
                placement={
                    "block_id": cn_text,
                    "page_id": "CN_OBS",
                    "page_index": 2,
                    "index_in_page": 0,
                },
            )
            en_text = next(bid for bid in patched["selected"] if pair_key(bid) == pair_key(cn_text) and bid.startswith("text:EN_OBS:"))
            cn_pages = patched["pages"]["CN_OBS"]
            en_pages = patched["pages"]["EN_OBS"]
            self.assertGreaterEqual(len(cn_pages), 2)
            self.assertEqual(len(cn_pages), len(en_pages))
            self.assertIn(cn_text, cn_pages[1]["block_ids"])
            self.assertIn(en_text, en_pages[1]["block_ids"])
            self.assertIsNone(patched["print_sample_sha256"])

    def test_drag_image_to_know_is_cross_face(self) -> None:
        ...
        with self.assertRaises(KnowledgeContractError) as raised:
            patch_pack(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                topic_slug="rabbit",
                actor="owner",
                now=COMPOSE_NOW,
                placement={
                    "block_id": "image:hero:CN_OBS",
                    "page_id": "CN_KNOW",
                    "page_index": 1,
                    "index_in_page": 0,
                },
            )
        self.assertEqual("PACK_CROSS_FACE", raised.exception.code)

    def test_placement_does_not_rerun_full_auto_paginate(self) -> None:
        """After drag to page 2, auto_paginate is not called; the block stays on page_index 2 even if it would fit on page 1."""
```

- [ ] **Step 2: Run tests — expect FAIL** (`placement` ignored or `TypeError`).

- [ ] **Step 3: Implement `apply_placement` and wire `patch_pack`**

Rules:
1. `block_id` must be in `selected` else `PACK_UNKNOWN_BLOCK`.
2. `face_of(block_id)` must equal `FACE_OF[target_page_id]` else `PACK_CROSS_FACE`.
3. `parse_block_id(block_id)["kind"] == "image"` and target KNOW → `PACK_CROSS_FACE`.
4. Remove the block from its current page. If the EN/CN pair exists in selected, remove it from its page too.
5. Ensure both paired faces have a page at `target_page_index` (append `{page_index, block_ids: []}`).
6. Insert CN block at `index_in_page` (clamp to len). Insert EN pair at the same index on the paired page (pad with empty if the pair id is missing from catalog — still occupy page_index).
7. Drop trailing empty pages only if both paired faces would drop the same trailing index; never drop page_index 1.
8. Clear `print_sample_sha256`. Do **not** call `auto_paginate`.
9. Reject frozen/stale the same as selected PATCH.

- [ ] **Step 4: Re-run Task 2 tests — PASS.**

- [ ] **Step 5: Commit** — skip unless asked.

---

## Phase 3: Print sample, lock, compose-lock gate

### Task 3: Print sample, selected projection HTML, `lock_pack_layout`, block `lock_composed_projection`

**Files:**
- Create: `src/cognitive_card_server/knowledge_pack/print_sample.py`
- Create: `src/cognitive_card_server/knowledge_pack/projection.py`
- Modify: `src/cognitive_card_server/knowledge_pack/pipeline.py`
- Modify: `src/cognitive_card_server/knowledge_compose/pipeline.py` (`lock_composed_projection`)
- Modify: `src/cognitive_card_server/knowledge_compose/__init__.py` (export `lock_pack_layout` only if you re-export; prefer pack package)
- Test: `tests/test_knowledge_pack.py`
- Test: `tests/test_knowledge_compose.py`

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_pack tests.test_knowledge_compose tests.test_artifact_pipeline -v
```

**Depends on:** Task 2.

**Interfaces:**
- Consumes: `write_a4_pdf`, `a4_pixels`, `record_review`, `load_compose`, `require_frozen_media_plan`, illustration PNG readers (`read_hero_png` / view / node paths), `page_modules`
- Produces:

```python
def pack_sample_digest(pack_topic_root: Path) -> str:
    """sha256_ref of sorted {path, sha256} for regular files under print/ and projection/."""

def print_pack_sample(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    work_root: Path,
    compose_root: Path,
    pack_root: Path,
    topic_slug: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    """Render A4 PNGs + print.pdf + projection HTML. Write print_sample_sha256. Draft only."""

def lock_pack_layout(
    *,
    library: KnowledgeLibrary,
    illustration_root: Path,
    work_root: Path,
    compose_root: Path,
    pack_root: Path,
    topic_slug: str,
    actor: str,
    now: datetime,
) -> dict[str, object]:
    """Freeze draft, QA approve pack-work/qa. Does not publish_approved. Does not change current.json."""
```

Candidate layout:

```text
{pack_root}/{topic}/print/cards/{stem}-{nn}.png
{pack_root}/{topic}/print/print.pdf
{pack_root}/{topic}/print/layout-report.json
{pack_root}/{topic}/projection/index.html
{pack_root}/{topic}/projection/meta.json
{pack_root}/{topic}/projection/assets/<sha256>.png
{pack_root}/{topic}/qa/qa-report.json
```

HTTP later uses `settings.candidate_root / "pack-work"` as `pack_root`.

- [ ] **Step 1: Write failing tests**

```python
from cognitive_card_server.four_card_render.pdf import a4_pixels
from cognitive_card_server.knowledge_compose.pipeline import lock_composed_projection
from cognitive_card_server.knowledge_pack.pipeline import lock_pack_layout, print_pack_sample

def _pack_args(root: Path, library):
    return dict(
        library=library,
        illustration_root=root / "illus",
        work_root=root / "work",
        compose_root=root / "compose",
        topic_slug="rabbit",
        now=COMPOSE_NOW,
    )

def _lock_args(root: Path, library):
    return dict(**_pack_args(root, library), pack_root=root / "pack-work", actor="owner")


class PackLockTests(ComposeProjectionTests):
    def test_lock_without_sample_is_stale_sample(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            get_pack(**_pack_args(root, library))
            with self.assertRaises(KnowledgeContractError) as raised:
                lock_pack_layout(**_lock_args(root, library))
            self.assertEqual("PACK_PRINT_SAMPLE_STALE", raised.exception.code)

    def test_patch_invalidates_sample(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            view = get_pack(**_pack_args(root, library))
            print_pack_sample(**_lock_args(root, library))
            trimmed = [bid for bid in view["selected"] if bid != "chrome:CN_OBS:copy"]
            patch_pack(**_pack_args(root, library), actor="owner", selected=trimmed)
            with self.assertRaises(KnowledgeContractError) as raised:
                lock_pack_layout(**_lock_args(root, library))
            self.assertEqual("PACK_PRINT_SAMPLE_STALE", raised.exception.code)

    def test_lock_approves_and_leaves_current_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            get_pack(**_pack_args(root, library))
            print_pack_sample(**_lock_args(root, library))
            before = (library.root / "rabbit" / "current.json").read_bytes()
            locked = lock_pack_layout(**_lock_args(root, library))
            self.assertEqual("frozen", locked["status"])
            report = json.loads((root / "pack-work" / "rabbit" / "qa" / "qa-report.json").read_text())
            self.assertEqual("approved", report["status"])
            self.assertEqual(before, (library.root / "rabbit" / "current.json").read_bytes())
            self.assertFalse((root / "package-catalog").exists())
            html = (root / "pack-work" / "rabbit" / "projection" / "index.html").read_text()
            self.assertNotIn("/card-os/ops/compose/", html)

    def test_lock_composed_projection_blocked_when_media_plan_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library, _intent = self._composed(root)
            with self.assertRaises(KnowledgeContractError) as raised:
                lock_composed_projection(
                    library=library,
                    illustration_root=root / "illus",
                    work_root=root / "work",
                    compose_root=root / "compose",
                    topic_slug="rabbit",
                    actor="owner",
                    now=COMPOSE_NOW,
                )
            self.assertEqual("PACK_LAYOUT_LOCK_REQUIRED", raised.exception.code)
```

In `tests/test_knowledge_compose.py`, change any test that currently expects `lock_composed_projection` to return `approved` on a frozen media-plan topic: it must now expect `PACK_LAYOUT_LOCK_REQUIRED`. Do not add a no-pointer `lock_composed_projection` success test: that function already raises `MEDIA_PLAN_NOT_FROZEN` when there is no pointer (`require_frozen_media_plan` is None). No-pointer topics keep `publish_from_artifact` only.

Print geometry tests:

```python
def test_print_sample_writes_numbered_faces(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        library, _intent = self._composed(root)
        get_pack(**_pack_args(root, library))
        print_pack_sample(**_lock_args(root, library))
        png = root / "pack-work" / "rabbit" / "print" / "cards" / "cn-observe-01.png"
        self.assertTrue(png.is_file())
        self.assertTrue((root / "pack-work" / "rabbit" / "print" / "print.pdf").is_file())
        from PIL import Image
        self.assertEqual(Image.open(png).size, a4_pixels(300))
```

Overflow lock: after `get_pack`, PATCH placement so two image blocks share page_index 1, then monkeypatch `PAGE_CONTENT_PX` used by `check_print_geometry` to `IMAGE_BLOCK_PX + 10` (or pass `page_content_px=IMAGE_BLOCK_PX + 10` into `print_pack_sample` for tests). `print_pack_sample` / `lock_pack_layout` must raise `PACK_PRINT_OVERFLOW`. Do not skip this test.

Page-count mismatch: after a valid print sample, rewrite `pack-layouts/revision-0001.json` so `pages["EN_OBS"]` has one fewer page than `CN_OBS`, restore `print_sample_sha256` to the on-disk digest, then `lock_pack_layout` raises `PACK_PAGE_COUNT_MISMATCH`.

- [ ] **Step 2: Run tests — expect FAIL.**

- [ ] **Step 3: Implement print, projection, lock, compose gate**

Print PNG: new Pillow page, background `PALETTE["paper"]`, margin `SAFE_MARGIN_PX`, draw blocks top-to-bottom at **existing** `DEFAULT_FONT_SIZE_PX` (never smaller). Images: contain into `IMAGE_BLOCK_PX` height, preserve aspect, do not enter clear-zone rectangles. If a block extends past `PAGE_CONTENT_PX` or intersects a reserved chrome rect → set overflow in `layout-report.json` and raise `PACK_PRINT_OVERFLOW` from `print_pack_sample` **and** `lock_pack_layout`. Clear-zone hit also raises `RENDER_ASSET_IN_CLEAR_ZONE`. Write `card_filename(page_id, page_index)`. Concatenate pages in order CN_OBS 01..n, EN_OBS 01..n, CN_KNOW 01..n, EN_KNOW 01..n into `print.pdf` via `write_a4_pdf`.

Projection HTML: four sections CN_OBS → EN_OBS → CN_KNOW → EN_KNOW. Reuse module chrome CSS classes from compose, but only modules/sub-blocks in `selected`. Images as `assets/<sha256>.png` relative URLs (copy bytes from illustration intent files). KNOW sections: **no** `<img>`. No ops compose URLs. `meta.json` lists selected ids + compose lock.

`print_pack_sample`: draft + not stale; rewrite print+projection dirs via temp + replace; set pointer `print_sample_sha256` to `pack_sample_digest`.

`lock_pack_layout` (all must hold):
1. Same slug/current/compose/frozen media-plan checks as compose lock (`ILLUS_SLUG_INVALID` / `MAPPING_NO_CURRENT` / `COMPOSE_NO_COMPOSE` / `MEDIA_PLAN_NOT_FROZEN` / `MEDIA_PLAN_STALE` / `COMPOSE_IDENTITY_MISMATCH`).
2. Pointer exists (`PACK_LAYOUT_NO_DRAFT`), status draft (`PACK_LAYOUT_NOT_DRAFT`), not stale (`PACK_LAYOUT_STALE`).
3. `print_sample_sha256` non-null and equals live `pack_sample_digest` (`PACK_PRINT_SAMPLE_STALE`).
4. `layout-report.json` overflow false (`PACK_PRINT_OVERFLOW`).
5. `len(CN_OBS)==len(EN_OBS)` and `len(CN_KNOW)==len(EN_KNOW)` (`PACK_PAGE_COUNT_MISMATCH`).
6. Each face has ≥1 selected block present in pages (`PACK_FACE_EMPTY`).
7. Human actor (`ILLUS_UNAUTHORIZED` / `QA_REVIEW_ACTOR_REQUIRED` — reuse compose `_require_actor`).

Success: write **next** frozen revision (`replace=False`) with same selected/pages; pointer status `frozen`, identity = current six keys, print_sample_sha256 kept; write `pack-work/qa/qa-report.json` with schema `cognitive-card-os-qa-report-v1`, `status=awaiting_review`, `render_output_sha256=print_sample_sha256`, `content_lock_sha256` from locked-record; then `record_review(..., decision="approve")`. Do not publish. Do not write catalog. Do not modify knowledge `current.json`.

Compose gate — first lines of `lock_composed_projection`:

```python
if library.get_media_plan(topic_slug) is not None:
    raise KnowledgeContractError("PACK_LAYOUT_LOCK_REQUIRED", topic_slug)
```

No-pointer topics keep the existing `record_review` path.

- [ ] **Step 4: Re-run Task 3 tests — PASS.** Existing no-pointer artifact tests still PASS.

- [ ] **Step 5: Commit** — skip unless asked.

---

## Phase 4: HTTP and ops

### Task 4: Admin pack API, `/ops/pack/{topic}`, compose button, errors, auth

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Modify: `src/cognitive_card_server/http/app.py`
- Modify: `src/cognitive_card_server/http/errors.py`
- Test: `tests/test_http_knowledge_pack.py` (create)
- Test: `tests/test_http_auth.py`
- Test: `tests/test_http_knowledge_ops.py` (compose HTML「进入排版」)

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_http_knowledge_pack tests.test_http_auth tests.test_http_knowledge_compose tests.test_http_knowledge_ops -v
```

**Depends on:** Task 3.

**Interfaces:**
- HTTP (admin Bearer, existing protocol headers):

| Method | Path | Handler |
| --- | --- | --- |
| GET | `/card-os/api/v1/admin/knowledge-pack/{topic}` | `get_pack` |
| PATCH | `/card-os/api/v1/admin/knowledge-pack/{topic}` | body `{"actor", "selected"? , "placement"?}` |
| POST | `/card-os/api/v1/admin/knowledge-pack/{topic}/print-sample` | `{"actor"}` |
| POST | `/card-os/api/v1/admin/knowledge-pack/{topic}/lock` | `{"actor"}` |
| GET | `/card-os/ops/pack/{topic}` | `render_pack_html(topic)` shell |

`pack_root=settings.candidate_root / "pack-work"`. Publish remains `POST /admin/knowledge-compose/{topic}/publish`.

`PROTECTED_ROUTES`: copy the compose `{topic}` regex (`[a-z][a-z0-9-]{2,63}`), add four entries, `Scope.ADMIN`. Measure `len(PROTECTED_ROUTES)` before editing; expected new length is old + 4. Update any auth test that asserts the exact length.

`errors.py`: add to `_CONFLICT_CODES`: `PACK_LAYOUT_LOCK_REQUIRED`, `PACK_LAYOUT_NO_DRAFT`, `PACK_LAYOUT_NOT_DRAFT`, `PACK_LAYOUT_STALE`, `PACK_PRINT_SAMPLE_STALE`, `PACK_PRINT_OVERFLOW`, `PACK_PAGE_COUNT_MISMATCH`, `PACK_FACE_EMPTY`, `PACK_BLOCK_TOO_LARGE`, `PACK_CROSS_FACE`. Add `PACK_UNKNOWN_BLOCK` to `_NOT_FOUND_CODES`.

- [ ] **Step 1: Write failing HTTP tests** (mirror `tests/test_http_knowledge_layout.py`: TestClient, issue admin token, protocol headers).

Cases:
1. GET pack without token → 401 `AUTH_REQUIRED`.
2. GET pack with token after compose → 200, `status=draft`, selected includes hero.
3. PATCH selected omitting one CN text → EN pair gone; 200.
4. POST lock without print-sample → 409 `PACK_PRINT_SAMPLE_STALE`.
5. POST compose `/lock` with media-plan pointer → 409 `PACK_LAYOUT_LOCK_REQUIRED`.
6. GET `/card-os/ops/pack/rabbit` without token → 200 HTML, body must not contain proposition text, `prop.rabbit`, catalog paths, or Skill claims (same assertion style as layout ops HTML).
7. PATCH unknown block → 404 `PACK_UNKNOWN_BLOCK`.

- [ ] **Step 2: Run tests — expect FAIL** (404 on pack routes).

- [ ] **Step 3: Wire routes and HTML**

Ops pack page (token required to fetch JSON, like compose):
- Left: checkbox tree by legend role; checking a role toggles all current catalog ids under that role then PATCH selected.
- Center: four columns of A4-ratio CSS frames (`width: 210mm` scaled); blocks are `draggable=true`; drop calls PATCH placement; frames with `overflow` from GET get a red overflow bar.
- Buttons: 「刷新印样」→ POST print-sample; 「锁定排版」→ POST lock (disabled in JS when `print_sample_sha256` is null).
- After frozen+approved: show existing「上架画廊」that POSTs compose publish (do not add a second publish route).

Compose page: when media-plan pointer exists and compose exists, replace the `锁定投影` button that POSTs `/knowledge-compose/{topic}/lock` with a link/button **进入排版** → `/card-os/ops/pack/{topic}`. Do not call `lock_composed_projection` from that UI.

Register `/ops/pack/{topic}` **before** `/ops/{topic}` so `pack` is not parsed as a slug. Reject `..` / `/` like other ops pages.

- [ ] **Step 4: Re-run Task 4 tests — PASS.**

- [ ] **Step 5: Commit** — skip unless asked.

---

## Phase 5: Publish package shape and PORTAL

### Task 5: Numbered package, dual gallery, old four-file regression, kids docs

**Files:**
- Modify: `src/cognitive_card_server/four_card_artifact/pipeline.py` (`publish_locked_projection`)
- Modify: `src/cognitive_card_server/four_card_publish/publish.py` (`_assemble_payload`, `_render_output_sha256`)
- Modify: `src/cognitive_card_server/four_card_portal/gallery.py`
- Test: `tests/test_knowledge_pack.py` (publish assertions)
- Test: `tests/test_artifact_pipeline.py`
- Test: `tests/test_four_card_portal.py`
- Kids: `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/README.md`, `docs/cognitive-card-os-roadmap.md`, `docs/cognitive-card-os-system-design.md`

**Verify:** combined focused gate at the top of this plan.

**Depends on:** Task 4.

**Interfaces:**
- Extend `publish_locked_projection` with `pack_root: Path`. HTTP passes `settings.candidate_root / "pack-work"`. Existing compose publish tests that freeze a media-plan **must** be rewritten to `get_pack` → `print_pack_sample` → `lock_pack_layout` → `publish_locked_projection`; they can no longer publish four unnumbered hero-band PNGs for a pointer topic.
- When `library.get_media_plan` is not None:
  1. Require frozen pack-layout, not stale (`PACK_LAYOUT_NO_DRAFT` / `PACK_LAYOUT_NOT_DRAFT` / `PACK_LAYOUT_STALE`).
  2. Require `print_sample_sha256 == pack_sample_digest(pack_work/topic)` (`PACK_PRINT_SAMPLE_STALE`).
  3. Require pack-work `qa-report.json` status `approved` (`PUBLISH_NOT_APPROVED`).
  4. Call `publish_approved(record, pack_work/qa, pack_staging, ...)` where staging contains numbered `cards/`, `print.pdf`, `projection/**`, and a copy of frozen `pack-layout.json`.
  5. Do **not** copy `artifact-work/{topic}/render/cards/cn-observe.png` (unnumbered hero-band files).
- When `get_media_plan` is None, `publish_locked_projection` is unused; `publish_from_artifact` four files unchanged.

`_assemble_payload` / `_render_output_sha256`: if `render_dir/cards` contains `cn-observe-01.png` (or any `{stem}-{nn}.png`), pack mode:
- Include every numbered PNG, `print.pdf`, `projection/index.html`, `projection/assets/*`, `pack-layout.json`.
- Artifact `page` field: `CN_OBS` / `EN_OBS` / `CN_KNOW` / `EN_KNOW` (same page_id for continuation files; distinguish by path).
- `render_output_sha256` = `pack_sample_digest` of that staging tree’s print+projection files (must match frozen `print_sample_sha256`).
- Do **not** write unnumbered `cards/cn-observe.png`.
- Else: existing `PAGE_FILES` loop (old packages).

PORTAL `resolve_artifact`:
1. Reject `..` and absolute paths.
2. Load `manifest.json` artifacts[].path for that revision; allow only those relatives that resolve inside the revision directory.
3. Old packages already declare the seven PUBLISH-01 files in the manifest — they keep working without a hardcoded seven-file set.
4. Keep `ALLOWED_FILES` only as a **fallback if manifest artifacts is missing** so corrupt fixtures still 404 closed; do not use it to block numbered paths.

`render_package_html` / `_card_markup`:
- If `pack-layout.json` exists in the revision (or manifest has `projection/index.html`): default view **A4 投影** — group images by face, ordered `-01`, `-02`, …; link `print.pdf`. Toggle control **完整投影** loads `projection/index.html` in an iframe or inlined object (read-only). No ops URLs.
- Else: existing four `cn-observe.png` figures.
- List thumbnail: if `cards/cn-observe-01.png` exists, use it; else `cards/cn-observe.png`.

`package_detail_payload` `files` array: manifest artifact paths, not hardcoded `ALLOWED_FILES`.

- [ ] **Step 1: Write failing tests**

```python
from cognitive_card_server.four_card_artifact.pipeline import publish_locked_projection

def test_publish_pack_layout_revision_shape(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        library, _intent = self._composed(root)
        get_pack(**_pack_args(root, library))
        print_pack_sample(**_lock_args(root, library))
        lock_pack_layout(**_lock_args(root, library))
        published = publish_locked_projection(
            library=library,
            illustration_root=root / "illus",
            work_root=root / "work",
            compose_root=root / "compose",
            catalog_root=root / "catalog",
            pack_root=root / "pack-work",
            topic_slug="rabbit",
            actor="owner",
            now=COMPOSE_NOW,
        )
        rev = Path(published["directory"])
        self.assertTrue((rev / "cards" / "cn-observe-01.png").is_file())
        self.assertFalse((rev / "cards" / "cn-observe.png").exists())
        self.assertTrue((rev / "projection" / "index.html").is_file())
        self.assertTrue((rev / "pack-layout.json").is_file())
        manifest = json.loads((rev / "manifest.json").read_text())
        paths = {item["path"] for item in manifest["artifacts"]}
        self.assertIn("projection/index.html", paths)
        pointer = json.loads((library.root / "rabbit" / "pack-layout.json").read_text())
        report = json.loads((rev / "qa-report.json").read_text())
        self.assertEqual(report["render_output_sha256"], pointer["print_sample_sha256"])

def test_publish_without_lock_blocked(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        library, _intent = self._composed(root)
        get_pack(**_pack_args(root, library))
        with self.assertRaises(KnowledgeContractError) as raised:
            publish_locked_projection(
                library=library,
                illustration_root=root / "illus",
                work_root=root / "work",
                compose_root=root / "compose",
                catalog_root=root / "catalog",
                pack_root=root / "pack-work",
                topic_slug="rabbit",
                actor="owner",
                now=COMPOSE_NOW,
            )
        self.assertIn(
            raised.exception.code,
            {"PACK_LAYOUT_NOT_DRAFT", "PACK_PRINT_SAMPLE_STALE", "PUBLISH_NOT_APPROVED"},
        )
```

Portal:

```python
def test_pack_package_default_a4_and_switcher(self) -> None:
    # write_gallery_pages on a pack revision
    html = (gallery / "rabbit" / "index.html").read_text()
    self.assertIn("A4", html)
    self.assertIn("完整投影", html)
    self.assertIn("cn-observe-01.png", html)
    self.assertNotIn("/card-os/ops/compose/", html)

def test_old_four_card_package_still_serves_unnumbered_png(self) -> None:
    # existing portal fixture using PAGE_FILES names
    path = resolve_artifact(catalog, slug, 1, "cards/cn-observe.png", viewer=VIEWER_PUBLIC)
    self.assertTrue(path.is_file())
```

- [ ] **Step 2: Run tests — expect FAIL** (publish still copies four hero-band PNGs).

- [ ] **Step 3: Implement assemble + portal + kids docs**

Kids docs only: point PACK-01 at this plan; status remains IN PROGRESS; do not mark DONE; record isolation (`dino-walk.local` only). Do not edit `AGENTS.md`.

- [ ] **Step 4: Combined focused gate** — new tests PASS; two known mapping-lock FAILs remain.

- [ ] **Step 5: Commit** — skip unless asked.

---

## Coverage check (plan vs spec)

| Spec § | Task |
| --- | --- |
| Compose then pack-layout then lock then publish | 3–5 |
| Block = legend module, split image/sentence/chrome | 1 |
| Default select all selectable | 1 |
| CN/EN paired select + same page_index | 1–2 |
| Four-card skeleton + continuation; page counts aligned | 1, 3 |
| Auto paginate then drag | 1–2 |
| HTML preview + 刷新印样; no lock if sample stale | 3–4 |
| Font size never shrinks | 3 |
| Min one block per face; hero optional | 1, 3 |
| Missing PNG not selectable | 1 |
| Two gallery versions, default A4, thumb `cn-observe-01` | 5 |
| Unselected in neither rendering | 3, 5 |
| current.json unchanged | 3 |
| Disk pointer / revision / pack-work | 1, 3 |
| GET create draft; stale response-only | 1 |
| `lock_pack_layout` table of failure codes | 3 |
| `lock_composed_projection` 409 when media-plan pointer | 3–4 |
| Package numbered PNGs + projection + pack-layout.json | 5 |
| PORTAL manifest allowlist; old seven-file packages | 5 |
| HTTP + `/ops/pack` + 进入排版 | 4 |
| Error codes including 404 `PACK_UNKNOWN_BLOCK` | 1, 4 |
| No Unfreeze; no production catalog; no image API | Global |
| Drag not dropped from contract | 2, 4 |
