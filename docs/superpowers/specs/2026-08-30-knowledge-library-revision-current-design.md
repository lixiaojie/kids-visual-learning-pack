# Knowledge Library：candidate、不可变 revision 与 current pointer

- Status: Approved for this execution tranche
- Date: 2026-08-30
- Related: ADR-002、[Knowledge Core 设计](2026-08-19-knowledge-core-and-projection-architecture-design.md) §4.2 / §13.2 / §18.5、[四对象合同](../../knowledge-core-contract-pilot-evidence.md)、ADR-003
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

在个人服务器侧增加一个**进程内知识库**，使本地 authoring 产出的四对象包可以：

1. 作为闭包完整的 private **candidate** 被接收；
2. 以不可变 **revision** 目录长期保存；
3. 用 **current pointer** 标明当前知识；过期且 `expiry_behavior=unlist_current` 时从 current 列表消失，历史 revision 保留。

本设计满足 Spec §18.5「经独立设计后增加 revision、current、freshness 和 candidate 管理」。它不授权 HTTP、SQLite、Portal 或现网接线。

## 2. 非目标

- 不把 draft 上传为服务器对象（Spec §11.2 / §13.2）。
- 不原地把 candidate 改成 published。晋升必须写入新的 publish-stage 包（可同内容、必须新 revision 号，沿用 AUTHOR-04）。
- 不修改四对象 validator：`unlist_current` 在 Publish 阶段仍阻断**新发布**；下架是 library 对已保存 revision 在 `now` 下的解释。
- 不复用 subscriber `CandidateStore`（那是四卡 packet 字节暂存，内容寻址，不是知识 revision）。
- 不新增第五个治理对象。pointer 与 audit 是 library 元数据。
- 不复制 Knowledge Core 字段表。来源、命题、时效、Learning / Projection 的内容权威仍是 [2026-08-19 设计](2026-08-19-knowledge-core-and-projection-architecture-design.md) 与 KNOW-02 合同。

本层只保证两件事：

1. **依赖关系**：四对象作为整体被引用；`learning-spec` → `knowledge-core`、`projection-spec` → `learning-spec`、manifest 绑定三文档摘要；命题图内的 `supersedes` / 先修等关系留在 `knowledge-core.json` 内，库不另建关系表。
2. **历史版本真相**：每个 `revision-NNNN/` 不可覆盖；current 只是 pointer；pointer 变化写入 `current-audit.jsonl`；下架或替换不删除旧目录。identity 是 `knowledge_revision_record`（`object_id`、`revision`、三文档 sha256、`final_content_lock_sha256`）。

## 3. 对象与权威

输入是已编译的 `KnowledgeBundle`（或等价的包目录）。服务器：

- 用 `parse_canonical_document` 读四对象；
- 按 manifest 声明加载 artifact 字节；
- 调用 `validate_bundle`；
- 用 `knowledge_revision_record` 复算 identity（`object_id`、`revision`、三文档 sha256、`final_content_lock_sha256`）。

客户端自报摘要若不匹配复算结果，fail closed。不信任 lifecycle、health 或 lock 字段的字面值以外、未经校验的声明。

`topic_slug` 取自 `knowledge-core.object_id` 的 `core.<slug>` 形式，且必须匹配 authoring slug：`^[a-z][a-z0-9-]{2,63}$`。

## 4. 目录布局

```text
{library_root}/
  {topic_slug}/
    revision-NNNN/          # 不可变；NNNN 为零填充四位
      knowledge-core.json
      learning-spec.json
      projection-spec.json
      manifest.json
      validation.json       # artifact
      artifacts/...
    current.json            # pointer；不是治理对象
    current-audit.jsonl     # 只追加
```

写入 revision 使用临时目录 + `os.replace`，已存在则 `LIBRARY_REVISION_EXISTS`。禁止覆盖、禁止跟随符号链接。

## 5. 操作

| 操作 | 校验 | 写 revision | 改 current |
| --- | --- | --- | --- |
| `accept_candidate` | Candidate 闭包；`lifecycle=candidate`；非 draft | 是 | 否 |
| `publish` | Publish 门禁；`lifecycle` ∈ {validated, published} | 是 | 是（指向新 revision） |
| `get_current(now)` | 复算 identity；按 `now` 解释 freshness | 否 | 否（只读） |
| `unlist_current` | 主题存在 | 否 | 清空 pointer 并审计 |
| `refresh_current(now)` | 若 current 指向的 revision 在 `now` 满足 unlist | 否 | 满足时清空并审计 |

Candidate 不得成为 current。Publish 不得指向未通过 Publish 门禁的 revision。

`get_current` 在下列情况返回空（历史目录仍在）：

- 无 pointer 或 pointer 已清空；
- 所指 revision 存在命题 `valid_until <= now` 且 `expiry_behavior=unlist_current`。

`block_publish` 过期不自动下架；它只阻止新 Publish（validator 已如此）。`review_due` 仍可列为 current。

Pointer 变化必须追加审计行：时间、主题、旧 revision、新 revision（空表示下架）、原因码。

## 6. current.json

```json
{
  "schema": "cognitive-card-knowledge-library-current-v1",
  "topic_slug": "rabbit",
  "revision": 1,
  "identity": {
    "object_id": "core.rabbit",
    "revision": 1,
    "knowledge_core_sha256": "<hex>",
    "learning_spec_sha256": "<hex>",
    "projection_spec_sha256": "<hex>",
    "final_content_lock_sha256": "sha256:<hex>"
  },
  "set_at": "2026-08-30T00:00:00Z",
  "reason": "publish"
}
```

下架时 `revision` 为 `null`，`identity` 为 `null`，`reason` 为 `unlist_current` 或 `refresh_unlist`。读取时若 pointer 中的 identity 与磁盘复算不一致，fail closed，不得静默当作 current。

## 7. CLI

`python3 -m cognitive_card_server.knowledge_library.cli`

- `accept-candidate --package-dir --library-root`
- `publish --package-dir --library-root`
- `current --topic --library-root [--now]`
- `unlist --topic --library-root`
- `refresh --topic --library-root [--now]`

成功与失败均输出一行 canonical JSON。不联网、不写 HTTP/DB。

## 8. 验收

- 兔子 publish 后 `current` 指向 `revision-0001`。
- Candidate（含 review-due / 已过期 unlist 的 AUTHOR-04 包）写入后 current 仍空。
- 同一 `revision-NNNN` 第二次写入失败，第一次目录不变。
- 先 publish 未到期的 `unlist_current` 包，再以 `valid_until` 之后的 `now` 读取：不列为 current，目录仍在。
- 替换 revision publish 后 current 指向新号，旧目录保留。
- 篡改 lock / 对象摘要的包被拒绝。
- 本批不改 validator、不接 HTTP、不 merge 进 `main`。
