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

export function ComparePairs({ pairs, topic, activePairId, evidence, visualSlot, onSelectPair, locale }: Props) {
  const activePair = pairs.find((pair) => pair.id === activePairId) ?? pairs[0];
  const visualSupport = activePair
    ? {
        title: activePair.title,
        body: `${activePair.a.name}: ${activePair.a.points.join(" · ")}\n${activePair.b.name}: ${activePair.b.points.join(" · ")}`,
        note: activePair.childConclusion,
      }
    : null;

  return (
    <article className="panel wide interaction-panel" id="topic-compare">
      <SectionHeader title={locale === "zh-CN" ? "容易混淆" : "Easy mix-ups"} />
      <div className="compare-grid interaction-controls node-strip">
        {pairs.map((pair, index) => (
          <button
            className={activePairId === pair.id ? "compare-card node-button active" : "compare-card node-button"}
            key={pair.id}
            type="button"
            data-evidence-source={`comparePairs.${pair.id}`}
            onClick={() => onSelectPair(pair.id)}
          >
            <span className="node-index">{index + 1}</span>
            <strong className="node-label">{pair.title}</strong>
          </button>
        ))}
      </div>
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={locale === "zh-CN" ? "对比图" : "Compare visual"} locale={locale === "en-US" ? "en-US" : "zh-CN"} visualSupport={visualSupport} />
    </article>
  );
}
