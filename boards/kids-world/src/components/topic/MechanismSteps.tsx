import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  mechanism: Topic["mechanism"];
  secondary?: Topic["secondaryMechanism"];
  locale: string;
};

function StepRow({ steps }: { steps: Topic["mechanism"]["steps"] }) {
  return (
    <div className="step-row">
      {steps.map((step, index) => (
        <div className="step-card" key={step.id}>
          <span>{index + 1}</span>
          <strong>{step.shortTitle}</strong>
          <small>{step.childExplanation}</small>
        </div>
      ))}
    </div>
  );
}

export function MechanismSteps({ mechanism, secondary, locale }: Props) {
  return (
    <>
      <article className="panel wide">
        <SectionHeader title={locale === "zh-CN" ? "机制步骤" : "How it works"} />
        <StepRow steps={mechanism.steps} />
      </article>
      {secondary && (
        <article className="panel wide">
          <SectionHeader title={secondary.title} />
          <StepRow steps={secondary.steps} />
        </article>
      )}
    </>
  );
}
