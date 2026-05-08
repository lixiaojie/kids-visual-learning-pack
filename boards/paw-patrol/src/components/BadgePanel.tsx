import { badges } from "../data/badges";
import { characters } from "../data/characters";
import { IconFor } from "./IconFor";

type BadgePanelProps = {
  unlockedBadges: string[];
  compact?: boolean;
};

export function BadgePanel({ unlockedBadges, compact = false }: BadgePanelProps) {
  return (
    <section className={compact ? "badge-panel compact" : "badge-panel"} aria-label="能力徽章">
      <div className="panel-title-row">
        <div>
          <p className="section-kicker">能力徽章</p>
          <h2>{compact ? "点亮进度" : "收集你的救援徽章"}</h2>
        </div>
        <strong className="progress-pill">
          {unlockedBadges.length}/{badges.length}
        </strong>
      </div>
      <div className="badge-grid">
        {badges.map((badge) => {
          const unlocked = unlockedBadges.includes(badge.id);
          const related = badge.relatedCharacterIds
            .map((id) => characters.find((character) => character.id === id)?.nameZh)
            .filter(Boolean)
            .join("、");

          return (
            <article className={unlocked ? "badge-card unlocked" : "badge-card"} key={badge.id}>
              <span className="badge-icon">
                <IconFor name={badge.icon} />
              </span>
              <div>
                <h3>{badge.name}</h3>
                <p>{badge.childText}</p>
                {!compact && <small>代表：{related || "全员"}</small>}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
