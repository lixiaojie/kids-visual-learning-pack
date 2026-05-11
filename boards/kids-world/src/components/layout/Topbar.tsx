import { useState } from "react";
import { Menu, Sparkles } from "lucide-react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { LocaleToggle } from "../shared/LocaleToggle";
import { getTopicHref } from "../../lib/asset-resolve";
import { getTopic } from "../../data/loaders/load-topic";
import registry from "../../data/topic-registry.json";

type Props = {
  map: ExplorationMap;
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
};

export function Topbar({ map, locale, onLocaleChange }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <header className="topbar">
      <a className="brand" href="#">
        <Sparkles />
        <span>
          <strong>{map.title}</strong>
          <small>{map.subtitle}</small>
        </span>
      </a>
      <button
        className="mobile-menu-button"
        type="button"
        aria-expanded={mobileNavOpen}
        aria-controls="topic-nav"
        onClick={() => setMobileNavOpen((open) => !open)}
      >
        <Menu size={18} />
        {locale === "zh-CN" ? "主题" : "Topics"}
      </button>
      <nav className={mobileNavOpen ? "open" : ""} id="topic-nav">
        {registry.firstBatch.slice(0, 3).map((topicSlug) => (
          <a href={getTopicHref(topicSlug)} key={topicSlug} onClick={() => setMobileNavOpen(false)}>
            {getTopic(topicSlug, locale)?.title}
          </a>
        ))}
      </nav>
      <LocaleToggle locale={locale} onChange={onLocaleChange} />
    </header>
  );
}
