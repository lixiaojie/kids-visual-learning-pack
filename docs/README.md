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
| [Project Documentation Governance Design](superpowers/specs/2026-07-24-project-documentation-governance-design.md) | Cross-model documentation governance | Active |

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
| [Project Documentation Governance Implementation](superpowers/plans/2026-07-24-project-documentation-governance-implementation.md) | Current implementation plan | Active |

## Operations, Compliance, and Decisions

| Document | Role | Status |
| --- | --- | --- |
| [Content IP Risk Register](compliance/content-ip-risk-register.md) | Content and copyright constraints | Canonical Current |
| [WeChat Mini-Program Checklist](compliance/wechat-miniprogram-checklist.md) | Mini-program compliance checklist | Active |
| [ADR Template](decisions/ADR-TEMPLATE.md) | Long-term decision record template | Canonical Current |

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
