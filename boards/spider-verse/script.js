const characters = [
  {
    id: "main-boy",
    name: "黑红少年",
    role: "刚开始冒险的主角",
    childLine: "他有点紧张，但愿意试试看。",
    parentNote: "普通孩子进入冒险，是整个故事的情感入口。",
    image: "assets/characters/main-boy.webp",
    tags: ["成长", "勇气", "新能力"]
  },
  {
    id: "girl-companion",
    name: "白帽女孩",
    role: "轻盈独立的朋友",
    childLine: "她轻盈、独立，也懂朋友。",
    parentNote: "这个角色帮助孩子理解朋友之间的信任、秘密和同行。",
    image: "assets/characters/girl-companion.webp",
    tags: ["朋友", "节奏", "理解"]
  },
  {
    id: "older-veteran",
    name: "红蓝前辈",
    role: "有经验的守护者",
    childLine: "他有经验，愿意保护别人。",
    parentNote: "前辈角色承载责任感，也让孩子看到榜样不是遥不可及。",
    image: "assets/characters/older-veteran.webp",
    tags: ["经验", "守护", "责任"]
  },
  {
    id: "worn-mentor",
    name: "外套导师",
    role: "不完美的大人",
    childLine: "他有点疲惫，但很温柔。",
    parentNote: "导师不是完美英雄，而是愿意陪伴、鼓励、重新学习的大人。",
    image: "assets/characters/worn-mentor.webp",
    tags: ["导师", "鼓励", "重新学习"]
  },
  {
    id: "pig-sidekick",
    name: "搞笑小猪",
    role: "让故事轻松的伙伴",
    childLine: "它让紧张故事变轻松。",
    parentNote: "幽默角色能降低紧张感，让孩子更愿意继续看故事。",
    image: "assets/characters/pig-sidekick.webp",
    tags: ["幽默", "轻松", "卡通"]
  },
  {
    id: "tech-girl-giant-robot",
    name: "科技女孩与大机器人",
    role: "一起想办法的组合",
    childLine: "她和大机器人一起想办法。",
    parentNote: "这个组合强调合作：聪明不只是一个人厉害，也可以是和伙伴配合。",
    image: "assets/characters/tech-girl-giant-robot.webp",
    tags: ["科技", "合作", "伙伴"]
  },
  {
    id: "noir-detective",
    name: "黑白侦探",
    role: "旧故事书里的英雄",
    childLine: "他来自旧故事书一样的世界。",
    parentNote: "黑白风格帮助孩子理解：不同世界可以有完全不同的视觉语言。",
    image: "assets/characters/noir-detective.webp",
    tags: ["侦探", "黑白", "风格"]
  },
  {
    id: "future-guardian",
    name: "未来守护者",
    role: "重视规则和秩序",
    childLine: "他很重视规则和秩序。",
    parentNote: "未来守护者适合讨论：规则重要，但规则也需要解释和照顾人。",
    image: "assets/characters/future-guardian.webp",
    tags: ["规则", "秩序", "分歧"]
  }
];

const relations = [
  { image: "assets/characters/father.webp", label: "爸爸 → 黑红少年", text: "爱他，也担心他", type: "family" },
  { image: "assets/characters/mother.webp", label: "妈妈 → 黑红少年", text: "希望他做真实的自己", type: "family" },
  { image: "assets/characters/uncle-secret.webp", label: "叔叔 ↔ 黑红少年", text: "亲近，但有秘密", type: "family-conflict" },
  { image: "assets/relationships/main-girl.webp", label: "白帽女孩 ↔ 黑红少年", text: "互相理解", type: "friend" },
  { image: "assets/relationships/main-mentor.webp", label: "外套导师 → 黑红少年", text: "教他，也鼓励他", type: "mentor" },
  { image: "assets/characters/future-guardian.webp", label: "未来守护者 ↔ 黑红少年", text: "规则与选择的冲突", type: "conflict" },
  { image: "assets/characters/portal-troublemaker.webp", label: "传送门麻烦 → 黑红少年", text: "小麻烦变成大问题", type: "problem" }
];

const powers = [
  ["爬墙", "可以从不一样的路过去", "帮助他找到新的方向", "如果你有这个能力，你会先帮助谁？"],
  ["荡绳", "在城市中快速移动", "赶到需要帮助的地方", "你会荡去哪里？"],
  ["危险感应", "发现危险要来了", "提醒他先观察再行动", "你生活里有过“不太对”的感觉吗？"],
  ["敏捷跳跃", "身体很灵活", "跨过看起来很难的地方", "你有没有害怕但还是跳了一步？"],
  ["蓝色光芒", "新能力，还在学习控制", "关键时刻保护自己和别人", "新本领一开始不会用怎么办？"],
  ["隐藏自己", "先观察，再行动", "不是逃避，而是等合适时机", "什么时候安静观察也很重要？"],
  ["节奏动作", "像音乐一样移动", "让动作更轻快、更有信心", "你会给这个动作配什么音乐？"],
  ["机器人协作", "和伙伴一起想办法", "一个人想不到，就一起想", "你最想和谁组队？"]
];

const storyOne = [
  ["01-new-school.webp", "新学校", "他来到新学校，有点不适应。", "普通生活是冒险的起点。", "紧张", "你有去新地方的经历吗？"],
  ["02-graffiti-tunnel.webp", "地下涂鸦", "他和叔叔有一个秘密基地。", "建立亲近关系。", "放松", "你有喜欢和家人一起做的事吗？"],
  ["03-glowing-bug.webp", "发光小虫", "奇怪的事情开始了。", "新能力的触发。", "惊讶", "你觉得他这时害怕还是好奇？"],
  ["04-sticky-accident.webp", "黏住课本", "新能力一点也不听话。", "能力先带来混乱。", "慌张", "新本领不好控制时怎么办？"],
  ["05-circular-machine.webp", "圆形机器", "城市开始变得不稳定。", "外部危机出现。", "不安", "你看到危险会先找谁帮忙？"],
  ["06-protector-falls.webp", "英雄倒下", "他第一次感到责任很重。", "成长的痛点。", "难过", "英雄可以难过吗？"],
  ["07-meet-mentor.webp", "遇到导师", "一个不完美的大人帮助他。", "导师关系建立。", "疑惑", "老师也会犯错吗？"],
  ["08-allies-portals.webp", "伙伴出现", "原来还有很多同伴。", "世界变大。", "惊喜", "你会先认识哪个伙伴？"],
  ["09-uncle-shadow.webp", "叔叔影子", "亲近的人也有秘密。", "复杂人物关系。", "混乱", "喜欢一个人就要赞成他所有选择吗？"],
  ["10-father-door.webp", "门外鼓励", "家人的话给了他力量。", "情感支撑。", "被支持", "你希望家人怎样鼓励你？"],
  ["11-leap-of-courage.webp", "勇敢一跃", "他终于相信自己。", "成长核心瞬间。", "勇敢", "哪句话能让你更勇敢？"],
  ["12-protect-city.webp", "守护城市", "他用自己的方式留下来。", "完成第一阶段成长。", "自信", "自己的方式是什么意思？"]
].map((item, index) => makeStoryItem("story-01", item, index));

const storyTwo = [
  ["01-girl-world.webp", "鼓手少女", "她也有自己的孤单。", "先建立伙伴的内心。", "孤单", "朋友也会有自己的烦恼吗？"],
  ["02-missing-friend.webp", "想念朋友", "主角想再次见到朋友。", "情感动机。", "想念", "想朋友时可以怎么做？"],
  ["03-portal-trouble.webp", "黑洞麻烦", "小麻烦开始变大。", "问题角色出现。", "困惑", "小问题什么时候会变大？"],
  ["04-rooftop-reunion.webp", "高处重逢", "两个朋友再次见面。", "情感连接。", "开心", "重逢时你会先说什么？"],
  ["05-multiverse-tunnel.webp", "彩色通道", "他进入更大的世界。", "多元世界展开。", "惊奇", "你想进入什么样的世界？"],
  ["06-city-rescue.webp", "城市救援", "他先选择救人。", "行动优先于规则。", "坚定", "看到别人需要帮助时怎么办？"],
  ["07-headquarters.webp", "巨大总部", "他见到很多冒险者。", "系统与组织出现。", "震撼", "人很多就一定更安全吗？"],
  ["08-rule-explanation.webp", "解释规则", "有人告诉他必须怎样。", "规则压力出现。", "压力", "规则需要解释吗？"],
  ["09-choose-family.webp", "选择家人", "他不想放弃重要的人。", "核心价值冲突。", "坚定", "重要的人遇到危险怎么办？"],
  ["10-headquarters-chase.webp", "总部追逐", "大家意见不同。", "团队和个人冲突。", "紧张", "意见不同还能做朋友吗？"],
  ["11-wrong-city.webp", "不对劲城市", "他回到一个奇怪地方。", "悬念和危机。", "不安", "哪里像家又不完全对？"],
  ["12-team-up.webp", "朋友组队", "朋友们决定帮助他。", "新阶段开启。", "希望", "真正的朋友会怎么做？"]
].map((item, index) => makeStoryItem("story-02", item, index));

const problemCards = [
  {
    name: "巨大机器人物",
    image: "assets/characters/machine-figure.webp",
    want: "想修复自己的遗憾",
    mistake: "用危险机器影响城市",
    lesson: "不能因为难过就伤害别人",
    emotion: "难过"
  },
  {
    name: "有秘密的叔叔",
    image: "assets/characters/uncle-secret.webp",
    want: "想保护自己，也关心主角",
    mistake: "隐藏身份，做了错误选择",
    lesson: "喜欢的人也可能犯错",
    emotion: "害怕"
  },
  {
    name: "黑洞小丑式人物",
    image: "assets/characters/portal-troublemaker.webp",
    want: "想被重视",
    mistake: "把怨气变成麻烦",
    lesson: "被忽视的情绪会变大",
    emotion: "被忽视"
  },
  {
    name: "未来守护者",
    image: "assets/characters/future-guardian.webp",
    want: "想保持秩序",
    mistake: "过度相信规则",
    lesson: "规则重要，但也要看人",
    emotion: "害怕失控"
  }
];

const worlds = [
  ["涂鸦城市", "街头、少年、涂鸦", "黑红少年"],
  ["白帽水彩世界", "音乐、轻盈、粉蓝", "白帽女孩"],
  ["经验城市", "稳定、红蓝、守护", "红蓝前辈"],
  ["旧电影城市", "黑白、侦探、街灯", "黑白侦探"],
  ["搞笑卡通世界", "夸张、轻松", "搞笑小猪"],
  ["科技机器人世界", "屏幕、线路、大机器人", "科技女孩"],
  ["未来秩序世界", "霓虹、几何、规则", "未来守护者"]
];

const choices = [
  ["勇气", "我害怕", "我也要试试", "成长不是没有害怕", "关联剧情：勇敢一跃"],
  ["家人", "保护秘密", "相信家人", "英雄也需要被支持", "关联剧情：门外鼓励、选择家人"],
  ["规则", "听规则", "问为什么", "规则重要，但不能停止思考", "关联剧情：解释规则"],
  ["朋友", "跟着团队", "帮助朋友", "朋友会在关键时刻站出来", "关联剧情：朋友组队"]
];

const artItems = [
  ["分格", "像漫画页一样看故事"],
  ["速度线", "让动作看起来很快"],
  ["声音形状", "声音也可以变成图形"],
  ["印刷圆点", "像印出来的图画书"],
  ["不同画风", "每个世界像不同绘本"],
  ["情绪色彩", "颜色能告诉我们心情"]
];

const generatedAssetManifest = [
  "assets/cast/cast-lineup.webp",
  "assets/characters/main-boy.webp",
  "assets/characters/girl-companion.webp",
  "assets/characters/older-veteran.webp",
  "assets/characters/worn-mentor.webp",
  "assets/characters/pig-sidekick.webp",
  "assets/characters/tech-girl-giant-robot.webp",
  "assets/characters/noir-detective.webp",
  "assets/characters/future-guardian.webp",
  "assets/characters/father.webp",
  "assets/characters/mother.webp",
  "assets/characters/uncle-secret.webp",
  "assets/characters/machine-figure.webp",
  "assets/characters/portal-troublemaker.webp",
  "assets/relationships/main-girl.webp",
  "assets/relationships/main-mentor.webp",
  "assets/relationships/main-family.webp",
  "assets/relationships/main-veteran.webp",
  "assets/story-01/01-new-school.webp",
  "assets/story-01/02-graffiti-tunnel.webp",
  "assets/story-01/03-glowing-bug.webp",
  "assets/story-01/04-sticky-accident.webp",
  "assets/story-01/05-circular-machine.webp",
  "assets/story-01/06-protector-falls.webp",
  "assets/story-01/07-meet-mentor.webp",
  "assets/story-01/08-allies-portals.webp",
  "assets/story-01/09-uncle-shadow.webp",
  "assets/story-01/10-father-door.webp",
  "assets/story-01/11-leap-of-courage.webp",
  "assets/story-01/12-protect-city.webp",
  "assets/story-02/01-girl-world.webp",
  "assets/story-02/02-missing-friend.webp",
  "assets/story-02/03-portal-trouble.webp",
  "assets/story-02/04-rooftop-reunion.webp",
  "assets/story-02/05-multiverse-tunnel.webp",
  "assets/story-02/06-city-rescue.webp",
  "assets/story-02/07-headquarters.webp",
  "assets/story-02/08-rule-explanation.webp",
  "assets/story-02/09-choose-family.webp",
  "assets/story-02/10-headquarters-chase.webp",
  "assets/story-02/11-wrong-city.webp",
  "assets/story-02/12-team-up.webp",
  "assets/boards/role-gallery-bg.webp",
  "assets/boards/relationship-map-bg.webp",
  "assets/boards/power-atlas-bg.webp",
  "assets/boards/story-01-board.webp",
  "assets/boards/story-02-board.webp",
  "assets/boards/problem-cards-bg.webp",
  "assets/boards/multiverse-books-bg.webp",
  "assets/boards/choice-balance-bg.webp",
  "assets/boards/art-lab-bg.webp",
  "assets/boards/creation-card-bg.webp"
];

function makeStoryItem(folder, item, index) {
  const [file, title, childLine, parentNote, emotion, question] = item;
  return {
    step: index + 1,
    title,
    childLine,
    parentNote,
    emotion,
    question,
    image: `assets/${folder}/${file}`
  };
}

function imageMarkup(src, alt) {
  return `<img src="${src}" alt="${alt}" data-fallback="${alt}">`;
}

function setDetail(panel, text) {
  panel.textContent = text;
  panel.classList.add("is-filled");
}

function clearDetail(panel, text) {
  panel.textContent = text;
  panel.classList.remove("is-filled");
}

function setMode(mode) {
  const toggle = document.querySelector("[data-mode-toggle]");
  document.body.dataset.mode = mode;
  toggle.textContent = mode === "child" ? "儿童模式" : "家长模式";
  toggle.setAttribute("aria-pressed", String(mode === "parent"));
}

function renderCharacters() {
  const grid = document.querySelector("#character-grid");
  const detail = document.querySelector("#character-detail");
  grid.innerHTML = characters.map((character, index) => `
    <button class="character-card ${index === 0 ? "is-active" : ""}" type="button" data-character="${character.id}">
      <span class="woven-badge" aria-hidden="true"></span>
      <span class="character-image asset-frame">${imageMarkup(character.image, character.name)}</span>
      <strong>${character.name}</strong>
      <em>${character.role}</em>
      <span>${character.childLine}</span>
      <small>${character.tags.join(" · ")}</small>
    </button>
  `).join("");
  setDetail(detail, characters[0].parentNote);

  grid.querySelectorAll("[data-character]").forEach((button) => {
    button.addEventListener("click", () => {
      grid.querySelectorAll(".is-active").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      const character = characters.find((item) => item.id === button.dataset.character);
      setDetail(detail, character.parentNote);
    });
  });
}

function renderRelations() {
  const list = document.querySelector("#relation-list");
  list.innerHTML = relations.map((relation) => `
    <article class="relation-card relation-${relation.type}">
      <span class="relation-thumb asset-frame">${imageMarkup(relation.image, relation.label)}</span>
      <div><strong>${relation.label}</strong><p>${relation.text}</p></div>
    </article>
  `).join("");
}

function renderPowers() {
  const grid = document.querySelector("#power-grid");
  const detail = document.querySelector("#power-detail");
  grid.innerHTML = powers.map(([name, childLine, useCase, question], index) => `
    <button class="power-card" type="button" data-power="${index}">
      <span class="power-symbol power-${index + 1}" aria-hidden="true"></span>
      <strong>${name}</strong>
      <span>${childLine}</span>
    </button>
  `).join("");

  grid.querySelectorAll("[data-power]").forEach((button) => {
    button.addEventListener("click", () => {
      const [name, , useCase, question] = powers[Number(button.dataset.power)];
      setDetail(detail, `${name}：${useCase}。亲子提问：${question}`);
    });
  });
}

function renderStoryGrid(target, items, groupName) {
  const list = document.querySelector(target);
  list.innerHTML = items.map((item) => `
    <li>
      <button class="story-frame" type="button" data-story="${groupName}" data-step="${item.step}">
        <span class="story-number">${String(item.step).padStart(2, "0")}</span>
        <span class="story-image asset-frame">${imageMarkup(item.image, item.title)}</span>
        <strong>${item.title}</strong>
        <span>${item.childLine}</span>
        <small class="parent-note">${item.parentNote}</small>
      </button>
    </li>
  `).join("");
}

function openStoryModal(storyName, step) {
  const modal = document.querySelector("#story-modal");
  const items = storyName === "one" ? storyOne : storyTwo;
  const item = items.find((entry) => entry.step === step);
  document.querySelector("#modal-image").src = item.image;
  document.querySelector("#modal-image").alt = item.title;
  document.querySelector("#modal-kicker").textContent = `${storyName === "one" ? "第一段故事" : "第二段故事"} · 第 ${item.step} 格 · ${item.emotion}`;
  document.querySelector("#modal-title").textContent = item.title;
  document.querySelector("#modal-child").textContent = item.childLine;
  document.querySelector("#modal-parent").textContent = item.parentNote;
  document.querySelector("#modal-question").textContent = `可以问孩子：${item.question}`;
  if (typeof modal.showModal === "function") modal.showModal();
  else modal.setAttribute("open", "");
}

function wireStoryModal() {
  document.querySelectorAll(".story-frame").forEach((button) => {
    button.addEventListener("click", () => {
      openStoryModal(button.dataset.story, Number(button.dataset.step));
    });
  });

  const close = document.querySelector("[data-modal-close]");
  close.addEventListener("click", () => close.closest("dialog").close());
}

function renderProblems() {
  const grid = document.querySelector("#problem-grid");
  const detail = document.querySelector("#problem-detail");
  grid.innerHTML = problemCards.map((card, index) => `
    <button class="problem-card" type="button" data-problem="${index}">
      <span class="problem-image asset-frame">${imageMarkup(card.image, card.name)}</span>
      <strong>${card.name}</strong>
      <dl>
        <dt>想要</dt><dd>${card.want}</dd>
        <dt>做错</dt><dd>${card.mistake}</dd>
        <dt>学到</dt><dd>${card.lesson}</dd>
      </dl>
    </button>
  `).join("");

  grid.querySelectorAll("[data-problem]").forEach((button) => {
    button.addEventListener("click", () => {
      const card = problemCards[Number(button.dataset.problem)];
      setDetail(detail, `情绪：${card.emotion} → 行为：${card.mistake} → 后果：影响别人。`);
    });
  });
}

function renderWorlds() {
  document.querySelector("#book-grid").innerHTML = worlds.map(([name, mood, role]) => `
    <article class="book-card">
      <span class="book-cover" aria-hidden="true"></span>
      <strong>${name}</strong>
      <span>${mood}</span>
      <small>${role}</small>
    </article>
  `).join("");
}

function renderChoices() {
  const grid = document.querySelector("#choice-grid");
  const detail = document.querySelector("#choice-detail");
  grid.innerHTML = choices.map(([name, left, right, note, link], index) => `
    <button class="choice-card" type="button" data-choice="${index}">
      <strong>${name}</strong>
      <span>${left}</span>
      <b>vs</b>
      <span>${right}</span>
      <small>${note}</small>
    </button>
  `).join("");

  grid.querySelectorAll("[data-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      const [name, , , note, link] = choices[Number(button.dataset.choice)];
      setDetail(detail, `${name}：${note}。${link}`);
    });
  });
}

function renderArtLab() {
  const grid = document.querySelector("#art-grid");
  const detail = document.querySelector("#art-detail");
  grid.innerHTML = artItems.map(([name, text], index) => `
    <button class="art-card" type="button" data-art="${index}">
      <span aria-hidden="true"></span>
      <strong>${name}</strong>
      <small>${text}</small>
    </button>
  `).join("");

  grid.querySelectorAll("[data-art]").forEach((button) => {
    button.addEventListener("click", () => {
      const [name, text] = artItems[Number(button.dataset.art)];
      setDetail(detail, `${name}：${text}`);
    });
  });
}

function wireModeToggle() {
  document.querySelector("[data-mode-toggle]").addEventListener("click", () => {
    setMode(document.body.dataset.mode === "child" ? "parent" : "child");
  });
}

function wireReset() {
  document.querySelector("[data-reset]").addEventListener("click", () => {
    document.querySelector(".top-actions").removeAttribute("open");
    setMode("child");
    document.querySelector(".creation-form").reset();
    document.querySelectorAll(".character-card.is-active").forEach((card) => card.classList.remove("is-active"));
    document.querySelector(".character-card")?.classList.add("is-active");

    setDetail(document.querySelector("#character-detail"), characters[0].parentNote);
    clearDetail(document.querySelector("#power-detail"), "点一个能力，看看它能帮忙解决什么问题。");
    clearDetail(document.querySelector("#problem-detail"), "点一张问题卡，看“情绪 → 行为 → 后果”。");
    clearDetail(document.querySelector("#choice-detail"), "点一个天平，看看它关联哪段剧情。");
    clearDetail(document.querySelector("#art-detail"), "点一个视觉模块，展开一句解释。");

    const modal = document.querySelector("#story-modal");
    if (modal.open && typeof modal.close === "function") modal.close();
    else modal.removeAttribute("open");

    document.querySelectorAll(".card-nav a.active").forEach((link) => link.classList.remove("active"));
    document.querySelector('.card-nav a[href="#hero"]')?.classList.add("active");
    document.querySelector("#hero").scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function wirePrint() {
  const printButton = document.querySelector("[data-print]");
  printButton.addEventListener("click", () => {
    document.querySelector(".top-actions").removeAttribute("open");
    window.print();
  });
}

function wireImageFallbacks() {
  document.querySelectorAll("img[data-fallback]").forEach((image) => {
    image.addEventListener("error", () => {
      const frame = image.closest(".asset-frame");
      if (!frame) return;
      frame.classList.add("is-missing");
      frame.dataset.fallback = image.dataset.fallback || "图片素材";
      image.hidden = true;
    }, { once: true });
  });
}

function preloadGeneratedAssets() {
  generatedAssetManifest.forEach((src) => {
    const image = new Image();
    image.src = src;
  });
}

function wireRevealAndNav() {
  const sections = Array.from(document.querySelectorAll(".reveal"));
  const navLinks = Array.from(document.querySelectorAll(".card-nav a"));
  if (!("IntersectionObserver" in window)) {
    sections.forEach((section) => section.classList.add("is-visible"));
    return;
  }

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  sections.forEach((section) => revealObserver.observe(section));

  const activeObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    navLinks.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === "#" + visible.target.id);
    });
  }, { threshold: [0.35, 0.55, 0.75] });
  document.querySelectorAll("#hero, .board-section, #appendix").forEach((section) => activeObserver.observe(section));
}

renderCharacters();
renderRelations();
renderPowers();
renderStoryGrid("#story-one-grid", storyOne, "one");
renderStoryGrid("#story-two-grid", storyTwo, "two");
renderProblems();
renderWorlds();
renderChoices();
renderArtLab();
preloadGeneratedAssets();
wireStoryModal();
wireModeToggle();
wireReset();
wirePrint();
wireImageFallbacks();
wireRevealAndNav();
