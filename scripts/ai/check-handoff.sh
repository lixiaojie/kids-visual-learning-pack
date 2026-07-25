#!/usr/bin/env bash
# check-handoff.sh — docs/ai/HANDOFF.md 时效性与完整性只读检查。
#
# 只读:不修改任何文件。无第三方依赖(仅 bash + git + grep/sed/awk)。
# 输出:每项检查打印 PASS / WARN / FAIL;存在任一 FAIL 时以非零退出码结束。
# 不输出密钥或完整敏感内容;疑似密钥只报字段名。

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2

HANDOFF="docs/ai/HANDOFF.md"
fail_count=0
warn_count=0

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; warn_count=$((warn_count + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; fail_count=$((fail_count + 1)); }

if [ ! -f "$HANDOFF" ]; then
  fail "missing $HANDOFF"
  printf 'RESULT: FAIL (%d failure(s), %d warning(s))\n' "$fail_count" "$warn_count"
  exit 1
fi
pass "file exists: $HANDOFF"

section() {
  awk -v h="$1" 'index($0, h) == 1 {f=1; next} /^## / {f=0} f' "$HANDOFF"
}

meta_field() {
  grep -E "^- $1:" "$HANDOFF" | head -1 | sed "s/^- $1:[[:space:]]*//"
}

# ---------------------------------------------------------------------------
# 1. 必需章节
# ---------------------------------------------------------------------------
for heading in "## Metadata" "## Summary" "## Changed Files" "## Verification Results" "## Known Failures" "## Remaining Work" "## Exact Next Action" "## Recovery Notes"; do
  if grep -qF -- "$heading" "$HANDOFF"; then
    pass "section present: $heading"
  else
    fail "section missing: $heading"
  fi
done

# ---------------------------------------------------------------------------
# 2. Exact Next Action 必须存在且非空
# ---------------------------------------------------------------------------
ena="$(section '## Exact Next Action')"
if [ -n "$(printf '%s' "$ena" | tr -d '[:space:]')" ]; then
  pass "Exact Next Action 非空"
else
  fail "Exact Next Action 为空或缺失(下一位 Agent 无法直接接手)"
fi

# ---------------------------------------------------------------------------
# 3. Verification Results 必须存在且有实际结果;未验证项必须明确标记
# ---------------------------------------------------------------------------
vr="$(section '## Verification Results')"
if [ -z "$(printf '%s' "$vr" | tr -d '[:space:]')" ]; then
  fail "Verification Results 为空"
else
  if printf '%s' "$vr" | grep -qE 'PASS|WARN|FAIL'; then
    pass "Verification Results 含实际验证结果(PASS/WARN/FAIL)"
  else
    fail "Verification Results 不含任何 PASS/WARN/FAIL 结果(未验证内容必须明确标记)"
  fi
  if printf '%s' "$vr" | grep -qE '待执行|未执行'; then
    warn "Verification Results 中存在标记为待执行/未执行的项(已明确标记,属允许状态)"
  fi
fi

# ---------------------------------------------------------------------------
# 4. 分支一致性(HANDOFF 记录 vs 当前实际)
# ---------------------------------------------------------------------------
handoff_branch="$(meta_field 'Branch')"
current_branch="$(git branch --show-current 2>/dev/null)"
if [ -z "$handoff_branch" ]; then
  warn "HANDOFF Metadata 中缺少 Branch 字段"
elif [ "$handoff_branch" != "$current_branch" ]; then
  warn "分支不一致: HANDOFF 记录 '$handoff_branch',当前 '$current_branch'(交接可能来自其他分支)"
else
  pass "分支一致: $current_branch"
fi

# ---------------------------------------------------------------------------
# 5. Base Commit 与 HEAD 的关系(信息级)
# ---------------------------------------------------------------------------
handoff_base="$(meta_field 'Base Commit' | awk '{print $1}' | cut -c1-7)"
head_short="$(git rev-parse --short HEAD 2>/dev/null)"
if [ -n "$handoff_base" ] && [ -n "$head_short" ]; then
  if [ "$handoff_base" = "$head_short" ]; then
    pass "Base Commit 与 HEAD 一致: $head_short"
  elif git merge-base --is-ancestor "$handoff_base" HEAD 2>/dev/null; then
    warn "Base Commit ($handoff_base) 落后于 HEAD ($head_short): 交接后有新提交"
  else
    warn "Base Commit ($handoff_base) 与 HEAD ($head_short) 不在同一祖先链上,需人工核实"
  fi
fi

# ---------------------------------------------------------------------------
# 6. Working Tree 描述与实际状态不得明显矛盾
# ---------------------------------------------------------------------------
wt="$(meta_field 'Working Tree')"
status_short="$(git status --short 2>/dev/null)"
if [ -n "$wt" ]; then
  if printf '%s' "$wt" | grep -qiE '干净|clean|无未提交|no changes'; then
    if [ -n "$status_short" ]; then
      warn "Working Tree 描述为干净,但 git status --short 非空(交接后工作区已变化)"
    else
      pass "Working Tree 描述(干净)与实际一致"
    fi
  elif [ -z "$status_short" ]; then
    warn "Working Tree 描述了未提交内容,但当前 git status --short 为空(可能已提交或交接过期)"
  else
    pass "Working Tree 描述与非空工作区状态不矛盾(语义一致性需人工复核)"
  fi
else
  warn "HANDOFF Metadata 中缺少 Working Tree 字段"
fi

# ---------------------------------------------------------------------------
# 7. 疑似密钥泄漏检查(只报字段名,不输出值)
# ---------------------------------------------------------------------------
if grep -qE 'sk-[A-Za-z0-9]{20,}' "$HANDOFF"; then
  fail "HANDOFF 中出现疑似 API key(field: sk-*)"
fi
if grep -qE -- '-----BEGIN [A-Z ]*PRIVATE KEY-----' "$HANDOFF"; then
  fail "HANDOFF 中出现私钥块(field: private-key-block)"
fi
assign="$(grep -inE '(api[_-]?key|secret|token|password|passwd)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_.=-]{16,}' "$HANDOFF" \
  | grep -ivE 'YOUR|EXAMPLE|placeholder|dummy|example\.invalid' || true)"
if [ -n "$assign" ]; then
  fail "HANDOFF 中出现疑似密钥赋值(仅提示字段: api_key/secret/token/password 之一)"
fi
if [ "$fail_count" -eq 0 ] || true; then
  if ! grep -qE 'sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' "$HANDOFF" && [ -z "$assign" ]; then
    pass "HANDOFF 无疑似密钥内容"
  fi
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
