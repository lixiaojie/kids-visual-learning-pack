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
  onSelectSide?: (pairId: string, side: "a" | "b") => void;
  locale: string;
};

export function ComparePairs({ pairs, topic, activePairId, evidence, visualSlot, onSelectPair, onSelectSide, locale }: Props) {
  return (
    <article className="panel wide interaction-panel" id="topic-compare">
      <SectionHeader title={locale === "zh-CN" ? "容易混淆" : "Easy mix-ups"} />
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={locale === "zh-CN" ? "对比图" : "Compare visual"} locale={locale === "en-US" ? "en-US" : "zh-CN"} />
      <div className="compare-grid interaction-controls">
        {pairs.map((pair) => (
          <div
            className={activePairId === pair.id ? "compare-card active" : "compare-card"}
            key={pair.id}
            role="button"
            tabIndex={0}
            data-evidence-source={`comparePairs.${pair.id}`}
            onClick={() => onSelectPair(pair.id)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") onSelectPair(pair.id);
            }}
          >
            <TopicVisual slot={topic.visualSlots?.find((slot) => slot.target === `comparePairs.${pair.id}`)} fallbackAlt={pair.title} locale={locale === "en-US" ? "en-US" : "zh-CN"} />
            <strong>{pair.title}</strong>
            <div
              role="button"
              tabIndex={0}
              onClick={(event) => {
                event.stopPropagation();
                onSelectSide?.(pair.id, "a");
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") onSelectSide?.(pair.id, "a");
              }}
            >
              <span>{pair.a.name}</span>
              <small>{pair.a.points.join(" · ")}</small>
            </div>
            <div
              role="button"
              tabIndex={0}
              onClick={(event) => {
                event.stopPropagation();
                onSelectSide?.(pair.id, "b");
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") onSelectSide?.(pair.id, "b");
              }}
            >
              <span>{pair.b.name}</span>
              <small>{pair.b.points.join(" · ")}</small>
            </div>
            <em>{pair.childConclusion}</em>
          </div>
        ))}
      </div>
    </article>
  );
}
