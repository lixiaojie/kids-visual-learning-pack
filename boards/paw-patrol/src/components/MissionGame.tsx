import { badges } from "../data/badges";
import { characters } from "../data/characters";
import { locations } from "../data/locations";
import { missions } from "../data/missions";
import { IconFor } from "./IconFor";

type MissionResult = "best" | "helpful" | "try-again" | null;

type MissionGameProps = {
  currentMissionId: string;
  selectedCharacterId: string | null;
  result: MissionResult;
  onSelectCharacter: (id: string) => void;
  onNextMission: () => void;
};

export function MissionGame({
  currentMissionId,
  selectedCharacterId,
  result,
  onSelectCharacter,
  onNextMission,
}: MissionGameProps) {
  const mission = missions.find((item) => item.id === currentMissionId) ?? missions[0];
  const location = locations.find((item) => item.id === mission.locationId);
  const bestCharacter = characters.find((item) => item.id === mission.bestCharacterId);
  const selectedCharacter = characters.find((item) => item.id === selectedCharacterId);
  const reward = badges.find((item) => item.id === mission.badgeRewardId);

  return (
    <section className="mission-layout">
      <article className="mission-card">
        <p className="section-kicker">今日任务小游戏</p>
        <h2>{mission.title}</h2>
        <p className="big-text">{mission.description}</p>
        <div className="mission-tags">
          <span>{location?.name}</span>
          <span>{mission.problemType}</span>
        </div>
        <div className="mission-scene" aria-hidden="true">
          <span className="signal-ring" />
          <IconFor name={location?.icon ?? "MapPinned"} size={72} />
          <strong>任务信号</strong>
        </div>
      </article>

      <section className="choice-panel" aria-label="选择队员">
        <div className="panel-title-row">
          <div>
            <p className="section-kicker">选择队员</p>
            <h2>谁最适合？</h2>
          </div>
          <button className="secondary-button" type="button" onClick={onNextMission}>
            换任务
          </button>
        </div>
        <div className="mission-choices">
          {characters.slice(0, 6).map((character) => (
            <button
              className={
                character.id === selectedCharacterId
                  ? `choice-card ${character.colorHint} selected`
                  : `choice-card ${character.colorHint}`
              }
              key={character.id}
              type="button"
              onClick={() => onSelectCharacter(character.id)}
            >
              <IconFor name="PawPrint" />
              <strong>{character.nameZh}</strong>
              <span>{character.vehicle}</span>
            </button>
          ))}
        </div>

        <MissionFeedback
          result={result}
          rewardName={reward?.name ?? "能力徽章"}
          selectedName={selectedCharacter?.nameZh}
          bestName={bestCharacter?.nameZh ?? "合适队员"}
          reason={mission.reason}
          hint={mission.wrongChoiceHint}
        />
      </section>
    </section>
  );
}

function MissionFeedback({
  result,
  rewardName,
  selectedName,
  bestName,
  reason,
  hint,
}: {
  result: MissionResult;
  rewardName: string;
  selectedName?: string;
  bestName: string;
  reason: string;
  hint: string;
}) {
  if (!result) {
    return (
      <article className="feedback-card idle">
        <IconFor name="Megaphone" />
        <div>
          <strong>听清任务，再选队员。</strong>
          <p>想一想：这次需要车辆、工具，还是观察能力？</p>
        </div>
      </article>
    );
  }

  if (result === "best") {
    return (
      <article className="feedback-card best">
        <IconFor name="Trophy" />
        <div>
          <strong>太棒了！{selectedName} 很适合。</strong>
          <p>{reason}</p>
          <span>你获得了：{rewardName}</span>
        </div>
      </article>
    );
  }

  if (result === "helpful") {
    return (
      <article className="feedback-card helpful">
        <IconFor name="HeartHandshake" />
        <div>
          <strong>这个选择也有帮助！</strong>
          <p>这次最适合的是 {bestName}。{reason}</p>
        </div>
      </article>
    );
  }

  return (
    <article className="feedback-card try">
      <IconFor name="Sparkles" />
      <div>
        <strong>你发现了一个线索。</strong>
        <p>{hint}</p>
        <span>更适合的小狗是：{bestName}</span>
      </div>
    </article>
  );
}
