import { IconFor } from "./IconFor";

const steps = [
  {
    title: "发现问题",
    text: "有人遇到了困难。",
    icon: "Megaphone",
  },
  {
    title: "呼叫莱德",
    text: "莱德判断发生了什么。",
    icon: "BadgeHelp",
  },
  {
    title: "选择队员",
    text: "根据问题选择小狗。",
    icon: "Users",
  },
  {
    title: "出动救援",
    text: "使用车辆、工具和合作。",
    icon: "Rocket",
  },
  {
    title: "完成任务",
    text: "大家安全，也学到道理。",
    icon: "Award",
  },
];

const retellQuestions = [
  "这集是谁遇到了困难？",
  "问题发生在哪里？",
  "莱德派了谁？",
  "他们用了什么工具？",
  "最后怎么解决？",
  "你觉得哪里做得好？",
];

export function FlowPanel() {
  return (
    <section className="flow-page">
      <div className="main-panel">
        <p className="section-kicker">任务流程页</p>
        <h2>救援任务五步法</h2>
        <div className="flow-track" aria-label="五步任务流程">
          {steps.map((step, index) => (
            <article key={step.title}>
              <span className="step-number">{index + 1}</span>
              <IconFor name={step.icon} size={34} />
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </div>

      <section className="retell-panel">
        <div>
          <p className="section-kicker">看完一集后</p>
          <h2>说一说发生了什么</h2>
        </div>
        <div className="question-grid">
          {retellQuestions.map((question) => (
            <article key={question}>{question}</article>
          ))}
        </div>
      </section>
    </section>
  );
}
