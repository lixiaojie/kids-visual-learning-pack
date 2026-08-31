# Knowledge current → four-card 接合转换（CONV-01）

- Status: Approved for this execution tranche
- Date: 2026-08-30
- Related: [ADR-001](../../decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、接合 lock、[BROWSE-01](2026-08-30-knowledge-browse-projection-confirmation-design.md)、[WIRE-01](2026-08-30-knowledge-library-http-db-wiring-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

确认点 1 之后，把 **library current** 的四对象映射为现有接合 generation-input，使四卡 executor 能对同一主题密封：

1. 只读 current，不改 Knowledge Core 字节；
2. 把 knowledge-core 命题投影为 v1 FACT（含 `source_id` 点号映射）；
3. 调用已有 `assemble_from_knowledge_revision`，得到可通过 `validate_joined_generation_input` 的密封。

本设计满足路线图 CONV-01 完成条件，且不把存档 production-core 合入 Knowledge Core 存储层。

## 2. 非目标

- 不写 `production-record.json` 本体；那是 generate 阶段的 executor 输出。接合密封的 `required_outputs` 仍声明该路径。
- 不改 v1 FACT schema、四对象 schema、AUTHOR-05 默认表、packet 契约。
- 不新增 Projection family；不把 family 或分类写入 Knowledge Core。
- 不等于 PORTAL-01 / RENDER-01 / QA-01 / PUBLISH-01。
- 不新增 HTTP 转换端点；写出的 JSON 可交给已有 `POST /admin/generation-inputs`。
- 不 merge server `main`，不 push，不现网。
- 不解决儿童中文 claim（AGE-01）或分类进 authoring（KNOW-01）。

## 3. 在分层中的位置

```text
Knowledge Core          事实；禁止呈现方案
        ↓
library current         不可变 revision + pointer
        ↓
BROWSE-01               确认点 1（已完成）
        ↓
CONV-01（本设计）       current → FACT 投影 → 接合 generation-input
        ↓
现有 executor           密封入 store / compiled-job（WIRE-01 门禁仍有效）
        ↓
production-record       executor 输出；不在本批生产
```

转换器是投影，不是第五个治理对象。

## 4. 准入

同时满足才转换：

| 条件 | 失败码 |
| --- | --- |
| `get_current(topic, now)` 存在 | `CONVERTER_CURRENT_NOT_FOUND` |
| current 的 `projection-spec.blueprint.family` 为 `four-card` | `CONVERTER_FAMILY_NOT_FOUR_CARD` |
| 纳入 scope 的 active 命题至少一条 | `CONVERTER_NO_ACTIVE_PROPOSITIONS` |
| CLI 提供完整 four-card `normalized_request` JSON | 参数错误 / `CONVERTER_REQUEST_REQUIRED` |

默认兔子（`chaptered-guide`）必须先显式 `projection.family: four-card` 并重新 publish。不从历史 revision 建执行密封。Candidate / unlist / 过期 current 与 `get_current` 一致，视为无 current。

分类、地点、年龄档位、输出形态**不从 Knowledge Core 推断**。KNOW-01 完成前由 `--request` 提供（兔子试产使用既有 mammal 请求：`life` / `entity` / `animal/mammal`、`age-5-6`、双语、print）。

## 5. FACT 投影规则

只投影 **scope.included_unit_ids** 内、`standing` 为 `active`（缺省视为 active）的命题。`superseded` 不进入 FACT。

### 5.1 `source_id` 映射

Knowledge Core `_SAFE_ID` 允许 `.` 与 `_`；FACT `_SOURCE_ID` 为 `^[a-z][a-z0-9-]{1,63}$`。

对每个用到的 core `source_id`：

1. 把 `.` 与 `_` 换成 `-`；
2. 折叠连续 `-`，去掉首尾 `-`；
3. 结果必须完整匹配 FACT 正则，否则 `CONVERTER_SOURCE_ID_UNMAPPABLE`；
4. 两个不同 core id 映到同一 FACT id 则 `CONVERTER_SOURCE_ID_COLLISION`。

命题 `source_ids` 使用映射后的 id。Knowledge Core 文件不得被改写。

### 5.2 字段对应

| FACT | 来源 |
| --- | --- |
| `sources[].source_id` | 映射后的 core `source_id` |
| `sources[].title` | core `title` |
| `sources[].institution` | core `creator` |
| `sources[].locator` | core `locator`；必须 `https://` 前缀，否则 `CONVERTER_SOURCE_LOCATOR_INVALID` |
| `propositions[].proposition_id` / `meaning_id` | core `proposition_id`（FACT 命题 id **允许**点号，不映射） |
| `propositions[].certainty` | `established`/`probable` → `known`；`uncertain`/`disputed` → `unknown` |
| `propositions[].cn` / `en` | AGE-01 起由 `age-language-adapter-v1` 写入儿童中文与 beginner 英文；未登记 claim fail closed。见 [AGE-01](2026-08-31-age-language-adapter-design.md) |
| `unknowns` | 仅 `unknown` 命题；`policy=preserve-unresolved`；boundary 与命题 `cn`/`en` 对齐（AGE-01 后为适配表达） |
| `safety` | 纳入命题的 `safety_scope` 字符串；`safety_id=safety-NN`；`policy=from-knowledge-core`；cn/en 为原文 |
| `semantic_core.propositions` | 与 FACT 命题逐字段相同 |

不把 temporal、evidence span、单元标题写入 FACT（v1 无这些键）。

## 6. 密封

转换器调用现有 `assemble_from_knowledge_revision`：

- `knowledge_core` / `learning_spec` / `projection_spec` 来自 current 目录；
- `fact` / `semantic_core` 来自第 5 节；
- `request` 来自 CLI；
- `snapshot_id` / `registry_commit` 由 CLI 指向已导入 catalog（试产默认 active 兼容 snapshot `ae563e…` + catalog 所载 `registry_commit`）。

接合 lock 仍摘要四对象 identity，不是平行 FACT 文件。内层 v1 lock 仍摘要 FACT 密封。二者不同。

WIRE-01 门禁不变：入库 / 建 job 仍要求声明的 `knowledge_revision` 等于当时 current。

## 7. CLI

```text
python3 -m cognitive_card_server.knowledge_library.cli convert \
  --library-root <library> \
  --topic <slug> \
  --repo-root <server-checkout> \
  --snapshot-id sha256:<64hex> \
  --registry-commit <40hex> \
  --request <four-card-request.json> \
  --output <joined.json> \
  --now <utc>
```

成功：写出接合 JSON，stdout 一行含 `status=ok`、topic、revision、两个 lock 摘要。失败：稳定码，非 0。只读 library。

## 8. 验收

- 显式 four-card 的合成兔子 current 转换后 `validate_joined_generation_input` 通过；FACT `source_id` 无点号；磁盘 knowledge-core 的 `source_id` 仍有点号。
- 默认 `chaptered-guide` 兔子 current 返回 `CONVERTER_FAMILY_NOT_FOUR_CARD`。
- 无 current 返回 `CONVERTER_CURRENT_NOT_FOUND`。
- 映射碰撞 fail closed。
- 只改 Projection 文档时 `knowledge_core_sha256` 不变，接合 `generation_input_lock_sha256` 变。
- 本设计不授权 merge 进 server `main`、不授权现网、不授权抢救存档 `core/` 进本批。
