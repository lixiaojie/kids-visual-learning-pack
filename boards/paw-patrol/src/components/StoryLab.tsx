import { useState } from "react";
import { IconFor } from "./IconFor";

const storySteps = ["发现问题", "呼叫莱德", "选择队员", "出动救援", "完成任务"];

const prompts = [
  "谁遇到了困难？",
  "问题在哪里发生？",
  "莱德派了谁？",
  "用了什么车辆或工具？",
  "最后大家学到了什么？",
];

type StoryLabProps = {
  onUnlockReview: () => void;
};

export function StoryLab({ onUnlockReview }: StoryLabProps) {
  const [checked, setChecked] = useState<string[]>([]);

  function toggleStep(step: string) {
    setChecked((previous) => {
      const next = previous.includes(step) ? previous.filter((item) => item !== step) : [...previous, step];
      if (next.length === storySteps.length) onUnlockReview();
      return next;
    });
  }

  return (
    <section className="story-page">
      <div className="main-panel">
        <p className="section-kicker">故事复述卡</p>
        <h2>按顺序讲清楚一集故事</h2>
        <div className="story-checklist">
          {storySteps.map((step, index) => (
            <button
              className={checked.includes(step) ? "story-step done" : "story-step"}
              key={step}
              type="button"
              onClick={() => toggleStep(step)}
            >
              <span>{index + 1}</span>
              <strong>{step}</strong>
              <IconFor name={checked.includes(step) ? "CheckCircle2" : "Sparkles"} />
            </button>
          ))}
        </div>
      </div>
      <aside className="detail-panel story-detail">
        <IconFor name="BadgeQuestionMark" size={52} />
        <p className="section-kicker">亲子提问</p>
        <h2>说出理由</h2>
        <div className="mini-list">
          {prompts.map((prompt) => (
            <span key={prompt}>{prompt}</span>
          ))}
        </div>
        <div className="tip-box">
          <strong>复盘徽章</strong>
          <span>五步都点亮后，会保存复盘徽章。</span>
        </div>
      </aside>
    </section>
  );
}
