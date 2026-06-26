import { useRouter, useShareAppMessage, useShareTimeline } from "@tarojs/taro";
import { Text, View } from "@tarojs/components";
import { getTopic, type Locale } from "@yutou/kids-content";
import { SceneDeckTopicPage } from "../../components/topic/SceneDeckTopicPage";
import "./index.scss";

const supportedLocales: Locale[] = ["zh-CN", "en-US"];

function normalizeLocale(locale: string | undefined): Locale {
  return supportedLocales.includes(locale as Locale) ? (locale as Locale) : "zh-CN";
}

export default function TopicPage() {
  const router = useRouter();
  const locale = normalizeLocale(router.params.locale);
  const slug = router.params.slug || "dinosaurs";
  const topic = getTopic(slug, locale);

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

  return <SceneDeckTopicPage topic={topic} locale={locale} />;
}
