# Project Documentation Map

- Last Reviewed: 2026-07-24
- Next Review Due: 2026-08-24

Start with [PROJECT_CONTEXT](../PROJECT_CONTEXT.md). This file is the only canonical map of formal project documentation; it does not replace code, tests, task state, or handoff records.

## Canonical Current Docs

| Document | Role | Status |
| --- | --- | --- |
| [Project README](../README.md) | Product purpose, commands, and local entrypoints | Canonical Current |
| [Project Context](../PROJECT_CONTEXT.md) | Thin root index and read order | Canonical Current |
| [Project Structure](project-structure.md) | Repository module layout | Canonical Current |
| [Architecture Iteration v1.3](architecture-iteration-v1.3.md) | Current H5 and mini-program architecture baseline | Canonical Current |
| [Cross-Renderer Decisions](cross-renderer-decisions.md) | Intentional renderer differences and parity decisions | Canonical Current |
| [Card OS System Design](cognitive-card-os-system-design.md) | Normative Card OS architecture entrypoint | Canonical Current |
| [Card OS Roadmap](cognitive-card-os-roadmap.md) | Active Card OS task ledger | Active |
| [Card OS Deployment Runbook](operations/cognitive-card-server-deployment-2026-07-14.md) | Production deployment and operations truth | Canonical Current |

## Current Task and Handoff

| Document | Role | Status |
| --- | --- | --- |
| [Current Task](ai/CURRENT_TASK.md) | Unique current execution scope | Active |
| [Latest Handoff](ai/HANDOFF.md) | Latest verified execution state | Active |
| [Backlog](ai/BACKLOG.md) | Non-Card-OS candidate work | Active |
| [Agent Infrastructure](ai/README.md) | Cross-model collaboration workflow | Canonical Current |
| [Start Prompts](ai/START_PROMPTS.md) | Copy-ready recovery and handoff prompts | Canonical Current |
| [Local Configuration Boundary](ai/LOCAL_CONFIG.md) | Private-data and local-config rules | Canonical Current |

## Active Product and Architecture Docs

| Document | Role | Status |
| --- | --- | --- |
| [Project Spec v2.1](spec-v2.md) | Baseline product and content model used by v1.3 architecture | Active |
| [EdgeOne and Mini-Program Alignment](edgeone-miniprogram-alignment-spec-v1.md) | Cross-channel content alignment specification | Active |
| [Yutou Verse Main Tracking v1.2](yutou-verse-main-tracking-spec-v1.2.md) | Interaction-evidence tracking draft | Needs Review |
| [Kids World Image Generation Handoff](kids-world-image-generation-handoff.md) | Topic-level image generation state | Active |
| [Card OS Asset Migration Inventory](cognitive-card-os-asset-migration-inventory.md) | Historical asset source inventory | Active |

## Active Designs and Plans

### Designs

| Document | Role | Status |
| --- | --- | --- |
| [Mobile Scene Deck Design](superpowers/specs/2026-06-23-mobile-scene-deck-design.md) | Mobile scene deck design | Needs Review |
| [Card OS Pro Subscriber Execution Design](superpowers/specs/2026-07-13-cognitive-card-pro-subscriber-execution-design.md) | Pro-client execution architecture | Approved |
| [Card OS Server Deployment Design](superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md) | Production deployment architecture | Implemented |
| [Card OS Thin Skill Release Design](superpowers/specs/2026-07-15-cognitive-card-thin-skill-release-design.md) | Thin Skill distribution architecture | Approved |
| [Card OS Trusted Upstream Compiler Design](superpowers/specs/2026-07-31-cognitive-card-trusted-upstream-compiler-design.md) | API-01 trusted upstream compiler and core snapshot design | Approved |
| [Card OS Knowledge Core and Projection Design](superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md) | Knowledge-first content model, learning layers, multi-projection architecture, and complexity budget | Approved |
| [Knowledge Library Revision and Current Design](superpowers/specs/2026-08-30-knowledge-library-revision-current-design.md) | Server-side candidate intake, immutable four-object revisions, current pointer, and unlist_current | Approved |
| [Projection Family Selection Design](superpowers/specs/2026-08-30-projection-family-selection-design.md) | Deterministic Projection family recommendation, alternatives, and explicit override without a fifth governed object | Approved |
| [Knowledge Library HTTP/DB Wiring Design](superpowers/specs/2026-08-30-knowledge-library-http-db-wiring-design.md) | Controlled loopback HTTP adapters for the file-backed knowledge library and join-path compiled jobs against current | Approved |
| [Knowledge Browse and Projection Confirmation Design](superpowers/specs/2026-08-30-knowledge-browse-projection-confirmation-design.md) | Confirmation-point-1 UI: read-only library browse plus projection-family selection; not PORTAL-01 | Approved |
| [Knowledge Four-Card Converter Design](superpowers/specs/2026-08-30-knowledge-four-card-converter-design.md) | CONV-01: library current to joined four-card generation-input; source_id mapping; not production-record emit | Approved |
| [Age and Language Adapter Design](superpowers/specs/2026-08-31-age-language-adapter-design.md) | AGE-01: versioned server adapters for age-3-4 / age-5-6 child Chinese and beginner English; fact identity unchanged | Approved |
| [Locked Four-Card Render Design](superpowers/specs/2026-08-31-locked-four-card-render-design.md) | RENDER-01: content-lock four-card layout, copy_plan COPY, A4 PDF; not PORTAL/QA/PUBLISH | Approved |
| [Strict QA and Human Review Design](superpowers/specs/2026-08-31-strict-qa-human-review-design.md) | QA-01: machine QA gate before awaiting_review; human actor, decision, and audit; not PORTAL/PUBLISH | Approved |
| [Immutable Package Publish Design](superpowers/specs/2026-08-31-immutable-package-publish-design.md) | PUBLISH-01: immutable package revision; withdraw/replace keep history; not PORTAL | Approved |
| [Rabbit End-to-End Acceptance Design](superpowers/specs/2026-08-31-rabbit-end-to-end-acceptance-design.md) | ACCEPT-01: rabbit Shenzhen age-5-6 bilingual print through lock/render/QA/package; local same-version view; not PORTAL | Approved |
| [Classification Registry Design](superpowers/specs/2026-08-31-classification-registry-design.md) | KNOW-01: domain × form × subtype coverage matrix, server registry, authoring-controlled classification; not PORTAL | Approved |
| [Template Family Registry Design](superpowers/specs/2026-08-31-template-family-registry-design.md) | TMPL-01: four-card family coverage, stable skeletons, TEMPLATE_GAP, cross-object fixtures; not PORTAL | Approved |
| [Published Artifact Gallery Design](superpowers/specs/2026-08-31-published-artifact-gallery-design.md) | PORTAL-01: read-only published package gallery; not BROWSE-01; not a knowledge CMS | Approved |
| [Card OS Kids-World Knowledge Entry Design](superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md) | SITE-01: parallel gallery then cut over the knowledge home; not SITE-02 URL mapping | Approved |
| [Card OS Legacy URL and Rollback Design](superpowers/specs/2026-08-31-card-os-legacy-url-and-rollback-design.md) | SITE-02: old kids-world URL mapping, substitute pages, and one-deploy activeMode rollback | Approved |
| [Operator Knowledge Workbench Design](superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md) | WB-01: token-gated read-only knowledge library and projection menu; not PORTAL-01; not WB-02/WB-03 | Approved |
| [Four-Card Text-Mature Projection Design](superpowers/specs/2026-08-31-four-card-text-mature-projection-design.md) | Parked; superseded for WB-02 by mapping-scheme spec; leftover packing overflow not adopted by WB-03 | Parked |
| [Operator Mapping Scheme Design](superpowers/specs/2026-09-01-operator-mapping-scheme-design.md) | WB-02: ops select family and lock slot mapping; no PNG/gallery | Approved |
| [Operator Mapping Artifact Publish Design](superpowers/specs/2026-09-01-operator-mapping-artifact-publish-design.md) | WB-03: mapping revision → text-mature four-card → local gallery; no image gen; no production | Approved |
| [Mapping-Artifact Weighted Layout Design](superpowers/specs/2026-09-02-mapping-artifact-weighted-layout-design.md) | WB-03 print binding: content-sized zone heights for mapping-artifact-v1; not a Core contract; not ACCEPT-01 | Approved |
| [Operator Free-Prompt Knowledge Compile Design](superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md) | API-01 this slice: ops expands copyable ChatGPT prompt, ingests reply into four-object current; no API executor | Approved |
| [Operator Illustration Hero Page Design](superpowers/specs/2026-09-02-operator-illustration-hero-page-design.md) | IMG-01 first slice: copyable ChatGPT image prompt, one PNG upload, ops page of hero + active claims; no image API | Approved |
| [Operator Composite Projection Display Design](superpowers/specs/2026-09-03-operator-composite-projection-display-design.md) | COMPOSE-01: hero PNG + locked four-card text → HTML page and OBS print image band; no burn-in | Approved |
| [Projection Legend v1 Design](superpowers/specs/2026-09-03-projection-legend-v1-design.md) | LEGEND-01: closed cognitive roles + visual grammar; empty modules omitted; not knowledge taxonomy | Approved |
| [Multi-View Wordless Assets Design](superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md) | IMG-02: optional extra wordless PNGs keyed by legend role+view; IMG-01 isolate hero kept; not RENDER-02 | Approved |
| [Legend Module Chrome Design](superpowers/specs/2026-09-04-legend-module-chrome-design.md) | RENDER-02: regroup compose HTML by legend role; print PNG unchanged; extra views by sha only; not IMG prompts | Approved |
| [Entity Knowledge Coverage Design](superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md) | KNOW-03: pluggable coverage + seven-topic compatibility suite; not projection | Approved/Implemented |
| [Knowledge Suite Library Seed Design](superpowers/specs/2026-09-01-knowledge-suite-library-seed-design.md) | KNOW-04: seed six allowed suite topics into production library current; not Gwen; not WB-02 | Approved/Implemented |
| [Knowledge Core Contract Pilot Evidence](knowledge-core-contract-pilot-evidence.md) | Verified local evidence for the four-object contract fixtures, zero-runtime boundary, and full-suite baseline limitation | Verified |
| [Card OS ACCEPT-01 Evidence](cognitive-card-os-accept-01-evidence.md) | Verified local rabbit print pack: four cards, A4 PDF, approved QA, immutable package, same-version local view | Verified |
| [Project Documentation Governance Design](superpowers/specs/2026-07-24-project-documentation-governance-design.md) | Cross-model documentation governance | Implemented |

### Plans

| Document | Role | Status |
| --- | --- | --- |
| [Mobile Scene Deck Implementation](superpowers/plans/2026-06-23-mobile-scene-deck-implementation-plan.md) | Mobile scene deck implementation plan | Needs Review |
| [Card OS Asset Inventory and Dedup](superpowers/plans/2026-07-13-cognitive-card-asset-inventory-dedup-plan.md) | Asset inventory implementation | Needs Review |
| [Card OS Remote API Auth Protocol](superpowers/plans/2026-07-13-cognitive-card-remote-api-auth-protocol-plan.md) | API and authentication implementation | Needs Review |
| [Card OS Subscriber Execution Foundation](superpowers/plans/2026-07-13-cognitive-card-subscriber-execution-foundation-plan.md) | Subscriber-client foundation | Needs Review |
| [Card OS Server Deployment](superpowers/plans/2026-07-14-cognitive-card-server-deployment-plan.md) | Deployment execution plan | Needs Review |
| [Card OS Skill Registry](superpowers/plans/2026-07-15-cognitive-card-skill-registry-plan.md) | Skill registry execution plan | Needs Review |
| [Card OS Thin Client](superpowers/plans/2026-07-15-cognitive-card-thin-client-plan.md) | Thin-client execution plan | Needs Review |
| [Card OS Knowledge Core Contract Pilot](superpowers/plans/2026-08-19-knowledge-core-contract-pilot-implementation-plan.md) | Completed canonical-doc convergence and server-authoritative four-object contract fixture plan | Completed |
| [Project Documentation Governance Implementation](superpowers/plans/2026-07-24-project-documentation-governance-implementation.md) | Completed documentation-governance implementation plan | Completed |
| [Operator Knowledge Workbench Implementation](superpowers/plans/2026-08-31-operator-knowledge-workbench-implementation-plan.md) | WB-01 execution plan: token-gated ops HTML and admin knowledge-library JSON | Completed |
| [Operator Mapping Scheme Implementation](superpowers/plans/2026-09-01-operator-mapping-scheme-implementation-plan.md) | WB-02 execution: safety registry, preview/lock mapping, ops third panel; not PNG | Completed |
| [Operator Mapping Artifact Publish Implementation](superpowers/plans/2026-09-01-operator-mapping-artifact-publish-implementation-plan.md) | WB-03 execution: convert_mapping, fail-closed pack, generate/publish ops; not production | Completed |
| [Mapping-Artifact Weighted Layout Implementation](superpowers/plans/2026-09-02-mapping-artifact-weighted-layout-implementation-plan.md) | WB-03 print binding: shared weighted zone heights; not Core; not ACCEPT-01 equal split | Completed |
| [Operator Free-Prompt Knowledge Compile Implementation](superpowers/plans/2026-09-02-operator-free-prompt-knowledge-compile-implementation-plan.md) | API-01 execution: copyable ChatGPT prompt, reply compile, confirm current; worktree only, not production | Completed |
| [Operator Illustration Hero Page Implementation](superpowers/plans/2026-09-02-operator-illustration-hero-page-implementation-plan.md) | IMG-01 first slice: versioned hero prompt, one authenticated PNG, identity-pinned active-claim page; not production | Completed |
| [Operator Composite Projection Display Implementation](superpowers/plans/2026-09-03-operator-composite-projection-display-implementation-plan.md) | COMPOSE-01: compose gate, ops HTML, OBS image band; not production | In Progress |
| [Projection Legend v1 Implementation](superpowers/plans/2026-09-03-projection-legend-v1-implementation-plan.md) | LEGEND-01: registry, role resolve, compile gate, mapping legend block; not IMG-02/RENDER-02 | In Progress |
| [Multi-View Wordless Assets Implementation](superpowers/plans/2026-09-03-multi-view-wordless-assets-implementation-plan.md) | IMG-02: optional extra PNGs on the same illustration-intent; IMG-01 hero kept; not RENDER-02 | In Progress |
| [Legend Module Chrome Implementation](superpowers/plans/2026-09-04-legend-module-chrome-implementation-plan.md) | RENDER-02: compose HTML modules by legend role; print PNG unchanged; not IMG prompts; server `427bf89` local; not production | In Progress |

## Operations, Compliance, and Decisions

| Document | Role | Status |
| --- | --- | --- |
| [Content IP Risk Register](compliance/content-ip-risk-register.md) | Content and copyright constraints | Canonical Current |
| [WeChat Mini-Program Checklist](compliance/wechat-miniprogram-checklist.md) | Mini-program compliance checklist | Active |
| [ADR Template](decisions/ADR-TEMPLATE.md) | Long-term decision record template | Canonical Current |
| [ADR-001 Card OS Client Contract and Production Core Ownership](decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md) | Packet contract owns M1 claim/submit; production core stays server-side; package-v5 upload defers to PUBLISH-01 | Accepted |
| [ADR-002 Card OS Knowledge Core and Projection Architecture](decisions/ADR-002-knowledge-core-and-projection-architecture.md) | Knowledge Core owns facts and scope; learning design and multiple projections remain downstream | Accepted |
| [ADR-003 Knowledge Pipeline Workspace and Branch Governance](decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md) | Kids governs, server stores knowledge, thin Skill executes; live worktrees are capped until the join contract exists | Accepted |
| [ADR-004 Single-Operator Main Flow](decisions/ADR-004-single-operator-main-flow.md) | 单人主路径优先；SKILL-02/OPS-01 单人门禁关闭；BROWSE-01 是确认点 1，不等于 PORTAL-01 | Accepted |
| [ADR-005 Knowledge Entry Cutover Without Topic Remakes](decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md) | SITE-01 可在 13 个 C 级主题冻结后切主入口；旧 URL 与回滚属 SITE-02 | Accepted |

## Codex Memory Snapshots

These are manually curated, secondary retrieval material. They preserve reusable Card OS deployment safeguards and local Cognitive Card OS Skill-installation lessons, but do not establish current implementation or architecture truth.

| Document | Role | Status |
| --- | --- | --- |
| [Codex Memory Snapshot](knowledge/codex-memory/README.md) | Curated project-local snapshot index, including Card OS deployment operations and local Skill installation lessons | Secondary Snapshot |

## Historical Reference

| Document | Role | Status |
| --- | --- | --- |
| [Kids World Refactor Design](2026-05-11-kids-world-refactor-design.md) | Completed refactor design provenance | Historical Reference |
| [Kids World Refactor Plan](2026-05-11-kids-world-refactor-plan.md) | Completed refactor plan provenance | Historical Reference |
| [Architecture Review v1](architecture-review-v1.md) | Earlier architecture assessment | Historical Reference |
| [Cicada Life Spec v1.1](cicada-life-project-spec-v1.1.md) | Observation-template example | Historical Reference |
| [Cross-Renderer Parity Plan v1](cross-renderer-parity-plan-v1.md) | Earlier parity execution plan | Historical Reference |

Historical reference files remain in place until explicit replacement evidence justifies archival.

## Archive

[Archive Manifest](archive/README.md) records every superseded document, its retained location, reason, and replacement. Archived files are never first-read context.

## Maintenance

- Update this map whenever a formal Markdown file is added, moved, superseded, or archived.
- Review this map and the memory snapshot every 31 days.
- Run `bash scripts/ai/check-doc-governance.sh` and `bash scripts/ai/check-agent-state.sh`.
