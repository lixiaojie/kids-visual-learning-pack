import type { Topic, VisualEvidenceState, VisualSlot } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";
import { TopicVisual } from "./TopicVisual";

type Props = {
  pairs: Topic["comparePairs"];
  topic: Topic;
  activePairId: string;
  evidence?: VisualEvidenceState | null;
  visualSlot?: VisualSlot | null;
  onSelectPair: (id: string) => void;
  locale: string;
};

export function ComparePairs({ pairs, topic, activePairId, evidence, visualSlot, onSelectPair, locale }: Props) {
  return (
    <article className="panel wide" id="topic-compare">
      <SectionHeader title={locale === "zh-CN" ? "容易混淆" : "Easy mix-ups"} />
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={locale === "zh-CN" ? "对比图" : "Compare visual"} locale={locale === "en-US" ? "en-US" : "zh-CN"} />
      <div className="compare-grid">
        {pairs.map((pair) => (
          <button
            className={activePairId === pair.id ? "compare-card active" : "compare-card"}
            key={pair.id}
            type="button"
            data-evidence-source={`comparePairs.${pair.id}`}
            onClick={() => onSelectPair(pair.id)}
          >
            <TopicVisual slot={topic.visualSlots?.find((slot) => slot.target === `comparePairs.${pair.id}`)} fallbackAlt={pair.title} locale={locale === "en-US" ? "en-US" : "zh-CN"} />
            <strong>{pair.title}</strong>
            <div>
              <span>{pair.a.name}</span>
              <small>{pair.a.points.join(" · ")}</small>
            </div>
            <div>
              <span>{pair.b.name}</span>
              <small>{pair.b.points.join(" · ")}</small>
            </div>
            <em>{pair.childConclusion}</em>
          </button>
        ))}
      </div>
    </article>
  );
}
