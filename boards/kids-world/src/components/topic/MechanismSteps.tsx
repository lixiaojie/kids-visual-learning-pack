import type { Topic, VisualEvidenceState, VisualSlot } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";
import { TopicVisual } from "./TopicVisual";

type Props = {
  topic: Topic;
  mechanism: Topic["mechanism"];
  secondary?: Topic["secondaryMechanism"];
  activeMechanismStepId: string;
  activeSecondaryStepId: string;
  onSelectMechanismStep: (id: string) => void;
  onSelectSecondaryStep: (id: string) => void;
  mechanismEvidence?: VisualEvidenceState | null;
  secondaryEvidence?: VisualEvidenceState | null;
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

export function MechanismSteps({
  mechanism,
  secondary,
  activeMechanismStepId,
  activeSecondaryStepId,
  onSelectMechanismStep,
  onSelectSecondaryStep,
  mechanismEvidence,
  secondaryEvidence,
  mechanismSlot,
  secondarySlot,
  locale,
}: Props) {
  const normalizedLocale = locale === "en-US" ? "en-US" : "zh-CN";

  return (
    <>
      <article className="panel wide" id="topic-mechanism">
        <SectionHeader title={mechanism.title ?? (locale === "zh-CN" ? "机制步骤" : "How it works")} />
        <TopicVisual slot={mechanismSlot} evidence={mechanismEvidence} fallbackAlt={mechanism.title ?? (locale === "zh-CN" ? "机制图" : "Process visual")} locale={normalizedLocale} />
        <StepRow steps={mechanism.steps} activeStepId={activeMechanismStepId} onSelectStep={onSelectMechanismStep} sourcePrefix="mechanism.steps" />
      </article>
      {secondary && (
        <article className="panel wide" id="topic-secondary-mechanism">
          <SectionHeader title={secondary.title} />
          <TopicVisual slot={secondarySlot} evidence={secondaryEvidence} fallbackAlt={secondary.title} locale={normalizedLocale} />
          <StepRow steps={secondary.steps} activeStepId={activeSecondaryStepId} onSelectStep={onSelectSecondaryStep} sourcePrefix="secondaryMechanism.steps" />
        </article>
      )}
    </>
  );
}
