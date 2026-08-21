# Knowledge Core Contract Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge the approved Knowledge Core architecture into project truth, then build a server-authoritative, runtime-disconnected four-object contract validated by rabbit composite, geometry progressive, and time-sensitive fixtures.

**Architecture:** The kids repository remains the authority for product architecture and task governance. A new pure `knowledge_contract` package in the server repository owns canonical object validation, cross-object closure, stage gates, and fixture identities; it has no HTTP, SQLite, subscriber-state, renderer, or production wiring. The pilot proves the four-object boundary and keeps current four-card packages operational through a `four-card` projection fixture without changing the deployed protocol.

**Tech Stack:** Markdown governance documents; Python 3.11+ standard library; frozen dataclasses; canonical JSON and SHA-256; `unittest`; Git worktrees.

**Spec:** `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md`

## Global Constraints

- Decision authority: `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md` is `Accepted`; the design Spec is `Approved`.
- Kids repository: `/Users/admin/Documents/kids-visual-learning-pack`.
- Server repository: `/Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server`.
- Server implementation base: local branch `codex/api-01-core-snapshot` at exact commit `9c1b82b`; verify this identity and a clean worktree before execution.
- Create a new isolated server worktree and branch `codex/knowledge-core-contract-v1`; never modify `.worktrees/cognitive-card-server-api-01` in place.
- Do not push the API-01 base branch or the new contract branch without separate user authorization.
- Do not add HTTP routes, database migrations, subscriber state changes, renderer code, portal code, deployment assets, or production operations.
- Do not place full Knowledge Core authority in `skills/cognitive-card-os/`; ADR-001 keeps production core authority server-side.
- Preserve API-01's executor-neutral compile/generate contract, generation input lock, final content lock, server-side digest recomputation, and immutable revisions.
- Preserve current four-card runtime and package contracts. This pilot adds a `four-card` Projection fixture; it does not replace or migrate historical packages.
- MVP persists exactly four governed objects: `knowledge-core`, `learning-spec`, `projection-spec`, and `manifest`.
- Ordinary authoring is budgeted for no more than two explicit confirmations, but this contract pilot does not implement authoring UI.
- Use Python standard library only inside `knowledge_contract`; reuse the server's canonical JSON convention: UTF-8, sorted keys, compact separators, exactly one trailing newline.
- Every validation error has a stable uppercase code and an exact object path. No validation path may silently delete required content or accept undeclared files.
- Execution commits occur only when the user's execution authorization explicitly includes commits. Otherwise stop after each verified task with an uncommitted handoff.
- Run the focused suite after every GREEN step and the complete server suite before each authorized server commit:

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## Scope Decomposition

This plan covers one independently testable tranche:

1. canonical documentation convergence in the kids repository;
2. pure four-object contract and three fixture families in the server repository;
3. evidence and handoff in the kids repository.

The following each require a later plan after this pilot passes:

- local authoring MVP and its two-confirmation interaction;
- actual four-card production-record conversion;
- server revision/current/freshness persistence and APIs;
- review queues, update scheduling, Portal browsing, Renderer families, migration, and production release.

## File Map

### Kids repository

- Modify `README.md` — describe Knowledge Core as the long-term product and four cards as one Projection.
- Modify `PROJECT_CONTEXT.md` — point canonical direction to ADR-002 and the approved design without copying dynamic progress.
- Modify `docs/cognitive-card-os-system-design.md` — replace the four-card-only product boundary with the eight logical layers, four physical objects, and compatibility transition.
- Modify `docs/cognitive-card-os-roadmap.md` — add `KNOW-02` contract pilot, update execution order, and record approval/implementation status.
- Modify `docs/README.md` — register this plan and maintain final statuses.
- Modify `docs/ai/CURRENT_TASK.md` — establish the exact execution tranche before implementation.
- Modify `docs/ai/HANDOFF.md` — record each verified task, server branch identity, commands, known failures, and next action.
- Create `docs/knowledge-core-contract-pilot-evidence.md` — record fixture coverage, field-consumption evidence, complexity-budget applicability, and deferred metrics without claiming unmeasured human timings.

### Server repository

- Create `src/cognitive_card_server/knowledge_contract/__init__.py` — public contract exports.
- Create `src/cognitive_card_server/knowledge_contract/model.py` — schema constants, frozen report types, canonical JSON, digest helpers, and stable error type.
- Create `src/cognitive_card_server/knowledge_contract/validator.py` — exact-key validation, temporal evaluation, cross-object closure, manifest construction, and publish gates.
- Create `tests/test_knowledge_contract_model.py` — canonical bytes, identity, enums, and report semantics.
- Create `tests/test_knowledge_contract_validation.py` — positive and negative unit-level contract tests.
- Create `tests/test_knowledge_contract_fixtures.py` — three vertical fixtures, four-card compatibility fixture, stage behavior, and complexity boundary tests.
- Modify `README.md` — document the internal pilot module, its non-runtime status, and focused test command.

## Normative Object Shapes

All four documents reject undeclared top-level keys.

### `cognitive-card-knowledge-core-v1`

Top-level keys:

```python
{
    "schema",
    "object_id",
    "revision",
    "sources",
    "propositions",
    "relations",
    "knowledge_units",
    "scope",
}
```

Nested records:

```python
source = {
    "source_id": SAFE_ID,
    "kind": "fixture" | "book" | "article" | "dataset" | "first_party",
    "title": str,
    "locator": str,
    "retrieved_at": UTC_TIMESTAMP,
    "creator": str,
    "published_at": UTC_TIMESTAMP | None,
    "version": str,
    "license": str,
    "usage_boundaries": list[str],
    "quality": "fixture" | "primary" | "secondary" | "tertiary",
    "valid_until": UTC_TIMESTAMP | None,
    "evidence_spans": list[{
        "span_id": SAFE_ID,
        "locator": str,
        "summary": str,
        "proposition_ids": list[SAFE_ID],
        "relation": "supports" | "limits" | "conflicts_with" | "background",
    }],
}

temporal = {
    "mode": "timeless" | "slow-changing" | "periodic" | "event-driven",
    "reviewed_at": UTC_TIMESTAMP | None,
    "review_interval_days": int | None,
    "next_review_at": UTC_TIMESTAMP | None,
    "valid_from": UTC_TIMESTAMP | None,
    "valid_until": UTC_TIMESTAMP | None,
    "expiry_behavior": "warn" | "block_publish" | "unlist_current",
    "event_triggers": list[str],
}

proposition = {
    "proposition_id": SAFE_ID,
    "canonical_claim": str,
    "claim_language": str,
    "certainty": "established" | "probable" | "uncertain" | "disputed",
    "revision": int,
    "unknowns": list[str],
    "confusion_boundary": list[str],
    "safety_scope": list[str],
    "freshness": "fresh" | "review_due" | "stale" | "expired",
    "source_ids": list[SAFE_ID],
    "source_relations": list[{
        "source_id": SAFE_ID,
        "relation": "supports" | "limits" | "conflicts_with",
        "evidence_span_ids": list[SAFE_ID],
    }],
    "temporal": temporal,
    "standing": "active" | "disputed" | "superseded",
}

relation = {
    "relation_type": "supports" | "limits" | "conflicts_with" | "part_of" | "compares_with" | "prerequisite_of" | "supersedes",
    "from_id": str,
    "to_id": str,
}

knowledge_unit = {
    "unit_id": str,
    "title": str,
    "proposition_ids": list[str],
}

scope = {
    "scope_id": str,
    "scope_type": "single" | "composite" | "progressive",
    "included_unit_ids": list[str],
    "excluded_questions": list[str],
    "unresolved_gaps": list[str],
}
```

### `cognitive-card-learning-spec-v1`

```python
{
    "schema": "cognitive-card-learning-spec-v1",
    "object_id": str,
    "revision": int,
    "knowledge_core_ref": {"object_id": str, "revision": int},
    "plan": {
        "audience_profiles": list[str],
        "languages": list[str],
        "depth": "introductory" | "intermediate" | "advanced",
        "duration_minutes": int,
        "goals": list[str],
        "usage_context": str,
        "required_unit_ids": list[str],
        "optional_unit_ids": list[str],
    },
    "path": {
        "strategy": "flat" | "hierarchical" | "progressive" | "example-first" | "concept-first" | "compare" | "inquiry" | "spiral" | "mixed",
        "nodes": list[{
            "node_id": str,
            "node_type": "content" | "example" | "question" | "exercise",
            "knowledge_unit_id": str,
            "proposition_ids": list[str],
            "goal_ids": list[str],
            "purpose": NON_BLANK_STRING,
        }],
        "edges": list[{
            "from_node_id": str,
            "to_node_id": str,
            "edge_type": "next" | "branch" | "prerequisite",
        }],
    },
}
```

### `cognitive-card-projection-spec-v1`

```python
{
    "schema": "cognitive-card-projection-spec-v1",
    "object_id": str,
    "revision": int,
    "learning_spec_ref": {"object_id": str, "revision": int},
    "blueprint": {
        "family": "four-card" | "chaptered-guide" | "progressive-exploration" | "time-sensitive-brief",
        "slots": list[{
            "slot_id": str,
            "node_ids": list[str],
            "required": bool,
        }],
    },
    "renderer_binding": {
        "renderer_id": str,
        "target_medium": str,
        "size": str,
        "platform": str,
        "capability_version": str,
        "required_capabilities": list[str],
        "optional_capabilities": list[str],
        "degraded_capabilities": list[str],
        "slot_mappings": list[{
            "slot_id": SAFE_ID,
            "component_id": SAFE_ID,
            "output_path": SAFE_RELATIVE_POSIX_PATH,
        }],
        "asset_requirements": list[{
            "asset_id": SAFE_ID,
            "kind": "font" | "image" | "audio" | "animation" | "interaction",
            "required": bool,
            "path": SAFE_RELATIVE_POSIX_PATH,
        }],
        "qa_profile": str,
    },
}
```

Projection records have no fact-text field. Display prose remains an Artifact derived from path nodes and proposition IDs; this makes “Projection added a fact” structurally rejectable.

### `cognitive-card-artifact-manifest-v1`

```python
{
    "schema": "cognitive-card-artifact-manifest-v1",
    "object_id": str,
    "revision": int,
    "lifecycle": "draft" | "candidate" | "validated" | "published" | "withdrawn",
    "downstream_health": "healthy" | "degraded" | "broken",
    "generation_input_lock_sha256": "sha256:" + 64_HEX,
    "final_content_lock_sha256": "sha256:" + 64_HEX,
    "objects": list[{
        "role": "knowledge-core" | "learning-spec" | "projection-spec",
        "path": str,
        "sha256": 64_HEX,
        "size_bytes": int,
    }],
    "artifacts": list[{
        "path": str,
        "media_type": str,
        "sha256": 64_HEX,
        "size_bytes": int,
    }],
    "qa": {
        "profile": str,
        "blocking_issue_codes": list[str],
        "accepted_warning_codes": list[str],
    },
}
```

`final_content_lock_sha256` is the SHA-256 reference of canonical JSON over the three validated upstream documents in role order. The package root is not added as a fifth governed object; manifest file records and artifact records provide closure. `source_relations.source_id` must exactly cover `source_ids`; evidence span references close on the same source and proposition. Plan/path units close on `scope.included_unit_ids`; node propositions close on that node's Knowledge Unit; node goals close on and collectively cover Plan goals. Required Path nodes are covered only by required Blueprint slots, every required slot has exactly one mapping, mapping outputs and required assets are declared Artifacts, and `manifest.qa.profile` matches Renderer Binding. Future `valid_from` warns at candidate and blocks publish; publish also requires `downstream_health == "healthy"`, while bundle validation rejects a healthy declaration when freshness issues remain.

---

### Task 1: Converge Approved Architecture into Canonical Project Documents

**Files:**

- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `docs/cognitive-card-os-system-design.md`
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `docs/README.md`
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`

**Interfaces:**

- Consumes: ADR-002 and the approved 2026-08-19 design Spec.
- Produces: one non-conflicting canonical direction and a `KNOW-02` execution ledger entry for Tasks 2–7.

- [ ] **Step 1: Establish the exact execution task before editing canonical docs**

Update `docs/ai/CURRENT_TASK.md` so its In Scope lists the seven kids files above plus the existing server parent directories `src/cognitive_card_server/` and `tests/`; list the exact planned create paths in a separate deliverables subsection so the task-state checker does not mistake not-yet-created files for missing inputs. Record server base `9c1b82b`, new branch `codex/knowledge-core-contract-v1`, zero runtime wiring, and the acceptance commands from this plan.

Run:

```bash
bash scripts/ai/check-task-state.sh
```

Expected: PASS with every referenced repository path present or explicitly identified as a planned create path.

- [ ] **Step 2: Capture the pre-change contradiction evidence**

Run:

```bash
rg -n "四个投影|固定顺序的四张卡|任何正式包都必须通过四页顺序|将一个明确的学习对象转化" README.md docs/cognitive-card-os-system-design.md docs/cognitive-card-os-roadmap.md
```

Expected: matches showing the current four-card-only product boundary. Save the exact matching sections in the HANDOFF as pre-change evidence; do not delete the legacy compatibility requirements.

- [ ] **Step 3: Update the normative system design**

Make these exact semantic changes in `docs/cognitive-card-os-system-design.md`:

- §2: product goal becomes server-managed Knowledge Core plus multiple Projection families; four-card remains the first compatible family.
- §3.1: rename the principle to “one governed Knowledge Core, multiple projections” and retain stable propositions, bilingual fact alignment, and COPY rules specifically under the `four-card` family.
- §3.2: classification becomes Knowledge Scope input, not the sole Projection router; audience/language/depth/duration move to Learning Plan.
- §3.3: final content lock covers `knowledge-core`, `learning-spec`, `projection-spec`, sources, unknowns, safety, and asset requirements.
- §4 and §6: insert the eight logical layers and the four physical objects; keep server authority and executor-neutral generation.
- §7: make age/language adaptation a Learning Plan concern, without changing facts.
- §10: replace universal four-page gates with Projection-family gates plus shared cross-object closure; retain four-card-specific QA as family rules.
- §11–13: add the `KNOW-02` pilot before local MVP/server management, and state that existing four-card runtime stays compatible during transition.

- [ ] **Step 4: Update roadmap and project entrypoints**

In `docs/cognitive-card-os-roadmap.md`:

- add `KNOW-02 | Knowledge Core four-object contract | IN PROGRESS` to the overview;
- define its dependency on ADR-002 and the API-01 snapshot base;
- define completion as pure validators plus rabbit/geometry/time fixtures, zero HTTP/DB/runtime wiring;
- place local authoring MVP, four-card converter, server revision management, and Portal as distinct later items or explicit follow-on splits;
- record the 2026-08-19 approval and plan entry in the update log;
- remove the second-computer validation from the immediate execution sequence without rewriting the historical SKILL-02 completion condition.

Update `README.md` and `PROJECT_CONTEXT.md` with the same canonical direction. Update `docs/README.md` to register this plan as `Approved` once the plan itself has been reviewed for execution.

- [ ] **Step 5: Verify documentation convergence**

Run:

```bash
bash scripts/ai/check-doc-governance.sh
bash scripts/ai/check-agent-state.sh
git diff --check
```

Expected: document governance PASS, task/handoff checks PASS, 0 failures overall; the known secret-related field-name scan may remain WARN with no high-confidence secret value.

- [ ] **Step 6: Commit only if execution authorization includes commits**

```bash
git add README.md PROJECT_CONTEXT.md docs/README.md docs/cognitive-card-os-system-design.md docs/cognitive-card-os-roadmap.md docs/ai/CURRENT_TASK.md docs/ai/HANDOFF.md docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md docs/superpowers/plans/2026-08-19-knowledge-core-contract-pilot-implementation-plan.md
git commit -m "docs(card-os): adopt knowledge core architecture"
```

Expected: one kids-repository documentation commit. If commits are not authorized, stop after verification and record the exact status in HANDOFF.

### Task 2: Add Canonical Contract Primitives

**Files:**

- Create: `src/cognitive_card_server/knowledge_contract/__init__.py`
- Create: `src/cognitive_card_server/knowledge_contract/model.py`
- Create: `tests/test_knowledge_contract_model.py`

**Interfaces:**

- Consumes: Python 3.11 standard library and the server's existing canonical JSON convention.
- Produces: `ValidationStage`, `IssueSeverity`, `ValidationIssue`, `ValidationReport`, `KnowledgeBundle`, `KnowledgeContractError`, `canonical_json()`, `parse_canonical_document()`, `sha256_hex()`, `sha256_ref()`, and `parse_utc()`.

- [ ] **Step 1: Create the isolated server worktree**

At execution time, use `superpowers:using-git-worktrees` and verify:

```bash
git -C /Users/admin/Documents/Codex/2026-07-11/new-chat/work/cognitive-card-server rev-parse codex/api-01-core-snapshot
git -C /Users/admin/Documents/kids-visual-learning-pack/.worktrees/cognitive-card-server-api-01 status --short
```

Expected: first command prints `9c1b82b` expanded to 40 hex; second command prints nothing. Create `.worktrees/cognitive-card-server-knowledge-core` from that commit on branch `codex/knowledge-core-contract-v1`. Stop if either identity or cleanliness differs.

- [ ] **Step 2: Write failing model tests**

Create `tests/test_knowledge_contract_model.py`:

```python
import unittest
from datetime import datetime, timezone

from cognitive_card_server.knowledge_contract.model import (
    IssueSeverity,
    KnowledgeBundle,
    ValidationIssue,
    ValidationReport,
    ValidationStage,
    canonical_json,
    parse_utc,
    sha256_ref,
)


class KnowledgeContractModelTests(unittest.TestCase):
    def test_canonical_json_is_compact_sorted_and_newline_terminated(self) -> None:
        self.assertEqual(canonical_json({"b": 2, "a": 1}), b'{"a":1,"b":2}\n')

    def test_sha256_ref_uses_canonical_bytes(self) -> None:
        self.assertEqual(
            sha256_ref({"b": 2, "a": 1}),
            "sha256:e8d38819d39f705646bfb643368eca78f7db476c16471dbc33b941b27326410d",
        )

    def test_report_blocks_only_error_severity(self) -> None:
        warning = ValidationIssue("REVIEW_DUE", "knowledge-core.propositions[0]", IssueSeverity.WARNING)
        error = ValidationIssue("MISSING_SOURCE", "knowledge-core.propositions[0]", IssueSeverity.ERROR)
        self.assertFalse(ValidationReport((warning,)).blocked)
        self.assertTrue(ValidationReport((warning, error)).blocked)

    def test_parse_utc_rejects_non_utc_or_impossible_timestamp(self) -> None:
        self.assertEqual(parse_utc("2026-08-19T00:00:00Z"), datetime(2026, 8, 19, tzinfo=timezone.utc))
        for value in ("2026-08-19", "2026-02-30T00:00:00Z", "2026-08-19T08:00:00+08:00"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "UTC_TIMESTAMP_REQUIRED"):
                parse_utc(value)
```

The pinned digest is SHA-256 of the exact bytes `b'{"a":1,"b":2}\n'` and was independently recomputed while writing this plan.

- [ ] **Step 3: Verify RED**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model -v
```

Expected: import failure because `cognitive_card_server.knowledge_contract` does not exist.

- [ ] **Step 4: Implement the minimal model API**

Use these exact public types in `model.py`:

```python
class ValidationStage(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    PUBLISH = "publish"


class IssueSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    severity: IssueSeverity
    detail: str = ""


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def blocked(self) -> bool:
        return any(issue.severity is IssueSeverity.ERROR for issue in self.issues)


@dataclass(frozen=True)
class KnowledgeBundle:
    knowledge_core: dict[str, object]
    learning_spec: dict[str, object]
    projection_spec: dict[str, object]
    manifest: dict[str, object]
    artifacts: Mapping[str, bytes]
```

Add exact schema constants, `KnowledgeContractError(code, path="", detail="")`, canonical bytes, SHA-256 helpers, strict `sha256:<64hex>` validation, and real UTC parsing. `parse_canonical_document(content, expected_schema=...)` must reject non-UTF-8, non-object JSON, noncanonical bytes, and the wrong schema with stable codes. Export only these public names from `__init__.py`.

- [ ] **Step 5: Verify GREEN and complete suite**

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected: focused tests PASS; complete suite has no new failures. If the two previously recorded real-uvicorn tests still fail, verify the same failures on base `9c1b82b` and record them as baseline, not GREEN.

- [ ] **Step 6: Commit if authorized**

```bash
git add src/cognitive_card_server/knowledge_contract tests/test_knowledge_contract_model.py
git commit -m "feat(core): add knowledge contract primitives"
```

### Task 3: Validate Knowledge Core, Scope, and Temporal State

**Files:**

- Create: `src/cognitive_card_server/knowledge_contract/validator.py`
- Create: `tests/test_knowledge_contract_validation.py`

**Interfaces:**

- Consumes: model API from Task 2 and `cognitive-card-knowledge-core-v1` shape.
- Produces: `validate_knowledge_core(document, *, stage, now) -> ValidationReport` and reusable exact-key/ID/reference helpers kept private to `validator.py`.

- [ ] **Step 1: Write failing Knowledge Core tests**

Create a minimal `valid_core()` factory inside `tests/test_knowledge_contract_validation.py`. It must contain one source, one proposition, one unit, and a `single` scope using the exact shapes in this plan. Define `NOW = datetime(2026, 8, 19, tzinfo=timezone.utc)` and this assertion helper:

```python
def assert_issue(
    self,
    core: dict[str, object],
    code: str,
    stage: ValidationStage,
    severity: IssueSeverity = IssueSeverity.ERROR,
) -> None:
    report = validate_knowledge_core(core, stage=stage, now=NOW)
    self.assertIn((code, severity), {(issue.code, issue.severity) for issue in report.issues})
```

`conflicting_core_without_supersession()` clones `valid_core()`, adds a second proposition with a distinct ID and the same source, then adds one `conflicts_with` relation between the two active propositions without a `supersedes` relation. Add tests:

```python
def test_valid_single_scope_passes_candidate_validation(self) -> None:
    report = validate_knowledge_core(valid_core(), stage=ValidationStage.CANDIDATE, now=NOW)
    self.assertFalse(report.blocked)

def test_missing_source_blocks_candidate(self) -> None:
    core = valid_core()
    core["propositions"][0]["source_ids"] = ["src_missing"]
    self.assert_issue(core, "MISSING_SOURCE_REFERENCE", ValidationStage.CANDIDATE)

def test_scope_cannot_reference_unknown_unit(self) -> None:
    core = valid_core()
    core["scope"]["included_unit_ids"] = ["unit_missing"]
    self.assert_issue(core, "MISSING_UNIT_REFERENCE", ValidationStage.CANDIDATE)

def test_expired_block_publish_is_warning_for_candidate_and_error_for_publish(self) -> None:
    core = valid_core()
    core["propositions"][0]["temporal"].update({
        "mode": "periodic",
        "valid_until": "2026-08-18T00:00:00Z",
        "expiry_behavior": "block_publish",
    })
    self.assert_issue(core, "KNOWLEDGE_EXPIRED", ValidationStage.CANDIDATE, IssueSeverity.WARNING)
    self.assert_issue(core, "KNOWLEDGE_EXPIRED", ValidationStage.PUBLISH, IssueSeverity.ERROR)

def test_unresolved_conflict_blocks_publish(self) -> None:
    core = conflicting_core_without_supersession()
    self.assert_issue(core, "UNRESOLVED_PROPOSITION_CONFLICT", ValidationStage.PUBLISH)
```

- [ ] **Step 2: Verify RED**

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_validation -v
```

Expected: import failure for `validator.validate_knowledge_core`.

- [ ] **Step 3: Implement exact structural and temporal validation**

Implement fail-closed checks for:

- exact keys and exact schema;
- safe IDs matching `^[a-z][a-z0-9._-]{2,127}$`;
- unique source/proposition/unit IDs;
- all proposition source references;
- all unit proposition references;
- scope included units and scope type;
- relation endpoints and allowed relation types;
- conflict pairs lacking a superseding or standing resolution;
- temporal field combinations and real UTC timestamps;
- `review_due` as warning, `expired + block_publish` as candidate warning/publish error, and `expired + unlist_current` as publish error;
- empty `unresolved_gaps` at publish stage.

Sort issues deterministically by `(path, code, severity.value, detail)` before returning the report.

- [ ] **Step 4: Verify GREEN**

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation -v
```

Expected: all focused tests PASS.

- [ ] **Step 5: Add negative closure coverage**

Add tests for duplicate IDs, unknown relation endpoints, invalid policy-field combinations, non-real timestamps, a proposition with no sources, a unit with no propositions, and undeclared fields such as `card_text` inside a proposition. Run the focused suite again and require PASS.

- [ ] **Step 6: Commit if authorized**

```bash
git add src/cognitive_card_server/knowledge_contract/validator.py tests/test_knowledge_contract_validation.py
git commit -m "feat(core): validate knowledge scope and freshness"
```

### Task 4: Validate Learning Plan, Learning Path, and Projection Fidelity

**Files:**

- Modify: `src/cognitive_card_server/knowledge_contract/validator.py`
- Modify: `tests/test_knowledge_contract_validation.py`

**Interfaces:**

- Consumes: a structurally valid Knowledge Core from Task 3.
- Produces: `validate_learning_spec(document, *, knowledge_core, stage) -> ValidationReport` and `validate_projection_spec(document, *, knowledge_core, learning_spec, stage) -> ValidationReport`.

- [ ] **Step 1: Write failing Learning Spec tests**

Add `valid_learning_spec(core)` with one content node. `progressive_learning_spec_with_cycle(core)` adds a second node plus prerequisite edges in both directions. Define `assert_learning_issue()` to call `validate_learning_spec(..., knowledge_core=valid_core(), stage=ValidationStage.CANDIDATE)` and match the issue code/severity exactly. Add tests for:

```python
def test_learning_spec_required_units_are_covered(self) -> None:
    spec = valid_learning_spec(valid_core())
    spec["path"]["nodes"] = []
    self.assert_learning_issue(spec, "REQUIRED_UNIT_NOT_COVERED")

def test_learning_path_rejects_prerequisite_cycle(self) -> None:
    spec = progressive_learning_spec_with_cycle(valid_core())
    self.assert_learning_issue(spec, "PREREQUISITE_CYCLE")

def test_example_node_must_bind_existing_propositions(self) -> None:
    spec = valid_learning_spec(valid_core())
    spec["path"]["nodes"][0]["proposition_ids"] = ["prop_missing"]
    self.assert_learning_issue(spec, "MISSING_PROPOSITION_REFERENCE")
```

- [ ] **Step 2: Verify RED, implement, and verify GREEN**

Run the focused test and expect attribute/import failure. Implement exact-key checks, core revision binding, required/optional unit disjointness, node/reference closure, unique nodes, valid edge endpoints, DFS cycle detection for prerequisite edges, and non-empty goals/languages/audiences. Re-run and require PASS.

- [ ] **Step 3: Write failing Projection tests**

Add `valid_projection_spec(learning_spec)` with one required slot, required capability `text-content`, no optional or degraded capabilities, and QA profile `knowledge-contract-pilot-v1`. Define `assert_projection_issue()` to call `validate_projection_spec(..., knowledge_core=valid_core(), learning_spec=valid_learning_spec(valid_core()), stage=ValidationStage.CANDIDATE)` and match the issue code/severity exactly. Add tests:

```python
def test_required_path_node_must_be_bound_to_projection_slot(self) -> None:
    projection = valid_projection_spec(valid_learning_spec(valid_core()))
    projection["blueprint"]["slots"] = []
    self.assert_projection_issue(projection, "REQUIRED_NODE_UNBOUND")

def test_projection_rejects_fact_text_escape_hatch(self) -> None:
    projection = valid_projection_spec(valid_learning_spec(valid_core()))
    projection["blueprint"]["fact_text"] = "untracked claim"
    self.assert_projection_issue(projection, "UNDECLARED_FIELD")

def test_required_capability_cannot_be_silently_degraded(self) -> None:
    projection = valid_projection_spec(valid_learning_spec(valid_core()))
    projection["renderer_binding"]["required_capabilities"] = ["required-content"]
    projection["renderer_binding"]["degraded_capabilities"] = ["required-content"]
    self.assert_projection_issue(projection, "REQUIRED_CAPABILITY_DEGRADED")
```

- [ ] **Step 4: Verify RED, implement, and verify GREEN**

Implement learning revision binding, family enum validation, unique slot IDs, node closure, required-node coverage, required/optional capability disjointness, and `degraded_capabilities` as a subset of optional capabilities only. Required path nodes are nodes whose `knowledge_unit_id` appears in `plan.required_unit_ids`. A Projection can only select path node IDs; any prose or fact field is an undeclared-field error. Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_validation -v
```

Expected: PASS.

- [ ] **Step 5: Commit if authorized**

```bash
git add src/cognitive_card_server/knowledge_contract/validator.py tests/test_knowledge_contract_validation.py
git commit -m "feat(core): validate learning and projection closure"
```

### Task 5: Build and Validate the Artifact Manifest

**Files:**

- Modify: `src/cognitive_card_server/knowledge_contract/validator.py`
- Modify: `tests/test_knowledge_contract_validation.py`

**Interfaces:**

- Consumes: three valid upstream documents plus `artifacts: Mapping[str, bytes]`.
- Produces: `final_content_lock(knowledge_core, learning_spec, projection_spec) -> str`, `build_manifest(...) -> dict[str, object]`, `validate_manifest(bundle, *, stage) -> ValidationReport`, and `validate_bundle(bundle, *, stage, now) -> ValidationReport`.

- [ ] **Step 1: Write failing manifest construction test**

```python
def test_manifest_binds_three_objects_and_artifacts(self) -> None:
    core = valid_core()
    learning = valid_learning_spec(core)
    projection = valid_projection_spec(learning)
    artifacts = {"artifacts/outline.txt": b"fixture outline\n"}
    manifest = build_manifest(
        object_id="manifest.fixture",
        revision=1,
        lifecycle="candidate",
        generation_input_lock_sha256="sha256:" + "1" * 64,
        knowledge_core=core,
        learning_spec=learning,
        projection_spec=projection,
        artifacts=artifacts,
        qa_profile="knowledge-contract-pilot-v1",
    )
    self.assertEqual([record["role"] for record in manifest["objects"]], [
        "knowledge-core", "learning-spec", "projection-spec"
    ])
    self.assertEqual(manifest["final_content_lock_sha256"], final_content_lock(core, learning, projection))
```

- [ ] **Step 2: Verify RED and implement deterministic construction**

Expected RED: `build_manifest` missing. Construct object file records in fixed role order and artifact records in UTF-8 path-byte order. Use paths `knowledge-core.json`, `learning-spec.json`, and `projection-spec.json`. Validate safe relative POSIX paths with no empty, dot, parent, backslash, absolute, or NUL component.

Implement the final lock exactly as:

```python
def final_content_lock(knowledge_core, learning_spec, projection_spec) -> str:
    return sha256_ref([
        {"role": "knowledge-core", "document": knowledge_core},
        {"role": "learning-spec", "document": learning_spec},
        {"role": "projection-spec", "document": projection_spec},
    ])
```

- [ ] **Step 3: Add manifest negative tests**

Cover:

- wrong object digest or size;
- missing one of the three object roles;
- duplicate role or path;
- wrong final content lock;
- undeclared artifact bytes;
- declared artifact missing from bytes;
- artifact digest/size mismatch;
- path traversal and symlink-shaped paths;
- publish lifecycle with blocking QA issue codes;
- candidate lifecycle with explicit warning codes;
- noncanonical serialized manifest bytes.

- [ ] **Step 4: Implement bundle validation and stage gates**

`validate_bundle()` must concatenate all layer reports, verify manifest closure, sort issues deterministically, and never mutate inputs. `PUBLISH` stage requires lifecycle `validated` or `published`, at least one artifact, no blocking QA codes, fresh/review-acceptable critical propositions, complete required-node binding, and a matching final content lock. `CANDIDATE` allows explicit temporal warnings and unresolved noncritical warning codes but still rejects broken references and digest mismatches.

- [ ] **Step 5: Verify focused and complete suites**

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected: focused PASS; complete suite has no new failure relative to base.

- [ ] **Step 6: Commit if authorized**

```bash
git add src/cognitive_card_server/knowledge_contract/validator.py tests/test_knowledge_contract_validation.py
git commit -m "feat(core): bind knowledge artifact manifests"
```

### Task 6: Add the Three Vertical Fixtures and Four-Card Compatibility Case

**Files:**

- Create: `tests/test_knowledge_contract_fixtures.py`
- Modify: `README.md`

**Interfaces:**

- Consumes: public model/validator APIs from Tasks 2–5.
- Produces: fixture factories `rabbit_composite_bundle()`, `geometry_progressive_bundle()`, `time_sensitive_bundle(*, revision, reviewed_at, valid_until)`, and `four_card_bundle()`.

- [ ] **Step 1: Write the rabbit composite fixture**

Create sources and propositions for fixture-only statements, using `fixture://rabbit/reference` so the test does not claim current real-world sourcing. Define units `unit.rabbit.appearance`, `unit.rabbit.classification`, `unit.rabbit.anatomy`, and `unit.rabbit.care`; scope type is `composite`; path strategy is `hierarchical`; Projection family is `chaptered-guide`. Fixture factories that are expected to pass `PUBLISH` must build manifests with lifecycle `validated`.

Test:

```python
def test_rabbit_composite_bundle_is_publishable(self) -> None:
    report = validate_bundle(rabbit_composite_bundle(), stage=ValidationStage.PUBLISH, now=NOW)
    self.assertEqual((), report.issues)
```

Expected initial RED: fixture factory missing.

- [ ] **Step 2: Write the geometry progressive fixture**

Define units `unit.geometry.plane`, `unit.geometry.solid`, and `unit.geometry.multidimensional`; connect their key propositions with `prerequisite_of`; use `progressive` scope and path; use `progressive-exploration` Projection.

Tests must prove:

- the valid sequence publishes;
- reversing a prerequisite edge to form a cycle returns `PREREQUISITE_CYCLE`;
- an introductory Plan may omit the advanced unit only when that unit is optional;
- changing only Projection family does not change `sha256_ref(knowledge_core)`.

- [ ] **Step 3: Write the time-sensitive fixture**

Use a synthetic public-venue schedule claim with `fixture://venue/schedule`, never a real venue. Revision 1 has `periodic`, `valid_until=2026-08-18T00:00:00Z`, and `block_publish`. Revision 2 contains both the old proposition marked `superseded` and a new active proposition with a new source/review timestamp and future validity; its `supersedes` relation therefore has two endpoints present in the same Knowledge Core revision.

Tests:

```python
def test_expired_revision_stays_candidate_but_cannot_publish(self) -> None:
    bundle = time_sensitive_bundle(revision=1, reviewed_at="2026-08-01T00:00:00Z", valid_until="2026-08-18T00:00:00Z")
    candidate = validate_bundle(bundle, stage=ValidationStage.CANDIDATE, now=NOW)
    published = validate_bundle(bundle, stage=ValidationStage.PUBLISH, now=NOW)
    self.assertIn("KNOWLEDGE_EXPIRED", [issue.code for issue in candidate.issues])
    self.assertFalse(candidate.blocked)
    self.assertTrue(published.blocked)

def test_reviewed_revision_gets_new_identity_and_publishes(self) -> None:
    old = time_sensitive_bundle(revision=1, reviewed_at="2026-08-01T00:00:00Z", valid_until="2026-08-18T00:00:00Z")
    new = time_sensitive_bundle(revision=2, reviewed_at="2026-08-19T00:00:00Z", valid_until="2026-09-19T00:00:00Z")
    self.assertNotEqual(old.manifest["final_content_lock_sha256"], new.manifest["final_content_lock_sha256"])
    self.assertFalse(validate_bundle(new, stage=ValidationStage.PUBLISH, now=NOW).blocked)
```

- [ ] **Step 4: Add four-card compatibility fixture**

Use the same four-object contract with Projection family `four-card`, four required slots in exact order `cn-observation`, `en-observation`, `cn-knowledge`, `en-knowledge`, and required Renderer capability `print-a4`. Bind observation and knowledge slots only to path nodes; do not duplicate factual text in the Projection.

Test exact slot order, shared proposition IDs across CN/EN path nodes, and unchanged Knowledge Core digest when Renderer Binding changes from `text-faithful` to `print-a4`.

- [ ] **Step 5: Verify all fixtures and regression suite**

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_fixtures -v
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected: fixture and focused suites PASS; complete suite has no new failures.

- [ ] **Step 6: Document the non-runtime pilot and commit if authorized**

Add to server `README.md`:

```markdown
## Knowledge Contract Pilot

`cognitive_card_server.knowledge_contract` is a pure validation pilot for the approved four-object Knowledge Core model. It is not connected to HTTP, SQLite, subscriber jobs, rendering, or production publication. Run it with:

`PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures -v`
```

Then, if authorized:

```bash
git add src/cognitive_card_server/knowledge_contract tests/test_knowledge_contract_fixtures.py README.md
git commit -m "test(core): add knowledge contract pilot fixtures"
```

### Task 7: Record Pilot Evidence and Close the Tranche

**Files:**

- Create: `docs/knowledge-core-contract-pilot-evidence.md`
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `docs/README.md`
- Modify: `docs/ai/CURRENT_TASK.md`
- Modify: `docs/ai/HANDOFF.md`

**Interfaces:**

- Consumes: verified server commits or verified uncommitted diff, focused/full test output, and Task 1 canonical docs.
- Produces: reviewable evidence, truthful roadmap state, and an exact next action for the local authoring MVP plan.

- [ ] **Step 1: Write the evidence document from actual outputs**

Use this exact structure and replace bracketed labels with actual measured values before saving; do not retain bracket characters in the final file:

```markdown
# Knowledge Core Contract Pilot Evidence

## Identity

- Server branch:
- Base commit:
- Final commit or uncommitted diff identity:

## Fixture Results

| Fixture | Scope | Path | Projection | Candidate | Publish | Negative gates |
| --- | --- | --- | --- | --- | --- | --- |
| Rabbit composite | composite | hierarchical | chaptered-guide | result | result | result |
| Geometry progressive | progressive | progressive | progressive-exploration | result | result | result |
| Time-sensitive revision 1/2 | single | flat | time-sensitive-brief | result | result | result |
| Four-card compatibility | single | mixed | four-card | result | result | result |

## Contract Boundary Evidence

- Four governed objects:
- Projection changes leave Knowledge Core digest unchanged:
- Expired knowledge cannot publish and is not overwritten:
- Undeclared fact fields and artifact files are rejected:
- HTTP/DB/runtime integration diff:

## Complexity Budget

- Explicit confirmation count: not measured in this contract-only tranche; measured by the later local authoring MVP.
- Human governance time: not measured in this contract-only tranche; measured by the later local authoring MVP.
- Required fields consumed by validation or identity:
- Repeated warnings ignored by users: not measurable without the authoring MVP.
- General infrastructure added beyond fixture needs:

## Verification

- Focused command and result: `PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures -v` — 2026-08-21 fresh PASS, 128 tests.
- Full command and result: `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 2026-08-21 fresh WARN, 389 tests / 5 import errors; not a full PASS.
- Baseline comparison for any existing failure: the same five HTTP-test imports fail because this no-install environment lacks `fastapi`/`httpx`; there is no new failure category relative to the recorded base-environment baseline.
```

The text explicitly distinguishes measured contract evidence from interaction metrics deferred to the local MVP; it must not invent confirmation counts or human timings.

- [ ] **Step 2: Confirm zero runtime wiring**

Run in the server worktree:

```bash
git diff --name-only 9c1b82b...HEAD
git diff --name-only
rg -n "knowledge_contract" src/cognitive_card_server/http src/cognitive_card_server/subscriber src/cognitive_card_server/auth
```

Expected: the union of committed and uncommitted diff names contains only `knowledge_contract`, its tests, and server README; `rg` returns no runtime reference.

- [ ] **Step 3: Run final server and kids verification**

Server:

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
git status --short
```

Kids:

```bash
bash scripts/ai/check-doc-governance.sh
bash scripts/ai/check-agent-state.sh
git diff --check
git status --short
```

Expected: focused contract suite PASS; no new server regression relative to base; kids checks have 0 failures, with any existing field-name warning reported rather than suppressed.

- [ ] **Step 4: Update status without overstating completion**

Mark `KNOW-02` `DONE` only if all four fixtures and all negative gates pass, zero runtime wiring is proven, actual verification counts are synchronized across canonical evidence/status documents, and the final scoped re-review has no remaining Critical or Important finding. Keep the interaction complexity metrics open for the local authoring MVP. Set `docs/ai/CURRENT_TASK.md` to `Done` for this tranche and make HANDOFF's Exact Next Action: write and review the separate local authoring MVP plan; do not begin it automatically.

- [ ] **Step 5: Commit kids evidence only if authorized**

```bash
git add docs/knowledge-core-contract-pilot-evidence.md docs/cognitive-card-os-roadmap.md docs/README.md docs/ai/CURRENT_TASK.md docs/ai/HANDOFF.md
git commit -m "docs(card-os): record knowledge contract pilot evidence"
```

## Plan Self-Review Checklist

- [ ] Every approved Spec section maps to this tranche or to an explicitly named later plan.
- [ ] Four governed objects and eight logical layers remain distinct.
- [ ] Server authority, two locks, executor neutrality, and immutable revisions are preserved.
- [ ] No Task adds HTTP, DB, runtime, renderer, Portal, migration, deployment, or second-computer work.
- [ ] Every code-producing Task has an explicit RED command, minimal interface, GREEN command, and regression command.
- [ ] Function names and object field names are identical across Tasks 2–6.
- [ ] Rabbit, geometry, time-sensitive, and four-card fixtures have distinct acceptance behavior.
- [ ] Interaction metrics are not fabricated in a contract-only tranche.
- [ ] Commit and push boundaries remain subject to explicit authorization.
