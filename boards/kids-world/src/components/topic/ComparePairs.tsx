import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = { pairs: Topic["comparePairs"]; locale: string };

export function ComparePairs({ pairs, locale }: Props) {
  return (
    <article className="panel wide">
      <SectionHeader title={locale === "zh-CN" ? "容易混淆" : "Easy mix-ups"} />
      <div className="compare-grid">
        {pairs.map((pair) => (
          <div className="compare-card" key={pair.id}>
            <strong>{pair.title}</strong>
            <div>
              <span>{pair.a.name}</span>
              <small>{pair.a.points.join(" · ")}</small>
            </div>
            <div>
              <span>{pair.b.name}</span>
              <small>{pair.b.points.join(" · ")}</small>
            </div>
            <em>{pair.childConclusion}</em>
          </div>
        ))}
      </div>
    </article>
  );
}
