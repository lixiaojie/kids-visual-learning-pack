import { forwardRef } from "react";
import { ChevronRight } from "lucide-react";
import type { ExplorationMap, World } from "../../types/world";
import type { Locale } from "../../types/topic";
import { GeneratedImage } from "../shared/GeneratedImage";
import { StatusPill } from "../shared/StatusPill";
import { SectionHeader } from "../shared/SectionHeader";
import { getTopicHref } from "../../lib/asset-resolve";
import { getKnowledgeTopicAssetId } from "../../lib/asset-map";
import { hasTopicData } from "../../data/loaders/load-topic";

type Props = { world: World; map: ExplorationMap; locale: Locale };

export const WorldTopicPanel = forwardRef<HTMLDivElement, Props>(function WorldTopicPanel({ world, map, locale }, ref) {
  return (
    <section className="selected-world-panel" ref={ref}>
      <div>
        <SectionHeader title={world.name} kicker={world.entryCard.badge}>
          {world.parentNote}
        </SectionHeader>
      </div>
      <div className="topic-card-grid">
        {world.topicCards.map((topic) => {
          const topicHref = topic.slug && hasTopicData(topic.slug) ? getTopicHref(topic.slug) : undefined;
          const Tag = topicHref ? "a" : "div";
          return (
            <Tag className={`topic-card ${topic.status}`} href={topicHref} key={topic.slug ?? topic.id}>
              <GeneratedImage alt="" assetId={getKnowledgeTopicAssetId(topic)} className="topic-card-image" />
              <StatusPill status={topic.status} map={map} />
              <strong>{topic.title}</strong>
              <span>{topic.cardDescription}</span>
              <div className="tag-row">{topic.learningGoalTags?.map((tag) => <em key={tag}>{tag}</em>)}</div>
              {topicHref && (
                <small className="open-topic">
                  {locale === "zh-CN" ? "打开看板" : "Open board"} <ChevronRight size={15} />
                </small>
              )}
            </Tag>
          );
        })}
      </div>
    </section>
  );
});
