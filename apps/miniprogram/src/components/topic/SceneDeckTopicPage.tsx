import { useEffect, useMemo, useRef, useState } from "react";
import { Text, View } from "@tarojs/components";
import { usePageScroll } from "@tarojs/taro";
import {
  createInitialSceneInteractionState,
  normalizeTopicToSceneDeck,
  reduceSceneInteractionState,
  resolveScenePresentation,
  type SceneInteractionAction,
  type SceneInteractionState,
} from "@yutou/kids-content/scene-deck";
import type { Locale, Topic } from "@yutou/kids-content";
import { GeneratedImage } from "../shared/GeneratedImage";

type Props = {
  topic: Topic;
  locale: Locale;
};

function blockBody(block: { body?: string; items?: string[] }) {
  return block.body ?? block.items?.join("\n") ?? "";
}

export function SceneDeckTopicPage({ topic, locale }: Props) {
  const deck = useMemo(() => normalizeTopicToSceneDeck(topic, { locale }), [topic, locale]);
  const [state, setState] = useState<SceneInteractionState>(() => createInitialSceneInteractionState(deck));
  const presentation = useMemo(() => resolveScenePresentation(deck, state), [deck, state]);
  const activeScene = presentation.activeScene;
  const [sceneNavOpen, setSceneNavOpen] = useState(false);
  const lastScrollY = useRef(0);

  useEffect(() => {
    setState(createInitialSceneInteractionState(deck));
    setSceneNavOpen(false);
    lastScrollY.current = 0;
  }, [deck]);

  usePageScroll((event) => {
    const nextY = event.scrollTop;
    const delta = nextY - lastScrollY.current;
    lastScrollY.current = nextY;

    if (sceneNavOpen && delta > 8) {
      setSceneNavOpen(false);
    }
  });

  function dispatch(action: SceneInteractionAction) {
    setState((current) => reduceSceneInteractionState(deck, current, action));
    if (action.type === "SELECT_SCENE") {
      setSceneNavOpen(false);
    }
  }

  return (
    <View className="topic-page scene-deck-page" data-topic-mode="scene-deck">
      <View className="scene-deck-hero">
        <Text className="topic-kicker">{topic.subtitle}</Text>
        <Text className="topic-title">{topic.title}</Text>
        <Text className="topic-lead">{topic.coreQuestion}</Text>
      </View>

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
                  if (!region.bounds) return null;
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
    </View>
  );
}
