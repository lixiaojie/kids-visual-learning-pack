import { useState } from "react";
import type { Locale } from "./types/topic";
import { useHashRoute } from "./hooks/use-hash-route";
import { getMap } from "./data/loaders/load-map";
import { PageShell } from "./components/layout/PageShell";
import { HomePage } from "./pages/HomePage";
import { TopicPage } from "./pages/TopicPage";

export function App() {
  const topicSlug = useHashRoute();
  const [locale, setLocale] = useState<Locale>("zh-CN");
  const map = getMap(locale);

  return (
    <PageShell locale={locale} onLocaleChange={setLocale} map={map}>
      {topicSlug ? (
        <TopicPage slug={topicSlug} locale={locale} map={map} />
      ) : (
        <HomePage locale={locale} map={map} />
      )}
    </PageShell>
  );
}
