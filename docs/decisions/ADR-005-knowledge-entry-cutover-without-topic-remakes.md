# ADR-005: 知识入口可在 C 级冻结后切换，不必等主题重制

- Status: Accepted
- Date: 2026-08-31
- Owners: 项目所有者（2026-08-31 书面授权：SITE-01 先并行验收再切主入口；SITE-02 只做旧 URL 映射与回滚开关）
- Related Task: SITE-01（`docs/ai/CURRENT_TASK.md`）
- Related Files: `docs/cognitive-card-os-system-design.md` §12、`docs/cognitive-card-os-asset-migration-inventory.md` §11、`docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`

## Context

系统总设计 §12.3 与 MIG-01 切换门禁要求：旧站 13 个知识主题全部具有「已迁移 package 或明确归档决定」，并完成链接/权限/打印/移动端验收后，才能把主入口从 `kids-world` 交给 Card OS。

13 个现站主题在 MIG-01 中已定为 C 级：旧网页槽位不能机械映射为四卡，须按新工作流重制（MIG-03）。若把「已迁移 package」当作 SITE-01 门禁，入口切换会无限期等待重制。

用户本会话将 SITE-01 收窄为知识入口替换（并行可访问，再切主 CTA），并把旧 URL 映射与回滚开关留给 SITE-02。

## Decision

1. **MIG-01 对 13 个主题的 C 级重制决定，视为 SITE-01 入口切换所需的明确冻结/归档决定。** 旧主题继续由冻结的 `kids-world` 提供，不进入 PUBLISH-01 catalog，也不因旧站曾展示而出现在画廊。
2. **SITE-01 只切换知识入口，不完成主题迁移。** 主 CTA 指向 PORTAL-01 画廊；旧站降为档案入口。
3. **SITE-02 只做旧 URL 映射与回滚开关。** 不把 MIG-03 重制并进 SITE-02。
4. **系统总设计 §12.3 第 6 步的「13 主题 package」不再阻塞 SITE-01。** 它仍阻塞把旧站从可达档案中删除，以及把旧 URL 静默 404。

本 ADR 不改变 ADR-002 分层，也不改变 PORTAL-01 的公开/owner 隔离。

## Alternatives Considered

### Option A: 等 13 个主题全部重制后再切入口

优点：主入口与四卡覆盖一次对齐。缺点：C 级重制是独立内容工作流，会把已完成的画廊挡在公网入口之外。未采用。

### Option B: 入口切换时删除或重定向全部旧主题 URL

优点：用户只看见新站。缺点：旧链接会静默 404；映射与回滚属于 SITE-02。未采用。

### Option C: C 级冻结后切换入口，旧站并行可达（本 ADR）

优点：对准「先并行、再切主入口」；重制与 URL 映射可后续独立进行。采用。

## Consequences

### Positive

- SITE-01 可以在 PORTAL-01 完成后立即替换知识主 CTA。
- 旧主题在重制完成前仍可打开，不会因为入口切换而消失。

### Negative

- 主入口画廊与旧站主题集合暂时不一致；用户可能从新入口看不到蝉、恐龙等旧主题，除非走档案入口。

### Risks

- 把 C 级冻结理解成「可以当正式 package 发布」。禁止：正式发布仍须 PUBLISH-01。
- 未先更新 Nginx 就部署根入口，用户会打到 capabilities 307。现网顺序必须先 snippet、后根入口。

## Migration or Rollout

1. 仓库内交付 `activeMode=card-os` 的入口合同、根 `index.html` 与 Nginx snippet。
2. 授权现网时先 reload Nginx 画廊反代，再部署静态根入口。
3. SITE-02 把根 hub 接到 `activeMode` 生成器，并为 13 个冻结 slug 提供 hash 映射与独立路径替代说明页。一次部署回滚：`activeMode=parallel` → `node scripts/render-knowledge-entry.mjs --write-hub` → 既有静态部署。

## Verification

- 路线图 SITE-01 完成条件不再要求 13 个四卡 package。
- `shared/knowledge-entry.json` 列出 13 个冻结 slug。
- 生产根入口不删除 `boards/kids-world/`。

## References

- `docs/cognitive-card-os-system-design.md` §12
- `docs/cognitive-card-os-asset-migration-inventory.md`
- `docs/superpowers/specs/2026-08-31-published-artifact-gallery-design.md`
- `docs/superpowers/specs/2026-08-31-card-os-kids-world-knowledge-entry-design.md`
