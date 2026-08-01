# Cognitive Card OS 可信自由请求编译入口设计（API-01 修订草案）

状态：修订草案，待用户书面审阅；未获确认前不实施

日期：2026-07-31；修订：2026-08-01

关联：ADR-001、抢救清单与 Block 修复方案（抢救分支 `codex/card-os-salvage-v1`）、服务器 `0.3.1`（`c2a898c`）

## 1. 目标

以过去多轮迭代形成的 `core/` 生产管线为质量基线，使新任务在当前没有模型 API 的条件下，由登录 ChatGPT Pro 的受信 Codex 客户端按照同一套分类、事实、语义、模板、年龄语言、CONTENT LOCK 和输出规范完成生成，并把经过确定性校验的结果上传到服务器。

服务器是**规范、任务状态、输入锁、候选与验收的权威控制面**；客户端是当前的**生成执行器**，不是规范权威。未来接入模型 API 时，增加服务器侧 `ServerApiPipelineExecutor`，复用相同的 core 快照、GenerationPacket、sealed input、GenerationResult 和验证规则，只替换执行位置，不重写生产管线。

本设计的成功标准不是“服务器现在完成全部生成”，而是：

1. 当前客户端生成能够取得并验证完整、版本化的生产规范与任务输入；
2. 客户端和未来 API 执行器消费同一个生成合同；
3. 服务器能够追溯任务使用的快照、输入锁、模板指纹和最终内容锁；
4. 未通过确定性验证的结果只能停留在隔离区，不能进入 QA、评审或发布。

非目标：本批次不实现服务器模型 API、服务器渲染（RENDER-01）、完整视觉 QA（QA-01）、package-v5 发布面（PUBLISH-01）或正式站点替换。

## 2. 已确认决策与边界

- **当前生成位置**：客户端。CLASSIFICATION、FACT、SEMANTIC CORE、双语投影等推理在环步骤由登录 ChatGPT Pro 的受信 Codex 客户端执行。
- **未来生成位置**：服务器 API 执行器。它必须实现与客户端相同的 executor contract，不得形成第二套提示词、模板或验收规则。
- **服务器权威含义**：服务器拥有允许使用的 core snapshot catalog、任务与 packet 状态、sealed input、候选、验证结果和发布资格；不要求服务器当前具备 LLM。
- **薄客户端边界**：已发布 `0.1.1` 的 M1 领取/提交契约不变；自由概念仍不能由不可信薄客户端直接创建生产任务。
- **资产复用**：RENDER/QA/PUBLISH 继续采用 lift-and-harden；每个模块上服务器前通过信任边界重审、运行时钉住、输入面重验三道。

## 3. 方案取舍

| 方案 | 说明 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- | --- |
| A. 本地共享工作区 | compiler 与 executor 在同一客户端共享 sealed input，服务器只收 packet/result | 服务器改动最少 | 不能跨终端领取；未来 API 无法取得相同输入；恢复依赖本机 | 不采用 |
| B. 服务器 sealed input store | 服务器保存不可变 generation-input bundle；客户端和未来 API 通过摘要读取 | 一套合同覆盖当前与未来；可恢复、可审计、可跨执行器 | API-01 需新增受限输入存储/读取面 | **推荐** |
| C. 完整服务器编排 | 现在即实现自由输入、多阶段调度与服务器模型执行 | 长期形态一步到位 | 当前无模型 API，范围和成本过大 | 延后 |

本设计采用 B。公开浏览完整 core snapshot 的端点不属于 B 的必要条件，可继续延期；API-01 只增加执行器取得 sealed input 所需的受限读取面。

## 4. 总体架构

```text
自由概念（用户）
  → Trusted Upstream Compiler（受信 Codex 客户端，无提交凭据）
      · 校验 core snapshot 闭包
      · 执行 INPUT CHECK → CLASSIFICATION → FACT → SEMANTIC CORE → TEMPLATE PROFILE
      · 形成 generation-input-v1（前置生成输入锁）
      · 本地运行 resolver / generation-input validator
  → Deterministic Submitter（独立进程，短期 compiler_import token）
      · 上传不可变 generation-input bundle
      · 原子创建 locked job + GenerationPacket
  → Server Control Plane
      · snapshot catalog / sealed input store / packet / state / audit
  → PipelineExecutor.generate
      · 当前：ClientSubscriptionPipelineExecutor（Codex + ChatGPT Pro）
      · 未来：ServerApiPipelineExecutor（模型 API）
  → production-record-v1 + GenerationResult
  → Server Candidate Gate
      · 文件、摘要、production record 关系闭包验证
      · 通过后 candidate_staged；失败留在隔离区
  → 后续 RENDER / QA / REVIEW / PUBLISH
```

### 4.1 组件职责

| 组件 | 职责 | 不承担 |
| --- | --- | --- |
| Snapshot Catalog | 保存允许使用的不可变 core snapshot 与摘要映射 | LLM 推理 |
| Trusted Upstream Compiler | 调用当前 pipeline executor 的 compile 阶段，把自由概念收敛为 sealed generation input | 持有长期或全权 admin token |
| Deterministic Submitter | 校验 sealed input，完成受限上传与任务创建 | 运行 LLM、修改生成内容 |
| ClientSubscriptionPipelineExecutor | 当前用 ChatGPT Pro 执行 compile 与 generate 两个推理阶段 | 改写规范、选择未授权快照 |
| ServerApiPipelineExecutor | 未来用 API 执行同样两个阶段 | 建立第二套工作流 |
| Candidate Gate | 验证上传字节、schema、摘要和 production-record 闭包 | 自动批准发布 |

## 5. core 权威快照

### 5.1 快照来源与修复

候选来源仍是抢救分支的 `skills/cognitive-card-os/core/`。现有 `source-manifest.json` 有 34 个 `release_files`，但只有 27 个 `recovered_sources` 带内容摘要，因此它只能证明恢复来源和路径/mode 闭包，不能直接充当服务器内容寻址 manifest。

API-01-IMPL-1 必须生成 `cognitive-card-core-snapshot-v1`：

- 除 manifest 自身外，每个成员记录 `path`、`mode`、`size_bytes`、`sha256`；
- 成员按 UTF-8 路径字节升序排列；拒绝绝对路径、`.`、`..`、空段、反斜杠、NUL、symlink 和未声明文件；
- `snapshot_root_sha256 = sha256(canonical_json(member_records))`；
- `snapshot_id = "sha256:" + snapshot_root_sha256`；
- manifest 记录 schema、source identity、origin commit 和生成工具版本，但这些说明字段不进入成员 root digest；
- 导入时从已提交、clean、精确 commit 的 checkout 读取，打开文件后复核 stat，避免 dirty tree 与路径替换。

### 5.2 存放位置

推荐仍放在 `cognitive-card-server` 仓的 `core-snapshots/<snapshot_root_sha256>/`，原因是它需要与服务器部署、备份和回滚共同受治理。`registry_commit` 记录**首次引入该不可变 snapshot 的精确 commit**，后续无关服务器代码提交不改变既有任务的 registry identity。

如果未来 snapshot 发布频率明显高于服务器应用，再把它拆为独立治理仓；迁移时保持 snapshot manifest、root digest 和 registry commit 映射不变。

服务器维护只增不改的 snapshot catalog：

```json
{
  "registry_commit": "<40 lowercase hex>",
  "snapshot_id": "sha256:<64 lowercase hex>",
  "manifest_schema": "cognitive-card-core-snapshot-v1",
  "state": "active|retained"
}
```

## 6. 两级内容锁

当前 packet 生成发生在最终四卡文本完成之前，而 recovered core 的正式 CONTENT LOCK 位于 FINAL/COPY 之后。为避免混用，本设计明确两个不同摘要域。

### 6.1 Generation Input Lock

`cognitive-card-generation-input-v1` 是当前执行器的 sealed input，至少包含：

- normalized user request 与 use location；
- snapshot identity 与 registry commit；
- CLASSIFICATION、FACT、SEMANTIC CORE、LEARNING AXES；
- resolved TEMPLATE PROFILE，包括 structural/task-slot/style identities；
- age/language projection、output request、required stage；
- sources、unknowns、安全边界和不得新增事实的规则；
- executor-neutral 的 required outputs 与 validation profile。

其摘要为：

```text
generation_input_lock_sha256 = sha256(canonical_json(generation_input_without_digest))
```

服务器 `0.3.1` 的字段名已冻结为 `content_lock_digest`。在 API-01 v1 中，该字段承载 `"sha256:" + generation_input_lock_sha256`，只表示**packet 的不可变前置生成输入**，不声称最终卡片文本已经锁定。设计、日志和测试必须始终使用完整名称 `generation_input_lock` 解释该值。

### 6.2 Final Production Content Lock

客户端完成 FINAL、COPY、四卡投影和 IMAGE ELEMENTS 后，必须产出已有 `cognitive-card-os-production-record-v1`。最终内容锁直接复用：

```text
final_content_lock_sha256 = production_record.content_lock.sha256
```

该锁覆盖 normalized request、classification、resolved family、FACT、sources、unknowns、安全项、propositions、双语绑定、learning axes、最终 cards、COPY/trace 和 image elements。不得另造较弱的 content-lock schema。

GenerationResult 同时保留 packet 的 `content_lock_digest` 以证明执行输入未变；上传的 production record 内含 final content lock。后续 RENDER/QA/PUBLISH 使用 final content lock，而不是 packet 的前置输入锁。

## 7. 三个 packet 身份字段

- `registry_commit`：snapshot catalog 中首次引入当前 snapshot 的精确 Git commit；服务器创建任务时验证它属于 active/retained catalog。
- `template_fingerprint`：

  ```text
  "sha256:" + sha256(canonical_json({
    "schema": "cognitive-card-template-binding-v1",
    "structural_fingerprint": <resolver output>,
    "task_slot_fingerprint": <resolver output>,
    "page_zone_fingerprint": <resolver output>,
    "style_source_path": <normalized relative path>,
    "style_source_sha256": <raw UTF-8 file bytes sha256>
  }))
  ```

  服务器从 sealed generation input 与 snapshot 独立复算；不信任调用方自报值。
- `content_lock_digest`：API-01 v1 中是 generation input lock 的带前缀摘要。服务器从已存储的 generation-input object 独立复算。

三个字段共同绑定“使用哪套规范、哪种模板解析、执行什么不可变输入”，packet digest 再绑定 stage、instructions、required outputs 和时间身份。

## 8. Executor-neutral 生成合同

完整管线包含两个推理阶段；确定性 resolver、validator、摘要和服务器提交逻辑不属于 executor：

```text
PipelineExecutor.compile(
  FreeRequest,
  CoreSnapshot
) -> SealedGenerationInput

PipelineExecutor.generate(
  GenerationPacket,
  SealedGenerationInput
) -> GenerationResult + production-record-v1
```

当前 trusted upstream compiler 调用 `compile`，ClientSubscriptionPipelineExecutor 在领取 packet 后调用 `generate`。未来 ServerApiPipelineExecutor 必须同时替换两个阶段，才能从自由请求完成全部生成；不能只替换双语投影的后半段。

### 8.1 当前执行器

`ClientSubscriptionPipelineExecutor` 在受信 Codex 终端运行，使用用户已登录的 ChatGPT Pro 会话，不需要 OpenAI API Key。API-01 需要发布一个新增、向后兼容的 executor capability；不得修改已经发布的 `0.1.1` 字节，也不得让缺少该 capability 的旧客户端看到或 claim API-01 packet。具备 capability 的客户端在 generate 阶段：

1. 领取并复算 packet digest；
2. 按 `input_artifacts` 取得 sealed generation input，复算输入摘要；
3. 按 packet stage 与 core workflow 完成双语投影、FINAL、COPY、CONTENT LOCK 和 CARD OUTPUTS；
4. 运行 resolver 与 `validate_production_record.py`；
5. 只在本地验证通过后 complete/submit。

### 8.2 未来执行器

`ServerApiPipelineExecutor` 未来使用服务器配置的模型 API，先从自由请求产生同 schema 的 sealed input，再读取服务器创建的 packet 产出同一个 production record，并通过同一个 Candidate Gate。届时：

- 新增受控的 `server_api_autonomous` execution profile；
- 单独批准 API 凭据、预算、模型 pin、重试和审计方案；
- 不改变 client executor 的历史 packet/result；
- 不复制 core 提示词或 validator，直接复用同一 snapshot release。

本批次只冻结接口和兼容要求，不启用 `server_api_autonomous`。

### 8.3 执行侧代码与规范的分发

领取端 executor 在 generate 阶段需要 core workflow 指引、resolver 与 `validate_production_record.py` 等执行侧资产。本设计明确其到达路径只有一条：**随新增的 executor capability Skill release 版本化分发**，复用 SKILL-01 的注册表/安装器机制（不可变 release、摘要绑定、可回滚）。该 release 是新增、向后兼容的独立版本，不修改已发布的 `0.1.1` 字节；它只包含执行侧所需资产——workflow 指引、resolver、production-record validator 及其依赖的 references 子集。编译侧完整 core snapshot（全部知识库与编译脚本）仍只存在于服务器/可信上游，不随客户端 release 分发。

- release 与 snapshot 的兼容关系由服务器 capability metadata 钉死：executor 领取 packet 时验证其 release 版本与 snapshot/template 身份兼容，不兼容失败关闭；
- 执行侧代码只用于"按 sealed input 投影"：它不包含编译权威，不能创建任务，任何输入都经 digest 复算；
- §8.2 中未来 ServerApiPipelineExecutor"复用同一 snapshot release"指服务器本地读取 `core-snapshots/`；客户端侧代码只经本节路径到达，因此 §10.3"公开 core 浏览端点延期"不受影响——执行侧资产走受治理 release，不走浏览端点。

## 9. core 工作流到服务器 schema 的转换

字段逐项对照服务器 `c2a898c`。字段形状与权威语义必须同时满足。

### 9.1 LockedJobRequest

| 字段 | 来源 | 规则 |
| --- | --- | --- |
| `job_id` | normalized request | `job_<object-slug>_<input-digest-prefix>`，满足 `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`；相同 sealed input 得到相同逻辑 identity，重复创建返回已有任务或稳定冲突 |
| `content_lock_digest` | generation input store | `"sha256:" + generation_input_lock_sha256`，服务器复算 |
| `registry_commit` | snapshot catalog | 精确 commit，服务器验证 catalog membership |
| `template_fingerprint` | resolved template binding | 第 7 节 composite，服务器复算 |
| `age_profile` | normalized request | `age-5-6` 等，满足 `^age-[0-9]+(?:-[0-9]+)?$` |
| `execution_profile` | 当前 executor | 固定 `client_subscription_interactive` |

### 9.2 PacketIssueRequest

| 字段 | 来源 | 规则 |
| --- | --- | --- |
| `stage` | generation input | 首版为 `bilingual_projection`；图像生成仍属于后续 RENDER/QA 批次 |
| `language_projection` | age-language profile | 如 `cn_primary_en_support`，1–128 字符 |
| `instructions` | snapshot + sealed input | 编译器生成的有序、executor-neutral 指令；只描述当前 stage，不夹带凭据或本机路径 |
| `required_outputs` | production record contract | 首版固定一个 `production/production-record.json`，`application/json`，上限不超过 20 MiB |
| `forbidden_changes` | 固定策略 | 至少包含 `generation_input_lock`、`registry_commit`、`template_fingerprint`、`fact`、`semantic_core`；这些是 executor 约束，服务器仍以输入摘要和 production-record validator 实际执法 |
| `input_artifacts` | generation input store | 固定一个 `generation-input:sha256:<64hex>` 引用；executor 经受限读取端点取得字节并复算摘要 |

`packet_id`、`issued_at`、`expires_at`、`schema` 和 `packet_digest` 继续由服务器生成。

## 10. 服务器新增面与 M1 边界

### 10.1 M1 保持不变

现有 packets/results/jobs、read/submit auth、candidate store、Skill registry 与薄客户端 `0.1.1` 的公共合同不改变。API-01 packet 在服务器元数据中标记 `sealed-generation-input-v1` executor capability；available/list/get/claim 对缺少该 capability 的 principal 失败关闭，避免 `0.1.1` 先 claim 后才发现无法读取输入。该门禁是服务器新增行为，不改变 GenerationPacket v1 的字段集合。

### 10.2 API-01 必需新增面

推荐新增：

- `POST /admin/generation-inputs`：接收 sealed generation input，验证 snapshot、schema、摘要和模板绑定后按摘要不可变存储；仅 `compiler_import` scope；
- `GET /generation-inputs/{sha256}`：仅向被授权执行对应 packet 的 client/read principal 返回 sealed input；禁止列表与模糊查询；
- `POST /admin/compiled-jobs`：在一个服务器事务中校验 generation input，并以既有 `LockedJobRequest` + `PacketIssueRequest` 结构创建 job 和 packet，避免先创建 job、后 issue 失败留下不完整任务。
- executor capability metadata 与 claim 门禁：API-01 客户端使用新签发的 capability-bound credential，旧 `0.1.1` credential 看不到 compiled packet；

这些是新的 admin/input surface，不改变 M1 已发布领取/提交路线。具体 URL 可在实施设计中调整，但“不可变输入存储、受限读取、原子建 job+packet”三项能力不可省略。

### 10.3 可延期面

以下继续延期到 RENDER-01 或门户需求成立时：

- 向普通客户端公开浏览或下载完整 core snapshot；
- capabilities 广告全部历史 snapshot；
- 服务器 API 模型执行；
- core snapshot 的通用管理 UI。

## 11. 凭据与信任边界

LLM authoring 与持凭据提交必须隔离：

1. Trusted Upstream Compiler/ChatGPT Pro 工作区不含 Card OS token；
2. compiler 只输出经过本地 schema、resolver 和关系闭包校验的 sealed generation input；
3. 独立 Deterministic Submitter 在人工确认后读取 sealed input；
4. submitter 使用一次性、job-bound、≤15 分钟的 `compiler_import` token，而不是全权 admin；执行生成的客户端另用 capability-bound read/submit credential；
5. token 通过 `umask 077` 创建的 0600 文件或受保护进程输入传递，不进 argv、stdout、日志、LLM transcript、工作区和 Git；
6. 成功、失败和中断路径都执行 revoke；TTL 是撤销失败后的兜底，不是主要隔离手段。

自由概念、年龄和 use location 可能构成个人信息。审计只保存任务必要字段和摘要；LLM 中间稿、来源抓取缓存和本地工作区的保留期在实施设计中明确，默认验收完成后清理。

## 12. 失败关闭与恢复

- snapshot、generation input、template composite 或 packet 任一摘要不匹配：拒绝创建任务；
- `compiled-jobs` 在一个事务中创建 job+packet，失败不产生可领取 packet；
- executor 取得 sealed input 后复算失败：不 claim/complete/submit；
- production record 验证失败：结果留在隔离区，不进入 `candidate_staged`；
- packet 过期：沿用服务器现有过期恢复；sealed input 与审计继续保留，可由操作员基于同一 input 创建新 packet；
- submit 响应不确定：通过既有幂等和 job/event 查询确认，不盲目重复创建逻辑任务；
- client 与未来 API 的失败都使用相同稳定错误类别，执行器专属错误只放 details。

外部 client 对返回 packet digest 的复算用于发现传输或实现错误；服务器已经在事务内完成权威校验，因此外部复算失败不会把一个未校验 packet 暴露为合法任务。

## 13. 后续 lift-and-harden 接口

- **RENDER-01**：`render_card_candidate.py`、模板族和固定 Pillow 运行时上服务器，消费已验证 production record；使用 final content lock 和 template fingerprint。
- **QA-01**：`validate_card_package.py`、`validate_production_record.py` 与 image-quality QA 形成服务器 QA 门；API-01 已复用 production-record validator，QA-01 增加渲染、图像和包级规则。
- **PUBLISH-01**：先关闭 package-v5 两个 Block：服务器复算 authority 闭包、gallery revision 与资产 URL 绑定；final content lock 与 snapshot identity 贯穿 manifest、四卡和 PDF。
- 每批次继续执行信任边界重审、运行时钉住、输入面重验。

## 14. 测试与验收

### 14.1 Snapshot

- 34 个 release 成员（除新 manifest 自身）均有 path/mode/size/SHA-256；
- 缺失、篡改、额外文件、symlink、dirty/wrong commit、路径替换均拒绝；
- snapshot root digest 有跨实现固定测试向量。

### 14.2 Compiler 与 sealed input

- 兔子与第二个哺乳动物使用相同 family structural identity；
- resolver、FACT/semantic/source/unknown 闭包负向夹具；
- generation input canonical digest 与 template composite 固定向量；
- LLM 工作区无 token，submitter 不读取非 sealed input 文件。

### 14.3 Server

- 伪造但形状正确的 registry/template/input digest 被服务器拒绝；
- generation input 不可变、无列表枚举、无越权读取；
- `compiled-jobs` 任一子步骤失败时数据库中无可领取 packet；
- token 不出现在 stdout、日志、audit、database、packet、trace；revoke 后 403。

### 14.4 Executor parity

- 当前客户端：自由概念“兔子，深圳，5～6岁，中英文，打印版”→ sealed input → packet → production record → submit → candidate_staged；
- 同一 sealed input 重跑得到相同输入身份、模板身份和结构闭包；自然语言可变部分作为新 candidate revision，不伪造相同输出摘要；
- 未来 ServerApiPipelineExecutor 的 compile/generate contract fixture 现在建立但标记 capability disabled；启用时必须让相同 fixture 通过。

### 14.5 回归

- 薄客户端与 registry 既有测试不受影响；
- M1 领取/提交现有链路保持兼容；
- `bash scripts/ai/check-agent-state.sh` 与 `git diff --check` 通过。

## 15. 已冻结决定与后续开放项

本次冻结：

- 当前客户端执行、未来 API 执行，二者共用 compile + generate 两阶段 executor contract；
- 服务器保存不可变 sealed generation input；
- packet 的 `content_lock_digest` 在 API-01 v1 表示 generation input lock，final lock 保留在 production record；
- 服务器应用仓保存 snapshot；
- API-01 前置受限 input store/read 与原子 compiled-job 创建，不前置公开 core 浏览端点；
- 首版 required output 是一个规范 production record，不是四个散装卡片 JSON。
- API-01 使用新增 capability-bound 客户端；已发布 `0.1.1` 保持原字节与 M1 行为，不能 claim compiled packet。
- 执行侧代码（workflow 指引、resolver、production-record validator 及 references 子集）随新增 executor capability Skill release 版本化分发；编译侧完整 snapshot 不下发，公开 core 浏览端点继续延期。

后续实施设计仍需给出但不改变上述方向：

- generation-input-v1 的完整 JSON Schema；
- `compiler_import` scope 与 token issue/revoke 的精确 CLI/API；
- sealed input 的保留期、备份与清理规则；
- compiled-jobs 的幂等键与重复请求响应；
- ServerApiPipelineExecutor 的模型、预算和运行时 pin（接入 API 时另行批准）。

## 16. 实施分解（获书面确认后另行立项）

1. **API-01-IMPL-1 Snapshot**：生成完整 snapshot manifest、导入 catalog、闭包与负向测试；
2. **API-01-IMPL-2 Input Contract**：generation-input-v1 schema、resolver/validator、template composite、固定向量；
3. **API-01-IMPL-3 Server Control Plane**：immutable input store/read、compiler_import scope、原子 compiled-jobs 与测试；
4. **API-01-IMPL-4 Client Executor**：trusted compiler 与 deterministic submitter 隔离、packet 执行、production record 上传；
5. **API-01-IMPL-5 Acceptance**：兔子 + 第二个哺乳动物、隔离薄客户端、恢复/撤销/负向安全验收与独立评审。

每个实施批次需单独进入 CURRENT_TASK；本设计确认不授权任何实现、生产变更或发布。
