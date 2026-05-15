import type { ExplorationMap } from "../../types/world";
import { StatusPill } from "../shared/StatusPill";

type Props = { topics: string[]; map: ExplorationMap; locale: string };

export function RelatedTopics({ topics, map, locale }: Props) {
  return (
    <section className="related-strip" id="topic-related">
      <strong>{locale === "zh-CN" ? "继续探索" : "Keep exploring"}</strong>
      <div className="tag-row">
        {topics.map((related) => (
          <em key={related}>{related}</em>
        ))}
      </div>
      <StatusPill status="building" map={map} />
    </section>
  );
}
