# 兔子端到端验收（ACCEPT-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-001](../../decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §10 / §11](../../cognitive-card-os-system-design.md)、[CONV-01](2026-08-30-knowledge-four-card-converter-design.md)、[AGE-01](2026-08-31-age-language-adapter-design.md)、[RENDER-01](2026-08-31-locked-four-card-render-design.md)、[QA-01](2026-08-31-strict-qa-human-review-design.md)、[PUBLISH-01](2026-08-31-immutable-package-publish-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

用一条真实兔子主题，把已落地的知识主路径串成可验收交付：

1. 正式输入固定为兔子、深圳、`age-5-6`、中英双语、打印版；
2. 从四对象 revision / library current 到四卡 PNG、A4 PDF、机器 QA、人工复核、不可变 package；
3. 本机用静态页查看**同一** `content_lock_sha256` 的知识浏览与 package 产物。

本设计满足路线图 ACCEPT-01 单人完成条件。公网画廊仍属 PORTAL-01；第二终端仍属 SKILL-03。

## 2. 非目标

- 不改四对象 schema、v1 FACT 键集、packet 契约、AUTHOR-05 默认表。
- 不等于 PORTAL-01 / KNOW-01 / TMPL-01 / AGE-02 / ACCEPT-02。
- 不实现完整 `production-record-v1` 生成器，不调用外部模型，不发明命题。
- 不把 RUN-01 的 HTTP packet 领取/提交再跑一遍；该闭合已由 `c55f51b` 证明。
- 不新增公网 HTTP 端点；不 merge server `main`；不 push；不现网。

## 3. 在分层中的位置

```text
正式输入                rabbit-real.json + Shenzhen four-card request
        ↓
authoring + four-card   运行时覆盖 projection.family；不改夹具文件
        ↓
library current         不可变知识 revision
        ↓
BROWSE-01               确认点 1 静态 HTML
        ↓
CONV-01 + AGE-01        current → 儿童表达 FACT → 接合密封
        ↓
LOCK（本批）            确定性锁定四卡记录；不是第五个治理对象
        ↓
RENDER-01               四页 A4 PNG + PDF
        ↓
QA-01                   机器门禁 → awaiting_review → 人工 approve
        ↓
PUBLISH-01              不可变 package revision + current pointer
        ↓
本机查看页              file:// 同一 content_lock_sha256；不是 PORTAL
```

确定性 lock 替代本路径上的 Codex generate。完整 production-record 闭合与高视觉仍留给后续 generate / TMPL。

## 4. 正式输入

同时满足才进入验收编排：

| 条件 | 失败码 |
| --- | --- |
| authoring 主题 `slug=rabbit`，来源为 AUTHOR-02 `rabbit-real.json` | `ACCEPT_INPUT_TOPIC` |
| four-card `object.name` 为 `rabbit` 或 `兔子` | `ACCEPT_INPUT_OBJECT` |
| `object.use_location` 为 `Shenzhen` 或 `深圳` | `ACCEPT_INPUT_LOCATION` |
| `age.main.profile_id=age-5-6`，CN 同档，EN `beginner`，`language.output=bilingual` | `ACCEPT_INPUT_AGE_LANGUAGE` |
| `output.request=print` | `ACCEPT_INPUT_OUTPUT` |
| 运行时 `projection.family=four-card`；默认 chaptered-guide 不得直接转换 | 沿用 `CONVERTER_FAMILY_NOT_FOUR_CARD` |

不把 `four-card` 写回 `examples/authoring/rabbit-real.json`。AUTHOR-05 默认表保持 `chaptered-guide`。

分类、地点、年龄、输出形态由 authoring 受控分类与 `usage` 提供；`--request` 可选。见 [KNOW-01](2026-08-31-classification-registry-design.md)。

## 5. 确定性锁定

输入：CONV-01 接合密封中的 `generation_input`（已含 AGE-01 FACT 与 snapshot 解析的 mammal family）。

输出：RENDER-01 / QA-01 消费的锁定记录（`normalized_request`、`fact`、`cards`、`resolved_family`、`content_lock`）。

规则：

1. 只投影 FACT 已有命题、来源、未知项边界和安全原文；不得添加 claim。
2. 知识卡 `appearance` 与 `uncertainty` 按英文排版行数装箱；装不下的命题全文落到 `sources` 区（仍带命题 id），避免 A4 溢出。两页命题 id 集合必须等于 FACT。
3. 观察卡 `look` 使用已出现在同语言知识卡上的命题；`record` 保持空清场区；`copy` / `trace` 由 RENDER-01 按 `copy_plan` 覆盖。
4. `safety` 区等于 FACT `safety` 原文；`sources` 区包含全部 FACT `source_id`。
5. `content_lock.sha256` 由服务器复算 `artifacts + change_policy`。
6. Knowledge Core 文件不得被写入。

失败码：`LOCK_FACT_INVALID`、`LOCK_FAMILY_GAP`、`LOCK_PAGE_ORDER`、`LOCK_OVERFLOW_RISK`（若分区后仍无法落入 mammal 四区合同）。

## 6. 本机同一版本

验收编排在工作根写出：

```text
{work_root}/
  library/                  # 知识 current
  browse/index.html         # 确认点 1
  convert/joined.json
  record/locked-record.json
  render/                   # 四页 PNG + print.pdf
  qa/qa-report.json
  catalog/{slug}/revision-NNNN/
  view/index.html           # 指向上述同一 lock
```

`view/index.html` 展示 `content_lock_sha256`、QA actor、package revision 路径，并链到四页、PDF 与 browse。它是本机文件，不是 `/card-os/` 公网门户。

人类 actor 不得为 `qa-01-v1` / `publish-01-v1` / `machine`。单人验收使用 `owner`。

## 7. CLI

`python3 -m cognitive_card_server.four_card_lock`

- `--input` 接合密封或内层 generation-input JSON
- `--output` 锁定记录
- `--repo-root`

`python3 -m cognitive_card_server.four_card_accept`

- `--authoring` `--request` `--repo-root` `--work-root` `--actor` `[--slug] [--now]`
- `--snapshot-id` / `--registry-commit` 默认 active catalog 条目

成功与失败均输出一行 canonical JSON。不联网、不写公网 HTTP。

## 8. 验收

- AUTHOR-02 真实兔子 + Shenzhen request：package `current` 存在，四页与 PDF 可打开，QA `approved`。
- 本机 `view/index.html` 与 package revision、browse 页报告同一 `content_lock_sha256`。
- 知识库 `knowledge-core.json` 字节在转换/锁定/渲染/发布前后一致。
- 省略 four-card family 时转换失败；错误地点/年龄 fail closed。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 9. 错误码

| 码 | 含义 |
| --- | --- |
| `ACCEPT_INPUT_TOPIC` | authoring 不是兔子主题 |
| `ACCEPT_INPUT_OBJECT` | 请求对象名不是兔子 |
| `ACCEPT_INPUT_LOCATION` | 使用地点不是深圳 |
| `ACCEPT_INPUT_AGE_LANGUAGE` | 年龄或语言不是 age-5-6 双语 |
| `ACCEPT_INPUT_OUTPUT` | 输出不是 print |
| `LOCK_FACT_INVALID` | FACT 无法投影为四卡 |
| `LOCK_FAMILY_GAP` | snapshot family 缺少页序或分区 |
| `LOCK_PAGE_ORDER` | 页序不是固定四页 |
| `ACCEPT_VIEW_MISMATCH` | 本机查看页与 package lock 不一致 |
| `ACCEPT_QA_FAILED` | 机器 QA 未进入 awaiting_review |
| `ACCEPT_CORE_MUTATED` | 知识库 Knowledge Core 字节被改写 |
