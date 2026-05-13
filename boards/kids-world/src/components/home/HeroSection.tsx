import { BadgeCheck, BookOpen, Play } from "lucide-react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { GeneratedImage } from "../shared/GeneratedImage";

type Props = { map: ExplorationMap; locale: Locale };

export function HeroSection({ map, locale }: Props) {
  return (
    <section className="home-hero">
      <div>
        <p className="kicker">{locale === "zh-CN" ? "芋头宇宙" : "Yutou Verse"}</p>
        <h1>{map.homeHero.title}</h1>
        <p>{map.homeHero.childIntro}</p>
        <div className="hero-actions">
          <a className="primary-button" href="#worlds">
            <Play size={18} />
            {map.homeHero.primaryCTA}
          </a>
          <a className="secondary-button" href="#topics">
            <BadgeCheck size={18} />
            {map.homeHero.secondaryCTA}
          </a>
        </div>
      </div>
      <aside className="parent-note home-hero-visual">
        <GeneratedImage alt="" assetId="homepage-exploration-map-hero" className="home-hero-image" />
        <div>
          <BookOpen />
          <strong>{map.homeHero.subtitle}</strong>
          <span>{map.homeHero.parentIntro}</span>
        </div>
      </aside>
    </section>
  );
}
