import { useState } from "react";
import { Menu, Sparkles } from "lucide-react";
import { getTopic, type ExplorationMap, type Locale } from "@yutou/kids-content";
import { LocaleToggle } from "../shared/LocaleToggle";
import { getTopicHref } from "../../lib/asset-resolve";

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
        {map.worlds
          .flatMap((world) => world.topicCards)
          .filter((topic) => topic.slug)
          .slice(0, 3)
          .map((topic) => (
            <a href={getTopicHref(topic.slug as string)} key={topic.slug} onClick={() => setMobileNavOpen(false)}>
              {getTopic(topic.slug as string, locale)?.title}
            </a>
          ))}
      </nav>
      <LocaleToggle locale={locale} onChange={onLocaleChange} />
    </header>
  );
}
