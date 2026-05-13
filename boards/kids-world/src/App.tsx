import { useEffect, useState } from "react";
import type { Locale } from "./types/topic";
import { useHashRoute } from "./hooks/use-hash-route";
import { getMap } from "./data/loaders/load-map";
import { hasTopicData } from "./data/loaders/load-topic";
import { PageShell } from "./components/layout/PageShell";
import { HomePage } from "./pages/HomePage";
import { TopicPage } from "./pages/TopicPage";

const localeStorageKey = "yutou-verse-locale";
const supportedLocales: Locale[] = ["zh-CN", "en-US"];

function getInitialLocale(): Locale {
  const params = new URLSearchParams(window.location.search);
  const queryLocale = params.get("locale") as Locale | null;
  if (queryLocale && supportedLocales.includes(queryLocale)) return queryLocale;

  const savedLocale = window.localStorage.getItem(localeStorageKey) as Locale | null;
  return savedLocale && supportedLocales.includes(savedLocale) ? savedLocale : "zh-CN";
}

export function App() {
  const topicSlug = useHashRoute();
  const [locale, setLocale] = useState<Locale>(getInitialLocale);
  const map = getMap(locale);
  const visibleTopicSlug = topicSlug && hasTopicData(topicSlug) ? topicSlug : null;
  const missingTopic = topicSlug && !visibleTopicSlug;

  useEffect(() => {
    window.localStorage.setItem(localeStorageKey, locale);
  }, [locale]);

  return (
    <PageShell locale={locale} onLocaleChange={setLocale} map={map}>
      {visibleTopicSlug ? (
        <TopicPage slug={visibleTopicSlug} locale={locale} map={map} />
      ) : (
        <HomePage locale={locale} map={map} notice={missingTopic ? "这个探索页还在准备中。" : undefined} />
      )}
    </PageShell>
  );
}
