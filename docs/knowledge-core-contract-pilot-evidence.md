# Knowledge Core Contract Pilot Evidence

## Identity

- Server branch: `codex/knowledge-core-contract-v1`.
- Base commit: `9c1b82be69df2da8348f66970a993e9c1984ce6d`.
- Final commit identity: the verified contract was later committed together with AUTHOR-01 on isolated branch `codex/knowledge-core-contract-v1` as `120e5fcc48e4e6cabb1a28678379f687553c0788`; it remains unpushed and unmerged.

## Fixture Results

| Fixture | Scope | Path | Projection | Candidate | Publish | Negative gates |
| --- | --- | --- | --- | --- | --- | --- |
| Rabbit composite | composite | hierarchical | chaptered-guide | PASS — empty Candidate report | PASS — empty Publish report | Exact four-unit composite shape is asserted; shared exact-shape, closure, and manifest gates pass. |
| Geometry progressive | progressive | progressive | progressive-exploration | PASS — empty Candidate report | PASS — empty Publish report | A closing prerequisite edge yields only `PREREQUISITE_CYCLE`; making the optional advanced unit required while omitting it yields `REQUIRED_UNIT_NOT_COVERED`. |
| Time-sensitive revision 1/2 | single | flat | time-sensitive-brief | PASS — revision 1 reports non-blocking `KNOWLEDGE_EXPIRED`; revision 2 is clean | PASS — revision 1 is blocked by `KNOWLEDGE_EXPIRED`; revision 2 is clean | Revision 2 has a different final-content identity, retains revision 1 as `superseded` with its original temporal record, and records the `supersedes` relation. |
| Four-card compatibility | single | mixed | four-card | PASS — empty Candidate report | PASS — empty Publish report | Exact required slot order and paired CN/EN proposition references are asserted; Projection canonical bytes contain no claim text, and the renderer-only change preserves the Knowledge Core digest. |

## Contract Boundary Evidence

- Four governed objects: `knowledge-core`, `learning-spec`, `projection-spec`, and `manifest`; their exact schemas, object/revision references, canonical bytes, digests, and fixed-role manifest closure are covered by the three focused modules.
- Generation-input lock: `generation_input_lock_sha256` is a required manifest field gated for a valid `sha256:` reference format; malformed or absent values fail closed at `manifest.generation_input_lock_sha256`. `test_manifest_rejects_wrong_final_lock_and_malformed_generation_lock` exercises the malformed-lock rejection.
- Final-content lock: `final_content_lock_sha256` is recomputed as the SHA-256 of canonical data with the three fixed roles, in order: `knowledge-core`, `learning-spec`, and `projection-spec`. A mismatching supplied value fails closed at `manifest.final_content_lock_sha256`; `test_manifest_rejects_wrong_final_lock_and_malformed_generation_lock` exercises that mismatch rejection.
- Projection changes leave Knowledge Core digest unchanged: `test_geometry_projection_change_preserves_knowledge_core_digest` and `test_four_card_fixture_preserves_slot_and_proposition_compatibility` pass after Projection or Renderer Binding changes and manifest rebuilds.
- Expired knowledge cannot publish and is not overwritten: `test_expired_revision_stays_candidate_but_cannot_publish` proves the Candidate warning and Publish block; `test_reviewed_revision_gets_new_identity_and_publishes` proves a new identity plus retained superseded history.
- Undeclared fact fields and artifact files are rejected: `test_undeclared_proposition_field_is_rejected_at_its_exact_path`, `test_projection_rejects_fact_text_escape_hatch`, and manifest declared-byte closure tests pass in the focused suite.
- Artifact payload bytes remain opaque to this pure-contract tranche. The pilot proves node-to-slot-to-output/asset structural trace, declared-byte digest closure, and QA-profile consistency; it does **not** prove byte-level semantic prose fidelity. That semantic check belongs to the later Renderer/QA tranche and is not claimed complete here.
- HTTP/DB/runtime integration diff: `git diff --name-only 9c1b82b...120e5fc` contains only README, the synthetic authoring example, four pure contract/authoring modules, and four focused test files. `rg -n "knowledge_contract" src/cognitive_card_server/http src/cognitive_card_server/subscriber src/cognitive_card_server/auth` returned exit 1 with no matches.

## Complexity Budget

- Explicit confirmation count: not measured in this contract-only tranche; measured by the later local authoring MVP.
- Human governance time: not measured in this contract-only tranche; measured by the later local authoring MVP.
- Spec-to-field/gate mapping below records the load-bearing families added by the final fix. It is evidence of tested consumers, not a claim that every scalar field needs a separate row:

| Spec family | Contract fields / gate | Consumer | Test evidence |
| --- | --- | --- | --- |
| Source and proposition governance | source creator/version/license/usage/quality/evidence spans; proposition revision/unknowns/confusion/safety/freshness/source relations | `validate_knowledge_core`, canonical Core/final locks | `test_source_governance_shape_and_evidence_span_closure_fail_closed`, `test_proposition_source_relations_match_sources_and_evidence`, `test_governance_fields_participate_in_core_and_final_lock_identity` |
| Knowledge Scope and Learning goals | `scope.included_unit_ids`; Plan required/optional units and goals; Path node unit/proposition/goal/purpose closure | `validate_learning_spec` | `test_learning_plan_and_path_units_must_be_inside_knowledge_scope`, `test_learning_node_proposition_must_belong_to_its_knowledge_unit`, `test_learning_node_goal_references_and_plan_goal_coverage_close` |
| Renderer and Artifact binding | required node → required slot; slot mapping → declared output; required asset → declared Artifact; Renderer/Manifest QA-profile equality | `validate_projection_spec`, `validate_manifest`, `validate_bundle` | `test_projection_required_slots_have_one_valid_mapping`, `test_projection_renderer_paths_and_asset_requirements_fail_closed`, `test_manifest_closes_renderer_output_and_required_asset_paths`, `test_manifest_qa_profile_must_match_renderer_binding` |
| Temporal and downstream health | event triggers, declared freshness, future `valid_from`, expiry behavior, `downstream_health` and freshness/health consistency | `validate_knowledge_core`, `validate_manifest`, `validate_bundle` | `test_temporal_event_triggers_and_declared_freshness_are_consistent`, `test_future_valid_from_warns_candidate_and_blocks_publish`, `test_manifest_downstream_health_is_exact_and_publish_requires_healthy`, `test_bundle_health_must_reflect_freshness_issues` |
| Canonical identity and two locks | canonical bytes, object/artifact digests, generation-input lock and recomputed final-content lock | `canonical_json`, SHA-256 helpers, `final_content_lock`, `validate_manifest` | `test_canonical_json_is_compact_sorted_and_newline_terminated`, `test_sha256_helpers_use_canonical_bytes`, `test_manifest_rejects_wrong_final_lock_and_malformed_generation_lock` |
- Repeated warnings ignored by users: not measurable without the authoring MVP.
- General infrastructure added beyond fixture needs: not independently measured. The verified boundary is that no HTTP, database, subscriber, auth, renderer, Portal, deployment, or runtime wiring was added.

## Verification

- Focused command and result: `PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures -v` — 2026-08-21 fresh PASS, `Ran 128 tests`, `OK`.
- Full command and result: `UV_CACHE_DIR=/tmp/cognitive-card-uv-cache uv run --extra test python -m unittest discover -s tests -v` — 2026-08-21 fresh PASS with declared test dependencies, `Ran 444 tests`, `OK`.
- Baseline clarification: the earlier no-install system Python run reported five HTTP-test import errors because `fastapi`/`httpx` were absent; the declared dependency environment proves those were environment-only and the full suite is green.

## Review Closure

- Final whole-change repair closed the original 2 Critical, 4 Important, and 1 Minor code/architecture findings.
- The docs-only scoped re-review confirmed both documentation residuals addressed; a final targeted recheck of the plan Verification block returned `ADDRESSED; CLEAN`, with no new Critical or Important finding.
- This evidence is therefore verified for the contract pilot boundary. It does not authorize runtime wiring or claim the later authoring, Renderer/QA, Portal, migration, or production stages are complete.
