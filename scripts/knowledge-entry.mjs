import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

export const RESERVED_PAGE_HASHES = ["worlds", "recent-observation"];
export const HIDDEN_BOARD_IDS = ["kids-world", "spider-verse", "paw-patrol"];

export function repoRoot() {
  return root;
}

export function loadKnowledgeEntry(sourceRoot = root) {
  return JSON.parse(readFileSync(join(sourceRoot, "shared/knowledge-entry.json"), "utf8"));
}

export function loadTopicRegistry(sourceRoot = root) {
  return JSON.parse(
    readFileSync(join(sourceRoot, "boards/kids-world/src/data/topic-registry.json"), "utf8"),
  );
}

export function topicTitleBySlug(sourceRoot = root) {
  const titles = new Map();
  for (const topic of loadTopicRegistry(sourceRoot).topics) {
    titles.set(topic.slug, topic.title);
  }
  return titles;
}

export function kidsWorldTopicHref(slug) {
  return `boards/kids-world/index.html#topic/${encodeURIComponent(slug)}`;
}

export function legacyTopicPath(slug) {
  return `boards/${slug}/index.html`;
}

export function decodeMaybe(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function resolveTopicSlug(search, hash) {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const queryTopic = params.get("topic");
  if (queryTopic) return decodeMaybe(queryTopic);

  const raw = String(hash || "").replace(/^#/, "");
  if (!raw || RESERVED_PAGE_HASHES.includes(raw)) return null;

  const topicMatch = raw.match(/^topic\/(.+)$/);
  if (topicMatch?.[1]) return decodeMaybe(topicMatch[1]);

  if (raw.includes("/") || raw.includes("=")) return null;
  return decodeMaybe(raw);
}

export function mapIndexedLocation({ pathname = "", search = "", hash = "" }, entry) {
  const frozen = new Set(entry.frozenKidsWorldTopics);
  const path = pathname.replace(/^\//, "").replace(/\/$/, "");
  const pathMatch = path.match(/^boards\/([^/]+)(?:\/index\.html)?$/);
  if (pathMatch) {
    const slug = pathMatch[1];
    if (slug === "kids-world") {
      // Fall through to hash/query mapping on the archive SPA.
    } else if (HIDDEN_BOARD_IDS.includes(slug)) {
      return { kind: "existing-board", slug };
    } else if (frozen.has(slug)) {
      return {
        kind: "substitute-page",
        slug,
        archiveHref: kidsWorldTopicHref(slug),
        galleryHref: entry.cardOsPublicUrl,
      };
    } else {
      return { kind: "unknown-path", slug };
    }
  }

  const slug = resolveTopicSlug(search, hash);
  if (!slug) return { kind: "not-a-topic" };
  if (frozen.has(slug)) {
    return {
      kind: "archive-topic",
      slug,
      archiveHref: kidsWorldTopicHref(slug),
    };
  }
  return { kind: "unknown-topic", slug };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function cardMarkup({ role, href, className, label, title, detail }) {
  return `      <a
        class="${className}"
        data-knowledge-entry="${role}"
        href="${escapeHtml(href)}"
        aria-label="${escapeHtml(label)}"
      >
        <span class="board-art badge" aria-hidden="true">
          <i></i><i></i><i></i>
        </span>
        <span class="board-meta">
          <strong>${escapeHtml(title)}</strong>
          <small>${escapeHtml(detail)}</small>
        </span>
      </a>`;
}

export function hubCopy(entry) {
  if (entry.activeMode === "parallel") {
    return {
      intro: "Card OS 画廊与旧知识站并行可访问。当前主入口仍是旧知识站。",
      canonical: entry.kidsWorldArchiveHref,
      primary: {
        role: "primary",
        href: entry.kidsWorldArchiveHref,
        className: "board-card pending",
        label: "打开旧知识站",
        title: "进入探索地图",
        detail: "六大知识世界 · 最近观察 · 中英文切换 · 点击任务",
      },
      secondary: {
        role: "secondary",
        href: entry.cardOsPublicUrl,
        className: "board-card archive",
        label: "打开 Card OS 知识画廊",
        title: "Card OS 画廊（并行）",
        detail: "已发布四卡 · 验收中 · 尚未作为主入口",
      },
    };
  }

  return {
    intro: "知识主入口已迁到 Card OS 画廊。旧知识站仍可打开，但不再扩展新的内容模型。",
    canonical: entry.cardOsPublicUrl,
    primary: {
      role: "primary",
      href: entry.cardOsPublicUrl,
      className: "board-card pending",
      label: "打开 Card OS 知识画廊",
      title: "进入知识画廊",
      detail: "已发布四卡 · PDF · 来源与 QA · 版本历史",
    },
    secondary: {
      role: "archive",
      href: entry.kidsWorldArchiveHref,
      className: "board-card archive",
      label: "打开冻结的旧知识站",
      title: "旧知识站档案",
      detail: "13 个主题冻结保留 · 不再作为主入口",
    },
  };
}

export function renderHubHtml(entry) {
  const copy = hubCopy(entry);
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>芋头宇宙</title>
  <meta name="description" content="从真实观察和好奇问题出发，点亮生命、身体、地球、宇宙、能量和人造系统的儿童认知看板。">
  <link rel="icon" href="shared/icons/favicon.ico" sizes="48x48">
  <link rel="icon" href="shared/icons/icon-32.png" type="image/png" sizes="32x32">
  <link rel="icon" href="shared/icons/icon-192.png" type="image/png" sizes="192x192">
  <link rel="apple-touch-icon" href="shared/icons/apple-touch-icon.png">
  <meta property="og:title" content="芋头宇宙">
  <meta property="og:description" content="从真实观察和好奇问题出发，点亮真正的世界知识。">
  <meta property="og:image" content="__OG_IMAGE__">
  <meta property="og:type" content="website">
  <link rel="canonical" href="${escapeHtml(copy.canonical)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&amp;family=Noto+Sans+SC:wght@400;500;700;900&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="shared/styles/home.css">
</head>
<body>
  <main class="home-shell">
    <header class="hero" aria-labelledby="page-title">
      <p class="eyebrow">Yutou Verse</p>
      <h1 id="page-title">芋头宇宙</h1>
      <p class="intro">${escapeHtml(copy.intro)}</p>
    </header>

    <section class="board-grid" aria-label="知识入口">
${cardMarkup(copy.primary)}
${cardMarkup(copy.secondary)}
    </section>
  </main>
</body>
</html>
`;
}

export function renderLegacyTopicPageHtml(slug, title, entry) {
  const archiveHref = `../kids-world/index.html#topic/${encodeURIComponent(slug)}`;
  const safeTitle = escapeHtml(title);
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${safeTitle} · 旧知识站</title>
  <meta name="description" content="${safeTitle}仍在冻结的旧知识站里，还没有做成 Card OS 四卡。">
  <link rel="canonical" href="${escapeHtml(archiveHref)}">
  <link rel="icon" href="../../shared/icons/favicon.ico" sizes="48x48">
  <link rel="stylesheet" href="../../shared/styles/home.css">
</head>
<body>
  <main class="home-shell">
    <header class="hero" aria-labelledby="page-title">
      <p class="eyebrow">旧链接说明</p>
      <h1 id="page-title">${safeTitle}</h1>
      <p class="intro">这个主题仍是冻结档案，还不是 Card OS 四卡。知识主入口已迁到新画廊；旧页可以继续打开。</p>
    </header>
    <section class="board-grid" aria-label="替代入口">
      <a class="board-card pending" href="${escapeHtml(archiveHref)}">
        <span class="board-meta">
          <strong>打开旧主题页</strong>
          <small>冻结的 kids-world 档案 · ${escapeHtml(slug)}</small>
        </span>
      </a>
      <a class="board-card archive" href="${escapeHtml(entry.cardOsPublicUrl)}">
        <span class="board-meta">
          <strong>打开新知识画廊</strong>
          <small>已发布四卡 · 不是这个旧主题的机械映射</small>
        </span>
      </a>
    </section>
  </main>
</body>
</html>
`;
}

export function assertLegacySlugSafe(slug) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    throw new Error(`unsafe legacy topic slug: ${slug}`);
  }
  if (HIDDEN_BOARD_IDS.includes(slug)) {
    throw new Error(`refusing to write a stub over an existing board: ${slug}`);
  }
}
