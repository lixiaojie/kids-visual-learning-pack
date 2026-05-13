import { useRef, useState } from "react";
import type { ExplorationMap } from "../types/world";
import type { Locale } from "../types/topic";
import { HeroSection } from "../components/home/HeroSection";
import { InterestBand } from "../components/home/InterestBand";
import { WorldGrid } from "../components/home/WorldGrid";
import { WorldTopicPanel } from "../components/home/WorldTopicPanel";

type Props = { locale: Locale; map: ExplorationMap };

type HomePageProps = Props & { notice?: string };

export function HomePage({ locale, map, notice }: HomePageProps) {
  const [selectedWorldId, setSelectedWorldId] = useState("animation");
  const selectedWorld = map.worlds.find((world) => world.id === selectedWorldId) ?? map.worlds[0];
  const knowledgeWorlds = map.worlds.filter((world) => world.id !== "animation");
  const animationWorld = map.worlds.find((world) => world.id === "animation");
  const topicPanelRef = useRef<HTMLDivElement>(null);

  function handleSelectWorld(id: string) {
    setSelectedWorldId(id);
    requestAnimationFrame(() => {
      topicPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  return (
    <main className="page-shell">
      {notice ? <p className="route-notice">{notice}</p> : null}
      <HeroSection map={map} locale={locale} />
      {animationWorld ? <InterestBand world={animationWorld} /> : null}
      <WorldGrid
        worlds={knowledgeWorlds}
        selectedWorldId={selectedWorldId}
        onSelectWorld={handleSelectWorld}
        map={map}
        locale={locale}
      />
      {selectedWorld ? <WorldTopicPanel ref={topicPanelRef} world={selectedWorld} map={map} locale={locale} /> : null}
    </main>
  );
}
