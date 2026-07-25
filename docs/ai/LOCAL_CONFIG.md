# Local Private Configuration

本文件只说明本地私有配置的边界，**不记录任何真实值**。

## 不得提交到 Git 的内容

- Claude Code 登录信息
- Codex 登录信息
- Kimi Code 登录信息
- API Key 和 Token
- OAuth 凭证、Cookie
- 内部 LLM Proxy 地址
- 内部模型名称
- 本机用户名和绝对路径
- 个人 MCP 配置
- Shell alias 与 Shell 配置
- 私人权限配置
- `migration/card-os/inventory-roots.local.json` 等本机路径配置（已被 `.gitignore` 忽略）

## Recommended Storage

- macOS Keychain
- 操作系统凭证管理器
- 未被 Git 跟踪的本地配置文件
- 用户级客户端配置目录（如 `~/.claude/`、`~/.codex/`、`~/.kimi-code/`，本次基础设施不修改这些目录）

## Prohibited

- 把真实 Key 写进 `AGENTS.md`
- 把真实 Key 写进 `CLAUDE.md`
- 把真实 Key 写进 `.env.example`
- 把真实 Key 写进脚本
- 把真实 Key 输出到 `HANDOFF.md`
- 把本机绝对路径写进仓库文档（文档中使用相对路径）

## 占位符约定

文档和示例中只允许使用明显的占位符，例如:

```text
YOUR_API_KEY
https://example.invalid
```

## 既有相关约定

- `.gitignore` 已忽略 `migration/card-os/inventory-roots.local.json`（本机盘点根目录）。
- `ops/cognitive-card-server/env/card-os.env` 是仓库内的服务端路径配置模板，不含密钥；新增密钥类字段一律不得提交。
- Card OS 生产 token 的保管与使用方式见 `docs/operations/cognitive-card-server-deployment-2026-07-14.md`，该手册只使用占位符示例。
