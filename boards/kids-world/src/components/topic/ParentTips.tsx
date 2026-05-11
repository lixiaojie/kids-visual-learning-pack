import { SectionHeader } from "../shared/SectionHeader";

type Props = { tips: string[]; locale: string };

export function ParentTips({ tips, locale }: Props) {
  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "家长提示" : "Parent prompts"} />
      <ul className="parent-tips">
        {tips.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </article>
  );
}
