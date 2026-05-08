import { useEffect, useMemo, useState } from "react";
import { BadgePanel } from "./components/BadgePanel";
import { CharacterPanel } from "./components/CharacterPanel";
import { FlowPanel } from "./components/FlowPanel";
import { GearWorkshop } from "./components/GearWorkshop";
import { HomeDashboard } from "./components/HomeDashboard";
import { IconFor } from "./components/IconFor";
import { MapExplorer } from "./components/MapExplorer";
import { MissionGame } from "./components/MissionGame";
import { ParentGuide } from "./components/ParentGuide";
import { StoryLab } from "./components/StoryLab";
import { characters } from "./data/characters";
import { missions } from "./data/missions";
import type { TabKey } from "./types";

const storageKey = "paw-rescue-badges";

type MissionResult = "best" | "helpful" | "try-again" | null;

const tabs: Array<{ key: TabKey; label: string; icon: string }> = [
  { key: "home", label: "首页", icon: "MapPinned" },
  { key: "characters", label: "角色", icon: "Users" },
  { key: "map", label: "地图", icon: "MapPinned" },
  { key: "gear", label: "装备", icon: "Rocket" },
  { key: "mission", label: "任务", icon: "Rocket" },
  { key: "flow", label: "流程", icon: "CheckCircle2" },
  { key: "story", label: "复述", icon: "BadgeQuestionMark" },
  { key: "badges", label: "徽章", icon: "Award" },
];

export function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("home");
  const [selectedCharacterId, setSelectedCharacterId] = useState(characters[0].id);
  const [currentMissionId, setCurrentMissionId] = useState(missions[0].id);
  const [selectedMissionCharacterId, setSelectedMissionCharacterId] = useState<string | null>(null);
  const [missionResult, setMissionResult] = useState<MissionResult>(null);
  const [unlockedBadges, setUnlockedBadges] = useState<string[]>([]);
  const [guideOpen, setGuideOpen] = useState(false);

  useEffect(() => {
    const saved = window.localStorage.getItem(storageKey);
    if (!saved) return;

    try {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) setUnlockedBadges(parsed.filter((item) => typeof item === "string"));
    } catch {
      setUnlockedBadges([]);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(storageKey, JSON.stringify(unlockedBadges));
  }, [unlockedBadges]);

  const currentMission = useMemo(
    () => missions.find((mission) => mission.id === currentMissionId) ?? missions[0],
    [currentMissionId],
  );

  function unlockBadge(badgeId: string) {
    setUnlockedBadges((previous) => Array.from(new Set([...previous, badgeId])));
  }

  function handleMissionChoice(characterId: string) {
    setSelectedMissionCharacterId(characterId);

    if (characterId === currentMission.bestCharacterId) {
      setMissionResult("best");
      unlockBadge(currentMission.badgeRewardId);
      return;
    }

    if (currentMission.recommendedCharacterIds.includes(characterId)) {
      setMissionResult("helpful");
      return;
    }

    setMissionResult("try-again");
  }

  function handleNextMission() {
    const availableMissions = missions.filter((mission) => mission.id !== currentMissionId);
    const nextMission = availableMissions[Math.floor(Math.random() * availableMissions.length)] ?? missions[0];
    setCurrentMissionId(nextMission.id);
    setSelectedMissionCharacterId(null);
    setMissionResult(null);
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brand-link" href="../../index.html" aria-label="返回学习包首页">
          <span className="brand-badge">
            <IconFor name="PawPrint" />
          </span>
          <span>
            <strong>汪汪队任务指挥中心</strong>
            <small>角色分工 · 地图装备 · 能力徽章</small>
          </span>
        </a>
        <nav className="tab-nav" aria-label="页面切换">
          {tabs.map((tab) => (
            <button
              className={activeTab === tab.key ? "active" : ""}
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
            >
              <IconFor name={tab.icon} size={19} />
              {tab.label}
            </button>
          ))}
        </nav>
        <button className="guide-button" type="button" onClick={() => setGuideOpen(true)}>
          家长说明
        </button>
      </header>

      <main className="app-main">
        {activeTab === "home" && (
          <HomeDashboard
            unlockedBadges={unlockedBadges}
            onChangeTab={setActiveTab}
            onOpenGuide={() => setGuideOpen(true)}
            onSelectCharacter={setSelectedCharacterId}
          />
        )}
        {activeTab === "characters" && (
          <CharacterPanel selectedCharacterId={selectedCharacterId} onSelectCharacter={setSelectedCharacterId} />
        )}
        {activeTab === "map" && <MapExplorer />}
        {activeTab === "gear" && <GearWorkshop />}
        {activeTab === "mission" && (
          <MissionGame
            currentMissionId={currentMissionId}
            result={missionResult}
            selectedCharacterId={selectedMissionCharacterId}
            onNextMission={handleNextMission}
            onSelectCharacter={handleMissionChoice}
          />
        )}
        {activeTab === "flow" && <FlowPanel />}
        {activeTab === "story" && <StoryLab onUnlockReview={() => unlockBadge("review")} />}
        {activeTab === "badges" && <BadgePanel unlockedBadges={unlockedBadges} />}
      </main>

      <ParentGuide open={guideOpen} onClose={() => setGuideOpen(false)} />
    </div>
  );
}
