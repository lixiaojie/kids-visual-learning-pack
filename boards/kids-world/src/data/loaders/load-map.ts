import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import explorationMapBase from "../exploration-map.json";
import explorationMapEn from "../locales/en-US/exploration-map.json";
import topicRegistry from "../topic-registry.json";
import channelPolicy from "../../../../../channel-policy.json";
import { deepMerge } from "./locale-merge";

type ChannelName = keyof typeof channelPolicy;
type ChannelPolicy = (typeof channelPolicy)[ChannelName];

const defaultChannel: ChannelName = "web-production";
const renderReadySlugs = new Set(
  topicRegistry.topics
    .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
    .map((topic) => topic.slug),
);

function getChannel(): ChannelName {
  const env = (import.meta as unknown as { env?: { VITE_CHANNEL?: string } }).env;
  const channel = env?.VITE_CHANNEL;
  return channel && channel in channelPolicy ? (channel as ChannelName) : defaultChannel;
}

function isTopicVisible(slug: string | undefined, policy: ChannelPolicy) {
  if (policy.visibleTopics === "all") return true;
  if (!slug) return false;
  if (policy.visibleTopics === "all-render-ready") return renderReadySlugs.has(slug);
  return policy.visibleTopics.includes(slug);
}

function isBoardHrefVisible(href: string | undefined, policy: ChannelPolicy) {
  if (!href) return true;
  return !policy.hiddenBoards.some((board) => href.includes(`boards/${board}/`));
}

function applyChannelPolicy(map: ExplorationMap, policy: ChannelPolicy): ExplorationMap {
  const worlds = map.worlds
    .map((world) => ({
      ...world,
      topicCards: world.topicCards.filter(
        (topic) => isTopicVisible(topic.slug, policy) && isBoardHrefVisible(topic.href, policy),
      ),
    }))
    .filter((world) => world.type === "knowledgeWorld" || world.topicCards.length > 0);
  const visibleWorldIds = new Set(worlds.map((world) => world.id));

  return {
    ...map,
    worlds,
    sections: map.sections
      .map((section) => ({
        ...section,
        worlds: section.worlds.filter((worldId) => visibleWorldIds.has(worldId)),
      }))
      .filter((section) => section.worlds.length > 0),
  };
}

export function getMap(locale: Locale): ExplorationMap {
  const base = explorationMapBase as unknown as ExplorationMap;
  const localizedMap = locale === "en-US" ? deepMerge(base, explorationMapEn) : base;
  return applyChannelPolicy(localizedMap, channelPolicy[getChannel()]);
}
