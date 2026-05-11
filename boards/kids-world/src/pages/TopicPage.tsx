import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import type { ExplorationMap } from "../types/world";
import type { Locale } from "../types/topic";
import { getTopic } from "../data/loaders/load-topic";
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

type Props = { slug: string; locale: Locale; map: ExplorationMap };

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

  const [activeObjectId, setActiveObjectId] = useState(topic.representativeObjects[0]?.id ?? "");
  const activeObject = topic.representativeObjects.find((item) => item.id === activeObjectId) ?? topic.representativeObjects[0];

  return (
    <main className="page-shell topic-page">
      <a className="back-link" href="#">
        <ArrowLeft size={18} />
        {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
      </a>

      <TopicHero topic={topic} />

      <section className="content-grid">
        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "看一看主场景" : "Look at the scene"} kicker={topic.coreQuestion}>
            {topic.hero.sceneExplanation}
          </SectionHeader>
        </article>

        <ClassificationGroups groups={topic.classificationGroups} activeGroupId={activeObject?.groupId} locale={locale} />
        <RepresentativeObjects objects={topic.representativeObjects} activeObjectId={activeObjectId} onSelectObject={setActiveObjectId} locale={locale} />
        <MechanismSteps mechanism={topic.mechanism} secondary={topic.secondaryMechanism} locale={locale} />
        <ComparePairs pairs={topic.comparePairs} locale={locale} />

        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "点击任务" : "Tap tasks"} kicker={locale === "zh-CN" ? "不计分，多试几次" : "No score pressure"} />
          <div className="task-grid">
            {topic.clickTasks.map((task) => (
              <ClickTaskCard task={task} key={task.id} />
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
