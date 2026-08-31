import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft } from "lucide-react";
import {
  createInitialSceneInteractionState,
  normalizeTopicToSceneDeck,
  reduceSceneInteractionState,
  resolveScenePresentation,
  type SceneInteractionAction,
  type SceneInteractionState,
} from "@yutou/kids-content/scene-deck";
import type { Locale, Topic } from "@yutou/kids-content";
import { KnowledgeEntryNotice } from "../home/KnowledgeEntryNotice";
import { GeneratedImage } from "../shared/GeneratedImage";

type Props = {
  topic: Topic;
  locale: Locale;
};

function contentBlockBody(block: { body?: string; items?: string[] }) {
  if (block.body) return block.body;
  return block.items?.join(localeSeparator) ?? "";
}

const localeSeparator = "\n";

export function SceneDeckTopicPage({ topic, locale }: Props) {
  const deck = useMemo(() => normalizeTopicToSceneDeck(topic, { locale }), [topic, locale]);
  const [state, setState] = useState<SceneInteractionState>(() => createInitialSceneInteractionState(deck));
  const [sceneNavOpen, setSceneNavOpen] = useState(false);
  const sceneNavToggleRef = useRef<HTMLButtonElement | null>(null);
  const lastScrollY = useRef(0);
  const presentation = useMemo(() => resolveScenePresentation(deck, state), [deck, state]);
  const activeScene = presentation.activeScene;

  useEffect(() => {
    setState(createInitialSceneInteractionState(deck));
    setSceneNavOpen(false);
  }, [deck]);

  useEffect(() => {
    if (typeof window === "undefined" || !sceneNavOpen) return;

    lastScrollY.current = window.scrollY;

    const handleScroll = () => {
      const nextY = window.scrollY;
      const delta = nextY - lastScrollY.current;
      lastScrollY.current = nextY;

      if (delta > 8) {
        setSceneNavOpen(false);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, [sceneNavOpen]);

  function dispatch(action: SceneInteractionAction) {
    setState((current) => reduceSceneInteractionState(deck, current, action));
    if (action.type === "SELECT_SCENE") {
      const shouldRestoreSceneNavFocus = sceneNavOpen;
      setSceneNavOpen(false);
      if (typeof window !== "undefined" && typeof document !== "undefined") {
        window.requestAnimationFrame(() => {
          if (shouldRestoreSceneNavFocus) {
            sceneNavToggleRef.current?.focus({ preventScroll: true });
          }
          document.querySelector(".scene-panel-evidence")?.scrollIntoView({ block: "start", behavior: "smooth" });
        });
      }
    }
  }

  return (
    <main className="page-shell topic-page scene-deck-page" data-topic-mode="scene-deck">
      <a className="back-link" href="#">
        <ArrowLeft size={18} />
        {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
      </a>
      <KnowledgeEntryNotice locale={locale} />

      <header className="scene-deck-hero">
        <p>{topic.subtitle}</p>
        <h1>{topic.title}</h1>
        <strong>{topic.coreQuestion}</strong>
      </header>

      <div className={sceneNavOpen ? "scene-deck-nav-shell expanded" : "scene-deck-nav-shell"}>
        <button
          ref={sceneNavToggleRef}
          className="scene-nav-toggle"
          type="button"
          aria-controls="scene-deck-nav"
          aria-expanded={sceneNavOpen}
          onClick={() => setSceneNavOpen((open) => !open)}
        >
          <span>{activeScene.order}</span>
          <strong>{activeScene.title}</strong>
        </button>
        <nav id="scene-deck-nav" className="scene-deck-nav" aria-label={locale === "zh-CN" ? "场景导航" : "Scene navigation"}>
          {deck.scenes.map((scene) => (
            <button
              className={scene.id === activeScene.id ? "active" : ""}
              key={scene.id}
              type="button"
              aria-current={scene.id === activeScene.id ? "true" : undefined}
              onClick={() => dispatch({ type: "SELECT_SCENE", sceneId: scene.id })}
            >
              <span>{scene.order}</span>
              <strong>{scene.title}</strong>
            </button>
          ))}
        </nav>
      </div>

      <section className="scene-panel-deck" id={activeScene.id}>
        <article className="scene-panel scene-panel-evidence">
          <article className="scene-deck-copy">
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

            <span className="scene-task-panel" hidden />
          </article>

          <div className="scene-visual-panel">
            <div className="scene-visual-frame">
              <GeneratedImage assetId={activeScene.visual.assetId} alt={activeScene.visual.alt} className="scene-visual-image" />
              <div className="scene-region-layer" aria-hidden="true">
                {activeScene.visual.regions.map((region) => {
                  if (!region.bounds) return null;
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
    </main>
  );
}
