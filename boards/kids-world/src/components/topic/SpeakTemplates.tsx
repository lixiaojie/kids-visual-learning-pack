import { SectionHeader } from "../shared/SectionHeader";

type Props = { templates: string[]; locale: string };

export function SpeakTemplates({ templates, locale }: Props) {
  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "讲一讲" : "Try explaining"} />
      <div className="speak-list">
        {templates.map((template) => (
          <span key={template}>{template}</span>
        ))}
      </div>
    </article>
  );
}
