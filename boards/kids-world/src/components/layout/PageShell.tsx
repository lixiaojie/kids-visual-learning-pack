import type { ReactNode } from "react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { Topbar } from "./Topbar";

type Props = {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  map: ExplorationMap;
  children: ReactNode;
  isTopicPage?: boolean;
};

export function PageShell({ locale, onLocaleChange, map, children, isTopicPage }: Props) {
  return (
    <div className={isTopicPage ? "app-shell app-shell-topic" : "app-shell"}>
      <Topbar map={map} locale={locale} onLocaleChange={onLocaleChange} isTopicPage={isTopicPage} />
      {children}
    </div>
  );
}
