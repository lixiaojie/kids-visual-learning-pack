import Taro from "@tarojs/taro";
import { ScrollView, Text, View } from "@tarojs/components";
import type { LearningFlowStage, Locale } from "@yutou/kids-content";
import "./LearningFlowRail.scss";

type Props = {
  activeStageId: string;
  stages: LearningFlowStage[];
  locale: Locale;
  onSelectStage: (id: string) => void;
  collapsed?: boolean;
  hidden?: boolean;
  onExpand?: () => void;
};

export function LearningFlowRail({ activeStageId, stages, locale, onSelectStage, collapsed = false, hidden = false, onExpand }: Props) {
  function handleSelect(stage: LearningFlowStage) {
    onSelectStage(stage.id);
    const selector = `#${stage.sectionIds[0]}`;
    Taro.pageScrollTo({ selector, duration: 280 });
  }

  const activeStageIndex = Math.max(0, stages.findIndex((stage) => stage.id === activeStageId));
  const activeStage = stages[activeStageIndex] ?? stages[0];

  return (
    <View className={`learning-flow-wrap ${collapsed ? "collapsed" : ""} ${hidden ? "hidden" : ""}`}>
      <Text className="learning-flow-title">{locale === "zh-CN" ? "学习路线" : "Learning path"}</Text>
      {collapsed && activeStage ? (
        <View className="learning-flow-current" onClick={() => onExpand?.()}>
          {activeStageIndex + 1}. {activeStage.label}
        </View>
      ) : null}
      <ScrollView className="learning-flow-scroll" scrollX enhanced showScrollbar={false}>
        <View className="learning-flow-list">
          {stages.map((stage, index) => (
            <View
              className={`learning-flow-chip ${activeStageId === stage.id ? "active" : ""}`}
              key={stage.id}
              onClick={() => handleSelect(stage)}
            >
              <Text className="learning-flow-index">{index + 1}</Text>
              <View className="learning-flow-label">{stage.label}</View>
              {stage.childPrompt ? <View className="learning-flow-prompt">{stage.childPrompt}</View> : null}
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}
