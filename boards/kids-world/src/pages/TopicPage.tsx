import { useEffect, useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";
import {
  getTopic,
  getTopicLearningFlow,
  getVisualSlotForTarget,
  type ExplorationMap,
  type Locale,
  type Topic,
} from "@yutou/kids-content";
import { SectionHeader } from "../components/shared/SectionHeader";
import { TopicHero } from "../components/topic/TopicHero";
import { ClassificationGroups } from "../components/topic/ClassificationGroups";
import { RepresentativeObjects } from "../components/topic/RepresentativeObjects";
import { MechanismSteps } from "../components/topic/MechanismSteps";
import { ComparePairs } from "../components/topic/ComparePairs";
import { ClickTaskCard } from "../components/topic/ClickTaskCard";
import { SpeakTemplates } from "../components/topic/SpeakTemplates";
import { ParentTips } from "../components/topic/ParentTips";
import { RelatedTopics } from "../components/topic/RelatedTopics";
import { LearningFlowRail } from "../components/topic/LearningFlowRail";
import { TopicVisual } from "../components/topic/TopicVisual";

type Props = { slug: string; locale: Locale; map: ExplorationMap };

function TopicPageContent({ topic, locale, map }: { topic: Topic; locale: Locale; map: ExplorationMap }) {
  const [activeObjectId, setActiveObjectId] = useState(topic.representativeObjects[0]?.id ?? "");
  const activeObject = topic.representativeObjects.find((item) => item.id === activeObjectId) ?? topic.representativeObjects[0];
  const flowStages = useMemo(() => getTopicLearningFlow(topic, locale), [topic, locale]);
  const [activeStageId, setActiveStageId] = useState(flowStages[0]?.id ?? "");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!visible) return;
        const stage = flowStages.find((item) => item.sectionIds.includes(visible.target.id));
        if (stage) setActiveStageId(stage.id);
      },
      { rootMargin: "-28% 0px -58% 0px", threshold: [0.1, 0.35, 0.6] },
    );

    const observedSections = flowStages
      .flatMap((stage) => stage.sectionIds)
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => Boolean(section));
    observedSections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [flowStages]);

  function handleSelectGroup(groupId: string) {
    const firstObject = topic.representativeObjects.find((item) => item.groupId === groupId);
    if (firstObject) setActiveObjectId(firstObject.id);
    document.getElementById("topic-objects")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main className="page-shell topic-page">
      <a className="back-link" href="#">
        <ArrowLeft size={18} />
        {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
      </a>

      <TopicHero topic={topic} />
      <LearningFlowRail activeStageId={activeStageId} stages={flowStages} locale={locale} />

      <section className="content-grid">
        <article className="panel wide" id="topic-observe">
          <SectionHeader title={locale === "zh-CN" ? "看一看主场景" : "Look at the scene"} kicker={topic.coreQuestion}>
            {topic.hero.sceneExplanation}
          </SectionHeader>
        </article>

        <ClassificationGroups
          topic={topic}
          groups={topic.classificationGroups}
          activeGroupId={activeObject?.groupId}
          onSelectGroup={handleSelectGroup}
          locale={locale}
        />
        <RepresentativeObjects
          topic={topic}
          objects={topic.representativeObjects}
          activeObjectId={activeObjectId}
          onSelectObject={setActiveObjectId}
          visualSlot={getVisualSlotForTarget(topic, `representativeObjects.${activeObjectId}`)}
          locale={locale}
        />
        <MechanismSteps
          topic={topic}
          mechanism={topic.mechanism}
          secondary={topic.secondaryMechanism}
          mechanismSlot={getVisualSlotForTarget(topic, "mechanism")}
          secondarySlot={getVisualSlotForTarget(topic, "secondaryMechanism")}
          locale={locale}
        />
        <ComparePairs pairs={topic.comparePairs} topic={topic} locale={locale} />

        <article className="panel wide" id="topic-tasks">
          <SectionHeader title={locale === "zh-CN" ? "点击任务" : "Tap tasks"} kicker={locale === "zh-CN" ? "不计分，多试几次" : "No score pressure"} />
          <TopicVisual slot={topic.visualSlots?.find((slot) => slot.target === "clickTasks")} fallbackAlt={locale === "zh-CN" ? "任务图" : "Task visual"} locale={locale} />
          <div className="task-grid">
            {topic.clickTasks.map((task) => (
              <ClickTaskCard
                task={task}
                topic={topic}
                key={task.id}
                locale={locale}
                visualSlot={topic.visualSlots?.find((slot) => slot.target === `clickTasks.${task.id}`)}
              />
            ))}
          </div>
        </article>

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
