import { useState } from "react";
import type { ExplorationMap } from "../types/world";
import type { Locale } from "../types/topic";
import { HeroSection } from "../components/home/HeroSection";
import { InterestBand } from "../components/home/InterestBand";
import { WorldGrid } from "../components/home/WorldGrid";
import { WorldTopicPanel } from "../components/home/WorldTopicPanel";

type Props = { locale: Locale; map: ExplorationMap };

export function HomePage({ locale, map }: Props) {
  const [selectedWorldId, setSelectedWorldId] = useState("animation");
  const selectedWorld = map.worlds.find((world) => world.id === selectedWorldId) ?? map.worlds[0];
  const knowledgeWorlds = map.worlds.filter((world) => world.id !== "animation");
  const animationWorld = map.worlds.find((world) => world.id === "animation") ?? map.worlds[0];

  return (
    <main className="page-shell">
      <HeroSection map={map} locale={locale} />
      <InterestBand world={animationWorld} />
      <WorldGrid
        worlds={knowledgeWorlds}
        selectedWorldId={selectedWorldId}
        onSelectWorld={setSelectedWorldId}
        map={map}
        locale={locale}
      />
      <WorldTopicPanel world={selectedWorld} map={map} locale={locale} />
    </main>
  );
}
