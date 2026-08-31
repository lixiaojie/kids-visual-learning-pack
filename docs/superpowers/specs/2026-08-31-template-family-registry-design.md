# 模板族注册表与跨对象夹具（TMPL-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §4.1 / §7.3](../../cognitive-card-os-system-design.md)、[KNOW-01](2026-08-31-classification-registry-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把 four-card 模板族做成**带版本的服务器注册表**，使相同主路由得到稳定骨架，缺口停止而不是猜测：

1. 发布 `template-registry-v1`：登记精确族与紧凑族，记录固定四页骨架、槽位、年龄/语言适配、结构指纹，以及发布/回滚兼容矩阵；
2. 每个已启用 family 至少两个对象夹具，解析为同一 `template_family_id` 与同一骨架；
3. 无注册路由返回 `TEMPLATE_GAP`；次领域/次形态只能激活已声明模块。

本设计满足路线图 TMPL-01 完成条件。不为 ACCEPT-02 写第二个哺乳动物正式试产。

## 2. 非目标

- 不改四对象顶层 schema 名、v1 FACT 键集、packet 契约、AUTHOR-05 默认 Projection 表。
- 不修改不可变 core snapshot 字节；snapshot resolver 仍为 generation-input 密封复算权威。
- 不等于 PORTAL-01 / AGE-02 / ACCEPT-02。
- 不新增 HTTP 端点；不 merge server `main`；不 push；不现网。
- 不阻塞已完成的 RUN-01 / KNOW-01：兔子 mammal 路径继续通过。

## 3. 在分层中的位置

```text
classification-registry-v1     分类允许 gap 单元格
        ↓
template-registry-v1           本设计：主路由 → family 或 TEMPLATE_GAP
        ↓
CONV-01 convert_current        密封前先走注册表
        ↓
snapshot resolve_template      仅对已映射路由复算指纹
        ↓
generation-input v1            键集不变
```

注册表是投影与校验权威，不是第五个治理对象。分类 `gap` 仍可 authoring；四卡转换在无模板映射时失败。

## 4. 注册表合同

版本常量：`template-registry-v1`。摘要为注册表规范文档的 canonical SHA-256。

### 4.1 主路由

主路由是精确元组：

```text
primary_domain + primary_form + object_subtype
+ age.main.profile_id
+ cn_profile + en_profile
```

只匹配登记的精确元组。**不**把未登记 subtype 静默映射到同 domain/form 的 `general` fallback。`life + entity + general` 是自己的路由；`life + entity + animal/bird` 是缺口。

次领域 / 次形态不参与 family 选择，只在命中 family 之后激活已声明模块。

### 4.2 已启用 family

首批从 snapshot 迁入服务器（不改 snapshot 文件）：

| family id | 来源 | 年龄 |
| --- | --- | --- |
| `life.entity.animal-mammal.…family-v1` | 精确 `family.json` | age-5-6 |
| `life.entity.animal-mammal.…family-v1` | 紧凑 registry | age-3-4 |
| `paleontology.entity.dinosaur.…family-v2` | 精确 `family.json` | age-5-6 |
| `life.entity.generic.…family-v1` 及 `domain_form_families.json` 其余 domain/form 族 | 紧凑 registry | age-5-6 |

数学 `space-geometry` 与社会 `schedule` 在 KNOW-01 分类矩阵为 `enabled`，但不是 four-card 模板族；四卡解析返回 `TEMPLATE_GAP`。它们继续走 `progressive-exploration` / `time-sensitive-brief`。

恐龙精确路由 `paleontology + entity + dinosaur` 在分类矩阵为 `gap`，但模板已登记；分类可通过，四卡可解析。

### 4.3 骨架

每个 family 记录：

- `page_order`：固定 `CN_OBS` → `EN_OBS` → `CN_KNOW` → `EN_KNOW`
- 有序 `task_slot_spec`（`required` / `optional` / `suppressed`）
- `locked_zones`
- 精确族另有 `page_zones` 与 snapshot 对齐的结构 / 槽位 / 页区指纹
- `age_adapter` 与 `language_adapters`
- `secondary_modules.domains` / `forms`

同一主路由的两个对象夹具必须得到相等的骨架记录。允许因对象不同而空着可选槽；不得改页序、锁区或槽位语义。

### 4.4 兼容与回滚

每个 family 一行：

| 字段 | 含义 |
| --- | --- |
| `template_family_id` | 结构 major（`family-v1` / `family-v2`） |
| `template_version` | 族内兼容修订（semver） |
| `status` | `active` 或 `retired` |
| `snapshot_id` | 绑定的 core snapshot |
| `replaces` | 被本行替代的旧 family id，可空 |
| `rollback_to` | 授权回滚目标，可空 |

`retired` 行保留历史，不参与选择。本批全部为 `active`；恐龙 v2 无服务器侧 v1 可回滚。结构不兼容必须改 family suffix，不得静默复用版本号。

### 4.5 跨对象夹具

每个 `active` family 至少两个对象夹具，只含路由键（对象名 + 分类 + 年龄/语言），不含完整 Knowledge Core。哺乳动物 age-5-6 用 `rabbit` 与 `cat`；恐龙用 `stegosaurus` 与 `triceratops`。其余紧凑族用稳定合成对象名。

## 5. 与 converter 的接线

`convert_current` 在 `assemble_request` 之后、年龄适配与 snapshot 密封之前调用 `resolve_route`：

- 命中：继续既有 AGE-01 + snapshot 路径；
- 未命中：`TEMPLATE_GAP`，不调用 snapshot；
- 次 facet 无模块或不在 `task_slots` 中：`INVALID_SECONDARY_MODULE`。

既有兔子 `--request` 与省略 `--request` 路径必须继续通过。

## 6. 验收

- 覆盖报告可枚举：每个已登记 family 有骨架；每个分类单元格 × 支持年龄要么 mapped 要么 gap。
- `rabbit` 与 `cat` 同为 mammal v1 骨架；`stegosaurus` 与 `triceratops` 同为 dinosaur v2 骨架。
- `ocean + entity + habitat` 与 `life + entity + animal/bird` 返回 `TEMPLATE_GAP`。
- mammal 次领域 `ecology` 可激活 `comparison`；次领域 `arts` 失败。
- 兔子 convert 仍 PASS。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 7. 错误码

| 码 | 含义 |
| --- | --- |
| `TEMPLATE_GAP` | 主路由无登记 family |
| `INVALID_SECONDARY_MODULE` | 次领域/次形态未声明或槽位不在 family 中 |
| `TEMPLATE_FAMILY_RETIRED` | 命中已退役 family（本批夹具不触发） |
