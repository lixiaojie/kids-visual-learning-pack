import Taro from "@tarojs/taro";
import { useState } from "react";
import { Button, Text, View } from "@tarojs/components";
import { getKnowledgeTopicAssetId, getMap, getTopic, type Locale } from "@yutou/kids-content";
import { GeneratedImage } from "../../components/shared/GeneratedImage";
import "./index.scss";

const locale: Locale = "zh-CN";
const map = getMap(locale, "miniprogram");
const knowledgeWorlds = map.worlds.filter((world) => world.type === "knowledgeWorld");
const featuredCard = knowledgeWorlds.flatMap((world) => world.topicCards).find((topic) => topic.slug === "cicada-life");
const featuredTopic = featuredCard?.slug ? getTopic(featuredCard.slug, locale) : undefined;
const defaultWorldId = knowledgeWorlds.find((world) => world.id === "life")?.id ?? knowledgeWorlds[0]?.id ?? "";

function openTopic(slug: string) {
  Taro.navigateTo({ url: `/pages/topic/index?slug=${slug}&locale=${locale}` });
}

export default function IndexPage() {
  const [selectedWorldId, setSelectedWorldId] = useState(defaultWorldId);
  const selectedWorld = knowledgeWorlds.find((world) => world.id === selectedWorldId) ?? knowledgeWorlds[0];

  return (
    <View className="mini-page">
      <View className="mini-nav">
        <Text className="mini-nav-item active">首页</Text>
        <Text className="mini-nav-item" onClick={() => Taro.pageScrollTo({ selector: "#worlds" })}>
          世界探索
        </Text>
        <Text className="mini-nav-item" onClick={() => Taro.navigateTo({ url: "/pages/about/index" })}>
          关于
        </Text>
      </View>

      <View className="hero">
        <Text className="eyebrow">Yutou Verse</Text>
        <Text className="title">{map.homeHero.title}</Text>
        <Text className="intro">{map.homeHero.childIntro}</Text>
      </View>

      {featuredCard?.slug && featuredTopic ? (
        <View className="featured-card" onClick={() => openTopic(featuredCard.slug as string)}>
          <GeneratedImage assetId={getKnowledgeTopicAssetId(featuredCard)} alt={featuredTopic.title} />
          <View className="featured-copy">
            <Text className="section-eyebrow">本周新发现</Text>
            <Text className="featured-title">{featuredTopic.title}</Text>
            <Text className="featured-question">{featuredTopic.coreQuestion}</Text>
          </View>
        </View>
      ) : null}

      <View className="world-section" id="worlds">
        <Text className="section-eyebrow">世界探索</Text>
        <Text className="section-title">六大知识世界</Text>
        <View className="world-list">
          {knowledgeWorlds.map((world) => (
            <View
              className={selectedWorldId === world.id ? "world-card world-card-active" : "world-card"}
              key={world.id}
              onClick={() => setSelectedWorldId(world.id)}
            >
              <Text className="world-badge">{world.entryCard.badge}</Text>
              <Text className="world-title">{world.name}</Text>
              <Text className="world-intro">{world.childOneLiner}</Text>
            </View>
          ))}
        </View>
      </View>

      {selectedWorld ? (
        <View className="topic-panel">
          <Text className="section-eyebrow">{selectedWorld.entryCard.badge}</Text>
          <Text className="section-title">{selectedWorld.name}</Text>
          <Text className="world-note">{selectedWorld.parentNote}</Text>
          {selectedWorld.topicCards.length > 0 ? (
            <View className="topic-list">
              {selectedWorld.topicCards.map((topic) =>
                topic.slug ? (
                  <View className="topic-card" key={topic.slug} onClick={() => openTopic(topic.slug as string)}>
                    <GeneratedImage assetId={getKnowledgeTopicAssetId(topic)} alt={topic.title} />
                    <View className="topic-copy">
                      <Text className="topic-title">{topic.title}</Text>
                      <Text className="topic-question">{topic.cardDescription}</Text>
                    </View>
                  </View>
                ) : null,
              )}
            </View>
          ) : (
            <Text className="empty-note">这个世界的看板正在整理中。</Text>
          )}
        </View>
      ) : null}

      <Button className="about-button" onClick={() => Taro.navigateTo({ url: "/pages/about/index" })}>
        家长说明与隐私政策
      </Button>
    </View>
  );
}
