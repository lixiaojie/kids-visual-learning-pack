# Operator Composite Projection Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For a topic that already has an illustrated no-text hero PNG and a WB-03 `awaiting_review` four-card lock, compose an ops HTML page of four card sections and re-render observation cards with a top image band.

**Architecture:** File-backed compose record under `{candidate_root}/compose/{topic}/`. Gate on one `illustrated` intent plus artifact-work identity. Reuse `hero.png` by sha. Print uses `allocate_zone_heights(..., top_band_px=720)` only on OBS pages. Knowledge-card PNGs stay byte-identical. `generate_from_mapping` stays image-optional.

**Tech Stack:** Python 3 unittest, FastAPI TestClient, Pillow, existing knowledge-pipeline-v1 worktree.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-03-operator-composite-projection-display-design.md` (Approved).
- No image API, no burn-in, no new projection family, no KNOW-04 production library, no merge/push/release.
- Do not fail `generate_from_mapping` when no illustration exists.
- Pin six identity keys: `object_id`, `revision`, `knowledge_core_sha256`, `learning_spec_sha256`, `projection_spec_sha256`, `final_content_lock_sha256`.
- `OBS_IMAGE_BAND_PX = 720`. Contain, no crop. Keys only `CN_OBS:band` and `EN_OBS:band`.
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core`. `PYTHONPATH=src .venv/bin/python`.
- Do not git commit unless the operator asks. Do not add `uv.lock` or kids `outputs/`.
- Do not mark roadmap `IMG-01` `DONE`.

### Combined focused gate

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_http_knowledge_ops tests.test_knowledge_library_mapping tests.test_weighted_layout tests.test_http_auth tests.test_knowledge_illustration tests.test_http_knowledge_illustration tests.test_knowledge_compose tests.test_http_knowledge_compose tests.test_artifact_pipeline
```

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/knowledge_compose/__init__.py` | Export `compose_projection`, `load_compose` |
| `src/cognitive_card_server/knowledge_compose/pipeline.py` | Gate, identity, re-render, public payload |
| `src/cognitive_card_server/knowledge_compose/store.py` | `compose/{topic}/meta.json` |
| `src/cognitive_card_server/four_card_render/weighted_layout.py` | `top_band_px` on usable + stack origin |
| `src/cognitive_card_server/four_card_render/render.py` | OBS top band placement |
| `src/cognitive_card_server/knowledge_ops/{http.py,pages.py}` | Admin + ops HTML |
| `src/cognitive_card_server/http/{app.py,errors.py}` | Protected routes + status map |
| `tests/test_knowledge_compose.py` | Domain gate + rabbit render |
| `tests/test_http_knowledge_compose.py` | HTTP + HTML shell |
| `tests/test_weighted_layout.py` | Band deduction |
| `tests/test_http_auth.py` | Registry length 50 |

---

## Phase 1: Gate

### Task 1: compose_projection gate

**Files:**
- Create: `src/cognitive_card_server/knowledge_compose/store.py`
- Create: `src/cognitive_card_server/knowledge_compose/pipeline.py`
- Create: `src/cognitive_card_server/knowledge_compose/__init__.py`
- Test: `tests/test_knowledge_compose.py`

**Interfaces:**

```python
COMPOSE_SCHEMA = "cognitive-card-compose-v1"
OBS_IMAGE_BAND_PX = 720
IDENTITY_KEYS = (
    "object_id", "revision", "knowledge_core_sha256",
    "learning_spec_sha256", "projection_spec_sha256", "final_content_lock_sha256",
)

def compose_projection(*, library, illustration_root, work_root, compose_root, topic_slug, actor, now) -> dict
def load_compose(*, library, illustration_root, work_root, compose_root, topic_slug, now) -> dict
```

Public dict always includes: `topic_slug`, `intent_id`, `hero_png_sha256`, `identity`, `mapping_identity`, `content_lock_sha256`, `pages` (four entries with `page`, `has_hero`, `zones` of `{id, text}`).

- [ ] Write failing tests: no illustration, no artifact, identity mismatch, actor reserved.
- [ ] Implement gate without render first; then Task 3 adds re-render.

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose -v`

**Depends on:** nothing

---

## Phase 2: Print band

### Task 2: weighted usable deduction

**Files:**
- Modify: `weighted_layout.py` `page_usable` callers: add `top_band_px: int = 0` to `allocate_zone_heights` and `origin_y` to `stack_weighted_layout` (default `margin`).
- Test: `tests/test_weighted_layout.py`

When `top_band_px > 0`, zone usable = `page_usable(...) - top_band_px - gap`. Stack starts at `margin + top_band_px + gap`. Existing tests stay green with default 0.

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_weighted_layout -v`

**Depends on:** Task 1

### Task 3: OBS band render + rabbit compose

**Files:**
- Modify: `render.py` `_render_page` for `mapping-artifact-v1` OBS pages when `assets` has `f"{page_id}:band"`.
- Modify: `pipeline.py` to call `render_locked(record, render_dir, assets={...})`.
- Test: rabbit-real generate then compose; know PNGs unchanged; observe PNGs change; no TEXT_OVERFLOW.

Do not pass look/record/copy keys. Knowledge pages get empty assets.

**Verify:** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compose tests.test_weighted_layout tests.test_artifact_pipeline -v`

**Depends on:** Task 2

---

## Phase 3: HTTP

### Task 4: admin + ops HTML

**Files:**
- Modify: `knowledge_ops/http.py`, `pages.py`, `http/app.py`, `http/errors.py`, `tests/test_http_auth.py`
- Test: `tests/test_http_knowledge_compose.py`

Routes (register compose HTML before `{topic}`):

- `POST /card-os/api/v1/admin/knowledge-compose`
- `GET /card-os/api/v1/admin/knowledge-compose/{topic}`
- `GET /card-os/ops/compose/{topic}`

Shell must not contain `claim` or locked look text. Topic page button `合成展示`. Conflict codes include the four `COMPOSE_*` codes. `PROTECTED_ROUTES` length 50.

**Verify:** focused gate above.

**Depends on:** Task 3
