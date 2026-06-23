import { readFileSync } from "node:fs";
import { strict as assert } from "node:assert";

const read = (file) => readFileSync(file, "utf8");

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const findClosingBrace = (source, openBraceIndex) => {
  let depth = 0;

  for (let index = openBraceIndex; index < source.length; index += 1) {
    if (source[index] === "{") {
      depth += 1;
    } else if (source[index] === "}") {
      depth -= 1;

      if (depth === 0) {
        return index;
      }
    }
  }

  return -1;
};

const cssBlocksInMedia = (source, mediaQuery) => {
  const blocks = [];
  const mediaLabel = `@media ${mediaQuery}`;
  let searchStart = 0;

  while (searchStart < source.length) {
    const mediaStart = source.indexOf(mediaLabel, searchStart);

    if (mediaStart < 0) {
      break;
    }

    const mediaOpenBrace = source.indexOf("{", mediaStart);
    assert.ok(mediaOpenBrace >= 0, `Expected @media ${mediaQuery} to contain a block`);

    const mediaCloseBrace = findClosingBrace(source, mediaOpenBrace);
    assert.ok(mediaCloseBrace > mediaOpenBrace, `Expected @media ${mediaQuery} to close`);

    blocks.push(source.slice(mediaOpenBrace + 1, mediaCloseBrace));
    searchStart = mediaCloseBrace + 1;
  }

  assert.ok(blocks.length > 0, `Expected @media ${mediaQuery} to exist`);

  return blocks;
};

const cssRuleInMedia = (source, mediaQuery, selector) => {
  const rulePattern = new RegExp(`${escapeRegExp(selector)}\\s*{`);

  for (const mediaBlock of cssBlocksInMedia(source, mediaQuery)) {
    const ruleMatch = rulePattern.exec(mediaBlock);

    if (!ruleMatch) {
      continue;
    }

    const ruleOpenBrace = mediaBlock.indexOf("{", ruleMatch.index);
    const ruleCloseBrace = findClosingBrace(mediaBlock, ruleOpenBrace);
    assert.ok(ruleCloseBrace > ruleOpenBrace, `Expected ${selector} rule to close inside @media ${mediaQuery}`);

    return mediaBlock.slice(ruleOpenBrace + 1, ruleCloseBrace);
  }

  assert.fail(`Expected ${selector} inside @media ${mediaQuery}`);
};

const webTopicPage = read("boards/kids-world/src/pages/TopicPage.tsx");
const webSceneDeck = read("boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx");
const webTopbar = read("boards/kids-world/src/components/layout/Topbar.tsx");
const webLearningFlow = read("boards/kids-world/src/components/topic/LearningFlowRail.tsx");
const webTopicVisual = read("boards/kids-world/src/components/topic/TopicVisual.tsx");
const webClassificationGroups = read("boards/kids-world/src/components/topic/ClassificationGroups.tsx");
const webRepresentativeObjects = read("boards/kids-world/src/components/topic/RepresentativeObjects.tsx");
const webMechanismSteps = read("boards/kids-world/src/components/topic/MechanismSteps.tsx");
const webComparePairs = read("boards/kids-world/src/components/topic/ComparePairs.tsx");
const webClickTaskDeck = read("boards/kids-world/src/components/topic/ClickTaskDeck.tsx");
const webStyles = read("boards/kids-world/src/styles/styles.css");
const miniGeneratedImage = read("apps/miniprogram/src/components/shared/GeneratedImage.tsx");
const miniLearningFlow = read("apps/miniprogram/src/components/topic/LearningFlowRail.tsx");
const miniTopicVisual = read("apps/miniprogram/src/components/topic/TopicVisual.tsx");
const miniTopicVisualStyles = read("apps/miniprogram/src/components/topic/TopicVisual.scss");
const miniTopicPage = read("apps/miniprogram/src/components/topic/TopicRuntimePage.tsx");
const miniSceneDeck = read("apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx");
const miniTopicPageStyles = read("apps/miniprogram/src/pages/topic/index.scss");
const miniLearningFlowStyles = read("apps/miniprogram/src/components/topic/LearningFlowRail.scss");
const miniInfoList = read("apps/miniprogram/src/components/topic/InfoList.tsx");
const miniInfoListStyles = read("apps/miniprogram/src/components/topic/InfoList.scss");
const miniClickTaskDeck = read("apps/miniprogram/src/components/topic/ClickTaskDeck.tsx");
const miniTaskDeckStyles = read("apps/miniprogram/src/components/topic/ClickTaskDeck.scss");

assert.ok(
  !webTopicPage.includes("SCROLL_STAGE_VISIBLE"),
  "scroll position must not switch the active evidence source on the Web topic page",
);
assert.ok(
  !webTopicPage.includes('document.getElementById("topic-objects")?.scrollIntoView'),
  "classification group selection must not jump to the object section",
);
assert.match(webStyles, /\.topic-visual-image\s*{[^}]*object-fit:\s*contain;/s, "Web topic visuals must show the full image");
assert.ok(
  !/@media \(max-width: 640px\)[\s\S]*?\.interaction-panel > \.topic-visual\s*{[\s\S]*?position:\s*sticky;/.test(webStyles),
  "mobile interaction visuals must not stay sticky while scrolling",
);
assert.ok(
  /<nav[\s\S]*<LocaleToggle[\s\S]*<\/nav>/.test(webTopbar) && !/<\/nav>\s*<LocaleToggle/.test(webTopbar),
  "Web language switch must live inside the right-top global menu, not beside the main navigation",
);
assert.ok(webTopbar.includes("isTopicPage"), "Web topbar must accept topic-page mode");
assert.ok(webTopbar.includes("topbar-hidden"), "Web topbar must expose a transform-based hidden state");
assert.match(webStyles, /\.topbar\.topbar-hidden\s*{(?![^}]*display:\s*none)[^}]*transform:/s, "Web hidden topbar must use transform instead of display none");
assert.ok(
  webLearningFlow.includes("onExpand") && webLearningFlow.includes("learning-flow-status") && webLearningFlow.includes('type="button"'),
  "Web collapsed stage navigation must be clickable to expand",
);
assert.ok(webLearningFlow.includes("{collapsed && activeStage ?"), "Web collapsed stage status must not render before the expanded stage buttons");
assert.ok(webTopicPage.includes("SceneDeckTopicPage"), "Web topic page must route through the scene-deck renderer");
assert.ok(webSceneDeck.includes("scene-deck-nav") && webSceneDeck.includes("SELECT_SCENE"), "Web scene deck must expose single scene navigation");
assert.ok(webSceneDeck.includes("scene-focus-list") && webSceneDeck.includes("SELECT_FOCUS"), "Web scene deck must expose focus navigation inside the active scene");
assert.ok(webSceneDeck.includes("scene-task-options") && webSceneDeck.includes("CLICK_TASK_OPTION"), "Web scene deck must keep task options inside the active scene");
{
  const copyStart = webSceneDeck.indexOf('<article className="scene-deck-copy">');
  const copyEnd = webSceneDeck.indexOf("</article>", copyStart);
  const taskPanel = webSceneDeck.indexOf('className="scene-task-panel"');
  assert.ok(
    copyStart >= 0 && copyEnd > copyStart && taskPanel > copyStart && taskPanel < copyEnd,
    "Web scene tasks must live inside the main scene copy panel instead of below the stage",
  );
}
assert.match(webStyles, /\.learning-flow-rail\s*{[^}]*position:\s*fixed;/s, "Web mobile stage navigation must float outside page layout to avoid scroll feedback loops");
assert.match(webStyles, /\.learning-flow-rail\.is-hidden\s*{(?![^}]*display:\s*none)[^}]*visibility:\s*hidden;/s, "Web hidden stage navigation must not use display none");
for (const [name, source] of [
  ["classification group", webClassificationGroups],
  ["representative object", webRepresentativeObjects],
  ["mechanism step", webMechanismSteps],
]) {
  assert.ok(source.includes("visualSupport"), `Web ${name} interactions must expose a separate related text area`);
}
assert.ok(!webClassificationGroups.includes("group.childExplanation}</span>"), "Web classification buttons must not carry long explanation text");
assert.ok(!webRepresentativeObjects.includes("object.visualHint}</small>"), "Web object buttons must not carry long hint text");
assert.ok(!webMechanismSteps.includes("step.childExplanation}</small>"), "Web step buttons must not carry long explanation text");
assert.ok(!webClassificationGroups.includes("<strong>{group.name}</strong>"), "Web classification content navigation buttons must only show numbers");
assert.ok(!webRepresentativeObjects.includes("<strong>{object.name}</strong>"), "Web object content navigation buttons must only show numbers");
assert.ok(!webMechanismSteps.includes("<strong>{step.shortTitle}</strong>"), "Web step content navigation buttons must only show numbers");
assert.ok(!webComparePairs.includes("<strong>{pair.title}</strong>"), "Web compare content navigation buttons must only show numbers");
assert.ok(!webClickTaskDeck.includes("{task.title}</button>"), "Web task content navigation buttons must only show numbers");
assert.ok(
  !webTopicVisual.includes("evidence-panel") || webTopicVisual.includes("sr-only"),
  "Web image evidence status such as selected/correct must not be visible over the image",
);
assert.ok(webTopicVisual.includes("visual-support-text"), "Web topic visual must render the related text area beside the main visual");
assert.match(webStyles, /\.interaction-panel \.group-list,[\s\S]*?\.interaction-panel \.task-tabs\s*{[^}]*display:\s*grid;/s, "Web mobile content navigation must show all switch buttons without horizontal scrolling");
assert.ok(webSceneDeck.includes("scene-nav-toggle"), "Web scene deck must expose a collapsed floating scene nav control");
assert.ok(webSceneDeck.includes("scene-panel-deck"), "Web scene deck must render mobile scene panels");
assert.ok(webSceneDeck.includes("scene-panel-evidence"), "Web scene deck must group evidence copy and image in one mobile panel");
assert.ok(webSceneDeck.includes("scene-panel-task"), "Web scene deck must render task content as a scene panel");
assert.ok(webSceneDeck.includes("scene-panel-summary"), "Web scene deck must render speak prompts and parent tips as a scene panel");
{
  const mobileSceneNavShellRule = cssRuleInMedia(webStyles, "(max-width: 760px)", ".scene-deck-nav-shell");
  const mobileSceneCopyRule = cssRuleInMedia(webStyles, "(max-width: 760px)", ".scene-deck-copy");

  assert.match(mobileSceneNavShellRule, /position:\s*fixed;/s, "Web mobile scene navigation must float outside normal page layout");
  assert.match(mobileSceneCopyRule, /overflow:\s*visible;/s, "Web mobile scene copy must not use nested scrolling as the primary layout");
  assert.match(mobileSceneCopyRule, /max-height:\s*none;/s, "Web mobile scene copy must not inherit a capped workbench height");
}
assert.match(webStyles, /\.scene-visual-frame\s*{[^}]*aspect-ratio:\s*16\s*\/\s*9;/s, "Web scene visual must keep a stable inspectable frame");
assert.match(webStyles, /\.evidence-panel\s*{[^}]*display:\s*none;/s, "Web evidence panel must not be visible over the image");
assert.match(miniGeneratedImage, /mode="widthFix"/, "Mini Program generated images must use widthFix for full evidence visuals");
assert.match(miniTopicVisualStyles, /\.topic-visual-image\s*{[^}]*height:\s*auto;/s, "Mini Program topic visual image height must be content-fit");
assert.ok(
  !miniTopicVisual.includes("evidence-panel") || miniTopicVisual.includes("evidence-detail"),
  "Mini Program image evidence status such as selected/correct must not be visible over the image",
);
assert.ok(
  miniLearningFlow.includes("onExpand") && miniLearningFlow.includes("learning-flow-current") && miniLearningFlow.includes("onExpand?.()"),
  "Mini Program collapsed stage navigation must be clickable to expand",
);
assert.ok(miniLearningFlow.includes("{collapsed && activeStage ?"), "Mini Program collapsed stage status must not render before the expanded stage chips");
assert.ok(miniTopicPage.includes("SceneDeckTopicPage"), "Mini Program topic runtime must route through the scene-deck renderer");
assert.ok(miniSceneDeck.includes("scene-deck-nav") && miniSceneDeck.includes("SELECT_SCENE"), "Mini Program scene deck must expose single scene navigation");
assert.ok(miniSceneDeck.includes("scene-focus-list") && miniSceneDeck.includes("SELECT_FOCUS"), "Mini Program scene deck must expose focus navigation inside the active scene");
assert.ok(miniSceneDeck.includes("scene-task-options") && miniSceneDeck.includes("CLICK_TASK_OPTION"), "Mini Program scene deck must keep task options inside the active scene");
assert.ok(miniSceneDeck.includes("scene-nav-toggle"), "Mini Program scene deck must expose a collapsed scene nav control");
assert.ok(miniSceneDeck.includes("scene-panel-deck"), "Mini Program scene deck must render mobile scene panels");
assert.ok(miniSceneDeck.includes("scene-panel-evidence"), "Mini Program scene deck must group evidence copy and image in one panel");
assert.ok(miniSceneDeck.includes("scene-panel-task"), "Mini Program scene deck must render task content as a scene panel");
assert.ok(miniSceneDeck.includes("scene-panel-summary"), "Mini Program scene deck must render speak prompts and parent tips as a scene panel");
assert.match(miniTopicPageStyles, /\.scene-deck-nav-shell\s*{[^}]*position:\s*fixed;/s, "Mini Program scene navigation must float outside normal page layout");
assert.match(miniLearningFlowStyles, /\.learning-flow-wrap\s*{[^}]*position:\s*fixed;/s, "Mini Program stage navigation must float outside page layout to avoid scroll feedback loops");
assert.match(miniLearningFlowStyles, /\.learning-flow-wrap\.hidden\s*{(?![^}]*display:\s*none)[^}]*visibility:\s*hidden;/s, "Mini Program hidden stage navigation must not use display none");
assert.ok(miniTopicVisual.includes("visual-support-text"), "Mini Program topic visual must render the related text area beside the main visual");
assert.ok(miniInfoList.includes("supportingText"), "Mini Program content navigation must move long item body text out of switch buttons");
assert.ok(!miniInfoList.includes('<Text className="info-item-body">{item.body}</Text>'), "Mini Program content switch buttons must not carry long body text");
assert.ok(!miniInfoList.includes('<Text className="info-item-title">{item.title}</Text>'), "Mini Program content navigation buttons must only show numbers");
assert.ok(!miniSceneDeck.includes('<Text className="step-title">{step.shortTitle}</Text>'), "Mini Program scene deck must not render legacy step-title buttons");
assert.ok(!miniClickTaskDeck.includes("<Text>{task.title}</Text>"), "Mini Program task navigation buttons must only show numbers");
assert.ok(miniSceneDeck.includes("scene-evidence-card"), "Mini Program scene deck must expose related evidence text outside switch buttons");
assert.match(miniTopicVisualStyles, /\.evidence-panel\s*{[^}]*display:\s*none;/s, "Mini Program evidence panel must not be visible over the image");
assert.ok(!miniTopicPage.includes("usePageScroll"), "Mini Program scene-deck runtime must not depend on scroll-driven stage switching");
assert.match(miniLearningFlowStyles, /\.learning-flow-wrap\s*{[^}]*top:\s*0;/s, "Mini Program stage navigation must stay at the top");
assert.match(miniLearningFlowStyles, /\.learning-flow-wrap\.collapsed[\s\S]*?\.learning-flow-current\s*{[^}]*display:\s*block;/s, "Mini Program collapsed stage navigation must show the current stage");
assert.ok(!miniInfoList.includes("<ScrollView"), "Mini Program content navigation lists must show all switch buttons on screen");
assert.match(miniInfoListStyles, /\.info-list-track\s*{[^}]*display:\s*grid;/s, "Mini Program content navigation must show all switch buttons without horizontal scrolling");
assert.match(miniInfoListStyles, /\.info-item\.active\s*{[^}]*border-color:\s*#4f46e5;/s, "Mini Program content navigation must preserve active position state");
assert.ok(!miniSceneDeck.includes('className="step-scroll"'), "Mini Program scene navigation must show all switch buttons on screen");
assert.match(miniTopicPageStyles, /\.step-track\s*{[^}]*display:\s*grid;/s, "Mini Program step navigation must show all switch buttons without horizontal scrolling");
assert.match(miniTaskDeckStyles, /\.click-task-tabs\s*{[^}]*display:\s*grid;/s, "Mini Program task navigation must show all switch buttons without horizontal scrolling");

console.log("visual navigation behavior checked");
