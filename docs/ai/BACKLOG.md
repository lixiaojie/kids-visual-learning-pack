# Backlog

本文件只收录**尚未进入当前执行范围**、且在仓库中有明确证据的事项。Card OS 专项任务不由本文件维护，见 `docs/cognitive-card-os-roadmap.md`（该文件是 Card OS 唯一动态任务账本）。执行范围以 `CURRENT_TASK.md` 为准；本文件不等于执行计划；不从聊天历史推测事项。

状态枚举:`Candidate` / `Ready` / `In Progress` / `Blocked` / `Done`
优先级枚举:`P0` / `P1` / `P2` / `P3`

| ID | Priority | Status | Item | Acceptance Criteria | Dependencies | Source |
| --- | --- | --- | --- | --- | --- | --- |
| B-001 | P2 | Candidate | 芋头宇宙 V2.1 批量生图（43 个资产）并导入 `boards/kids-world/public/assets/` | manifest 中 43 个资产的 PNG/WebP 同名配对落地，`npm run check:images` 通过 | 批量生图工具额度 | `docs/kids-world-image-generation-handoff.md`、`boards/kids-world/src/data/image-generation-manifest.json` |
| B-002 | P3 | Candidate | 修复 `boards/kids-world/structure.test.mjs` 既有断言失败（19 !== 18) | 该测试通过，且不通过删除断言掩盖问题 | 确认 19 与 18 哪个是当前结构真值 | 实测 `node boards/kids-world/structure.test.mjs`(2026-07-17) |
| B-003 | P2 | Candidate | Card OS 专项任务（KNOW-01、TMPL-01、AGE-01、API-01、AUTH-01、SKILL-01、OPS-01 等） | 以 roadmap 中各任务的完成条件为准 | 见 roadmap 各任务依赖 | `docs/cognitive-card-os-roadmap.md` |
| B-004 | P2 | Candidate | 新增 CI 轻量 job 执行 `bash scripts/ai/check-agent-state.sh` 作为服务端兜底 | CI 中该 job 存在且在 push/PR 时执行通过 | 选定 CI 平台（GitHub Actions 或 GitLab CI) | 2026-07-17 核查：本仓库无 CI 配置；建议片段见 `docs/ai/README.md` 第 12 节 |

说明:

- 只有进入正式执行范围的事项才迁移到 `CURRENT_TASK.md`。
- B-003 是引用条目，具体状态以 `docs/cognitive-card-os-roadmap.md` 为准，不在此重复维护。
