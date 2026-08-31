import { useRef, useState } from "react";
import type { ExplorationMap } from "../types/world";
import type { Locale } from "../types/topic";
import { HeroSection } from "../components/home/HeroSection";
import { FeaturedObservation } from "../components/home/FeaturedObservation";
import { WorldGrid } from "../components/home/WorldGrid";
import { WorldTopicPanel } from "../components/home/WorldTopicPanel";

type Props = { locale: Locale; map: ExplorationMap };

type HomePageProps = Props & { notice?: string };

export function HomePage({ locale, map, notice }: HomePageProps) {
  const knowledgeWorlds = map.worlds.filter((world) => world.type === "knowledgeWorld");
  const initialWorldId = knowledgeWorlds.find((world) => world.id === "life")?.id ?? knowledgeWorlds[0]?.id ?? "";
  const [selectedWorldId, setSelectedWorldId] = useState(initialWorldId);
  const selectedWorld = knowledgeWorlds.find((world) => world.id === selectedWorldId) ?? knowledgeWorlds[0];
  const topicPanelRef = useRef<HTMLDivElement>(null);

  function handleSelectWorld(id: string) {
    setSelectedWorldId(id);
    requestAnimationFrame(() => {
      topicPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  const cardOsHref = "https://www.yutou.space/card-os/";
  const entryNotice =
    locale === "zh-CN"
      ? "知识主入口已迁到 Card OS 画廊。本页是冻结的旧知识站。"
      : "The knowledge home is now the Card OS gallery. This page is a frozen archive.";
  const entryLinkLabel = locale === "zh-CN" ? "打开新画廊" : "Open the new gallery";

  return (
    <main className="page-shell">
      {notice ? <p className="route-notice">{notice}</p> : null}
      <p className="knowledge-entry-notice">
        {entryNotice}{" "}
        <a href={cardOsHref}>{entryLinkLabel}</a>
      </p>
      <HeroSection map={map} locale={locale} />
      <FeaturedObservation map={map} locale={locale} />
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
