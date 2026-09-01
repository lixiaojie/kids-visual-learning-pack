# KNOW-03 Knowledge Source Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is a **large** plan: expand Phase N to full TDD steps only when that phase is next.

**Goal:** Make Knowledge Core fail-closed on completeness and accuracy for seven typical learning objects, using versioned coverage plugins rather than a fifth governed file or a four-card template.

**Architecture:** A `coverage` package in the server loads JSON plugins (record-shape, intake, accuracy kernel, form packs, subtype overrides, domain overlays). `compile_authoring_request` still emits the four objects; the host then selects a pack and, when enforced, rejects incomplete or unsourced cores. Plugin identity is stored as optional fields inside `knowledge-core`, not as a new top-level object.

**Tech Stack:** Python 3 unittest, existing `knowledge_contract` exact-key validators, `classification-registry-v1`, JSON plugin files hashed by raw bytes.

**Plan size:** Large (8 tasks, 4 phases, incremental expansion)

**Spec:** `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md`

## Global Constraints

- Kids repo governs product docs; server implementation is `.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1`. Do not merge server `main`, do not push, do not add `uv.lock` or `outputs/`.
- Do not change four-object **filenames** (`knowledge-core.json`, `learning-spec.json`, `projection-spec.json`, `manifest.json`). Do not change v1 FACT keys or packet contract.
- Do not implement WB-02, WB-03, API-01, ChatGPT/web search, or compile-time HTTP fetch of locators.
- Do not reload production knowledge-library, gallery, or Nginx.
- `spider-gwen` stays in server `examples/authoring/` tests only. Never publish it, never seed production library, never add kids-world / PORTAL / miniprogram paths that load it.
- `projection` on suite authoring JSON remains `{}`.
- Commit server or kids changes only when the operator explicitly asks in that session.
- Existing `_rabbit_request` / geometry / schedule fixtures that omit `coverage_facet` are **legacy**: coverage required-bar is skipped (may warn). Suite slugs always enforce. Default `entity` pack is `required` only when the request already uses the record-shape keys (`coverage_facet` or `identity`).
- Do not overload proposition `standing` (`active` / `disputed` / `superseded`). Fiction uses new `epistemic_mode`: `real-world` | `fictional` (spec’s “standing=fictional 或等价”).
- Unresolved coverage facets that must persist as `scope.unresolved_gaps` cannot compile at default `PUBLISH` (existing `UNRESOLVED_GAPS` gate). Suite fixtures that still have gaps compile with `stage=CANDIDATE`. Rabbit after split should be fully sourced and stay `PUBLISH`.
- Focused server command after each GREEN step:

```bash
cd /Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core
PYTHONPATH=src python3 -m unittest tests.test_coverage_host tests.test_classification_registry tests.test_knowledge_contract_authoring -v
```

Before an authorized server commit, also run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## File Map

### Server (knowledge-pipeline-v1 worktree)

| Path | Responsibility |
| --- | --- |
| `src/cognitive_card_server/coverage/__init__.py` | Public exports |
| `src/cognitive_card_server/coverage/host.py` | Load plugins, select pack/override, later run gates |
| `src/cognitive_card_server/coverage/plugins/packs/*.v1.json` | One file per `primary_form` |
| `src/cognitive_card_server/coverage/plugins/overrides/arts.entity.fictional-character.v1.json` | Gwen pack |
| `src/cognitive_card_server/coverage/plugins/overlays/*.v1.json` | Domain overlays |
| `src/cognitive_card_server/coverage/plugins/kernels/accuracy-kernel-v1.json` | Kernel identity |
| `src/cognitive_card_server/coverage/plugins/shapes/record-shape-v1.json` | Record-shape identity |
| `src/cognitive_card_server/coverage/plugins/intake/source-intake-*.v1.json` | manual enabled; verify defined; search disabled |
| `src/cognitive_card_server/classification/registry.py` | `fictional-character` subtype; later enabled cells |
| `src/cognitive_card_server/knowledge_contract/authoring.py` | Optional record-shape keys; independent `retrieved_at`; hook host |
| `src/cognitive_card_server/knowledge_contract/validator.py` | Optional Core keys for identity, coverage stamp, fact_type, etc. |
| `examples/authoring/rabbit-real.json` | Split care/safety; facets; identity; intake |
| `examples/authoring/heptapleurum-arboricola.json` | Plant entity suite |
| `examples/authoring/tyrannosaurus-rex.json` | Paleontology overlay |
| `examples/authoring/forbidden-city.json` | Place pack |
| `examples/authoring/four-crossings-chishui.json` | Event pack |
| `examples/authoring/newton-first-law.json` | Rule-principle pack |
| `examples/authoring/spider-gwen.json` | Override pack; local only |
| `tests/test_coverage_host.py` | Plugin load, override, no-network |
| `tests/test_coverage_compile.py` | Kernel, entity bar, suite, negatives, legacy skip |
| `tests/test_classification_registry.py` | New subtype; later enabled cells |

### Kids

| Path | Responsibility |
| --- | --- |
| `docs/superpowers/plans/2026-09-01-entity-knowledge-coverage-implementation-plan.md` | This plan |
| `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md` | Status Approved |
| `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/README.md`, `docs/cognitive-card-os-roadmap.md` | Execution state |

---

## Phase 1: Plugin catalog and pack selection

Full TDD steps. Does **not** yet fail authoring compiles.

### Task 1.1: Coverage plugin files and host loader

**Files:**
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/__init__.py`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/host.py`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/entity.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/material.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/place.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/structure.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/system.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/process.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/cycle.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/event.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/phenomenon.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/relationship.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/rule-principle.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/evidence-record.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/abstract-concept.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/packs/other.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/overrides/arts.entity.fictional-character.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/overlays/paleontology.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/overlays/geography-place.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/overlays/history-archaeology.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/overlays/fiction-media.v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/kernels/accuracy-kernel-v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/shapes/record-shape-v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/intake/source-intake-manual-v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/intake/source-intake-verify-v1.json`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/coverage/plugins/intake/source-intake-search-v1.json`
- Test: `.worktrees/cognitive-card-server-knowledge-core/tests/test_coverage_host.py`

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_host -v` → all pass
**Depends on:** None

**Interfaces:**
- Consumes: `sha256_hex` / file bytes; classification dict with `primary_domain`, `primary_form`, `object_subtype`
- Produces:

```python
PLUGIN_ROOT: Path  # .../coverage/plugins

@dataclass(frozen=True)
class CoveragePlugin:
    kind: str
    id: str
    version: str
    path: Path
    sha256: str  # "sha256:" + hex of raw file bytes
    document: dict[str, object]
    enforcement: str  # packs/overlays: required | defined; intake uses enabled bool

@dataclass(frozen=True)
class CoverageCatalog:
    packs: dict[str, CoveragePlugin]          # primary_form -> plugin
    overrides: dict[tuple[str, str, str], CoveragePlugin]
    overlays: dict[str, CoveragePlugin]
    kernels: dict[str, CoveragePlugin]
    shapes: dict[str, CoveragePlugin]
    intakes: dict[str, CoveragePlugin]

def load_coverage_catalog(root: Path | None = None) -> CoverageCatalog: ...

def select_coverage_pack(
    classification: dict[str, object], catalog: CoverageCatalog
) -> CoveragePlugin:
    """Override by (domain, form, subtype) else default form pack.
    Missing pack -> KnowledgeContractError("COVERAGE_PACK_GAP", ...)."""

COMPAT_TOPIC_SLUGS: frozenset[str]
# rabbit, heptapleurum-arboricola, tyrannosaurus-rex, spider-gwen,
# forbidden-city, four-crossings-chishui, newton-first-law
```

- [ ] **Step 1: Write the failing test**

Create `tests/test_coverage_host.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cognitive_card_server.coverage.host import (
    COMPAT_TOPIC_SLUGS,
    load_coverage_catalog,
    select_coverage_pack,
)
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError


def _cls(domain: str, form: str, subtype: str) -> dict[str, object]:
    return {
        "primary_domain": domain,
        "secondary_domains": [],
        "primary_form": form,
        "secondary_forms": [],
        "object_subtype": subtype,
    }


class CoverageHostTests(unittest.TestCase):
    def test_catalog_loads_every_form_pack_with_unique_sha(self) -> None:
        catalog = load_coverage_catalog()
        expected_forms = {
            "entity",
            "material",
            "place",
            "structure",
            "system",
            "process",
            "cycle",
            "event",
            "phenomenon",
            "relationship",
            "rule-principle",
            "evidence-record",
            "abstract-concept",
            "other",
        }
        self.assertEqual(expected_forms, set(catalog.packs))
        shas = [plugin.sha256 for plugin in catalog.packs.values()]
        self.assertEqual(len(shas), len(set(shas)))
        self.assertTrue(all(item.startswith("sha256:") for item in shas))
        self.assertEqual("required", catalog.packs["entity"].enforcement)
        for form, plugin in catalog.packs.items():
            if form != "entity":
                self.assertEqual("defined", plugin.enforcement)
        self.assertIn("accuracy-kernel-v1", catalog.kernels)
        self.assertIn("record-shape-v1", catalog.shapes)
        self.assertTrue(catalog.intakes["source-intake-manual-v1"].document["enabled"])
        self.assertFalse(catalog.intakes["source-intake-search-v1"].document["enabled"])
        self.assertEqual("defined", catalog.intakes["source-intake-verify-v1"].enforcement)

    def test_gwen_classification_selects_override_not_entity_facets(self) -> None:
        catalog = load_coverage_catalog()
        plugin = select_coverage_pack(
            _cls("arts", "entity", "fictional-character"), catalog
        )
        self.assertEqual("coverage-pack-fictional-character-v1", plugin.id)
        self.assertNotIn("care", plugin.document["required_facets"])
        self.assertNotIn("habits", plugin.document["required_facets"])
        self.assertIn("publication_provenance", plugin.document["required_facets"])

    def test_rabbit_classification_selects_entity_pack(self) -> None:
        catalog = load_coverage_catalog()
        plugin = select_coverage_pack(
            _cls("life", "entity", "animal/mammal"), catalog
        )
        self.assertEqual("coverage-pack-entity-v1", plugin.id)
        self.assertEqual(
            [
                "recognition",
                "appearance",
                "physical_features",
                "habits",
                "environment",
                "safety",
                "care",
            ],
            plugin.document["required_facets"],
        )

    def test_new_pack_file_is_loaded_without_schema_change(self) -> None:
        catalog = load_coverage_catalog()
        root = Path(tempfile.mkdtemp())
        packs = root / "packs"
        packs.mkdir(parents=True)
        for path in (
            Path(__file__).resolve().parents[1]
            / "src/cognitive_card_server/coverage/plugins/packs"
        ).glob("*.json"):
            (packs / path.name).write_bytes(path.read_bytes())
        extra = {
            "kind": "pack",
            "id": "coverage-pack-fixture-form-v1",
            "version": "1",
            "applies_to": {"primary_form": "fixture-form"},
            "required_facets": ["only-facet"],
            "optional_facets": [],
            "modules": {},
            "forbidden_inferences": [],
            "required_source_kinds": [],
            "enforcement": "defined",
        }
        (packs / "fixture-form.v1.json").write_text(
            json.dumps(extra) + "\n", encoding="utf-8"
        )
        loaded = load_coverage_catalog(root)
        self.assertIn("fixture-form", loaded.packs)
        self.assertEqual("only-facet", loaded.packs["fixture-form"].document["required_facets"][0])
        self.assertNotIn("fixture-form", catalog.packs)

    def test_unknown_form_is_coverage_pack_gap(self) -> None:
        catalog = load_coverage_catalog()
        with self.assertRaises(KnowledgeContractError) as ctx:
            select_coverage_pack(_cls("life", "not-a-form", "plant"), catalog)
        self.assertEqual("COVERAGE_PACK_GAP", ctx.exception.code)

    def test_compat_slugs_are_the_seven_suite_topics(self) -> None:
        self.assertEqual(
            {
                "rabbit",
                "heptapleurum-arboricola",
                "tyrannosaurus-rex",
                "spider-gwen",
                "forbidden-city",
                "four-crossings-chishui",
                "newton-first-law",
            },
            set(COMPAT_TOPIC_SLUGS),
        )

    def test_host_module_does_not_import_network_clients(self) -> None:
        import cognitive_card_server.coverage.host as host

        source = Path(host.__file__).read_text(encoding="utf-8")
        for banned in ("urllib", "http.client", "requests", "openai"):
            self.assertNotIn(banned, source)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
PYTHONPATH=src python3 -m unittest tests.test_coverage_host -v
```

Expected: FAIL with `ModuleNotFoundError: cognitive_card_server.coverage`

- [ ] **Step 3: Add plugin JSON and host**

Pack/overlay/intake documents (write each as UTF-8 JSON, one trailing newline, no key sorting requirement other than valid JSON). Shared keys for `kind=pack|overlay`: `kind`, `id`, `version`, `applies_to`, `required_facets`, `optional_facets`, `modules`, `forbidden_inferences`, `required_source_kinds`, `enforcement`.

**`plugins/packs/entity.v1.json`**

```json
{
  "kind": "pack",
  "id": "coverage-pack-entity-v1",
  "version": "1",
  "applies_to": {"primary_form": "entity"},
  "required_facets": ["recognition", "appearance", "physical_features", "habits", "environment", "safety", "care"],
  "optional_facets": ["comparison"],
  "modules": {"comparison": {"secondary_forms": ["relationship"]}},
  "forbidden_inferences": [],
  "required_source_kinds": [],
  "enforcement": "required",
  "semantic_axis_by_facet": {
    "appearance": ["visual"],
    "physical_features": ["visual", "functional"],
    "habits": ["functional", "relational"],
    "environment": ["spatial", "contextual"]
  }
}
```

**Defined form packs** (same envelope; `enforcement` is `defined`; `id` is `coverage-pack-{form}-v1`; filename `{form}.v1.json`):

| form | required_facets |
| --- | --- |
| place | locate, spatial_range, landmarks, function, visit_safety |
| structure | parts, arrangement, load_path, function, public_safety |
| system | components, interaction, flow, use_boundary |
| process | start_state, sequence, observed_change, result, safety_boundary |
| cycle | stages, sequence, loop, conditions |
| event | time_place, actors, sequence, before_after, evidence, result |
| phenomenon | observation, conditions, effect, limits |
| relationship | members, direction, roles, dependency |
| rule-principle | try_case, compare_outcome, state_rule, limits |
| evidence-record | source_type, observable_clue, provenance, uncertainty, supports |
| material | identity, properties, uses, safety |
| abstract-concept | identity, definition, example, limits, relations |
| other | `[]` |

**`plugins/overrides/arts.entity.fictional-character.v1.json`**

```json
{
  "kind": "pack",
  "id": "coverage-pack-fictional-character-v1",
  "version": "1",
  "applies_to": {
    "primary_domain": "arts",
    "primary_form": "entity",
    "object_subtype": "fictional-character"
  },
  "required_facets": ["identity", "appearance", "role", "continuity", "publication_provenance", "confusion_boundary", "ip_safety"],
  "optional_facets": [],
  "modules": {},
  "forbidden_inferences": ["real-world-biology", "real-world-husbandry"],
  "required_source_kinds": [],
  "enforcement": "required"
}
```

**Overlays** (`enforcement`: `defined` until Phase 3 wires them; files still load):

- `overlays/paleontology.v1.json` — extra facets `geologic_time`, `discovery_region`, `observable_evidence`, `reconstruction_uncertainty`; `forbidden_inferences`: `body_color`, `soft_tissue`, `sound`, `speed`, `parenting`, `feather_state` as established
- `overlays/geography-place.v1.json` — no extra facets; `forbidden_inferences`: `require-biological-appearance`
- `overlays/history-archaeology.v1.json` — extra facets already in event pack; forbidden: `invented-dialogue`, `film-as-sole-source`
- `overlays/fiction-media.v1.json` — applies_to fictional-character pack id; forbidden: `care-as-husbandry`

**Kernels / shape / intake**

- `kernels/accuracy-kernel-v1.json`: `{"kind":"kernel","id":"accuracy-kernel-v1","version":"1"}`
- `shapes/record-shape-v1.json`: `{"kind":"shape","id":"record-shape-v1","version":"1"}`
- `intake/source-intake-manual-v1.json`: `{"kind":"intake","id":"source-intake-manual-v1","version":"1","method":"manual","enabled":true,"enforcement":"required"}`
- `intake/source-intake-verify-v1.json`: method `fetch`, `enabled`: false, `enforcement`: `defined`
- `intake/source-intake-search-v1.json`: method `search`, `enabled`: false, `enforcement`: `defined`

**`host.py` essentials:** walk `packs/`, `overrides/`, `overlays/`, `kernels/`, `shapes/`, `intake/` under `root or PLUGIN_ROOT`. Load only `*.v1.json` this tranche. SHA = `"sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()`. Reject duplicate `id`. `select_coverage_pack` looks up override tuple first. Raise `KnowledgeContractError("COVERAGE_PACK_GAP", f"classification.primary_form")` when neither override nor form pack exists. Do **not** implement `{form}.v2` selection: a later upgrade is a new file + new sha; old revisions keep the sha Task 2.1 writes into Core. This task only ships and loads v1.

**`__init__.py`:** export `load_coverage_catalog`, `select_coverage_pack`, `COMPAT_TOPIC_SLUGS`, `CoverageCatalog`, `CoveragePlugin`.

- [ ] **Step 4: Re-run tests**

```bash
PYTHONPATH=src python3 -m unittest tests.test_coverage_host -v
```

Expected: PASS

- [ ] **Step 5: Commit only if the operator asked** — message: `feat: load coverage packs and fictional-character override`

---

### Task 1.2: Classification subtype for fictional character

**Files:**
- Modify: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/classification/registry.py` (`SUBTYPES["arts"]`)
- Modify: `.worktrees/cognitive-card-server-knowledge-core/tests/test_classification_registry.py`

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_classification_registry tests.test_coverage_host -v` → all pass
**Depends on:** Task 1.1 (Gwen pack exists; classification must accept the subtype)

**Interfaces:**
- Consumes: existing `validate_classification`
- Produces: `fictional-character` in `SUBTYPES["arts"]`. Cell stays `gap` until Task 3.3 enables it. Do not remove `review` on `paleontology + entity + fossil-animal`.

- [ ] **Step 1: Add failing assertion**

```python
def test_arts_fictional_character_is_a_controlled_subtype(self) -> None:
    self.assertIn("fictional-character", SUBTYPES["arts"])
    result = validate_classification(
        _classification("arts", "entity", "fictional-character")
    )
    self.assertEqual("fictional-character", result["object_subtype"])
    self.assertEqual(
        "gap", coverage_status("arts", "entity", "fictional-character")
    )
```

Also assert `paleontology + entity + dinosaur` is still not `review` (it is `gap` until Task 3.2). Keep existing fossil-animal `review` test.

- [ ] **Step 2: Run test, expect FAIL**

```bash
PYTHONPATH=src python3 -m unittest tests.test_classification_registry.ValidateClassificationTests.test_arts_fictional_character_is_a_controlled_subtype -v
```

Expected: FAIL `CLASSIFICATION_UNKNOWN` or `fictional-character` not in `SUBTYPES["arts"]`.

- [ ] **Step 3: Add `"fictional-character"` to `SUBTYPES["arts"]` in `registry.py`** (keep `visual`, `music`, `dance`, `craft`, `general`, `other`). Do not add ENABLED_CELLS yet.

- [ ] **Step 4: Re-run**

```bash
PYTHONPATH=src python3 -m unittest tests.test_classification_registry tests.test_coverage_host -v
```

Expected: PASS

- [ ] **Step 5: Commit only if asked** — `feat: add arts fictional-character subtype`

---

## Phase 2: Record shape, intake, accuracy kernel

### Task 2.1: Optional Core / authoring fields for record-shape

**Files:**
- Modify: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/knowledge_contract/validator.py`
- Modify: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/knowledge_contract/authoring.py`
- Create: `.worktrees/cognitive-card-server-knowledge-core/tests/test_coverage_compile.py`

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_knowledge_contract_authoring tests.test_coverage_host tests.test_classification_registry -v` → all pass
**Depends on:** Task 1.1

**Interfaces:**
- Consumes: existing `compile_authoring_request`, `_rabbit_request`
- Produces: optional record-shape keys compile into Core and survive `validate_bundle` / PUBLISH for a fully sourced fixture

Do **not** call accuracy kernel or fail on missing facets yet (Task 2.2 / 3.1). Do **not** write `coverage` stamp yet unless it is optional and omitted when absent.

Authoring optional keys (only when present; `_exact_keys` must allow them):

- top-level `identity`: `{names: {cn, en, scientific?}, aliases?: []}`
- top-level `excluded_questions`: `string[]`
- top-level `proposition_relations[]`: `{from_proposition_slug, to_proposition_slug, relation_type}` in `supports|limits|conflicts_with|part_of|compares_with`
- each named source: `retrieved_at`, `source_language`, `intake: {method, query?, tool?, captured_at}`
- each unit: `coverage_facet`, `question`
- each proposition: `fact_type`, `semantic_axes`, `epistemic_mode` (default `real-world` when omitted), `source_slugs` list **or** legacy `source_slug` (not both)
- evidence span: `relation` default `supports` (`supports|limits|conflicts_with|background`); `representation` default `paraphrase` (`paraphrase|locator_only`)

Validator: use `optional=` so fixtures without the new keys still exact-match. Add optional keys:

- `_UNIT_OPTIONAL_KEYS`: `coverage_facet`, `question`
- `_PROPOSITION_OPTIONAL_KEYS`: `fact_type`, `semantic_axes`, `epistemic_mode`
- `_SOURCE_OPTIONAL_KEYS`: `source_language`, `intake`
- `_EVIDENCE_SPAN_OPTIONAL_KEYS`: `representation`
- `_SCOPE_OPTIONAL_KEYS` already has `classification`; add `identity`
- `_RELATION_TYPES` already includes supports/limits/conflicts_with/part_of/compares_with

`retrieved_at` on Core sources: if request provides it, use it; else keep current authored_at copy for **legacy** requests. A request that includes `intake` or `identity` **must** provide per-source `retrieved_at` (else `RECORD_SHAPE_GAP` on that source).

Map `identity` → `scope.identity`. Map `excluded_questions` → `scope.excluded_questions` (replace the empty default list).

`source_slugs` → `source_ids` and `source_relations` with relation `supports` unless a per-item relation is supplied later.

- [ ] **Step 1: Write failing tests** in `tests/test_coverage_compile.py`

```python
from __future__ import annotations

import copy
import unittest

from cognitive_card_server.knowledge_contract.authoring import compile_authoring_request
from cognitive_card_server.knowledge_contract.model import KnowledgeContractError
from tests.test_knowledge_contract_authoring import _rabbit_request


def _shaped_request() -> dict[str, object]:
    return {
        "schema": "cognitive-card-authoring-request-v1",
        "authored_at": "2026-08-21T00:00:00Z",
        "topic": {
            "slug": "shape-probe",
            "title": "Record shape probe",
            "revision": 1,
            "scope_type": "single",
        },
        "classification": {
            "primary_domain": "life",
            "secondary_domains": [],
            "primary_form": "entity",
            "secondary_forms": [],
            "object_subtype": "animal/mammal",
        },
        "identity": {
            "names": {"cn": "探针", "en": "probe", "scientific": None},
            "aliases": [],
        },
        "excluded_questions": ["How to cook it?"],
        "sources": [
            {
                "slug": "synth",
                "kind": "article",
                "title": "Synthetic",
                "locator": "https://example.invalid/probe",
                "creator": "Fixture",
                "published_at": None,
                "version": "v1",
                "license": "fixture-only",
                "usage_boundaries": ["Synthetic test content only."],
                "quality": "secondary",
                "valid_until": None,
                "retrieved_at": "2026-08-20T00:00:00Z",
                "source_language": "en",
                "intake": {
                    "method": "manual",
                    "captured_at": "2026-08-20T00:00:00Z",
                },
            }
        ],
        "units": [
            {
                "slug": "appearance",
                "title": "Appearance",
                "coverage_facet": "appearance",
                "question": "What does it look like?",
                "propositions": [
                    {
                        "slug": "fur",
                        "claim": "Synthetic fur is short.",
                        "claim_language": "en",
                        "certainty": "established",
                        "evidence_locator": "https://example.invalid/probe#fur",
                        "evidence_summary": "Synthetic paraphrase.",
                        "unknowns": [],
                        "confusion_boundary": [],
                        "safety_scope": [],
                        "source_slug": "synth",
                        "fact_type": "property",
                        "semantic_axes": ["visual"],
                        "epistemic_mode": "real-world",
                    }
                ],
            }
        ],
        "learning": {
            "audience_profiles": ["age-5-6"],
            "languages": ["zh-CN", "en"],
            "depth": "introductory",
            "duration_minutes": 10,
            "goal": "Probe record shape.",
            "usage_context": "guided family learning",
            "strategy": "hierarchical",
        },
        "projection": {},
    }


class RecordShapeCompileTests(unittest.TestCase):
    def test_legacy_rabbit_request_still_compiles(self) -> None:
        bundle = compile_authoring_request(_rabbit_request())
        source = bundle.knowledge_core["sources"][0]
        self.assertEqual("2026-08-21T00:00:00Z", source["retrieved_at"])
        self.assertNotIn("intake", source)
        unit = bundle.knowledge_core["knowledge_units"][0]
        self.assertNotIn("coverage_facet", unit)

    def test_retrieved_at_is_not_copied_from_authored_at(self) -> None:
        bundle = compile_authoring_request(_shaped_request())
        source = bundle.knowledge_core["sources"][0]
        self.assertEqual("2026-08-20T00:00:00Z", source["retrieved_at"])
        self.assertEqual("manual", source["intake"]["method"])
        self.assertEqual(
            "探针", bundle.knowledge_core["scope"]["identity"]["names"]["cn"]
        )
        self.assertEqual(
            ["How to cook it?"],
            bundle.knowledge_core["scope"]["excluded_questions"],
        )
        unit = bundle.knowledge_core["knowledge_units"][0]
        self.assertEqual("appearance", unit["coverage_facet"])
        prop = bundle.knowledge_core["propositions"][0]
        self.assertEqual("property", prop["fact_type"])
        self.assertEqual(["visual"], prop["semantic_axes"])
        self.assertEqual("real-world", prop["epistemic_mode"])
        span = source["evidence_spans"][0]
        self.assertEqual("supports", span["relation"])
        self.assertEqual("paraphrase", span["representation"])

    def test_identity_without_retrieved_at_is_record_shape_gap(self) -> None:
        request = _shaped_request()
        del request["sources"][0]["retrieved_at"]
        with self.assertRaises(KnowledgeContractError) as ctx:
            compile_authoring_request(request)
        self.assertEqual("RECORD_SHAPE_GAP", ctx.exception.code)
```

- [ ] **Step 2: Run tests, expect FAIL** (`AUTHORING_UNDECLARED_FIELD` on identity or retrieved_at)

```bash
PYTHONPATH=src python3 -m unittest tests.test_coverage_compile -v
```

- [ ] **Step 3: Minimal authoring + validator optional-key mapping** so the three tests pass. Do not enforce coverage facets. Do not import urllib.

- [ ] **Step 4: Re-run verify command** (compile + authoring + host + classification). Expected: PASS

- [ ] **Step 5: Do not commit unless the operator asked**

---

### Task 2.2: Accuracy kernel and manual-only intake

**Files:**
- Create: `src/cognitive_card_server/coverage/accuracy.py`
- Modify: `authoring.py` `compile_authoring_request` to call kernel when coverage is in play
- Test: `tests/test_coverage_compile.py`

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile -v` → PASS
**Depends on:** Task 2.1, Task 1.1

**Interface contract:**

```python
def apply_accuracy_kernel(core: dict[str, object], catalog: CoverageCatalog) -> None:
    """Raise KnowledgeContractError with CORE_ACCURACY_GAP or INTAKE_METHOD_DISABLED.
    Never opens a socket."""

def coverage_in_play(request: dict[str, object]) -> bool:
    """True if identity/coverage_facet present or topic.slug in COMPAT_TOPIC_SLUGS."""
```

Rules from spec §5: established/probable need source_id + evidence locator; image/toy/film/generated-image cannot be the **only** source unless `epistemic_mode=fictional` **and** overlay `fiction-media` applies; `intake.method` in {search, fetch} → `INTAKE_METHOD_DISABLED` this tranche.

**Key decisions:**
- Kernel does not GET locators.
- Search intake plugin remains loaded but `enabled: false`.
- `coverage_in_play` is true if request has `identity`, any unit `coverage_facet`, or `topic.slug in COMPAT_TOPIC_SLUGS`. Legacy `_rabbit_request` is false → kernel skipped.
- When in play, after `_build_core`, call kernel then write optional `knowledge-core.coverage` stamp (ids+shas from catalog + `coverage_pack_override`). Validator: `_CORE_OPTIONAL_KEYS = {"coverage"}`.

- [ ] **Step 1: Add failing tests** to `tests/test_coverage_compile.py`:
  - `test_search_intake_is_disabled`: copy shaped request, set `intake.method=search` → `INTAKE_METHOD_DISABLED`
  - `test_film_only_source_is_accuracy_gap`: shaped request with `kind=film` as the only source, established claim, epistemic_mode real-world → `CORE_ACCURACY_GAP`
  - `test_legacy_rabbit_still_skips_kernel`: `_rabbit_request()` still compiles
  - `test_accuracy_module_has_no_network_imports`: read `accuracy.py` text, forbid urllib/http.client/requests/openai
  - `test_in_play_compile_writes_coverage_stamp`: shaped request compile has `coverage` with `coverage_pack_id` containing entity pack id

- [ ] **Step 2: Run** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile -v` expect FAIL (kernel not wired)

- [ ] **Step 3: Implement `coverage/accuracy.py` and hook `compile_authoring_request` only when `coverage_in_play`.** Do not enforce pack facets.

- [ ] **Step 4:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_knowledge_contract_authoring tests.test_coverage_host -v` → PASS

- [ ] **Step 5: Do not commit**

---

## Phase 3: Enforced packs and seven-topic suite

*Full steps will be expanded before execution. Authoring JSON must paraphrase only; no copied page text.*

### Task 3.1: Entity required bar, rabbit split, 鹅掌藤

**Files:**
- Modify: `examples/authoring/rabbit-real.json`
- Create: `examples/authoring/heptapleurum-arboricola.json`
- Modify: `classification/registry.py` — enable `("life", "entity", "plant")`
- Modify: `authoring.py` / `host.py` — run pack completeness when in play
- Test: `tests/test_coverage_compile.py`

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_knowledge_contract_authoring -v` → all pass; geometry/schedule/`_rabbit_request` still in that authoring suite
**Depends on:** Task 2.2

**Interface contract:**

```python
def apply_coverage_pack(
    core: dict[str, object],
    pack: CoveragePlugin,
    *,
    topic_slug: str,
    enforced: bool,
) -> None:
    """If enforced: every required facet has a unit or unresolved_gaps entry.
    care and safety cannot share a unit. Missing facet -> CORE_COVERAGE_GAP.
    Unknown facet -> AUTHORING_COVERAGE_UNKNOWN. Missing facet field on
    entity enforced compile -> AUTHORING_FIELD_REQUIRED.
    Missing names.cn/en -> RECORD_SHAPE_GAP.
    """
```

Rabbit mapping (existing propositions, no invented claims): recognition from class in `body-shape`; appearance `body-shape`; physical_features `hopping`/`growing-teeth`/`cecotropes`; habits `social-curious`; environment `safe-hiding`; care `hay-and-fiber`; safety `safe-handling`. Split `care-safety` unit. Identity names.cn/en/scientific as spec. `intake.method=manual`, real `retrieved_at` (use `2026-08-21T00:00:00Z` matching existing RSPCA version dates, not silent authored_at copy in compiler).

Plant: seven facets; `care` is cultivation / do-not-forage, not hay. Scientific name sourced or unresolved/`probable`. Synthetic locators must use `example.invalid` or labeled synthetic quality — never fake journal URLs.

Enable cell `("life", "entity", "plant")`.

Negatives: entity in-play without environment unit and without unresolved → `CORE_COVERAGE_GAP`; without `fact_type` → `RECORD_SHAPE_GAP`.

---

### Task 3.2: Overlays and 霸王龙 / 故宫 / 四渡赤水 / 牛顿第一定律

**Files:**
- Create: `examples/authoring/tyrannosaurus-rex.json`
- Create: `examples/authoring/forbidden-city.json`
- Create: `examples/authoring/four-crossings-chishui.json`
- Create: `examples/authoring/newton-first-law.json`
- Modify: `src/cognitive_card_server/coverage/host.py` — `select_overlay`, `apply_overlay`, suite-slug enforcement, overlay facets as known
- Modify: `src/cognitive_card_server/coverage/__init__.py` — export new symbols
- Modify: `src/cognitive_card_server/coverage/plugins/packs/place.v1.json` — add `history_context` module
- Modify: `src/cognitive_card_server/coverage/plugins/packs/rule-principle.v1.json` — `"scientific_name": "not_applicable"`
- Modify: `src/cognitive_card_server/classification/registry.py` — enable dinosaur + urban-landmark cells; do **not** change `fossil-animal` review
- Modify: `src/cognitive_card_server/knowledge_contract/authoring.py` — hook overlay; suite enforcement; optional `overlay_inference`; optional request `unresolved_gaps`
- Modify: `src/cognitive_card_server/knowledge_contract/validator.py` — optional proposition `overlay_inference` if Core persists it
- Modify: `tests/test_coverage_compile.py`, `tests/test_coverage_host.py`, `tests/test_classification_registry.py`

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_coverage_host tests.test_classification_registry tests.test_knowledge_contract_authoring -v` → all pass
**Depends on:** Task 3.1

**Do not commit.** Do not add `uv.lock`. Do not create `spider-gwen.json` (Task 3.3). Do not enable `("arts", "entity", "fictional-character")`. Do not attach `fiction-media` to T-rex / 故宫 / 四渡赤水 / 牛顿.

Copy authoring JSON **shape** from `examples/authoring/heptapleurum-arboricola.json` (identity, excluded_questions, per-source `retrieved_at` + `intake.method=manual`, per-proposition `fact_type` / `semantic_axes` / `epistemic_mode=real-world`, `projection: {}`). Paraphrase only. Synthetic locators must use `https://example.invalid/...` and `kind`/`quality`/`license` labeled fixture. No invented dialogue. No copied page text.

**Interface contract:**

```python
def select_overlay(
    classification: dict[str, object], catalog: CoverageCatalog
) -> CoveragePlugin | None:
    """Return at most one overlay.
    1. Resolve pack via select_coverage_pack.
    2. If pack.id == coverage-pack-fictional-character-v1, return the overlay
       whose applies_to.pack_id matches that id (fiction-media). Task 3.2
       fixtures must not hit this branch.
    3. Else ignore overlays that only apply via pack_id.
    4. If an overlay applies_to.primary_domain == classification.primary_domain,
       return that overlay (primary wins).
    5. Else if an overlay applies_to.primary_domain is in
       classification.secondary_domains, return that overlay
       (paleontology as secondary still applies).
    6. Else return None.
    """

def apply_overlay(
    core: dict[str, object],
    overlay: CoveragePlugin,
    *,
    topic_slug: str,
    enforced: bool,
) -> None:
    """If not enforced: return.
    Overlay required_facets must each have a unit or unresolved_gaps entry
    else CORE_COVERAGE_GAP. Overlay must not delete pack required facets
    (do not mutate pack; only add extra required).
    If a unit-referenced proposition has overlay_inference in
    overlay.forbidden_inferences and certainty == established →
    OVERLAY_INFERENCE_FORBIDDEN.
    """
```

Extend `apply_coverage_pack(..., overlay: CoveragePlugin | None = None)`: when overlay is passed, `known_facets` = pack required+optional UNION overlay required+optional. Pack **required** bar still uses only `pack.document["required_facets"]`. Without this union, T-rex units `geologic_time` / `discovery_region` / `observable_evidence` / `reconstruction_uncertainty` would be `AUTHORING_COVERAGE_UNKNOWN`.

**Suite-slug enforcement** (Global Constraints: suite slugs always enforce). In `compile_authoring_request`, when coverage is in play:

```python
enforced = pack.enforcement == "required" or topic_slug in COMPAT_TOPIC_SLUGS
overlay = select_overlay(classification, catalog)
apply_coverage_pack(core, pack, topic_slug=topic_slug, enforced=enforced, overlay=overlay)
if overlay is not None:
    apply_overlay(core, overlay, topic_slug=topic_slug, enforced=enforced)
```

Stamp `core["coverage"]` as today, plus when overlay is not None: `overlay_id`, `overlay_sha256`. T-rex/故宫 must record their domain overlay ids. T-rex and 故宫 coverage stamps must **not** contain fiction-media.

**Modules:** add to `place.v1.json`:

```json
"modules": {
  "history_context": {
    "secondary_domains": ["history-archaeology"]
  }
}
```

When `classification.secondary_forms` is non-empty, every listed form must appear in some `pack.document["modules"][*]["secondary_forms"]` else `COVERAGE_MODULE_UNKNOWN`. Same for `secondary_domains` vs `modules[*]["secondary_domains"]`. Empty secondary lists skip the check. 故宫 fixture: include `secondary_domains: ["history-archaeology"]` so the module path is live; `select_overlay` still returns geography-place (primary wins).

**Scientific name:** add `"scientific_name": "not_applicable"` to `rule-principle.v1.json`. Newton identity may omit `names.scientific` or set it null. Do not fail Newton for missing scientific. Entity biological fixtures (T-rex) keep a sourced scientific string.

**Classification cells to enable:**

- `("paleontology", "entity", "dinosaur")`
- `("geography-place", "place", "urban-landmark")`

Keep `("paleontology", "entity", "fossil-animal")` as **review**. `("history-archaeology", "event", "historical-event")` and `("physics", "rule-principle", "general")` are already enabled.

**Authoring plumbing:**

- Allow optional top-level `unresolved_gaps` (list of facet id strings) and copy into `scope.unresolved_gaps` (today hardcoded `[]`). Happy-path suite fixtures should be fully sourced PUBLISH; this key is for the Newton-missing-limits negative (omit the unit, do not add unresolved) and future CANDIDATE fixtures.
- Allow optional proposition key `overlay_inference` (string). Persist onto compiled propositions so `apply_overlay` can read it. Validator: add to proposition optional keys if Core exact-keys would reject it.

**Happy-path fixtures (PUBLISH, `projection: {}`, manual intake, `retrieved_at` `2026-08-21T00:00:00Z`):**

| File | slug | classification | pack facets | extra overlay facets | identity.cn / en / scientific | care / safety notes |
| --- | --- | --- | --- | --- | --- | --- |
| tyrannosaurus-rex.json | tyrannosaurus-rex | paleontology, entity, dinosaur | entity 7 | geologic_time, discovery_region, observable_evidence, reconstruction_uncertainty | 霸王龙 / Tyrannosaurus / Tyrannosaurus rex | care = do not keep as a pet; museum viewing distance. Do **not** mark body color / soft tissue / sound / speed / parenting / feather_state as established |
| forbidden-city.json | forbidden-city | geography-place, place, urban-landmark; secondary_domains history-archaeology | locate, spatial_range, landmarks, function, visit_safety | none from geography overlay (required_facets []) | 故宫 / Forbidden City / omit scientific | visit_safety: do not climb walls or enter closed areas. **No** care or habits units |
| four-crossings-chishui.json | four-crossings-chishui | history-archaeology, event, historical-event | time_place, actors, sequence, before_after, evidence, result | history overlay facets are the same ids — covering event facets satisfies overlay | 四渡赤水 / Four Crossings of the Chishui / omit scientific | Neutral wording; no invented dialogue; **not** film-only (use fixture text source `kind` article or similar, not film) |
| newton-first-law.json | newton-first-law | physics, rule-principle, general | try_case, compare_outcome, state_rule, limits | none | 牛顿第一定律 / Newton's first law / omit scientific | limits claim must cover idealization / approximation |

**Negatives (tests, not extra fixture files unless cloned in-memory from the JSON):**

- T-rex clone: one proposition `overlay_inference=body_color`, `certainty=established` → `OVERLAY_INFERENCE_FORBIDDEN`
- T-rex clone: drop `geologic_time` unit, no unresolved → `CORE_COVERAGE_GAP`
- 故宫 clone: add a unit `coverage_facet=care` → `AUTHORING_COVERAGE_UNKNOWN`
- 四渡赤水 clone: only source `kind=film` (and all props real-world) → `CORE_ACCURACY_GAP` (existing kernel)
- Newton clone: drop `limits` unit, no unresolved → `CORE_COVERAGE_GAP`
- Place request with `secondary_forms: ["relationship"]` → `COVERAGE_MODULE_UNKNOWN`
- `select_overlay(life+entity+plant, secondary_domains=[paleontology])` → paleontology overlay (secondary still applies)
- `select_overlay(geography-place+place+urban-landmark, secondary_domains=[history-archaeology])` → geography-place overlay, not history
- `coverage_status("paleontology", "entity", "fossil-animal")` still `review`
- Compiled T-rex/故宫 `coverage` has overlay_id of the domain overlay, not fiction-media
- `_rabbit_request()` and geometry-progressive-real still compile without overlay stamp

- [ ] **Step 1: Write failing tests** for `select_overlay` (primary, secondary paleontology, fiction-media not selected for T-rex class, geography primary beats history secondary), dinosaur/urban-landmark enabled, fossil-animal still review, then compile/negative tests listed above (JSON files may be empty placeholders first).

- [ ] **Step 2:** Run `PYTHONPATH=src python3 -m unittest tests.test_coverage_host tests.test_classification_registry tests.test_coverage_compile -v` → FAIL on new tests.

- [ ] **Step 3: Implement** host overlay selection/application, suite enforcement, place module, rule-principle scientific_name, authoring hook + overlay_inference + unresolved_gaps, classification cells, four authoring JSON files (fully sourced, paraphrase, example.invalid).

- [ ] **Step 4:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_coverage_host tests.test_classification_registry tests.test_knowledge_contract_authoring -v` → PASS. Confirm rabbit-real / heptapleurum / `_rabbit_request` still pass.

- [ ] **Step 5: Do not commit**

---

### Task 3.3: 蜘蛛侠（格温）override and isolation

**Files:**
- Create: `examples/authoring/spider-gwen.json`
- Modify: `src/cognitive_card_server/classification/registry.py` — enable `("arts", "entity", "fictional-character")`
- Modify: `src/cognitive_card_server/coverage/host.py` — `PACK_OVERRIDE_REQUIRED` when that cell has no override in catalog
- Modify: `src/cognitive_card_server/coverage/accuracy.py` — media-only fictional claims allowed **only** with fiction-media overlay
- Modify: `src/cognitive_card_server/coverage/plugins/overrides/arts.entity.fictional-character.v1.json` — `"scientific_name": "not_applicable"`
- Modify: `src/cognitive_card_server/knowledge_contract/authoring.py` — select overlay before kernel (or pass overlay into kernel) so fiction-media can narrow media-only
- Modify: `tests/test_coverage_compile.py`, `tests/test_coverage_host.py`, `tests/test_classification_registry.py`

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_coverage_host tests.test_classification_registry tests.test_knowledge_contract_authoring -v` → all pass; `rg spider-gwen tests/test_http_portal.py tests/test_http_knowledge_ops.py` exits 1
**Depends on:** Task 3.2, Task 1.2

**Do not commit.** Do not add `uv.lock`. Do not publish Gwen. Do not seed production library. Do not add kids-world / PORTAL / miniprogram / nginx paths that load `spider-gwen`. Fixture lives only under `examples/authoring/` and tests.

**Interface contract:**

```python
# select_coverage_pack: after override lookup fails,
# if (primary_domain, primary_form, object_subtype) ==
# ("arts", "entity", "fictional-character") → PACK_OVERRIDE_REQUIRED
# (do not fall through to entity seven facets).

# apply_accuracy_kernel(..., overlay: CoveragePlugin | None = None)
# media-only kinds {image, toy, film, generated-image} as sole sources:
#   epistemic_mode != fictional → CORE_ACCURACY_GAP (unchanged)
#   epistemic_mode == fictional and overlay is not None
#       and overlay.id == "domain-overlay-fiction-media-v1" → allow
#   epistemic_mode == fictional otherwise → CORE_ACCURACY_GAP
```

Call `select_coverage_pack` + `select_overlay` **before** `apply_accuracy_kernel`, then pass `overlay=` into the kernel. Pack completeness and `apply_overlay` still run after the kernel (spec §4.1 order: kernel, then pack bar, then overlay). Stamp `coverage_pack_override=true` when the override key is in `catalog.overrides` (already true for this cell once the file is loaded).

Update Task 2.2 test `test_film_only_source_is_allowed_for_fictional_mode`: entity + film-only + fictional **without** fiction-media overlay must now be `CORE_ACCURACY_GAP`. Add a Gwen-path test: story claim with film as sole source **and** fiction-media overlay compiles.

**Gwen fixture** (`spider-gwen.json`): copy shape from `heptapleurum-arboricola.json`. slug `spider-gwen`. classification `arts + entity + fictional-character`. `projection: {}`. identity names.cn=格温 (or 蜘蛛格温), names.en=Spider-Gwen / Gwen Stacy (fictional), omit scientific. Facets **only** the override pack: `identity`, `appearance`, `role`, `continuity`, `publication_provenance`, `confusion_boundary`, `ip_safety`. **No** `care` / `habits` / entity seven-facet ids.

- Story claims (powers, costume, in-story events): `epistemic_mode=fictional`. Comic/film locators allowed on those claims (`kind` film or article). Use `https://example.invalid/...` fixture locators; paraphrase only; no official style-guide dump.
- Publication facts (first appearance, creators, work title): `epistemic_mode=real-world`, bibliographic-style fixture source (`kind` article or book, **not** film-only), `certainty` established or probable.
- `continuity`: comic vs film Gwen are not one real person; unresolved or separate claims.
- `confusion_boundary`: fictional character ≠ real person.
- `ip_safety`: do not treat official costume recitation as an observation object; do not treat fight choreography as real-world instruction.
- `intake.method=manual`, `retrieved_at` `2026-08-21T00:00:00Z`.

**Isolation test:** `spider-gwen` must not appear as a substring in:
- server `tests/test_http_portal.py`
- server `tests/test_http_knowledge_ops.py`
- kids `ops/cognitive-card-server/` (walk files if the directory exists relative to the worktree: `../../ops/cognitive-card-server`)
- kids `apps/miniprogram/` (same: `../../apps/miniprogram`)
Skip a root that does not exist. The fixture path `examples/authoring/spider-gwen.json` and coverage tests **may** contain the slug.

**Other tests:**
- Compile `spider-gwen.json` at PUBLISH; `coverage_pack_id` is `coverage-pack-fictional-character-v1`; `coverage_pack_override` is true; `overlay_id` is `domain-overlay-fiction-media-v1`; required_facets of the compiled pack do not include `care` or `habits`.
- Temp catalog with packs but **without** the fictional-character override file: `select_coverage_pack(arts, entity, fictional-character)` → `PACK_OVERRIDE_REQUIRED`.
- Gwen clone with a `care` unit → `AUTHORING_COVERAGE_UNKNOWN`.
- Gwen clone: a **real-world** publication proposition whose only source is `kind=film` → `CORE_ACCURACY_GAP`.
- `coverage_status("arts", "entity", "fictional-character")` is `enabled`.
- T-rex / 故宫 still do not stamp fiction-media. `_rabbit_request` still skips coverage.

- [ ] **Step 1: Write failing tests** (cell enabled, PACK_OVERRIDE_REQUIRED, gwen compile + overlay stamp, isolation, kernel film-only tightening, care unit unknown).

- [ ] **Step 2:** Run `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_coverage_host tests.test_classification_registry -v` → FAIL on new tests.

- [ ] **Step 3: Implement** registry cell, select_coverage_pack gap, kernel overlay AND, authoring call order, override JSON scientific_name, spider-gwen.json.

- [ ] **Step 4:** Verify command above → PASS. `rg spider-gwen tests/test_http_portal.py tests/test_http_knowledge_ops.py` exits 1.

- [ ] **Step 5: Do not commit**

---

## Phase 4: Kids governance closeout

*Full steps will be expanded before execution.*

### Task 4.1: Mark spec/plan/roadmap after server tests pass

**Files (kids repo only):**
- Modify: `docs/superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md` — Status remains **Approved** (do not mark Implemented; code is uncommitted)
- Modify: `docs/README.md` — spec stays Approved; this plan status **Needs Review** until the operator accepts (do not write Implemented)
- Modify: `docs/cognitive-card-os-roadmap.md` — KNOW-03 stays **IN PROGRESS**; update the KNOW-03 section and current-slice notes with the facts below; do not mark DONE
- Modify: `docs/ai/CURRENT_TASK.md` — Status In Progress; acceptance: server Tasks 1.1–3.3 landed uncommitted; operator has not authorized commit
- Modify: `docs/ai/HANDOFF.md` — real git status and unittest counts below

**Do not** modify server worktree files. **Do not commit** kids or server. **Do not** write production install steps. **Do not** claim KNOW-03 DONE.

**Verified facts (write these numbers, do not invent):**

Server worktree `.worktrees/cognitive-card-server-knowledge-core`, branch `knowledge-pipeline-v1`, HEAD still `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`. All KNOW-03 code uncommitted. `uv.lock` untracked, leave it.

Focused coverage+authoring (2026-09-01):

```
PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_coverage_host tests.test_classification_registry tests.test_knowledge_contract_authoring -v
Ran 90 tests in ~1.2s
OK
```

Full `unittest discover -s tests`: Ran 631 tests; **FAILED (failures=2, errors=52)**. Errors: missing `fastapi` on the default interpreter (pre-existing, same class as earlier worktree limitation). Failures (related to this tranche): `tests.test_four_card_accept.AcceptCliTests.test_cli_writes_view_index` and `AcceptInputTests.test_wrong_location_fail_closed` — `ACCEPT_INPUT_TOPIC` after rabbit-real.json claim re-slice in Task 3.1. Record in HANDOFF Known Failures as related to KNOW-03 rabbit split, not fastapi.

Kids HEAD `bbefb9f4343f2ecd9d569192c2348008735d9c75` on `main`. Uncommitted: KNOW-03 spec/plan + CURRENT_TASK/HANDOFF/roadmap/README; pre-existing WB-01 ops docs; `outputs/` not in scope.

Exact Next Action: operator reviews uncommitted server KNOW-03 on `knowledge-pipeline-v1` and explicitly asks to commit (kids and server stay separate per ADR-003). Do not merge server `main`. Do not reload production. Do not implement WB-02.

- [ ] **Step 1:** Update the five kids files with the facts above. HANDOFF fields: Metadata, Summary, Completed, Changed Files, Decisions, Isolation Map, Verification Results, Known Failures, Remaining Work, Exact Next Action, Recovery Notes. CURRENT_TASK Objective still KNOW-03 closeout pending operator commit; tick focused unittest criterion; leave commit/DONE unticked.

- [ ] **Step 2:** `bash scripts/ai/check-agent-state.sh` → WARN allowed only for overdue Last Reviewed. `git diff --check` → no output, exit 0. `bash scripts/ai/check-task-state.sh` and `bash scripts/ai/check-handoff.sh` PASS.

- [ ] **Step 3: Do not commit**

---

### Task 4.2: Closed fact_type / axes and entity safety + facet-axis gates

Follow-on from whole-branch review Important leftovers (spec §4.4 closed vocab, §8.3 safety_scope, §4.4 last paragraph facet→axis). Tasks 1.1–4.1 stay as-is. Do not commit.

**Files:**
- Modify: `src/cognitive_card_server/coverage/host.py` — enforced path of `apply_coverage_pack`
- Modify: `examples/authoring/{tyrannosaurus-rex,four-crossings-chishui,newton-first-law,spider-gwen}.json` — remap illegal `fact_type` values only (do not rewrite claims)
- Modify: `tests/test_coverage_compile.py` — `_shaped_request` safety unit needs non-empty `safety_scope`; add negatives
- Modify: kids `docs/ai/HANDOFF.md` / `CURRENT_TASK.md` with real test counts after GREEN

**Verify:** `PYTHONPATH=src python3 -m unittest tests.test_coverage_compile tests.test_coverage_host tests.test_classification_registry tests.test_knowledge_contract_authoring tests.test_four_card_accept tests.test_age_language_adapter -v`

**Closed sets (verbatim spec §4.4):**

```python
FACT_TYPES = frozenset({"identity", "property", "process", "relation", "safety", "unknown_boundary"})
SEMANTIC_AXES = frozenset({
    "visual", "spatial", "temporal", "functional", "historical",
    "contextual", "relational", "entity_or_concept",
})
ENTITY_FACET_AXES = {
    "recognition": frozenset({"entity_or_concept"}),
    "appearance": frozenset({"visual"}),
    "physical_features": frozenset({"visual", "functional"}),
    "habits": frozenset({"functional", "relational"}),
    "environment": frozenset({"spatial", "contextual"}),
    "safety": frozenset({"contextual", "functional"}),
    "care": frozenset({"functional"}),
}
SAFETY_FACETS = frozenset({"safety", "visit_safety", "ip_safety", "public_safety"})
```

On **enforced** compiles only (legacy `_rabbit_request` still skips):

1. `fact_type` present (already) **and** in `FACT_TYPES` else `RECORD_SHAPE_GAP`.
2. `semantic_axes` is a non-empty list whose members are all in `SEMANTIC_AXES` else `RECORD_SHAPE_GAP`.
3. If selected pack id is `coverage-pack-entity-v1`, every **pack** required facet that has a unit must have ≥1 unit-referenced proposition whose axes intersect `ENTITY_FACET_AXES[facet]` else `CORE_COVERAGE_GAP`. Overlay extra facets (T-rex geologic_time etc.) are **not** in this table.
4. For each required facet id in `SAFETY_FACETS` that is in the selected pack's `required_facets` and not in `scope.unresolved_gaps`: ≥1 unit-referenced proposition on that facet has non-empty `safety_scope` else `CORE_COVERAGE_GAP`. `care` having `safety_scope` does **not** satisfy `safety`. Empty `safety_scope` on care is allowed; rabbit care may keep its existing notes.
5. Entity pack enforced: `scope.excluded_questions` length ≥ 1 else `RECORD_SHAPE_GAP`.

**Fixture remaps (claims unchanged):**

| Current | New |
| --- | --- |
| `evidence` | `unknown_boundary` |
| `uncertainty` | `unknown_boundary` |
| `comparison` | `relation` |
| `outcome` | `process` |
| `observation` | `property` |
| `principle` | `identity` on `state_rule`; `unknown_boundary` on `limits` |
| `provenance` | `identity` |

`_shaped_request` safety probe currently has `safety_scope: []` — give it a one-item synthetic scope so happy-path still compiles.

**Negatives** (clone `_shaped_request` unless noted):

- `fact_type="provenance"` → `RECORD_SHAPE_GAP`
- `semantic_axes=["mood"]` → `RECORD_SHAPE_GAP`
- appearance unit axes `["functional"]` only (no visual) → `CORE_COVERAGE_GAP`
- safety unit `safety_scope=[]` → `CORE_COVERAGE_GAP`
- drop all `excluded_questions` → `RECORD_SHAPE_GAP`
- `_rabbit_request()` still compiles
- rabbit-real / heptapleurum / T-rex / 故宫 / 四渡赤水 / Newton / Gwen still PUBLISH-compile
- four_card_accept + age_language_adapter still pass (do not change rabbit claim strings)

- [ ] **Step 1:** Failing tests for the five negatives and one remap compile (T-rex `unknown_boundary`).
- [ ] **Step 2:** Run focused coverage compile tests → FAIL on new tests.
- [ ] **Step 3:** Implement host checks; remap four fixture files; fix `_shaped_request` safety_scope.
- [ ] **Step 4:** Verify command → PASS. `tests.test_four_card_accept` + `tests.test_age_language_adapter` PASS.
- [ ] **Step 5: Do not commit**

---

## Spec coverage (self-review)

| Spec | Task |
| --- | --- |
| §4.1 host + override | 1.1, 3.3 |
| §4.2 plugin files / sha | 1.1 |
| §4.4 record-shape | 2.1 |
| §4.5 manual intake, no search | 2.2 |
| §5 accuracy kernel | 2.2 |
| §6 packs | 1.1 |
| §7 overlays | 3.2, 3.3 |
| §8.1–8.5 suite | 3.1–3.3 |
| §8.6 defined pack files | 1.1 |
| §9 error codes | 1.1, 2.2, 3.1–3.3 |
| AUTHOR-03/04 grandfather | 3.1 Global Constraints |
| No production / no Gwen publish | Global Constraints, 3.3, 4.1 |

## Expansion note

Before starting Phase 2, replace Task 2.1–2.2 skeletons with full TDD checkboxes (failing test source, exact `_SOURCE_KEYS` / `_UNIT_KEYS` diffs, expected unittest names). Repeat for Phase 3 authoring JSON field lists so locators stay paraphrased and sourced.
