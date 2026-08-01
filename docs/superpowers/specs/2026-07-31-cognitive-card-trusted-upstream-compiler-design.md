# Cognitive Card OS 可信自由请求编译入口设计（API-01 草案）

状态：草案，待用户书面审阅；未获确认前不实施

日期：2026-07-31

关联：ADR-001、抢救清单与 Block 修复方案（抢救分支 `codex/card-os-salvage-v1`)、服务器 `0.3.1`(`c2a898c`)

## 1. 目标

把抢救回来的生产核心（`core/`）迁移为**服务器侧内容寻址权威快照 + 可信上游编译器**，使用户在任意 Codex 终端提出自由概念（如"兔子，深圳，5～6岁，中英文，打印版"）时，由可信上游按同一套规范把它编译为锁定 GenerationPacket 导入服务器；任何终端的薄客户端（已发布的 `0.1.1`）随后领取该 packet 并按同一机制生成高质量候选。

非目标：本批次不做服务器渲染（RENDER-01)、服务器 QA(QA-01)、package-v5 发布面（PUBLISH-01，须先关闭两个评审 Block)、正式站点替换。本文件只为它们预留接口。

## 2. 已确认的关键决策（用户书面）

- 方向：**可信上游编译器**。服务器应用（FastAPI）无 LLM;`core/SKILL.md` 的 CLASSIFICATION/FACT/SEMANTIC CORE 等推理在环步骤由可信上游（登录 ChatGPT Pro 的受信 Codex 终端）执行。
- 复用策略：**lift-and-harden**。RENDER/QA/PUBLISH 不新写服务器管线，直接采用厚客户端已验证模块；每个模块上服务器前过三道：信任边界重审、运行时钉住、输入面重验。
- 薄客户端 `0.1.1` 与 SKILL-01 冻结契约不变；服务器 `0.3.1` 的 M1 链路（packets API、auth、candidate store、registry）零改动。

## 3. 总体架构

```text
自由概念（用户，任意终端）
  → 可信上游编译器（受信 Codex 终端，短期 admin scope token）
      · 读取 core 权威快照（摘要绑定）
      · 按 core 工作流执行推理步骤（ChatGPT Pro）
      · 确定性组装 LockedJobRequest + PacketIssueRequest（编译器代码，非 LLM）
      · POST /admin/locked-jobs → POST /admin/jobs/{id}/packets（已部署 0.3.1）
      · 撤销 admin token
  → 服务器：锁定 job（content_locked）+ packet（可领取）
  → 任意终端薄客户端 0.1.1：doctor → auth → list/claim/get（复算 packet_digest）
  → 本地生成（无 OpenAI API Key）→ complete → results submit → candidate_staged
```

"同一机制"不由各终端本地副本保证，而由三点保证：(1) core 快照在服务器侧唯一权威、内容寻址；(2) 编译产物（packet）把规范实例化为 digest 绑定的 `instructions`/`required_outputs`/content lock;(3) 薄客户端只认 `packet_digest`，拒绝任何不匹配。

## 4. core 权威快照

### 4.1 快照内容

以抢救分支的 `skills/cognitive-card-os/core/`（34 文件）为唯一来源，其 `source-manifest.json`(schema `cognitive-card-os-recovered-core-v1`,identity `installed-cognitive-card-os-v5-audited-runtime`）已提供闭包与摘要绑定：17 个知识/规范 references、7 个模板族 assets、6 个确定性脚本、provenance、SKILL.md、agents/openai.yaml。**编译侧只迁移 references/assets/provenance/SKILL.md 与编译所需脚本；渲染与发布面脚本留给对应批次。**

### 4.2 存储与寻址（两个选项，推荐 A)

**选项 A（推荐，零服务器应用改动）**：快照作为服务器应用仓内的受治理版本化资产（`cognitive-card-server` 仓新增 `core-snapshots/<snapshot-id>/`，含 source-manifest 与全部文件），随应用部署落盘；编译器与服务器都从该仓的精确 commit 读取。`registry_commit` 记录该仓 commit;`template_fingerprint` = 所用模板族文件的规范 JSON 摘要。优点：复用现有部署/回滚机制，无新端点。缺点：快照读取不经 API，终端无法独立核对快照内容（只能核对 packet digest)。

**选项 B（显式新增面，留作后续）**：服务器增加内容寻址快照存储与只读端点（如 `/card-os/api/v1/core-snapshots/<digest>`),capabilities 广告当前快照摘要。优点：终端可独立验证编译所用规范；缺点：服务器应用新增面，需要单独评审与硬化。本设计不依赖 B;B 可在 RENDER-01 前重新评估。

### 4.3 快照绑定规则（进入 packet 的三个字段）

- `registry_commit`：服务器应用仓包含该快照的精确 commit(40 位小写 hex，满足 `LockedJobRequest.registry_commit` 的 `^[0-9a-f]{7,64}$`)。
- `template_fingerprint`:`"sha256:" + sha256(canonical_json({"families": <编译所用 family 文件规范 JSON>, "style_tokens": <对应 style_tokens 内容>}))`，编译器确定性计算并在 LockedJobRequest 中提交；服务器原样持久化（权威来自编译器，服务器复算留待 RENDER-01)。
- `content_lock_digest`:`"sha256:" + sha256(canonical_json(编译锁内容))`，锁内容 = 分类结果、FACT、SEMANTIC CORE、模板解析结果、年龄/语言投影、输出声明的规范 JSON（见第 6 节转换表）。编译器计算；packet 的 `forbidden_changes` 至少含 `content_lock_digest`。

## 5. 可信上游编译器

### 5.1 运行位置与形态

编译器是服务器应用仓的受治理操作员工具（建议 `cognitive_card_server/compiler/`，纯 Python 标准库 + 既有 schema 模型），以 CLI 在受信 Codex 终端运行。推理步骤由该终端的 ChatGPT Pro 会话执行；**编译器代码只做确定性工作**：加载并校验快照闭包（按 source-manifest 复算全部摘要）、执行 schema 校验、计算三个绑定摘要、组装并提交 admin 请求、记录审计。LLM 产出物（分类、FACT、SEMANTIC CORE、卡片文本草稿）以文件形式落在编译工作区，编译器把它们当不可信输入重验（schema、长度、受控字符）后才纳入锁内容。

### 5.2 凭据模型

- 编译用短期（≤15 分钟）`admin` scope token，经服务器 `cognitive-card-auth issue` 签发，编译完成或失败后立即 `revoke`；
- token 只经 0600 文件/`CARD_OS_TOKEN` 环境传递，不进 argv/日志/工作区文件/Git;
- 编译器不持有任何长期凭据；薄客户端永远得不到 admin scope。

### 5.3 编译流程

1. `compiler lock <workspace>`：读取快照，引导操作员（或受信 Codex）按 `core/SKILL.md` 工作流产出锁材料；编译器复算快照摘要、校验锁材料、计算 `content_lock_digest` 与 `template_fingerprint`，提交 `POST /admin/locked-jobs`;
2. `compiler issue <workspace>`：基于锁内容组装 PacketIssueRequest(stage、language_projection、instructions、required_outputs、forbidden_changes、input_artifacts)，提交 `POST /admin/jobs/{job_id}/packets`;
3. `compiler verify <packet-id>`：用薄客户端同款公式复算服务器返回的 `packet_digest`，不一致即失败关闭并报告；
4. 任一失败：已创建的 job/packet 通过过期（`expires_at`）失效，不留下可领取的半成品；审计记录不含自由概念以外的敏感信息。

### 5.4 与既有验收的关系

SKILL-02 Task 8 的锁定 packet 创建流程（admin token → locked-jobs → packets → revoke）已在现网跑通两次，编译器的 admin 导入段直接复用该已验证路径，仅把"手工拼请求体"替换为"快照 + 锁材料的确定性组装"。

## 6. 权威转换表（core 工作流产出 → 服务器 schema)

逐字段对照 `c2a898c`（不发明字段）。LockedJobRequest:`job_id`、`content_lock_digest`、`registry_commit`、`template_fingerprint`、`age_profile`、`execution_profile`。PacketIssueRequest:`stage`、`language_projection`、`instructions`、`required_outputs`、`forbidden_changes`、`input_artifacts`。

| 服务器字段 | 来源（core 工作流） | 规则 |
| --- | --- | --- |
| `job_id` | INPUT CHECK | `job_<object-slug>_v<NN>`;`^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` |
| `content_lock_digest` | CONTENT LOCK | 第 4.3 节规则，编译器计算 |
| `registry_commit` | 快照 | 服务器应用仓快照 commit |
| `template_fingerprint` | TEMPLATE PROFILE | 第 4.3 节规则 |
| `age_profile` | INPUT CHECK | `age-5-6` 等，`^age-[0-9]+(?:-[0-9]+)?$` |
| `execution_profile` | 固定 | `client_subscription_interactive`（唯一枚举值） |
| `stage` | 工作流位置 | 枚举 `source_research`/`semantic_draft`/`bilingual_projection`/`image_generation`；首版默认 `bilingual_projection`（四卡文本），图像任务为 `image_generation` |
| `language_projection` | age-language-profiles | 如 `cn_primary_en_support`,1–128 字符 |
| `instructions` | core/SKILL.md 工作流 + 锁内容 | 编译器从锁内容生成的有序指令（1–128 条），含四卡产出规则、命题 ID 一致性、确定性要求 |
| `required_outputs` | output-templates / 锁内容 | 每项 `{relative_path, media_type, max_bytes}`；首版文本类：`cards/cn-observation.json`、`cards/en-observation.json`、`cards/cn-knowledge.json`、`cards/en-knowledge.json`(application/json，上限按 output-templates 推导，≤20 MiB)；路径经薄客户端同款安全规则 |
| `forbidden_changes` | 固定 + 锁内容 | 至少 `["content_lock_digest"]` |
| `input_artifacts` | 可选 | 默认 `[]`（自由概念无输入资产） |

packet 的 `packet_id`/`issued_at`/`expires_at`/`schema`/`packet_digest` 由服务器生成，编译器只读并复算。

## 7. 与服务器 `0.3.1` 的边界

- M1 链路（packets/results/jobs、auth、candidate store、registry)**零改动**;
- 服务器应用仓的变更仅限：新增 `core-snapshots/` 受治理资产目录与 `compiler/` 操作员工具 + 对应测试；不新增任何 HTTP 端点（选项 A);
- 服务器应用部署（systemd/Nginx/env）不变；快照随应用仓部署，回滚 = 应用仓回滚。

## 8. 后续批次接口预留（lift-and-harden)

- **RENDER-01**:`render_card_candidate.py` + 模板族 + 固定 Pillow 上服务器，消费 accepted candidate + 同一 core 快照渲染四卡；`template_fingerprint` 即渲染输入绑定。
- **QA-01**:`validate_card_package.py`/`validate_production_record.py`/`image-quality-qa` 作为服务器 QA 门，在渲染后、发布前执行；输入面按不可信重验。
- **PUBLISH-01**:package-v5 上传面（先按修复方案关闭两个 Block:authority 闭包服务端复算——可直接采用 `governed_authority.py`/`validate_package_v5.py`;gallery revision 绑定）。`content_lock_digest` 与快照摘要贯穿四卡、PDF 与发布 manifest。
- 每批次的厚模块上服务器前都过三道：信任边界重审、运行时钉住（Pillow/libwebp 版本）、输入面重验。

## 9. 安全与失败关闭

- 薄客户端零权威：自由概念在薄客户端依旧返回 `TRUSTED_UPSTREAM_REQUIRED`（行为不变）;
- 编译器是唯一能把自由概念变成锁定 packet 的入口，且只存在于受信终端 + 短期 admin token;
- 所有 digest 由编译器确定性计算、客户端/服务器各自复算自己负责的部分；任何不匹配失败关闭，不降级；
- token 不进 argv/日志/证据/Git；编译工作区不含凭据；
- 编译器不读取/上传 ChatGPT Cookie、会话或身份材料。

## 10. 测试与验收

- 单元：快照闭包校验（缺失/篡改/额外文件拒绝）、三个摘要的确定性、转换表逐字段 schema 合规（对照 `c2a898c` 的 StrictRequestModel)、锁材料不可信输入的拒绝用例；
- 集成（临时库）：编译 → admin 导入 → packet 可领取 → digest 复算一致；
- 现网验收（API-01 实施批次）：兔子自由概念经可信上游编译为锁定 packet → 隔离薄客户端 claim→生成→complete→submit→candidate_staged，审计链完整，token 撤销后 403;
- 回归：薄客户端 280 项与 registry 81 项测试不受影响（零改动的证明）。

## 11. 风险与开放问题

- **转换规则的首次正确性**:core 工作流 → packet 的映射是本设计的最大工作量；实施时先用 2–3 个真实概念（兔子、恐龙）走形态 3（人工在环）校准，再固化编译器规则。
- **core 快照与 `c2a898c` 的漂移**：快照源自 07-16，绑定规则以 `c2a898c` schema 为唯一准绳；编译器测试直接引用服务器 schema 模型，防止各自演化。
- **图像任务**：首版聚焦文本类四卡 packet;`image_generation` stage 与视觉确认人在环步骤归 RENDER-01/QA-01 细化。
- **选项 B（快照只读端点）** 是否提前：默认不做，RENDER-01 前重新评估。
- 快照存放仓：建议服务器应用仓（与部署/回滚同生命周期）；如用户希望放治理仓经 rsync 分发，作为显式备选。

## 12. 实施分解（获书面确认后另行立项）

1. API-01-IMPL-1：服务器应用仓 `core-snapshots/` 导入（source-manifest 闭包 + 摘要复算工具 + 测试）;
2. API-01-IMPL-2：编译器确定性部分（快照加载校验、三个摘要、schema 组装、admin 导入、verify)+ 测试；
3. API-01-IMPL-3：人工在环校准（兔子/恐龙两个概念）+ 现网验收（隔离薄客户端端到端）+ 评审。
