import { Dna } from "lucide-react";
import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  objects: Topic["representativeObjects"];
  activeObjectId: string;
  onSelectObject: (id: string) => void;
  locale: string;
};

export function RepresentativeObjects({ objects, activeObjectId, onSelectObject, locale }: Props) {
  const activeObject = objects.find((item) => item.id === activeObjectId) ?? objects[0];

  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "对象卡" : "Object cards"} />
      <div className="object-grid">
        {objects.map((object) => (
          <button
            className={activeObjectId === object.id ? "object-card active" : "object-card"}
            key={object.id}
            type="button"
            onClick={() => onSelectObject(object.id)}
          >
            <Dna size={20} />
            <strong>{object.name}</strong>
            <small>{object.visualHint}</small>
          </button>
        ))}
      </div>
      {activeObject && (
        <div className="object-detail">
          <strong>{activeObject.name}</strong>
          <span>{activeObject.childExplanation}</span>
          <small>{activeObject.commonMisread}</small>
        </div>
      )}
    </article>
  );
}
