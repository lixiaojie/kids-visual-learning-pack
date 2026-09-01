# Operator Mapping Scheme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Let an operator preview and lock a Projection family slot mapping against knowledge current without moving `current.json`, without PNG, and without changing Knowledge Core facts.

**Architecture:** Add a versioned safety-expression registry next to AGE-01 claim tables. Add a pure `preview_mapping` that assigns path nodes to four-card (or existing family) slots. Add `KnowledgeLibrary.lock_mapping` that writes a new revision with `set_current=False` and a sibling `mapping.json` pointer. Expose preview/lock on admin ops HTTP and a third panel on the detail page. CLI calls the same functions.

**Tech Stack:** Python 3 unittest, existing `KnowledgeLibrary` / `knowledge_ops` / FastAPI admin routes on server `knowledge-pipeline-v1`.

**Plan size:** Medium (5 tasks, 2 phases)

## Global Constraints

- Four-object schema, v1 FACT keys, AUTHOR-05 defaults, and packet contract stay unchanged.
- Do not call CONV-01, RENDER-01, QA-01, PUBLISH-01, or `KnowledgeLibrary.publish` from mapping lock.
- `lock_mapping` must not change `current.json`.
- Fact payload (`sources`, `propositions`, `relations`, `knowledge_units`, `scope`, `coverage`) must match current after aligning `revision` fields; only identity/refs and projection-spec/manifest may change.
- Slot ids stay `slot.{topic_slug}.{suffix}` with suffixes `cn-observation`, `en-observation`, `cn-knowledge`, `en-knowledge` in that order for four-card.
- Do not overflow leftover propositions into sources. Empty active knowledge nodes → `MAPPING_FOUR_CARD_OVERLOADED`. Look < 2 distinct nodes or not ⊆ knowledge → `MAPPING_LOOK_UNDERFILLED`.
- Collect safety English strings from each proposition's `safety` list (and top-level `safety_scope` if present). Unregistered string → `AGE_SAFETY_EXPRESSION_GAP`; cannot lock four-card.
- First registry keys (verbatim): `Ask a rabbit-savvy veterinarian before making significant diet changes.`; `Children must be supervised; only adults or responsible older children should pick up rabbits.`; `A struggling rabbit can injure its fragile spine, so handling must stay calm and secure.`
- Pin `age-language-adapter-v1` and `safety-expression-registry-v1` on locked four-card `renderer_binding.required_capabilities` (union with existing caps, keep `text-content`).
- HTML ops shells must not embed claims without a token. No Generate button. No PNG/PDF files.
- Do not merge server `main`, push, add `uv.lock`, or install a production release. Do not auto git commit (operator authorizes commits separately).
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1`.

---

## Phase 1: Mapping core (server)

### Task 1.1: Safety expression registry

**Files:**
- Create: `src/cognitive_card_server/age_language/safety_registry.py`
- Modify: `src/cognitive_card_server/age_language/adapter.py` (re-export lookup)
- Test: `tests/test_age_safety_expression.py`

**Verify:** `python3 -m unittest tests.test_age_safety_expression -v` → all pass
**Depends on:** None

**Interfaces:**
- Produces: `SAFETY_REGISTRY_VERSION = "safety-expression-registry-v1"`; `lookup_safety_cn(english: str) -> str` raises `KnowledgeContractError("AGE_SAFETY_EXPRESSION_GAP", ...)` on miss; `project_safety_strings(texts: Sequence[str]) -> list[dict[str, str]]` with `{en, cn}`

- [x] **Step 1: Write failing tests** for exact-key hit on the three rabbit strings (cn must keep 监护 / 脊椎 meaning), miss → `AGE_SAFETY_EXPRESSION_GAP`, no mutation of the English key.

- [x] **Step 2: Run tests, expect import/attribute failure**

- [x] **Step 3: Implement registry dict + lookup.** Chinese must not drop 须监护 / 伤脊椎 / 兽医. Fail closed. No translator.

- [x] **Step 4: Re-run tests → PASS.** Do not commit.

### Task 1.2: `preview_mapping` pure function

**Files:**
- Create: `src/cognitive_card_server/knowledge_library/mapping.py`
- Test: `tests/test_mapping_preview.py`

**Verify:** `python3 -m unittest tests.test_mapping_preview tests.test_age_safety_expression -v` → all pass
**Depends on:** Task 1.1

**Interfaces:**
- Consumes: `load_package`, `select_projection_family`, `signals_from_compiled`, `lookup_safety_cn` / `project_safety_strings`, authoring slot suffix rules
- Produces:

```python
def collect_safety_texts(core: Mapping[str, object]) -> tuple[str, ...]
def preview_mapping(bundle: KnowledgeBundle, *, family: str) -> dict[str, object]
```

Preview dict (no disk): `family`, `selection` (PROJ-01 `as_dict()` with `requested_family=family`), `slots` (list of `{slot_id, node_ids, proposition_ids, claims}`), `look_subset` bool, `record_empty` True, `sources` (`source_id`, `title`), `safety` (`en`, `cn` or gap), `errors` (list of codes). Unknown family → raise `MAPPING_FAMILY_UNKNOWN` (or reuse selector error mapped to that code). No current is not this function's job.

four-card assignment:
- Active knowledge nodes = path content nodes whose unit is in `scope.included_unit_ids` and none of their propositions have `standing=="superseded"` (missing standing = active).
- Knowledge slots both get the full active node list (same order as path). If empty → errors include `MAPPING_FOUR_CARD_OVERLOADED`.
- Look nodes = active nodes that have at least one proposition with `certainty != "unknown"` (missing certainty counts as includable). If len < 2 or not ⊆ knowledge → `MAPPING_LOOK_UNDERFILLED`.
- Observation slots get look nodes; do not add a record slot.
- Sources: every core source must have non-blank `title` or `MAPPING_SOURCE_TITLE_MISSING`.
- Safety: `collect_safety_texts`; any GAP recorded; preview still returns slots; lock (next task) refuses four-card if GAP.
- Other families: rebuild slots with existing `_build_projection` strategy (progressive per-node, else `main`) using active node ids; no safety GAP block.

Rabbit-real fixture (`examples/authoring/rabbit-real.json` compiled, no four-card overlay): knowledge proposition_ids ≥ 4 distinct; look ≥ 2 ⊆ knowledge; sources include `Description and Physical Characteristics of Rabbits` or `Diet for Rabbits` or an RSPCA title; three safety English keys project to Chinese.

- [x] **Step 1: Failing tests** for rabbit-real four-card preview; unknown family; missing source title (mutate a copy); look underfilled (tiny synthetic); safety gap (drop a registry key via a local override only if needed — prefer a synthetic core string).

- [x] **Step 2: Implement `mapping.py`.** Import `_build_projection` from authoring if needed for non-four-card; do not duplicate selector fit rules.

- [x] **Step 3: Tests PASS.** Do not commit.

### Task 1.3: `lock_mapping` + `mapping.json`

**Files:**
- Modify: `src/cognitive_card_server/knowledge_library/store.py`
- Modify: `src/cognitive_card_server/knowledge_library/cli.py`
- Modify: `src/cognitive_card_server/knowledge_library/__init__.py` if it exports symbols
- Test: `tests/test_knowledge_library_mapping.py`
- Modify: `tests/test_knowledge_library.py` only if pointer helpers must stay compatible

**Verify:** `python3 -m unittest tests.test_knowledge_library_mapping tests.test_knowledge_library tests.test_mapping_preview -v` → all pass
**Depends on:** Task 1.2

**Interfaces:**
- Produces: `KnowledgeLibrary.lock_mapping(self, topic_slug: str, *, family: str, now: datetime) -> LibraryRevision`
- Produces: `KnowledgeLibrary.get_mapping(self, topic_slug: str) -> dict[str, object] | None` (`None` if missing file)
- Mapping pointer schema `cognitive-card-knowledge-library-mapping-v1` as spec §7 plus identity of the **new** bundle
- CLI: `preview-mapping --topic --family --library-root --now`; `lock-mapping` same; `mapping --topic --library-root` prints pointer or `listed=false`

Behavior:
1. `get_current` or raise `MAPPING_NO_CURRENT`.
2. `preview_mapping(load_package(current.directory), family=family)`. If `errors` non-empty for this family (four-card: any of OVERLOADED / LOOK_UNDERFILLED / SOURCE_TITLE_MISSING / AGE_SAFETY_EXPRESSION_GAP) → raise first code.
3. Deep copy core+learning. `next_rev = max(_revision_numbers(slug), default=0)+1`. Set `core["revision"]`, `learning["revision"]`, `learning["knowledge_core_ref"]["revision"]`.
4. Assert fact payload equal to current after forcing both cores' `revision` to the same int.
5. Build new projection: four-card via preview slot lists + `_build_projection` then **overwrite** `blueprint.slots[].node_ids` to preview assignment; set `required_capabilities` to unique list including `text-content`, `age-language-adapter-v1`, `safety-expression-registry-v1`. Projection `revision=next_rev`, `learning_spec_ref.revision=next_rev`.
6. `build_manifest(...)` with copied artifacts from current (same bytes), lifecycle `validated`, new locks. Validate PUBLISH stage.
7. `_write_revision(..., set_current=False, reason="lock_mapping")`.
8. Write `mapping.json` and append `mapping-audit.jsonl` (same atomic replace pattern as current pointer; **do not** write `current.json`).

Tests:
- Publish rabbit-real as current (rev 1). Lock four-card. `get_current` still rev 1. `mapping.json` revision 2. Directories `revision-0001` and `revision-0002` both exist. Fact payload equal. `publish` was not used (current reason still publish).
- Second lock → revision 3, mapping pointer advances, current still 1.
- GAP: temporarily use a family preview path — or lock after monkeypatching registry — four-card lock raises `AGE_SAFETY_EXPRESSION_GAP` and current/mapping unchanged.
- Preview-only does not create directories.

- [x] **Step 1: Failing tests**
- [x] **Step 2: Implement store + CLI**
- [x] **Step 3: Tests PASS including existing `tests.test_knowledge_library`.** Do not commit.

---

## Phase 2: Ops surface + kids governance

### Task 2.1: Ops HTTP + third panel

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Modify: `src/cognitive_card_server/http/app.py` (`PROTECTED_ROUTES` for new GET/POST)
- Modify: `src/cognitive_card_server/http/errors.py` if new codes need 409 (`MAPPING_NO_CURRENT`, `LIBRARY_REVISION_EXISTS` already 409)
- Test: `tests/test_http_knowledge_ops.py` (extend)

**Verify:** `python3 -m unittest tests.test_http_knowledge_ops tests.test_knowledge_library_mapping -v` → all pass
**Depends on:** Task 1.3

Routes (admin Bearer, same prefix as WB-01):
- GET `.../{topic}/mapping-preview?family=`
- GET `.../{topic}/mapping` → pointer or `{"listed": false}` HTTP 200
- POST `.../{topic}/mapping-lock` body `{"family": "four-card"}`

No token: 401, not 200 empty. Invalid slug: `OPS_NOT_FOUND`. Detail HTML: add `data-panel="mapping"` built **client-side after token** (buttons, slot lists from preview JSON). Shell source without token still has no claims / no Merck / no safety English. No control whose text is `生成` / `Generate`. Clicking family option refetches preview only. Confirm calls POST lock then GET mapping.

Add `MAPPING_NO_CURRENT` to conflict codes (409). `AGE_SAFETY_EXPRESSION_GAP` stays 400.

Keep existing WB-01 tests green.

- [x] **Step 1: Failing HTTP tests** (preview no write; lock keeps current; listed=false; 401; HTML no Generate / no claims without token)
- [x] **Step 2: Implement routes + JS panel**
- [x] **Step 3: Tests PASS.** Do not commit.

### Task 2.2: Kids governance

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md` (WB-02 completion criteria = spec §10; mark DONE after tests pass), `docs/README.md` (spec Approved; this plan listed), `docs/cognitive-card-os-system-design.md`
- This plan file

**Verify:** `bash scripts/ai/check-task-state.sh`; `bash scripts/ai/check-handoff.sh`; `bash scripts/ai/check-doc-governance.sh` (WARN overdue Last Reviewed allowed); `git diff --check`
**Depends on:** Task 2.1 for Done claim; may update IN PROGRESS notes immediately after plan exists

- [x] Record server test commands and PASS/FAIL in HANDOFF. Do not claim production install. Do not commit unless operator asks.

---

## Spec coverage

| Spec § | Task |
| --- | --- |
| 5 select family | 2.1 |
| 6.1–6.3 slots | 1.2 |
| 6.4 safety registry | 1.1, 1.2, 1.3 |
| 7 mapping.json / no publish | 1.3 |
| 8 HTTP + third block | 2.1 |
| 9 error codes | 1.2–2.1 |
| 10 acceptance | 1.2, 1.3, 2.1 |
| 11 no Nginx / no PNG | Global Constraints |
