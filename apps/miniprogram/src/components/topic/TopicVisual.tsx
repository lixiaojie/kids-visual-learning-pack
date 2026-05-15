import { Text, View } from "@tarojs/components";
import type { Locale, VisualEvidenceState, VisualFocus, VisualSlot } from "@yutou/kids-content";
import { GeneratedImage } from "../shared/GeneratedImage";
import "./TopicVisual.scss";

type Props = {
  slot?: VisualSlot | null;
  evidence?: VisualEvidenceState | null;
  fallbackAlt?: string;
  locale?: Locale;
};

const statusLabels: Record<Locale, Record<VisualEvidenceState["status"], string>> = {
  "zh-CN": {
    idle: "未开始",
    selected: "已选择",
    correct: "答对",
    wrong: "再观察",
    partial: "进行中",
    complete: "完成",
  },
  "en-US": {
    idle: "Start",
    selected: "Selected",
    correct: "Correct",
    wrong: "Try again",
    partial: "In progress",
    complete: "Complete",
  },
};

function FocusOverlay({ focus }: { focus?: VisualFocus }) {
  if (!focus?.regions?.length) return null;
  const activeRegionIds = new Set(focus.activeRegionIds ?? []);

  return (
    <View className={`visual-focus-overlay focus-${focus.mode}`}>
      {focus.regions.map((region) => {
        const isActive = activeRegionIds.size === 0 || activeRegionIds.has(region.id);
        return (
          <View
            className={`visual-focus-region ${isActive ? "active" : "inactive"} ${region.emphasis ?? "primary"}`}
            key={region.id}
            style={{
              left: `${region.x * 100}%`,
              top: `${region.y * 100}%`,
              width: `${region.width * 100}%`,
              height: `${region.height * 100}%`,
            }}
          >
            {isActive && region.label ? <Text className="visual-focus-label">{region.label}</Text> : null}
          </View>
        );
      })}
    </View>
  );
}

export function TopicVisual({ slot, evidence, fallbackAlt, locale = "zh-CN" }: Props) {
  if (!slot) return null;
  const labels = statusLabels[locale];

  return (
    <View className={`topic-visual ${evidence ? `evidence-${evidence.status}` : ""}`}>
      <View className="topic-visual-image-wrap">
        <GeneratedImage assetId={slot.assetId} alt={slot.alt ?? slot.caption ?? fallbackAlt} className="topic-visual-image" />
        <FocusOverlay focus={evidence?.focus} />
      </View>
      {slot.caption ? <Text className="topic-visual-caption">{slot.caption}</Text> : null}
      {evidence ? (
        <View className="evidence-panel">
          <View className="evidence-heading">
            <Text className="evidence-title">{evidence.evidenceTitle}</Text>
            <Text className="evidence-status">{labels[evidence.status]}</Text>
          </View>
          {evidence.observePrompt ? <Text className="evidence-copy">{evidence.observePrompt}</Text> : null}
          {evidence.selectedLabels?.length ? (
            <Text className="evidence-copy">
              {locale === "zh-CN" ? "已选：" : "Selected: "}
              {evidence.selectedLabels.join(locale === "zh-CN" ? "、" : ", ")}
            </Text>
          ) : null}
          {evidence.markerChips?.length ? (
            <View className="evidence-chips">
              {evidence.markerChips.map((chip) => (
                <Text className={`evidence-chip ${chip.emphasis ?? "supporting"}`} key={`${chip.label}-${chip.meaning}`}>
                  {chip.label}: {chip.meaning}
                </Text>
              ))}
            </View>
          ) : null}
          <Text className="evidence-copy">{evidence.evidenceCopy}</Text>
        </View>
      ) : null}
    </View>
  );
}
