# Knowledge Library HTTP/DB 受控接线

- Status: Approved for this execution tranche
- Date: 2026-08-30
- Related: ADR-002、ADR-003、[Knowledge Core 设计](2026-08-19-knowledge-core-and-projection-architecture-design.md) §13.2 / §18.5、[LIB-01](2026-08-30-knowledge-library-revision-current-design.md)、[PROJ-01](2026-08-30-projection-family-selection-design.md)、API-01
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把已落地的进程内知识库与 Projection 选择面接到现有 loopback HTTP 应用，并使接合 generation-input 在进入 SQLite compiled-job 之前核对 library **current**：

1. HTTP 调用 `KnowledgeLibrary` 与 `select_projection_family`，不复制写入规则；
2. 接合密封仅当声明的 `knowledge_revision` 等于当前 current identity 时可以存储并创建 job；
3. v1 FACT 密封路径保持兼容，不要求 library。

本设计满足 Spec §13.2「服务器验证并保存闭包完整的 private candidate、管理不可变 revisions 与 current pointer」，且不把本批做成 Portal。

## 2. 非目标

- 不 merge 进 server `main`，不 push，不现网，不改生产必填环境变量。
- 不新增 SQLite 表，不把四对象 JSON 或 current pointer 镜像进数据库。
- 不复用 subscriber `CandidateStore`。
- 不新增第五个治理对象；选择面仍不持久化。
- 不改 v1 FACT 密封合同、AUTHOR-05 默认表、四对象 schema、validator family 枚举。
- 不建设 Portal、Renderer、调度器或浏览器会话。

## 3. 存储权威

| 状态 | 权威 | 本批 |
| --- | --- | --- |
| 四对象 revision 字节 | `{library_root}/{topic}/revision-NNNN/` | 不变；默认 `CARD_OS_CANDIDATE_ROOT/knowledge-library` |
| current pointer / audit | `current.json`、`current-audit.jsonl` | 不变 |
| 密封 generation-input | `GenerationInputStore`（内容寻址文件） | 接合与 v1 共用；按 schema 分支校验 |
| jobs / packets / tokens | 现有 SQLite | 接合 job 仍只存 lock digest；不新增列 |
| Projection 选择 | 每次请求重算 | 不写盘 |

HTTP 适配器禁止实现第二套 accept/publish/unlist 规则。

## 4. HTTP 面

前缀仍为 `/card-os/api/v1`。写路径必须进入 `PROTECTED_ROUTES`（鉴权先于 body）。`now` 只用应用 clock，不接受客户端覆盖。

| 方法 | 路径 | Scope | 行为 |
| --- | --- | --- | --- |
| POST | `/admin/knowledge-library/candidates` | `compiler_import` | `accept_candidate`；不设 current |
| POST | `/admin/knowledge-library/publish` | `admin` | `publish`；设 current |
| GET | `/knowledge-library/{topic}/current` | `read` | `get_current`；无 current 时 `listed=false`、HTTP 200 |
| POST | `/admin/knowledge-library/{topic}/unlist` | `admin` | `unlist_current` |
| POST | `/admin/knowledge-library/{topic}/refresh` | `admin` | `refresh_current` |
| POST | `/projection-family` | `read` | `signals_from_request` + `select_projection_family` |

`{topic}` 与 library slug 相同：`^[a-z][a-z0-9-]{2,63}$`。

包 POST JSON 精确键：

```json
{
  "knowledge_core": {},
  "learning_spec": {},
  "projection_spec": {},
  "manifest": {},
  "artifacts": {"relative/path": "<base64>"}
}
```

服务器用 canonical parse 重建 `KnowledgeBundle`，复算 identity 与 artifact digest；不信任客户端 lock 字面值。成功响应含 `topic_slug`、`revision`、`identity`、`lifecycle`、`current`（publish 为 true）。

选择面请求体为 authoring request（或等价结构）；响应为已有 `ProjectionSelection.as_dict()`。未知 family fail closed。

## 5. 接合与 SQLite 门禁

`POST /admin/generation-inputs` 与 `POST /admin/compiled-jobs` 保持现有路径与 scope。

- payload `schema` 为 v1 generation-input：现有 `validate_generation_input`；不读 library。
- payload `schema` 为接合 `cognitive-card-generation-input-knowledge-revision-v1`：
  1. 从声明的 `knowledge_revision.object_id` 取 topic；
  2. `get_current(topic, now)` 必须存在；
  3. current identity 必须与声明记录逐字段相等，否则 fail closed；
  4. 用磁盘上的四对象复算 `validate_joined_generation_input`；
  5. 通过后才写入 GenerationInputStore / 创建 SQLite compiled-job。

Candidate 或已 unlist 的 revision 不能创建执行 job。历史目录仍保留。GET 接合密封时同样核对 current，避免过期知识继续发给 executor。

不把 `knowledge_revision` 写成新的 job 列：job 的 `content_lock_digest` 已是接合 lock；权威仍在 library 文件与密封字节。

## 6. 错误映射

`KnowledgeContractError` 与 `GenerationInputError` 不得变成 `INTERNAL_ERROR`。稳定码映射：

| 码 | HTTP |
| --- | --- |
| `LIBRARY_REVISION_EXISTS`、`KNOWLEDGE_LIBRARY_REVISION_NOT_CURRENT`、`LIBRARY_POINTER_MISMATCH` | 409 |
| `LIBRARY_TOPIC_MISSING`、`KNOWLEDGE_LIBRARY_CURRENT_NOT_FOUND`、`*_NOT_FOUND` | 404 |
| 其余 library / projection-family / join 校验失败 | 400 |
| 既有 AUTH / protocol 码 | 不变 |

## 7. 验收

- 兔子 authoring 包经 HTTP publish 后 GET current 列出 revision 1 与复算 identity。
- 同一 revision 第二次 publish 返回 409，目录不变。
- Candidate HTTP 写入后 current 仍 `listed=false`。
- 接合密封在未 publish / identity 不匹配 / unlist 之后不能入库或建 job；v1 FACT 密封仍能建 job。
- 省略 family 的兔子 request 经 HTTP 选择面 chosen 仍为 `chaptered-guide`；`four-card` 不会被推荐。
- submitter 不能 publish 或 import；reader 不能 publish。
- 本批不改 validator、不新增 SQLite 表、不 merge 进 `main`。
