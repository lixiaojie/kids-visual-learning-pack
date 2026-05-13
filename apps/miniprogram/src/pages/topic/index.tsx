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

      <View className="section">
        <Text className="section-title">{topic.mechanism.title ?? (locale === "zh-CN" ? "它怎么发生" : "How it works")}</Text>
        {topic.mechanism.steps.slice(0, 4).map((step) => (
          <View className="step" key={step.id}>
            <Text className="step-title">{step.shortTitle}</Text>
            <Text className="section-body">{step.childExplanation}</Text>
          </View>
        ))}
      </View>

      <TopicSummary topic={topic} locale={locale} />
    </View>
  );
}
