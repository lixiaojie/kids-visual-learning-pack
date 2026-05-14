import { useMemo } from "react";
import { useRouter, useShareAppMessage, useShareTimeline } from "@tarojs/taro";
import { Navigator, Text, View } from "@tarojs/components";
import {
  getMap,
  getKnowledgeTopicAssetId,
  getTopic,
  type Locale,
  type Topic,
} from "@yutou/kids-content";
import { GeneratedImage } from "../../components/shared/GeneratedImage";
import { ClickTaskCard } from "../../components/topic/ClickTaskCard";
import { ComparePairCard } from "../../components/topic/ComparePairCard";
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
  const map = useMemo(() => getMap(locale, "miniprogram"), [locale]);
  const relatedTopicCards = useMemo(() => {
    if (!topic) return [];
    const relatedTopics = new Set(topic.relatedTopics);
    return map.worlds.flatMap((world) => world.topicCards).filter((card) => card.slug && relatedTopics.has(card.slug));
  }, [map, topic]);

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
        title={locale === "zh-CN" ? "先分成几类" : "Classification groups"}
        items={topic.classificationGroups.map((group) => ({
          id: group.id,
          title: group.name,
          body: group.parentNote ? `${group.childExplanation}\n${group.parentNote}` : group.childExplanation,
        }))}
      />

      <InfoList
        title={locale === "zh-CN" ? "认识几个代表对象" : "Representative objects"}
        items={topic.representativeObjects.map((item) => ({
          id: item.id,
          title: item.name,
          body: item.childExplanation,
        }))}
      />

      <View className="section">
        <Text className="section-title">{topic.mechanism.title ?? (locale === "zh-CN" ? "它怎么发生" : "How it works")}</Text>
        {topic.mechanism.steps.map((step) => (
          <View className="step" key={step.id}>
            <Text className="step-title">{step.shortTitle}</Text>
            <Text className="section-body">{step.childExplanation}</Text>
          </View>
        ))}
      </View>

      {topic.secondaryMechanism && (
        <View className="section">
          <Text className="section-title">{topic.secondaryMechanism.title}</Text>
          {topic.secondaryMechanism.steps.map((step) => (
            <View className="step" key={step.id}>
              <Text className="step-title">{step.shortTitle}</Text>
              <Text className="section-body">{step.childExplanation}</Text>
            </View>
          ))}
        </View>
      )}

      <View className="section">
        <Text className="section-title">{locale === "zh-CN" ? "比一比" : "Compare"}</Text>
        <View className="compare-stack">
          {topic.comparePairs.map((pair) => (
            <ComparePairCard pair={pair} key={pair.id} />
          ))}
        </View>
      </View>

      <View className="section">
        <Text className="section-title">{locale === "zh-CN" ? "点击任务" : "Tap tasks"}</Text>
        <View className="task-stack">
          {topic.clickTasks.map((task) => (
            <ClickTaskCard task={task} key={task.id} />
          ))}
        </View>
      </View>

      <TopicSummary topic={topic} locale={locale} />

      <InfoList
        title={locale === "zh-CN" ? "家长可以这样陪聊" : "Parent prompts"}
        items={topic.parentTips.map((tip, index) => ({
          id: `tip-${index}`,
          title: `${locale === "zh-CN" ? "提示" : "Prompt"} ${index + 1}`,
          body: tip,
        }))}
      />

      {relatedTopicCards.length > 0 && (
        <View className="section">
          <Text className="section-title">{locale === "zh-CN" ? "接着探索" : "Explore next"}</Text>
          <View className="related-list">
            {relatedTopicCards.map((card) => (
              <Navigator
                className="related-link"
                hoverClass="related-link-hover"
                key={card.slug}
                url={`/pages/topic/index?slug=${card.slug}&locale=${locale}`}
              >
                <Text className="related-title">{card.title}</Text>
                <Text className="section-body">{card.cardDescription}</Text>
              </Navigator>
            ))}
          </View>
        </View>
      )}
    </View>
  );
}
