# ADR-004: 单人主流程优先与门禁裁剪

- Status: Accepted
- Date: 2026-08-30
- Owners: 项目所有者（2026-08-30 书面授权：单人维护、单人使用，先跑通主流程）
- Related Task: 单人主流程纳入整体计划（`docs/ai/CURRENT_TASK.md`）
- Related Files: `docs/cognitive-card-os-roadmap.md`、`docs/cognitive-card-os-system-design.md`、`docs/superpowers/specs/2026-08-30-knowledge-browse-projection-confirmation-design.md`、[ADR-001](ADR-001-card-os-client-contract-and-production-core-ownership.md)、[ADR-002](ADR-002-knowledge-core-and-projection-architecture.md)

## Context

知识管线在本地已具备四对象合同、authoring、library current、Projection 选择面和 loopback HTTP（`knowledge-pipeline-v1`，未进生产）。缺的是确认点 1 的人机界面：浏览源头知识并选择映射到哪种 Projection family。

与此同时，账本仍把两件「长期多用户 / 多终端」能力当成当前完成门禁：

1. SKILL-02 / ADR-001 验证条款要求第二台真实 Codex 电脑安装同一摘要。
2. OPS-01 要求加密、可校验、带告警的异地备份，以及容量/证书可投递告警。

当前运营事实是单人维护、单人使用。继续把第二台电脑和完整异地备份当作主流程门禁，会推迟「能看见知识、能确认呈现方案」这条最短路径。

本 ADR 不改变 ADR-001 的契约归属（packet 契约、生产核心在服务器），也不改变 ADR-002 的知识/学习/Projection 分层。

## Decision

1. **当前运营假设是单人维护、单人使用。** 主流程优先于长期多用户、多终端和运维硬化。后者保留为后续迭代，不从账本删除。
2. **单人知识主路径**定义为：结构化输入 → 四对象 revision → library current → **浏览并确认 Projection family** → 再进入接合 / 四卡执行。HTML 预览可以证明确认点 1；完整 Portal、打印站和旧站替换不在这条路径上。
3. **BROWSE-01 是确认点 1 的界面**，消费 library 与已有选择面。它不是 PORTAL-01。PORTAL-01 仍是已发布 Artifact 的只读画廊，保持 BACKLOG。
4. **SKILL-02 在单人门禁下标记 DONE。** 已满足：本机代码、两个隔离安装、现网领取与上传。第二台真实电脑安装同一摘要改为后期 `SKILL-03`，不阻塞 SKILL-02 或主流程。
5. **OPS-01 在单人门禁下以本机恢复点为完成条件。** 已有本机 SQLite/候选备份、manifest 校验、隔离恢复和 14 天保留即足够。加密异地副本、容量/证书可投递告警改为 `OPS-02` BACKLOG。异地不做独立子系统：需要时由维护者把已验证的本机备份目录拷到第二块盘或另一台机器，不设计加密复制服务、不设计告警栈。
6. 浏览器会话、只读 MCP、SITE-01、UPLOAD-01、第二终端、异地备份**均不作为单人主路径门禁**。AUTH-01 已部署的 machine token 继续使用；浏览器会话不提前立项挡 BROWSE-01。

## Alternatives Considered

### Option A: 保持第二台电脑与加密异地备份为当前门禁

优点：多终端与灾难恢复一次做完。缺点：单人项目没有第二终端可验收；完整异地设计会变成未使用的运维面。未采用：与「先跑通主流程」冲突。

### Option B: 把确认点 1 并进 PORTAL-01 再一起做

优点：一个门户覆盖浏览。缺点：PORTAL-01 依赖发布包、PDF、权限隔离，范围远大于确认点 1；会再次推迟知识可见。未采用。

### Option C: 单人主路径 + 把门禁后置（本 ADR）

优点：最短路径对准「看见知识、确认映射」；历史验收记录保留；后期多用户能力仍有任务号。采用。

## Consequences

### Positive

- 下一步产品工作对准 BROWSE-01，而不是第二台电脑或备份子系统。
- SKILL-02 / OPS-01 不再用不可控的外部条件卡住账本。
- PORTAL-01 与知识浏览的职责分开，避免 8 层表单或把 family 写进 Knowledge Core。

### Negative

- 单机故障会丢失本机备份；接受为单人阶段风险，用 OPS-02  eventual 手工拷贝缓解。
- 第二台电脑从未实证安装同一摘要；多终端阶段必须补 SKILL-03，不能把单人 DONE 当成跨终端证明。

### Risks

- 「简化异地备份」被理解成「可以不备份」。本机 timer 与隔离恢复仍必须保持。
- 把 BROWSE-01 做成可编辑 CMS 或第五个治理对象。设计禁止：只读浏览 + 展示选择面；覆盖 family 仍走 CLI 重编译。

## Migration or Rollout

1. 更新路线图状态、近期执行顺序与系统总设计交付阶段。
2. ADR-001 验证条款中「两台电脑才可标记 SKILL-02 DONE」由本 ADR 取代；packet 契约正文不变。
3. 运维记录 §8 与 OPS-01 完成条件对齐本机恢复点；异地项移到 OPS-02。
4. BROWSE-01 实现另立 CURRENT_TASK；本 ADR 不授权写代码、merge 或现网。

## Verification

- 路线图中 SKILL-02 为 `DONE`，SKILL-03 为 `BACKLOG`；OPS-01 为本机恢复点 `DONE`，OPS-02 为 `BACKLOG`。
- 近期执行顺序以 BROWSE-01 为下一产品切片，不列第二台电脑或异地备份。
- BROWSE-01 设计明确：不在 Knowledge Core 内存呈现方案；不等于 PORTAL-01。

## References

- `docs/cognitive-card-os-roadmap.md`
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md` §11.1
- `docs/superpowers/specs/2026-08-30-projection-family-selection-design.md`
- `docs/operations/cognitive-card-server-deployment-2026-07-14.md` §8
