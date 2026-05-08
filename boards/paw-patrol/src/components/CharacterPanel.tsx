import { badges } from "../data/badges";
import { characters } from "../data/characters";
import type { Character } from "../types";
import { IconFor } from "./IconFor";

type CharacterPanelProps = {
  selectedCharacterId: string;
  onSelectCharacter: (id: string) => void;
};

export function CharacterPanel({ selectedCharacterId, onSelectCharacter }: CharacterPanelProps) {
  const selected = characters.find((character) => character.id === selectedCharacterId) ?? characters[0];

  return (
    <section className="page-grid characters-page">
      <div className="main-panel">
        <p className="section-kicker">角色分工页</p>
        <h2>每只小狗负责不同问题</h2>
        <div className="character-grid">
          {characters.map((character) => (
            <CharacterCard
              character={character}
              isSelected={character.id === selected.id}
              key={character.id}
              onSelect={() => onSelectCharacter(character.id)}
            />
          ))}
        </div>
      </div>
      <CharacterDetail character={selected} />
    </section>
  );
}

function CharacterCard({
  character,
  isSelected,
  onSelect,
}: {
  character: Character;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const badge = badges.find((item) => item.id === character.badgeId);

  return (
    <button
      className={isSelected ? `character-card ${character.colorHint} selected` : `character-card ${character.colorHint}`}
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
    >
      <span className="pup-avatar" aria-hidden="true">
        <IconFor name="PawPrint" />
      </span>
      <strong>
        {character.nameZh}
        <small>{character.nameEn}</small>
      </strong>
      <span>{character.shortRole}</span>
      <em>{badge?.name}</em>
    </button>
  );
}

function CharacterDetail({ character }: { character: Character }) {
  const badge = badges.find((item) => item.id === character.badgeId);

  return (
    <aside className={`detail-panel ${character.colorHint}`} aria-label={`${character.nameZh}详情`}>
      <div className="detail-avatar">
        <IconFor name="PawPrint" size={44} />
      </div>
      <p className="section-kicker">我是 {character.nameZh}</p>
      <h2>
        {character.nameZh} <span>{character.nameEn}</span>
      </h2>
      <p className="big-text">{character.childIntro}</p>
      <dl className="info-list">
        <div>
          <dt>职业</dt>
          <dd>{character.role}</dd>
        </div>
        <div>
          <dt>车辆</dt>
          <dd>{character.vehicle}</dd>
        </div>
        <div>
          <dt>工具</dt>
          <dd>{character.tools.join("、")}</dd>
        </div>
        <div>
          <dt>适合</dt>
          <dd>{character.bestFor.join("、")}</dd>
        </div>
      </dl>
      <div className="tip-box">
        <strong>{badge?.name}</strong>
        <span>{character.parentNote}</span>
      </div>
    </aside>
  );
}
