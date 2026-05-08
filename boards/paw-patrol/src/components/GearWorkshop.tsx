import { useState } from "react";
import { characters } from "../data/characters";
import { gearItems } from "../data/gear";
import { IconFor } from "./IconFor";

export function GearWorkshop() {
  const [selectedGearId, setSelectedGearId] = useState(gearItems[0].id);
  const selected = gearItems.find((gear) => gear.id === selectedGearId) ?? gearItems[0];
  const owner = characters.find((character) => character.id === selected.characterId);

  return (
    <section className="gear-page">
      <div className="main-panel">
        <p className="section-kicker">装备工坊</p>
        <h2>车辆和工具用来解决问题</h2>
        <div className="gear-grid">
          {gearItems.map((gear) => {
            const character = characters.find((item) => item.id === gear.characterId);
            return (
              <button
                className={gear.id === selected.id ? `gear-card ${character?.colorHint ?? "blue"} selected` : `gear-card ${character?.colorHint ?? "blue"}`}
                key={gear.id}
                type="button"
                onClick={() => setSelectedGearId(gear.id)}
              >
                <IconFor name={gear.type === "vehicle" ? "Rocket" : "BadgeQuestionMark"} />
                <strong>{gear.name}</strong>
                <span>{character?.nameZh}</span>
              </button>
            );
          })}
        </div>
      </div>

      <aside className={`detail-panel gear-detail ${owner?.colorHint ?? "blue"}`}>
        <div className="detail-avatar">
          <IconFor name={selected.type === "vehicle" ? "Rocket" : "BadgeQuestionMark"} size={44} />
        </div>
        <p className="section-kicker">{owner?.nameZh} 的装备</p>
        <h2>{selected.name}</h2>
        <div className="mini-list numbered">
          <strong>3 个功能点</strong>
          {selected.functions.map((item, index) => (
            <span key={item}>
              {index + 1}. {item}
            </span>
          ))}
        </div>
        <div className="mini-list">
          <strong>适合问题</strong>
          {selected.bestForProblemTypes.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </aside>
    </section>
  );
}
