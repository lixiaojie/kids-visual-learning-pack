#!/usr/bin/env bash
# check-agent-state.sh — 多 Agent 基础设施统一检查入口。
#
# 按序执行:
#   1. scripts/ai/check-agent-infra.sh
#   2. scripts/ai/check-task-state.sh
#   3. scripts/ai/check-handoff.sh
#   4. git diff --check
# 汇总 PASS / WARN / FAIL;任一步骤 FAIL 时以非零退出码结束。
# 只读:自身与各子检查均不修改文件。

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2

step_fail=0
step_warn=0
step_pass=0

run_step() {
  name="$1"; shift
  echo "============================================================"
  echo "STEP: $name"
  echo "============================================================"
  out="$("$@" 2>&1)"
  rc=$?
  printf '%s\n' "$out"
  if [ "$rc" -ne 0 ]; then
    step_fail=$((step_fail + 1))
    printf '>>> STEP RESULT: FAIL (%s, exit=%d)\n' "$name" "$rc"
  elif printf '%s\n' "$out" | grep -q 'RESULT: WARN'; then
    step_warn=$((step_warn + 1))
    printf '>>> STEP RESULT: WARN (%s)\n' "$name"
  else
    step_pass=$((step_pass + 1))
    printf '>>> STEP RESULT: PASS (%s)\n' "$name"
  fi
  echo
}

run_step "check-agent-infra" bash scripts/ai/check-agent-infra.sh
run_step "check-task-state" bash scripts/ai/check-task-state.sh
run_step "check-handoff" bash scripts/ai/check-handoff.sh
run_step "git diff --check" git diff --check

echo "============================================================"
echo "SUMMARY: pass=$step_pass warn=$step_warn fail=$step_fail"
if [ "$step_fail" -gt 0 ]; then
  echo "RESULT: FAIL"
  exit 1
elif [ "$step_warn" -gt 0 ]; then
  echo "RESULT: WARN"
  exit 0
else
  echo "RESULT: PASS"
  exit 0
fi
