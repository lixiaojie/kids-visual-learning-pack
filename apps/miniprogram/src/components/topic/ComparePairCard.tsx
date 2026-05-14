import { Text, View } from "@tarojs/components";
import type { Topic } from "@yutou/kids-content";
import "./ComparePairCard.scss";

type ComparePair = Topic["comparePairs"][number];

function CompareSide({ name, points }: ComparePair["a"]) {
  return (
    <View className="compare-side">
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

export function ComparePairCard({ pair }: { pair: ComparePair }) {
  return (
    <View className="compare-pair-card">
      <Text className="compare-pair-title">{pair.title}</Text>
      <View className="compare-sides">
        <CompareSide name={pair.a.name} points={pair.a.points} />
        <CompareSide name={pair.b.name} points={pair.b.points} />
      </View>
      <Text className="compare-conclusion">{pair.childConclusion}</Text>
    </View>
  );
}
