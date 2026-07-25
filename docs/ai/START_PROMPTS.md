# 标准启动提示词

以下提示词可直接复制到任一 Agent(Claude Code / Codex / Kimi Code）会话开头使用。Kimi Code 在当前版本会自动读取根目录 `AGENTS.md`；若你使用的客户端没有自动读取规则文件，把对应提示词完整粘贴为会话首条消息。

启动协议与结束协议的权威定义在 `AGENTS.md` 第 3 节和第 11 节；以下提示词与之保持一致，如发生冲突以 `AGENTS.md` 为准。

## 1. 恢复当前任务（含启动协议）

```text
请按序执行启动协议:

1. 确认当前 Git 仓库根目录(git rev-parse --show-toplevel);
2. 检查当前分支(git branch --show-current);
3. 检查未提交修改(git status --short);
4. 读取 AGENTS.md;
5. 读取 docs/ai/CURRENT_TASK.md;
6. 读取 docs/ai/HANDOFF.md;
7. 读取与当前任务有关的架构文档和 ADR。

然后向我报告:仓库根目录、当前分支、未提交修改、当前任务目标、In Scope、Out of Scope、Acceptance Criteria、HANDOFF 中的 Exact Next Action、本次预计修改范围。

完成上述核实后再修改文件。不要依赖之前的会话记忆,不要修改范围外文件,不要求通读整个仓库,只针对任务探索相关代码和文档。完成后执行规定验证,并按结束协议更新 docs/ai/HANDOFF.md(附 git diff --check 与 git status --short 结果)。
```

## 2. 启动新任务

```text
请先读取 AGENTS.md、docs/ai/BACKLOG.md、相关架构文档和 ADR。

当前需要处理的新任务是:

【在此填写任务】

先检查它是否与现有 CURRENT_TASK.md 冲突。基于代码和文档整理 Objective、Acceptance Criteria、In Scope、Out of Scope、Constraints 和 Verification Plan,并更新 CURRENT_TASK.md。

在任务边界明确后再实施。不要把无关重构加入任务。
```

## 3. 只做代码审查

```text
请读取 AGENTS.md、CURRENT_TASK.md、HANDOFF.md,并检查当前 Git diff。

本次只做代码审查，不修改文件。

重点检查:

1. 是否满足 Acceptance Criteria;
2. 是否违反架构约束;
3. 是否存在兼容性问题;
4. 是否存在错误处理遗漏;
5. 测试是否充分;
6. 文档与代码是否一致;
7. 是否修改了范围外内容。

按严重级别输出问题，并为每个问题提供文件路径、位置、影响和修复建议。没有证据的问题不要推测。
```

## 4. 任务交接（含结束协议）

```text
请执行结束协议,基于当前 Git 状态、实际代码修改和已经执行的验证,更新 docs/ai/HANDOFF.md。

不得根据会话印象填写。必须按序完成:

1. 检查实际 Git 状态(git status --short、git branch --show-current);
2. 更新 docs/ai/HANDOFF.md;
3. 记录实际修改文件(以 git status / git diff 为准);
4. 记录实际运行的验证命令;
5. 记录 PASS、WARN 和 FAIL;
6. 记录已知失败是否与本次修改相关及判断依据;
7. 记录剩余工作;
8. 写出 Exact Next Action(下一位 Agent 可直接执行的具体动作);
9. 执行 git diff --check;
10. 输出 git status --short。

不要声称未验证的内容已经完成。可运行 bash scripts/ai/check-handoff.sh 自查交接质量。
```

## 5. 基础设施自检

```text
请检查多 Agent 工程基础设施是否完整。

检查:

- AGENTS.md 是否为唯一通用规则源;
- CLAUDE.md 是否只做适配;
- CURRENT_TASK、HANDOFF、BACKLOG 是否职责清晰;
- 是否存在重复或冲突规则;
- 是否有凭证或本地路径进入 Git;
- 构建和测试命令是否有仓库依据;
- HANDOFF 是否能让另一个 Agent 直接接手;
- 文档是否存在 TBD、TODO、占位符或虚构信息。

只修复基础设施文件，不修改业务代码。可先运行 bash scripts/ai/check-agent-infra.sh 获得机械检查结果。
```
