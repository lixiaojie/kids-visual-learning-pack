import { useState } from "react";
import { resolveVisualEvidence } from "@yutou/kids-content";
import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";
import { TopicVisual } from "./TopicVisual";

type Props = { pairs: Topic["comparePairs"]; topic: Topic; locale: string };

export function ComparePairs({ pairs, topic, locale }: Props) {
  const [activePairId, setActivePairId] = useState(pairs[0]?.id ?? "");
  const activeEvidence = activePairId
    ? resolveVisualEvidence(topic, { source: `comparePairs.${activePairId}`, result: "selected", locale: locale === "en-US" ? "en-US" : "zh-CN" })
    : null;
  const sharedSlot = activeEvidence
    ? topic.visualSlots?.find((slot) => slot.id === activeEvidence.visualSlotId)
    : topic.visualSlots?.find((slot) => slot.target === "comparePairs");

  return (
    <article className="panel wide" id="topic-compare">
      <SectionHeader title={locale === "zh-CN" ? "容易混淆" : "Easy mix-ups"} />
      <TopicVisual slot={sharedSlot} evidence={activeEvidence} fallbackAlt={locale === "zh-CN" ? "对比图" : "Compare visual"} locale={locale === "en-US" ? "en-US" : "zh-CN"} />
      <div className="compare-grid">
        {pairs.map((pair) => (
          <button
            className={activePairId === pair.id ? "compare-card active" : "compare-card"}
            key={pair.id}
            type="button"
            data-evidence-source={`comparePairs.${pair.id}`}
            onClick={() => setActivePairId(pair.id)}
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
