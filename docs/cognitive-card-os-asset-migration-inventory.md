# Cognitive Card OS 历史资产迁移清单

状态：发现阶段  
发现日期：2026-07-13  
整体策略：[Cognitive Card OS 整体设计](cognitive-card-os-system-design.md#12-网站替换与历史资产迁移)  
动态任务：[Cognitive Card OS 路线图](cognitive-card-os-roadmap.md)

## 1. 清单用途

本文记录历史资产的位置、规模、结构完整度和迁移等级，是迁移工作的来源清单，不是正式 package manifest。

本轮只执行只读发现：

- 未复制、移动、删除或重命名任何文件；
- 未把旧资产写入服务器；
- 未将旧网页公开状态等同于 Card OS 发布状态；
- 未在发现阶段为缺失的 FACT、来源、命题或 CONTENT LOCK 编造内容。

正式迁移前，`MIG-01` 必须为每个候选文件计算 SHA-256、媒体类型、像素/页面信息、来源别名和重复组。

## 2. 发现范围

本轮扫描：

- `/Users/admin/Documents/kids-visual-learning-pack`；
- `/Users/admin/Documents/Codex` 下的 `outputs`、`output`、`assets` 和相关 manifest；
- 用户指定的 Codex 任务 `019f02ca-cf3c-79e0-919d-9f8b90a076db`；
- 该任务对应的生成图源目录。

同时对 `/Users/admin/Documents` 下常见资产目录进行了规模筛查。与儿童知识卡无关的金融、PPT、个人照片、论文和第三方依赖资产不进入本清单。

## 3. 资产组总览

| 组 ID | 来源 | 发现规模 | 等级 | 决定 |
| --- | --- | ---: | --- | --- |
| `rabbit-full-v01` | 2026-07-11 兔子任务 | 40 个文件、12 张 PNG、1 个 PDF | A | 严格复验后优先导入 |
| `paleobiology-packages-20260707` | 当前项目 `outputs/` | 6 个包候选、5 个概念 | B | 升级 manifest、复算并去重 |
| `shenzhen-plants-20260626` | 指定 Codex 任务 | 14 张 PNG、1 份工作流文档、约 24 MB | C | 保留双面图，按新四卡体系重建 |
| `kids-world-current` | 当前 `kids-world` | 13 个主题、87 PNG + 87 WebP、约 228 MB | C | 主题级重制，图片单独评估 |
| `kids-world-batch-20260612` | 6 月批量生图任务 | 190 个文件，其中 188 张图片、约 229 MB | C/D | 与现站和后续重生成批次做摘要去重 |
| `kids-world-regenerated-20260614` | 6 月重生成任务 | 35 个文件，其中 32 张图片、约 192 MB | C/D | 识别替代版本与未采用版本 |
| `llm-last-image-20260614` | 单图补生成任务 | 1 张图片、约 3.3 MB | C/D | 通过文件名与摘要归并到对应主题 |
| `kids-world-older-copies` | 5 月及其他 Codex 工作目录 | 多组旧图片副本 | D | 仅作 provenance 别名，不重复导入 |
| `spider-verse` | 旧故事主题 | 约 133 MB | D/旧版馆 | 保留独立体验，不转四卡 |
| `paw-patrol` | 旧任务主题 | 约 132 KB 代码与页面资源 | D/旧版馆 | 保留独立体验，不转四卡 |
| `temporary-validation` | `tmp/` 和测试目录 | 多组验证副本 | D | 不进入正式资产库 |

## 4. A 级候选：兔子完整包

来源根目录：

```text
/Users/admin/Documents/Codex/2026-07-11/new-chat/outputs/life/animal_mammal/rabbit/
20260712_214042__rabbit__full_package__v01/
```

已发现：

- normalized request 与 routing record；
- FACT、sources、semantic core、proposition alignment、unknowns、COPY 和 CONTENT LOCK；
- 四卡 final content；
- page prompts、image brief 和 generation input；
- 四张 high-visual 成品、四张 source、四张 text-faithful 成品；
- A4 打印 PDF 和 print metadata；
- classification、age/language、bilingual、family、image、print 和 manifest QA；
- family 与 style token 快照；
- package manifest。

迁移决定：作为首个 A 级导入夹具。导入前仍需用服务器目标版本重新运行 manifest、声明文件、摘要、模板身份和未声明文件检查。

## 5. B 级候选：古生物包

当前项目中发现 6 个含根 manifest 的目录，加上兔子以外共涉及以下古生物概念：

- Tyrannosaurus rex；
- Stegosaurus；
- Triceratops；
- Parasaurolophus；
- Pterosaurs。

另有一份较早的 Stegosaurus 包，构成同概念重复候选。古生物包普遍包含 FACT、semantic core、cards、CONTENT LOCK、提示和四张高视觉卡，但部分导出轨或打印轨标记为 `NOT_REQUESTED`，且 schema 与当前严格 manifest 需要重新核对。

迁移决定：

1. 先按 package 根目录计算摘要和结构差异；
2. 对两份 Stegosaurus 选择内容更完整、校验更严格的一份作为升级来源，另一份保留 provenance；
3. 复算现行分类、模板、命题、COPY、样式和资产声明；
4. 缺少打印或 text-faithful 的包不得伪装为全轨 package，可升级生成后发布新 revision。

## 6. C 级候选：深圳植物双面卡

Codex 任务：`019f02ca-cf3c-79e0-919d-9f8b90a076db`  
工作目录：`/Users/admin/Documents/Codex/2026-06-26/h/outputs`

| 对象 | 观察卡 | 知识卡 | 当前限制 |
| --- | --- | --- | --- |
| 凤凰木 | 有 | 有 | 仅中文双面图，缺现行 manifest 与四卡命题链 |
| 水石榕 | 有 | 有 | 同上 |
| 鹅掌藤 | 有 | 有 | 同上 |
| 合欢树 | 有 | 有 | 同上 |
| 红继木 | 有 | 有 | 名称与园艺类型需重新核验 |
| 洋紫荆 | 有 | 有 | 中文名指代存在地区差异，必须保留混淆边界 |
| 新几内亚凤仙花 | 有 | 有 | 园艺类型与地点级花期需重新核验 |

该任务还保存了 `自然认知卡片工作流.md`，以及 14 张对应的生成源图。源图和输出图用于 provenance 对照，不因视觉上完整而直接升级为 A/B 级。

迁移决定：为每个植物创建新的明确请求，补齐分类、年龄、语言、来源和参考样式；现有图片可作为 `reference_style` 或候选视觉素材。正式发布必须重新生成或验证中文观察、英文观察、中文知识、英文知识四页和内容锁。

## 7. C 级候选：旧 `kids-world`

当前站点发现：

- 13 个主题 JSON；
- 87 张 PNG 原图；
- 87 张同名 WebP 浏览副本；
- 中文主题数据、英文 locale overlay、图片生成 manifest、交互规则和主题注册表。

知识主题包括生命、人体、地球、太空、工程与技术等多种 domain/form。旧主题页面的 hero、mechanism、compare、object icons、click task 和 parent guide 不是现行四卡槽位，不能机械映射为 CN/EN observation/knowledge pages。

迁移决定：以“主题”为迁移单元：

1. 从旧 JSON 提取对象、文案、交互和图片关系；
2. 重新分类并选择现行模板族；
3. 对事实和来源重新核验；
4. 生成新的命题、四卡和 CONTENT LOCK；
5. 将通过视觉与版权检查的旧图片登记为候选参考或补充资产；
6. 新 package 发布前，旧主题继续由兼容页提供。

## 8. 批量生图与重复资产

发现三个主要批次：

- 2026-06-12：188 张图片；
- 2026-06-14 重生成：32 张图片；
- 2026-06-14 补最后一张：1 张图片。

这些批次与当前 `kids-world/public/assets` 存在明显的文件名重合，另有 5 月工作目录保存早期副本。本轮没有仅凭名称判断哪一份是最终版本。

正式去重规则：

- 内容相同：按 SHA-256 合并为一个内容对象，保留多条来源路径；
- 文件名相同但内容不同：建立 version candidate 组，通过现站引用、生成批次时间、视觉 QA 和人工选择确定角色；
- PNG 与 WebP：记录为 source/derivative 关系，不当作重复垃圾直接删除；
- 未被现站引用的重生成图片：保留为候选或归档，不自动发布。

## 9. D 级和非迁移范围

- `spider-verse` 与 `paw-patrol` 保持旧版主题馆入口；
- `dist/`、`tmp/`、测试输出和 `.DS_Store` 不导入正式资产库；
- 本地 skill 备份中的模板注册表属于规则资产，不按内容 package 迁移；
- 与儿童知识卡无关的工作目录和个人资料不进入清单；
- 版权或来源不清的素材在完成权利审查前保持归档状态。

## 10. 正式迁移记录

`MIG-01` 生成的机器清单每项至少包含：

```json
{
  "migration_asset_id": "mig_...",
  "source_path": "...",
  "source_thread_id": "...",
  "sha256": "...",
  "size_bytes": 0,
  "media_type": "...",
  "object_name": "...",
  "classification": {},
  "rights_status": "review_required",
  "structural_evidence": {
    "fact": false,
    "propositions": false,
    "content_lock": false,
    "four_cards": false,
    "qa": false,
    "print_pdf": false
  },
  "migration_grade": "C",
  "duplicate_group": null,
  "target_package_id": null,
  "decision": "rebuild"
}
```

`size_bytes`、摘要、分类、权利状态和目标 package 只由正式盘点与审核写入；发现文档不为尚未核实的字段提供推测值。

## 11. 切换门禁

旧知识站只有在以下条件全部满足后才能从主入口退出：

- 13 个旧主题全部有已迁移 package 或明确归档决定；
- 新站的搜索、详情、四卡预览、PDF、来源、QA 和版本历史可用；
- 手机与桌面主要路径通过验收；
- 旧链接具有兼容页、重定向或明确替代说明；
- 新旧资产的摘要映射和 provenance 可查询；
- 备份、恢复、容量和回滚已经演练；
- `spider-verse` 与 `paw-patrol` 的旧版主题馆入口未被误删。
