# WB-01 Operator Knowledge Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve a token-gated `/card-os/ops/` shell and admin knowledge-library JSON so an operator can read AUTHOR-02 rabbit Knowledge Core and the Projection family menu without changing the public gallery.

**Architecture:** Add a `knowledge_ops` HTTP adapter next to `four_card_portal`. HTML shells contain no claims. JSON lives under `/card-os/api/v1/admin/knowledge-library*` with `admin` scope and calls existing `KnowledgeLibrary` plus `signals_from_package_dir` / `select_projection_family`. Nginx prefix-proxies `/card-os/ops/` before the catch-all 404. Production library seed is a later install step and must not rewrite the ACCEPT-01 package catalog.

**Tech Stack:** Python 3 FastAPI/Starlette unittest, existing Card OS auth middleware, kids-repo Nginx snippet + `tests/test_card_os_deployment_assets.py`.

## Global Constraints

- Do not change four-object schema, v1 FACT keys, AUTHOR-05 defaults, or ACCEPT-01 package bytes.
- Do not bind Uvicorn off loopback; do not merge server `main` unless the session explicitly authorizes it.
- Public `/card-os/` gallery copy and CTA stay unchanged; no ops link on the gallery.
- HTML shells must not embed claims, source locators, or family reason text.
- Unauthenticated admin JSON must not return HTTP 200 with an empty list.
- Invalid slug and missing topic/revision on ops JSON both use `OPS_NOT_FOUND` (404).
- Projection GET with no current uses `OPS_NO_CURRENT` (409).
- Existing `GET /knowledge-library` (`read`) behavior stays.
- Do not add `uv.lock` or `outputs/` to commits.
- Production: seed AUTHOR-02 rabbit as library current before reloading `/card-os/ops/`.

---

### Task 1: Admin JSON + ops HTML (server)

**Files:**
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/knowledge_ops/__init__.py`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/knowledge_ops/pages.py`
- Create: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/knowledge_ops/http.py`
- Create: `.worktrees/cognitive-card-server-knowledge-core/tests/test_http_knowledge_ops.py`
- Modify: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/http/app.py` (`PROTECTED_ROUTES`, `create_app`, `status` mapping via errors.py)
- Modify: `.worktrees/cognitive-card-server-knowledge-core/src/cognitive_card_server/http/errors.py` (`OPS_NO_CURRENT` → 409)

**Interfaces:**
- Consumes: `KnowledgeLibrary.list_topics/get_current/list_revisions/get_revision`, `load_package`, `signals_from_package_dir`, `select_projection_family`, `require_admin`
- Produces: `attach_ops_routes(app, api_router, settings, require_admin, clock)`

- [x] **Step 1: Write failing HTTP tests** in `tests/test_http_knowledge_ops.py` covering: admin list/current/revision/projection-family on `rabbit-real.json`; submit/read tokens 403; no token 401; HTML `/card-os/ops/` and `/card-os/ops/rabbit` 200 without claims; HEAD same status; invalid slug and missing revision `OPS_NOT_FOUND`; projection without current `OPS_NO_CURRENT`; chosen `chaptered-guide` and four-card `discouraged`.
- [x] **Step 2: Run tests, expect collection/import or 404 failures**
- [x] **Step 3: Implement pages + http adapter + PROTECTED_ROUTES + error mapping**
- [x] **Step 4: Run `python3 -m unittest tests.test_http_knowledge_ops tests.test_http_knowledge_library tests.test_http_portal -v`** Expected: PASS
- [x] **Step 5: Commit on server branch only if the operator asked** — `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`

### Task 2: Nginx ops prefix (kids)

**Files:**
- Modify: `ops/cognitive-card-server/nginx/card-os.conf`
- Modify: `tests/test_card_os_deployment_assets.py` (`EXPECTED_NGINX` and location selection assertions)

- [x] **Step 1: Add failing assertion that `/card-os/ops/rabbit` selects `^~ /card-os/ops/`**
- [x] **Step 2: Add `location = /card-os/ops` 308 and `location ^~ /card-os/ops/` GET/HEAD proxy (same timeouts as packages), before catch-all**
- [x] **Step 3: Sync `EXPECTED_NGINX` byte-for-byte**
- [x] **Step 4: Run `python3 -m unittest tests.test_card_os_deployment_assets tests.test_card_os_release -v`** Expected: PASS（67 tests；未在沙箱跑完整 `npm run test:card-os-deploy`）

### Task 3: Governance docs

**Files:**
- Modify: `docs/ai/CURRENT_TASK.md`, `docs/ai/HANDOFF.md`, `docs/cognitive-card-os-roadmap.md`, `docs/README.md`, `docs/operations/cognitive-card-server-deployment-2026-07-14.md` (append WB-01 local evidence; do not rewrite 0.3.1 tables)
- Create: `docs/superpowers/plans/2026-08-31-operator-knowledge-workbench-implementation-plan.md` (this file)

- [x] Mark WB-01 implementation in progress until production seed+reload; do not claim production Done until rabbit library current is chaptered-guide and ops is proxied.

### Task 4: Production seed and reload (blocked on server commit + release)

Do not reload Nginx onto an empty library. After a server commit and immutable release install:

1. Compile `examples/authoring/rabbit-real.json` with `compile_authoring_request` (no four-card overlay).
2. `publish` into `$CARD_OS_CANDIDATE_ROOT/knowledge-library` as `rabbit` current.
3. Confirm catalog `package_sha256` for ACCEPT-01 rabbit is unchanged.
4. Reload Nginx snippet including `/card-os/ops/`.
5. Check: unauthenticated ops HTML has no claims; admin JSON shows 4 units / 8 propositions / 4 sources; gallery PDF still 200 with the same digest.

This task is not executed until the operator authorizes a server commit and production install.
