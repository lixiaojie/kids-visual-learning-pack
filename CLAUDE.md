@AGENTS.md

# Claude Code Adapter

本文件只是 Claude Code 的适配层。跨 Agent 通用工程规则的唯一来源是 `AGENTS.md`，本文件不复制其内容。上方的 `@AGENTS.md` 为 Claude Code 的文件导入语法；如果当前版本不支持导入，必须先手动完整阅读 `AGENTS.md`，再继续工作。

开始任务前读取：

- @docs/ai/CURRENT_TASK.md
- @docs/ai/HANDOFF.md

工作要求：

- 严格遵守 AGENTS.md。
- 不修改当前任务范围外文件。
- 不覆盖未提交修改。
- 完成前执行 AGENTS.md 第 5、8 节中的验证命令。
- 结束前更新 docs/ai/HANDOFF.md。
