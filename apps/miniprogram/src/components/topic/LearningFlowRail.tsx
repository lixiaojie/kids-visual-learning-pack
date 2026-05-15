import Taro from "@tarojs/taro";
import { ScrollView, Text, View } from "@tarojs/components";
import type { LearningFlowStage, Locale } from "@yutou/kids-content";
import "./LearningFlowRail.scss";

type Props = {
  activeStageId: string;
  stages: LearningFlowStage[];
  locale: Locale;
  onSelectStage: (id: string) => void;
};

export function LearningFlowRail({ activeStageId, stages, locale, onSelectStage }: Props) {
  function handleSelect(stage: LearningFlowStage) {
    onSelectStage(stage.id);
    const selector = `#${stage.sectionIds[0]}`;
    Taro.pageScrollTo({ selector, duration: 280 });
  }

  return (
    <View className="learning-flow-wrap">
      <Text className="learning-flow-title">{locale === "zh-CN" ? "学习路线" : "Learning path"}</Text>
      <ScrollView className="learning-flow-scroll" scrollX enhanced showScrollbar={false}>
        <View className="learning-flow-list">
          {stages.map((stage, index) => (
            <View
              className={`learning-flow-chip ${activeStageId === stage.id ? "active" : ""}`}
              key={stage.id}
              onClick={() => handleSelect(stage)}
            >
              <Text className="learning-flow-index">{index + 1}</Text>
              <Text className="learning-flow-label">{stage.label}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}
