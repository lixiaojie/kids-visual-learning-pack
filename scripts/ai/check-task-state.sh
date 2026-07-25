#!/usr/bin/env bash
# check-task-state.sh — docs/ai/CURRENT_TASK.md 状态一致性只读检查。
#
# 只读:不修改任何文件。无第三方依赖(仅 bash + grep/sed/awk/sort)。
# 输出:每项检查打印 PASS / WARN / FAIL;存在任一 FAIL 时以非零退出码结束。

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2

TASK_FILE="docs/ai/CURRENT_TASK.md"
fail_count=0
warn_count=0

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; warn_count=$((warn_count + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; fail_count=$((fail_count + 1)); }

if [ ! -f "$TASK_FILE" ]; then
  fail "missing $TASK_FILE"
  printf 'RESULT: FAIL (%d failure(s), %d warning(s))\n' "$fail_count" "$warn_count"
  exit 1
fi
pass "file exists: $TASK_FILE"

# ---------------------------------------------------------------------------
# 1. 必需章节
# ---------------------------------------------------------------------------
for heading in "## Metadata" "## Objective" "## Acceptance Criteria" "## In Scope" "## Out of Scope" "## Verification Plan"; do
  if grep -qF -- "$heading" "$TASK_FILE"; then
    pass "section present: $heading"
  else
    fail "section missing: $heading"
  fi
done

section() {
  awk -v h="$1" 'index($0, h) == 1 {f=1; next} /^## / {f=0} f' "$TASK_FILE"
}

# ---------------------------------------------------------------------------
# 2. Status 字段:唯一、取值合法、无相互矛盾
# ---------------------------------------------------------------------------
status_lines="$(grep -cE '^- Status:' "$TASK_FILE" || true)"
if [ "$status_lines" -eq 0 ]; then
  fail "Metadata 中缺少 '- Status:' 行"
  status_value=""
elif [ "$status_lines" -gt 1 ]; then
  fail "存在 $status_lines 个 '- Status:' 行(状态矛盾)"
  status_value="$(grep -E '^- Status:' "$TASK_FILE" | head -1 | sed 's/^- Status:[[:space:]]*//')"
else
  status_value="$(grep -E '^- Status:' "$TASK_FILE" | sed 's/^- Status:[[:space:]]*//')"
  case "$status_value" in
    "Not Defined"|"In Progress"|"Done"|"Blocked"|"Paused")
      pass "Status 取值合法: $status_value" ;;
    *)
      warn "Status 取值不在推荐枚举(Not Defined / In Progress / Done / Blocked / Paused): $status_value" ;;
  esac
fi

objective="$(section '## Objective')"

# Status: Not Defined 时,Objective 应明确写为未定义
if [ "$status_value" = "Not Defined" ]; then
  if printf '%s' "$objective" | grep -qE '未|Not|not defined|待定'; then
    pass "Status 为 Not Defined 且 Objective 已明确标记未定义"
  else
    warn "Status 为 Not Defined,但 Objective 未明确说明任务未定义"
  fi
fi

# 其他状态下 Objective 不得仍声称任务未定义(矛盾)
case "$status_value" in
  "In Progress"|"Done"|"Paused")
    if printf '%s' "$objective" | grep -qE '未发现经过确认的当前任务|任务未定义'; then
      fail "状态矛盾: Status 为 $status_value,但 Objective 声称任务未定义"
    else
      pass "Status 与 Objective 无矛盾"
    fi ;;
esac

# Status: Done 时,验收项不应存在未勾选项
if [ "$status_value" = "Done" ]; then
  unchecked="$(section '## Acceptance Criteria' | grep -cE '^\s*- \[ \]' || true)"
  if [ "$unchecked" -gt 0 ]; then
    warn "Status 为 Done,但 Acceptance Criteria 仍有 $unchecked 个未勾选项"
  else
    pass "Status 为 Done 且验收项全部勾选"
  fi
fi

# ---------------------------------------------------------------------------
# 3. Objective / Verification Plan 非空
# ---------------------------------------------------------------------------
if [ -n "$(printf '%s' "$objective" | tr -d '[:space:]')" ]; then
  pass "Objective 非空"
else
  fail "Objective 为空"
fi

vp="$(section '## Verification Plan')"
if [ -n "$(printf '%s' "$vp" | tr -d '[:space:]')" ]; then
  pass "Verification Plan 非空"
else
  fail "Verification Plan 为空"
fi

# ---------------------------------------------------------------------------
# 4. CURRENT_TASK 中引用的仓库内文件必须存在
#    只检查形如 `path` 且指向仓库内位置的引用;命令、外部 URL、~ 路径跳过。
# ---------------------------------------------------------------------------
refs="$(grep -oE '`[~A-Za-z0-9_./-]+`' "$TASK_FILE" | tr -d '`' | sort -u)"
missing=""
checked=0
for p in $refs; do
  case "$p" in
    -*|*..*|http*|https*|~*|*\**|*/'{'*) continue ;;
  esac
  if printf '%s' "$p" | grep -qE '^(docs|scripts|boards|ops|packages|apps|migration|skills|tests|shared|\.githooks)/'; then
    :
  elif printf '%s' "$p" | grep -qE '^[A-Za-z0-9_.-]+\.(md|sh|json|mjs|py|ts|cjs|yaml|yml|toml|txt)$'; then
    :
  else
    continue
  fi
  checked=$((checked + 1))
  if [ ! -e "$p" ]; then
    missing="$missing  $p
"
  fi
done
if [ -n "$missing" ]; then
  fail "CURRENT_TASK 引用的仓库路径不存在:
$missing"
else
  pass "CURRENT_TASK 引用的 $checked 个仓库路径全部存在"
fi

# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------
echo "------------------------------------------------------------"
if [ "$fail_count" -gt 0 ]; then
  printf 'RESULT: FAIL (%d failure(s), %d warning(s))\n' "$fail_count" "$warn_count"
  exit 1
elif [ "$warn_count" -gt 0 ]; then
  printf 'RESULT: WARN (0 failures, %d warning(s))\n' "$warn_count"
  exit 0
else
  printf 'RESULT: PASS (all checks green)\n'
  exit 0
fi
