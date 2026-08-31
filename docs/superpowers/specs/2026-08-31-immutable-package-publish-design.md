# 不可变 package 发布（PUBLISH-01）

- Status: Approved for this execution tranche
- Date: 2026-08-31
- Related: [ADR-001](../../decisions/ADR-001-card-os-client-contract-and-production-core-ownership.md)、[ADR-002](../../decisions/ADR-002-knowledge-core-and-projection-architecture.md)、[ADR-004](../../decisions/ADR-004-single-operator-main-flow.md)、[系统总设计 §4.4 / §10](../../cognitive-card-os-system-design.md)、[QA-01](2026-08-31-strict-qa-human-review-design.md)、[LIB-01](2026-08-30-knowledge-library-revision-current-design.md)
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把 QA-01 **已批准**的锁定四卡产物写成服务器权威的不可变 package revision：

1. 只消费 `approved` 报告与 RENDER-01 产物，不回写 Knowledge Core，不发明命题；
2. 每个 `revision-NNNN/` 只写一次；已存在目录不得覆盖；
3. 撤回与替代只改 current pointer 并追加历史；旧 revision 字节保留。

本设计满足路线图 PUBLISH-01 完成条件。公网画廊与下载 URL 仍属 PORTAL-01。

## 2. 非目标

- 不改四对象 schema、v1 FACT 键集、packet 契约、AUTHOR-05 默认表。
- 不等于 PORTAL-01 / ACCEPT-01 / TMPL-01 / KNOW-01 / AGE-02。
- 不把存档 `e78c2fa` 上传面、客户端 package-v5 打包器或恐龙 visual vocabulary 钉死合入。
- 不接线现有 subscriber `JobState` / HTTP / SQLite 任务表。
- 不新增 HTTP 端点；不 merge server `main`；不 push；不现网。
- 不做容量门禁、备份硬化或公网授权下载。本机 `revision` 目录即本批次的下载句柄。

## 3. 在分层中的位置

```text
Knowledge Core          事实；禁止呈现方案
        ↓
AGE-01 + CONV-01        儿童表达
        ↓
锁定 production-record  content_lock + 四卡文本 + FACT
        ↓
RENDER-01               四页 A4 PNG + PDF
        ↓
QA-01                   机器门禁 → awaiting_review → 人工 approve
        ↓
PUBLISH-01（本设计）    不可变 package revision + current pointer
        ↓
PORTAL-01               后期；本批次不挂 URL
```

Package 是 Artifact 层，不是第五个治理对象。Knowledge library 的 revision 仍是知识权威；本层不改写它。

## 4. 准入

同时具备才发布：

| 条件 | 失败码 |
| --- | --- |
| QA 报告 schema 为 `cognitive-card-os-qa-report-v1` 且可复算为规范 JSON | `PUBLISH_QA_REQUIRED` |
| `status=approved` 且 `review.decision=approve` | `PUBLISH_NOT_APPROVED` |
| 人类 `actor` 去空白后非空，且不是 `publish-01-v1` / `qa-01-v1` / `machine` | `PUBLISH_ACTOR_REQUIRED` |
| `package_slug` 匹配 `^[a-z][a-z0-9-]{2,63}$` | `PUBLISH_SLUG_INVALID` |
| 渲染目录四页 PNG、`print.pdf` 复算摘要等于报告中的 `render_output_sha256` | `PUBLISH_RENDER_DIGEST` |
| 报告 `content_lock_sha256` 等于锁定记录声明值 | `PUBLISH_LOCK_MISMATCH` |

`reject` / `awaiting_review` / `machine_failed` 一律不得发布。

抢救（ADR-001）采用存档 package-v5 的**合同**（不可变包、内容锁贯穿 manifest、撤回/替代保留历史），不是其客户端打包器或未关闭 Block 的上传面。

## 5. 目录与身份

```text
{catalog_root}/
  {package_slug}/
    revision-NNNN/          # 不可变；NNNN 为零填充四位
      manifest.json
      qa-report.json
      sources.json
      cards/cn-observe.png
      cards/en-observe.png
      cards/cn-know.png
      cards/en-know.png
      print.pdf
    current.json            # pointer；不是治理对象
    history.jsonl           # 只追加
```

写入使用临时目录 + `os.replace`。目标已存在则 `PUBLISH_REVISION_EXISTS`。禁止覆盖、禁止跟随符号链接。

身份（content identity）由服务器复算，不信任客户端自报：

- `package_slug`
- `content_lock_sha256`
- `render_output_sha256`
- `qa_report_sha256`
- 各 artifact 相对路径与 SHA-256

`package_sha256` 是上述字段的规范摘要。`revision` 不进入 content identity，因此相同内容不会因编号变化被当成新包。

## 6. 操作

| 操作 | 写 revision | 改 current | 历史关系 |
| --- | --- | --- | --- |
| `publish` 且无 current | 下一序号 | 指向新 revision | `supersedes=null` |
| `publish` 且 current 内容身份相同 | 否 | 否 | 幂等返回已有 current |
| `publish` 且 current 内容不同 | 下一序号 | 指向新 revision | `supersedes=旧序号`；旧目录保留 |
| `publish` 且某历史 revision 内容身份相同 | 否 | 指向该历史 revision | 撤回后再发同一包，不复制字节 |
| `withdraw` | 否 | 清空 pointer | 审计 `from_revision` → `null` |

current 只是 pointer。撤回不是删除。替代不是覆盖。

`current.json` 中的 identity 与磁盘复算不一致时 fail closed。

本机授权路径：`{catalog_root}/{slug}/revision-NNNN/`。PORTAL-01 再把它映射为下载 URL。

## 7. CLI

`python3 -m cognitive_card_server.four_card_publish`

- `publish --record --qa-dir --render-dir --catalog-root --slug --actor [--now]`
- `current --slug --catalog-root`
- `withdraw --slug --catalog-root --actor [--now]`

成功与失败均输出一行 canonical JSON。不联网、不写 HTTP/DB。

## 8. 验收

- 合成兔子 `age-5-6`：QA `approve` 后 `publish` 得到 `revision-0001`，`current` 指向它。
- 再发不同渲染摘要：`revision-0002` 的 `supersedes=1`，`revision-0001` 字节不变。
- 对已存在目录原地再写：失败，原文件不变。
- `withdraw` 后 `current` 为空，历史目录仍在；再发同一内容只恢复 pointer。
- 未批准报告、空 actor：fail closed。
- 本设计不授权 merge 进 server `main`、不授权现网。

## 9. 错误码

| 码 | 含义 |
| --- | --- |
| `PUBLISH_QA_REQUIRED` | 缺少或非规范 approved QA 报告 |
| `PUBLISH_NOT_APPROVED` | 报告不是人工批准态 |
| `PUBLISH_ACTOR_REQUIRED` | 缺少合法人类 actor |
| `PUBLISH_SLUG_INVALID` | slug 不合法 |
| `PUBLISH_LOCK_MISMATCH` | 内容锁与 QA/渲染不一致 |
| `PUBLISH_RENDER_DIGEST` | 渲染字节或摘要不符 |
| `PUBLISH_REVISION_EXISTS` | 目标 revision 已存在 |
| `PUBLISH_POINTER_MISMATCH` | current pointer 与磁盘身份不一致 |
| `PUBLISH_NOT_CURRENT` | 无 current 可撤回 |
| `PUBLISH_UNSAFE_ROOT` | catalog 根不安全（符号链接等） |
| `PUBLISH_IO_ERROR` | 读写失败 |
