import { CircleHelp } from "lucide-react";
import type { ExplorationMap, World } from "../../types/world";
import type { Locale } from "../../types/topic";
import { worldIcons } from "../../lib/world-icons";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  worlds: World[];
  selectedWorldId: string;
  onSelectWorld: (id: string) => void;
  map: ExplorationMap;
  locale: Locale;
};

export function WorldGrid({ worlds, selectedWorldId, onSelectWorld, map, locale }: Props) {
  const knowledgeSection = map.sections.find((section) => section.id === "knowledge-worlds") ?? map.sections[0];

  return (
    <section className="worlds-section" id="worlds">
      <SectionHeader
        title={knowledgeSection?.title ?? (locale === "zh-CN" ? "六大知识世界" : "Knowledge Worlds")}
        kicker={locale === "zh-CN" ? "六大知识世界" : "Knowledge Worlds"}
      >
        {knowledgeSection?.description ?? ""}
      </SectionHeader>
      <div className="world-grid">
        {worlds.map((world) => {
          const Icon = worldIcons[world.id as keyof typeof worldIcons] ?? CircleHelp;
          return (
            <button
              className={selectedWorldId === world.id ? "world-card active" : "world-card"}
              key={world.id}
              style={{ "--accent": world.recommendedColor.hex, "--soft": world.recommendedColor.softHex } as React.CSSProperties}
              type="button"
              onClick={() => onSelectWorld(world.id)}
            >
              <Icon />
              <span>{world.entryCard.badge}</span>
              <strong>{world.name}</strong>
              <small>{world.childOneLiner}</small>
            </button>
          );
        })}
      </div>
    </section>
  );
}
