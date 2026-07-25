#!/usr/bin/env bash
# install-hooks.sh — 安装本仓库的 Git Hook(仓库副本级,每个 clone 一次)。
#
# 只做两件事:
#   1. git config core.hooksPath .githooks   (写入当前仓库副本的 .git/config)
#   2. 验证 .githooks/pre-commit 具有执行权限
#
# 不修改任何用户级配置(不动全局 git config、~/.git-hooks 等)。
# 注意:本机全局 core.hooksPath(如已配置)会被本仓库配置覆盖;
# .githooks/pre-commit 在自身检查通过后会链式调用全局 pre-commit(如存在)。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "==> chmod +x .githooks/pre-commit scripts/ai/*.sh"
chmod +x .githooks/pre-commit scripts/ai/*.sh

echo "==> git config core.hooksPath .githooks (repo-local)"
git config core.hooksPath .githooks

actual="$(git config --get core.hooksPath || true)"
if [ "$actual" != ".githooks" ]; then
  echo "FAIL: core.hooksPath 校验失败,期望 .githooks,实际 '${actual:-<unset>}'" >&2
  exit 1
fi

if [ ! -x .githooks/pre-commit ]; then
  echo "FAIL: .githooks/pre-commit 不具备执行权限" >&2
  exit 1
fi

global_hooks="$(git config --global --get core.hooksPath 2>/dev/null || true)"
if [ -n "$global_hooks" ]; then
  echo "NOTE: 检测到全局 core.hooksPath=$global_hooks;本仓库将改用 .githooks。"
  echo "      .githooks/pre-commit 会在自身检查通过后链式调用该目录中的 pre-commit。"
fi

echo "OK: hooksPath=$actual, .githooks/pre-commit 可执行。安装完成(仅当前仓库副本)。"
