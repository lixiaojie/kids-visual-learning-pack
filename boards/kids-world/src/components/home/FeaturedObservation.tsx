import { ChevronRight } from "lucide-react";
import {
  getKnowledgeTopicAssetId,
  getTopic,
  hasTopicData,
  type ExplorationMap,
  type Locale,
  type TopicCard,
} from "@yutou/kids-content";
import { getTopicHref } from "../../lib/asset-resolve";
import { GeneratedImage } from "../shared/GeneratedImage";
import { SectionHeader } from "../shared/SectionHeader";
import { StatusPill } from "../shared/StatusPill";

type Props = { map: ExplorationMap; locale: Locale };

function findFeaturedObservation(map: ExplorationMap): TopicCard | undefined {
  return map.worlds.flatMap((world) => world.topicCards).find((topic) => topic.slug === "cicada-life");
}

export function FeaturedObservation({ map, locale }: Props) {
  const topicCard = findFeaturedObservation(map);
  const topic = topicCard?.slug ? getTopic(topicCard.slug, locale) : undefined;

  if (!topicCard?.slug || !topic || !hasTopicData(topicCard.slug)) return null;

  return (
    <section className="featured-observation" id="recent-observation">
      <SectionHeader
        title={locale === "zh-CN" ? "本周新发现" : "This Week's Observation"}
        kicker={locale === "zh-CN" ? "最近观察" : "Recent observation"}
      >
        {locale === "zh-CN"
          ? "从孩子身边真实发现的问题出发，再进入对应的知识世界。"
          : "Start from a real observation nearby, then enter the matching knowledge world."}
      </SectionHeader>
      <a className="featured-observation-card" href={getTopicHref(topicCard.slug)}>
        <GeneratedImage alt="" assetId={getKnowledgeTopicAssetId(topicCard)} className="featured-observation-image" />
        <div className="featured-observation-copy">
          <StatusPill status={topicCard.status} map={map} />
          <strong>{topic.title}</strong>
          <span>{topic.coreQuestion}</span>
          <div className="tag-row">{topicCard.learningGoalTags?.map((tag) => <em key={tag}>{tag}</em>)}</div>
          <small className="open-topic">
            {locale === "zh-CN" ? "进入生命世界观察" : "Open the life observation"} <ChevronRight size={15} />
          </small>
        </div>
      </a>
    </section>
  );
}
