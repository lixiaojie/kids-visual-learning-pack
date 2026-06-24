import { useEffect, useState } from "react";
import { useRouter, useShareAppMessage, useShareTimeline } from "@tarojs/taro";
import { Text, View } from "@tarojs/components";
import type { Locale, Topic } from "@yutou/kids-content";
import { getTopicPageUrl } from "../../lib/topic-routes";
import { SceneDeckTopicPage } from "./SceneDeckTopicPage";
import "../../pages/topic/index.scss";

const supportedLocales: Locale[] = ["zh-CN", "en-US"];

function normalizeLocale(locale: string | undefined): Locale {
  return supportedLocales.includes(locale as Locale) ? (locale as Locale) : "zh-CN";
}

type Props = {
  slug: string;
  loadTopic: (locale: Locale) => Promise<Topic> | Topic;
};

export function TopicRuntimePage({ slug, loadTopic: loadTopicForLocale }: Props) {
  const router = useRouter();
  const locale = normalizeLocale(router.params.locale);
  const [topic, setTopic] = useState<Topic | null>(null);
  const [isTopicLoading, setIsTopicLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsTopicLoading(true);
    setTopic(null);

    Promise.resolve(loadTopicForLocale(locale))
      .then((loadedTopic) => {
        if (!cancelled) setTopic(loadedTopic);
      })
      .finally(() => {
        if (!cancelled) setIsTopicLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [slug, locale, loadTopicForLocale]);

  useShareAppMessage(() => ({
    title: topic ? `芋头宇宙｜${topic.title}` : "芋头宇宙",
    path: getTopicPageUrl(slug, locale),
  }));

  useShareTimeline(() => ({
    title: topic ? `芋头宇宙｜${topic.title}` : "芋头宇宙",
    query: `locale=${locale}`,
  }));

  if (isTopicLoading) {
    return (
      <View className="topic-page">
        <Text className="missing-title">探索页加载中</Text>
      </View>
    );
  }

  if (!topic) {
    return (
      <View className="topic-page">
        <Text className="missing-title">这个探索页还在准备中</Text>
      </View>
    );
  }

  return <SceneDeckTopicPage topic={topic} locale={locale} />;
}
