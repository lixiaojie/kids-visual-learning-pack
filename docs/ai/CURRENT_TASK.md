# Current Task

## Metadata

- Updated At: 2026-08-21
- Updated By: OpenAI Codex
- Status: Done
- Branch: main（kids 任务治理）；codex/knowledge-core-contract-v1（服务器隔离实现）
- Base Commit: kids 0257a86；server 9c1b82be69df2da8348f66970a993e9c1984ce6d
- Server Implementation Commit: 120e5fcc48e4e6cabb1a28678379f687553c0788

## Objective

实现最小 local authoring MVP，跑通“结构化主题输入 → 四个治理对象 → Publish 校验 → revision 产物目录 → 本地浏览页”的单条端到端路径。首版复用已验证的 Knowledge Core Contract，不引入联网生成、服务器 API、数据库或正式 Renderer。

## Background

- `KNOW-02` 四对象合同已完成并通过独立复审；合同与 AUTHOR-01 已固化到 server commit `120e5fc`。
- 当前 Codex/人工负责提供来源、证据和命题；authoring 工具只做确定性标准化、编译、校验与物化，不自行发明事实。
- 用户要求优先形成实际功能闭环，减少研发框架投入；本批按 bounded 设计直接 TDD，不新增架构 Spec 或实施计划。

## Acceptance Criteria

- [x] 标准库 CLI 可读取简化 authoring request，生成四对象 JSON、validation 记录和 `artifacts/index.html`
- [x] 输出目录按安全 topic slug 与 revision 隔离，目标已存在时 fail closed 且不改写既有文件
- [x] `single/composite` 默认 `chaptered-guide`，`progressive` 默认 `progressive-exploration`；`four-card` 仅显式请求时启用
- [x] 生成的 bundle 通过现有 Publish validation；无效输入输出稳定错误且不留下半成品目录
- [x] 浏览页只展示来源、命题、知识单元、学习路径、Projection slots 和验证结果，不声称是最终儿童 Renderer
- [x] 提供一个 synthetic rabbit composite 示例请求与本地运行说明
- [x] CLI 不交互追问；成功包保存 Publish validation issue list，任何 validation issue 都以结构化错误交还上层且不物化目录
- [x] focused authoring/contract tests PASS；使用 server 声明的 test dependencies 跑完整 suite `444` 项 PASS；文档与 handoff 同步
- [x] server 实现已按用户 2026-08-21 授权 commit；未 push、merge、deploy、启动服务、修改生产配置或执行第二台电脑验证

## In Scope

- server src/cognitive_card_server/knowledge_contract/authoring.py
- server `src/cognitive_card_server/knowledge_contract/__init__.py`
- server tests/test_knowledge_contract_authoring.py
- server examples/authoring/rabbit-composite.json
- server `README.md`
- kids `docs/cognitive-card-os-roadmap.md`
- kids `docs/ai/CURRENT_TASK.md`
- kids `docs/ai/HANDOFF.md`

## Out of Scope

- LLM/API/联网检索或事实自动生成
- Web 表单、HTTP route、数据库、server revision/current API
- 正式儿童 Renderer、图片、PDF、打印 QA、Portal 与部署
- four-card `production-record` converter 与历史迁移
- 覆盖用户既有 `outputs/`
- commit、push、merge、部署和第二台电脑验证

## Constraints

- 直接调用现有 `knowledge_contract` model/validator，不复制或弱化四对象 schema。
- Python 标准库实现；所有写入先在同父目录临时目录完成，Publish validation 通过后再原子落位。
- 输入必须显式包含来源和命题；缺失事实治理信息时 fail closed，不生成占位知识。
- 浏览页必须 HTML escape 所有输入文本，不执行用户提供的 HTML/脚本。
- 普通路径不增加交互式确认；Projection 使用确定性默认值，可由显式字段覆盖。

## Verification Plan

```bash
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_authoring -v
PYTHONPATH=src python3 -m unittest tests.test_knowledge_contract_model tests.test_knowledge_contract_validation tests.test_knowledge_contract_fixtures tests.test_knowledge_contract_authoring -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m py_compile src/cognitive_card_server/knowledge_contract/authoring.py tests/test_knowledge_contract_authoring.py
```
- server/kids `git diff --check`
- `bash scripts/ai/check-agent-state.sh`

## Relevant References

- `docs/decisions/ADR-002-knowledge-core-and-projection-architecture.md`
- `docs/superpowers/specs/2026-08-19-knowledge-core-and-projection-architecture-design.md`
- `docs/knowledge-core-contract-pilot-evidence.md`
- `docs/cognitive-card-os-system-design.md`
- `docs/cognitive-card-os-roadmap.md`
