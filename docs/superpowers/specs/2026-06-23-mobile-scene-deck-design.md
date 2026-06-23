# Mobile Scene Deck Design

## Goal

Improve mobile browsing for Kids World topic pages by making the active scene the center of the experience. The current mobile layout keeps global navigation, scene navigation, visual evidence, copy, tasks, and summary content in one vertical flow. Users often need to tap navigation, scroll down to content, then scroll back up to change scenes. Content-heavy scenes also split related copy and images across separate scroll positions.

This design keeps the existing `learningScenes[]` and scene-deck runtime contract, but changes the mobile rendering model so each scene is presented as one to three viewport-sized panels.

## Current Problems

1. Navigation consumes prime mobile viewport space. The global topbar and scene rail can occupy most of the first screen before the learning content appears.
2. Web mobile has nested scrolling: the page scrolls, and `scene-deck-copy` also scrolls internally. This makes it hard to keep the image and related copy together.
3. Mini Program mobile stacks tasks and summary panels after the stage, so a scene can become several disconnected vertical sections.
4. Content-rich scenes do not have a screen-level structure. Users must manually connect text, evidence, image, task, and feedback while scrolling.

## Recommended Approach

Use a mobile-only immersive scene layout:

1. The global topbar collapses while reading topic content.
2. Scene navigation becomes a floating compact control instead of occupying document height.
3. Each active scene renders as a panel deck:
   - Evidence panel: scene title, kid question, active evidence copy, focus chips, and matching image.
   - Task panel: task prompt, options, and feedback when the scene has tasks.
   - Summary panel: speak prompts and parent tips when the scene has them.
4. Each panel targets one mobile viewport using `100svh`-based sizing with safe padding for the floating scene control.
5. Related text and images must appear in the same panel whenever they explain the same evidence source.

This approach avoids a full data migration. It adds a mobile presentation layer over the existing scene-deck view model.

## Navigation Behavior

### Global Topbar

On topic pages at mobile breakpoints, the global topbar should not remain part of the reading flow.

- Initial entry may show a compact bar with back, title, and menu affordance.
- After a scene is selected or the user scrolls down, the bar hides using transform and opacity, not `display: none`.
- Upward scroll or tapping the floating scene control can reveal it.
- The hidden state must preserve accessibility semantics and avoid layout jumps.

### Scene Navigation

The scene navigation should become a floating control at the top edge of the viewport.

- Collapsed state shows current scene order and title.
- Expanded state shows all scene buttons in a compact sheet or wrap grid.
- Selecting a scene closes the sheet and scrolls the scene deck to the first panel of that scene.
- Downward scroll collapses the sheet.
- The control must not permanently consume content height.

## Scene Panel Structure

### Evidence Panel

The evidence panel is the default first screen for every scene.

It includes:

- scene type or short kicker
- scene title
- kid question
- focus chips if the scene has focus items
- active evidence title, observe prompt, and evidence copy
- scene image with active region highlight
- image caption only when it fits without pushing the image away from the evidence copy

On narrow phones, the image and evidence copy should share the same panel. A practical layout is image first with compact evidence below, or a split layout when height allows. The panel may scroll internally only if content exceeds the viewport after aggressive compaction, but this should be an exception.

### Task Panel

The task panel appears only when the active scene has tasks.

It includes:

- task title and prompt
- option buttons
- feedback message after selection
- the same visual evidence image only when the task depends on visual inspection

If a scene has multiple tasks, they should be grouped inside the task panel with compact cards. If they cannot fit, the renderer can create one task panel per task rather than forcing a long page.

### Summary Panel

The summary panel appears only when speak prompts or parent tips exist.

It includes:

- child-facing speak prompts first
- parent tips second
- no large decorative card chrome

This panel can be shorter than one full viewport, but it should still align as a clear screen-level stop in the scene.

## Web Implementation Shape

Primary files:

- `boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx`
- `boards/kids-world/src/styles/styles.css`
- `boards/kids-world/src/components/layout/Topbar.tsx`

Expected changes:

1. Add mobile-only scene panel markup inside the existing scene-deck component, or annotate existing blocks so CSS can form panel sections.
2. Keep desktop behavior close to the current workbench layout.
3. Replace mobile `scene-deck-copy` nested scrolling with panel-level layout.
4. Add topbar hidden/collapsed state for topic pages.
5. Add a floating scene nav state with collapsed and expanded modes.

## Mini Program Implementation Shape

Primary files:

- `apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx`
- `apps/miniprogram/src/pages/topic/index.scss`

Expected changes:

1. Move tasks and summary content into the same scene panel structure used by Web.
2. Keep the Mini Program scene-deck runtime independent from scroll-driven scene switching.
3. Use Taro-compatible fixed positioning for the floating scene navigation.
4. Avoid nested `ScrollView` unless a panel has genuinely overflow content.

## Data Flow

No new authored content field is required for the first implementation.

The renderer derives panels from the existing `SceneViewModel`:

- `focusItems` and `activeEvidence` feed the evidence panel.
- `visual` feeds the image frame and region layer.
- `tasks` feed task panels.
- `speakPrompts` and `parentTips` feed the summary panel.

If later editorial control is needed, a small optional field such as `mobilePanels` can be added to `LearningScene`, but this should not be part of the first pass.

## Edge Cases

1. Scenes with no focus items still render the scene question, image, and first available content block in the evidence panel.
2. Very long evidence copy should be line-clamped with a reveal affordance, or moved into a secondary text panel if it cannot fit with the image.
3. Scenes with several tasks may split into multiple task panels.
4. Landscape mobile should fall back to a compact split workbench rather than forcing tall portrait panels.
5. Reduced motion users should get instant hide/show transitions.

## Testing And Validation

Update existing tests instead of adding a separate test family.

Required validation:

1. `npm run validate:scene-ui`
2. `npm run test:visual-navigation`
3. `npm run validate:scene-deck`
4. A Web mobile browser check at 390x844 and 430x932.
5. A Mini Program visual check for at least one content-heavy topic and one task-heavy topic.

Expected test updates:

- `scripts/visual-navigation.test.mjs` should no longer require mobile scene navigation to occupy normal page flow.
- The test should assert that Web and Mini Program scene tasks remain inside the active scene structure.
- The test should assert that mobile scene copy does not require nested scrolling as the primary behavior.
- The test should keep the existing full-image requirement for visual evidence.

## Acceptance Criteria

1. On a mobile topic page, selecting a scene hides or collapses navigation and immediately presents learning content.
2. A content-heavy scene presents related copy and image together in the same screen-level panel.
3. A task scene presents task prompt, options, feedback, and any required visual context without forcing the user back to the top of the page.
4. Web and Mini Program follow the same scene panel model.
5. Desktop topic pages keep the current inspectable workbench behavior.
6. No existing `learningScenes[]` data must be rewritten to ship the first version.

## Implementation Boundaries

This project should not redesign the home page, change topic content, regenerate images, or replace the scene-deck runtime. It should focus on mobile topic-page layout and navigation behavior.
