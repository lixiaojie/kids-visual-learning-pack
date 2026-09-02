# 操作台自由 prompt 编译成知识源（API-01 本刀）

- Status: Approved for this execution tranche
- Date: 2026-09-02
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-003](../../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[LIB-01](2026-08-30-knowledge-library-revision-current-design.md)、[KNOW-03](2026-09-01-entity-knowledge-coverage-design.md)、[WB-01](2026-08-31-operator-knowledge-workbench-design.md)、[WB-02](2026-09-01-operator-mapping-scheme-design.md)、[WB-03](2026-09-01-operator-mapping-artifact-publish-design.md)、[可信上游编译器](2026-07-31-cognitive-card-trusted-upstream-compiler-design.md)
- Does not implement: 2026-07-31 IMPL-1..5 salvage；`generation-input` / `GenerationPacket`；OpenAI API；Codex claim 执行器；生图；生产安装
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

当前没有模型 API，生成仍走 **ChatGPT 会员**（人在浏览器里跑）。本刀把操作台做成这条路径的两端，而不是再做一个领取任务的执行器：

1. 操作员只输入**简短**学习对象与目标（加新 topic slug）；
2. 服务器用受治理的提示词模板，把短输入**扩展成完整提示词**，供复制到 ChatGPT；
3. 操作员把 ChatGPT 回复贴回操作台；
4. 服务器生产管线把回复编译成四对象知识源候选；操作员确认后设为 library current，之后走现有 WB-02 / WB-03。

服务器仍然不调用 ChatGPT、不跑 Codex claim、不把自由长文当知识源。未确认的候选不是知识源。

本设计满足路线图 `API-01` 在本刀的范围。它叠加在 Knowledge Core / library / 操作台之上，不把知识源编回四卡 packet。

## 2. 非目标

- 不接 OpenAI API，不实现 `ServerApiPipelineExecutor`。
- 不写 Skill 领取面：无 `knowledge_compile` claim、无租约、无独立执行器 token。
- 不写出 `cognitive-card-generation-input-v1`，不创建 `GenerationPacket`，不走 0.3.1 领取/提交。
- 不实施 [2026-07-31](2026-07-31-cognitive-card-trusted-upstream-compiler-design.md) 的 IMPL-5，不把 salvage 分支接现网。
- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表。
- 不改 KNOW-04 六主题 current（含生产 `rabbit`）；不编译 `spider-gwen`。
- 不在本刀改已有 current 的命题（知识源「更改」）。
- 不要求本刀走完 WB-02 / WB-03；确认 current 后那些路径必须**能**接着走，但不作为完成条件。
- 不生图、不打应用 release、不 reload Nginx、不 merge server `main`、不 push、不写生产 knowledge-library。
- 不实现浏览器登录会话、AUTH-01 新会话子系统。
- 不把「四卡装得下」写成知识源准入。
- 不从自由散文自动抽取命题：回复必须是可解析的结构化 authoring 稿，否则失败关闭。

## 3. 在主路径中的位置

```text
本刀·短输入         学习对象 + 目标 + 新 slug
本刀·扩提示词       受治理模板 → 可复制完整提示词
        ↓
人 · ChatGPT 会员   复制提问，必要时用网页搜索
        ↓
本刀·贴回复         操作台提交回复
本刀·管线           解析 + 覆盖/准确性 → 隔离四对象候选
本刀·确认           设为 library current
        ↓
知识源管理·浏览     WB-01
知识源管理·选择     WB-02：选 family、lock_mapping
        ↓
投影产物输出        WB-03：按映射生成并上架
```

相对 ADR-002：本刀补的是知识源**生成**。ChatGPT 是人用的会员工具，不是服务器权威。四卡仍只在 WB-02 之后出现。

## 4. 已锁定产品决定

| 决定 | 值 |
| --- | --- |
| 编译主产物 | 四对象知识源 revision，不是 generation-input |
| 推理位置 | 人 + ChatGPT 会员；服务器无 LLM、无 API |
| 操作台职责 | 扩完整提示词 + 收回复 + 管线编译 + 确认 current |
| 实现路径 | `compile-intent`；无 claim/租约 |
| 短输入 | `subject`（学习对象）+ `goal`（目标）；不是一长段自由 prompt |
| 完整提示词 | 服务器按版本化模板填出来，供复制；操作员不手写生产规范 |
| 回复合同 | 提示词要求输出与 authoring 夹具同形的结构化稿；解析失败则 `failed` |
| 入库 | 操作员确认「设为 current」；未确认不进 library |
| slug | 操作员给出；须尚无 current；另禁 `spider-gwen` |
| 年龄 | intent 不收年龄；命题保持年龄中性；AGE-01 仍在 WB-03 生成时生效 |
| 重试 | 同一 intent：`failed` 或退回后可再贴回复；确认 current 后不可重试 |
| 覆盖 | 本路径启用 `source-intake-search-v1`（ChatGPT 网页搜索写入 locator）；`compile_authoring_request` CLI 仍禁止 search |
| Projection | authoring 请求 `projection: {}`；四对象 `projection-spec` 仍须通过合同校验（不能是 JSON `{}`），由管线按 KNOW-04 同样规则推导 recommended family；不写 `mapping.json`；family 锁定仍由 WB-02 |
| 验收主题 | 新 slug `cat`；loopback；不写生产 library |
| 交付面 | 本机操作台 + 显式注入的 library 根；现网应用 / Nginx / 生产 library 不改 |

## 5. compile-intent

操作员用 admin token `POST` 创建一条 intent。短输入与 slug 创建后不可变；完整提示词由服务器生成，也不可被操作员改写。

| 字段 | 规则 |
| --- | --- |
| `intent_id` | 服务器签发；形如 `ci_` + 小写 hex |
| `topic_slug` | 操作员给出；合法 slug；该 slug **不得已有 current** |
| `subject` | 学习对象短名；UTF-8；空串拒绝；上限 200 字 |
| `goal` | 学习目标短句；UTF-8；空串拒绝；上限 2 KiB |
| `prompt_template_id` / `prompt_template_sha256` | 当时生效的模板身份；进入 intent 快照 |
| `expanded_prompt` | 模板填入 `subject` / `goal` / `slug` 后的完整提示词；只读 |
| `created_at` / `actor` | 创建者；须为人类 actor，禁止 `machine` / `qa-01-v1` / `publish-01-v1` |

禁止：intent 带年龄、family、mapping、图片；禁止操作员上传自己改过的「完整提示词」冒充模板输出。

slug 已有 current → `COMPILE_SLUG_EXISTS`。非法 slug → `COMPILE_SLUG_INVALID`。`spider-gwen` → `COMPILE_SLUG_FORBIDDEN`。KNOW-04 六主题已有 current，走 `COMPILE_SLUG_EXISTS`。同一 slug 若已有非终态 intent（`open` / `compiled` / `failed`）→ `COMPILE_INTENT_ACTIVE`。

创建可用幂等键：同一 `Idempotency-Key` + 相同 body 返回同一 `intent_id`。不同 body 同键 → 失败关闭。

### 5.1 提示词模板

模板是服务器受治理文件，不是 ChatGPT 系统记忆。至少要求回复：

- 输出一份可解析的 authoring JSON（与 `examples/authoring/*.json` 同形的字段：分类、units、propositions、sources、scope）；
- 命题年龄中性；不写四卡槽、COPY、字号；
- `projection` 不要填；
- 用网页搜索找机构页，写入 `locator` + `intake.method=search` + `query` + `tool`；禁止发明 locator；
- entity 默认覆盖七面，缺面须显式 unresolved。

模板变更必须改 `prompt_template_id` 或内容 digest。已创建 intent 继续使用创建时快照的 `expanded_prompt`，不随新模板漂移。

## 6. 状态与重试

```text
open → compiled → current
        ↘ failed
open ← failed 后重试（再贴回复）
open ← compiled 后操作员退回候选
cancelled 终态（确认前可取消）
current 终态（不可重试）
```

| 状态 | 含义 | 谁可推进 |
| --- | --- | --- |
| `open` | 完整提示词已生成，等待贴回复 | admin 提交回复 |
| `compiled` | 管线已过门，待确认 | admin 确认 current，或退回 `open` |
| `failed` | 回复无法解析或未过覆盖/准确性 | 再贴回复（视为重试）或退回后重贴 |
| `cancelled` | 确认前取消 | 终态 |
| `current` | 已 ingest 且 current 指向该 revision | 终态 |

重试**不**改 `intent_id` / `subject` / `goal` / `topic_slug` / `expanded_prompt`。每次接受新回复必须丢弃上一份隔离候选。`current` 之后要改知识源，须另立「更改」切片。

无 claim、无租约、无 `COMPILE_LEASE_HELD`。

## 7. 操作台页面

本机 loopback 扩展 WB-01，不改公网画廊。HTML 壳仍不得内嵌 `subject` / `goal`、完整提示词、回复、命题、来源 locator。

| 路径 | 作用 |
| --- | --- |
| `/card-os/ops/` | 既有主题列表；增加「编译新主题」入口 |
| `/card-os/ops/compile` | 表单：slug + 学习对象 + 目标 |
| `/card-os/ops/compile/{intent_id}` | 展示可复制完整提示词；粘贴回复；状态、预览、确认 / 退回 / 取消 |
| `/card-os/ops/{topic}` | 确认 current 后走既有详情（WB-01/02/03） |

`open` / `failed`：主操作是「复制提示词」和「提交回复」。`compiled`：预览单元 / 命题 / 来源标题，确认或退回。确认按钮仅 `compiled` 可用。请求体必填人类 `actor`（界面默认 `owner`，可改，不得空）。

Token 仍放 `sessionStorage`，规则与 WB-01 相同。完整提示词只经 admin JSON 到达页面，供复制；无 token 的 HTML 源码不得含提示词正文。

## 8. 鉴权

只要一把 `admin` 钥匙。人既扩词也贴回复，也确认 current。本刀不发执行器 token。

| 主体 | scope | 允许 | 禁止 |
| --- | --- | --- | --- |
| 操作员 | 既有 `admin` | 建 intent、读完整提示词、提交回复、读预览、确认 current、退回、取消 | 把未过门回复写成 current；改模板快照 |

已发布 Skill `0.1.1` 的 `read` / `submit` 不能打 admin 编译面。不新增 `knowledge-compile-v1` capability。

无 token：JSON 不得 200 空成功；HTML 壳不得含提示词或命题。不新增公网匿名写入。不新增 Nginx location（走既有 `/card-os/api/` 与 `/card-os/ops/`）。

## 9. HTTP

Admin（`Authorization: Bearer` admin，前缀 `/card-os/api/v1/admin/knowledge-compile`）：

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/` | 创建 intent；body `topic_slug`、`subject`、`goal`、`actor`；返回 `expanded_prompt` |
| GET | `/{intent_id}` | 状态 + `expanded_prompt`；`compiled` 时含预览摘要；无则 `COMPILE_NO_INTENT` |
| POST | `/{intent_id}/reply` | body `{"reply":"...","actor":"..."}`；`open` 或 `failed`；过门 → `compiled`，否则 `failed` |
| POST | `/{intent_id}/confirm-current` | body `{"actor":"..."}`；仅 `compiled`；ingest + set current |
| POST | `/{intent_id}/return` | `compiled` 或 `failed` → `open`；丢弃候选 |
| POST | `/{intent_id}/cancel` | 确认前取消 |

没有执行器前缀，没有 `claim` / `PUT candidate`。

`reply` 上限 256 KiB UTF-8。过大 → `COMPILE_REPLY_TOO_LARGE`。不能解析为 authoring 对象 → `COMPILE_REPLY_INVALID`，状态 `failed`，library 不变。

CLI 与 HTTP 同一函数。测试可只跑 CLI（夹具回复，不接 ChatGPT）。library 根必须由调用方显式注入。HTTP 本机验收把 library 指到临时/夹具目录，**不得**复用现网 KNOW-04 正在服务的 knowledge-library 路径。

## 10. 管线：回复 → 候选

`POST .../reply` 只做确定性工作：

1. 把回复解析为 authoring 请求对象（JSON；允许围栏代码块；围栏外或无围栏时允许说明文字，但不得再有第二份 `{` 对象）。解析后做**确定性键别名与结构折叠**（见 §10.1），再交给 `compile_authoring_request`；
2. 校验 `topic` / slug 与 intent 一致，不一致 → `COMPILE_REPLY_INVALID`；
3. 走与 `compile_authoring_request` 相同的四对象编译，但本路径放行 `intake.method=search`；
4. 覆盖 + 准确性失败关闭；
5. 写出隔离候选。回复里的 `projection` 在编译前清成 `{}`，使 family 由既有 `select_projection_family` 推导，与 KNOW-04 一致；不得采用回复自带的四卡槽位。不写 `mapping.json`。

| 对象 | 本刀规则 |
| --- | --- |
| `knowledge-core` | 闭合；分类受 KNOW-01 词表约束；entity 默认七面 |
| `learning-spec` | 由管线按 Core 推导 |
| `projection-spec` | 合法四对象文档；authoring 请求里的 family/槽位一律丢弃后再编译，使结果与 KNOW-04「请求 `projection: {}`」相同。不得把回复里的四卡 mapping 写进 current |
| `manifest` | pack / kernel / overlay id+sha、intent_id、`prompt_template_sha256`、候选摘要 |

`source-intake-search-v1` 在本路径**启用**：每条 Source 须有 `locator`、`intake.method=search`、`intake.query`、`intake.tool`、独立 `retrieved_at`。禁止发明 locator；禁止把搜索摘要当作 `canonical_claim` 而不建 Source。

服务器**不**联网抓页、不跑 ChatGPT。准确性内核检查记录是否闭合，不证明页上真有那句话。ChatGPT 网页搜索发生在会员会话里，由回复把 locator 带回来。

`compile_authoring_request` CLI 保持 KNOW-03 §8.8：结构化夹具编译仍不得 search。本刀只放行 compile-intent 的 reply 校验器。

### 10.1 ChatGPT 回复归一（API-01-TPL）

提示词模板必须列出与 `examples/authoring/rabbit-real.json` 同形的必填键。同时，解析层兼容会员模型常见的**仍为结构化 JSON**的偏题形态，避免每次人工改写。允许且仅允许：

| 输入形态 | 归一 |
| --- | --- |
| 围栏前说明、` ```JSON `、无围栏但正文是一个对象 | 取出唯一 JSON 对象 |
| `sources[].id` / `publisher` / `source_type` | `slug` / `creator` / `kind`（未知 `source_type` → `article`） |
| 命题 `id` / `canonical_claim` / `source_ids` | `slug` / `claim` / `source_slug`（取第一项）；`evidence_locator` 来自对应 Source；缺的 `unknowns`/`confusion_boundary` 填空列表；`safety` 面若缺 `safety_scope` 则**复用该命题已有 claim**，不另写新句 |
| 缺 `units`，但有 `coverage.facets` + 顶层 `propositions`（带 `facet`） | 按 facet 折叠成 `units`（`coverage_facet` = facet；不发明 question 文案以外的主张） |
| 缺 `learning`，但有 `learning_goal` / `audience` | 填 `learning` 合同键；`goal` 用 `learning_goal` |
| `classification` 为分类学（`entity_type=mammal` / `class=Mammalia`）而无 KNOW-01 键 | 映射为 `life` + `entity` + `animal/mammal` |
| 缺 `topic.scope_type` / `projection` / Source 许可与质量槽 | `composite` / `{}` / 固定非主张默认值 |
| 额外顶层键（`coverage`、`scope`、`audience`、`authoring_constraints` 等） | 丢弃，避免 `AUTHORING_UNDECLARED_FIELD` |

禁止：从散文抽命题；发明 `claim`、locator、`safety_scope` 句子；把无法映射的自造键伪装成过门。折叠后仍缺合同键 → 既有 `AUTHORING_*` / `COMPILE_REPLY_INVALID`，状态 `failed`。

覆盖缺口 → `CORE_COVERAGE_GAP`。未sourced 命题 → `CORE_ACCURACY_GAP`。不得为过门而发明命题。

验收 `cat` 按 `life + entity + animal/mammal`、无 paleontology overlay。

不得把四卡槽、COPY、字号、区高写入 Core。`TEMPLATE_GAP` 只在日后 convert 时出现，不阻断本刀 current。

## 11. 确认入库

`confirm-current` 同时满足才继续：

| 条件 | 失败码 |
| --- | --- |
| intent 存在 | `COMPILE_NO_INTENT` |
| 状态为 `compiled` | `COMPILE_NOT_COMPILED` |
| 尚未是 `current` | `COMPILE_ALREADY_CURRENT` |
| slug 仍无 library current | `COMPILE_SLUG_EXISTS` |
| 候选四对象仍过覆盖/准确性门 | 既有 KNOW-03 / authoring 码 |
| body 人类 `actor` 非空且非机器名 | 沿用 WB-03 actor 规则 |

成功：`KnowledgeLibrary.publish` 写入新 revision，并把 `current` 指过去。intent 进入 `current`，记录 `revision` 号。knowledge-core 字节以候选为准，确认步骤不得改命题。

确认后 WB-01 列表出现该 slug。本刀不自动 `lock_mapping`。

## 12. 错误码

| 码 | 含义 |
| --- | --- |
| `COMPILE_SLUG_EXISTS` | slug 已有 current |
| `COMPILE_SLUG_FORBIDDEN` | 本刀禁止的 slug（`spider-gwen`） |
| `COMPILE_INTENT_ACTIVE` | 该 slug 已有未终态 intent |
| `COMPILE_SLUG_INVALID` | slug 非法 |
| `COMPILE_BRIEF_TOO_LARGE` | `subject` / `goal` 超上限 |
| `COMPILE_REPLY_TOO_LARGE` | 回复超过 256 KiB |
| `COMPILE_REPLY_INVALID` | 回复不是可解析的单一 authoring 对象，或 slug 不一致 |
| `COMPILE_NO_INTENT` | intent 不存在 |
| `COMPILE_NOT_COMPILED` | 确认时没有可确认候选 |
| `COMPILE_ALREADY_CURRENT` | 已经确认过 |
| `CORE_COVERAGE_GAP` / `CORE_ACCURACY_GAP` / `INTAKE_*` | 沿用 KNOW-03；本路径允许 search intake |
| `OPS_NOT_FOUND` | 沿用 WB-01 |

鉴权失败继续使用既有 AUTH 码。不再使用 `COMPILE_LEASE_HELD` / `COMPILE_CAPABILITY_MISSING`。

## 13. 与 2026-07-31 的关系

[可信上游编译器](2026-07-31-cognitive-card-trusted-upstream-compiler-design.md) 保持 Approved，合同对象仍是 sealed generation-input 与 compiled-job。本文件**不重写、不废止**该设计。

本刀也不实现那份设计里的 Codex claim 执行器。ChatGPT 会员会话留在浏览器里，操作台只提供可复制提示词和回复入口。

| | 2026-07-31 | 本刀 |
| --- | --- | --- |
| 主产物 | generation-input + packet | 四对象知识源 |
| 推理 | Codex 领取 packet / 未来 API | 人复制到 ChatGPT 会员 |
| 入库 | 候选卡片 / production-record | library current |
| 本里程碑 | salvage IMPL-1..4 后置 | 队列第 19 项 |

后续若改走模型 API 或 Codex 自动领取，须另立会话。不得把本刀 current 偷偷当成 generation-input。

## 14. 验收

本机：显式 library 根（临时或夹具，不是现网 KNOW-04 路径）+ 本机操作台/CLI。测试用夹具 `subject`/`goal` 与夹具回复，**不**要求本刀会话内打开 ChatGPT。不安装到现网。

必须成立：

1. 对已有 current 的 slug（含 `rabbit`）创建 intent 失败；六主题 Core 字节不变。
2. 对 `cat` 创建 intent 成功；GET 返回非空 `expanded_prompt`，其中含 `subject`/`goal` 与覆盖/search 约束；无 token 的 ops 壳不含提示词。
3. 贴上过门的夹具回复后状态 `compiled`；此时 library 仍无 `cat` current。
4. 贴无法解析或缺 Source 的回复 → `failed`；library 仍无 current。
5. `actor=owner` 确认后：`cat` current 存在；无 `mapping.json`；WB-01 能列出并打开；来源含 search intake 字段。回复里若带 four-card 槽位，current 的 projection 不得采用那些槽位。
6. `failed` 或退回后同一 `intent_id` 可再贴回复；旧候选不能被确认。
7. 现网应用、Nginx、生产 library、画廊 ACCEPT-01 包摘要不被本刀改写。

本刀完成不等于 `cat` 已四卡上架。操作员**可以**在确认后手跑 WB-02/03，那是相邻路径，不是本文件的完成条件。

测试：intent 创建/幂等、slug 门禁、模板扩词稳定性、回复解析成败、search 放行与 CLI authoring 仍禁 search、确认 ingest、退回重试、既有 WB-01/02/03 focused 回归。不要求完整 suite 清零既有 real-uvicorn 502。不要求生产安装。不要求真实 ChatGPT 会话。

## 15. 实现落点

权威仓库：server `knowledge-pipeline-v1`。kids 仓：本设计、路线图、任务/交接、文档地图。

优先：compile-intent 与提示词模板、`expanded_prompt` 生成、reply → 四对象管线（覆盖 + search intake）、ops 编译页（复制提示词 / 粘贴回复）、confirm → `KnowledgeLibrary.publish`。不接 API，不接 Skill claim，不改 Nginx，不写生产 library，不改未提交的 WB-03 加权代码行为。
