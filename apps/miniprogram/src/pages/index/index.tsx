import Taro from "@tarojs/taro";
import { Button, Text, View } from "@tarojs/components";
import { getMap, getTopic, getVisibleTopicSlugs, getKnowledgeTopicAssetId, type Locale } from "@yutou/kids-content";
import { GeneratedImage } from "../../components/shared/GeneratedImage";
import "./index.scss";

const locale: Locale = "zh-CN";
const map = getMap(locale, "miniprogram");
const visibleTopicSlugs = getVisibleTopicSlugs("miniprogram");
const featuredTopics = visibleTopicSlugs.map((slug) => getTopic(slug, locale)).filter(Boolean);

function openTopic(slug: string) {
  Taro.navigateTo({ url: `/pages/topic/index?slug=${slug}&locale=${locale}` });
}

export default function IndexPage() {
  return (
    <View className="mini-page">
      <View className="hero">
        <Text className="eyebrow">Yutou Verse</Text>
        <Text className="title">{map.homeHero.title}</Text>
        <Text className="intro">{map.homeHero.childIntro}</Text>
      </View>

      <View className="topic-list">
        {featuredTopics.map((topic) =>
          topic ? (
            <View className="topic-card" key={topic.slug} onClick={() => openTopic(topic.slug)}>
              <GeneratedImage assetId={getKnowledgeTopicAssetId({ slug: topic.slug, title: topic.title, status: "building", cardDescription: "" })} alt={topic.title} />
              <View className="topic-copy">
                <Text className="topic-title">{topic.title}</Text>
                <Text className="topic-question">{topic.coreQuestion}</Text>
              </View>
            </View>
          ) : null,
        )}
      </View>

      <Button className="about-button" onClick={() => Taro.navigateTo({ url: "/pages/about/index" })}>
        家长说明与隐私政策
      </Button>
    </View>
  );
}
