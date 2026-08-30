# Projection family 选择面

- Status: Approved for this execution tranche
- Date: 2026-08-30
- Related: ADR-002、ADR-003、[Knowledge Core 设计](2026-08-19-knowledge-core-and-projection-architecture-design.md) §3.6 / §9.3 / §11.1 / §16、AUTHOR-05
- Authority: kids 仓为产品规范；实现落在 server `knowledge-pipeline-v1`

## 1. 目标

把 authoring 里「scope_type → 一张默认表」升级为可解释的 **Projection family 选择面**：

1. 给出唯一推荐 family 和稳定理由；
2. 列出其余已注册 family 作为可选项，并标明适合 / 不推荐；
3. 用户显式请求时覆盖默认，但推荐结果仍可见；
4. `four-card` 保持 opt-in，不会被自动选中。

本设计满足 Spec §9.3，且不增加第三个确认点：选择发生在合并方案确认之前的自动推导里。CLI 与 HTML 预览只展示结果，不是 Portal。

## 2. 非目标

- 不新增 Projection family。注册表仍是 `four-card`、`chaptered-guide`、`progressive-exploration`、`time-sensitive-brief`。
- 不改四对象 schema，不把选择记录写成第五个治理对象，不新增 package 文件。
- 不改 validator 的 family 枚举集合；未知 family 在选择面与 validator 都 fail closed。
- 不改 AUTHOR-05 默认表：省略 `projection.family` 时，兔子/几何仍是 `chaptered-guide` / `progressive-exploration`；时效 fixture 若省略 family 仍是 `chaptered-guide`，`time-sensitive-brief` 仍须显式请求才会被 chosen。
- 不根据打印、设备或可访问性新增必填 request 字段。现有 `usage_context` / `languages` / `duration_minutes` 只作为适合度信号。
- 不接 HTTP、SQLite、Portal、Renderer。

## 3. 输入信号

选择面只读下列已存在字段，不发明事实：

| 信号 | 来源 |
| --- | --- |
| `scope_type` | Knowledge Scope / authoring `topic.scope_type` |
| `unit_count` | 当前 Scope 的 knowledge units |
| `prerequisite_count` | `prerequisite_of` 关系数 |
| `languages` | Learning Plan |
| `usage_context` | Learning Plan |
| `duration_minutes` | Learning Plan |
| `has_hard_expiry` | 任一非 `superseded` 命题的 `expiry_behavior` ∈ {`block_publish`, `unlist_current`} |
| `requested_family` | 可选；authoring `projection.family` |

信号可从结构化 request 或已编译的 `knowledge-core` + `learning-spec` 提取。两路必须得到相同 chosen。

## 4. 默认 chosen（冻结）

省略 `requested_family` 时，chosen = recommended，且等于现行 authoring 表：

| `scope_type` | recommended / default chosen |
| --- | --- |
| `single` | `chaptered-guide` |
| `composite` | `chaptered-guide` |
| `progressive` | `progressive-exploration` |

`four-card` 与 `time-sensitive-brief` **从不**进入 recommended，除非用户显式请求（此时 recommended 仍按上表，chosen 为请求值，`source=explicit`）。

这是有意保守：AUTHOR-05 证明默认路由 2/3 可用；时效主题的 family 是人工结构选择，不自动改写。

## 5. 适合度

每个已注册且未被 chosen 的 family 进入 `options`，`fit` 为 `eligible` 或 `discouraged`。本批没有 `ineligible` 桶：四个 family 都能绑定现有 local-html 槽位；显式请求 discouraged family 仍编译。未知 family 不进 options，直接错误。

| family | `discouraged` 当 |
| --- | --- |
| `four-card` | `scope_type=progressive`，或 `unit_count > 2`，或语言不是同时含 `zh-CN` 与 `en` |
| `chaptered-guide` | `scope_type=progressive`（会压平阶段） |
| `progressive-exploration` | `scope_type` 不是 `progressive` 且 `prerequisite_count=0` |
| `time-sensitive-brief` | 没有 `has_hard_expiry` |

其余情况为 `eligible`。`four-card` 即使 `eligible` 也只作为 option，不会成为 default recommended。

推荐理由码（稳定、机器可读）：

- `DEFAULT_SCOPE_SINGLE` / `DEFAULT_SCOPE_COMPOSITE` / `DEFAULT_SCOPE_PROGRESSIVE`
- `EXPLICIT_REQUEST`
- `COMPRESSES_COMPOSITE`
- `FLATTENS_PROGRESSIVE`
- `NO_PROGRESSION`
- `NOT_BILINGUAL`
- `HARD_EXPIRY_PRESENT` / `NO_HARD_EXPIRY`

## 6. 输出

```json
{
  "schema": "cognitive-card-projection-family-selection-v1",
  "chosen": "chaptered-guide",
  "source": "default",
  "recommended": {
    "family": "chaptered-guide",
    "reason_codes": ["DEFAULT_SCOPE_COMPOSITE"]
  },
  "options": [
    {
      "family": "four-card",
      "fit": "discouraged",
      "reason_codes": ["COMPRESSES_COMPOSITE"]
    }
  ]
}
```

`source` 为 `default` 或 `explicit`。`options` 按 family 名排序，不含 chosen。成功与失败均一行 canonical JSON。

## 7. 与 authoring / library 的边界

- authoring 用选择面的 `chosen` 填 `projection-spec.blueprint.family`，槽位策略仍按现行 family 分支（four-card 四槽、progressive 每节点一槽、其余 `main`）。
- HTML 预览增加 chosen / recommended / options 文本；package 文件集合不变。
- library 继续只存四对象 + artifacts；不解释 family。
- 改变 family 不得改变 `knowledge-core` 摘要（已有合同测试）。

## 8. CLI

`python3 -m cognitive_card_server.projection_family.cli suggest`

- `--input` authoring request JSON；或
- `--package-dir` 已编译包。读取 `knowledge-core.json` 与 `learning-spec.json`。若 `projection-spec.blueprint.family` 等于该 scope 的默认 recommended，视为 `source=default`；否则把已锁定 family 当作显式请求。

不联网、不写盘、不写 HTTP/DB。

## 9. 验收

- 兔子省略 family：chosen `chaptered-guide`，`source=default`；`four-card` 为 discouraged（单元数）。
- 几何省略 family：chosen `progressive-exploration`；`chaptered-guide` 为 discouraged。
- 时效 fixture 省略 family：chosen 仍 `chaptered-guide`；`time-sensitive-brief` 为 eligible。显式该 family 时 chosen 为它，recommended 仍是 `chaptered-guide`。
- 显式 `four-card` 的 single 主题：chosen `four-card`，recommended 仍按 scope 默认。
- `comic` 等未知值：选择面错误，不写 revision。
- 本批不改 validator 枚举、不接 HTTP、不 merge 进 `main`。
