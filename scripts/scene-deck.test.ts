import assert from "node:assert/strict";
import {
  getTopic,
  getVisibleTopicSlugs,
} from "../packages/kids-content/src/index";
import {
  createInitialSceneInteractionState,
  normalizeTopicToSceneDeck,
  reduceSceneInteractionState,
  resolveScenePresentation,
} from "../packages/kids-content/src/scene-deck";

const topic = getTopic("cicada-life", "zh-CN");
assert.ok(topic, "cicada-life topic should exist");

const deck = normalizeTopicToSceneDeck(topic, {
  locale: "zh-CN",
  cdnBase: "https://cdn.example/boards/kids-world",
});

assert.equal(deck.topic.slug, "cicada-life");
assert.equal(deck.scenes.length, 6, "cicada-life should use its authored scene deck");
assert.deepEqual(
  deck.scenes.map((scene) => scene.id),
  [
    "scene-entry-ground",
    "scene-life-map",
    "scene-molting-path",
    "scene-compare-pupa",
    "scene-observation-tasks",
    "scene-summary-talk",
  ],
);
assert.ok(
  deck.scenes.every((scene) => !["observe", "classify", "inspect", "trace", "compare", "tasks", "next"].includes(scene.navLabel)),
  "scene navigation labels should be child-facing, not technical stage names",
);

for (const scene of deck.scenes) {
  assert.ok(scene.visual.assetId, `${scene.id} should expose a visual asset`);
  assert.ok(scene.visual.url?.startsWith("https://cdn.example/boards/kids-world/"), `${scene.id} should resolve the configured CDN URL`);
  const regionIds = new Set(scene.visual.regions.map((region) => region.id));
  for (const focusItem of scene.focusItems) {
    assert.ok(focusItem.source, `${scene.id}/${focusItem.id} should expose a source`);
    assert.ok(focusItem.regionIds.length > 0, `${scene.id}/${focusItem.id} should expose region ids`);
    for (const regionId of focusItem.regionIds) {
      assert.ok(regionIds.has(regionId), `${scene.id}/${focusItem.id} should reference an existing scene region: ${regionId}`);
    }
  }
}

const initialState = createInitialSceneInteractionState(deck);
assert.equal(initialState.activeSceneId, "scene-entry-ground");
const classifyScene = deck.scenes.find((scene) => scene.id === "scene-life-map");
assert.ok(classifyScene, "fallback deck should expose the classification scene");
const classifyFocus = classifyScene.focusItems[1] ?? classifyScene.focusItems[0];
assert.ok(classifyFocus, "classification scene should expose focus items");

const afterSceneSelect = reduceSceneInteractionState(deck, initialState, {
  type: "SELECT_SCENE",
  sceneId: "scene-life-map",
});
assert.equal(afterSceneSelect.activeSceneId, "scene-life-map");

const afterFocusSelect = reduceSceneInteractionState(deck, afterSceneSelect, {
  type: "SELECT_FOCUS",
  sceneId: "scene-life-map",
  source: classifyFocus.source,
});
assert.equal(afterFocusSelect.activeSceneId, "scene-life-map", "focus clicks should not change the active scene");
assert.equal(afterFocusSelect.activeFocusSourceByScene["scene-life-map"], classifyFocus.source);

const taskScene = deck.scenes.find((scene) => scene.id === "scene-observation-tasks");
assert.ok(taskScene, "fallback deck should expose the task scene");
const task = taskScene.tasks[0];
assert.ok(task, "task scene should expose normalized tasks");
const option = task.options[0];
assert.ok(option, "normalized task should expose options");

const taskState = reduceSceneInteractionState(deck, { ...afterFocusSelect, activeSceneId: "scene-observation-tasks" }, {
  type: "CLICK_TASK_OPTION",
  sceneId: "scene-observation-tasks",
  taskId: task.id,
  optionId: option.id,
});
assert.equal(taskState.activeSceneId, "scene-observation-tasks", "task clicks should not change the active scene");
assert.ok(taskState.taskStateByTaskId[task.id], "task clicks should store per-task state");
const presentation = resolveScenePresentation(deck, taskState);
assert.equal(presentation.activeScene.id, "scene-observation-tasks");
assert.ok(presentation.activeEvidence, "task presentation should resolve active evidence");

const fallbackTopic = getTopic("dinosaurs", "zh-CN");
assert.ok(fallbackTopic, "dinosaurs topic should exist");
const fallbackDeck = normalizeTopicToSceneDeck(fallbackTopic, {
  locale: "zh-CN",
  cdnBase: "https://cdn.example/boards/kids-world",
});
assert.deepEqual(
  fallbackDeck.scenes.map((scene) => scene.id),
  ["scene-entry", "scene-classify", "scene-process", "scene-compare", "scene-task", "scene-summary"],
  "topics without learningScenes should still normalize through the fallback scene deck",
);

for (const slug of getVisibleTopicSlugs("miniprogram")) {
  const visibleTopic = getTopic(slug, "zh-CN");
  assert.ok(visibleTopic, `${slug} should resolve from the shared topic registry`);
  assert.equal(visibleTopic.learningScenes?.length, 6, `${slug} should author six learningScenes instead of relying on fallback scenes`);
  const visibleDeck = normalizeTopicToSceneDeck(visibleTopic, {
    locale: "zh-CN",
    cdnBase: "https://cdn.example/boards/kids-world",
  });
  assert.equal(visibleDeck.scenes.length, 6, `${slug} should normalize to a six-scene deck`);
  for (const scene of visibleDeck.scenes) {
    assert.ok(scene.title, `${slug}/${scene.id} should expose a scene title`);
    assert.ok(scene.kidQuestion, `${slug}/${scene.id} should expose a child-facing question`);
    assert.ok(scene.visual.assetId, `${slug}/${scene.id} should expose an asset id`);
  }
}

const enTopic = getTopic("cicada-life", "en-US");
assert.ok(enTopic, "cicada-life English topic should exist");
const enDeck = normalizeTopicToSceneDeck(enTopic, {
  locale: "en-US",
  cdnBase: "https://cdn.example/boards/kids-world",
});
assert.deepEqual(
  enDeck.scenes.map((scene) => scene.title),
  ["First Look", "Recognize It", "Watch Change", "Compare", "Try It", "Tell It Back"],
);
assert.equal(enDeck.scenes[0]?.focusItems[0]?.evidenceTitle, "It is not a flying cicada yet");

const authoredTopic = structuredClone(topic) as typeof topic & { learningScenes: unknown[] };
authoredTopic.learningScenes = [
  {
    id: "scene-authored-entry",
    order: 1,
    sceneType: "entry-scene",
    title: "先看一眼",
    kidQuestion: "你先看到了什么？",
    visualPlan: {
      id: "vp-authored-entry",
      assetId: "life-cicada-life-hero",
      layoutPreset: "single-focus-scene",
      imageRole: "scene",
      aspectRatio: "16:9",
      compositionZones: [
        {
          id: "zone-main",
          label: "主角区域",
          purpose: "main-subject",
          preferredBounds: { x: 200, y: 200, w: 500, h: 500 },
          requiredEntities: ["main-cicada"],
        },
      ],
      visualEntities: [{ id: "main-cicada", label: "蝉", required: true }],
      regions: [
        {
          id: "region-main",
          entityIds: ["main-cicada"],
          label: "蝉",
          shape: "rect",
          bounds: { x: 240, y: 260, w: 420, h: 360 },
        },
      ],
    },
    focusItems: [
      {
        id: "focus-main",
        source: "scene-authored-entry.focus.main",
        label: "蝉",
        regionIds: ["region-main"],
        entityIds: ["main-cicada"],
        evidenceTitle: "先看主角",
        observePrompt: "看看它在画面哪里。",
        evidenceCopy: "这是一只正在被观察的蝉。",
      },
    ],
    contentBlocks: [
      {
        id: "copy-main",
        type: "short-explanation",
        body: "这个 authored scene 应该直接驱动页面。",
      },
    ],
  },
];

const authoredDeck = normalizeTopicToSceneDeck(authoredTopic, {
  locale: "zh-CN",
  cdnBase: "https://cdn.example/boards/kids-world",
});
assert.equal(authoredDeck.scenes.length, 1);
assert.equal(authoredDeck.scenes[0]?.id, "scene-authored-entry");
assert.equal(authoredDeck.scenes[0]?.focusItems[0]?.source, "scene-authored-entry.focus.main");
assert.equal(authoredDeck.scenes[0]?.visual.regions[0]?.bounds.x, 240);

console.log("scene deck checks passed");
