import type { Locale, VisualEvidenceState, VisualSlot } from "@yutou/kids-content";
import { GeneratedImage } from "../shared/GeneratedImage";

type Props = {
  slot?: VisualSlot | null;
  evidence?: VisualEvidenceState | null;
  className?: string;
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

export function TopicVisual({ slot, evidence, className = "", fallbackAlt, locale = "zh-CN" }: Props) {
  if (!slot) return null;
  const labels = statusLabels[locale];

  return (
    <figure className={`topic-visual ${evidence ? `evidence-${evidence.status}` : ""} ${className}`.trim()} data-evidence-source={evidence?.source}>
      <GeneratedImage
        alt={slot.alt ?? slot.caption ?? fallbackAlt ?? ""}
        assetId={slot.assetId}
        className="topic-visual-image"
      />
      {slot.caption ? <figcaption>{slot.caption}</figcaption> : null}
      {evidence ? (
        <div className="evidence-panel" data-testid="evidence-panel">
          <div className="evidence-heading">
            <strong>{evidence.evidenceTitle}</strong>
            <span>{labels[evidence.status]}</span>
          </div>
          {evidence.observePrompt ? <p>{evidence.observePrompt}</p> : null}
          {evidence.selectedLabels?.length ? (
            <p>
              {locale === "zh-CN" ? "已选：" : "Selected: "}
              {evidence.selectedLabels.join(locale === "zh-CN" ? "、" : ", ")}
            </p>
          ) : null}
          {evidence.markerChips?.length ? (
            <div className="evidence-chips">
              {evidence.markerChips.map((chip) => (
                <span className={`evidence-chip ${chip.emphasis ?? "supporting"}`} key={`${chip.label}-${chip.meaning}`} title={chip.meaning}>
                  {chip.label}
                  <small>{chip.meaning}</small>
                </span>
              ))}
            </div>
          ) : null}
          <p>{evidence.evidenceCopy}</p>
        </div>
      ) : null}
    </figure>
  );
}
