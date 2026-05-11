import { CheckCircle2 } from "lucide-react";
import type { Topic } from "../../types/topic";
import { topicHeroAssetBySlug } from "../../lib/asset-map";
import { GeneratedImage } from "../shared/GeneratedImage";

function PlaceholderScene({ topic }: { topic: Topic }) {
  const type = topic.hero.placeholder?.type ?? topic.pageType;
  const assetId = topicHeroAssetBySlug[topic.slug];
  return (
    <div className={`placeholder-scene ${String(type)} ${assetId ? "generated-scene" : ""}`}>
      <GeneratedImage
        alt=""
        assetId={assetId}
        className="scene-image"
        fallbackPath={topic.hero.placeholder?.asset ?? topic.assets?.hero?.path}
      />
      <span className="scene-orbit" />
      <span className="scene-node one" />
      <span className="scene-node two" />
      <span className="scene-node three" />
      <span className="scene-label">{topic.title}</span>
    </div>
  );
}

export function TopicHero({ topic }: { topic: Topic }) {
  return (
    <section className="topic-hero">
      <div className="topic-hero-copy">
        <p className="kicker">{topic.hero.kicker}</p>
        <h1>{topic.hero.title}</h1>
        <p>{topic.hero.lead}</p>
        <div className="goal-list">
          {topic.learningGoals.map((goal) => (
            <span key={goal}>
              <CheckCircle2 size={16} />
              {goal}
            </span>
          ))}
        </div>
      </div>
      <PlaceholderScene topic={topic} />
    </section>
  );
}
