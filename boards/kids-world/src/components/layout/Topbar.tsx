import { useState } from "react";
import { Menu, Sparkles } from "lucide-react";
import type { ExplorationMap, Locale } from "@yutou/kids-content";
import { LocaleToggle } from "../shared/LocaleToggle";

type Props = {
  map: ExplorationMap;
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
};

export function Topbar({ map, locale, onLocaleChange }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const navItems = [
    { href: "#", label: locale === "zh-CN" ? "探索首页" : "Home" },
    { href: "#worlds", label: locale === "zh-CN" ? "全部世界" : "Worlds" },
    { href: "#parent-guide", label: locale === "zh-CN" ? "家长说明" : "Parent Guide" },
  ];

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
        aria-controls="global-nav"
        onClick={() => setMobileNavOpen((open) => !open)}
      >
        <Menu size={18} />
        {locale === "zh-CN" ? "导航" : "Menu"}
      </button>
      <nav aria-label={locale === "zh-CN" ? "全局导航" : "Global navigation"} className={mobileNavOpen ? "open" : ""} id="global-nav">
        {navItems.map((item) => (
          <a href={item.href} key={item.href} onClick={() => setMobileNavOpen(false)}>
            {item.label}
          </a>
        ))}
      </nav>
      <LocaleToggle locale={locale} onChange={onLocaleChange} />
    </header>
  );
}
