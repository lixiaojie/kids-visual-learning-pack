import {
  ArrowLeft,
  BadgeCheck,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Dna,
  Languages,
  Menu,
  Play,
  Search,
  Sparkles,
} from "lucide-react";

import registry from "./data/topic-registry.json";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import type { ExplorationMap, TopicCard, World } from "./types/world";
import type { ClickTask, Locale, TaskResult, TextMap, Topic } from "./types/topic";
import type { GeneratedImageAsset } from "./types/assets";
import { getTopicHref, getExternalHref, resolveBoardAssetCandidates } from "./lib/asset-resolve";
import { generatedAssets, topicHeroAssetBySlug, getTopicCardAssetId, getKnowledgeTopicAssetId } from "./lib/asset-map";
import { worldIcons } from "./lib/world-icons";
import { getMap } from "./data/loaders/load-map";
import { getTopic, hasTopicData } from "./data/loaders/load-topic";
import { useHashRoute } from "./hooks/use-hash-route";

function GeneratedImage({
  assetId,
  fallbackPath,
  className,
  alt,
}: {
  assetId?: string;
  fallbackPath?: string;
  className: string;
  alt: string;
}) {
  const asset = assetId ? generatedAssets[assetId] : undefined;
  const sources = [asset?.webpPath, asset?.pngPath, fallbackPath]
    .flatMap((path) => resolveBoardAssetCandidates(path))
    .filter(Boolean);
  const [sourceIndex, setSourceIndex] = useState(0);

  useEffect(() => {
    setSourceIndex(0);
  }, [assetId, fallbackPath]);

  const source = sources[sourceIndex];

  if (!source) {
    return null;
  }

  return (
    <img
      alt={alt}
      className={className}
      src={source}
      onError={() => {
        setSourceIndex((current) => (current + 1 < sources.length ? current + 1 : sources.length));
      }}
    />
  );
}

function LocaleToggle({ locale, onChange }: { locale: Locale; onChange: (locale: Locale) => void }) {
  return (
    <div className="locale-toggle" aria-label="Language switch">
      <Languages size={18} />
      <button className={locale === "zh-CN" ? "active" : ""} type="button" onClick={() => onChange("zh-CN")}>
        中文
      </button>
      <button className={locale === "en-US" ? "active" : ""} type="button" onClick={() => onChange("en-US")}>
        English
      </button>
    </div>
  );
}

function StatusPill({ status, map }: { status: string; map: ExplorationMap }) {
  const statusText = map.statusLegend.find((item) => item.status === status);
  return <span className={`status-pill status-${status}`}>{statusText?.childLabel ?? status}</span>;
}

function PlaceholderScene({ topic }: { topic: Topic }) {
  const type = topic.hero.placeholder?.type ?? topic.pageType;
  const assetId = topicHeroAssetBySlug[topic.slug];
  return (
    <div className={`placeholder-scene ${String(type)} ${assetId ? "generated-scene" : ""}`}>
      <GeneratedImage
        alt=""
        assetId={assetId}
        className="scene-image"
        fallbackPath={topic.hero.placeholder?.asset ?? topic.assets?.hero?.path}
      />
      <span className="scene-orbit" />
      <span className="scene-node one" />
      <span className="scene-node two" />
      <span className="scene-node three" />
      <span className="scene-label">{topic.title}</span>
    </div>
  );
}

function SectionHeader({ kicker, title, children }: { kicker?: string; title: string; children?: ReactNode }) {
  return (
    <div className="section-head">
      {kicker && <p className="kicker">{kicker}</p>}
      <h2>{title}</h2>
      {children && <p>{children}</p>}
    </div>
  );
}

function HomePage({ locale, map }: { locale: Locale; map: ExplorationMap }) {
  const [selectedWorldId, setSelectedWorldId] = useState("animation");
  const selectedWorld = map.worlds.find((world) => world.id === selectedWorldId) ?? map.worlds[0];
  const knowledgeWorlds = map.worlds.filter((world) => world.id !== "animation");
  const animationWorld = map.worlds.find((world) => world.id === "animation") ?? map.worlds[0];

  return (
    <main className="page-shell">
      <section className="home-hero">
        <div>
          <p className="kicker">{locale === "zh-CN" ? "芋头世界" : "Yutou World"}</p>
          <h1>{map.homeHero.title}</h1>
          <p>{map.homeHero.childIntro}</p>
          <div className="hero-actions">
            <a className="primary-button" href="#worlds">
              <Play size={18} />
              {map.homeHero.primaryCTA}
            </a>
            <a className="secondary-button" href="#topics">
              <BadgeCheck size={18} />
              {map.homeHero.secondaryCTA}
            </a>
          </div>
        </div>
        <aside className="parent-note home-hero-visual">
          <GeneratedImage alt="" assetId="homepage-exploration-map-hero" className="home-hero-image" />
          <div>
            <BookOpen />
            <strong>{map.homeHero.subtitle}</strong>
            <span>{map.homeHero.parentIntro}</span>
          </div>
        </aside>
      </section>

      <section className="interest-band" id="topics">
        <SectionHeader title={animationWorld.entryCard.title} kicker={animationWorld.entryCard.badge}>
          {animationWorld.entryCard.subtitle}
        </SectionHeader>
        <div className="topic-card-grid animation-topics">
          {animationWorld.topicCards.map((topic) => (
            <a className="topic-card completed" href={getExternalHref(topic.href)} key={topic.id}>
              <GeneratedImage alt="" assetId={getTopicCardAssetId(topic)} className="topic-card-image" />
              <Sparkles />
              <strong>{topic.title}</strong>
              <span>{topic.cardDescription}</span>
              <div className="tag-row">{topic.learningGoalTags?.map((tag) => <em key={tag}>{tag}</em>)}</div>
              {topic.suggestedRoute && <small>{topic.suggestedRoute}</small>}
            </a>
          ))}
        </div>
      </section>

      <section className="worlds-section" id="worlds">
        <SectionHeader title={map.sections[1].title} kicker={locale === "zh-CN" ? "六大知识世界" : "Knowledge Worlds"}>
          {map.sections[1].description}
        </SectionHeader>
        <div className="world-grid">
          {knowledgeWorlds.map((world) => {
            const Icon = worldIcons[world.id as keyof typeof worldIcons] ?? CircleHelp;
            return (
              <button
                className={selectedWorldId === world.id ? "world-card active" : "world-card"}
                key={world.id}
                style={{ "--accent": world.recommendedColor.hex, "--soft": world.recommendedColor.softHex } as React.CSSProperties}
                type="button"
                onClick={() => setSelectedWorldId(world.id)}
              >
                <Icon />
                <span>{world.entryCard.badge}</span>
                <strong>{world.name}</strong>
                <small>{world.childOneLiner}</small>
              </button>
            );
          })}
        </div>
      </section>

      <section className="selected-world-panel">
        <div>
          <SectionHeader title={selectedWorld.name} kicker={selectedWorld.entryCard.badge}>
            {selectedWorld.parentNote}
          </SectionHeader>
        </div>
        <div className="topic-card-grid">
          {selectedWorld.topicCards.map((topic) => {
            const topicHref = topic.slug && hasTopicData(topic.slug) ? getTopicHref(topic.slug) : undefined;
            return (
              <a className={`topic-card ${topic.status}`} href={topicHref ?? "#worlds"} key={topic.slug ?? topic.id}>
                <GeneratedImage alt="" assetId={getKnowledgeTopicAssetId(topic)} className="topic-card-image" />
                <StatusPill status={topic.status} map={map} />
                <strong>{topic.title}</strong>
                <span>{topic.cardDescription}</span>
                <div className="tag-row">{topic.learningGoalTags?.map((tag) => <em key={tag}>{tag}</em>)}</div>
                {topicHref && (
                  <small className="open-topic">
                    {locale === "zh-CN" ? "打开看板" : "Open board"} <ChevronRight size={15} />
                  </small>
                )}
              </a>
            );
          })}
        </div>
      </section>
    </main>
  );
}

function TopicPage({ map, topic, locale }: { map: ExplorationMap; topic: Topic; locale: Locale }) {
  const [activeObjectId, setActiveObjectId] = useState(topic.representativeObjects[0]?.id ?? "");

  const activeObject = topic.representativeObjects.find((item) => item.id === activeObjectId) ?? topic.representativeObjects[0];

  return (
    <main className="page-shell topic-page">
      <a className="back-link" href="#">
        <ArrowLeft size={18} />
        {locale === "zh-CN" ? "返回探索地图" : "Back to map"}
      </a>

      <section className="topic-hero">
        <div className="topic-hero-copy">
          <p className="kicker">{topic.hero.kicker}</p>
          <h1>{topic.hero.title}</h1>
          <p>{topic.hero.lead}</p>
          <div className="goal-list">
            {topic.learningGoals.map((goal) => (
              <span key={goal}>
                <CheckCircle2 size={16} />
                {goal}
              </span>
            ))}
          </div>
        </div>
        <PlaceholderScene topic={topic} />
      </section>

      <section className="content-grid">
        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "看一看主场景" : "Look at the scene"} kicker={topic.coreQuestion}>
            {topic.hero.sceneExplanation}
          </SectionHeader>
        </article>

        <article className="panel">
          <SectionHeader title={locale === "zh-CN" ? "分类线索" : "Sorting clues"} />
          <div className="group-list">
            {topic.classificationGroups.map((group) => (
              <button
                className={activeObject?.groupId === group.id ? "group-card active" : "group-card"}
                key={group.id}
                type="button"
              >
                <strong>{group.name}</strong>
                <span>{group.childExplanation}</span>
              </button>
            ))}
          </div>
        </article>

        <article className="panel">
          <SectionHeader title={locale === "zh-CN" ? "对象卡" : "Object cards"} />
          <div className="object-grid">
            {topic.representativeObjects.map((object) => (
              <button
                className={activeObjectId === object.id ? "object-card active" : "object-card"}
                key={object.id}
                type="button"
                onClick={() => setActiveObjectId(object.id)}
              >
                <Dna size={20} />
                <strong>{object.name}</strong>
                <small>{object.visualHint}</small>
              </button>
            ))}
          </div>
          {activeObject && (
            <div className="object-detail">
              <strong>{activeObject.name}</strong>
              <span>{activeObject.childExplanation}</span>
              <small>{activeObject.commonMisread}</small>
            </div>
          )}
        </article>

        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "机制步骤" : "How it works"} />
          <div className="step-row">
            {topic.mechanism.steps.map((step, index) => (
              <div className="step-card" key={step.id}>
                <span>{index + 1}</span>
                <strong>{step.shortTitle}</strong>
                <small>{step.childExplanation}</small>
              </div>
            ))}
          </div>
        </article>

        {topic.secondaryMechanism && (
          <article className="panel wide">
            <SectionHeader title={topic.secondaryMechanism.title} />
            <div className="step-row">
              {topic.secondaryMechanism.steps.map((step, index) => (
                <div className="step-card" key={step.id}>
                  <span>{index + 1}</span>
                  <strong>{step.shortTitle}</strong>
                  <small>{step.childExplanation}</small>
                </div>
              ))}
            </div>
          </article>
        )}

        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "容易混淆" : "Easy mix-ups"} />
          <div className="compare-grid">
            {topic.comparePairs.map((pair) => (
              <div className="compare-card" key={pair.id}>
                <strong>{pair.title}</strong>
                <div>
                  <span>{pair.a.name}</span>
                  <small>{pair.a.points.join(" · ")}</small>
                </div>
                <div>
                  <span>{pair.b.name}</span>
                  <small>{pair.b.points.join(" · ")}</small>
                </div>
                <em>{pair.childConclusion}</em>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide">
          <SectionHeader title={locale === "zh-CN" ? "点击任务" : "Tap tasks"} kicker={locale === "zh-CN" ? "不计分，多试几次" : "No score pressure"} />
          <div className="task-grid">
            {topic.clickTasks.map((task) => (
              <ClickTaskCard task={task} key={task.id} />
            ))}
          </div>
        </article>

        <article className="panel">
          <SectionHeader title={locale === "zh-CN" ? "讲一讲" : "Try explaining"} />
          <div className="speak-list">
            {topic.speakTemplates.map((template) => (
              <span key={template}>{template}</span>
            ))}
          </div>
        </article>

        <article className="panel">
          <SectionHeader title={locale === "zh-CN" ? "家长提示" : "Parent prompts"} />
          <ul className="parent-tips">
            {topic.parentTips.map((tip) => (
              <li key={tip}>{tip}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="related-strip">
        <strong>{locale === "zh-CN" ? "继续探索" : "Keep exploring"}</strong>
        <div className="tag-row">
          {topic.relatedTopics.map((related) => (
            <em key={related}>{related}</em>
          ))}
        </div>
        <StatusPill status="building" map={map} />
      </section>
    </main>
  );
}

function ClickTaskCard({ task }: { task: ClickTask }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<TaskResult>("idle");
  const [message, setMessage] = useState("");

  function resolveWrongHint(optionId?: string) {
    if (optionId && task.wrongHints && optionId in task.wrongHints) return task.wrongHints[optionId as keyof typeof task.wrongHints];
    return task.wrongHint ?? "再观察一个线索试试看。";
  }

  function handleSingleChoice(optionId: string) {
    if (optionId === task.correctOptionId) {
      setResult("correct");
      setMessage(task.successCopy ?? "");
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
  }

  function handleFindTarget(optionId: string) {
    if (task.targetIds?.includes(optionId)) {
      const next = Array.from(new Set([...selectedIds, optionId]));
      setSelectedIds(next);
      const complete = task.targetIds.every((id) => next.includes(id));
      setResult(complete ? "correct" : "idle");
      setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
  }

  function handleSequence(optionId: string) {
    const next = [...selectedIds, optionId];
    const expected = task.correctSequence?.[selectedIds.length];
    if (optionId !== expected) {
      setSelectedIds([]);
      setResult("wrong");
      setMessage(resolveWrongHint(optionId));
      return;
    }
    setSelectedIds(next);
    const complete = next.length === task.correctSequence?.length;
    setResult(complete ? "correct" : "idle");
    setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
  }

  function handleClick(optionId: string) {
    if (task.type === "singleChoice") handleSingleChoice(optionId);
    if (task.type === "findTarget") handleFindTarget(optionId);
    if (task.type === "sequenceClick") handleSequence(optionId);
  }

  const options =
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: id.replace(/-/g, " "),
    }));

  return (
    <div className={`task-card ${result}`}>
      <Search size={20} />
      <strong>{task.title}</strong>
      {task.prompt && <span>{task.prompt}</span>}
      <div className="task-options">
        {options.map((option) => (
          <button
            className={selectedIds.includes(option.id) ? "selected" : ""}
            key={option.id}
            type="button"
            onClick={() => handleClick(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>
      {message && <p>{message}</p>}
    </div>
  );
}

export function App() {
  const [locale, setLocale] = useState<Locale>("zh-CN");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const slug = useHashRoute();
  const map = getMap(locale);
  const topic = slug ? getTopic(slug, locale) : null;

  return (
    <div className="app-shell">
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
          {registry.firstBatch.slice(0, 3).map((topicSlug) => (
            <a href={getTopicHref(topicSlug)} key={topicSlug} onClick={() => setMobileNavOpen(false)}>
              {getTopic(topicSlug, locale)?.title}
            </a>
          ))}
        </nav>
        <LocaleToggle locale={locale} onChange={setLocale} />
      </header>
      {topic ? <TopicPage locale={locale} map={map} topic={topic} /> : <HomePage locale={locale} map={map} />}
    </div>
  );
}
