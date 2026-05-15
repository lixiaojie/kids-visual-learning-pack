import { useState } from "react";
import { resolveVisualEvidence } from "@yutou/kids-content";
import type { Topic, VisualSlot } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";
import { TopicVisual } from "./TopicVisual";

type Props = {
  topic: Topic;
  mechanism: Topic["mechanism"];
  secondary?: Topic["secondaryMechanism"];
  mechanismSlot?: VisualSlot | null;
  secondarySlot?: VisualSlot | null;
  locale: string;
};

function StepRow({
  steps,
  activeStepId,
  onSelectStep,
  sourcePrefix,
}: {
  steps: Topic["mechanism"]["steps"];
  activeStepId: string;
  onSelectStep: (id: string) => void;
  sourcePrefix: "mechanism.steps" | "secondaryMechanism.steps";
}) {
  return (
    <div className="step-row">
      {steps.map((step, index) => (
        <button
          className={activeStepId === step.id ? "step-card active" : "step-card"}
          key={step.id}
          type="button"
          data-evidence-source={`${sourcePrefix}.${step.id}`}
          onClick={() => onSelectStep(step.id)}
        >
          <span>{index + 1}</span>
          <strong>{step.shortTitle}</strong>
          <small>{step.childExplanation}</small>
        </button>
      ))}
    </div>
  );
}

export function MechanismSteps({ topic, mechanism, secondary, mechanismSlot, secondarySlot, locale }: Props) {
  const [activeMechanismStepId, setActiveMechanismStepId] = useState(mechanism.steps[0]?.id ?? "");
  const [activeSecondaryStepId, setActiveSecondaryStepId] = useState(secondary?.steps[0]?.id ?? "");
  const normalizedLocale = locale === "en-US" ? "en-US" : "zh-CN";
  const mechanismEvidence = activeMechanismStepId
    ? resolveVisualEvidence(topic, { source: `mechanism.steps.${activeMechanismStepId}`, result: "selected", locale: normalizedLocale })
    : null;
  const mechanismEvidenceSlot = mechanismEvidence ? topic.visualSlots?.find((slot) => slot.id === mechanismEvidence.visualSlotId) : mechanismSlot;
  const secondaryEvidence = activeSecondaryStepId
    ? resolveVisualEvidence(topic, { source: `secondaryMechanism.steps.${activeSecondaryStepId}`, result: "selected", locale: normalizedLocale })
    : null;
  const secondaryEvidenceSlot = secondaryEvidence ? topic.visualSlots?.find((slot) => slot.id === secondaryEvidence.visualSlotId) : secondarySlot;

  return (
    <>
      <article className="panel wide" id="topic-mechanism">
        <SectionHeader title={mechanism.title ?? (locale === "zh-CN" ? "机制步骤" : "How it works")} />
        <TopicVisual slot={mechanismEvidenceSlot ?? mechanismSlot} evidence={mechanismEvidence} fallbackAlt={mechanism.title ?? (locale === "zh-CN" ? "机制图" : "Process visual")} locale={normalizedLocale} />
        <StepRow steps={mechanism.steps} activeStepId={activeMechanismStepId} onSelectStep={setActiveMechanismStepId} sourcePrefix="mechanism.steps" />
      </article>
      {secondary && (
        <article className="panel wide" id="topic-secondary-mechanism">
          <SectionHeader title={secondary.title} />
          <TopicVisual slot={secondaryEvidenceSlot ?? secondarySlot} evidence={secondaryEvidence} fallbackAlt={secondary.title} locale={normalizedLocale} />
          <StepRow steps={secondary.steps} activeStepId={activeSecondaryStepId} onSelectStep={setActiveSecondaryStepId} sourcePrefix="secondaryMechanism.steps" />
        </article>
      )}
    </>
  );
}
