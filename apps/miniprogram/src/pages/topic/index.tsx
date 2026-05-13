import { useMemo } from "react";
import { useRouter, useShareAppMessage, useShareTimeline } from "@tarojs/taro";
import { Text, View } from "@tarojs/components";
import {
  getKnowledgeTopicAssetId,
  getTopic,
  type Locale,
  type Topic,
} from "@yutou/kids-content";
import { GeneratedImage } from "../../components/shared/GeneratedImage";
import { ClickTaskCard } from "../../components/topic/ClickTaskCard";
import { InfoList } from "../../components/topic/InfoList";
import { TopicSummary } from "../../components/topic/TopicSummary";
import "./index.scss";

const supportedLocales: Locale[] = ["zh-CN", "en-US"];

function normalizeLocale(locale: string | undefined): Locale {
  return supportedLocales.includes(locale as Locale) ? (locale as Locale) : "zh-CN";
}

function getHeroAssetId(topic: Topic) {
  return getKnowledgeTopicAssetId({ slug: topic.slug, title: topic.title, status: "building", cardDescription: "" });
}

export default function TopicPage() {
  const router = useRouter();
  const locale = normalizeLocale(router.params.locale);
  const slug = router.params.slug || "dinosaurs";
  const topic = useMemo(() => getTopic(slug, locale), [slug, locale]);

  useShareAppMessage(() => ({
    title: topic ? `芋头宇宙｜${topic.title}` : "芋头宇宙",
    path: `/pages/topic/index?slug=${slug}&locale=${locale}`,
  }));

  useShareTimeline(() => ({
    title: topic ? `芋头宇宙｜${topic.title}` : "芋头宇宙",
    query: `slug=${slug}&locale=${locale}`,
  }));

  if (!topic) {
    return (
      <View className="topic-page">
        <Text className="missing-title">这个探索页还在准备中</Text>
      </View>
    );
  }

  return (
    <View className="topic-page">
      <View className="topic-hero">
        <Text className="topic-kicker">{topic.hero.kicker}</Text>
        <Text className="topic-title">{topic.hero.title}</Text>
        <Text className="topic-lead">{topic.hero.lead}</Text>
        <GeneratedImage assetId={getHeroAssetId(topic)} alt={topic.title} className="topic-image" />
      </View>

      <View className="section">
        <Text className="section-title">{locale === "zh-CN" ? "先观察" : "Observe"}</Text>
        <Text className="section-body">{topic.hero.sceneExplanation}</Text>
      </View>

      <InfoList
        title={locale === "zh-CN" ? "认识几个代表对象" : "Representative objects"}
        items={topic.representativeObjects.slice(0, 5).map((item) => ({
          id: item.id,
          title: item.name,
          body: item.childExplanation,
        }))}
      />

      <View className="section">
        <Text className="section-title">{topic.mechanism.title ?? (locale === "zh-CN" ? "它怎么发生" : "How it works")}</Text>
        {topic.mechanism.steps.slice(0, 4).map((step) => (
          <View className="step" key={step.id}>
            <Text className="step-title">{step.shortTitle}</Text>
            <Text className="section-body">{step.childExplanation}</Text>
          </View>
        ))}
      </View>

      <InfoList
        title={locale === "zh-CN" ? "比一比" : "Compare"}
        items={topic.comparePairs.slice(0, 3).map((pair) => ({
          id: pair.id,
          title: pair.title,
          body: pair.childConclusion,
        }))}
      />

      <View className="section">
        <Text className="section-title">{locale === "zh-CN" ? "点击任务" : "Tap tasks"}</Text>
        <View className="task-stack">
          {topic.clickTasks.slice(0, 3).map((task) => (
            <ClickTaskCard task={task} key={task.id} />
          ))}
        </View>
      </View>

      <TopicSummary topic={topic} locale={locale} />

      <InfoList
        title={locale === "zh-CN" ? "家长可以这样陪聊" : "Parent prompts"}
        items={topic.parentTips.slice(0, 3).map((tip, index) => ({
          id: `tip-${index}`,
          title: `${locale === "zh-CN" ? "提示" : "Prompt"} ${index + 1}`,
          body: tip,
        }))}
      />
    </View>
  );
}
