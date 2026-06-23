# Mobile Scene Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a mobile-first scene-deck topic experience where navigation collapses out of the reading flow and each active scene is grouped into screen-level evidence, task, and summary panels.

**Architecture:** Keep the existing scene-deck runtime and desktop workbench behavior. Add mobile-only presentation structure in the Web and Mini Program scene renderers, then use responsive styles to make scene navigation fixed/floating and to remove nested copy scrolling as the primary mobile behavior.

**Tech Stack:** React, Taro React components, CSS/SCSS, existing Node validation scripts.

---

## File Structure

- Modify `scripts/visual-navigation.test.mjs`: update structural assertions so tests describe the new mobile scene-deck contract before implementation.
- Modify `boards/kids-world/src/App.tsx`: pass topic-page context into the page shell.
- Modify `boards/kids-world/src/components/layout/PageShell.tsx`: pass topic-page context into `Topbar` and expose a shell class for topic mode.
- Modify `boards/kids-world/src/components/layout/Topbar.tsx`: auto-hide the topbar on topic pages while scrolling or after scene selection.
- Modify `boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx`: add floating scene navigation state and scene panel markup.
- Modify `boards/kids-world/src/styles/styles.css`: add mobile-only immersive scene layout, fixed scene nav, panel sizing, and reduced motion behavior while preserving desktop layout.
- Modify `apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx`: mirror the Web panel structure using Taro primitives.
- Modify `apps/miniprogram/src/pages/topic/index.scss`: add Mini Program panel layout and fixed scene nav styles.

## Task 1: Update Structural Test Contract

**Files:**
- Modify: `scripts/visual-navigation.test.mjs`

- [ ] **Step 1: Replace stale Web scene-deck assertions with mobile panel assertions**

In `scripts/visual-navigation.test.mjs`, replace these two assertions:

```js
assert.match(webStyles, /\.scene-deck-nav\s*{[^}]*display:\s*flex;[^}]*overflow-x:\s*auto;/s, "Web scene navigation must be a compact horizontal rail");
assert.match(webStyles, /\.scene-deck-copy\s*{[^}]*max-height:\s*var\(--scene-workbench-height\);[^}]*overflow-y:\s*auto;/s, "Web scene copy panel must scroll inside the workbench");
```

with:

```js
assert.ok(webSceneDeck.includes("scene-nav-toggle"), "Web scene deck must expose a collapsed floating scene nav control");
assert.ok(webSceneDeck.includes("scene-panel-deck"), "Web scene deck must render mobile scene panels");
assert.ok(webSceneDeck.includes("scene-panel-evidence"), "Web scene deck must group evidence copy and image in one mobile panel");
assert.ok(webSceneDeck.includes("scene-panel-task"), "Web scene deck must render task content as a scene panel");
assert.ok(webSceneDeck.includes("scene-panel-summary"), "Web scene deck must render speak prompts and parent tips as a scene panel");
assert.match(webStyles, /@media \(max-width: 760px\)[\s\S]*?\.scene-deck-nav-shell\s*{[^}]*position:\s*fixed;/s, "Web mobile scene navigation must float outside normal page layout");
assert.match(webStyles, /@media \(max-width: 760px\)[\s\S]*?\.scene-deck-copy\s*{(?![^}]*overflow-y:\s*auto)[^}]*}/s, "Web mobile scene copy must not use nested scrolling as the primary layout");
```

- [ ] **Step 2: Add Web topbar topic-mode assertions**

After the existing `webTopbar` language switch assertion, add:

```js
assert.ok(webTopbar.includes("isTopicPage"), "Web topbar must accept topic-page mode");
assert.ok(webTopbar.includes("topbar-hidden"), "Web topbar must expose a transform-based hidden state");
assert.match(webStyles, /\.topbar\.topbar-hidden\s*{(?![^}]*display:\s*none)[^}]*transform:/s, "Web hidden topbar must use transform instead of display none");
```

- [ ] **Step 3: Add Mini Program panel assertions**

After the current Mini Program scene deck assertions, add:

```js
assert.ok(miniSceneDeck.includes("scene-nav-toggle"), "Mini Program scene deck must expose a collapsed scene nav control");
assert.ok(miniSceneDeck.includes("scene-panel-deck"), "Mini Program scene deck must render mobile scene panels");
assert.ok(miniSceneDeck.includes("scene-panel-evidence"), "Mini Program scene deck must group evidence copy and image in one panel");
assert.ok(miniSceneDeck.includes("scene-panel-task"), "Mini Program scene deck must render task content as a scene panel");
assert.ok(miniSceneDeck.includes("scene-panel-summary"), "Mini Program scene deck must render speak prompts and parent tips as a scene panel");
assert.match(miniTopicPageStyles, /\.scene-deck-nav-shell\s*{[^}]*position:\s*fixed;/s, "Mini Program scene navigation must float outside normal page layout");
```

- [ ] **Step 4: Run test to verify it fails**

Run:

```bash
npm run test:visual-navigation
```

Expected: FAIL with messages about missing `scene-nav-toggle`, missing `scene-panel-deck`, and missing `isTopicPage`.

- [ ] **Step 5: Commit test contract**

Run:

```bash
git add scripts/visual-navigation.test.mjs
git commit -m "test: define mobile scene deck layout contract"
```

## Task 2: Add Web Topic Mode And Topbar Auto-Hide

**Files:**
- Modify: `boards/kids-world/src/App.tsx`
- Modify: `boards/kids-world/src/components/layout/PageShell.tsx`
- Modify: `boards/kids-world/src/components/layout/Topbar.tsx`
- Modify: `boards/kids-world/src/styles/styles.css`

- [ ] **Step 1: Pass topic-page state into `PageShell`**

In `boards/kids-world/src/App.tsx`, change the `PageShell` call to:

```tsx
  return (
    <PageShell locale={locale} onLocaleChange={setLocale} map={map} isTopicPage={Boolean(visibleTopicSlug)}>
      {visibleTopicSlug ? (
        <TopicPage slug={visibleTopicSlug} locale={locale} map={map} />
      ) : (
        <HomePage locale={locale} map={map} notice={missingTopic ? "这个探索页还在准备中。" : undefined} />
      )}
    </PageShell>
  );
```

- [ ] **Step 2: Thread topic-page state through `PageShell`**

In `boards/kids-world/src/components/layout/PageShell.tsx`, replace the file with:

```tsx
import type { ReactNode } from "react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { Topbar } from "./Topbar";

type Props = {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  map: ExplorationMap;
  children: ReactNode;
  isTopicPage?: boolean;
};

export function PageShell({ locale, onLocaleChange, map, children, isTopicPage = false }: Props) {
  return (
    <div className={isTopicPage ? "app-shell app-shell-topic" : "app-shell"}>
      <Topbar map={map} locale={locale} onLocaleChange={onLocaleChange} isTopicPage={isTopicPage} />
      {children}
    </div>
  );
}
```

- [ ] **Step 3: Add transform-based topbar hiding**

In `boards/kids-world/src/components/layout/Topbar.tsx`, replace the file with:

```tsx
import { useEffect, useState } from "react";
import { Menu, Sparkles } from "lucide-react";
import type { ExplorationMap, Locale } from "@yutou/kids-content";
import { LocaleToggle } from "../shared/LocaleToggle";

type Props = {
  map: ExplorationMap;
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  isTopicPage?: boolean;
};

export function Topbar({ map, locale, onLocaleChange, isTopicPage = false }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [topbarHidden, setTopbarHidden] = useState(false);
  const navItems = [
    { href: "#", label: locale === "zh-CN" ? "探索首页" : "Home" },
    { href: "#worlds", label: locale === "zh-CN" ? "全部世界" : "Worlds" },
    { href: "#parent-guide", label: locale === "zh-CN" ? "家长说明" : "Parent Guide" },
  ];

  useEffect(() => {
    if (!isTopicPage) {
      setTopbarHidden(false);
      return;
    }

    let lastY = window.scrollY;
    const mobileQuery = window.matchMedia("(max-width: 760px)");

    function onScroll() {
      if (!mobileQuery.matches || mobileNavOpen) {
        setTopbarHidden(false);
        lastY = window.scrollY;
        return;
      }

      const nextY = window.scrollY;
      const delta = nextY - lastY;
      if (nextY < 24 || delta < -8) setTopbarHidden(false);
      if (nextY > 80 && delta > 8) setTopbarHidden(true);
      lastY = nextY;
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [isTopicPage, mobileNavOpen]);

  return (
    <header className={topbarHidden ? "topbar topbar-hidden" : "topbar"} data-topic-page={isTopicPage ? "true" : "false"}>
      <a className="brand" href="#">
        <Sparkles />
        <span>
          <strong>{map.title}</strong>
          <small>{map.subtitle}</small>
        </span>
      </a>
      <button
        className="mobile-menu-button"
        type="button"
        aria-expanded={mobileNavOpen}
        aria-controls="global-nav"
        onClick={() => {
          setMobileNavOpen((open) => !open);
          setTopbarHidden(false);
        }}
      >
        <Menu size={18} />
        {locale === "zh-CN" ? "导航" : "Menu"}
      </button>
      <nav aria-label={locale === "zh-CN" ? "全局导航" : "Global navigation"} className={mobileNavOpen ? "open" : ""} id="global-nav">
        {navItems.map((item) => (
          <a href={item.href} key={item.href} onClick={() => setMobileNavOpen(false)}>
            {item.label}
          </a>
        ))}
        <LocaleToggle
          locale={locale}
          onChange={(nextLocale) => {
            onLocaleChange(nextLocale);
            setMobileNavOpen(false);
          }}
        />
      </nav>
    </header>
  );
}
```

- [ ] **Step 4: Add topbar hidden styles**

In `boards/kids-world/src/styles/styles.css`, add this after the existing `.topbar` block:

```css
.topbar {
  transition: transform 180ms ease, opacity 180ms ease;
}

.topbar.topbar-hidden {
  transform: translateY(-100%);
  opacity: 0;
  pointer-events: none;
}
```

Inside the existing `@media (max-width: 640px)` block, add:

```css
  .app-shell-topic .topbar {
    position: fixed;
    right: 0;
    left: 0;
  }
```

Near the end of the file, add:

```css
@media (prefers-reduced-motion: reduce) {
  .topbar {
    transition: none;
  }
}
```

- [ ] **Step 5: Run focused validation**

Run:

```bash
npm run validate:scene-ui
npm run test:visual-navigation
```

Expected: `validate:scene-ui` passes. `test:visual-navigation` still fails only for missing scene panel and scene nav contract from Task 3 and Task 4.

- [ ] **Step 6: Commit Web topic mode**

Run:

```bash
git add boards/kids-world/src/App.tsx boards/kids-world/src/components/layout/PageShell.tsx boards/kids-world/src/components/layout/Topbar.tsx boards/kids-world/src/styles/styles.css
git commit -m "feat(web): collapse topbar on mobile topic pages"
```

## Task 3: Build Web Mobile Scene Panels And Floating Scene Nav

**Files:**
- Modify: `boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx`
- Modify: `boards/kids-world/src/styles/styles.css`

- [ ] **Step 1: Add scene nav expanded state**

In `boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx`, change the import to:

```tsx
import { useEffect, useMemo, useState } from "react";
```

Then add this state after `activeScene`:

```tsx
  const [sceneNavOpen, setSceneNavOpen] = useState(false);
```

In `dispatch`, add a close-on-scene-select branch:

```tsx
  function dispatch(action: SceneInteractionAction) {
    setState((current) => reduceSceneInteractionState(deck, current, action));
    if (action.type === "SELECT_SCENE") {
      setSceneNavOpen(false);
      window.requestAnimationFrame(() => {
        document.querySelector(".scene-panel-evidence")?.scrollIntoView({ block: "start", behavior: "smooth" });
      });
    }
  }
```

- [ ] **Step 2: Replace scene navigation markup**

Replace the existing `<nav className="scene-deck-nav" ...>` block with:

```tsx
      <div className={sceneNavOpen ? "scene-deck-nav-shell expanded" : "scene-deck-nav-shell"}>
        <button className="scene-nav-toggle" type="button" aria-expanded={sceneNavOpen} onClick={() => setSceneNavOpen((open) => !open)}>
          <span>{activeScene.order}</span>
          <strong>{activeScene.title}</strong>
        </button>
        <nav className="scene-deck-nav" aria-label={locale === "zh-CN" ? "场景导航" : "Scene navigation"}>
          {deck.scenes.map((scene) => (
            <button
              className={scene.id === activeScene.id ? "active" : ""}
              key={scene.id}
              type="button"
              onClick={() => dispatch({ type: "SELECT_SCENE", sceneId: scene.id })}
            >
              <span>{scene.order}</span>
              <strong>{scene.title}</strong>
            </button>
          ))}
        </nav>
      </div>
```

- [ ] **Step 3: Replace scene stage markup with panel deck**

Replace the existing `<section className="scene-deck-stage" id={activeScene.id}>...</section>` block with this structure. Keep the existing task option mapping exactly as shown so interaction state remains unchanged.

```tsx
      <section className="scene-panel-deck" id={activeScene.id}>
        <article className="scene-panel scene-panel-evidence">
          <div className="scene-deck-copy">
            <p className="scene-kicker">{activeScene.sceneType}</p>
            <h2>{activeScene.title}</h2>
            <p>{activeScene.kidQuestion}</p>

            {activeScene.focusItems.length > 0 ? (
              <div className="scene-focus-list">
                {activeScene.focusItems.map((focus) => (
                  <button
                    className={presentation.activeFocusSource === focus.source ? "active" : ""}
                    key={focus.id}
                    type="button"
                    onClick={() => dispatch({ type: "SELECT_FOCUS", sceneId: activeScene.id, source: focus.source })}
                  >
                    {focus.shortLabel ?? focus.label}
                  </button>
                ))}
              </div>
            ) : null}

            {presentation.activeEvidence ? (
              <div className="scene-evidence-card">
                <strong>{presentation.activeEvidence.evidenceTitle}</strong>
                {presentation.activeEvidence.observePrompt ? <p>{presentation.activeEvidence.observePrompt}</p> : null}
                <p>{presentation.activeEvidence.evidenceCopy}</p>
              </div>
            ) : null}

            {activeScene.contentBlocks.map((block) => (
              <div className="scene-content-block" key={block.id}>
                {block.title ? <strong>{block.title}</strong> : null}
                {contentBlockBody(block) ? <p>{contentBlockBody(block)}</p> : null}
              </div>
            ))}
          </div>

          <div className="scene-visual-panel">
            <div className="scene-visual-frame">
              <GeneratedImage assetId={activeScene.visual.assetId} alt={activeScene.visual.alt} className="scene-visual-image" />
              <div className="scene-region-layer" aria-hidden="true">
                {activeScene.visual.regions.map((region) => {
                  const isActive = presentation.activeEvidence?.regionIds.includes(region.id);
                  return (
                    <span
                      className={isActive ? "scene-region active" : "scene-region"}
                      key={region.id}
                      style={{
                        left: `${region.bounds.x / 10}%`,
                        top: `${region.bounds.y / 10}%`,
                        width: `${region.bounds.w / 10}%`,
                        height: `${region.bounds.h / 10}%`,
                      }}
                    />
                  );
                })}
              </div>
            </div>
            {activeScene.visual.caption ? <p className="scene-visual-caption">{activeScene.visual.caption}</p> : null}
          </div>
        </article>

        {activeScene.tasks.length > 0 ? (
          <section className="scene-panel scene-panel-task" aria-label={locale === "zh-CN" ? "场景任务" : "Scene tasks"}>
            {activeScene.tasks.map((task) => {
              const taskState = presentation.taskStateByTaskId[task.id];
              return (
                <article className="scene-task-card" key={task.id}>
                  <h3>{task.title}</h3>
                  <p>{task.prompt}</p>
                  <div className="scene-task-options">
                    {task.options.map((option) => (
                      <button
                        className={taskState?.selectedOptionIds.includes(option.id) ? "selected" : ""}
                        key={option.id}
                        type="button"
                        onClick={() =>
                          dispatch({
                            type: "CLICK_TASK_OPTION",
                            sceneId: activeScene.id,
                            taskId: task.id,
                            optionId: option.id,
                          })
                        }
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                  {taskState?.feedbackMessage ? <strong className={`scene-task-feedback ${taskState.result}`}>{taskState.feedbackMessage}</strong> : null}
                </article>
              );
            })}
          </section>
        ) : null}

        {activeScene.speakPrompts.length > 0 || activeScene.parentTips.length > 0 ? (
          <section className="scene-panel scene-panel-summary" aria-label={locale === "zh-CN" ? "表达和亲子提示" : "Speak prompts and parent tips"}>
            {activeScene.speakPrompts.map((prompt) => (
              <p key={prompt}>{prompt}</p>
            ))}
            {activeScene.parentTips.map((tip) => (
              <p key={tip}>{tip}</p>
            ))}
          </section>
        ) : null}
      </section>
```

- [ ] **Step 4: Add desktop compatibility styles**

In `boards/kids-world/src/styles/styles.css`, add this before the current `.scene-deck-stage` block:

```css
.scene-deck-nav-shell {
  display: grid;
  gap: 6px;
}

.scene-nav-toggle {
  display: none;
}

.scene-panel-deck {
  display: grid;
  gap: 12px;
}

.scene-panel-evidence {
  display: grid;
  grid-template-columns: minmax(300px, 0.68fr) minmax(420px, 1.32fr);
  gap: 18px;
  align-items: stretch;
  min-height: var(--scene-workbench-height);
}

.scene-panel-task,
.scene-panel-summary {
  display: grid;
  gap: 12px;
}
```

Leave the existing `.scene-deck-stage` styles in place during this task if other legacy pages still use them.

- [ ] **Step 5: Replace mobile scene styles**

Inside `@media (max-width: 760px)`, replace the current scene-deck mobile overrides with:

```css
  .scene-deck-page {
    --scene-workbench-height: auto;
    width: 100%;
    gap: 0;
    padding: 0 0 28px;
  }

  .scene-deck-page .back-link,
  .scene-deck-hero {
    display: none;
  }

  .scene-deck-nav-shell {
    position: fixed;
    top: 10px;
    right: 10px;
    left: 10px;
    z-index: 35;
    gap: 8px;
    pointer-events: none;
  }

  .scene-nav-toggle {
    display: grid;
    grid-template-columns: 28px minmax(0, 1fr);
    align-items: center;
    gap: 8px;
    min-height: 42px;
    padding: 8px 12px;
    border: 2px solid rgba(23, 32, 51, 0.12);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.94);
    box-shadow: 0 10px 28px rgba(23, 32, 51, 0.12);
    pointer-events: auto;
    text-align: left;
  }

  .scene-nav-toggle span {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border-radius: 999px;
    background: #172033;
    color: #fff;
    font-weight: 900;
  }

  .scene-nav-toggle strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .scene-deck-nav {
    display: none;
    margin: 0;
    padding: 10px;
    border: 1px solid rgba(23, 32, 51, 0.1);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 18px 44px rgba(23, 32, 51, 0.14);
    pointer-events: auto;
  }

  .scene-deck-nav-shell.expanded .scene-deck-nav {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .scene-panel-deck {
    gap: 0;
  }

  .scene-panel {
    min-height: 100svh;
    padding: 64px 12px 18px;
    scroll-margin-top: 0;
  }

  .scene-panel-evidence {
    display: grid;
    grid-template-columns: 1fr;
    align-content: start;
    gap: 12px;
    min-height: 100svh;
  }

  .scene-visual-panel {
    order: -1;
  }

  .scene-visual-frame {
    max-height: min(42svh, 360px);
  }

  .scene-deck-copy {
    max-height: none;
    overflow: visible;
    padding: 13px;
  }

  .scene-deck-copy h2,
  .scene-task-card h3 {
    font-size: 20px;
  }

  .scene-deck-copy p,
  .scene-content-block p,
  .scene-evidence-card p,
  .scene-task-card p,
  .scene-summary-panel p {
    font-size: 14px;
    line-height: 1.45;
  }

  .scene-focus-list,
  .scene-task-options {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .scene-panel-task,
  .scene-panel-summary {
    align-content: center;
  }
```

- [ ] **Step 6: Run focused validation**

Run:

```bash
npm run test:visual-navigation
npm run validate:scene-ui
```

Expected: `validate:scene-ui` passes. `test:visual-navigation` still fails only for missing Mini Program panel structure and Mini Program fixed nav styles.

- [ ] **Step 7: Commit Web scene panels**

Run:

```bash
git add boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx boards/kids-world/src/styles/styles.css
git commit -m "feat(web): add mobile scene panel deck"
```

## Task 4: Build Mini Program Scene Panels And Floating Scene Nav

**Files:**
- Modify: `apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx`
- Modify: `apps/miniprogram/src/pages/topic/index.scss`

- [ ] **Step 1: Add Mini Program scene nav state**

In `apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx`, keep the existing React import and add this after `activeScene`:

```tsx
  const [sceneNavOpen, setSceneNavOpen] = useState(false);
```

Replace `dispatch` with:

```tsx
  function dispatch(action: SceneInteractionAction) {
    setState((current) => reduceSceneInteractionState(deck, current, action));
    if (action.type === "SELECT_SCENE") {
      setSceneNavOpen(false);
    }
  }
```

- [ ] **Step 2: Replace Mini Program scene nav markup**

Replace the existing `<View className="scene-deck-nav">...</View>` block with:

```tsx
      <View className={sceneNavOpen ? "scene-deck-nav-shell expanded" : "scene-deck-nav-shell"}>
        <View className="scene-nav-toggle" onClick={() => setSceneNavOpen((open) => !open)}>
          <Text className="scene-nav-index">{activeScene.order}</Text>
          <Text className="scene-nav-label">{activeScene.title}</Text>
        </View>
        <View className="scene-deck-nav">
          {deck.scenes.map((scene) => (
            <View
              className={scene.id === activeScene.id ? "scene-nav-item active" : "scene-nav-item"}
              key={scene.id}
              onClick={() => dispatch({ type: "SELECT_SCENE", sceneId: scene.id })}
            >
              <Text className="scene-nav-index">{scene.order}</Text>
              <Text className="scene-nav-label">{scene.title}</Text>
            </View>
          ))}
        </View>
      </View>
```

- [ ] **Step 3: Replace Mini Program stage and trailing panels with one panel deck**

Replace the existing `<View className="scene-deck-stage" id={activeScene.id}>...</View>` block and the following task and summary blocks with:

```tsx
      <View className="scene-panel-deck" id={activeScene.id}>
        <View className="scene-panel scene-panel-evidence">
          <View className="scene-deck-copy">
            <Text className="scene-kicker">{activeScene.sceneType}</Text>
            <Text className="section-title">{activeScene.title}</Text>
            <Text className="section-body">{activeScene.kidQuestion}</Text>

            {activeScene.focusItems.length > 0 ? (
              <View className="scene-focus-list">
                {activeScene.focusItems.map((focus) => (
                  <View
                    className={presentation.activeFocusSource === focus.source ? "scene-focus-item active" : "scene-focus-item"}
                    key={focus.id}
                    onClick={() => dispatch({ type: "SELECT_FOCUS", sceneId: activeScene.id, source: focus.source })}
                  >
                    <Text>{focus.shortLabel ?? focus.label}</Text>
                  </View>
                ))}
              </View>
            ) : null}

            {presentation.activeEvidence ? (
              <View className="scene-evidence-card">
                <Text className="scene-evidence-title">{presentation.activeEvidence.evidenceTitle}</Text>
                {presentation.activeEvidence.observePrompt ? <Text className="section-body">{presentation.activeEvidence.observePrompt}</Text> : null}
                <Text className="section-body">{presentation.activeEvidence.evidenceCopy}</Text>
              </View>
            ) : null}

            {activeScene.contentBlocks.map((block) => (
              <View className="scene-content-block" key={block.id}>
                {block.title ? <Text className="scene-evidence-title">{block.title}</Text> : null}
                {blockBody(block) ? <Text className="section-body">{blockBody(block)}</Text> : null}
              </View>
            ))}
          </View>

          <View className="scene-visual-panel">
            <View className="scene-visual-frame">
              <GeneratedImage assetId={activeScene.visual.assetId} alt={activeScene.visual.alt} className="scene-visual-image" />
              <View className="scene-region-layer">
                {activeScene.visual.regions.map((region) => {
                  const isActive = presentation.activeEvidence?.regionIds.includes(region.id);
                  return (
                    <View
                      className={isActive ? "scene-region active" : "scene-region"}
                      key={region.id}
                      style={{
                        left: `${region.bounds.x / 10}%`,
                        top: `${region.bounds.y / 10}%`,
                        width: `${region.bounds.w / 10}%`,
                        height: `${region.bounds.h / 10}%`,
                      }}
                    />
                  );
                })}
              </View>
            </View>
            {activeScene.visual.caption ? <Text className="topic-visual-caption">{activeScene.visual.caption}</Text> : null}
          </View>
        </View>

        {activeScene.tasks.length > 0 ? (
          <View className="scene-panel scene-panel-task">
            {activeScene.tasks.map((task) => {
              const taskState = presentation.taskStateByTaskId[task.id];
              return (
                <View className="scene-task-card" key={task.id}>
                  <Text className="scene-evidence-title">{task.title}</Text>
                  <Text className="section-body">{task.prompt}</Text>
                  <View className="scene-task-options">
                    {task.options.map((option) => (
                      <View
                        className={taskState?.selectedOptionIds.includes(option.id) ? "scene-task-option selected" : "scene-task-option"}
                        key={option.id}
                        onClick={() =>
                          dispatch({
                            type: "CLICK_TASK_OPTION",
                            sceneId: activeScene.id,
                            taskId: task.id,
                            optionId: option.id,
                          })
                        }
                      >
                        <Text>{option.label}</Text>
                      </View>
                    ))}
                  </View>
                  {taskState?.feedbackMessage ? <Text className={`scene-task-feedback ${taskState.result}`}>{taskState.feedbackMessage}</Text> : null}
                </View>
              );
            })}
          </View>
        ) : null}

        {activeScene.speakPrompts.length > 0 || activeScene.parentTips.length > 0 ? (
          <View className="scene-panel scene-panel-summary">
            {activeScene.speakPrompts.map((prompt) => (
              <Text className="section-body" key={prompt}>
                {prompt}
              </Text>
            ))}
            {activeScene.parentTips.map((tip) => (
              <Text className="section-body" key={tip}>
                {tip}
              </Text>
            ))}
          </View>
        ) : null}
      </View>
```

- [ ] **Step 4: Replace Mini Program scene styles**

In `apps/miniprogram/src/pages/topic/index.scss`, replace the scene-deck section from `.scene-deck-page` through `.scene-task-feedback.wrong` with:

```scss
.scene-deck-page {
  gap: 0;
  padding: 0 0 28px;
}

.scene-deck-hero {
  display: none;
}

.scene-deck-nav-shell {
  position: fixed;
  top: 12px;
  right: 12px;
  left: 12px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.scene-nav-toggle {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  align-items: center;
  gap: 9px;
  min-height: 56px;
  padding: 8px 14px;
  border: 2px solid rgba(23, 32, 51, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12px 30px rgba(23, 32, 51, 0.14);
  pointer-events: auto;
}

.scene-deck-nav {
  display: none;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 12px;
  border: 1px solid rgba(23, 32, 51, 0.1);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 18px 44px rgba(23, 32, 51, 0.14);
  pointer-events: auto;
}

.scene-deck-nav-shell.expanded .scene-deck-nav {
  display: grid;
}

.scene-focus-list,
.scene-task-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.scene-nav-item,
.scene-focus-item,
.scene-task-option {
  display: grid;
  align-items: center;
  min-width: 0;
  min-height: 50px;
  padding: 9px 10px;
  border: 2px solid rgba(23, 32, 51, 0.08);
  border-radius: 12px;
  background: #ffffff;
}

.scene-nav-item,
.scene-nav-toggle {
  grid-template-columns: 34px minmax(0, 1fr);
}

.scene-nav-item.active,
.scene-focus-item.active,
.scene-task-option.selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.scene-nav-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #172033;
  color: #ffffff;
  font-size: 20px;
  font-weight: 800;
}

.scene-nav-item.active .scene-nav-index {
  background: #2563eb;
}

.scene-nav-label,
.scene-focus-item,
.scene-task-option {
  color: #172033;
  font-size: 21px;
  font-weight: 800;
  line-height: 1.22;
  white-space: normal;
  word-break: break-all;
  overflow-wrap: anywhere;
}

.scene-panel-deck {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.scene-panel {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
  padding: 72px 12px 20px;
}

.scene-panel-evidence {
  justify-content: flex-start;
}

.scene-deck-copy,
.scene-task-card,
.scene-panel-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid rgba(23, 32, 51, 0.08);
  border-radius: 8px;
  background: #ffffff;
}

.scene-kicker {
  color: #0f766e;
  font-size: 20px;
  font-weight: 900;
  text-transform: uppercase;
}

.scene-evidence-card,
.scene-content-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background: #f8fafc;
}

.scene-evidence-title {
  color: #172033;
  font-size: 24px;
  font-weight: 800;
}

.scene-visual-panel {
  display: flex;
  flex-direction: column;
  order: -1;
  gap: 8px;
}

.scene-visual-frame {
  position: relative;
  max-height: 42vh;
  overflow: hidden;
  border-radius: 8px;
  background: #f8fafc;
}

.scene-visual-image {
  width: 100%;
}

.scene-region-layer,
.scene-region {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  pointer-events: none;
}

.scene-region {
  right: auto;
  bottom: auto;
  border: 2px solid rgba(37, 99, 235, 0.28);
  border-radius: 10px;
  opacity: 0.5;
}

.scene-region.active {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.14);
  opacity: 1;
}

.scene-task-feedback {
  color: #2563eb;
  font-size: 23px;
  font-weight: 800;
}

.scene-task-feedback.wrong {
  color: #be123c;
}
```

- [ ] **Step 5: Run focused validation**

Run:

```bash
npm run test:visual-navigation
npm run validate:scene-ui
npm run validate:scene-deck
```

Expected: all three commands pass.

- [ ] **Step 6: Commit Mini Program scene panels**

Run:

```bash
git add apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx apps/miniprogram/src/pages/topic/index.scss
git commit -m "feat(miniprogram): add mobile scene panel deck"
```

## Task 5: Full Verification And Visual Gut Check

**Files:**
- No source files should change in this task unless verification exposes a concrete bug.

- [ ] **Step 1: Run required command validation**

Run:

```bash
npm run validate:scene-ui
npm run test:visual-navigation
npm run validate:scene-deck
```

Expected:

```text
scene UI checked
visual navigation behavior checked
scene deck validation passed
```

- [ ] **Step 2: Run Web build**

Run:

```bash
npm run build:kids-world
```

Expected: Vite build completes without TypeScript or CSS processing errors.

- [ ] **Step 3: Start local dev server for visual checks**

Run:

```bash
npm run dev
```

Expected: server reports a local URL such as `http://127.0.0.1:5173/`.

- [ ] **Step 4: Check mobile topic pages in browser**

Open these URLs at 390x844 and 430x932:

```text
http://127.0.0.1:5173/boards/kids-world/index.html#cicada-life
http://127.0.0.1:5173/boards/kids-world/index.html#digestion
```

Expected:

- the topbar does not consume the first content screen after scrolling
- the scene nav appears as a floating collapsed control
- tapping the scene nav expands a compact scene list
- selecting a scene collapses the list and returns to the evidence panel
- evidence copy and the image appear in the same screen-level panel
- task content appears in a task panel without requiring the user to scroll back to the scene nav

- [ ] **Step 5: Commit verification fixes if needed**

If visual checks require code fixes, commit only those touched files:

```bash
git add boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx boards/kids-world/src/styles/styles.css apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx apps/miniprogram/src/pages/topic/index.scss scripts/visual-navigation.test.mjs
git commit -m "fix: polish mobile scene deck verification"
```

If no fixes are needed, do not create a commit in this step.

## Self-Review

Spec coverage:

- Navigation auto-hide is covered in Task 2.
- Floating scene navigation is covered in Task 3 and Task 4.
- Evidence, task, and summary panel grouping is covered in Task 3 and Task 4.
- Web and Mini Program parity is covered in Task 3, Task 4, and Task 5.
- Desktop preservation is covered by keeping desktop workbench styles and testing `validate:scene-ui`.
- No content migration is introduced.

Placeholder scan:

- The plan contains no open-ended implementation placeholders. Each task names files, code shape, commands, and expected outcomes.

Type consistency:

- `isTopicPage`, `sceneNavOpen`, `scene-nav-toggle`, `scene-deck-nav-shell`, `scene-panel-deck`, `scene-panel-evidence`, `scene-panel-task`, and `scene-panel-summary` are used consistently across tests, Web markup, Mini Program markup, and styles.
