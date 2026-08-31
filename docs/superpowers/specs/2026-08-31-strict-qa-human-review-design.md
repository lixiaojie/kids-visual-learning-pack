# 严格 QA 与人工复核（QA-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-001](../../decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §3.3 / §4.4 / §10](../../cognitive-card-os-system-design.md)、[RENDER-01](2026-08-31-locked-four-card-render-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

对**已锁定**且已经 RENDER-01 排出的四卡做服务器权威机器 QA；全部通过后才进入 `awaiting_review`。人工复核必须留下 actor、决策与审计：

1. 机器 QA 只消费内容锁与 RENDER-01 产物，不回写 Knowledge Core，不发明命题；
2. 任一项机器失败则状态停在 `machine_failed`，不得进入 `awaiting_review`；
3. 人工 `approve` / `reject` 仅在 `awaiting_review` 可写；必须有非空人类 actor；追加只读审计事件。

本设计满足路线图 QA-01 完成条件。不可变发布仍属 PUBLISH-01。

## 2. 非目标

- 不改四对象 schema、v1 FACT 键集、packet 契约、AUTHOR-05 默认表。
- 不等于 PORTAL-01 / PUBLISH-01 / TMPL-01 / KNOW-01 / AGE-02。
- 不把存档客户端 `audit-package` receipt、恐龙 visual vocabulary 或 package-v5 钉死合入。
- 不接线现有 subscriber `JobState` / HTTP / SQLite 任务表。
- 不新增 HTTP 端点；不 merge server `main`；不 push；不现网。
- 不要求真实高视觉素材上的主观观感验收（仍由人工决策覆盖，本批次只做可机器判定的图像规则）。

## 3. 在分层中的位置

```text
Knowledge Core          事实；禁止呈现方案
        ↓
AGE-01 + CONV-01        儿童表达；copy_plan 不进 generation-input
        ↓
锁定 production-record  content_lock + 四卡文本 + FACT
        ↓
RENDER-01               copy_plan 覆盖观察卡动作区 → A4 PNG + PDF
        ↓
QA-01（本设计）         机器门禁 → awaiting_review → 人工 actor 决策 + 审计
        ↓
PUBLISH-01              后期；本批次不发布
```

QA 是门禁，不是第五个治理对象。

## 4. 机器 QA

输入同时具备才跑：锁定记录（与 RENDER-01 相同子集）+ RENDER-01 输出目录（含 `render-set.json`）。输出写到**独立** QA 目录，不污染渲染目录的未声明文件检查。

| 检查 | 失败码 |
| --- | --- |
| 内容锁存在且可复算 | 沿用 `RENDER_LOCK_MISSING` / `RENDER_LOCK_MISMATCH` |
| 固定四页顺序与 zone 合同 | 沿用 `RENDER_PAGE_ORDER` / `RENDER_ZONE_DRIFT` |
| AGE-01 profile 可解析 | 沿用 `AGE_*` |
| COPY/描红等于 `copy_plan` 且为同语言知识卡子串 | `QA_COPY_MISMATCH`；沿用 `RENDER_COPY_NOT_ON_SOURCE` |
| 知识卡不得承载 copy/trace 任务槽 | `QA_KNOWLEDGE_HAS_COPY` |
| CN/EN 知识卡命题 id 集合与 FACT 一致、确定性一致 | `QA_PROPOSITION_DRIFT` |
| 观察任务命题必须出现在同语言知识卡 | `QA_OBS_NOT_ON_SOURCE` |
| 来源 id 出现在知识卡 sources 区 | `QA_SOURCE_MISSING` |
| 未知项边界可在 uncertainty/confusion 或知识可见文本还原 | `QA_UNKNOWN_MISSING` |
| 安全区等于 FACT `safety` 原文 | `QA_SAFETY_REWRITTEN` |
| 渲染四页存在、A4、摘要与 `render-set` 一致 | `QA_RENDER_DIGEST` |
| PDF 有 PDF 头且恰好四个 CropBox | `QA_PRINT_PDF` |
| 布局报告 overflow/overlap/crop 均为 false；清场区无插图 | `QA_LAYOUT` / 沿用 `RENDER_ASSET_IN_CLEAR_ZONE` |
| 渲染目录仅允许声明文件 | `QA_UNDECLARED_FILE` |

允许的渲染目录文件（相对 `render-dir`）：

```text
render-set.json
print.pdf
cards/cn-observe.png
cards/en-observe.png
cards/cn-know.png
cards/en-know.png
reports/CN_OBS.layout.json
reports/EN_OBS.layout.json
reports/CN_KNOW.layout.json
reports/EN_KNOW.layout.json
```

机器跑完收集全部问题，不 fail-fast。`issues` 非空 → `status=machine_failed`。全部通过 → `status=awaiting_review`。

抢救（ADR-001）采用存档验证器的**合同**（锁复算、COPY 溯源、双语命题绑定、未声明文件、打印页几何），不是恐龙词表或客户端 workspace lock。

## 5. 人工复核与审计

| 规则 | 失败码 |
| --- | --- |
| 当前状态必须是 `awaiting_review` | `QA_REVIEW_NOT_READY` |
| 已有终态不得覆盖 | `QA_REVIEW_ALREADY_RECORDED` |
| `actor` 去空白后非空，且不是机器身份 `qa-01-v1` / `machine` | `QA_REVIEW_ACTOR_REQUIRED` |
| `decision` 只能是 `approve` 或 `reject` | `QA_REVIEW_DECISION` |

`approve` 不发布。`reject` 不回写 Knowledge Core，也不自动重渲。PUBLISH-01 只消费 `approved` 报告。

审计文件 `audit.jsonl` 只追加。每条事件绑定 `content_lock_sha256`、当时 `qa_report_sha256`、UTC `at`（测试可注入）。机器事件 `actor` 固定为 `qa-01-v1`；人类事件必须使用调用方 actor。

## 6. 产物

| 文件 | 内容 |
| --- | --- |
| `qa-report.json` | schema `cognitive-card-os-qa-report-v1`；status；issues；锁与渲染摘要；可选 `review` |
| `audit.jsonl` | 机器运行与人工决策的规范 JSON 行 |

报告与审计字节使用既有 `canonical_json`。同一输入两次机器 QA，在相同 `at` 下报告摘要稳定。

## 7. 验收

- 合成兔子 `age-5-6`：RENDER-01 产物机器 QA 通过并进入 `awaiting_review`。
- 缺锁、COPY 不在知识卡、渲染摘要被篡改、多出未声明文件：`machine_failed`，`review` 被拒绝。
- 机器通过后，`actor=tester` + `approve` 写入审计；无 actor 或对失败报告复核 fail closed。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 8. 错误码

| 码 | 含义 |
| --- | --- |
| `QA_COPY_MISMATCH` | 布局 COPY/描红不是当前 `copy_plan` |
| `QA_KNOWLEDGE_HAS_COPY` | 知识卡带了 copy/trace 槽 |
| `QA_PROPOSITION_DRIFT` | 中英命题或确定性漂移 |
| `QA_OBS_NOT_ON_SOURCE` | 观察命题未出现在同语言知识卡 |
| `QA_SOURCE_MISSING` | 来源未出现在知识卡 |
| `QA_UNKNOWN_MISSING` | 未知项无法从知识卡还原 |
| `QA_SAFETY_REWRITTEN` | 安全区不是 FACT 原文 |
| `QA_RENDER_DIGEST` | 渲染产物缺失或摘要不符 |
| `QA_PRINT_PDF` | PDF 结构或页数不对 |
| `QA_LAYOUT` | 布局报告几何失败 |
| `QA_UNDECLARED_FILE` | 渲染目录有未声明文件 |
| `QA_REVIEW_NOT_READY` | 机器 QA 未通过 |
| `QA_REVIEW_ALREADY_RECORDED` | 复核已记录 |
| `QA_REVIEW_ACTOR_REQUIRED` | 缺少合法人类 actor |
| `QA_REVIEW_DECISION` | 决策不是 approve/reject |
| `QA_IO_ERROR` | 读写失败 |
