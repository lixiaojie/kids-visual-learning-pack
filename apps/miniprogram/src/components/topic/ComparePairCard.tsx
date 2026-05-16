import { Text, View } from "@tarojs/components";
import type { Locale, Topic, VisualEvidenceState, VisualSlot } from "@yutou/kids-content";
import { TopicVisual } from "./TopicVisual";
import "./ComparePairCard.scss";

type ComparePair = Topic["comparePairs"][number];

function CompareSide({
  name,
  points,
  onSelect,
}: ComparePair["a"] & {
  onSelect?: (event: { stopPropagation?: () => void }) => void;
}) {
  return (
    <View className="compare-side" onClick={onSelect}>
      <Text className="compare-side-name">{name}</Text>
      <View className="compare-point-list">
        {points.map((point) => (
          <Text className="compare-point" key={point}>
            {point}
          </Text>
        ))}
      </View>
    </View>
  );
}

export function ComparePairCard({
  pair,
  visualSlot,
  evidence,
  active,
  onSelect,
  onSelectSide,
  locale = "zh-CN",
}: {
  pair: ComparePair;
  visualSlot?: VisualSlot | null;
  evidence?: VisualEvidenceState | null;
  active?: boolean;
  onSelect?: () => void;
  onSelectSide?: (side: "a" | "b") => void;
  locale?: Locale;
}) {
  return (
    <View className={`compare-pair-card ${active ? "active" : ""}`} onClick={onSelect} data-evidence-source={`comparePairs.${pair.id}`}>
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={pair.title} locale={locale} />
      <Text className="compare-pair-title">{pair.title}</Text>
      <View className="compare-sides">
        <CompareSide
          name={pair.a.name}
          points={pair.a.points}
          onSelect={(event) => {
            event.stopPropagation?.();
            onSelectSide?.("a");
          }}
        />
        <CompareSide
          name={pair.b.name}
          points={pair.b.points}
          onSelect={(event) => {
            event.stopPropagation?.();
            onSelectSide?.("b");
          }}
        />
      </View>
      <Text className="compare-conclusion">{pair.childConclusion}</Text>
    </View>
  );
}
