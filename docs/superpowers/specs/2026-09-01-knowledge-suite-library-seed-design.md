# 兼容套件上库（KNOW-04）

- Status: Approved/Implemented
- Date: 2026-09-01
- Related: [KNOW-03](2026-09-01-entity-knowledge-coverage-design.md)、[KNOW-03-prod](../../cognitive-card-os-roadmap.md)、[LIB-01](2026-08-30-knowledge-library-revision-current-design.md)、[WB-01](2026-08-31-operator-knowledge-workbench-design.md)、[ADR-003](../../decisions/ADR-003-knowledge-pipeline-workspace-and-branch-governance.md)
- Authority: kids 仓为产品规范与运维证据；编译用 server `7aaeb2b`，不改 server Git

## 1. 目标

KNOW-03-prod 已把 coverage 应用装上现网。本刀只把本机兼容套件里**允许上库**的知识对象写成生产 `knowledge-library` current，让 `/card-os/ops/` 能列出它们。

允许上库：

| slug | 来源夹具 | 生产 revision |
| --- | --- | --- |
| `rabbit` | KNOW-03 修订 `rabbit-real.json`，编译时把 `topic.revision` 设为 `2` | `0002` 为 current；保留 AUTHOR-02 `0001` |
| `heptapleurum-arboricola` | `heptapleurum-arboricola.json` | `0001` current |
| `tyrannosaurus-rex` | `tyrannosaurus-rex.json` | `0001` current |
| `forbidden-city` | `forbidden-city.json` | `0001` current |
| `four-crossings-chishui` | `four-crossings-chishui.json` | `0001` current |
| `newton-first-law` | `newton-first-law.json` | `0001` current |

禁止上库：`spider-gwen`。夹具仍只在 server `examples/authoring/`。

## 2. 非目标

- 不换应用 `current`，不打新 release。
- 不 reload Nginx，不改 snippet。
- 不改公开画廊 catalog / ACCEPT-01 包。
- 不实施 WB-02 / WB-03 / API-01。
- 不 merge server `main`、不 push、不改 server 夹具文件（兔子 revision=2 只在编译副本上发生）。
- 不覆盖 `rabbit/revision-0001`。

## 3. 做法

1. 在 server worktree `7aaeb2b` 用 `compile_authoring_request` / `write_authoring_package` 编六份四对象包；`projection` 保持 `{}`。
2. 用 `KnowledgeLibrary.publish` 写入生产 `$CARD_OS_CANDIDATE_ROOT/knowledge-library`。
3. 目录属主保持 `cardos:cardos`；新 revision 不可覆盖已有同号目录。
4. 抽查：六主题 current 存在；无 `spider-gwen`；画廊 PDF 字节不变；无 token 的 ops HTML 仍无命题。

## 4. 回滚

只撤回本刀 library 写入时：

- 把 `rabbit/current.json` 指回 `revision-0001`；
- 删除五个新 topic 目录与 `rabbit/revision-0002`（仅在确认不是 AUTHOR-02 目录之后）；
- 不删 `rabbit/revision-0001`，不改应用 `current`，不 reload Nginx。

精确命令与哈希写入运维记录本批章节，不改写第 1–12 节。
