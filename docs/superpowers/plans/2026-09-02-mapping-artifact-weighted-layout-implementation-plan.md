# Mapping-Artifact Weighted Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `mapping-artifact-v1` print cards use content-sized zone heights so rabbit-real mapped propositions fit knowledge main zones and observation look, without shrinking type or overflowing into sources.

**Architecture:** Extract one weighted-height allocator used by pack, COPY budget, and RENDER. Knowledge pages flex `appearance`; observation pages flex `look`. ACCEPT-01 equal `stack_layout` and overflow-to-sources stay untouched. COPY stop-append uses remaining height after look min + record band + trace.

**Tech Stack:** Python 3 unittest, Pillow wrap already in `four_card_render.render`, server worktree `knowledge-pipeline-v1`.

**Plan size:** Medium (4 tasks, 2 phases)

## Global Constraints

- Do not edit Knowledge Core bytes, proposition claims, certainty, safety English, or mapping `node_ids`.
- Do not shrink font below 16 pt. Do not overflow propositions into the sources zone.
- Fail closed: after weighted allocation, remaining overflow is `TEXT_OVERFLOW` on the flex zone path (`CN_KNOW.appearance`, `EN_OBS.look`, …).
- `lock_version = mapping-artifact-v1` only. ACCEPT-01 `accept-01-v1` equal four-zone split and `_pack_knowledge_groups` overflow-to-sources stay.
- Pack preview and final RENDER must call the same height function. Do not pack look against empty copy/trace label bands then render with filled COPY.
- `AGE_COPY_SPAN_UNAVAILABLE` only when age-5-6 has no sliceable COPY span in knowledge text. Geometry that stops every extra sentence must not use that code if at least one legal span exists; empty COPY after stop-append is allowed. Look that still cannot fit → `TEXT_OVERFLOW`.
- Do not change four-object schema, v1 FACT keys, AUTHOR-05 defaults, or packet contract.
- Do not git commit, merge server `main`, push, add `uv.lock`, reload Nginx, or install a production release.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core`. Use `.venv/bin/python` with `PYTHONPATH=src`. System `python3` lacks FastAPI and is not required for these tests.
- Snapshot / registry: reuse `SNAPSHOT_ID` / `REGISTRY_COMMIT` from `tests.test_four_card_converter`.
- Do not mark roadmap `WB-03` `DONE` in this plan; operator still accepts visible cards.
- Kids docs live in `/Users/admin/projects/family/kids-visual-learning-pack`. Do not touch `outputs/`.

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/four_card_render/weighted_layout.py` | Shared `usable` / `content_h` / `allocate_zone_heights` / `stack_weighted_layout` |
| `src/cognitive_card_server/four_card_render/render.py` | `mapping-artifact-v1` pages use `stack_weighted_layout`; equal `stack_layout` remains default |
| `src/cognitive_card_server/four_card_artifact/pack.py` | Weighted assert per page; OBS assert after COPY plan texts |
| `src/cognitive_card_server/four_card_artifact/copy_plan.py` | Stop-append using look + copy + trace content heights |
| `tests/test_weighted_layout.py` | Allocator unit tests |
| `tests/test_pack_from_mapping.py` | Rabbit-real pack succeeds; synthetic flex overflow still `TEXT_OVERFLOW`; COPY budget |
| `tests/test_artifact_pipeline.py` | Rabbit-real generate succeeds (`awaiting_review`) |
| `tests/test_four_card_lock.py` / `tests/test_four_card_render.py` | ACCEPT-01 regression only (run, do not change unless a test breaks for an unrelated reason — then stop) |

Kids (Task 4): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md` (plan/spec status already listed).

---

## Phase 1: Shared geometry and mapping-artifact packing

### Task 1: Weighted height allocator

**Files:**
- Create: `src/cognitive_card_server/four_card_render/weighted_layout.py`
- Test: `tests/test_weighted_layout.py`

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_weighted_layout -v` → all pass
**Depends on:** None

**Interfaces:**
- Consumes: `a4_pixels`, `SAFE_MARGIN_PX`, `wrap_text`, `load_font`, `DEFAULT_FONT_PATH` from `cognitive_card_server.four_card_render.render` (import wrap/load inside functions or at module level; `render.py` must not import this module at top level until Task 3, or import only `stack_weighted_layout` later — **this module may import from `render.py`** because `render.py` will import it only inside `_render_page` / a helper, not at module import time of `weighted_layout` cycling back through `copy_plan`).
- Produces:

```python
LABEL_TO_TEXT_PX = 112
ZONE_BOTTOM_PAD_PX = 28
TEXT_INSET_PX = 28
ZONE_GAP_PX = 24
LABEL_BAND_PX = LABEL_TO_TEXT_PX + ZONE_BOTTOM_PAD_PX  # 140

FLEX_ZONE = {
    "CN_KNOW": "appearance",
    "EN_KNOW": "appearance",
    "CN_OBS": "look",
    "EN_OBS": "look",
}

def page_usable(page_height: int, margin: int, zone_count: int, gap: int = ZONE_GAP_PX) -> int:
    """page_h - 2*margin - gap*(n-1). Same as stack_layout."""

def layout_metrics(font, page_size: tuple[int, int], margin: int) -> tuple[object, object, int, int]:
    """Return (draw, font, text_width, line_height). text_width = inner_w - 2*TEXT_INSET_PX. line_height = ascent+descent+8."""

def zone_content_height(text: str, language: str, *, draw, font, text_width: int, line_height: int) -> int:
    """Empty text → LABEL_BAND_PX. Else LABEL_BAND_PX + len(wrap_text(...)) * line_height."""

def allocate_zone_heights(
    zone_order: list[str],
    texts: Mapping[str, str],
    flex_zone: str,
    language: str,
    *,
    overflow_path: str,
    page_size: tuple[int, int] | None = None,
    margin: int | None = None,
    gap: int = ZONE_GAP_PX,
    draw=None,
    font=None,
) -> dict[str, int]:
    """non_flex = sum(content_h(z) for z != flex); flex_h = usable - non_flex.
    If flex_h < content_h(flex) raise KnowledgeContractError("TEXT_OVERFLOW", overflow_path).
    Else heights[flex]=flex_h, others content_h."""

def stack_weighted_layout(
    zones: list[str],
    heights: Mapping[str, int],
    page_size: tuple[int, int],
    margin: int,
    *,
    gap: int = ZONE_GAP_PX,
) -> list[tuple[str, tuple[int, int, int, int]]]:
    """Sequential boxes like stack_layout, zone height from heights[zone]. Sum(heights)+gaps must equal usable (flex already absorbed leftover)."""
```

Default `page_size`/`margin`: `a4_pixels(300)` and `SAFE_MARGIN_PX` when omitted. Create a 16×16 RGB draw surface like `_layout_budget` when `draw`/`font` omitted (load default font).

- [ ] **Step 1: Write the failing tests**

```python
"""Weighted zone-height allocator for mapping-artifact print binding."""

from __future__ import annotations

import unittest

from cognitive_card_server.four_card_render.pdf import a4_pixels
from cognitive_card_server.four_card_render.render import SAFE_MARGIN_PX, wrap_text
from cognitive_card_server.four_card_render.weighted_layout import (
    FLEX_ZONE,
    LABEL_BAND_PX,
    ZONE_GAP_PX,
    allocate_zone_heights,
    layout_metrics,
    page_usable,
    stack_weighted_layout,
    zone_content_height,
)
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError


class WeightedLayoutTests(unittest.TestCase):
    def test_page_usable_matches_equal_stack_formula(self) -> None:
        _w, height = a4_pixels(300)
        n = 4
        expected = height - 2 * SAFE_MARGIN_PX - ZONE_GAP_PX * (n - 1)
        self.assertEqual(expected, page_usable(height, SAFE_MARGIN_PX, n))

    def test_empty_zone_is_label_band(self) -> None:
        draw, font, text_w, line_h = layout_metrics(
            None, a4_pixels(300), SAFE_MARGIN_PX
        )
        self.assertEqual(
            LABEL_BAND_PX,
            zone_content_height("", "en", draw=draw, font=font, text_width=text_w, line_height=line_h),
        )

    def test_flex_gets_leftover_and_short_text_fits(self) -> None:
        heights = allocate_zone_heights(
            ["appearance", "uncertainty", "safety", "sources"],
            {
                "appearance": "Long ears.\nSoft fur.",
                "uncertainty": "",
                "safety": "Stay with an adult.",
                "sources": "Tiny Title (src-tiny)",
            },
            "appearance",
            "en",
            overflow_path="EN_KNOW.appearance",
        )
        _w, height = a4_pixels(300)
        usable = page_usable(height, SAFE_MARGIN_PX, 4)
        self.assertEqual(usable, sum(heights.values()))
        self.assertGreater(heights["appearance"], heights["uncertainty"])
        self.assertEqual(LABEL_BAND_PX, heights["uncertainty"])

    def test_flex_overflow_is_text_overflow_on_path(self) -> None:
        draw, font, text_w, line_h = layout_metrics(
            None, a4_pixels(300), SAFE_MARGIN_PX
        )
        chunk = "word " * 80
        lines = wrap_text(draw, chunk, font, text_w, "en")
        while zone_content_height(
            chunk, "en", draw=draw, font=font, text_width=text_w, line_height=line_h
        ) < page_usable(a4_pixels(300)[1], SAFE_MARGIN_PX, 4) - 3 * LABEL_BAND_PX:
            chunk = chunk + " extra"
            if len(chunk) > 20000:
                self.fail("could not grow overflow fixture")
        with self.assertRaises(KnowledgeContractError) as caught:
            allocate_zone_heights(
                ["appearance", "uncertainty", "safety", "sources"],
                {
                    "appearance": chunk,
                    "uncertainty": "",
                    "safety": "",
                    "sources": "",
                },
                "appearance",
                "en",
                overflow_path="EN_KNOW.appearance",
            )
        self.assertEqual("TEXT_OVERFLOW", caught.exception.code)
        self.assertEqual("EN_KNOW.appearance", caught.exception.path)

    def test_stack_weighted_layout_uses_given_heights(self) -> None:
        zones = ["look", "record", "trace", "copy"]
        heights = {"look": 2000, "record": 140, "trace": 200, "copy": 400}
        layout = stack_weighted_layout(zones, heights, a4_pixels(300), SAFE_MARGIN_PX)
        self.assertEqual(4, len(layout))
        self.assertEqual("look", layout[0][0])
        x0, y0, x1, y1 = layout[0][1]
        self.assertEqual(2000, y1 - y0)


if __name__ == "__main__":
    unittest.main()
```

`layout_metrics(None, ...)` must accept `font=None` and load the default font.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_weighted_layout -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `weighted_layout.py`**

Match constants to `_render_page`: `text_top = y0 + 112`, `text_bottom = y1 - 28`, horizontal inset 28, `gap=24`. `stack_weighted_layout` must call the same `_validate_layout_geometry` as `stack_layout` (import from `render` if it is already a module-level function; it is `_validate_layout_geometry` in `render.py` — import it). If importing `_validate_layout_geometry` from `render` pulls `copy_plan` and cycles, duplicate the tiny overlap/bounds check in `weighted_layout.py` (copy the 15-line function, do not import `render` except `wrap_text` / `load_font` / `DEFAULT_FONT_PATH` / `SAFE_MARGIN_PX` / `a4_pixels`).

Preferred import pattern to avoid cycles:

```python
from cognitive_card_server.four_card_render.pdf import a4_pixels
from cognitive_card_server.four_card_render.render import (
    DEFAULT_FONT_PATH,
    SAFE_MARGIN_PX,
    load_font,
    wrap_text,
)
```

`render.py` currently does not import `weighted_layout` at top level (Task 3 adds a function-local import). That keeps this import acyclic.

`layout_metrics(font, page_size, margin)`: if `font` is `None`, `load_font(DEFAULT_FONT_PATH)`.

- [ ] **Step 4: Re-run tests**

Same command as Step 2. Expected: OK.

- [ ] **Step 5: Do not commit**

Operator authorizes git commits separately.

---

### Task 2: Pack + COPY budget on weighted heights

**Files:**
- Modify: `src/cognitive_card_server/four_card_artifact/pack.py`
- Modify: `src/cognitive_card_server/four_card_artifact/copy_plan.py`
- Modify: `tests/test_pack_from_mapping.py`

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_pack_from_mapping tests.test_weighted_layout -v` → all pass
**Depends on:** Task 1

**Interfaces:**
- Consumes: `allocate_zone_heights`, `FLEX_ZONE`, `layout_metrics` from Task 1; `resolve_profile`; `copy_plan_from_knowledge_cards`
- Produces: `pack_from_mapping` still returns the same locked-record shape; COPY overlay still happens in `bind_locked_record`. Pack **must** call `copy_plan_from_knowledge_cards` on the in-progress cards (look filled, copy/trace still empty on the card dict) and then `allocate_zone_heights` for OBS using joined COPY/trace visible strings from that plan.

Copy-plan signature stays:

```python
def copy_plan_from_knowledge_cards(
    cards: Mapping[str, object],
    propositions: Sequence[Mapping[str, object]],
    profile: AgeLanguageProfile,
) -> dict[str, object]:
```

Read look text from `cards["CN_OBS"]["zones"]["look"]["visible_text"]` (empty string if missing). `_fill_copy` must stop when `allocate_zone_heights` for `["look","record","trace","copy"]` with `flex_zone="look"` would raise `TEXT_OVERFLOW`. Recompute trace from the candidate copy list each attempt (existing `_trace_from_copy`).

Legal-span gate: if age-5-6 and `_sentences(knowledge_text)` has no sentence that maps to a proposition id, raise `AGE_COPY_SPAN_UNAVAILABLE`. Do **not** raise that code merely because every extra sentence fails the height check (COPY list may be shorter, including empty, when look already consumes the page).

Replace per-zone `_fits` / `_assert_zone_fits` in `pack.py` with one `_assert_weighted_page(page_id, language, texts)` that calls `allocate_zone_heights(..., overflow_path=f"{page_id}.{FLEX_ZONE[page_id]}")`. Keep `_fits` deleted or unused.

KNOW pages: texts = appearance, uncertainty, safety, sources (as packed). OBS pages: look, record `""`, trace from plan, copy from plan.

`test_rabbit_real_pack_fails_closed_on_text_overflow`: invert to success:

- `pack_from_mapping` returns a record
- `lock_version == mapping-artifact-v1`
- CN/EN knowledge main `proposition_ids` equal FACT ids (9 known)
- look ≥ 2 and ⊆ main
- sources `visible_text` contains titles, `proposition_ids == []`
- sources text does not contain a full appearance claim line

Keep `test_mapped_main_zone_overflow_is_text_overflow_not_sources`, but grow overflow strings with `allocate_zone_heights` until KNOW appearance overflows **after** short safety/sources/empty uncertainty — do not use equal `_layout_budget()[3]` as the overflow threshold (that is too small once appearance is flex). Helper:

```python
def _flex_overflow_text(language: str) -> str:
    from cognitive_card_server.four_card_render.weighted_layout import allocate_zone_heights
    base = "字" * 40 if language == "cn" else ("word " * 40).strip()
    text = base
    while True:
        try:
            allocate_zone_heights(
                ["appearance", "uncertainty", "safety", "sources"],
                {"appearance": text, "uncertainty": "", "safety": "x", "sources": "y"},
                "appearance",
                language,
                overflow_path="PROBE.appearance",
            )
        except KnowledgeContractError as error:
            if error.code == "TEXT_OVERFLOW":
                return text
            raise
        text = text + base
        if len(text) > 50000:
            raise AssertionError("overflow fixture did not exceed flex")
```

`test_copy_overflow_stops_without_text_overflow`: stop using equal `max_lines`. Build `_knowledge_cards` **and** OBS look text long enough that only some COPY sentences fit. Example: look = many wrapped English lines (repeat a short sentence), knowledge = `max_lines+3` short sentences; assert COPY length ≥ 1 and < sentence count; adding one more sentence would make `allocate_zone_heights` raise.

`test_mapping_artifact_overlay_copy_is_knowledge_substring_and_allows_more_than_two` must remain green (3 short sentences still fit).

- [ ] **Step 1: Change rabbit-real pack test to expect success; add flex overflow helper; rewrite COPY overflow test**
- [ ] **Step 2: Run `tests.test_pack_from_mapping` — rabbit success test FAIL (still TEXT_OVERFLOW) and overflow helper tests as they land**
- [ ] **Step 3: Implement pack.py + copy_plan.py as specified**
- [ ] **Step 4: Re-run Verify command — OK**
- [ ] **Step 5: Do not commit**

Pack must pass `normalized_request` into `_cards_from_mapping` so `resolve_profile(request)` works.

---

## Phase 2: RENDER + generate + kids docs

### Task 3: RENDER uses weighted stack for mapping-artifact-v1

**Files:**
- Modify: `src/cognitive_card_server/four_card_render/render.py` (`_render_page` layout selection)
- Test: extend `tests/test_pack_from_mapping.py` MappingArtifactCopyPlanTests **or** add one method on `tests/test_weighted_layout.py` that `bind_locked_record` + inspects that planned bbox heights are unequal for a mapping-artifact tiny pack. Prefer adding `test_mapping_artifact_render_look_taller_than_record` in `tests/test_pack_from_mapping.py` that packs `_tiny_payload`, `render_locked` to a temp dir, reads `reports/CN_KNOW.layout.json` (or OBS), asserts appearance `planned_bbox` height > uncertainty height.

**Verify:** `cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_pack_from_mapping tests.test_four_card_render tests.test_weighted_layout -v` → all pass
**Depends on:** Task 2

**Interfaces:**
- Consumes: `allocate_zone_heights`, `stack_weighted_layout`, `FLEX_ZONE`
- `_render_page` today: `layout = stack_layout(zones, page_size, SAFE_MARGIN_PX)`
- When `bound["render_input"]` or lock version is mapping-artifact: build `texts` from `page_record["zones"][z]["visible_text"]` (COPY already overlaid in `bound["pages"]`), `flex = FLEX_ZONE[page_id]`, `heights = allocate_zone_heights(...)`, `layout = stack_weighted_layout(zones, heights, page_size, SAFE_MARGIN_PX)`
- Pass `overflow_path=f"{page_id}.{flex}"`
- Detect version: `bound["render_input"]` does not currently include `lock_version`. Add `lock_version` into `render_input` in `bind_locked_record` (string `mapping-artifact-v1` or `""`) so PNG hashes stay deterministic **and** `_render_page` can branch. Including it in `render_input` changes `render_input_sha256` for mapping-artifact only — ACCEPT-01 records have other lock_version and stay on equal stack (empty/`accept-01-v1`).

```python
lock_version = ""
lock = record.get("content_lock")
# existing extraction in bind_locked_record — also set
render_input["lock_version"] = lock_version
```

`_render_page`:

```python
from cognitive_card_server.four_card_render.weighted_layout import (
    FLEX_ZONE,
    allocate_zone_heights,
    stack_weighted_layout,
)

lock_version = str(bound["render_input"].get("lock_version") or "")
if lock_version == "mapping-artifact-v1":
    texts = {
        zone: str(page_record["zones"][zone].get("visible_text") or "")
        for zone in zones
    }
    heights = allocate_zone_heights(
        zones,
        texts,
        FLEX_ZONE[page_id],
        language,
        overflow_path=f"{page_id}.{FLEX_ZONE[page_id]}",
        page_size=page_size,
        margin=SAFE_MARGIN_PX,
        draw=draw,
        font=font,
    )
    layout = stack_weighted_layout(zones, heights, page_size, SAFE_MARGIN_PX)
else:
    layout = stack_layout(zones, page_size, SAFE_MARGIN_PX)
```

Note: `draw` is created after current `stack_layout` call. Reorder: create canvas/draw, then weighted allocate using that draw/font, then paint. Equal path can keep layout-first if easier: for equal path, keep current order; for weighted, create canvas first then allocate.

- [ ] **Step 1: Write render bbox test (tiny pack → layout json appearance taller than uncertainty)**
- [ ] **Step 2: Run it — FAIL (equal heights ~ equal)**
- [ ] **Step 3: Wire `_render_page` + `render_input.lock_version`**
- [ ] **Step 4: Verify command — OK. `tests.test_four_card_render` must still pass (ACCEPT-01 equal stack)**
- [ ] **Step 5: Do not commit**

---

### Task 4: Rabbit generate + kids governance

**Files:**
- Modify: `tests/test_artifact_pipeline.py` (`test_rabbit_real_generate_fails_closed_on_text_overflow` → success)
- Modify (kids): `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md` (2026-09-02 note: weighted implemented in worktree, WB-03 still IN PROGRESS until operator accepts cards)
- Do not mark `WB-03` DONE

**Verify:**

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core
PYTHONPATH=src .venv/bin/python -m unittest tests.test_artifact_pipeline tests.test_pack_from_mapping tests.test_weighted_layout tests.test_four_card_render tests.test_four_card_lock -v
```

Expected: OK

Kids:

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack
bash scripts/ai/check-task-state.sh
bash scripts/ai/check-handoff.sh
bash scripts/ai/check-doc-governance.sh
git diff --check
```

**Depends on:** Task 3

**Rabbit generate success assertions:**

- `generate_from_mapping` returns `status == awaiting_review`
- work dir has four card PNGs + `print.pdf`
- `current.json` and `mapping.json` bytes unchanged
- no package-catalog created
- locked record knowledge main ids equal FACT; sources `proposition_ids` empty

Replace `test_rabbit_real_generate_fails_closed_on_text_overflow` with `test_rabbit_real_generate_awaits_review` (do not keep a test that expects TEXT_OVERFLOW for rabbit-real).

- [ ] **Step 1: Rewrite rabbit-real generate test to success assertions**
- [ ] **Step 2: Run it — should PASS if Task 3 is correct; if FAIL, fix render/pack, do not weaken assertions**
- [ ] **Step 3: Update kids CURRENT_TASK (check rabbit AC), HANDOFF (real commands), roadmap note. Spec stays Approved. WB-03 stays IN PROGRESS**
- [ ] **Step 4: Run both Verify blocks**
- [ ] **Step 5: Do not commit. Do not add `uv.lock` or `outputs/`**

---

## Spec coverage (self-review)

| Spec section | Task |
| --- | --- |
| §2 layering / no Core rewrite | Global Constraints + no authoring edits |
| §5 shared height function | Task 1 |
| §5.1 flex appearance / look | Task 2 + 3 |
| §5.2 COPY budget | Task 2 |
| §7.1–7.4 rabbit pack/generate | Task 2 + 4 |
| §7.5 synthetic overflow | Task 2 `_flex_overflow_text` |
| §7.6 ACCEPT-01 | Task 3 verify `test_four_card_render` + Task 4 `test_four_card_lock` |
| §8 extract helper | Task 1 `weighted_layout.py` |
