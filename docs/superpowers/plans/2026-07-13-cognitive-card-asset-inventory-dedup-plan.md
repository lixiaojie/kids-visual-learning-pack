# Cognitive Card Asset Inventory and Deduplication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the read-only historical asset discovery into a deterministic, machine-readable inventory with stable migration IDs, SHA-256 content identities, structural evidence, declared provenance, and duplicate groups—without moving, deleting, renaming, or publishing any source asset.

**Architecture:** Add a small Python scanner to the `kids-visual-learning-pack` governance repository. Portable source locators and human decisions live in a reviewed JSON config, while absolute machine roots live in an ignored local mapping. The scanner walks only resolved non-symlink roots, opens files with no-follow semantics, hashes eligible bytes, extracts image/PDF metadata, derives conservative structural evidence from exact package-relative components, assigns full-digest content and duplicate identities, and publishes all reports as one immutable versioned snapshot plus an atomic latest pointer. Tests use temporary fixtures only; the production scan remains read-only.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `hashlib`, `json`, `os`, `pathlib`, `tempfile`, `unittest`), Pillow for image metadata, pypdf for PDF page metadata, existing Node package scripts as command aliases, Git.

## Global Constraints

- Source inventory: `/Users/admin/Documents/kids-visual-learning-pack/docs/cognitive-card-os-asset-migration-inventory.md`.
- Implementation repository: `/Users/admin/Documents/kids-visual-learning-pack`.
- This is `MIG-01` only. Do not copy, move, rename, delete, transcode, upload, publish, or mutate any source asset.
- Do not infer copyright ownership, factual correctness, Card OS publication status, target package ID, or final classification from filenames.
- Do not follow symlinks. Record them as skipped entries with reason `symlink`.
- Do not scan undeclared roots, `.git`, `node_modules`, `dist`, `tmp`, caches, or macOS metadata unless a source rule explicitly overrides the exclusion.
- Content identity is SHA-256 of file bytes. Filename equality is not content equality.
- PNG/WebP render pairs remain separate content objects but are emitted in explicit `derivative_candidate_groups`: PNG is `source_candidate`, WebP is `derivative_candidate`, and relationship status remains `review_required` until human confirmation.
- `migration_asset_id` must be stable across machines for identical bytes: `mig_sha256_` plus the full 64-character SHA-256. No truncated identity is allowed.
- `duplicate_group` is `dup_sha256_` plus the full 64-character SHA-256 only when the same digest has two or more source aliases.
- Source paths are stored as declared root ID plus POSIX relative path. Absolute paths exist only in ignored `inventory-roots.local.json`; they never enter committed configuration, inventory, warnings, reports, or config digests.
- Rights default to `review_required`; target package defaults to `null`; scanner never upgrades either field.
- Output root and config/root-map paths must be distinct. The writer rejects either-direction ancestor/descendant containment between output and source roots, any resolved-path collision with config/root map, and any symlinked output ancestor.
- A complete run is staged in one temporary directory, renamed to an immutable `snapshots/<run_id>/` directory, then exposed by atomically replacing `latest.json`. An interrupted scan cannot mix files from different runs.
- Run tests before every commit:

```bash
python3 -m unittest tests.test_card_os_asset_inventory -v
```

---

## File Map

- Create `migration/card-os/inventory-sources.json` — portable source locators, exclusions, thread IDs, grades, and decisions.
- Create `migration/card-os/inventory-roots.example.json` — portable example of machine base mappings.
- Create ignored `migration/card-os/inventory-roots.local.json` — this Mac's absolute `workspace` and `codex_archive` roots.
- Create `migration/card-os/generated/.gitkeep` — generated snapshot directory.
- Create `requirements-card-os-inventory.txt` — Pillow and pypdf dependency ranges.
- Create `scripts/card_os_asset_inventory.py` — pure scanner, identity logic, report writer, and CLI.
- Create `tests/__init__.py` — test package marker.
- Create `tests/test_card_os_asset_inventory.py` — deterministic fixture tests.
- Modify `package.json` — `inventory:card-os` and `test:card-os-inventory` aliases.
- Generate `migration/card-os/generated/latest.json` — atomic pointer and shared snapshot digest.
- Generate `migration/card-os/generated/snapshots/<run_id>/inventory.json` — canonical machine snapshot.
- Generate `migration/card-os/generated/snapshots/<run_id>/duplicate-report.md` — human review summary.
- Generate `migration/card-os/generated/snapshots/<run_id>/scan-warnings.json` — skipped/missing/unreadable entries.
- Modify `docs/cognitive-card-os-asset-migration-inventory.md` — snapshot link, counts, and execution date.
- Modify `docs/cognitive-card-os-roadmap.md` — `MIG-01` evidence and next gate.
- Modify `README.md` — governance artifact links and regeneration command.

## Machine Contract

Top-level inventory:

```json
{
  "schema": "cognitive-card-migration-inventory-v1",
  "generated_at": "2026-07-13T00:00:00Z",
  "config_digest": "sha256:<64 hex>",
  "run_id": "inv_sha256_<64 hex>",
  "snapshot_digest": "sha256:<64 hex>",
  "scan_roots": [{"root_id":"rabbit-full-v01","locator":{"base":"codex_archive","relative":"..."},"status":"scanned"}],
  "metadata_readers": {"pillow":"<installed version>","pypdf":"<installed version>"},
  "summary": {
    "source_alias_count": 0,
    "content_object_count": 0,
    "duplicate_group_count": 0,
    "same_name_candidate_group_count": 0,
    "derivative_candidate_group_count": 0,
    "warning_count": 0,
    "total_source_bytes": 0,
    "unique_content_bytes": 0
  },
  "assets": [],
  "duplicate_groups": [],
  "same_name_candidate_groups": [],
  "derivative_candidate_groups": []
}
```

Each asset record represents one content digest and carries one or more aliases:

```json
{
  "migration_asset_id": "mig_sha256_<64 hex>",
  "sha256": "<64 hex>",
  "size_bytes": 0,
  "source_aliases": [
    {
      "root_id": "rabbit-full-v01",
      "relative_path": "cards/final/rabbit-cn-observation.png",
      "source_thread_id": null,
      "source_group": "rabbit-full-v01",
      "media_type": "image/png",
      "image_width": 1536,
      "image_height": 2048,
      "pdf_page_count": null,
      "metadata_status": "ok"
    }
  ],
  "object_name": null,
  "classification": null,
  "rights_status": "review_required",
  "structural_evidence": {
    "fact": false,
    "propositions": false,
    "content_lock": false,
    "four_cards": false,
    "qa": false,
    "print_pdf": false,
    "manifest": false
  },
  "migration_grades": ["A"],
  "media_types": ["image/png"],
  "duplicate_group": null,
  "target_package_id": null,
  "decisions": ["strict_revalidate"]
}
```

Arrays are sorted deterministically. Multiple source rules with the same bytes merge aliases, grades, decisions, media types, and structural evidence without choosing a preferred source. Media type and dimensions/page count remain on each alias because identical bytes may have differently named aliases.

Duplicate group schema:

```json
{
  "duplicate_group": "dup_sha256_<64 hex>",
  "sha256": "<64 hex>",
  "migration_asset_id": "mig_sha256_<64 hex>",
  "alias_count": 2,
  "aliases": [{"root_id":"...","relative_path":"..."}]
}
```

Warning schema:

```json
{
  "root_id": "rabbit-full-v01",
  "relative_path": "01_content/example.bin",
  "code": "unsupported_extension",
  "detail": "extension .bin is not enabled for this root"
}
```

`scan-warnings.json` wraps those records as:

```json
{
  "schema": "cognitive-card-migration-warnings-v1",
  "run_id": "inv_sha256_<64 hex>",
  "snapshot_digest": "sha256:<64 hex>",
  "warnings": []
}
```

Warnings never include absolute paths or exception representations that could reveal them. Same-basename/different-digest candidate groups use `name_sha256_<64 hex of normalized basename>` and sort member assets by full digest.

Same-name candidate schema:

```json
{
  "group_id": "name_sha256_<64 hex>",
  "normalized_basename": "manifest.json",
  "status": "review_required",
  "members": ["mig_sha256_<64 hex>"]
}
```

Normalize with `unicodedata.normalize("NFC", pathlib.PurePosixPath(relative_path).name).casefold()` and retain the extension. Hash the normalized UTF-8 bytes for the group ID. Emit a group only when two or more different full content digests share that normalized basename. Test ASCII case variants and canonically equivalent NFC/NFD names.

Derivative candidate schema:

```json
{
  "group_id": "deriv_sha256_<64 hex>",
  "status": "review_required",
  "normalized_stem": "topic/hero",
  "members": [
    {"migration_asset_id":"mig_sha256_<64 hex>","role":"source_candidate","extension":".png"},
    {"migration_asset_id":"mig_sha256_<64 hex>","role":"derivative_candidate","extension":".webp"}
  ]
}
```

Within one `source_group`, normalize the POSIX relative path without its final extension using Unicode NFC plus casefold. Emit a group only when both `.png` and `.webp` aliases exist. Group ID hashes canonical JSON of source group, normalized stem, sorted full content digests, extensions, and roles. This is a candidate relationship, never a publication or rights claim.

---

### Task 1: Define and Validate the Source Configuration

**Files:**
- Create: `migration/card-os/inventory-sources.json`
- Create: `migration/card-os/inventory-roots.example.json`
- Create: `migration/card-os/inventory-roots.local.json` (ignored local file)
- Create: `requirements-card-os-inventory.txt`
- Modify: `.gitignore`
- Create: `tests/__init__.py`
- Create: `tests/test_card_os_asset_inventory.py`
- Create: `scripts/card_os_asset_inventory.py`

- [ ] **Step 1: Install metadata dependencies and write failing configuration tests**

Create `requirements-card-os-inventory.txt` with the exact ranges shown in Step 3, then install it:

```bash
python3 -m pip install -r requirements-card-os-inventory.txt
```

Tests must create a temporary config and assert:

- schema must equal `cognitive-card-migration-sources-v1`;
- `root_id` values are unique and match `^[a-z0-9][a-z0-9-]{2,63}$`;
- each locator contains a known base key and a safe relative path with no `..`;
- each base mapping is absolute; if a resolved root exists it must be a non-symlink directory whose strict resolution equals its normalized path;
- grades are one of `A`, `B`, `C`, `D`, or `legacy-gallery`;
- decisions are from `strict_revalidate`, `upgrade_revalidate`, `rebuild`, `provenance_only`, `legacy_gallery`, `exclude`;
- a missing resolved root is a warning in production mode and an error with `--strict-roots`;
- duplicate resolved paths, including paths reached through symlinked base/root components, are rejected to avoid double traversal.

Use this public loader:

```python
@dataclass(frozen=True)
class SourceRule:
    root_id: str
    source_group: str
    locator_base: str
    locator_relative: str
    resolved_path: Path
    source_thread_id: str | None
    migration_grade: str
    decision: str
    include_extensions: tuple[str, ...]
    exclude_names: tuple[str, ...]

def load_source_config(
    path: Path,
    roots_path: Path,
    *,
    strict_roots: bool,
) -> SourceConfig: ...
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_asset_inventory.ConfigTests -v
```

Expected: import failure because the scanner module does not exist.

- [ ] **Step 3: Implement the loader and checked-in source rules**

The checked-in config uses `{ "base": "...", "relative": "..." }` locators and declares exactly these primary roots:

| Root ID | Portable locator | Thread | Grade | Decision |
| --- | --- | --- | --- | --- |
| `rabbit-full-v01` | `codex_archive:2026-07-11/new-chat/outputs/life/animal_mammal/rabbit/20260712_214042__rabbit__full_package__v01` | `null` | A | `strict_revalidate` |
| `paleobiology-packages-20260707` | `workspace:outputs` | `null` | B | `upgrade_revalidate` |
| `shenzhen-plants-20260626` | `codex_archive:2026-06-26/h/outputs` | `019f02ca-cf3c-79e0-919d-9f8b90a076db` | C | `rebuild` |
| `kids-world-current` | `workspace:boards/kids-world` | `null` | C | `rebuild` |
| `kids-world-batch-20260612` | `codex_archive:2026-06-12/files-mentioned-by-the-user-kids/outputs/kids-world-hotspot-v1-png` | `null` | C | `provenance_only` |
| `kids-world-regenerated-20260614` | `codex_archive:2026-06-14/files-mentioned-by-the-user-kids/outputs/kids-world-regenerated-2026-06-14` | `null` | C | `provenance_only` |
| `llm-last-image-20260614` | `codex_archive:2026-06-14/files-mentioned-by-the-user-kids-2/outputs` | `null` | D | `provenance_only` |
| `kids-world-older-copies` | `codex_archive:2026-05-12/files-mentioned-by-the-user-kids/boards/kids-world` | `null` | D | `provenance_only` |
| `spider-verse` | `workspace:boards/spider-verse` | `null` | legacy-gallery | `legacy_gallery` |
| `paw-patrol` | `workspace:boards/paw-patrol` | `null` | legacy-gallery | `legacy_gallery` |

Default eligible extensions:

```json
[".png", ".webp", ".jpg", ".jpeg", ".pdf", ".json", ".md", ".yaml", ".yml", ".txt", ".tsv"]
```

Default excluded names:

```json
[".git", ".DS_Store", "Thumbs.db", "node_modules", "dist", "tmp", "__pycache__"]
```

For `spider-verse` and `paw-patrol`, add source-specific `.html`, `.css`, `.js`, `.ts`, and `.tsx` extensions so the legacy experiences are actually represented. Keep these code extensions disabled for knowledge-package roots.

`inventory-roots.example.json` contains placeholder absolute values for `workspace` and `codex_archive`. Add `migration/card-os/inventory-roots.local.json` to `.gitignore`, and create the actual local file for this Mac without staging it. `config_digest` is SHA-256 of canonical JSON parsed from `inventory-sources.json`; the ignored absolute root mapping is intentionally excluded.

The ignored local mapping on this Mac is exactly:

```json
{
  "schema": "cognitive-card-migration-roots-v1",
  "bases": {
    "workspace": "/Users/admin/Documents/kids-visual-learning-pack",
    "codex_archive": "/Users/admin/Documents/Codex"
  }
}
```

Create `requirements-card-os-inventory.txt`:

```text
Pillow>=11,<13
pypdf>=5,<7
```

Record `PIL.__version__` and `pypdf.__version__` under top-level `metadata_readers`, include both in the canonical semantic payload, and test that a reader-version change produces a different `run_id` without changing byte-derived `migration_asset_id` values.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_asset_inventory.ConfigTests -v
git add .gitignore requirements-card-os-inventory.txt migration/card-os/inventory-sources.json migration/card-os/inventory-roots.example.json scripts/card_os_asset_inventory.py tests
git commit -m "feat(migration): declare historical asset scan roots"
```

### Task 2: Implement Read-Only Walking, Hashing, and Media Detection

**Files:**
- Modify: `scripts/card_os_asset_inventory.py`
- Modify: `tests/test_card_os_asset_inventory.py`

- [ ] **Step 1: Write failing scanner tests**

Install the declared metadata readers before importing scanner tests:

```bash
python3 -m pip install -r requirements-card-os-inventory.txt
```

Create fixture files with identical and distinct bytes. Assert:

- directory traversal and output ordering are stable regardless of file creation order;
- symlinked files/directories are skipped and never opened;
- excluded names and extensions are skipped with stable reason codes;
- SHA-256 is calculated by 1 MiB chunks;
- MIME mapping for non-image aliases is fixed, not platform-dependent:

```python
MEDIA_TYPES = {
    ".png": "image/png",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
    ".json": "application/json",
    ".md": "text/markdown",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
    ".txt": "text/plain",
    ".tsv": "text/tab-separated-values",
    ".html": "text/html",
    ".css": "text/css",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".tsx": "text/typescript",
}
```

- no source content, name, size, or modification-time changes are made; test snapshots those fields before and after;
- PNG, JPEG, and WebP aliases record Pillow-observed media type, width, and height; PDF aliases record pypdf page count; metadata fields are null for other formats;
- an image whose extension and observed format disagree is retained with observed `media_type` plus warning `media_type_mismatch`;
- malformed image/PDF metadata retains the hashed alias with null dimension/page fields and `metadata_status="unreadable"`, plus warning `metadata_unreadable`; later migration cannot promote it without review;
- a file that changes device, inode, size, mtime-ns, or ctime-ns between scan discovery and post-hash `fstat` is excluded with `source_changed_during_scan`;
- `os.open` is mocked to raise `PermissionError` for unreadable-file tests, so the test does not depend on process privilege.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_asset_inventory.ScannerTests -v
```

Expected: scanner functions are missing.

- [ ] **Step 3: Implement scanner primitives**

Expose descriptor-oriented primitives:

```python
def walk_source(
    rule: SourceRule,
    on_file: Callable[[PurePosixPath, int, os.stat_result], None],
) -> list[WarningRecord]: ...
def sha256_descriptor(
    descriptor: int, *, expected_stat: os.stat_result
) -> tuple[str, int, os.stat_result]: ...
def scan_source(rule: SourceRule) -> tuple[list[SourceAliasRecord], list[WarningRecord]]: ...
```

Open the resolved root with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW` and compare `lstat`/`fstat` identity. Traverse only by directory descriptors: call `os.scandir(parent_fd)`, open each child directory with `os.open(entry.name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW, dir_fd=parent_fd)`, compare the discovery stat to child `fstat`, recurse on that descriptor, and close it in `finally`. Open regular files with `os.open(entry.name, O_RDONLY | O_NOFOLLOW, dir_fd=parent_fd)`, compare discovery/pre/post identities, and hash/read metadata through that descriptor. Never recurse or reopen by pathname. Sort entry names before processing and construct only logical `PurePosixPath` aliases. Fail closed with `unsafe_source_entry` if an entry is replaced, becomes a symlink, or lacks required no-follow support. Tests replace a checked directory with a symlink immediately before child open and prove the target is never scanned. Never write inside a source root.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_asset_inventory.ScannerTests -v
python3 -m unittest tests.test_card_os_asset_inventory -v
git add scripts/card_os_asset_inventory.py tests/test_card_os_asset_inventory.py
git commit -m "feat(migration): scan and hash assets read only"
```

### Task 3: Build Stable Content Objects and Conservative Structural Evidence

**Files:**
- Modify: `scripts/card_os_asset_inventory.py`
- Modify: `tests/test_card_os_asset_inventory.py`

- [ ] **Step 1: Write failing aggregation tests**

Tests must prove:

- identical bytes across roots produce one asset with multiple aliases and one duplicate group;
- same filename with different bytes produces two assets;
- full-length `migration_asset_id` and duplicate ID derive only from the full digest and cannot collide for different digests;
- grades and decisions merge as sorted unique arrays;
- structural evidence is `true` only from conservative path/basename rules;
- no object name, classification, rights approval, target package, or preferred alias is inferred.
- same-name and PNG/WebP derivative candidates serialize into their declared top-level groups with the exact normalization, role, and ordering rules above.

Use exact lowercase path-component and basename matchers; never use arbitrary substring matching:

```python
FACT_BASENAMES = {"fact.json", "facts.json"}
PROPOSITION_BASENAMES = {
    "proposition_alignment.json", "semantic_core.json", "semantic-core.json"
}
CONTENT_LOCK_BASENAMES = {"content_lock.json", "content-lock.json"}
FOUR_CARD_BASENAMES = {"final_cards.json", "four_cards.json", "four-cards.json"}
FOUR_CARD_COMPONENTS = {"final_cards"}
QA_COMPONENTS = {"qa", "06_qa"}
PRINT_COMPONENTS = {"print", "05_print"}
MANIFEST_BASENAMES = {"manifest.json", "package_manifest.json", "package-manifest.json"}
```

`print_pdf` requires `.pdf` plus a `PRINT_COMPONENTS` path component; `qa` requires a `QA_COMPONENTS` component. Evidence is OR-merged across aliases. `four_cards` alone means only that a matching basename/component exists; it does not certify four complete pages. Add a fixture mirroring rabbit v3 paths `01_content/fact.json`, `01_content/final_cards.json`, `01_content/content_lock.json`, `06_qa/manifest.json`, `05_print/pdf/rabbit.pdf`, and a negative `artifact.json` case.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_asset_inventory.AggregationTests -v
```

Expected: aggregation interfaces are missing.

- [ ] **Step 3: Implement deterministic aggregation**

Expose:

```python
def build_inventory(
    config: SourceConfig,
    alias_records: Sequence[SourceAliasRecord],
    warnings: Sequence[WarningRecord],
    *,
    generated_at: str,
) -> dict[str, object]: ...
```

Sort assets by `(sha256, migration_asset_id)`, aliases by `(root_id, relative_path)`, grades by `A,B,C,D,legacy-gallery`, duplicate groups by ID, same-name candidate groups by normalized basename/group ID, and derivative candidates by `(source_group, normalized_stem, group_id)`. `total_source_bytes` counts aliases; `unique_content_bytes` counts content objects once. Validate uniqueness of every full-digest asset/group ID before serialization and fail with `identity_collision` if an internal inconsistency is detected.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest tests.test_card_os_asset_inventory.AggregationTests -v
python3 -m unittest tests.test_card_os_asset_inventory -v
git add scripts/card_os_asset_inventory.py tests/test_card_os_asset_inventory.py
git commit -m "feat(migration): aggregate content identities and evidence"
```

### Task 4: Add Atomic Outputs, CLI, and Reproducibility Check

**Files:**
- Modify: `scripts/card_os_asset_inventory.py`
- Modify: `tests/test_card_os_asset_inventory.py`
- Create: `migration/card-os/generated/.gitkeep`
- Modify: `package.json`

- [ ] **Step 1: Write failing writer and CLI tests**

Cover:

- deterministic JSON with `ensure_ascii=False`, `sort_keys=True`, two-space indent, trailing newline;
- Markdown report includes group counts, byte counts, aliases, and same-name/different-digest candidates;
- warnings JSON contains missing root, symlink, unreadable, unsupported extension, and changed-source reasons;
- output/config/root-map destinations are resolved and distinct; either-direction output/source containment, equality with config/root map, or any symlinked output ancestor is rejected before any write;
- a full run is staged in a temporary directory; a simulated failure before snapshot rename leaves the prior `latest.json` and snapshot unchanged;
- every inventory, warning document, report front matter, and `latest.json` shares one `run_id` and snapshot digest;
- `--check` regenerates in memory and exits 0 only when `latest.json` targets a semantically identical complete snapshot, ignoring only `generated_at`;
- `--generated-at` accepts RFC3339 UTC and makes tests reproducible;
- `--dry-run-summary` emits declared-root file count, eligible byte count, and a SHA-256 digest of sorted `(device, inode, relative_path, size_bytes, mtime_ns, ctime_ns)` tuples without hashing file contents or writing outputs;
- CLI returns non-zero on invalid config and never modifies source fixtures.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_card_os_asset_inventory.WriterAndCliTests -v
```

Expected: output/CLI functions are missing.

- [ ] **Step 3: Implement writers and CLI**

CLI:

```bash
python3 scripts/card_os_asset_inventory.py \
  --config migration/card-os/inventory-sources.json \
  --roots migration/card-os/inventory-roots.local.json \
  --output-root migration/card-os/generated
```

Options: `--strict-roots`, `--check`, `--generated-at`, and `--dry-run-summary`. Default `generated_at` is current UTC truncated to seconds. `--check` ignores only `generated_at`, never digest/count/alias differences. `--dry-run-summary` writes JSON to stdout and does not publish a snapshot.

Build one canonical semantic payload from the inventory excluding `generated_at`/`run_id`/`snapshot_digest`, the structured warnings array, metadata-reader versions, duplicate groups, same-name candidates, and derivative candidates. Let `snapshot_hex = sha256(canonical semantic payload)`; set `run_id = "inv_sha256_" + snapshot_hex` and `snapshot_digest = "sha256:" + snapshot_hex`. The Markdown report is derived from that payload and includes both values in front matter, so no circular digest is created. Stage `inventory.json`, `duplicate-report.md`, and `scan-warnings.json` under `generated/.staging-<random>/`; after verifying their shared run ID/digest, rename the directory to `generated/snapshots/<run_id>/`. If that immutable snapshot already exists, verify semantic equality and discard staging. Finally atomically replace `generated/latest.json` with:

```json
{
  "schema": "cognitive-card-migration-latest-v1",
  "run_id": "inv_sha256_<64 hex>",
  "snapshot_digest": "sha256:<64 hex>",
  "inventory": "snapshots/<run_id>/inventory.json",
  "duplicates": "snapshots/<run_id>/duplicate-report.md",
  "warnings": "snapshots/<run_id>/scan-warnings.json"
}
```

Add package scripts:

```json
"inventory:card-os": "python3 scripts/card_os_asset_inventory.py --config migration/card-os/inventory-sources.json --roots migration/card-os/inventory-roots.local.json --output-root migration/card-os/generated",
"test:card-os-inventory": "python3 -m unittest tests.test_card_os_asset_inventory -v"
```

- [ ] **Step 4: Verify GREEN and commit**

```bash
npm run test:card-os-inventory
python3 -m unittest tests.test_card_os_asset_inventory -v
git diff --check
git add package.json migration/card-os/generated/.gitkeep scripts/card_os_asset_inventory.py tests/test_card_os_asset_inventory.py
git commit -m "feat(migration): write deterministic inventory reports"
```

### Task 5: Run the Full Workspace Inventory and Reconcile the Human Record

**Files:**
- Generate: `migration/card-os/generated/latest.json`
- Generate: `migration/card-os/generated/snapshots/<run_id>/inventory.json`
- Generate: `migration/card-os/generated/snapshots/<run_id>/duplicate-report.md`
- Generate: `migration/card-os/generated/snapshots/<run_id>/scan-warnings.json`
- Modify: `docs/cognitive-card-os-asset-migration-inventory.md`
- Modify: `docs/cognitive-card-os-roadmap.md`
- Modify: `README.md`

- [ ] **Step 1: Establish a before-scan mutation guard**

Require a clean tracked worktree before the production scan; untracked historical `outputs/` is expected and remains untouched. Record the starting commit. For every declared root, record eligible file count, total byte count, and a listing of device, inode, relative path, size, mtime-ns, and ctime-ns in `/tmp/card-os-inventory-before.json`. The guard is diagnostic only and is not committed.

```bash
git diff --exit-code
git diff --cached --exit-code
python3 scripts/card_os_asset_inventory.py \
  --config migration/card-os/inventory-sources.json \
  --roots migration/card-os/inventory-roots.local.json \
  --dry-run-summary > /tmp/card-os-inventory-before.json
```

`--dry-run-summary` is the Task 4 contract: it stats declared eligible regular files, counts bytes, hashes sorted `(device, inode, relative_path, size_bytes, mtime_ns, ctime_ns)` tuples, and never hashes file content or writes outputs.

- [ ] **Step 2: Generate the canonical snapshot**

```bash
npm run inventory:card-os
python3 scripts/card_os_asset_inventory.py \
  --config migration/card-os/inventory-sources.json \
  --roots migration/card-os/inventory-roots.local.json \
  --output-root migration/card-os/generated \
  --check
```

Expected: both commands exit 0. Missing declared roots are allowed only when recorded in warnings; any unreadable file or changed-source warning must be investigated before commit.

- [ ] **Step 3: Re-run the mutation guard**

```bash
python3 scripts/card_os_asset_inventory.py \
  --config migration/card-os/inventory-sources.json \
  --roots migration/card-os/inventory-roots.local.json \
  --dry-run-summary > /tmp/card-os-inventory-after.json
cmp /tmp/card-os-inventory-before.json /tmp/card-os-inventory-after.json
python3 scripts/card_os_asset_inventory.py \
  --config migration/card-os/inventory-sources.json \
  --roots migration/card-os/inventory-roots.local.json \
  --output-root migration/card-os/generated \
  --check
```

Expected: `cmp` and the second full content-hash check exit 0. If not, stop and inspect; do not delete or repair source files automatically.

- [ ] **Step 4: Reconcile documentation using measured values only**

Update the human inventory with generated alias/content/duplicate/byte counts, warnings, config digest, and links to all three generated files. Update `MIG-01` to `DONE` only if every declared primary root was scanned and there are no unreadable or changed-source warnings. Otherwise keep it `IN PROGRESS` with the exact warning count and next action.

README must link the source config, inventory, duplicate report, and regeneration command.

- [ ] **Step 5: Verify and commit the snapshot**

```bash
npm run test:card-os-inventory
npm run inventory:card-os
python3 scripts/card_os_asset_inventory.py \
  --config migration/card-os/inventory-sources.json \
  --roots migration/card-os/inventory-roots.local.json \
  --output-root migration/card-os/generated \
  --check
git diff --check
git diff -- README.md docs/cognitive-card-os-roadmap.md docs/cognitive-card-os-asset-migration-inventory.md migration/card-os/generated
RUN_ID="$(python3 -c 'import json; print(json.load(open("migration/card-os/generated/latest.json", encoding="utf-8"))["run_id"])')"
git add migration/card-os/generated/latest.json "migration/card-os/generated/snapshots/$RUN_ID" docs/cognitive-card-os-asset-migration-inventory.md docs/cognitive-card-os-roadmap.md README.md
git commit -m "docs(migration): record canonical asset inventory snapshot"
```

---

## Final Verification Gate

- [ ] Confirm `git diff --check` passes and only intended governance files changed.
- [ ] Confirm source-root before/after device/inode/name/size/mtime/ctime summaries are byte-for-byte identical and the post-scan full-hash `--check` passes.
- [ ] Confirm every asset has a valid digest, stable ID, non-empty alias list, measured size, deterministic `media_types`, alias-level metadata status, `rights_status=review_required`, and `target_package_id=null`.
- [ ] Confirm duplicate groups contain at least two aliases with the same full SHA-256.
- [ ] Confirm same-name/different-content candidates are reported but not merged.
- [ ] Confirm `dist`, `tmp`, `.git`, `node_modules`, `.DS_Store`, and symlink targets were not inventoried.
- [ ] Confirm the requested thread ID `019f02ca-cf3c-79e0-919d-9f8b90a076db` appears on every Shenzhen plant alias.
- [ ] Confirm `spider-verse` and `paw-patrol` remain `legacy_gallery`, not Card OS package candidates.
- [ ] Run an independent review focused on accidental writes, nondeterminism, path leakage, overclaiming structural completeness, and duplicate-ID collisions.
