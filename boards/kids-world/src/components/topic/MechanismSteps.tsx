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
    <div className="step-row node-strip">
      {steps.map((step, index) => (
        <button
          className={activeStepId === step.id ? "step-card node-button active" : "step-card node-button"}
          key={step.id}
          type="button"
          data-evidence-source={`${sourcePrefix}.${step.id}`}
          onClick={() => onSelectStep(step.id)}
        >
          <span className="node-index">{index + 1}</span>
          <strong className="node-label">{step.shortTitle}</strong>
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
  const activeMechanismStep = mechanism.steps.find((step) => step.id === activeMechanismStepId) ?? mechanism.steps[0];
  const activeSecondaryStep = secondary?.steps.find((step) => step.id === activeSecondaryStepId) ?? secondary?.steps[0];
  const mechanismVisualSupport = activeMechanismStep
    ? {
        title: activeMechanismStep.shortTitle,
        body: activeMechanismStep.childExplanation,
        note: activeMechanismStep.parentNote,
      }
    : null;
  const secondaryVisualSupport = activeSecondaryStep
    ? {
        title: activeSecondaryStep.shortTitle,
        body: activeSecondaryStep.childExplanation,
        note: activeSecondaryStep.parentNote,
      }
    : null;

  return (
    <>
      <article className="panel wide interaction-panel" id="topic-mechanism">
        <SectionHeader title={mechanism.title ?? (locale === "zh-CN" ? "机制步骤" : "How it works")} />
        <div className="interaction-controls">
          <StepRow steps={mechanism.steps} activeStepId={activeMechanismStepId} onSelectStep={onSelectMechanismStep} sourcePrefix="mechanism.steps" />
        </div>
        <TopicVisual slot={mechanismSlot} evidence={mechanismEvidence} fallbackAlt={mechanism.title ?? (locale === "zh-CN" ? "机制图" : "Process visual")} locale={normalizedLocale} visualSupport={mechanismVisualSupport} />
      </article>
      {secondary && (
        <article className="panel wide interaction-panel" id="topic-secondary-mechanism">
          <SectionHeader title={secondary.title} />
          <div className="interaction-controls">
            <StepRow steps={secondary.steps} activeStepId={activeSecondaryStepId} onSelectStep={onSelectSecondaryStep} sourcePrefix="secondaryMechanism.steps" />
          </div>
          <TopicVisual slot={secondarySlot} evidence={secondaryEvidence} fallbackAlt={secondary.title} locale={normalizedLocale} visualSupport={secondaryVisualSupport} />
        </article>
      )}
    </>
  );
}
