import { useState } from "react";
import { characters } from "../data/characters";
import { locations } from "../data/locations";
import { IconFor } from "./IconFor";

export function MapExplorer() {
  const [selectedLocationId, setSelectedLocationId] = useState(locations[0].id);
  const selected = locations.find((location) => location.id === selectedLocationId) ?? locations[0];
  const recommended = selected.recommendedCharacterIds
    .map((id) => characters.find((character) => character.id === id))
    .filter(Boolean);

  return (
    <section className="map-page">
      <div className="main-panel">
        <p className="section-kicker">冒险湾地图</p>
        <h2>不同地点，需要不同能力</h2>
        <div className="explorer-map" aria-label="可点击地点地图">
          {locations.map((location, index) => (
            <button
              className={location.id === selected.id ? `map-pin pin-${index + 1} active` : `map-pin pin-${index + 1}`}
              key={location.id}
              type="button"
              onClick={() => setSelectedLocationId(location.id)}
            >
              <IconFor name={location.icon} />
              <span>{location.name}</span>
            </button>
          ))}
          <div className="map-route" aria-hidden="true" />
        </div>
      </div>

      <aside className="detail-panel map-detail">
        <IconFor name={selected.icon} size={52} />
        <p className="section-kicker">地点提示</p>
        <h2>{selected.name}</h2>
        <p className="big-text">{selected.description}</p>
        <div className="mini-list">
          <strong>这里可能发生</strong>
          {selected.commonProblems.map((problem) => (
            <span key={problem}>{problem}</span>
          ))}
        </div>
        <div className="mini-list">
          <strong>推荐队员</strong>
          {recommended.map((character) => (
            <span key={character!.id}>
              {character!.nameZh}：{character!.childIntro}
            </span>
          ))}
        </div>
      </aside>
    </section>
  );
}
