import { badges } from "../data/badges";
import { characters } from "../data/characters";
import { locations } from "../data/locations";
import { missions } from "../data/missions";
import type { TabKey } from "../types";
import { BadgePanel } from "./BadgePanel";
import { IconFor } from "./IconFor";

type HomeDashboardProps = {
  unlockedBadges: string[];
  onChangeTab: (tab: TabKey) => void;
  onSelectCharacter: (id: string) => void;
  onOpenGuide: () => void;
};

export function HomeDashboard({ unlockedBadges, onChangeTab, onSelectCharacter, onOpenGuide }: HomeDashboardProps) {
  const todayMission = missions[0];
  const location = locations.find((item) => item.id === todayMission.locationId);

  return (
    <section className="home-grid">
      <article className="hero-panel">
        <div className="hero-copy">
          <p className="section-kicker">汪汪队任务指挥中心</p>
          <h1>今天你来当小队长！</h1>
          <p>观察问题，选择队员，一起完成救援。</p>
          <div className="hero-actions">
            <button className="primary-button" type="button" onClick={() => onChangeTab("mission")}>
              <IconFor name="Rocket" />
              开始任务
            </button>
            <button className="secondary-button" type="button" onClick={() => onChangeTab("characters")}>
              认识队员
            </button>
            <button className="secondary-button" type="button" onClick={() => onChangeTab("flow")}>
              任务流程
            </button>
          </div>
        </div>
        <div className="map-board" aria-label="冒险湾任务地图">
          {locations.map((place, index) => (
            <button className={`map-pin pin-${index + 1}`} key={place.id} type="button" title={place.description}>
              <IconFor name={place.icon} />
              <span>{place.name}</span>
            </button>
          ))}
          <div className="map-route" aria-hidden="true" />
        </div>
      </article>

      <aside className="mission-preview">
        <p className="section-kicker">今日任务</p>
        <h2>{todayMission.title}</h2>
        <p>{todayMission.description}</p>
        <div className="mission-tags">
          <span>{location?.name}</span>
          <span>{todayMission.problemType}</span>
        </div>
        <button className="primary-button full" type="button" onClick={() => onChangeTab("mission")}>
          出动看看
        </button>
      </aside>

      <section className="quick-characters" aria-label="角色快捷入口">
        <div className="panel-title-row">
          <div>
            <p className="section-kicker">角色入口</p>
            <h2>选一个队员</h2>
          </div>
          <button className="text-button" type="button" onClick={() => onChangeTab("characters")}>
            全部
          </button>
        </div>
        <div className="quick-grid">
          {characters.slice(0, 6).map((character) => (
            <button
              className={`quick-pup ${character.colorHint}`}
              key={character.id}
              type="button"
              onClick={() => {
                onSelectCharacter(character.id);
                onChangeTab("characters");
              }}
            >
              <IconFor name="PawPrint" />
              <span>{character.nameZh}</span>
            </button>
          ))}
        </div>
      </section>

      <BadgePanel compact unlockedBadges={unlockedBadges} />

      <section className="parent-strip">
        <div>
          <p className="section-kicker">亲子共学</p>
          <h2>完成任务后说一说</h2>
          <p>谁遇到困难？在哪里？谁去帮忙？用了什么工具？最后怎么解决？</p>
        </div>
        <button className="secondary-button" type="button" onClick={onOpenGuide}>
          家长说明
        </button>
      </section>

      <section className="badge-meaning-strip" aria-label="徽章含义示例">
        {badges.slice(0, 4).map((badge) => (
          <article key={badge.id}>
            <IconFor name={badge.icon} />
            <strong>{badge.name}</strong>
            <span>{badge.meaning}</span>
          </article>
        ))}
      </section>
    </section>
  );
}
