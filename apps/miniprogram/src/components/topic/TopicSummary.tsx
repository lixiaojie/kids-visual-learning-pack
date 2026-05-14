import { Text, View } from "@tarojs/components";
import type { Locale, Topic } from "@yutou/kids-content";
import "./TopicSummary.scss";

export function TopicSummary({ topic, locale }: { topic: Topic; locale: Locale }) {
  return (
    <View className="topic-summary">
      <Text className="summary-kicker">{topic.coreQuestion}</Text>
      <Text className="summary-title">{locale === "zh-CN" ? "可以这样讲" : "Try saying this"}</Text>
      {topic.speakTemplates.map((template) => (
        <Text className="summary-line" key={template}>
          {template}
        </Text>
      ))}
    </View>
  );
}
