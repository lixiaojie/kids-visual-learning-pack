# Cognitive Card OS 路线图与任务账本

状态：活动中  
最近更新：2026-07-14
整体设计：[Cognitive Card OS 整体设计](cognitive-card-os-system-design.md)

## 1. 维护规则

本文是 Cognitive Card OS 唯一动态待办账本。

状态只使用：

- `DONE`：实现、验证和必要审查全部完成；
- `IN PROGRESS`：已有活动实施批次；
- `READY`：依赖满足，可立即进入设计或实施；
- `BLOCKED`：存在明确外部阻塞；
- `BACKLOG`：已定义但尚未达到开始条件；
- `REQUIRES AUDIT`：历史上做过工作，但当前状态需要重新核实。

每个任务必须记录权威仓库、依赖和可验证的完成条件。设计通过不等于实现完成；代码存在也不等于部署完成。

## 2. 当前里程碑

**M1：可远程领取与提交**

目标：一个安装薄 Skill 的受信任 Codex 客户端，通过 `www.yutou.space` 发现服务、登录 Card OS、领取生成包并上传候选结果；整个流程不需要 OpenAI API Key，也不传递 ChatGPT 身份。

M1 包含：`API-01`、`AUTH-01`、`PROTO-01`、`SKILL-01`、`SKILL-02`、`DEPLOY-01`。

资产迁移作为并行治理工作流推进，但在 API、认证和正式导入工具完成前不写入服务器。发现清单见 [历史资产迁移清单](cognitive-card-os-asset-migration-inventory.md)。

## 3. 总览

| ID | 工作流 | 状态 | 下一动作 |
| --- | --- | --- | --- |
| GOV-01 | 总设计与唯一任务账本 | DONE | 后续变更持续更新 |
| KNOW-01 | 分类与对象类型体系 | IN PROGRESS | 做覆盖矩阵与缺口测试 |
| TMPL-01 | 领域/形态模板族 | IN PROGRESS | 补齐模板注册表和跨对象夹具 |
| AGE-01 | 3–4、5–6 岁配置 | IN PROGRESS | 服务端化并验证路由 |
| AGE-02 | 8、10、15 岁配置 | BACKLOG | 分年龄建立认知与语言规范 |
| EXEC-01 | 订阅执行核心 | DONE | 作为 API 应用服务使用 |
| API-01 | HTTPS 写入 API | IN PROGRESS | 将已验证的锁定任务 API 部署到 HTTPS；自由规范化任务入口另行设计 |
| AUTH-01 | Card OS 身份与权限 | IN PROGRESS | 部署 machine scoped token；补浏览器会话与轮换操作面 |
| PROTO-01 | capability/protocol discovery | DONE | 作为 Skill 注册表和部署兼容门禁使用 |
| SKILL-01 | Skill 发布注册表 | READY | 设计不可变 release、摘要、stable 与回滚 |
| SKILL-02 | 薄 Skill 客户端 | BLOCKED | 等待 API/AUTH 部署与 SKILL-01 可安装 release |
| MIG-01 | 历史资产发现、摘要与去重清单 | DONE | 人工复核重复与衍生候选，等待 MIG-02 导入条件 |
| MIG-02 | A/B 级结构化 package 导入 | BACKLOG | 依赖导入接口、严格验证和 MIG-01 |
| MIG-03 | C 级旧主题重制 | BACKLOG | 依赖模板、发布链路和 MIG-01 |
| PORTAL-01 | 只读资产门户 | BACKLOG | 依赖认证和资产查询 API |
| UPLOAD-01 | 浏览器手动上传 | BACKLOG | 依赖 AUTH-01、API-01 |
| SITE-01 | Card OS 替换 `kids-world` | BACKLOG | 依赖门户、发布和迁移覆盖 |
| SITE-02 | 旧站兼容与重定向 | BACKLOG | 依赖 SITE-01 切换门禁 |
| RENDER-01 | 四卡排版与打印 PDF | BACKLOG | 依赖内容锁和资产接口 |
| QA-01 | 严格 QA 与人工复核 | BACKLOG | 依赖 RENDER-01 |
| PUBLISH-01 | 不可变 package 发布 | BACKLOG | 依赖 QA-01 |
| MCP-01 | 只读 MCP | BACKLOG | 依赖稳定查询 API |
| DEPLOY-01 | Card OS 服务部署 | IN PROGRESS | 按实施计划完成本地 release 验证与服务器部署 |
| OPS-01 | 容量、备份与监控治理 | IN PROGRESS | 按已审计基线实施备份、恢复和告警 |
| ACCEPT-01 | 兔子完整验收 | BACKLOG | 依赖发布链路 |
| ACCEPT-02 | 第二个哺乳动物一致性验收 | BACKLOG | 依赖 ACCEPT-01 与模板族 |

## 4. 任务明细

### GOV-01 总设计与治理入口

- 状态：`DONE`
- 权威仓库：`kids-visual-learning-pack`
- 产物：整体设计、路线图、README 导航、子系统文档索引。
- 完成条件：整体边界、权威来源、路线图状态语义和文档更新规则明确。

### KNOW-01 分类与对象类型覆盖

- 状态：`IN PROGRESS`
- 权威来源：当前 `cognitive-card-os` 分类规范；目标迁入服务器版本化注册表。
- 已有：领域、概念形态、领域自有 subtype、稳定 machine value 和分类停机规则。
- 待办：
  - 建立 `domain x form x subtype` 覆盖矩阵；
  - 为尚未出现首个对象的领域补充 subtype 词表；
  - 为 `general`、`other` 和 `CLASSIFICATION_REVIEW` 增加边界夹具；
  - 将注册表、版本和摘要纳入服务器权威发布。
- 完成条件：所有受控枚举可机器校验；新增概念不会靠自由文本绕过分类。

### TMPL-01 领域与形态模板体系

- 状态：`IN PROGRESS`
- 已有：哺乳动物 3–4、5–6 岁精确模板，以及多个 domain/form 家族和受控 fallback。
- 待办：
  - 建立模板族覆盖报告；
  - 记录每个 family 的固定四页骨架、槽位、年龄/语言适配和结构指纹；
  - 为每个已启用大类配置至少两个对象夹具；
  - 保证次领域和次形态只能激活已声明模块；
  - 将模板发布、回滚和兼容矩阵迁入服务器。
- 完成条件：相同主路由得到稳定骨架；模板缺口返回 `TEMPLATE_GAP`，不静默套用错误模板。

### AGE-01 现有年龄与语言配置

- 状态：`IN PROGRESS`
- 范围：`age-3-4`、`age-5-6`、CN 同年龄配置、EN `beginner`。
- 待办：把年龄与语言规则发布为带版本的服务器适配器；增加跨对象事实不漂移和 COPY 来源测试。
- 完成条件：年龄只改变表达与任务负荷；四卡命题、确定性和安全边界保持一致。

### AGE-02 未来年龄升级

- 状态：`BACKLOG`
- 范围：分别设计约 8、10、15 岁的独立年龄配置。
- 依赖：AGE-01 稳定、每个年龄拥有代表性对象和语言验收集。
- 完成条件：每个年龄带有独立阅读、因果、系统、证据、任务负荷和 QA 规则；请求按一个主年龄版本输出。

### EXEC-01 订阅执行核心

- 状态：`DONE`
- 权威仓库：`https://github.com/lixiaojie/cognitive-card-server`（私有）
- 版本：`0.2.0`
- 提交：`b74c401bd8f04aa5e765cd4d1e8cdccf8f0bf596`
- 已完成：SQLite 事务、任务状态、生成包、租约、幂等结果、候选隔离存储、摘要校验、审计、撤销和恢复。
- 验证：133 项测试通过；完整分支审查为 Critical 0、Important 0、Minor 0。

### API-01 HTTPS 应用 API

- 状态：`IN PROGRESS`
- 权威仓库：`cognitive-card-server`
- 依赖：EXEC-01。
- 已实现批次：服务版本 `0.3.0`，提交 `dc043ba4473915ebbd1a98c76dab46fcba703de3`；提供 health、capability、锁定任务、包签发/领取/完成、候选结果提交、状态与事件查询共 11 条路径。
- 已验证：273 项测试连续通过；真实 Uvicorn 并发认领、重启恢复、幂等、媒体/大小限制、鉴权先于 body 解析、凭据零写入和日志脱敏均覆盖；whole-branch 审查为 Critical 0、Important 0、Minor 0。
- 第一批端点职责：
  - 健康和 capability 查询；
  - 创建规范化任务；
  - 查询任务状态；
  - 领取和下载生成包；
  - 标记客户端生成完成；
  - 上传 manifest 与候选文件；
  - 查询稳定错误和审计摘要。
- 约束：HTTP 适配器不复制状态机；只调用现有应用服务。请求必须有大小、超时、媒体类型和幂等限制。
- `0.3.0` 批次验收：真实 HTTP 集成测试覆盖正常流程、错误码、重启恢复和并发认领。
- `API-01` 完成条件：上述批次保持通过；服务经 `www.yutou.space` 的 HTTPS 和持久化部署验收；受信任上游能把用户请求转换为规范化锁定任务，而服务器仍拒绝自由 payload 绕过内容锁。
- 未完成：通过 `www.yutou.space` 的 HTTPS 部署；把自由概念请求编译为规范化锁定任务的可信上游接口。因此当前批次不能被描述为通用概念创建 API。
- 实施计划：[远程 API、认证与协议实施计划](superpowers/plans/2026-07-13-cognitive-card-remote-api-auth-protocol-plan.md)。首批只接受可信上游产生的已锁定任务，不把自由主题输入伪装为服务器端知识编译。

### AUTH-01 Card OS 身份与权限

- 状态：`IN PROGRESS`
- 依赖：API-01 的路由边界。
- 范围：`read`、`submit`、`review`、`admin`；浏览器会话；CLI/Skill scoped token；撤销与轮换；审计 actor。
- 不包含：ChatGPT 登录代理、ChatGPT Cookie、OpenAI Token。
- 已实现：machine token 签发、列表和按 token ID 撤销；scope implication、过期与即时撤销；请求级仓储关闭；原始 token 只在签发时返回一次，日志和数据库仅保留安全标识/摘要。
- 未完成：浏览器会话、面向个人服务器运维的轮换流程和正式 TLS 部署验证。
- `0.3.0` 批次验收：machine token 最小权限生效；撤销立即阻止认领和提交；日志和数据库不含原始密钥。
- `AUTH-01` 完成条件：上述批次保持通过；浏览器会话、正式轮换/恢复流程和 TLS 部署身份边界完成验收。

### PROTO-01 协议发现与兼容

- 状态：`DONE`
- 依赖：EXEC-01。
- 范围：server version、protocol range、packet/result schema、minimum Skill release、capability flags 和稳定升级错误。
- 已完成：`0.3.0` capability 文档、规范无符号十进制协议头、minimum Skill release 检查，以及稳定的 `CLIENT_UPGRADE_REQUIRED` / `SERVER_UPGRADE_REQUIRED` 前置拒绝。
- 验证：不兼容请求在任务/包工作之前拒绝；版本、运行时包和 capability 版本一致；生产文档端点关闭。
- 完成条件：不兼容客户端在认领前收到 `CLIENT_UPGRADE_REQUIRED`；不兼容服务器在创建任务前收到 `SERVER_UPGRADE_REQUIRED`。

### SKILL-01 Skill 发布注册表

- 状态：`READY`
- 依赖：PROTO-01。
- 目标路径：
  - `/skill/v1/manifest.json`
  - `/skill/v1/releases/<version>/cognitive-card-os.zip`
  - `/skill/v1/releases/<version>/sha256.txt`
- 完成条件：发布不可变、摘要可验证、stable 可回滚、旧客户端可检测兼容性。

### SKILL-02 薄 Skill 客户端

- 状态：`BLOCKED`
- 依赖：API-01、AUTH-01、PROTO-01、SKILL-01。
- 阻塞：API/AUTH 尚未部署到个人服务器，且 SKILL-01 尚无可校验的安装 release；在此之前不发布依赖本地仓库状态的临时客户端。
- 范围：输入收集、本地形状校验、服务发现、任务创建、包领取、摘要确认、候选上传、错误解释、离线限制和版本升级。
- 完成条件：两台独立 Codex 客户端安装相同发布摘要，并能完成同一服务器上的任务领取与结果上传。

### MIG-01 历史资产发现、摘要与去重

- 状态：`DONE`
- 权威清单：[历史资产迁移清单](cognitive-card-os-asset-migration-inventory.md)。
- 已完成：10 个声明根全部只读扫描；808 个来源别名聚合为 622 个 SHA-256 内容对象，形成 170 个重复组、159 个同名不同内容候选组和 138 个 PNG/WebP 衍生候选组。
- 测量：来源总计 893,825,675 字节，唯一内容 571,623,546 字节；盘点前后设备/inode/路径/大小/mtime/ctime 摘要一致，内容级复现检查通过。
- warnings：共 70 条规则性跳过记录，其中 28 条 `excluded_name`、42 条 `unsupported_extension`；没有缺失根、不可读元数据、扫描中变化、不安全源项或媒体类型不匹配。
- 产物：[latest 指针](../migration/card-os/generated/latest.json)、[机器 inventory](../migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/inventory.json)、[重复报告](../migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/duplicate-report.md) 和 [warnings](../migration/card-os/generated/snapshots/inv_sha256_e69f1cf4ba70f2d63a3182465cc3db8c77778e08e2d51e454f636e1ed980d8bd/scan-warnings.json)。
- 后续：人工复核 170 个重复组、159 个同名候选组和 138 个衍生候选组；在导入 API、严格 package 验证和不可变存储就绪后启动 MIG-02，不在盘点阶段自动删除、选择或发布资产。
- 完成条件：每个候选文件有稳定 `migration_asset_id`；相同内容合并来源别名；无文件在盘点阶段被移动或删除。
- 实施计划：[历史资产机器清单与去重实施计划](superpowers/plans/2026-07-13-cognitive-card-asset-inventory-dedup-plan.md)。

### MIG-02 A/B 级结构化 package 导入

- 状态：`BACKLOG`
- 范围：兔子完整包，以及升级后的古生物包。
- 依赖：MIG-01、API-01、严格 package 验证和服务器不可变存储。
- 完成条件：所有声明文件、摘要、模板、内容锁和 QA 由目标服务器版本复算；重复 Stegosaurus 包有明确主来源和 provenance 关系。

### MIG-03 C 级旧主题重制

- 状态：`BACKLOG`
- 范围：7 种深圳植物、13 个旧 `kids-world` 知识主题和可复用旧图片。
- 依赖：TMPL-01、AGE-01、RENDER-01、QA-01、PUBLISH-01。
- 完成条件：每个迁移主题通过现行分类、来源、命题、四卡、内容锁、打印和 QA；旧图只作为审核过的素材或参考，不继承旧发布状态。

### PORTAL-01 只读资产门户

- 状态：`BACKLOG`
- 目标入口：`https://www.yutou.space/card-os/`
- 范围：搜索、筛选、四卡预览、PDF、manifest、来源、QA、摘要、版本历史和状态隔离。
- 完成条件：未授权用户看不到 owner-only、隔离或草稿资产；发布版本可稳定下载。

### UPLOAD-01 浏览器手动上传

- 状态：`BACKLOG`
- 依赖：AUTH-01、API-01。
- 范围：查看已领取生成包、上传声明文件、显示摘要和验证结果、按错误修正重试。
- 完成条件：不依赖 MCP 写能力即可完成 eligible packet；验证规则与薄 Skill 完全相同。

### SITE-01 Card OS 替换 `kids-world`

- 状态：`BACKLOG`
- 范围：以 `/card-os/` 提供新的知识首页、搜索、package 详情、四卡、PDF、来源、QA 和历史版本。
- 依赖：PORTAL-01、PUBLISH-01、MIG-01；13 个旧主题均有迁移或归档决定。
- 完成条件：新站通过移动端、桌面端、权限、打印和链接验收后成为主入口；`spider-verse` 与 `paw-patrol` 继续作为旧版主题馆。

### SITE-02 旧站兼容与重定向

- 状态：`BACKLOG`
- 依赖：SITE-01。
- 范围：旧 `kids-world` 只读兼容页、旧 URL 映射、替代说明、渐进重定向和回滚开关。
- 完成条件：已索引旧链接无静默 404；新旧 package/provenance 映射可查询；可在一次部署内回滚入口切换。

### RENDER-01 四卡与打印渲染

- 状态：`BACKLOG`
- 范围：固定四页顺序、文本忠实布局、图像轨、A4 PDF、字体与中英文断行、manifest 指纹。
- 完成条件：渲染器只消费内容锁；输出字节和渲染输入均有摘要；打印 QA 通过。

### QA-01 严格 QA 与人工复核

- 状态：`BACKLOG`
- 范围：分类、模板、命题、语言、COPY、来源、未知项、安全、图像、排版、未声明文件和内容锁复算。
- 完成条件：机器 QA 通过后才进入 `awaiting_review`；人工复核有明确 actor、决策和审计记录。

### PUBLISH-01 不可变发布

- 状态：`BACKLOG`
- 依赖：QA-01。
- 范围：package revision、manifest、四卡、PDF、来源、QA 摘要、创建历史和授权下载。
- 完成条件：发布版本不可原地修改；撤回和替代保留历史关系。

### MCP-01 只读 MCP

- 状态：`BACKLOG`
- 依赖：稳定的查询 API 和 AUTH-01。
- 范围：capability、注册表身份、任务状态、生成包检查、资产搜索、package metadata 和授权下载链接。
- 完成条件：MCP 不拥有独立状态机，不承担首版写入路径。

### DEPLOY-01 Card OS 服务部署

- 状态：`IN PROGRESS`
- 目标：个人服务器，域名 `www.yutou.space`。
- 依赖：API-01、AUTH-01 的最小可运行版本。
- 已完成：2026-07-14 完成现网只读审计并选择 systemd + Python venv + 版本化 release + Nginx 方案；正式设计见 [个人服务器部署设计](superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md)。
- 实施计划：[个人服务器部署实施计划](superpowers/plans/2026-07-14-cognitive-card-server-deployment-plan.md)。
- 待办：按计划完成运维工具、精确制品、服务进程、反向代理、TLS、持久化目录、非 root 运行用户、环境配置、备份、健康检查和回滚验收。
- 完成条件：通过域名访问；重启后任务和候选资产仍在；部署不影响现有 `/kids/` 内容。

### OPS-01 容量、备份与监控

- 状态：`IN PROGRESS`
- 已审计：2026-07-14 根磁盘使用率约 54%，可用约 18 GiB；Nginx、UFW、Docker/CouchDB、域名证书和现有站点路径已核实。详细基线与部署约束见 [个人服务器部署设计](superpowers/specs/2026-07-14-cognitive-card-server-deployment-design.md)。
- 待办：容量阈值、资产保留、SQLite 在线备份、候选文件快照、恢复演练、日志轮转、证书与健康告警；异地副本在本机恢复点稳定后单独实施。
- 完成条件：容量告警早于 75%；备份新鲜度可见；恢复演练重建数据库、资产摘要和未完成任务。

### ACCEPT-01 兔子端到端验收

- 状态：`BACKLOG`
- 输入：兔子、深圳、`age-5-6`、中英文、打印版。
- 完成条件：从正式输入到四卡、PDF、QA、复核和门户发布全链路完成；可从第二终端查看同一不可变版本。

### ACCEPT-02 第二个哺乳动物一致性验收

- 状态：`BACKLOG`
- 依赖：ACCEPT-01、TMPL-01。
- 对象选择规则：与兔子同为 `life + entity + animal/mammal`，但外观、习性和人与其关系足够不同。
- 完成条件：两者解析为同一模板族和固定骨架；差异只来自事实、可选槽位和图像元素。

## 5. 近期执行顺序

下一轮只启动一个可独立验收的子项目：

1. 执行 `DEPLOY-01`：把已验证的 `0.3.0` API/AUTH/PROTO 部署到个人服务器，完成 TLS、非 root 运行、持久化、备份和回滚门禁；
2. 执行 `SKILL-01`：发布不可变 Skill release、SHA-256、stable 指针和兼容回滚；
3. 部署验证通过后解除 `SKILL-02` 阻塞，实现在两个独立 Codex 客户端上可安装的薄客户端；
4. 人工复核 MIG-01 的 170 个重复组、159 个同名候选和 138 个衍生候选，不自动删除或选择来源；
5. 待严格 package 验证与服务器不可变存储就绪后启动 MIG-02。

门户、渲染和 MCP 不进入下一实现批次。

## 6. 更新记录

### 2026-07-14

- 完成远程锁定任务 API、machine scoped token 与 capability/protocol 批次；服务版本 `0.3.0`，273 项测试和 whole-branch C0/I0/M0 审查通过。
- 将 `PROTO-01` 标记为 `DONE`；`API-01`、`AUTH-01` 保持 `IN PROGRESS`，明确部署、自由规范化任务入口和浏览器会话尚未完成。
- 将 `SKILL-01` 转为 `READY`，并在 API/AUTH 部署和可安装 release 完成前把 `SKILL-02` 标记为 `BLOCKED`。
- 完成 MIG-01 机器清单与去重快照：10 个根、808 个来源别名、622 个内容对象；盘点前后守卫一致。

### 2026-07-13

- 建立整体设计和唯一任务账本。
- 记录订阅执行核心 `0.2.0` 完成状态。
- 将“可远程领取与提交”设为当前里程碑。
- 将 API、认证和协议发现设为下一独立设计批次。
- 确认 Cognitive Card OS 将替换 `kids-world` 知识站；旧故事主题保留为旧版主题馆。
- 扫描指定 Codex 任务及工作目录，建立历史资产迁移分级和双轨切换门禁。
