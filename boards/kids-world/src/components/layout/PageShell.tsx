import type { ReactNode } from "react";
import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import { Topbar } from "./Topbar";

type Props = {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
  map: ExplorationMap;
  children: ReactNode;
};

export function PageShell({ locale, onLocaleChange, map, children }: Props) {
  return (
    <div className="app-shell">
      <Topbar map={map} locale={locale} onLocaleChange={onLocaleChange} />
      {children}
    </div>
  );
}
