import { Sparkles } from "lucide-react";
import type { World } from "../../types/world";
import { GeneratedImage } from "../shared/GeneratedImage";
import { SectionHeader } from "../shared/SectionHeader";
import { getExternalHref } from "../../lib/asset-resolve";
import { getTopicCardAssetId } from "../../lib/asset-map";

type Props = { world: World };

export function InterestBand({ world }: Props) {
  return (
    <section className="interest-band" id="topics">
      <SectionHeader title={world.entryCard.title} kicker={world.entryCard.badge}>
        {world.entryCard.subtitle}
      </SectionHeader>
      <div className="topic-card-grid animation-topics">
        {world.topicCards.map((topic) => (
          <a className="topic-card completed" href={getExternalHref(topic.href)} key={topic.id}>
            <GeneratedImage alt="" assetId={getTopicCardAssetId(topic)} className="topic-card-image" />
            <Sparkles />
            <strong>{topic.title}</strong>
            <span>{topic.cardDescription}</span>
            <div className="tag-row">{topic.learningGoalTags?.map((tag) => <em key={tag}>{tag}</em>)}</div>
            {topic.suggestedRoute && <small>{topic.suggestedRoute}</small>}
          </a>
        ))}
      </div>
    </section>
  );
}
