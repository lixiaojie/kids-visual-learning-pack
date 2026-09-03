# Projection Legend v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `projection-legend-v1` on the knowledge-pipeline worktree so compile and four-card mapping resolve each active proposition to one closed cognitive role, omit empty roles, and fail closed on `misc` / unknown / unordered `sequence` / `blank` nodes.

**Architecture:** Mirror `templates/`: a projection registry that is not a governed object. Resolve roles from optional unit `legend_role`, else entity `coverage_facet` aliases, else `fact_type=process` → `sequence`, else unknown certainty → `uncertain`. Do not write roles into FACT. Mapping preview grows a `legend` block; lock fails on legend errors. IMG-02 and RENDER-02 are out of this plan.

**Tech Stack:** Python 3 unittest, existing `KnowledgeContractError`, `compile_authoring_request`, WB-02 `preview_mapping` / `lock_mapping`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md`
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1`
- Run tests with `PYTHONPATH=src .venv/bin/python`
- Do not change four-object top-level file names, v1 FACT keys, or KNOW-03 entity facet ids
- Do not implement IMG-02 multi-image slots, RENDER-02 chrome, burn-in OCR, or `LEGEND_UNCERTAIN_AS_FACT` drawing
- `LEGEND_BURN_IN` and `LEGEND_VIEW_UNKNOWN` may be defined as constants; do not wire them to illustration upload in this plan
- Do not merge/push/release, do not write production library, do not add `uv.lock` or kids `outputs/`
- Do not git commit unless the operator asks
- Rabbit `examples/authoring/rabbit-real.json` four-card preview must stay `errors == []` using aliases only

### Combined focused gate

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core && PYTHONPATH=src .venv/bin/python -m unittest tests.test_projection_legend tests.test_mapping_preview tests.test_knowledge_library_mapping tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_template_registry tests.test_coverage_compile tests.test_convert_mapping
```

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/projection_legend/roles.py` | Closed role ids, view ids, misc tokens, entity aliases |
| `src/cognitive_card_server/projection_legend/registry.py` | `REGISTRY_VERSION`, `registry_document`, sha256 |
| `src/cognitive_card_server/projection_legend/resolve.py` | `resolve_legend_role`, `assign_legend`, sequence order, place collapse |
| `src/cognitive_card_server/projection_legend/__init__.py` | Public exports |
| `src/cognitive_card_server/knowledge_contract/authoring.py` | Optional unit `legend_role` copy into `knowledge_units` |
| `src/cognitive_card_server/knowledge_library/mapping.py` | `preview["legend"]`; lock fail-closed |
| `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-v1.txt` | Role list; no dinosaur field checklist |
| `src/cognitive_card_server/knowledge_compile/parse.py` | Keep `legend_role` on units |
| `src/cognitive_card_server/knowledge_compile/pipeline.py` | After entity compile, `require_legend_assignments` |
| `tests/test_projection_legend.py` | Registry + resolver + assign |
| `tests/test_mapping_preview.py` | Rabbit legend block; blank/sequence/place failures |
| `tests/test_knowledge_compile.py` | Prompt contains roles; missing role fails new compile |

Kids docs (same session as last task, after server tests pass): spec Status, `docs/README.md` plan row, roadmap LEGEND-01.

---

### Task 1: Closed registry

**Files:**
- Create: `src/cognitive_card_server/projection_legend/roles.py`
- Create: `src/cognitive_card_server/projection_legend/registry.py`
- Create: `src/cognitive_card_server/projection_legend/__init__.py`
- Test: `tests/test_projection_legend.py`

**Interfaces:**

```python
REGISTRY_VERSION = "projection-legend-v1"
ENTITY_PACK_ID = "coverage-pack-entity-v1"
ROLE_IDS = frozenset({
    "observe", "compare", "evidence", "time", "place", "learning_place",
    "habit", "kind", "sequence", "setting", "uncertain", "safety",
    "source", "name", "write", "blank",
})
OBSERVE_VIEWS = frozenset({"isolate", "three_view", "section", "exploded"})
SETTING_VIEWS = frozenset({"in_situ", "interaction"})
MISC_TOKENS = frozenset({"misc", "other", "未分类", "miscellaneous"})
ENTITY_ALIASES = {
    "recognition": "observe",
    "appearance": "observe",
    "physical_features": "compare",
    "habits": "habit",
    "environment": "setting",
    "safety": "safety",
    "care": "safety",
}
CONTENT_ROLES = ROLE_IDS - frozenset({"name", "write", "blank", "source"})

def registry_document() -> dict[str, object]
def registry_sha256() -> str  # "sha256:" + hex
```

`registry_document()` keys: `schema` = `cognitive-card-projection-legend-v1`, `version`, `roles` (sorted list), `observe_views`, `setting_views`, `entity_pack_id`, `entity_aliases`.

- [ ] **Step 1: Write the failing test**

```python
from cognitive_card_server.projection_legend import (
    ENTITY_ALIASES,
    MISC_TOKENS,
    ROLE_IDS,
    REGISTRY_VERSION,
    registry_document,
    registry_sha256,
)

class RegistryTests(unittest.TestCase):
    def test_closed_roles_and_entity_aliases(self) -> None:
        self.assertEqual(REGISTRY_VERSION, "projection-legend-v1")
        self.assertIn("sequence", ROLE_IDS)
        self.assertIn("setting", ROLE_IDS)
        self.assertNotIn("misc", ROLE_IDS)
        self.assertEqual(ENTITY_ALIASES["appearance"], "observe")
        self.assertEqual(ENTITY_ALIASES["environment"], "setting")
        doc = registry_document()
        self.assertEqual(doc["schema"], "cognitive-card-projection-legend-v1")
        self.assertTrue(registry_sha256().startswith("sha256:"))
        self.assertEqual(len(registry_sha256()), 71)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_projection_legend.RegistryTests -v`

Expected: FAIL `ModuleNotFoundError` or import error.

- [ ] **Step 3: Write minimal implementation**

`roles.py` holds the frozensets/dicts. `registry.py` builds `registry_document` with `copy.deepcopy` of aliases and sorted role/view lists; `registry_sha256` uses `sha256_ref` from `knowledge_contract.model` like `templates/registry.py`. `__init__.py` re-exports.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_projection_legend.RegistryTests -v`

Expected: PASS

**Depends on:** nothing

---

### Task 2: Role resolver

**Files:**
- Create: `src/cognitive_card_server/projection_legend/resolve.py`
- Modify: `src/cognitive_card_server/projection_legend/__init__.py`
- Test: `tests/test_projection_legend.py`

**Interfaces:**

```python
def resolve_legend_role(
    *,
    legend_role: str | None,
    coverage_facet: str | None,
    fact_type: str | None,
    certainty: str | None,
    pack_id: str | None,
) -> str
```

Raises `KnowledgeContractError` with codes from spec §9.

Resolution (stop at first hit):

1. If `legend_role` in `MISC_TOKENS` → `LEGEND_MISC_FORBIDDEN` path `legend_role`
2. If `legend_role` is a non-empty string not in `ROLE_IDS` → `LEGEND_ROLE_UNKNOWN`
3. If `legend_role` in `ROLE_IDS` → return it
4. If `coverage_facet` in `ENTITY_ALIASES` and (`pack_id` is `None` or `pack_id == ENTITY_PACK_ID`) → return alias
5. If `coverage_facet` is a non-empty string, `pack_id` is set, and `pack_id != ENTITY_PACK_ID` → `LEGEND_ALIAS_PACK_GAP` path `coverage.coverage_pack_id`
6. If `fact_type == "process"` → `"sequence"`
7. If `certainty` in `{"unknown", "disputed"}` or `fact_type == "unknown_boundary"` → `"uncertain"`
8. Else `LEGEND_ROLE_MISSING` path `legend_role`

Skip step 5 when `coverage_facet` is empty so geometry units without facets do not hit pack gap inside this function; pack gap is for “has a facet but no alias table”.

- [ ] **Step 1: Write failing tests**

```python
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError
from cognitive_card_server.projection_legend import resolve_legend_role

class ResolveTests(unittest.TestCase):
    def test_explicit_role(self) -> None:
        self.assertEqual(
            resolve_legend_role(
                legend_role="time",
                coverage_facet="appearance",
                fact_type="property",
                certainty="established",
                pack_id="coverage-pack-entity-v1",
            ),
            "time",
        )

    def test_entity_alias(self) -> None:
        self.assertEqual(
            resolve_legend_role(
                legend_role=None,
                coverage_facet="physical_features",
                fact_type="property",
                certainty="established",
                pack_id="coverage-pack-entity-v1",
            ),
            "compare",
        )

    def test_process_fact_type(self) -> None:
        self.assertEqual(
            resolve_legend_role(
                legend_role=None,
                coverage_facet=None,
                fact_type="process",
                certainty="established",
                pack_id="coverage-pack-entity-v1",
            ),
            "sequence",
        )

    def test_unknown_certainty(self) -> None:
        self.assertEqual(
            resolve_legend_role(
                legend_role=None,
                coverage_facet=None,
                fact_type="property",
                certainty="unknown",
                pack_id="coverage-pack-entity-v1",
            ),
            "uncertain",
        )

    def test_misc_forbidden(self) -> None:
        with self.assertRaises(KnowledgeContractError) as ctx:
            resolve_legend_role(
                legend_role="misc",
                coverage_facet=None,
                fact_type=None,
                certainty="established",
                pack_id="coverage-pack-entity-v1",
            )
        self.assertEqual(ctx.exception.code, "LEGEND_MISC_FORBIDDEN")

    def test_missing(self) -> None:
        with self.assertRaises(KnowledgeContractError) as ctx:
            resolve_legend_role(
                legend_role=None,
                coverage_facet=None,
                fact_type="property",
                certainty="established",
                pack_id="coverage-pack-entity-v1",
            )
        self.assertEqual(ctx.exception.code, "LEGEND_ROLE_MISSING")

    def test_non_entity_facet_pack_gap(self) -> None:
        with self.assertRaises(KnowledgeContractError) as ctx:
            resolve_legend_role(
                legend_role=None,
                coverage_facet="habitat",
                fact_type="property",
                certainty="established",
                pack_id="coverage-pack-place-v1",
            )
        self.assertEqual(ctx.exception.code, "LEGEND_ALIAS_PACK_GAP")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_projection_legend.ResolveTests -v`

Expected: FAIL import or `resolve_legend_role` missing.

- [ ] **Step 3: Implement `resolve_legend_role`**

Implement the eight-step order above. Treat `legend_role=""` as missing (same as `None`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_projection_legend.ResolveTests tests.test_projection_legend.RegistryTests -v`

Expected: PASS

**Depends on:** Task 1

---

### Task 3: Assign roles on a Knowledge Core

**Files:**
- Modify: `src/cognitive_card_server/projection_legend/resolve.py`
- Test: `tests/test_projection_legend.py`

**Interfaces:**

```python
def assign_legend(core: Mapping[str, object]) -> dict[str, object]:
    """Return legend assignment. Does not mutate core."""
```

Return shape:

```python
{
  "roles": {role: [proposition_id, ...]},  # only roles with ≥1 id, ids stable core order
  "empty_roles": [role, ...],  # sorted CONTENT_ROLES with zero ids
  "blank_proposition_ids": [proposition_id, ...],
  "sequence_order": [proposition_id, ...],  # sequence role only; else []
}
```

Algorithm:

- `pack_id = core.get("coverage", {}).get("coverage_pack_id")` if coverage is a dict.
- Build `unit_by_prop`: for each `knowledge_units` entry, for each `proposition_ids` item, record `coverage_facet` and optional `legend_role`.
- For each `propositions` item with `standing` missing or `active` (treat missing as active; skip `superseded`):
  - `role = resolve_legend_role(...)` using unit fields + `fact_type` + `certainty`
  - If role == `"blank"` append to `blank_proposition_ids`
  - Else append `proposition_id` to `roles[role]`
- `sequence_order`: proposition_ids in `roles["sequence"]`. If 2+ ids, walk `core["relations"]` where `relation_type == "part_of"` among those ids. If those edges contain a cycle → `LEGEND_SEQUENCE_UNORDERED` path `sequence`. Else topological order constrained to that set; append any leftover ids in core proposition list order.
- `LEGEND_PLACE_COLLAPSE`: if both `place` and `learning_place` have ids, and any pair has equal `canonical_claim` strings → that code, path `place`.
- `LEGEND_ROLE_CONFLICT` is already impossible if one resolve per proposition; do not assign two roles.

Rabbit fixture: compile `examples/authoring/rabbit-real.json`, `assign_legend` must not raise; `blank_proposition_ids` empty; `observe` and `habit` and `safety` non-empty via aliases; `roles` must not contain `"blank"`.

- [ ] **Step 1: Write failing tests** `AssignTests.test_rabbit_aliases` and `test_sequence_cycle`.

For the cycle test, copy rabbit core in memory, tag two units `legend_role="sequence"`, add two `part_of` edges that cycle, expect `LEGEND_SEQUENCE_UNORDERED`.

- [ ] **Step 2: Run to verify fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_projection_legend.AssignTests -v`

- [ ] **Step 3: Implement `assign_legend`**

Do not mutate `core`. Skip propositions whose `proposition_id` is missing.

- [ ] **Step 4: Run to verify pass**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_projection_legend -v`

Expected: PASS

**Depends on:** Task 2

---

### Task 4: Persist optional unit `legend_role`

**Files:**
- Modify: `src/cognitive_card_server/knowledge_contract/authoring.py` (`_UNIT_OPTIONAL_KEYS` around line 94; `unit_record` around 769–772)
- Test: `tests/test_projection_legend.py`

Add `"legend_role"` to `_UNIT_OPTIONAL_KEYS`. If present on the authoring unit, `_string` it onto `unit_record["legend_role"]`.

- [ ] **Step 1: Failing test**

Load rabbit-real JSON, set `units[0]["legend_role"] = "kind"`, `compile_authoring_request`, assert that unit in core has `legend_role == "kind"`, and `assign_legend` maps that unit’s `proposition_ids` to `kind` (explicit beats appearance alias).

- [ ] **Step 2: Run fail** (compile drops unknown keys today)

- [ ] **Step 3: Copy optional field**

- [ ] **Step 4: Run `tests.test_projection_legend tests.test_coverage_compile -v`**

Expected: PASS; coverage compile still green.

**Depends on:** Task 3

---

### Task 5: Mapping preview and lock

**Files:**
- Modify: `src/cognitive_card_server/knowledge_library/mapping.py`
- Test: `tests/test_mapping_preview.py`
- Test: `tests/test_knowledge_library_mapping.py` (must stay green)

**Interfaces:** `preview_mapping` return dict gains `"legend"` equal to `assign_legend(core)` when `family == "four-card"`. Other families: `"legend": None`.

In `assemble_mapped_bundle` / lock path, after `preview = preview_mapping(...)`, if `family == "four-card"`:

- If `legend["blank_proposition_ids"]` → `KnowledgeContractError("LEGEND_BLANK_HAS_NODES", "blank")`
- Legend errors currently raised inside `assign_legend` already abort preview; also append is unnecessary if we raise. Keep raise-from-assign so preview either succeeds with a legend block or raises. For mapping preview that currently collects `errors` lists: **raise** on legend contract failures (same as `MAPPING_FAMILY_UNKNOWN`), do not bury them in `errors` except we could append for consistency. Spec is fail closed: **raise** `KnowledgeContractError`.

`test_rabbit_four_card_preview`: assert `preview["legend"]["blank_proposition_ids"] == []`; assert `"observe" in preview["legend"]["roles"]`.

New tests: mutate rabbit bundle units so one active prop resolves to `blank` via `legend_role="blank"` then `preview_mapping` raises `LEGEND_BLANK_HAS_NODES`. Second: two sequence props with cyclic `part_of` raise `LEGEND_SEQUENCE_UNORDERED`.

- [ ] **Step 1: Write failing mapping tests**
- [ ] **Step 2: Run fail**
- [ ] **Step 3: Call `assign_legend` from `preview_mapping` for four-card; re-raise; attach `legend`**
- [ ] **Step 4: Run** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_mapping_preview tests.test_knowledge_library_mapping tests.test_convert_mapping tests.test_pack_from_mapping -v`

Expected: PASS

**Depends on:** Task 4

---

### Task 6: Compile prompt + parse + new-compile gate

**Files:**
- Modify: `src/cognitive_card_server/knowledge_compile/templates/knowledge-compile-v1.txt`
- Modify: `src/cognitive_card_server/knowledge_compile/parse.py` (`_fill_unit_propositions` / unit dicts: copy `legend_role` if str)
- Modify: `src/cognitive_card_server/knowledge_compile/pipeline.py` `submit_reply` after `compile_authoring_request`
- Test: `tests/test_knowledge_compile.py`

Prompt additions (keep existing rabbit-real field contract):

```
Projection legend (projection-legend-v1), not a knowledge taxonomy:
Closed legend_role values: observe, compare, evidence, time, place, learning_place, habit, kind, sequence, setting, uncertain, safety, source, name, write, blank.
Do not emit misc, other, or a catch-all bucket. Do not invent required dinosaur fields (Linnaean ranks, body mass, three-view).
coverage_facet remains entity knowledge faces (recognition, appearance, physical_features, habits, environment, safety, care).
Optional units[].legend_role only when a closed role is not implied by coverage_facet (time, place, learning_place, sequence, kind, evidence).
Empty roles stay empty. Do not fill modules by inventing claims.
```

`expand_prompt` test: `self.assertIn("projection-legend-v1", text)` and `self.assertIn("sequence", text)` and `self.assertNotIn("{{subject}}", text)`.

`submit_reply` after successful `compile_authoring_request`:

```python
from cognitive_card_server.projection_legend import ENTITY_PACK_ID, assign_legend

coverage = bundle.knowledge_core.get("coverage")
pack_id = coverage.get("coverage_pack_id") if isinstance(coverage, dict) else None
if pack_id == ENTITY_PACK_ID:
    assign_legend(bundle.knowledge_core)
```

If `assign_legend` raises, existing `except KnowledgeContractError` marks intent `failed` with that code.

New test: `_cat_reply()` already has entity facets → submit_reply still `compiled`. New test: authoring JSON with one unit, one established proposition, no `coverage_facet`, no `legend_role`, entity classification → after parse+compile gate, `LEGEND_ROLE_MISSING` / intent `failed`. Easiest: call `assign_legend` on a minimal compiled core in `test_projection_legend` already covers missing; compile test can `submit_reply` a stripped unit list if coverage kernel allows. If coverage kernel blocks first, keep the missing-role test at `assign_legend` only and compile test only checks prompt + rabbit/cat still compile.

If coverage pack requires facets, a unit without facet may fail `AUTHORING_*` first. Then do **not** add a compile-path missing-role test that fights the coverage kernel. Prompt + `assign_legend` on rabbit is enough; add compile test only for `legend_role=misc` on an otherwise valid rabbit clone unit → `LEGEND_MISC_FORBIDDEN` failed intent.

- [ ] **Step 1: Failing prompt assertion + misc unit compile test**
- [ ] **Step 2: Run `tests.test_knowledge_compile.PromptExpandTests` fail on missing string**
- [ ] **Step 3: Edit template, parse passthrough, pipeline gate**
- [ ] **Step 4: Run** `PYTHONPATH=src .venv/bin/python -m unittest tests.test_knowledge_compile tests.test_http_knowledge_compile tests.test_projection_legend tests.test_mapping_preview -v`

Expected: PASS. Template sha256 in intents will change; do not pin old digest.

**Depends on:** Task 5

---

### Task 7: Kids documentation alignment

**Files:**
- Modify: `docs/superpowers/specs/2026-09-03-projection-legend-v1-design.md` Status → `Approved for this execution tranche`
- Modify: `docs/README.md` plans table row for this file, status In Progress
- Modify: `docs/cognitive-card-os-roadmap.md` LEGEND-01: link this plan; status stays READY until server tests land, or IN PROGRESS once Task 1–6 are committed
- Modify: `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`

No server behavior change.

- [x] Update Status and maps
- [x] `bash scripts/ai/check-task-state.sh` and `bash scripts/ai/check-doc-governance.sh` from kids root
- [x] `git diff --check`

**Depends on:** Task 6 if implementation already happened in the same session; otherwise this task can run as soon as the plan exists (Status Approved + plan row). Prefer: run Task 7 when marking the spec approved at plan start, then again after server work.

---

## Spec coverage

| Spec | Task |
| --- | --- |
| §5 closed roles, no misc | 1 |
| §6 views registered not rendered | 1 (constants only) |
| §7 resolve order | 2 |
| §7.1 entity aliases | 1–2 |
| §7.2 sequence order / cycle | 3 |
| §7.3 uncertain-as-fact drawing | deferred RENDER-02 |
| §8 compile prompt | 6 |
| §8 mapping blank / empty omit | 3–5 |
| §8 IMG-01 single hero | untouched |
| §9 codes used this slice | 2–6; BURN_IN / VIEW_UNKNOWN unused |
| §10 rabbit alias convert/preview | 3, 5 |
| §11 IMG-02 / RENDER-02 | out of plan |

## Placeholder scan

No TBD. Commit steps omitted on purpose (operator-gated). `LEGEND_UNCERTAIN_AS_FACT` / burn-in explicitly deferred.
