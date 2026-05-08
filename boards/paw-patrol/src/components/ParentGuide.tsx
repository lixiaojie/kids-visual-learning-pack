type ParentGuideProps = {
  open: boolean;
  onClose: () => void;
};

export function ParentGuide({ open, onClose }: ParentGuideProps) {
  if (!open) return null;

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <section
        className="parent-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="parent-guide-title"
        onClick={(event) => event.stopPropagation()}
      >
        <button className="icon-close" type="button" onClick={onClose} aria-label="关闭家长说明">
          ×
        </button>
        <p className="section-kicker">给家长看的说明</p>
        <h2 id="parent-guide-title">把喜欢角色变成会表达</h2>
        <p>
          这个页面不是让孩子背角色信息，而是通过角色、任务和工具的匹配，练习分类、因果、表达、复述和合作理解。
        </p>
        <div className="guide-grid">
          <article>
            <strong>分类</strong>
            <span>这个问题属于交通、水上、工程，还是消防？</span>
          </article>
          <article>
            <strong>因果</strong>
            <span>为什么这只小狗适合这个任务？</span>
          </article>
          <article>
            <strong>表达</strong>
            <span>能不能说出选择理由？</span>
          </article>
          <article>
            <strong>复述</strong>
            <span>一集故事发生了什么？</span>
          </article>
          <article>
            <strong>合作</strong>
            <span>有些任务为什么需要多个队员？</span>
          </article>
        </div>
      </section>
    </div>
  );
}
