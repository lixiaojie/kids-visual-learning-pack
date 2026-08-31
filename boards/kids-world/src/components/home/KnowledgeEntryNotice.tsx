import type { Locale } from "../../types/topic";
import { isCardOsKnowledgeHome, knowledgeEntry } from "../../lib/knowledge-entry";

type Props = { locale: Locale };

export function KnowledgeEntryNotice({ locale }: Props) {
  const isCardOs = isCardOsKnowledgeHome();
  const zh = locale === "zh-CN";
  const notice = isCardOs
    ? zh
      ? "知识主入口已迁到 Card OS 画廊。本页是冻结的旧知识站。"
      : "The knowledge home is now the Card OS gallery. This page is a frozen archive."
    : zh
      ? "Card OS 画廊可并行打开。本页仍是当前知识主入口。"
      : "The Card OS gallery is available in parallel. This page is still the knowledge home.";
  const linkLabel = isCardOs
    ? zh
      ? "打开新画廊"
      : "Open the new gallery"
    : zh
      ? "打开 Card OS 画廊"
      : "Open the Card OS gallery";

  return (
    <p className="knowledge-entry-notice">
      {notice}{" "}
      <a href={knowledgeEntry.cardOsPublicUrl}>{linkLabel}</a>
    </p>
  );
}
