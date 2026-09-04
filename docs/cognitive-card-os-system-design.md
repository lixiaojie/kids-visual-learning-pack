# Cognitive Card OS 整体设计

状态：已确认，作为 Cognitive Card OS 的规范性总入口  
确认日期：2026-07-13  
适用范围：知识体系、模板、生成执行、服务器、客户端、资产、打印、发布与运维

## 1. 文档地位

本文回答 Cognitive Card OS 的整体边界、权威来源、组件关系和交付标准。子系统可以拥有独立设计与实施计划，但不得与本文冲突。

文档优先级如下：

1. 本文定义系统级边界和跨子系统合同。
2. 子系统设计定义其内部行为。
3. 实施计划定义代码任务、测试和提交顺序。
4. 动态进度只在 [Cognitive Card OS 路线图](cognitive-card-os-roadmap.md) 中维护。

当前订阅执行子系统由以下文档补充：

- [ChatGPT Pro 订阅客户端执行设计](superpowers/specs/2026-07-13-cognitive-card-pro-subscriber-execution-design.md)
- [订阅客户端执行基础实施计划](superpowers/plans/2026-07-13-cognitive-card-subscriber-execution-foundation-plan.md)
- [个人服务器生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md)

## 2. 产品目标

Cognitive Card OS 由服务器管理一个可追溯的 Knowledge Core，再将其分别用于学习设计和多种 Projection family。Knowledge Core 固定事实、范围、来源、未知项与安全边界；Learning Plan 和 Learning Path 决定面向特定受众的学习负荷；Projection 只组织已被学习路径引用的内容，不能新增事实。

首个兼容 Projection family 是 `four-card`，它继续把一个已锁定的学习路径投影为可追溯、年龄适配、中英文一致并可打印的四卡知识包：

1. 中文观察卡；
2. 英文观察卡；
3. 中文知识卡；
4. 英文知识卡。

系统需要支持自然对象、古生物、地点、基础设施、历史、过程、现象、抽象规则等不同领域和概念形态。不同领域和形态可以使用适合自己的 Projection family；同一 family 下保持稳定结构，不为单个对象任意改造模板。现有四卡运行时和 package 保持兼容，历史包只在受控迁移中映射和验证，不自动升级。

首个可用版本以登录 ChatGPT Pro 的 Codex 客户端执行模型生成，不要求 OpenAI API Key。个人服务器负责统一知识规则、任务、模板、资产、QA、发布和跨终端同步。

Cognitive Card OS 将逐步替换现有 `kids-world` 知识网站并成为新的知识内容与发布入口。旧站中可证明来源和质量的内容与图片可以迁移，但旧网页结构和旧格式不直接成为新系统的权威模型。`spider-verse` 与 `paw-patrol` 保留为旧版主题馆，不强制转换为四卡知识包。

## 3. 核心原则

### 3.1 一个受治理 Knowledge Core，多种 Projection

- 先建立 Knowledge Core 中稳定的 `FACT`、`SEMANTIC CORE`、Evidence、Knowledge Scope 和 `proposition_id`，再建立 Learning Plan、Learning Path 与 Projection。
- Projection 只能消费 Learning Path node 和已引用命题；展示或渲染变化不得回写或新增 Knowledge Core 事实。
- `four-card` family 中，CN 与 EN 可以使用不同句式和难度，但必须保持事实、确定性、来源、未知项和安全边界一致。
- `four-card` family 中，观察任务和 COPY 必须来自同语言知识卡上实际显示的命题文本；知识卡不放置抄写或描摹任务，COPY 只属于观察卡行动区。

### 3.2 分类定义 Knowledge Scope，Learning Plan 决定学习负荷

分类首先形成 Knowledge Scope，而不是唯一 Projection router：

```text
primary_domain
+ primary_form
+ object_subtype
```

- 主领域和主形态各有且只有一个。
- 次领域和次形态只能扩展已声明的 Knowledge Scope 单元，不能伪造新的事实权威。
- audience、language、depth、duration、usage context 和学习目标属于 Learning Plan；Learning Path 决定顺序、先修和练习。
- 同一概念可针对不同年龄与语言建立独立 Learning Plan，但不得混合难度或改写 Knowledge Core。
- 当前正式年龄配置为 `age-3-4` 与 `age-5-6`；未来 8、10、15 岁需要分别新增并验证年龄配置，而不是扩宽现有区间。

### 3.3 内容锁先于图像和正式产物

`final content lock` 固定以下内容或其摘要：

- `knowledge-core`、`learning-spec` 与 `projection-spec` 的身份、revision 和 canonical 摘要；
- Knowledge Core 的 FACT、SEMANTIC CORE、命题、来源与 Knowledge Scope；
- Learning Plan、Learning Path、Projection Blueprint 与 Renderer Binding；
- Projection 所需的 COPY、图像/其他资产要求及其对应关系；
- 未知项、安全边界和混淆边界；
- audience、年龄、语言、模板族和结构指纹。

图像提示、排版、PDF、QA 和发布只消费内容锁，不能在后续阶段新增事实或改写锁定对象。

### 3.4 服务器是生产权威，客户端只是模型执行器

- 服务器拥有分类、模板、内容锁、任务状态、候选验收、渲染、QA、发布和资产历史。
- 客户端只领取不可变生成包并返回候选文件与来源记录。
- 客户端生成物在服务器验收前不是正式资产。
- ChatGPT Cookie、内部 Token 和浏览器会话不得上传或保存到服务器。

## 4. 系统架构

```text
八个逻辑层（服务器权威）
  1. Evidence / Source：来源身份、证据片段、质量与使用边界
  2. Proposition Graph：事实命题、关系、未知项、安全与时间状态
  3. Knowledge Scope：知识单元、纳入、排除与未解决问题
  4. Learning Plan：受众、语言、深度、时长、目标与使用场景
  5. Learning Path：节点、顺序、先修、问题和练习
  6. Projection Blueprint：family 与内容槽位
  7. Renderer Binding：目标媒介、组件映射、资产要求、能力与 QA profile
  8. Artifact Package：manifest、锁、QA 与不可变产物

Knowledge Core = 第 1–3 层。Operations / Governance 是横跨八层的责任，
负责 revision、复核、freshness、发布、备份与审计，不是第 8 层。
                                  |
                                  v
客户端接入层
  薄 Skill、CLI、只读 MCP、浏览器手动上传
  ChatGPT Pro 仅在客户端执行；客户端只执行服务器签发的 executor-neutral GenerationPacket
```

### 4.1 知识、学习与 Projection 控制层

职责：

- 维护受控领域、概念形态和领域自有 subtype；
- 为不同 `primary_domain + primary_form` 提供领域知识轴和 Knowledge Scope 输入；
- 构建 FACT、命题、语义核心、来源、未知项、安全边界和内容锁；
- 分别维护 Learning Plan 的年龄和语言适配器，以及 Learning Path；
- 为同一 Projection family 提供稳定 Blueprint、Renderer Binding 与结构版本；
- 在模板缺失或分类有实质歧义时停止，而不是猜测。

Projection family 结构升级使用新的 family major；兼容调整使用语义化 `template_version`。兔子必须形成 `life + entity + animal/mammal` 的 Knowledge Scope，不能以私有页面骨架替代受治理范围。

### 4.2 服务器执行核心

职责：

- 持久化任务、生成包、租约、候选结果和审计事件；
- 签发带内容锁、模板和年龄身份的 `GenerationPacket`；
- 支持客户端认领、超时释放和中断恢复；
- 校验客户端、包、摘要、声明路径、媒体类型、大小和幂等键；
- 将通过校验的候选送入服务器验证，而不是直接发布。

服务端实现位于私有仓库 `lixiaojie/cognitive-card-server`。首个生产基线为 `0.3.1`：应用核心通过薄 HTTP 适配层提供 capability、认证和规范化锁定任务 API，并部署在 `https://www.yutou.space/card-os/`。该 API 不负责把自由主题直接编译为知识卡；自由输入仍须先经过受信任的分类、事实、模板和内容锁流程。

### 4.3 客户端接入层

首版支持以下表面：

| 表面 | 生成 | 上传 | 查看 | 说明 |
| --- | --- | --- | --- | --- |
| Codex app/CLI/IDE | 是 | 是 | 是 | 本地薄 Skill 调用 HTTPS |
| ChatGPT Pro 网页 | 人工 | 浏览器上传 | 是 | 不依赖 MCP 写操作 |
| 手机或平板浏览器 | 否 | 手动上传 | 是 | 响应式门户 |
| 普通终端 | 否 | 是 | 是 | CLI/HTTPS 客户端 |
| MCP | 否 | 否 | 是 | 首版只读 |

薄 Skill 只包含触发、输入收集、协议发现、本地校验、领取/上传帮助、摘要校验和错误映射。知识注册表、完整模板库、生产资产、ChatGPT 凭据和渲染器不放在薄 Skill 中。

### 4.4 Artifact、生产与发布层

职责：

- 从同一内容锁生成 family 定义的 Artifact；`four-card` family 继续生成固定顺序的四张卡；
- 使用受控排版生成与 family 对应的文本忠实版本和打印 PDF；
- 对图像执行视觉、事实、文本和版面 QA；
- 保存 manifest、来源、摘要、模板指纹和 QA 报告；
- 通过人工复核后发布不可变 package revision；
- 新修改生成新版本，不覆盖历史发布物。

### 4.5 资产与运维层

首版采用：

- SQLite 保存事务性元数据和审计；
- 服务器文件系统保存按摘要寻址的不可变候选及正式资产；
- HTTPS 提供 API、门户、下载和 Skill 发布；
- 定时备份元数据、资产、发布 manifest 和配置；
- 容量水位、备份新鲜度、任务积压、错误率和证书到期进入监控。

当并发、数据量或高可用需求超过单机边界时，才评估 PostgreSQL、对象存储或队列；首版不预先引入这些复杂度。

## 5. 权威来源与仓库边界

| 位置 | 权威内容 | 不应承载 |
| --- | --- | --- |
| `kids-visual-learning-pack` | 总设计、路线图、卡片产品与展示资产 | 运行时密钥、生产数据库 |
| `cognitive-card-server` | 服务端代码、协议、迁移、API、认证、验收和发布逻辑 | ChatGPT 会话、个人浏览器状态 |
| 个人服务器 | 运行时数据库、不可变资产、Skill 发布、备份与日志 | 未版本化的唯一模板规则 |
| 本地 `cognitive-card-os` | 薄客户端发布版本 | 可变知识库、完整模板库、生产历史 |

目标服务地址为 `https://www.yutou.space/card-os/`。服务器主机地址属于部署配置，不进入浏览器产物和公开协议；客户端通过域名发现服务。

## 6. 统一数据流

```text
用户请求
-> INPUT CHECK
-> Knowledge Core（FACT / SEMANTIC CORE / proposition_id / evidence）
-> Knowledge Scope（纳入、排除、未知项）
-> Learning Plan（audience / language / depth / duration）
-> Learning Path（顺序、先修、问题、练习）
-> Projection Blueprint（family / slots）
-> Renderer Binding（capabilities / QA profile）
-> `knowledge-core` + `learning-spec` + `projection-spec` final content lock
-> 分阶段 executor-neutral GenerationPacket
-> Codex + ChatGPT Pro 生成候选
-> 服务端隔离、跨对象 closure、Artifact manifest 校验、审计
-> family 对应渲染、严格 QA、人工复核、不可变发布
-> 门户查看、下载和打印
```

MVP 的四个物理治理对象为 `knowledge-core`、`learning-spec`、`projection-spec` 与 `manifest`；Artifact 文件由 manifest 闭包声明，不引入第五个治理对象。服务中断、客户端退出或租约过期不得丢失任务历史。恢复以服务器持久化状态为准，不以某个终端的聊天上下文为准。

## 7. 年龄、语言与同类一致性

### 7.1 单主版本原则

每次 Learning Plan 根据提供年龄选择一个主版本。只有明确要求多个年龄段且跨度足够大时，调用方才展开为多个单年龄带 Learning Plan。每个 Plan 独立生成、验证和发布，但引用同一 Knowledge Core 时不得改写事实。

### 7.2 年龄升级策略

Learning Plan 中的年龄和语言配置控制：

- 句子长度和词汇难度；
- 观察密度和比较复杂度；
- COPY、描摹、口头复述和独立阅读负荷；
- 因果、系统和证据解释深度。

年龄或语言配置不得改变事实命题、来源、未知项或安全边界。新增 8、10、15 岁配置前，分别建立语言、任务、认知负荷和 QA 规则及跨对象夹具。

### 7.3 同类模板一致性

一个 Projection family 至少使用两个同类对象验收。`four-card` 的 `animal/mammal` 首组验收对象为兔子和另一个哺乳动物。允许内容槽位因对象不同而为空或填充，但固定页面、锁定区、任务槽语义和结构指纹必须一致。

## 8. 协议和身份

首版协议对象：

- `cognitive-card-generation-packet-v1`；
- `cognitive-card-generation-result-v1`；
- 服务器 capability 和 protocol discovery；
- Skill release manifest；
- package manifest 与 immutable artifact identity。

Card OS 使用自己的身份，不转发 ChatGPT 身份。初始权限范围为 `read`、`submit`、`review` 和 `admin`。浏览器使用安全的 HTTP-only 会话；CLI 与薄 Skill 使用可撤销、可轮换的 scoped token，并存入操作系统凭据存储或受保护配置。

## 9. 错误、安全与恢复

- 所有跨进程错误使用稳定错误码并携带可操作说明。
- 上传先进入隔离区，验证通过后才成为接受的候选。
- 错误日志、数据库、manifest 和发布包不得包含 ChatGPT Cookie、OpenAI 内部 Token 或 Card OS 原始令牌。
- 客户端撤销必须同时阻止首次提交和幂等重放。
- 任务重试不得产生重复逻辑资产或重复审计状态。
- 自动化模式 `server_api_autonomous` 默认关闭；没有单独批准的凭据、预算和密钥方案时不得启用。
- 备份必须覆盖数据库、不可变文件、发布 manifest 和恢复所需配置；恢复演练必须验证摘要和任务连续性。

## 10. 测试与发布门禁

每个子系统至少具备：

- 单元测试：状态、路由、校验和错误码；
- 集成测试：数据库、文件、API、认证和恢复边界；
- 协议兼容测试：服务器与薄 Skill 的版本协商；
- 安全测试：凭据字段、路径、摘要、大小、撤销和权限；
- 代表性端到端测试：兔子 `age-5-6` 中英文打印包；
- 同类一致性测试：第二个哺乳动物使用相同模板族；
- 跨终端测试：多终端阶段由 `SKILL-03` 承担；单人 MVP 不要求第二台独立 Codex 安装（[ADR-004](decisions/ADR-004-single-operator-main-flow.md)）；
- 运维测试：服务重启与本机备份恢复；容量告警和证书检查不作为单人主路径门禁；

任何正式包都必须通过共享的跨对象 closure：对象引用、来源、未知项、安全边界、资产声明、两级锁和 manifest 均可复算；随后通过所属 Projection family 的结构、Renderer Binding、图像、打印和 QA 门禁，才进入人工复核。`four-card` family 额外要求四页顺序、共享命题、年龄/语言一致与 COPY 来源。

## 11. 交付阶段

已建立的基础能力（精确状态、依赖和遗留条件以路线图为准）包括：订阅执行核心、现网 HTTPS 锁定任务 API、protocol discovery、Skill 发布注册表和服务器部署。它们不是 `KNOW-02` 之后才开始的阶段；现有 API/持久化继续作为它所依赖的基线。

从当前状态起，按单人知识主路径推进（精确状态以路线图为准；[ADR-004](decisions/ADR-004-single-operator-main-flow.md)）：

1. `KNOW-02` Knowledge Core 四对象纯合同：已完成。
2. 本地 authoring MVP：已完成。
3. 服务器 revision、current 与 freshness 管理及 loopback HTTP 接线：本地完成，未进生产。
4. **`BROWSE-01` 知识浏览与 Projection 确认（确认点 1）**：本地已完成（静态 HTML + 只读 GET）；未 merge 进生产；不等于 PORTAL-01。
5. **`CONV-01` four-card converter** 与 **`RUN-01` 本机执行接合密封**：本地已完成（显式 four-card current → 接合 generation-input → loopback compiled-job / executor → validator 退出 0）；未 merge 进生产；转换器不写出 production-record 本体。
6. **`AGE-01` 年龄与中文表达适配**：本地已完成（`age-3-4` / `age-5-6` 服务器适配器；命题、确定性、安全边界不随年龄改写）；未 merge 进生产。
7. **`RENDER-01` 四卡排版与 A4 PDF**：本地已完成（内容锁 + `copy_plan` → 四页 PNG 与 A4 PDF）；已本地提交 `1ef6edc`；未 merge 进生产。
8. **`QA-01` 严格 QA 与人工复核**：本地已完成（机器 QA 通过后才 `awaiting_review`；人工决策绑定 actor 与审计）；已本地提交 `37a5927`；未 merge 进生产。
9. **`PUBLISH-01` 不可变 package**：本地已完成（只消费 `approved` 报告；revision 不可覆盖；撤回/替代保留历史）；已本地提交 `7a127b4`；未 merge 进生产。
10. **`ACCEPT-01` 兔子端到端**：本机已完成（正式输入到四卡、PDF、QA、不可变 package；本机可查看同一 lock）；已本地提交 `10b14c8`；未 merge 进生产。不扩 PORTAL。
11. **`KNOW-01` 分类注册表与 authoring 接入**：本机已完成（`classification-registry-v1`、覆盖矩阵、authoring 受控分类、convert 可省略 `--request`）；已本地提交 `4083ce7`；未 merge 进生产。
12. **`TMPL-01` 模板族注册表与跨对象夹具**：本机已完成（`template-registry-v1`、稳定四页骨架、`TEMPLATE_GAP`、每 family 两对象夹具）；已本地提交 `cbaf2b4`；未 merge 进生产。
13. **`PORTAL-01` 已发布 Artifact 只读画廊**：本机已完成（catalog 静态 HTML + loopback `/card-os/`；公开只看 public current；不替代 BROWSE-01；不写 Knowledge Core）；已本地提交 `fd696c2`；未 merge 进生产。
14. **`SITE-01` 知识入口切换**：仓库内已完成（根入口主 CTA 指向 Card OS 画廊；旧 `kids-world` 降为冻结档案；Nginx snippet 反代画廊 HTML 与 `/card-os/packages/`）；未现网应用。见 [ADR-005](decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md)。
15. **`SITE-02` 旧 URL 映射与一次部署回滚**：仓库内已完成（短 hash / query 打开冻结主题；独立路径替代说明页；`activeMode=parallel` 一次部署回滚主 CTA）；未现网。
16. **`DEPLOY-02` 现网落地试点**：Done。现网 `www.yutou.space/card-os/` 为 PORTAL-01 画廊；应用提交 `fd696c2`（版本号仍 `0.3.1`）；未 merge server `main`。不补知识源 schema。
17. **`WB-01` 令牌操作台只读知识源**：Done。现网 `/card-os/ops/`；应用 `115377b6da16a02e5aea5b73879ad7bb7ee5b2cd`（版本号仍 `0.3.1`）；library `rabbit` 为 AUTHOR-02；画廊仍是 ACCEPT-01。未 merge server `main`。见 [操作台设计](superpowers/specs/2026-08-31-operator-knowledge-workbench-design.md)。
18. **`WB-02`**：Done（本机 server `5c11880`；未现网）。操作台映射方案确认。见 [映射方案确认](superpowers/specs/2026-09-01-operator-mapping-scheme-design.md)。旧文字填满稿仍 Parked。
19. **`KNOW-03` 知识源覆盖与准确性**：Done（本机 `7aaeb2b`）。可插拔 pack/overlay；七主题兼容套件；吸收 Skill 知识生成、忽略投影。见 [知识源覆盖](superpowers/specs/2026-09-01-entity-knowledge-coverage-design.md)。
20. **`KNOW-03-prod` 现网装上 KNOW-03 应用**：Done。现网 `current`=`7aaeb2b80e591f348c54eb35fb18793e213c5122`（版本号仍 `0.3.1`）；library 当时仍为 AUTHOR-02；Nginx 未 reload。未 merge server `main`。见运维记录第 12 节。
21. **`KNOW-04` 兼容套件上库**：Done。生产 library 六主题 current（不含格温）；`rabbit` current=`revision-0002`；应用仍 `7aaeb2b`；Nginx / 画廊未改。见运维记录第 13 节与 [兼容套件上库](superpowers/specs/2026-09-01-knowledge-suite-library-seed-design.md)。
22. **`WB-03`**：Done（本机；`91b7cf3`；未现网）。mapping-artifact 路径 + 加权版式；操作者接受兔子卡基础信息；打印样式后置。见 [按映射生成并上架](superpowers/specs/2026-09-01-operator-mapping-artifact-publish-design.md)、[加权版式](superpowers/specs/2026-09-02-mapping-artifact-weighted-layout-design.md)。
23. **`API-01`**：本机已实施（`91b7cf3`；含 TPL 归一）。操作台扩展提示词 → ChatGPT 会员 → 贴回复 → 四对象 current。见 [本刀设计](superpowers/specs/2026-09-02-operator-free-prompt-knowledge-compile-design.md)。未现网、未 merge `main`。
24. **`LEGEND-01` 投影图例**：spec Approved。server `knowledge-pipeline-v1` @ `f9baf8f` 已本地提交（未 push、未生产）。认知角色凡例约束编译与呈现槽；不改 Knowledge Core schema。见 [投影图例](superpowers/specs/2026-09-03-projection-legend-v1-design.md)。
25. **`IMG-02` 多视图无字资产**：spec Approved。server `knowledge-pipeline-v1` @ `8710914` 已本地提交（未 push、未生产）。IMG-01 isolate 主图并存；额外像素键可选；不经 mapping-lock。见 [多视图无字资产](superpowers/specs/2026-09-03-multi-view-wordless-assets-design.md)。
26. **`RENDER-02` 图例模块铬**：spec Approved，实施计划已落盘。server `knowledge-pipeline-v1` @ `427bf89` 已本地提交（未 push、未生产）。屏幕 HTML 按角色换壳；打印 PNG 不变；三视/剖面/爆炸提示词仍属 IMG-02。不标 `DONE`。精确状态见路线图。见 [模块铬](superpowers/specs/2026-09-04-legend-module-chrome-design.md)。
27. 第二台电脑、加密异地备份、浏览器会话、只读 MCP：**后置**，不作为单人主路径门禁。
28. 第二个哺乳动物一致性验收仍依赖模板族。

各批次的状态、依赖与验收条件只在路线图中更新。

## 12. 网站替换与历史资产迁移

### 12.1 替换范围

- Cognitive Card OS 替换 `kids-world` 的知识内容生产、浏览和发布能力，并在验收完成后成为主入口。
- `spider-verse` 和 `paw-patrol` 保留独立入口，归入“旧版主题馆”。
- 旧 `kids-world` 在迁移期保持只读兼容，不再扩展新的内容模型。
- 新站首先部署在 `/card-os/`，通过并行验收后再切换主入口和配置重定向。

### 12.2 迁移等级

历史资产必须先登记、计算摘要、检查来源并分级：

| 等级 | 条件 | 处理 |
| --- | --- | --- |
| A | 具有现行 manifest、FACT、命题、CONTENT LOCK、四卡、QA，且严格验证通过 | 直接导入为候选 package revision |
| B | 已有结构化内容和四卡，但 schema、模板或 QA 版本较旧 | 升级 manifest、复算指纹并复验后导入 |
| C | 只有旧网页 JSON、图片或双面卡，缺少现行事实与锁定链 | 保留可用素材，以新工作流重建正式 package |
| D | 重复、临时、来源/版权不清、质量不足或不属于四卡产品 | 仅归档，不进入新站搜索和发布 |

任何等级都不允许因为“旧站曾公开展示”而跳过来源、版权、事实和内容锁检查。历史图片可以成为候选视觉素材，但不能单独证明卡片事实。

### 12.3 双轨切换

迁移顺序固定为：

1. 冻结旧知识站的内容结构，只允许必要修复；
2. 扫描工作目录并建立资产来源清单；
3. 对候选文件计算 SHA-256，识别源图、导出图、WebP 和重复副本；
4. 先迁移 A/B 级包，再按优先级重制 C 级主题；
5. 在 `/card-os/` 并行展示已发布的新 package；
6. 当旧站知识入口已切到 Card OS 画廊，且 13 个旧主题具有明确冻结/归档决定（[ADR-005](decisions/ADR-005-knowledge-entry-cutover-without-topic-remakes.md)）后，切换主 CTA；把旧站从可达档案中删除仍要求主题重制；
7. 旧 `kids-world` 保持只读兼容；历史 hash/query 打开冻结主题，独立路径保留替代说明；一次部署可将 `activeMode` 切回 `parallel`（SITE-02）。

发现阶段的资产来源、规模和等级记录在 [历史资产迁移清单](cognitive-card-os-asset-migration-inventory.md)。该清单记录来源事实；服务器正式资产仍以导入后的 package manifest 和不可变摘要为权威。

### 12.4 去重与可追溯性

- 每个导入对象获得稳定 `migration_asset_id`，保留原始路径、原 Codex 任务 ID、文件摘要和发现时间。
- 相同 SHA-256 的副本只保存一个内容对象，但保留全部来源别名。
- PNG 原图、WebP 浏览副本、文字数据和最终 PDF 分别记录角色，不能只凭文件名推断主副本。
- 迁移不修改原文件；正式导入使用服务器隔离区和新的不可变存储键。
- 旧内容若需事实修订，创建新 FACT、CONTENT LOCK 和 package revision，不回写伪造旧 provenance。

## 13. 规范基线与里程碑入口

系统已建立以下不可逆转的架构基线：

- 服务器通过正式域名提供 capability、Card OS 身份和规范化锁定任务 API；生产部署证据、调用和回滚命令见 [个人服务器生产部署与运维记录](operations/cognitive-card-server-deployment-2026-07-14.md)。
- 模型生成仍由登录 ChatGPT Pro 的受信任客户端执行；服务器不需要 OpenAI API Key，也不接收 ChatGPT 身份材料。
- 薄 Skill 必须通过不可变 release、摘要和兼容门禁发布，不能依赖某台电脑上的未发布本地仓库状态。
- 当前 API 不是自由概念创建接口；自由请求必须先形成可验证的分类、事实、模板和内容锁。
- 历史资产必须经过发现、去重、严格 package 验证和受控导入，不能因旧站曾展示而直接成为生产资产。
- [ADR-002](decisions/ADR-002-knowledge-core-and-projection-architecture.md) 已确认一个受治理 Knowledge Core、Learning Plan/Path 与多种 Projection family 的长期分层；[已批准设计](superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md) 定义其合同语义。`KNOW-02` 先验证四个治理对象和闭包，现有 four-card runtime 在过渡期间继续兼容。
- [ADR-004](decisions/ADR-004-single-operator-main-flow.md) 确认当前按单人维护、单人使用跑通知识主路径；第二台电脑、加密异地备份与公网 Portal 后置。确认点 1 由 `BROWSE-01` 本机 CLI 与 `WB-01` 令牌操作台承担，不等于 `PORTAL-01`。

动态状态、下一任务和依赖顺序只在 [Cognitive Card OS 路线图](cognitive-card-os-roadmap.md) 中维护，避免整体设计与执行账本产生两个“当前状态”。

## 14. 变更规则

- 跨子系统边界、权威来源或正式交付合同的修改必须先更新本文。
- 动态状态不得写回本文；状态只更新路线图。
- 子系统设计完成后必须在本文或路线图中建立链接。
- 已失效文档保留历史说明并指向替代文档，不与现行规范并列作为入口。
- 资产迁移状态、重复关系和导入决定必须更新迁移清单；不得只记录在聊天或临时脚本输出中。
