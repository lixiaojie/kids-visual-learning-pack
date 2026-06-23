import { useEffect, useRef, useState } from "react";
import { Menu, Sparkles } from "lucide-react";
import type { ExplorationMap, Locale } from "@yutou/kids-content";
import { LocaleToggle } from "../shared/LocaleToggle";

type Props = {
  map: ExplorationMap;
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  isTopicPage?: boolean;
};

type HiddenHeaderProps = {
  "aria-hidden"?: true;
  inert?: "";
};

export function Topbar({ map, locale, onLocaleChange, isTopicPage }: Props) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [topbarHidden, setTopbarHidden] = useState(false);
  const lastScrollY = useRef(0);
  const hiddenTabIndex = topbarHidden ? -1 : undefined;
  const hiddenHeaderProps: HiddenHeaderProps = topbarHidden ? { "aria-hidden": true, inert: "" } : {};
  const navItems = [
    { href: "#", label: locale === "zh-CN" ? "探索首页" : "Home" },
    { href: "#worlds", label: locale === "zh-CN" ? "全部世界" : "Worlds" },
    { href: "#parent-guide", label: locale === "zh-CN" ? "家长说明" : "Parent Guide" },
  ];

  useEffect(() => {
    if (!isTopicPage) {
      setTopbarHidden(false);
      return;
    }

    const mobileQuery = window.matchMedia("(max-width: 760px)");
    lastScrollY.current = window.scrollY;

    const revealIfDesktop = () => {
      if (!mobileQuery.matches) setTopbarHidden(false);
    };

    const handleScroll = () => {
      const nextY = window.scrollY;
      const delta = nextY - lastScrollY.current;
      lastScrollY.current = nextY;

      if (!mobileQuery.matches || mobileNavOpen) {
        setTopbarHidden(false);
        return;
      }

      if (nextY > 24 && delta > 8) {
        setMobileNavOpen(false);
        setTopbarHidden(true);
      } else if (nextY < 24 || delta < -8) {
        setTopbarHidden(false);
      }
    };

    if (mobileNavOpen) setTopbarHidden(false);
    window.addEventListener("scroll", handleScroll, { passive: true });
    mobileQuery.addEventListener("change", revealIfDesktop);
    handleScroll();

    return () => {
      window.removeEventListener("scroll", handleScroll);
      mobileQuery.removeEventListener("change", revealIfDesktop);
    };
  }, [isTopicPage, mobileNavOpen]);

  return (
    <header className={topbarHidden ? "topbar topbar-hidden" : "topbar"} data-topic-page={isTopicPage ? "true" : undefined} {...hiddenHeaderProps}>
      <a className="brand" href="#" tabIndex={hiddenTabIndex}>
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
        tabIndex={hiddenTabIndex}
        onClick={() => {
          setTopbarHidden(false);
          setMobileNavOpen((open) => !open);
        }}
      >
        <Menu size={18} />
        {locale === "zh-CN" ? "导航" : "Menu"}
      </button>
      <nav aria-label={locale === "zh-CN" ? "全局导航" : "Global navigation"} className={mobileNavOpen ? "open" : ""} id="global-nav">
        {navItems.map((item) => (
          <a href={item.href} key={item.href} tabIndex={hiddenTabIndex} onClick={() => setMobileNavOpen(false)}>
            {item.label}
          </a>
        ))}
        <LocaleToggle
          locale={locale}
          onChange={(nextLocale) => {
            onLocaleChange(nextLocale);
            setMobileNavOpen(false);
          }}
        />
      </nav>
    </header>
  );
}
