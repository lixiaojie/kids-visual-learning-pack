import { useMemo, useState } from "react";
import { useRouter, useShareAppMessage, useShareTimeline } from "@tarojs/taro";
import { Navigator, Text, View } from "@tarojs/components";
import {
  getMap,
  getKnowledgeTopicAssetId,
  getTopic,
  getTopicLearningFlow,
  getVisualSlotForTarget,
  resolveVisualEvidence,
  type Locale,
  type Topic,
} from "@yutou/kids-content";
import { GeneratedImage } from "../../components/shared/GeneratedImage";
import { ClickTaskCard } from "../../components/topic/ClickTaskCard";
import { ComparePairCard } from "../../components/topic/ComparePairCard";
import { InfoList } from "../../components/topic/InfoList";
import { LearningFlowRail } from "../../components/topic/LearningFlowRail";
import { TopicSummary } from "../../components/topic/TopicSummary";
import { TopicVisual } from "../../components/topic/TopicVisual";
import "./index.scss";

const supportedLocales: Locale[] = ["zh-CN", "en-US"];

function normalizeLocale(locale: string | undefined): Locale {
  return supportedLocales.includes(locale as Locale) ? (locale as Locale) : "zh-CN";
}

function getHeroAssetId(topic: Topic) {
  return getVisualSlotForTarget(topic, "hero")?.assetId ?? getKnowledgeTopicAssetId({ slug: topic.slug, title: topic.title, status: "building", cardDescription: "" });
}

export default function TopicPage() {
  const router = useRouter();
  const locale = normalizeLocale(router.params.locale);
  const slug = router.params.slug || "dinosaurs";
  const topic = useMemo(() => getTopic(slug, locale), [slug, locale]);
  const map = useMemo(() => getMap(locale, "miniprogram"), [locale]);
  const flowStages = useMemo(() => (topic ? getTopicLearningFlow(topic, locale) : []), [topic, locale]);
  const [activeStageId, setActiveStageId] = useState(flowStages[0]?.id ?? "");
  const [activeGroupId, setActiveGroupId] = useState("");
  const [activeObjectId, setActiveObjectId] = useState("");
  const [activeMechanismStepId, setActiveMechanismStepId] = useState("");
  const [activeSecondaryStepId, setActiveSecondaryStepId] = useState("");
  const [activeComparePairId, setActiveComparePairId] = useState("");
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

  const selectedGroupId = activeGroupId || topic.classificationGroups[0]?.id || "";
  const selectedObjectId = activeObjectId || topic.representativeObjects[0]?.id || "";
  const selectedMechanismStepId = activeMechanismStepId || topic.mechanism.steps[0]?.id || "";
  const selectedSecondaryStepId = activeSecondaryStepId || topic.secondaryMechanism?.steps[0]?.id || "";
  const selectedComparePairId = activeComparePairId || topic.comparePairs[0]?.id || "";
  const groupEvidence = selectedGroupId
    ? resolveVisualEvidence(topic, { source: `classificationGroups.${selectedGroupId}`, result: "selected", locale })
    : null;
  const objectEvidence = selectedObjectId
    ? resolveVisualEvidence(topic, { source: `representativeObjects.${selectedObjectId}`, result: "selected", locale })
    : null;
  const mechanismEvidence = selectedMechanismStepId
    ? resolveVisualEvidence(topic, { source: `mechanism.steps.${selectedMechanismStepId}`, result: "selected", locale })
    : null;
  const secondaryEvidence = selectedSecondaryStepId
    ? resolveVisualEvidence(topic, { source: `secondaryMechanism.steps.${selectedSecondaryStepId}`, result: "selected", locale })
    : null;
  const compareEvidence = selectedComparePairId
    ? resolveVisualEvidence(topic, { source: `comparePairs.${selectedComparePairId}`, result: "selected", locale })
    : null;
  const slotFromEvidence = (visualSlotId?: string) => topic.visualSlots?.find((slot) => slot.id === visualSlotId);

  return (
    <View className="topic-page">
      <View className="topic-hero" id="topic-hero">
        <Text className="topic-kicker">{topic.hero.kicker}</Text>
        <Text className="topic-title">{topic.hero.title}</Text>
        <Text className="topic-lead">{topic.hero.lead}</Text>
        <GeneratedImage assetId={getHeroAssetId(topic)} alt={topic.title} className="topic-image" />
      </View>

      <LearningFlowRail activeStageId={activeStageId} stages={flowStages} locale={locale} onSelectStage={setActiveStageId} />

      <View className="section" id="topic-observe">
        <Text className="section-title">{locale === "zh-CN" ? "先观察" : "Observe"}</Text>
        <Text className="section-body">{topic.hero.sceneExplanation}</Text>
      </View>

      <View id="topic-classification">
        <TopicVisual slot={slotFromEvidence(groupEvidence?.visualSlotId)} evidence={groupEvidence} fallbackAlt={locale === "zh-CN" ? "分类证据图" : "Classification evidence"} locale={locale} />
        <InfoList
          title={locale === "zh-CN" ? "先分成几类" : "Classification groups"}
          activeId={selectedGroupId}
          evidencePrefix="classificationGroups"
          onSelect={(id) => {
            setActiveGroupId(id);
            const firstObject = topic.representativeObjects.find((object) => object.groupId === id);
            if (firstObject) setActiveObjectId(firstObject.id);
          }}
          items={topic.classificationGroups.map((group) => ({
            id: group.id,
            title: group.name,
            body: group.parentNote ? `${group.childExplanation}\n${group.parentNote}` : group.childExplanation,
          }))}
        />
      </View>

      <View id="topic-objects">
        <TopicVisual slot={slotFromEvidence(objectEvidence?.visualSlotId) ?? getVisualSlotForTarget(topic, "representativeObjects")} evidence={objectEvidence} fallbackAlt={locale === "zh-CN" ? "代表对象观察图" : "Representative object visual"} locale={locale} />
        <InfoList
          title={locale === "zh-CN" ? "认识几个代表对象" : "Representative objects"}
          activeId={selectedObjectId}
          evidencePrefix="representativeObjects"
          onSelect={setActiveObjectId}
          items={topic.representativeObjects.map((item) => ({
            id: item.id,
            title: item.name,
            body: item.childExplanation,
          }))}
        />
      </View>

      <View className="section" id="topic-mechanism">
        <Text className="section-title">{topic.mechanism.title ?? (locale === "zh-CN" ? "它怎么发生" : "How it works")}</Text>
        <TopicVisual slot={slotFromEvidence(mechanismEvidence?.visualSlotId) ?? getVisualSlotForTarget(topic, "mechanism")} evidence={mechanismEvidence} fallbackAlt={topic.mechanism.title} locale={locale} />
        {topic.mechanism.steps.map((step) => (
          <View className={`step ${selectedMechanismStepId === step.id ? "active" : ""}`} key={step.id} onClick={() => setActiveMechanismStepId(step.id)} data-evidence-source={`mechanism.steps.${step.id}`}>
            <Text className="step-title">{step.shortTitle}</Text>
            <Text className="section-body">{step.childExplanation}</Text>
          </View>
        ))}
      </View>

      {topic.secondaryMechanism && (
        <View className="section" id="topic-secondary-mechanism">
          <Text className="section-title">{topic.secondaryMechanism.title}</Text>
          <TopicVisual slot={slotFromEvidence(secondaryEvidence?.visualSlotId) ?? getVisualSlotForTarget(topic, "secondaryMechanism")} evidence={secondaryEvidence} fallbackAlt={topic.secondaryMechanism.title} locale={locale} />
          {topic.secondaryMechanism.steps.map((step) => (
            <View className={`step ${selectedSecondaryStepId === step.id ? "active" : ""}`} key={step.id} onClick={() => setActiveSecondaryStepId(step.id)} data-evidence-source={`secondaryMechanism.steps.${step.id}`}>
              <Text className="step-title">{step.shortTitle}</Text>
              <Text className="section-body">{step.childExplanation}</Text>
            </View>
          ))}
        </View>
      )}

      <View className="section" id="topic-compare">
        <Text className="section-title">{locale === "zh-CN" ? "比一比" : "Compare"}</Text>
        <TopicVisual slot={slotFromEvidence(compareEvidence?.visualSlotId) ?? topic.visualSlots?.find((slot) => slot.target === "comparePairs")} evidence={compareEvidence} fallbackAlt={locale === "zh-CN" ? "对比图" : "Compare visual"} locale={locale} />
        <View className="compare-stack">
          {topic.comparePairs.map((pair) => (
            <ComparePairCard
              pair={pair}
              key={pair.id}
              visualSlot={topic.visualSlots?.find((slot) => slot.target === `comparePairs.${pair.id}`)}
              active={selectedComparePairId === pair.id}
              evidence={selectedComparePairId === pair.id ? compareEvidence : null}
              onSelect={() => setActiveComparePairId(pair.id)}
              locale={locale}
            />
          ))}
        </View>
      </View>

      <View className="section" id="topic-tasks">
        <Text className="section-title">{locale === "zh-CN" ? "点击任务" : "Tap tasks"}</Text>
        <TopicVisual slot={topic.visualSlots?.find((slot) => slot.target === "clickTasks")} fallbackAlt={locale === "zh-CN" ? "任务图" : "Task visual"} locale={locale} />
        <View className="task-stack">
          {topic.clickTasks.map((task) => (
            <ClickTaskCard task={task} topic={topic} locale={locale} key={task.id} visualSlot={topic.visualSlots?.find((slot) => slot.target === `clickTasks.${task.id}`)} />
          ))}
        </View>
      </View>

      <View id="topic-speak">
        <TopicSummary topic={topic} locale={locale} />
      </View>

      <View id="topic-parent">
        <TopicVisual slot={getVisualSlotForTarget(topic, "parentTips")} fallbackAlt={locale === "zh-CN" ? "家长提示图" : "Parent guide visual"} locale={locale} />
        <InfoList
          title={locale === "zh-CN" ? "家长可以这样陪聊" : "Parent prompts"}
          items={topic.parentTips.map((tip, index) => ({
            id: `tip-${index}`,
            title: `${locale === "zh-CN" ? "提示" : "Prompt"} ${index + 1}`,
            body: tip,
          }))}
        />
      </View>

      {relatedTopicCards.length > 0 && (
        <View className="section" id="topic-related">
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
