# Operator Mapping Artifact Publish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** From a locked four-card mapping revision, generate text-mature PNG/PDF, stop at `awaiting_review`, then let the operator approve and publish to a local package catalog without moving knowledge current.

**Architecture:** Add `convert_mapping` (read mapping revision, not current). Add `pack_from_mapping` that fail-closes if mapped nodes do not fit knowledge/look main zones. Orchestrate RENDER-01 + QA-01 into `artifact-work/{topic}/`. `publish_from_artifact` calls existing `record_review(approve)` + `publish_approved`. Ops fourth panel exposes generate / preview / publish. Do not call Skill, library `publish`, or ACCEPT-01 overflow packing.

**Tech Stack:** Python 3 unittest, existing converter / lock geometry helpers / render / QA / publish / knowledge_ops on server `knowledge-pipeline-v1`.

**Plan size:** Medium (7 tasks, 2 phases)

## Global Constraints

- Four-object schema, v1 FACT keys, AUTHOR-05 defaults, and packet contract stay unchanged.
- Input is `mapping.json` revision. Do not call `KnowledgeLibrary.publish`. Do not change `current.json`.
- Do not overflow leftover propositions into the sources zone. Knowledge/look main-zone overflow → `TEXT_OVERFLOW` / `LOCK_OVERFLOW_RISK` (same geometry as RENDER wrap). Sources zone: `title (source_id)` only.
- Do not call Skill / executor / `POST /admin/generation-inputs`.
- Do not generate images. Image track stays empty.
- `package_slug` equals topic slug. Catalog root is injected (`--catalog-root` or test temp dir). HTTP tests must use a temp `candidate_root`, never the production PORTAL catalog.
- Rabbit acceptance request must be Shenzhen / `age-5-6` / bilingual / print, assembled from the mapping bundle, not invented.
- Human actor on publish cannot be `qa-01-v1` / `publish-01-v1` / `machine`. Tests use `owner`.
- HTML ops shells must not embed claims or preview images without a token. No combined 「生成并上架」 control.
- Do not merge server `main`, push, add `uv.lock`, reload Nginx, or install a production release. Do not auto git commit (operator authorizes commits separately).
- Server worktree: `/Users/admin/projects/family/kids-visual-learning-pack/.worktrees/cognitive-card-server-knowledge-core` on `knowledge-pipeline-v1`.
- Reuse snapshot `sha256:ae563ea0c9d49046b2ff7e13f6294c1d6ddd1c5666f6bda5bd82d36872da1f20` and registry commit `9c1b82be69df2da8348f66970a993e9c1984ce6d` from `four_card_accept.run`.
- ACCEPT-01 `lock_generation_input` / `_pack_knowledge_groups` overflow path stays for historical tests. New path `lock_version = "mapping-artifact-v1"`.
- If rabbit-real's 8 propositions cannot fit the knowledge main zones, generate must fail. Do not relax packing to pass.

---

## File map

| Path | Role |
| --- | --- |
| `src/cognitive_card_server/four_card_converter/convert.py` | Add `convert_mapping` next to `convert_current` |
| `src/cognitive_card_server/four_card_artifact/__init__.py` | Export pipeline + pack |
| `src/cognitive_card_server/four_card_artifact/pack.py` | `pack_from_mapping`; fail-closed slot packing |
| `src/cognitive_card_server/four_card_artifact/copy_plan.py` | age-5-6 COPY from knowledge `visible_text` until COPY zone fills |
| `src/cognitive_card_server/four_card_artifact/pipeline.py` | `generate_from_mapping` / `publish_from_artifact` / work-dir layout |
| `src/cognitive_card_server/four_card_render/render.py` | Use mapping-artifact copy plan when `lock_version` matches |
| `src/cognitive_card_server/knowledge_ops/http.py` | Four admin routes |
| `src/cognitive_card_server/knowledge_ops/pages.py` | Fourth panel |
| `src/cognitive_card_server/http/app.py` | `PROTECTED_ROUTES` for the four routes |
| `tests/test_convert_mapping.py` | Converter from mapping |
| `tests/test_pack_from_mapping.py` | Fail-closed packing |
| `tests/test_artifact_pipeline.py` | Generate / publish / stale / idempotent |
| `tests/test_http_knowledge_ops.py` | Extend ops HTTP + HTML |

---

## Phase 1: Mapping → lock → work dir (server)

### Task 1.1: `convert_mapping`

**Files:**
- Modify: `src/cognitive_card_server/four_card_converter/convert.py`
- Modify: `src/cognitive_card_server/four_card_converter/__init__.py` (export)
- Test: `tests/test_convert_mapping.py`
- Modify: `tests/test_four_card_converter.py` only if `convert_current` chaptered-guide still must fail (keep that test green)

**Verify:** `python3 -m unittest tests.test_convert_mapping tests.test_four_card_converter -v` → all pass
**Depends on:** None

**Interfaces:**
- Consumes: `KnowledgeLibrary.get_current`, `get_mapping`, `load_package`, `fact_payload` (from `knowledge_library.mapping`), `assemble_request`, `apply_age_language`, `fact_from_knowledge_core`, `assemble_from_knowledge_revision`, `lookup_safety_cn` / `project_safety_strings`
- Produces:

```python
def apply_safety_registry(fact: Mapping[str, object]) -> dict[str, object]:
    """Set safety[].cn from registry; safety[].en must stay Core English."""

def convert_mapping(
    *,
    library: KnowledgeLibrary,
    topic: str,
    now,
    repo_root: Path,
    snapshot_id: str,
    registry_commit: str,
    request: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Seal joined generation-input against the mapping revision, not current."""
```

Behavior:
1. `get_current` or `MAPPING_NO_CURRENT`.
2. `get_mapping` or `ARTIFACT_NO_MAPPING`.
3. If `mapping["family"] != "four-card"` → `ARTIFACT_FAMILY_NOT_FOUR_CARD`.
4. If `mapping["source_current_revision"] != current.revision` → `ARTIFACT_MAPPING_STALE`.
5. `mapped = load_package(library root / topic / revision-NNNN for mapping["revision"])`. Use the same directory resolution as `_load_stored_revision`.
6. If mapped `blueprint.family != "four-card"` → `ARTIFACT_FAMILY_NOT_FOUR_CARD`.
7. After aligning both cores' `revision` to the same int, `fact_payload(mapped.knowledge_core) == fact_payload(current.knowledge_core)` or `MAPPING_CORE_DRIFT`.
8. `assemble_request` from **mapped** core/learning (not current). Missing fields → `ARTIFACT_REQUEST_REQUIRED` (map `CONVERTER_REQUEST_REQUIRED` to this code, or raise `ARTIFACT_REQUEST_REQUIRED` directly).
9. `fact = apply_safety_registry(apply_age_language(fact_from_knowledge_core(mapped.knowledge_core), assembled))`. Unregistered safety English → `AGE_SAFETY_EXPRESSION_GAP`.
10. `assemble_from_knowledge_revision(...)` with **mapped** four objects. Outer `knowledge_revision.revision` is the mapping revision number. Do not write library or compiled-jobs.

`convert_current` unchanged: chaptered-guide rabbit current still `CONVERTER_FAMILY_NOT_FOUR_CARD`.

Tests (use `rabbit-real.json`, publish as current **without** four-card overlay, then `lock_mapping(family="four-card")`):
- `convert_mapping` returns joined JSON that `validate_joined_generation_input` accepts; `knowledge_revision.revision` equals mapping revision; current still chaptered-guide.
- No mapping → `ARTIFACT_NO_MAPPING`.
- After a new `publish` of current without re-lock → `ARTIFACT_MAPPING_STALE`.
- `convert_current` on the same library still `CONVERTER_FAMILY_NOT_FOUR_CARD`.
- Safety `en` equals Core English; `cn` contains 监护 or 脊椎 for the registered strings.

- [x] **Step 1: Write failing tests** in `tests/test_convert_mapping.py` using helpers from `tests/test_four_card_converter.py` (`REPO_ROOT`, `SNAPSHOT_ID`, `REGISTRY_COMMIT`, `_request`, `_load_example`) and `KnowledgeLibrary.lock_mapping`.
- [x] **Step 2: Run** `python3 -m unittest tests.test_convert_mapping -v` → FAIL (import/`convert_mapping` missing).
- [x] **Step 3: Implement `apply_safety_registry` + `convert_mapping`.** Reuse `get_mapping` / `lock_mapping`; do not duplicate pointer schema.
- [x] **Step 4: Re-run tests including `tests.test_four_card_converter` → PASS.** Do not commit.

### Task 1.2: `pack_from_mapping`

**Files:**
- Create: `src/cognitive_card_server/four_card_artifact/__init__.py`
- Create: `src/cognitive_card_server/four_card_artifact/pack.py`
- Test: `tests/test_pack_from_mapping.py`

**Verify:** `python3 -m unittest tests.test_pack_from_mapping tests.test_convert_mapping tests.test_four_card_lock -v` → all pass
**Depends on:** Task 1.1

**Interfaces:**
- Consumes: `lock_from_payload`'s `_resolved_family`, `_page`, `_zone`, `_join_lang`, `_assert_zone_fits`, `_line_count`, `_layout_budget` — **import those helpers from `four_card_lock.lock` only if they are already public; otherwise copy the thin `_assert_zone_fits` usage by importing `_layout_budget` / `_line_count` after exporting them, or duplicate the four-line assert using `wrap_text` like lock.py**. Prefer exporting `_assert_zone_fits`, `_join_lang`, `_page`, `_zone`, `_resolved_family`, `_inner_generation_input` from `lock.py` rather than forking geometry.
- Consumes: mapping `projection-spec.blueprint.slots` `node_ids`; FACT propositions; `preview_mapping` slot ids `slot.{topic}.{cn-knowledge|...}`
- Produces:

```python
LOCK_VERSION = "mapping-artifact-v1"

def pack_from_mapping(
    payload: Mapping[str, object],
    *,
    repo_root: Path,
    projection_spec: Mapping[str, object],
) -> dict[str, object]:
    """Locked record. Fail closed if mapped nodes do not fit main zones."""
```

Return the same keys as `lock_generation_input`: `normalized_request`, `fact`, `cards`, `resolved_family`, `content_lock`. Set `content_lock.artifacts["lock_version"] = LOCK_VERSION`.

Packing (do **not** call `_pack_knowledge_groups`):
1. Parse inner generation-input (same as `_inner_generation_input`).
2. Index FACT propositions by id. Map slot `node_ids` → proposition_ids: a path node contributes the active propositions listed on that node in `learning-spec` (same resolution as `preview_mapping` / `_slot_preview_from_ids`). If a slot node has no FACT proposition → `ARTIFACT_SLOT_NODE_MISSING`.
3. Knowledge slot ids (cn and en) must have equal proposition_id sets. Observation look slots equal and ⊆ knowledge. Record unused.
4. Every FACT active knowledge proposition_id must be in the knowledge slot set → else `ARTIFACT_FACT_UNMAPPED`.
5. Split knowledge propositions: `certainty == "unknown"` → uncertainty zone, else appearance. Join with `"\n"`. **If `_assert_zone_fits` fails, raise `TEXT_OVERFLOW` (or keep `LOCK_OVERFLOW_RISK` but tests must accept the spec name: prefer raising `KnowledgeContractError("TEXT_OVERFLOW", path)` so ops surface matches spec §10).** Do not put leftovers in sources.
6. Look zone: join look propositions in slot order; fail closed if not fit; ≥ 2 already guaranteed by mapping lock, still assert ⊆ knowledge main-zone ids.
7. Sources zone text: for each FACT source, if title blank → `RENDER_SOURCE_TITLE_MISSING`; else `f"{title} ({source_id})"`. `proposition_ids=[]`.
8. Safety: CN pages `safety[].cn` joined; EN pages `safety[].en`. Do not fall back to English on CN.
9. Observation record/trace/copy empty zones (RENDER overlays copy later).
10. Do not put overflow proposition ids on sources.

Tests:
- Rabbit-real convert_mapping → pack: CN knowledge main-zone distinct proposition_ids ≥ 4 and equal FACT ids; look ≥ 2 ⊆ knowledge; sources `proposition_ids` empty; source visible_text contains `Description and Physical Characteristics of Rabbits` or `Diet for Rabbits` or RSPCA; CN safety has 监护 or 脊椎; EN safety equals Core English; `lock_from_payload` was not used.
- Synthetic: two long strings that exceed `_layout_budget` max lines → `TEXT_OVERFLOW`; sources still must not contain those claims if packing raises before write.
- `tests.test_four_card_lock` still passes (ACCEPT overflow path untouched).

- [x] **Step 1: Failing tests** as above.
- [x] **Step 2: Run** `python3 -m unittest tests.test_pack_from_mapping -v` → FAIL.
- [x] **Step 3: Implement `pack.py`.** Export lock helpers if needed (`_assert_zone_fits` etc.) with the smallest lock.py change.
- [x] **Step 4: Tests PASS including `tests.test_four_card_lock`.** Do not commit.

### Task 1.3: Mapping-artifact COPY plan

**Files:**
- Create: `src/cognitive_card_server/four_card_artifact/copy_plan.py`
- Modify: `src/cognitive_card_server/four_card_render/render.py` (`bind_locked_record`)
- Test: `tests/test_pack_from_mapping.py` (add COPY cases) or `tests/test_mapping_artifact_copy_plan.py`

**Verify:** `python3 -m unittest tests.test_pack_from_mapping tests.test_four_card_render tests.test_age_language -v` → all pass
**Depends on:** Task 1.2

**Interfaces:**
- Produces:

```python
def copy_plan_from_knowledge_cards(
    cards: Mapping[str, object],
    propositions: Sequence[Mapping[str, object]],
    profile,  # AgeLanguageProfile
) -> dict[str, object]:
    """age-3-4: empty COPY. age-5-6: whole sentences from knowledge visible_text until COPY zone would overflow."""
```

- `bind_locked_record`: after overlay, if `record["content_lock"]["artifacts"]["lock_version"] == "mapping-artifact-v1"`, call `copy_plan_from_knowledge_cards` instead of `copy_plan(propositions, profile)`.
- age-5-6: split CN_KNOW / EN_KNOW `appearance`+`uncertainty` `visible_text` on `。！？.!?` keeping spans exact substrings. Append whole sentence while `_assert_zone_fits` of the COPY zone text still passes; then stop. Trace: 1–6 exact spans from those sentences (existing `_trace_item` / first `TRACE_MAX_ITEMS` chars). No 2-sentence / 12-char / 8-word caps.
- age-3-4: COPY `[]`; tracing/oral unchanged from AGE-01 if profile says so (rabbit tests are age-5-6 only).
- Zero legal COPY span on age-5-6 → `AGE_COPY_SPAN_UNAVAILABLE`.
- `tests.test_age_language` must still enforce AGE-01 §4.3 caps on the **old** `copy_plan()` function.

- [x] **Step 1: Failing tests** — mapping-artifact lock overlay COPY is a substring of knowledge visible_text; more than 2 sentences allowed if they fit; AGE-01 `copy_plan` still caps at 2.
- [x] **Step 2: Implement copy_plan_from_knowledge_cards + bind_locked_record branch.**
- [x] **Step 3: Tests PASS.** Do not commit.

### Task 1.4: `generate_from_mapping` work dir

**Files:**
- Create: `src/cognitive_card_server/four_card_artifact/pipeline.py`
- Modify: `src/cognitive_card_server/four_card_artifact/__init__.py`
- Test: `tests/test_artifact_pipeline.py`

**Verify:** `python3 -m unittest tests.test_artifact_pipeline tests.test_pack_from_mapping tests.test_convert_mapping -v` → all pass
**Depends on:** Task 1.3

**Interfaces:**

```python
def mapping_identity(pointer: Mapping[str, object]) -> dict[str, object]:
    """Stable subset: topic_slug, revision, family, identity hashes."""

def generate_from_mapping(
    *,
    library: KnowledgeLibrary,
    topic: str,
    now,
    repo_root: Path,
    snapshot_id: str,
    registry_commit: str,
    work_root: Path,
) -> dict[str, object]:
    """Write artifact-work/{topic}/ and run machine QA. Does not publish."""
```

Work dir layout (spec §7):

```text
{work_root}/{topic}/
  mapping-identity.json
  convert/joined.json
  record/locked-record.json
  render/   # render_locked output
  qa/       # run_machine_qa output
```

Behavior:
1. `convert_mapping` → write `convert/joined.json`.
2. `pack_from_mapping(joined, repo_root=..., projection_spec=mapped.projection_spec)` → `record/locked-record.json`.
3. If `mapping-identity.json` matches current mapping identity AND `qa/qa-report.json` status is `awaiting_review` → return existing status without re-render.
4. If same identity and `machine_failed` → overwrite work dir files, do not touch catalog.
5. `render_locked(record, work/topic/render)`.
6. `run_machine_qa(record, render_dir, qa_dir, now=now)`.
7. Return `{status, mapping_identity, qa_status, listed: True}`. Catalog untouched.
8. Rabbit-real extra assertions when QA is `awaiting_review`: CN knowledge ≥ 4 distinct ids; look ≥ 2; record empty; source titles; no layout overflow in render-set qa flags.

If rabbit-real packing raises `TEXT_OVERFLOW`, `test_rabbit_generate_knowledge_fits` should **fail the test** (not skip). That is the spec completion gate. Do not catch and rewrite sources.

- [x] **Step 1: Failing tests** — no mapping; stale mapping; generate does not change `current.json`; second generate is idempotent; `package-catalog` dir is not created.
- [x] **Step 2: Implement pipeline.py.**
- [x] **Step 3: Tests PASS.** Do not commit.

### Task 1.5: `publish_from_artifact`

**Files:**
- Modify: `src/cognitive_card_server/four_card_artifact/pipeline.py`
- Test: `tests/test_artifact_pipeline.py` (add cases)

**Verify:** `python3 -m unittest tests.test_artifact_pipeline tests.test_four_card_publish tests.test_four_card_qa -v` → all pass
**Depends on:** Task 1.4

**Interfaces:**

```python
def publish_from_artifact(
    *,
    topic: str,
    actor: str,
    work_root: Path,
    catalog_root: Path,
    now,
) -> dict[str, object]:
    """Approve QA if awaiting_review, then publish_approved(slug=topic)."""
```

Behavior:
1. Load `qa/qa-report.json`. If missing → `ARTIFACT_NOT_AWAITING_REVIEW`.
2. If status `awaiting_review` → `record_review(qa_dir, actor=actor, decision="approve", now=now)`.
3. If status already `approved` and catalog current lock equals this record lock → return existing current (idempotent).
4. If `approved` but catalog current missing/different → `publish_approved(record, qa_dir, render_dir, catalog_root, slug=topic, actor=actor, now=now)` only (do not re-run machine QA).
5. If status not `awaiting_review` and not `approved` → `ARTIFACT_NOT_AWAITING_REVIEW`.
6. Empty/reserved actor → existing `QA_REVIEW_ACTOR_REQUIRED` / `PUBLISH_ACTOR_REQUIRED`.
7. Seed catalog with a dummy `revision-0001` directory + current pointer (minimal PNG bytes not required if `publish_approved` replaces current with new identity). Simpler path: empty catalog → first publish is `revision-0001`. Second test: write a pre-existing revision dir with different lock, then publish → `revision-0002` and old dir bytes unchanged.

Also: `generate_from_mapping` then `publish_from_artifact` must leave library `current.json` and `mapping.json` bytes unchanged.

- [x] **Step 1: Failing tests** for approve+publish, idempotent republish, reserved actor, generate-only does not create catalog current.
- [x] **Step 2: Implement `publish_from_artifact`.**
- [x] **Step 3: Tests PASS including `tests.test_four_card_publish` and `tests.test_four_card_qa`.** Do not commit.

---

## Phase 2: Ops surface + kids governance

### Task 2.1: Ops HTTP + fourth panel

**Files:**
- Modify: `src/cognitive_card_server/knowledge_ops/http.py`
- Modify: `src/cognitive_card_server/knowledge_ops/pages.py`
- Modify: `src/cognitive_card_server/http/app.py` (`PROTECTED_ROUTES`)
- Test: `tests/test_http_knowledge_ops.py`

**Verify:** `python3 -m unittest tests.test_http_knowledge_ops tests.test_artifact_pipeline -v` → all pass
**Depends on:** Task 1.5

Routes (admin Bearer, same prefix as WB-02):

| Method | Path | Handler |
| --- | --- | --- |
| POST | `/admin/knowledge-library/{topic}/artifact-generate` | `generate_from_mapping`; work_root=`candidate_root/"artifact-work"` |
| GET | `/admin/knowledge-library/{topic}/artifact` | status or `{"listed": false}` HTTP 200 |
| GET | `/admin/knowledge-library/{topic}/artifact/cards/{page}` | PNG; `page` in `cn-observe`,`en-observe`,`cn-know`,`en-know`; else `OPS_NOT_FOUND` |
| POST | `/admin/knowledge-library/{topic}/artifact-publish` | body `{"actor":"..."}`; catalog_root=`candidate_root/"package-catalog"` |

HTTP generate needs `settings.repo_root`. If None → 409 `ARTIFACT_REQUEST_REQUIRED`. snapshot/registry: import `SNAPSHOT_ID` / `REGISTRY_COMMIT` from `four_card_accept.run`.

Map `KnowledgeContractError` codes already used (`MAPPING_NO_CURRENT` → 409; `AGE_SAFETY_EXPRESSION_GAP` / `TEXT_OVERFLOW` / `ARTIFACT_*` → 400 except `OPS_NOT_FOUND` → 404). Add new codes to `http/errors.py` status map if a default would 500.

Detail HTML: add `data-panel="artifact"` **client-side after token** only. Buttons labelled `生成` and `批准并上架`. Actor input default `owner`. No control whose text is `生成并上架`. Preview `<img src=".../artifact/cards/...">` only after generate succeeds (JS). Shell without token: no 兔子 claims, no Merck, no safety English, no `<img`.

Existing mapping panel tests stay green. 401 without token. Invalid slug `OPS_NOT_FOUND`.

- [x] **Step 1: Failing HTTP tests** (401; listed=false; generate keeps current; HTML shell has no 生成并上架 / no claims; publish requires actor).
- [x] **Step 2: Implement routes + JS panel + PROTECTED_ROUTES.**
- [x] **Step 3: Tests PASS.** Do not commit.

### Task 2.2: Kids governance

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md` (In Scope stays docs+this plan until implementation starts; after server tests pass, do not mark WB-03 DONE until operator accepts)
- Modify: `docs/ai/HANDOFF.md`
- Modify: `docs/cognitive-card-os-roadmap.md` (WB-03 still IN PROGRESS until implementation+review)
- Modify: `docs/README.md` (this plan listed Completed/Active)
- Modify: `docs/superpowers/specs/2026-09-01-operator-mapping-artifact-publish-design.md` Status remains Approved
- This plan file (checkboxes)

**Verify:** `bash scripts/ai/check-task-state.sh`; `bash scripts/ai/check-handoff.sh`; `bash scripts/ai/check-doc-governance.sh` (WARN overdue Last Reviewed allowed); `git diff --check`
**Depends on:** Plan exists now; Done claim waits for Phase 1–2 implementation

- [x] After implementation: record server focused unittest commands and PASS/FAIL in HANDOFF. Do not claim production install. Do not commit unless operator asks.

Focused server verification (implementation phase):

```bash
python3 -m unittest \
  tests.test_convert_mapping \
  tests.test_pack_from_mapping \
  tests.test_artifact_pipeline \
  tests.test_http_knowledge_ops \
  tests.test_four_card_converter \
  tests.test_four_card_lock \
  tests.test_four_card_render \
  tests.test_four_card_qa \
  tests.test_four_card_publish \
  tests.test_knowledge_library_mapping \
  tests.test_mapping_preview \
  tests.test_age_safety_expression \
  -v
```

---

## Spec coverage

| Spec § | Task |
| --- | --- |
| 5 admission / stale / no current convert | 1.1, 1.4 |
| 6.1 convert_mapping + safety cn | 1.1 |
| 6.2 pack fail-closed + titles | 1.2 |
| 6.3 COPY overlay | 1.3 |
| 7 work dir + idempotent generate | 1.4 |
| 8 HTTP + fourth panel | 2.1 |
| 9 publish slug / history | 1.5 |
| 10 error codes | 1.1–2.1 |
| 11 rabbit acceptance | 1.4, 1.5, 2.1 |
| 12 no Nginx / no Skill / no production catalog | Global Constraints |

## Placeholder / consistency review

- Function names used later match Task 1.1–1.5: `convert_mapping`, `apply_safety_registry`, `pack_from_mapping`, `copy_plan_from_knowledge_cards`, `generate_from_mapping`, `publish_from_artifact`, `LOCK_VERSION = "mapping-artifact-v1"`.
- No TBD. Catalog is always injected. `convert_current` remains the current-only entry.
