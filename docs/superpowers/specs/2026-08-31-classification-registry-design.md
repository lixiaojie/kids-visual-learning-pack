# 分类注册表与 authoring 接入（KNOW-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §3.2 / §4.1](../../cognitive-card-os-system-design.md)、[CONV-01](2026-08-30-knowledge-four-card-converter-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把 faceted 分类做成**带版本的服务器注册表**，并接入 authoring，使新主题不能靠自由文本或手填四卡 request 绕过分类：

1. 发布 `classification-registry-v1`：受控 `primary_domain`、`primary_form`、领域自有 `object_subtype`，以及 `domain × form × subtype` 覆盖矩阵；
2. authoring 必填与四卡 request 同形的 `classification`；编译后写入 Knowledge Scope；
3. four-card convert / accept 默认从 current 的 Scope 分类与 Learning Plan 组装 `normalized_request`；完整 `--request` 变为可选。

本设计满足路线图 KNOW-01 完成条件。模板缺口仍属 TMPL-01。

## 2. 非目标

- 不改四对象顶层 schema 名、v1 FACT 键集、packet 契约、AUTHOR-05 默认 Projection 表。
- 不实现模板族覆盖或 `TEMPLATE_GAP`（TMPL-01）。
- 不等于 PORTAL-01 / AGE-02 / ACCEPT-02。
- 不新增 HTTP 端点；不 merge server `main`；不 push；不现网。
- 不阻塞已完成的 RUN-01：既有 `--request` 调用在分类与 Scope 一致时继续通过。

## 3. 在分层中的位置

```text
classification-registry-v1     服务器权威枚举与覆盖矩阵；不是治理对象
        ↓
authoring request              必填受控 classification；可选 usage
        ↓
Knowledge Scope                持久化 classification（可选键，新编译必写）
Learning Plan                  年龄 / 语言；可选 use_location / output_request
        ↓
CONV-01                        组装四卡 normalized_request；校验注册表
        ↓
generation-input v1            键集不变；classification 字段仍是密封输入
```

注册表是投影与校验权威，不是第五个治理对象。

## 4. 注册表合同

版本常量：`classification-registry-v1`。摘要为注册表规范文档的 canonical SHA-256。

### 4.1 受控枚举

机器值与存档 `classification-v2.md`（core snapshot 内的现行分类规范）对齐，并迁入服务器：

- 恰好一个 `primary_domain`、一个 `primary_form`；
- `secondary_domains` / `secondary_forms` 只能引用同一受控词表，且不得重复主键；
- `object_subtype` 属于所选 `primary_domain` 的词表；
- 每个 domain 都包含 `general` 与 `other`。`other` 是分析后的受控桶，不是自由文本占位。

尚未出现首个对象的领域在本批补齐 subtype 词表，覆盖矩阵对应单元格记为 `gap`。`gap` 允许被分类，不在本批当成模板失败。

### 4.2 覆盖矩阵

对每个 `(primary_domain, primary_form, object_subtype)` 生成单元格，状态为：

| 状态 | 含义 | authoring |
| --- | --- | --- |
| `enabled` | 已有首个对象、试产或已启用 family 路由 | 接受 |
| `gap` | 词表已有，尚无首个对象 / 模板 | 接受（TMPL-01 再挡模板） |
| `review` | 两条主路由会实质改变骨架 | `CLASSIFICATION_REVIEW` |

稀疏 overlay 标记 `enabled` 与 `review`；其余为 `gap`。

`enabled` 首批包括：兔子 `life + entity + animal/mammal`、几何 `mathematics + abstract-concept + space-geometry`、时效夹具 `society-culture + event + schedule`，以及存档 `domain_form_families.json` 已声明的 family 路由。

`review` 首批：`paleontology + entity + fossil-animal`、`paleontology + evidence-record + dinosaur`。另：`interdisciplinary` 作为主键且 `secondary_domains` 为空时 `CLASSIFICATION_REVIEW`。

### 4.3 边界

| 输入 | 结果 |
| --- | --- |
| 受控 `general` subtype | 接受 |
| 受控 `other` subtype | 接受 |
| 自由文本 domain / form / subtype | `CLASSIFICATION_UNKNOWN` |
| 矩阵 `review` 或 interdisciplinary 无次领域 | `CLASSIFICATION_REVIEW` |
| authoring 缺 classification | `AUTHORING_FIELD_REQUIRED` |
| `--request` 分类与 Scope 不一致 | `CLASSIFICATION_MISMATCH` |

## 5. Authoring 与持久化

authoring request 增加必填 `classification`（五键，与四卡 request 同形）和可选 `usage`：

```json
{
  "classification": {
    "primary_domain": "life",
    "secondary_domains": [],
    "primary_form": "entity",
    "secondary_forms": [],
    "object_subtype": "animal/mammal"
  },
  "usage": {
    "location": "Shenzhen",
    "output": "print"
  }
}
```

编译规则：

1. 先按注册表校验 `classification`，再写入 `knowledge-core.scope.classification`；
2. 若有 `usage`，写入 `learning-spec.plan.use_location` 与 `plan.output_request`；
3. Knowledge Core 既有夹具可以没有 `classification`（validator 将该键视为 Scope 可选）；**新** authoring 不能省略；
4. 不改命题、来源或 AUTHOR-02 正文。

## 6. 与 converter / accept 的接线

`convert_current` 的 `request` 变为可选：

- 省略：从 current 的 Scope 分类 + Plan 年龄/语言 + `use_location` / `output_request` 组装四卡 request；缺分类则 `CONVERTER_REQUEST_REQUIRED`；缺地点或输出则 `CONVERTER_USAGE_REQUIRED`；
- 提供：按原 v1 形状校验；若 Scope 已有分类，必须逐字段相等，否则 `CLASSIFICATION_MISMATCH`；CLI 不得用自由文本覆盖已登记分类。

年龄组装：`plan.audience_profiles` 必须恰好一个 `age-3-4` 或 `age-5-6`；CN profile 同年龄；EN `beginner`；`languages` 含 `zh-CN` 与 `en` 时 `language.output=bilingual`。对象名取 topic slug。

ACCEPT-01 CLI `--request` 同样可选；省略时用组装结果执行原地点/年龄/打印门禁。既有带 `--request` 的测试保持。

## 7. 验收

- 覆盖矩阵包含每个 domain × 每个 form × 该 domain 全部 subtype。
- 未出现首个对象的领域（如 `ocean`、`arts`）有 subtype 词表，单元格为 `gap`。
- `general` / `other` authoring 通过；自由文本失败；`review` 单元格失败。
- 兔子 authoring 编译后 Scope 为 `life + entity + animal/mammal`；convert 不传 `--request` 仍得到 Shenzhen / age-5-6 / bilingual / print。
- 传入与 Scope 不同的 `--request` 分类失败。
- 既有 RUN-01 `--request` 路径 PASS。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 8. 错误码

| 码 | 含义 |
| --- | --- |
| `CLASSIFICATION_UNKNOWN` | 枚举外的 domain / form / subtype / secondary |
| `CLASSIFICATION_REVIEW` | 主路由歧义，停止猜测 |
| `CLASSIFICATION_MISMATCH` | CLI request 与 Scope 分类不一致 |
| `CLASSIFICATION_SECONDARY_INVALID` | 次领域/次形态重复主键或不在词表 |
| `CONVERTER_USAGE_REQUIRED` | 无 `--request` 且 Plan 缺少地点或输出 |
| `CONVERTER_REQUEST_REQUIRED` | 无 `--request` 且 Scope 无分类（旧 revision） |
