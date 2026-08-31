# 年龄与中文表达服务器适配器（AGE-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §7](../../cognitive-card-os-system-design.md)、[CONV-01](2026-08-30-knowledge-four-card-converter-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把已批准的年龄与语言规则发布为**带版本的服务器适配器**，使 four-card 投影在转换时得到儿童中文与 beginner 英文，而不改写 Knowledge Core：

1. 覆盖 `age-3-4`、`age-5-6`；CN 与主年龄同配置；EN 为 `beginner`；
2. 年龄只改变表达与任务负荷（COPY / 描红 / 口头复述）；
3. 命题 id、确定性、来源、未知项政策、安全边界跨年龄保持一致。

本设计满足路线图 AGE-01 完成条件，并替换 CONV-01 §5.2 将 `canonical_claim` 同时写入 `cn`/`en` 的临时投影。

## 2. 非目标

- 不改四对象 schema、v1 FACT 键集、AUTHOR-05 默认表、packet 契约。
- 不把 COPY 写入 generation-input（RENDER-01 按本适配器对 FACT `cn`/`en` 重算）。
- 不新增 age-3-4 模板族（TMPL-01）；age-3-4 适配在进程内验证，不调用 snapshot 模板解析。
- 不等于 PORTAL-01 / RENDER-01 / QA-01 / PUBLISH-01 / KNOW-01 / AGE-02。
- 不新增 HTTP 端点；不 merge server `main`；不 push；不现网。
- 不调用外部模型发明中文。

## 3. 在分层中的位置

```text
Knowledge Core          事实；canonical_claim；禁止呈现方案
        ↓
AGE-01（本设计）        版本化年龄/语言适配器 → 儿童表达 + 任务负荷
        ↓
CONV-01 converter       FACT.cn / FACT.en 使用适配结果；safety 原文不动
        ↓
generation-input        v1 键集不变
        ↓
RENDER-01（后期）       COPY span 由适配器对已适配命题重算
```

适配器是投影，不是第五个治理对象。

## 4. 适配器合同

版本常量：`age-language-adapter-v1`。新增 8/10/15 岁走 AGE-02 新版本或新 profile，不扩宽本版本区间。

### 4.1 解析

从 four-card `normalized_request` 读取：

| 字段 | 规则 | 失败码 |
| --- | --- | --- |
| `age.main.profile_id` | 必须是 `age-3-4` 或 `age-5-6` | `AGE_PROFILE_GAP` |
| `language.cn_profile` | 必须等于 `age.main.profile_id` | `AGE_LANGUAGE_PROFILE_MISMATCH` |
| `language.en_profile` | 必须是 `beginner` | `AGE_LANGUAGE_PROFILE_MISMATCH` |
| `language.output` | 正式包仍为 `bilingual`（由既有 converter/request 门禁保证） | 不在本适配器重复 |

跨 profile 混合或 `multi_version` 仍由既有路由拒绝，本适配器一次只处理一个主年龄。

### 4.2 表达

对每条纳入 FACT 的命题，用 **精确** `canonical_claim` 在版本化登记表中查找 `{age-3-4, age-5-6} × {cn, en}`。

- 命中：写入 FACT `cn` / `en`；`unknowns[].boundary` 与命题文本对齐。
- 未命中：`AGE_EXPRESSION_GAP`，fail closed。
- 不得把 `unknown` 改成肯定句；确定性字段不读登记表。
- `safety[].cn` / `safety[].en` 保持 Knowledge Core `safety_scope` 原文，**不**随年龄改写。

登记表首批覆盖：合成兔子夹具两条 claim，以及 AUTHOR-02 真实兔子八条 claim。其他主题未登记则拒绝转换。

### 4.3 任务负荷

由年龄决定，不进入 FACT：

| 年龄 | COPY | 描红 | 口头复述 |
| --- | --- | --- | --- |
| `age-3-4` | 抑制（列表空） | 可选；若有则必须是知识表达的精确 span | 必需；span 覆盖同语言知识表达 |
| `age-5-6` | 每语言最多 2 句；CN 优先 ≤12 个汉字，EN 优先 ≤8 词 | 每语言 1–6 项精确 span | 不要求 |

COPY / 描红 / 口头复述的 `text` 必须等于 `knowledge_text[span.start:span.end]`，且 `proposition_id` 属于该语言已适配命题。知识页不承载 COPY：`copy_plan` 用 `source_card` 标明 span 取自知识卡文本，用 `action_card` 标明动作落在观察卡。

过长知识句：COPY 取该句中仍落在原文内、且满足长度上限的连续子串（优先整句；否则第一段仍在上限内的子句）。找不到合法 span 则 `AGE_COPY_SPAN_UNAVAILABLE`。

## 5. 与 converter 的接线

`fact_from_knowledge_core` 仍做 identity 投影（确定性映射、`source_id`、safety 原文）。`convert_current` 在组装密封前调用 `apply_age_language(fact, request)`。

Knowledge Core 文件字节不变。只改 Projection 文档时，`knowledge_core_sha256` 仍不变。

age-3-4 的 focused 测试只跑适配器与 COPY 计划，不调用 `assemble_from_knowledge_revision`（现网 snapshot 无 mammal `age-3-4` 模板族）。

## 6. 验收

- 同一 Knowledge Core 分别适配 `age-3-4` 与 `age-5-6`：命题 id、certainty、source_ids、safety 文本相同；`cn`/`en` 与 COPY 计划可以不同。
- 合成兔子 `age-5-6` convert 后 FACT `cn` 为登记中文，`en` 为 beginner 英文，且 `validate_joined_generation_input` 通过。
- 未登记 claim → `AGE_EXPRESSION_GAP`。
- CN profile 与年龄不一致 → `AGE_LANGUAGE_PROFILE_MISMATCH`。
- `age-3-4` COPY 列表为空；口头复述 span 可切片还原。
- `age-5-6` COPY/描红 span 可切片还原，且不超过第 4.3 节上限。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 7. 错误码

| 码 | 含义 |
| --- | --- |
| `AGE_PROFILE_GAP` | 未登记或不支持的年龄 profile |
| `AGE_LANGUAGE_PROFILE_MISMATCH` | CN 非同年龄或 EN 非 `beginner` |
| `AGE_EXPRESSION_GAP` | canonical claim 无儿童表达 |
| `AGE_COPY_SPAN_UNAVAILABLE` | 无法从知识表达切出合法 COPY span |
