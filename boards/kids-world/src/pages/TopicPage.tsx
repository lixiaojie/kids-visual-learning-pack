import { ArrowLeft } from "lucide-react";
import { getTopic, type ExplorationMap, type Locale } from "@yutou/kids-content";
import { KnowledgeEntryNotice } from "../components/home/KnowledgeEntryNotice";
import { SceneDeckTopicPage } from "../components/topic/SceneDeckTopicPage";

type Props = { slug: string; locale: Locale; map: ExplorationMap };

export function TopicPage({ slug, locale }: Props) {
  const topic = getTopic(slug, locale);

  if (!topic) {
    return (
      <main className="page-shell topic-page">
        <a className="back-link" href="#">
          <ArrowLeft size={18} />
          {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
        </a>
        <KnowledgeEntryNotice locale={locale} />
        <p>Topic not found.</p>
      </main>
    );
  }

  return <SceneDeckTopicPage topic={topic} locale={locale} />;
}
