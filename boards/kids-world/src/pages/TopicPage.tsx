import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";
import {
  createInitialTopicInteractionState,
  getTopic,
  getTopicLearningFlow,
  getVisualSlotForTarget,
  reduceTopicInteractionState,
  resolveTopicPresentation,
  type ExplorationMap,
  type Locale,
  type Topic,
  type TopicInteractionAction,
  type VisualEvidenceState,
} from "@yutou/kids-content";
import { SectionHeader } from "../components/shared/SectionHeader";
import { TopicHero } from "../components/topic/TopicHero";
import { ClassificationGroups } from "../components/topic/ClassificationGroups";
import { RepresentativeObjects } from "../components/topic/RepresentativeObjects";
import { MechanismSteps } from "../components/topic/MechanismSteps";
import { ComparePairs } from "../components/topic/ComparePairs";
import { ClickTaskDeck } from "../components/topic/ClickTaskDeck";
import { SpeakTemplates } from "../components/topic/SpeakTemplates";
import { ParentTips } from "../components/topic/ParentTips";
import { RelatedTopics } from "../components/topic/RelatedTopics";
import { LearningFlowRail } from "../components/topic/LearningFlowRail";

type Props = { slug: string; locale: Locale; map: ExplorationMap };

function TopicPageContent({ topic, locale, map }: { topic: Topic; locale: Locale; map: ExplorationMap }) {
  const flowStages = useMemo(() => getTopicLearningFlow(topic, locale), [topic, locale]);
  const [interactionState, setInteractionState] = useState(() => createInitialTopicInteractionState(topic, locale));
  const dispatch = useCallback(
    (action: TopicInteractionAction) => {
      setInteractionState((current) => reduceTopicInteractionState(topic, locale, current, action));
    },
    [topic, locale],
  );
  const presentation = useMemo(() => resolveTopicPresentation(topic, interactionState, locale), [topic, interactionState, locale]);

  useEffect(() => {
    setInteractionState(createInitialTopicInteractionState(topic, locale));
  }, [topic, locale]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!visible) return;
        const stage = flowStages.find((item) => item.sectionIds.includes(visible.target.id));
        if (stage) dispatch({ type: "SCROLL_STAGE_VISIBLE", stageId: stage.id });
      },
      { rootMargin: "-28% 0px -58% 0px", threshold: [0.1, 0.35, 0.6] },
    );

    const observedSections = flowStages
      .flatMap((stage) => stage.sectionIds)
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => Boolean(section));
    observedSections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [dispatch, flowStages]);

  function handleSelectGroup(groupId: string) {
    dispatch({ type: "SELECT_CLASSIFICATION_GROUP", groupId });
    document.getElementById("topic-objects")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function evidenceFor(prefix: string): VisualEvidenceState | null {
    return presentation.evidence?.source.startsWith(prefix) ? presentation.evidence : null;
  }

  function slotForEvidence(evidence: VisualEvidenceState | null, fallbackTarget: string) {
    return evidence
      ? topic.visualSlots?.find((slot) => slot.id === evidence.visualSlotId) ?? getVisualSlotForTarget(topic, fallbackTarget)
      : getVisualSlotForTarget(topic, fallbackTarget);
  }

  const classificationEvidence = evidenceFor("classificationGroups.");
  const objectEvidence = evidenceFor("representativeObjects.");
  const mechanismEvidence = evidenceFor("mechanism.steps.");
  const secondaryEvidence = evidenceFor("secondaryMechanism.steps.");
  const compareEvidence = evidenceFor("comparePairs.");
  const activeObjectId = interactionState.activeObjectId ?? topic.representativeObjects[0]?.id ?? "";

  return (
    <main className="page-shell topic-page">
      <a className="back-link" href="#">
        <ArrowLeft size={18} />
        {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
      </a>

      <TopicHero topic={topic} />
      <LearningFlowRail
        activeStageId={interactionState.activeStageId}
        stages={flowStages}
        locale={locale}
        onSelectStage={(stageId) => dispatch({ type: "SELECT_STAGE", stageId })}
      />

      <section className="content-grid">
        <article className="panel wide" id="topic-observe">
          <SectionHeader title={locale === "zh-CN" ? "看一看主场景" : "Look at the scene"} kicker={topic.coreQuestion}>
            {topic.hero.sceneExplanation}
          </SectionHeader>
        </article>

        <ClassificationGroups
          topic={topic}
          groups={topic.classificationGroups}
          activeGroupId={interactionState.activeGroupId ?? topic.classificationGroups[0]?.id}
          evidence={classificationEvidence}
          visualSlot={slotForEvidence(classificationEvidence, "classificationGroups")}
          onSelectGroup={handleSelectGroup}
          locale={locale}
        />
        <RepresentativeObjects
          topic={topic}
          objects={topic.representativeObjects}
          activeObjectId={activeObjectId}
          onSelectObject={(objectId) => dispatch({ type: "SELECT_REPRESENTATIVE_OBJECT", objectId })}
          visualSlot={slotForEvidence(objectEvidence, `representativeObjects.${activeObjectId}`)}
          evidence={objectEvidence}
          locale={locale}
        />
        <MechanismSteps
          topic={topic}
          mechanism={topic.mechanism}
          secondary={topic.secondaryMechanism}
          activeMechanismStepId={interactionState.activeMechanismStepId ?? topic.mechanism.steps[0]?.id ?? ""}
          activeSecondaryStepId={interactionState.activeSecondaryStepId ?? topic.secondaryMechanism?.steps[0]?.id ?? ""}
          onSelectMechanismStep={(stepId) => dispatch({ type: "SELECT_MECHANISM_STEP", stepId })}
          onSelectSecondaryStep={(stepId) => dispatch({ type: "SELECT_SECONDARY_MECHANISM_STEP", stepId })}
          mechanismEvidence={mechanismEvidence}
          secondaryEvidence={secondaryEvidence}
          mechanismSlot={slotForEvidence(mechanismEvidence, "mechanism")}
          secondarySlot={slotForEvidence(secondaryEvidence, "secondaryMechanism")}
          locale={locale}
        />
        <ComparePairs
          pairs={topic.comparePairs}
          topic={topic}
          activePairId={interactionState.activeComparePairId ?? topic.comparePairs[0]?.id ?? ""}
          evidence={compareEvidence}
          visualSlot={slotForEvidence(compareEvidence, "comparePairs")}
          onSelectPair={(pairId) => dispatch({ type: "SELECT_COMPARE_PAIR", pairId })}
          locale={locale}
        />

        <ClickTaskDeck topic={topic} state={interactionState} presentation={presentation} dispatch={dispatch} locale={locale} />

        <SpeakTemplates templates={topic.speakTemplates} locale={locale} />
        <ParentTips tips={topic.parentTips} locale={locale} />
      </section>

      <RelatedTopics topics={topic.relatedTopics} map={map} locale={locale} />
    </main>
  );
}

export function TopicPage({ slug, locale, map }: Props) {
  const topic = getTopic(slug, locale);

  if (!topic) {
    return (
      <main className="page-shell topic-page">
        <a className="back-link" href="#">
          <ArrowLeft size={18} />
          {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
        </a>
        <p>Topic not found.</p>
      </main>
    );
  }

  return <TopicPageContent topic={topic} locale={locale} map={map} />;
}
