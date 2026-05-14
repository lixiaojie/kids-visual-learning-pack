# EdgeOne + Mini Program Alignment Spec v1

> Date: 2026-05-14  
> Branch audited: `codex-miniprogram-b1-b2`  
> Goal: one content source, two renderers: EdgeOne/Web and WeChat Mini Program.

## 1. Product Target

The project should maintain a single Kids World content source and expose it through two renderers:

- EdgeOne/Web renderer: Vite + React app under `boards/kids-world`.
- Mini Program renderer: Taro + React app under `apps/miniprogram`.
- Shared content layer: `packages/kids-content`, the only runtime content API that both renderers depend on.

The intended dependency direction is:

```text
boards/kids-world/src/data/*.json
boards/kids-world/public/assets/**
channel-policy.json
        |
        v
packages/kids-content
        |
        +--> boards/kids-world Web renderer
        |
        +--> apps/miniprogram Taro renderer
```

Renderer code may differ. Content loading, locale merge, channel visibility, topic lookup, and generated-image URL resolution must not fork by renderer.

`packages/kids-content` must be independent of Web renderer runtime code. During the transition it may directly import shared JSON content and manifests from `boards/kids-world/src/data/**`, but it must not import Web-side loaders, components, pages, runtime config, or asset-map helpers. The dependency direction must never degrade into Web runtime -> package -> Mini Program.

## 2. Current Audit Snapshot

Fresh verification commands run during this audit:

| Check | Command | Result |
| --- | --- | --- |
| Working tree | `git status -sb` | Clean, branch `codex-miniprogram-b1-b2` |
| Content + scaffold validation | `npm run validate` | Passed |
| EdgeOne production build | `npm run build:edgeone` | Passed, `dist check passed for web-production: 100 files` |
| Mini Program build | `npm run build:weapp` in `apps/miniprogram` | Passed with warnings |
| Topic policy parity | Node policy check | 18 registry topics, 12 render-ready topics, 12 Mini Program visible topics, no missing/extra render-ready topic |

Mini Program build warnings to track:

- Tailwind warning: root `tailwind.config.cjs` has missing or empty `content`.
- Webpack warning: `common.js` is 568 KiB and exceeds the recommended 244 KiB limit.
- Webpack warning: no async chunks.

## 3. Current Implementation Status

### 3.1 Content Source

Current source files:

- Topic content: `boards/kids-world/src/data/topics/*.json`.
- English overlays: `boards/kids-world/src/data/locales/en-US/topics/*.json`.
- Exploration map: `boards/kids-world/src/data/exploration-map.json`.
- English map overlay: `boards/kids-world/src/data/locales/en-US/exploration-map.json`.
- Topic registry: `boards/kids-world/src/data/topic-registry.json`.
- Generated image manifest: `boards/kids-world/src/data/image-generation-manifest.json`.
- Channel policy: `channel-policy.json`.

Current topic set:

- Registry topics: 18.
- Render-ready topics: 12.
- Validated topic JSON files: 12.
- Validated English overlays: 12.
- Validated topic asset references: 135.

Render-ready topics currently visible in both production Web and Mini Program:

- `animal-classification-tree`
- `blood-cells-3d`
- `digestion`
- `dinosaurs`
- `earth-climate-cities`
- `ecosystem`
- `insects-and-spiders`
- `llm-kids-basics`
- `moon-phases`
- `robots`
- `solar-system-overview`
- `water-cycle`

Status: content source is effectively shared.

Gap: content runtime is not yet fully shared.

### 3.2 Channel Policy

`channel-policy.json` defines three channels:

| Channel | Visible boards | Hidden boards | Visible topics |
| --- | --- | --- | --- |
| `web-production` | `kids-world` | `paw-patrol`, `spider-verse` | `all-render-ready` |
| `web-preview` | `kids-world`, `paw-patrol`, `spider-verse` | none | `all` |
| `miniprogram` | `kids-world` | `paw-patrol`, `spider-verse` | explicit 12-topic list |

Status: topic visibility is currently aligned for render-ready Kids World content.

Gap: Web and Mini Program apply the policy through different implementations.

### 3.3 Shared Package

Current package:

- `packages/kids-content/src/index.ts`
- `packages/kids-content/src/map.ts`
- `packages/kids-content/src/media.ts`

Current exports include:

- `getTopic`
- `hasTopicData`
- `getMap`
- `getVisibleTopicSlugs`
- `getCdnAssetUrl`
- `getGeneratedImageUrl`
- shared types such as `Topic`, `Locale`, `ExplorationMap`

Status: package exists and validates.

Gaps:

- `packages/kids-content/src/index.ts` re-exports topic loading from `boards/kids-world/src/data/loaders/load-topic.ts`.
- `packages/kids-content/src/map.ts` duplicates channel-policy logic already present in `boards/kids-world/src/data/loaders/load-map.ts`.
- `packages/kids-content/src/media.ts` imports Web asset-map code directly.
- The package is not yet the only content runtime used by both renderers.

### 3.4 EdgeOne/Web Renderer

Current Web entry points:

- `boards/kids-world/src/App.tsx`
- `boards/kids-world/src/pages/HomePage.tsx`
- `boards/kids-world/src/pages/TopicPage.tsx`

Current Web content imports:

- `App.tsx` imports `getMap` from `./data/loaders/load-map`.
- `App.tsx` imports `hasTopicData` from `./data/loaders/load-topic`.
- `TopicPage.tsx` imports `getTopic` from `../data/loaders/load-topic`.
- `Topbar.tsx` also imports `getTopic` from local loaders.

Status:

- EdgeOne build is reproducible through `edgeone.json`.
- Production build hides old animation boards.
- Web has locale selection for `zh-CN` and `en-US`.
- Web renders the richest topic page version: hero, scene, classification groups, representative objects, mechanisms, compare pairs, click tasks, speak templates, parent tips, related topics.

Gap: Web does not consume `@yutou/kids-content` as its primary content API.

### 3.5 Mini Program Renderer

Current Mini Program entry points:

- `apps/miniprogram/src/pages/index/index.tsx`
- `apps/miniprogram/src/pages/topic/index.tsx`
- `apps/miniprogram/src/pages/about/index.tsx`

Current Mini Program content import shape:

- Pages import from `@yutou/kids-content`.
- `apps/miniprogram/config/index.ts` aliases `@yutou/kids-content` to `apps/miniprogram/src/lib/kids-content.ts`.

Current local adapter:

- `apps/miniprogram/src/lib/kids-content.ts`

Status:

- Taro app compiles to WeChat Mini Program.
- Mini Program uses `channel-policy.json` and the same JSON topic files.
- Mini Program has share handlers for friend and timeline sharing.
- Mini Program has privacy/about page.
- Mini Program renders all 12 visible topics on the home page.

Gaps:

- The local adapter duplicates topic imports, English overlay imports, `deepMerge`, generated image mapping, CDN URL resolution, and channel filtering.
- Type coverage is loose in the adapter: `Topic` is `any`.
- Mini Program topic rendering is intentionally thinner than Web:
  - representative objects: first 5 only.
  - mechanism steps: first 4 only.
  - compare pairs: first 3 only.
  - click tasks: first 3 only.
  - parent tips: first 3 only.
  - no classification-group interaction.
  - no related-topic navigation section.
  - no visible locale switch on the home page.
- Current validation requires the local adapter file, so it reinforces the temporary architecture instead of rejecting it.

## 4. Alignment Decision

Current state is:

```text
Same JSON content source: yes
Same visible topic set: yes
Same buildable product surfaces: yes
Same shared content runtime: no
Same renderer completeness: partial
```

Therefore the project is not yet fully aligned with "one content source, two renderers".

The corrected target is:

```text
Content JSON + assets + channel-policy
        |
        v
@yutou/kids-content
        |
        +--> Web renderer imports package APIs
        |
        +--> Mini Program renderer imports package APIs
```

No renderer may own a private implementation of:

- topic JSON import map.
- locale overlay merge.
- channel visibility filtering.
- render-ready topic filtering.
- generated asset manifest lookup.
- CDN URL construction.

## 5. Required Shared Content API

`@yutou/kids-content` must provide the stable API below.

### 5.1 Types

- `Locale = "zh-CN" | "en-US"`
- `ContentChannel = "web-production" | "web-preview" | "miniprogram"`
- `Topic`
- `ExplorationMap`
- `TopicCard`
- `GeneratedImageAsset`
- `ClickTask`
- `TaskResult`

### 5.2 Runtime Functions

| Function | Required behavior |
| --- | --- |
| `getTopic(slug, locale)` | Return localized topic or `null`; uses the single topic import map. |
| `hasTopicData(slug)` | Return true only when topic JSON exists. |
| `getMap(locale, channel)` | Return localized exploration map after applying `channel-policy.json`. |
| `getVisibleTopicSlugs(channel)` | Return visible topic slugs for the channel. |
| `getKnowledgeTopicAssetId(topic)` | Return the generated hero/card asset id for a topic. |
| `getGeneratedImageUrl(assetId, cdnBase?)` | Resolve generated image URL from the manifest. |
| `getCdnAssetUrl(assetPath, cdnBase?)` | Resolve public asset URL with normalized base path. |

`deepMerge` is an internal package helper, not a stable renderer-facing API. Renderer code must call `getTopic` and `getMap` and receive already-localized content. A package-internal test may cover merge behavior, but Web and Mini Program code should not import or call `deepMerge` directly.

### 5.3 Default Channel Rules

- Web renderer must pass `web-production` or `web-preview` explicitly, or resolve it once from `VITE_CHANNEL` and pass it into `getMap`.
- Mini Program renderer must pass `miniprogram` explicitly.
- Shared package may default to `miniprogram` only for Mini Program convenience if every Web call remains explicit.

## 6. Cross-Renderer Parity Matrix

### 6.1 Content Parity

| Item | EdgeOne/Web | Mini Program | Expected |
| --- | --- | --- | --- |
| Topic JSON source | `boards/kids-world/src/data/topics` | same via local adapter | same via `@yutou/kids-content` |
| Locale overlays | Web loaders | local adapter | shared package |
| Topic visibility | `web-production: all-render-ready` | explicit 12 list | both evaluated by shared package |
| Hidden boards | filtered in Web loader/build | filtered in local adapter | shared package policy helper |
| Generated images | Web asset map | local adapter manifest reducer | shared package |
| CDN base | site config/build metadata + package media helper | local adapter default | shared package config |

### 6.2 Renderer Coverage

Mini Program does not need to match Web interaction richness one-for-one, but it must not silently drop core educational content. Section parity should separate education completeness from interaction richness:

| Content class | Meaning | Mini Program strategy |
| --- | --- | --- |
| Core educational content | Required for a child to understand the topic's main cognition chain | Must be fully shown, with folding/accordion allowed |
| Enrichment content | Extra knowledge, parent prompts, or optional depth | May default collapsed or use a documented quantity cap |
| Interaction-only enhancement | Web-specific richer interaction around content already represented elsewhere | May simplify to static cards or lighter controls |

Any `.slice(...)` limit in Mini Program must map to one of these classes and be documented. It must not silently cut a core concept out of the learning path.

| Topic section | EdgeOne/Web | Mini Program current | Mini Program target |
| --- | --- | --- | --- |
| Hero image and copy | yes | yes | yes |
| Scene explanation | yes | yes | yes |
| Classification groups | yes | no | required for parity, or explicitly waived |
| Representative objects | full + interactive | first 5 | mobile-appropriate full/expandable |
| Mechanism steps | full | first 4 | mobile-appropriate full/expandable |
| Secondary mechanism | yes where available | no | required if content exists, or explicitly waived |
| Compare pairs | full | first 3 | mobile-appropriate full/expandable |
| Click tasks | full | first 3 | full task set or documented limit |
| Speak templates | yes | via `TopicSummary` only if covered | explicit parity check needed |
| Parent tips | full | first 3 | full/expandable or documented limit |
| Related topics | yes | no | required for navigation parity |
| Locale switch | yes | query-only | visible Mini Program control if bilingual release is in scope |

### 6.3 Build and Deployment

| Surface | Build command | Required gate |
| --- | --- | --- |
| Shared validation | `npm run validate` | must pass before either renderer build |
| EdgeOne/Web | `npm run build:edgeone` | must pass, production dist must hide old boards |
| Mini Program | `npm run build:weapp` in `apps/miniprogram` | must pass, warnings tracked |

## 7. Cross-Check Checklist

Use this checklist for every future topic iteration.

### 7.1 Content Source

- [ ] Topic base JSON exists under `boards/kids-world/src/data/topics`.
- [ ] English overlay exists under `boards/kids-world/src/data/locales/en-US/topics`.
- [ ] Topic is present in `topic-registry.json`.
- [ ] Topic status is correct: `render-ready` only when both renderers can consume it.
- [ ] All asset IDs referenced by the topic exist in `image-generation-manifest.json`.
- [ ] The topic has no renderer-specific fields.

### 7.2 Channel Policy

- [ ] `web-production` includes the topic through `all-render-ready` or an explicit policy.
- [ ] `miniprogram.visibleTopics` includes the topic only after Mini Program rendering is ready.
- [ ] Hidden boards remain excluded from production and Mini Program.
- [ ] A policy parity script confirms no accidental missing/extra Mini Program render-ready topic.

### 7.3 Shared Package

- [ ] New topic is imported exactly once by shared runtime code or by generated package manifest code.
- [ ] Web renderer does not add a parallel topic import.
- [ ] Mini Program renderer does not add a parallel topic import.
- [ ] `packages/kids-content` does not import Web runtime loaders, components, pages, runtime config, or Web-only asset-map code.
- [ ] `packages/kids-content` uses no Node-only runtime APIs such as `fs`, `path`, runtime filesystem reads, or unsupported dynamic imports.
- [ ] `getTopic(slug, "zh-CN")` returns base content.
- [ ] `getTopic(slug, "en-US")` returns merged content.
- [ ] `getMap(locale, "web-production")` and `getMap(locale, "miniprogram")` return expected cards.

### 7.4 Web Renderer

- [ ] Home card appears or remains hidden according to policy.
- [ ] Topic route works.
- [ ] Locale toggle keeps topic content coherent.
- [ ] All expected topic sections render.
- [ ] Production build does not expose hidden board links or directories.

### 7.5 Mini Program Renderer

- [ ] Home card appears in `miniprogram.visibleTopics` order.
- [ ] Topic page route works with `slug`.
- [ ] Missing slug shows the preparation state.
- [ ] Hero image resolves through CDN URL helper.
- [ ] Share title/path includes the topic slug.
- [ ] Renderer coverage table is updated if any section is intentionally thinner than Web.
- [ ] WeChat Developer Tools preview is checked before submission.

### 7.6 Verification Commands

- [ ] `npm run validate`
- [ ] `npm run build:edgeone`
- [ ] `npm run build:weapp` from `apps/miniprogram`
- [ ] Optional visual smoke test for Web.
- [ ] Optional WeChat Developer Tools preview for Mini Program.

## 8. Required Alignment Work

### P0: Make `packages/kids-content` the Single Runtime Layer

Acceptance criteria:

- `packages/kids-content` does not import Web renderer loaders, components, pages, runtime config, or Web-only asset-map code.
- The package may temporarily import shared JSON content from `boards/kids-world/src/data/**`, but all loading, locale merge, policy filtering, asset lookup, and CDN URL resolution are implemented inside the package.
- Long term, content source should move to `packages/kids-content/data/**` or `packages/kids-content/content/**`, with Web and Mini Program consuming only the package.
- `deepMerge` remains an internal helper unless a documented renderer-facing use case is approved.
- The package is browser/weapp-safe: no `fs`, `path`, runtime filesystem reads, Node-only APIs, or unsupported dynamic imports.
- Taro either transpiles `@yutou/kids-content` from source or consumes a compiled ESM output.
- JSON imports from the shared package are bundled into the Mini Program build.
- Web imports `getMap`, `getTopic`, and `hasTopicData` from `@yutou/kids-content`, directly or through thin compatibility wrappers.
- Mini Program alias points to `packages/kids-content`, not `apps/miniprogram/src/lib/kids-content.ts`.
- `apps/miniprogram/src/lib/kids-content.ts` is removed or reduced to a pure re-export with no content logic.
- Topic import map, locale merge, channel filtering, and generated-image lookup exist in one place.
- `scripts/validate-miniprogram-scaffold.mjs` fails if Mini Program aliases `@yutou/kids-content` to an app-local content adapter.
- Removing `apps/miniprogram/src/lib/kids-content.ts` does not break `npm run build:weapp`.
- A minimum import-contract guard is added in this phase so the next iteration cannot reintroduce local adapters or Web-runtime package imports.

### P1: Add Alignment Validation

Acceptance criteria:

- A validation script compares:
  - render-ready topics from `topic-registry.json`.
  - Mini Program visible topics from `channel-policy.json`.
  - topic import coverage in `@yutou/kids-content`.
  - generated image references for both renderers.
- The script is included in `npm run validate`.
- The script prints actionable missing/extra topic slugs.
- The script fails when Web imports topic/map/media loaders from `boards/kids-world/src/data/loaders/**` instead of the package or a thin package-backed wrapper.
- The script fails when Mini Program aliases `@yutou/kids-content` to an app-local adapter.
- The script fails when `packages/kids-content` imports Web renderer runtime files.
- The script fails when a render-ready topic exists in registry but is missing from shared package import coverage.
- The script fails when a topic references generated image asset IDs missing from `image-generation-manifest.json`.
- Preferred follow-up: add `scripts/generate-kids-content-manifest.mjs` to generate package-side topic imports, locale imports, and image manifest bindings, then validate generated files are up to date.

### P2: Decide Mini Program Renderer Completeness

Acceptance criteria:

- Each topic section is marked as one of:
  - core educational content.
  - enrichment content.
  - interaction-only enhancement.
- Core educational content is fully shown in Mini Program, with folding allowed.
- Enrichment content may be collapsed or quantity-limited only with a documented cap.
- Interaction-only enhancements may be simplified to static cards when the underlying learning content remains available.
- Any simplification must be data-driven and stable, not a silent `.slice(...)` without a documented content class and cap.
- Mini Program UI should not lose required educational content without a product decision.

### P3: Bundle and Warning Cleanup

Acceptance criteria:

- Tailwind warning is either eliminated for Mini Program builds or documented as harmless because Mini Program SCSS does not depend on Tailwind utilities.
- `common.js` size warning is tracked, with a threshold and mitigation plan if it grows.

## 9. Definition of Aligned

The two versions are considered aligned only when all conditions below are true:

- Both renderers build from the same content package APIs.
- No renderer contains a private topic loader or generated-image manifest reducer.
- `packages/kids-content` does not depend on Web renderer runtime code.
- Removing the Mini Program app-local adapter does not break Taro compilation.
- `npm run validate` checks the alignment contract.
- EdgeOne/Web and Mini Program visible topic sets are intentionally equal or intentionally different by `channel-policy.json`.
- Renderer differences are documented in the renderer coverage matrix.
- Adding a new topic does not require updating Web renderer or Mini Program renderer code.
- If the shared package still requires manual topic import registration, that coverage is validated.
- Preferred long-term flow: topic JSON, overlay, manifest, registry, and channel policy drive generated package import maps.

## 10. Recommended Workflow Per Topic

For future work, use one vertical branch per topic or topic batch:

```text
content JSON/assets
  -> shared package import/API check
  -> EdgeOne renderer verification
  -> Mini Program renderer verification
  -> dual build
```

Recommended branch shape:

```text
codex/topic-<slug>-both-renderers
```

Do not run long-lived separate Web and Mini Program branches for the same topic unless one branch is clearly only doing renderer infrastructure with no content contract changes.
