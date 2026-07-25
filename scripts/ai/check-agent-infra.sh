#!/usr/bin/env bash
# check-agent-infra.sh — 多 Agent 工程基础设施只读检查。
#
# 只读:不修改任何文件。无第三方依赖(仅 bash + git + grep/sed/sort/uniq/comm)。
# 输出:每项检查打印 PASS / WARN / FAIL;存在任一 FAIL 时以非零退出码结束。
# 本脚本不包含任何真实密钥;扫描命中时只输出文件路径和字段名称,不输出值。

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2

fail_count=0
warn_count=0

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; warn_count=$((warn_count + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; fail_count=$((fail_count + 1)); }

# ---------------------------------------------------------------------------
# 1. 必需文件存在性
# ---------------------------------------------------------------------------
REQUIRED_FILES="
AGENTS.md
CLAUDE.md
PROJECT_CONTEXT.md
README.md
docs/README.md
docs/ai/README.md
docs/ai/CURRENT_TASK.md
docs/ai/HANDOFF.md
docs/ai/BACKLOG.md
docs/ai/LOCAL_CONFIG.md
docs/ai/START_PROMPTS.md
docs/archive/README.md
docs/archive/2026-07-24-doc-governance/spec-v1.md
docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md
docs/knowledge/codex-memory/README.md
docs/knowledge/codex-memory/memory_summary.md
docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md
docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md
docs/decisions/ADR-TEMPLATE.md
scripts/ai/check-doc-governance.sh
scripts/ai/test-doc-governance.sh
scripts/ai/test-pre-commit.sh
scripts/ai/check-task-state.sh
scripts/ai/check-handoff.sh
scripts/ai/check-agent-state.sh
scripts/ai/install-hooks.sh
.githooks/pre-commit
"

for f in $REQUIRED_FILES; do
  if [ -f "$f" ]; then
    pass "required file exists: $f"
  else
    fail "missing required file: $f"
  fi
done

# ---------------------------------------------------------------------------
# 2. 关键标题存在性(文件存在时才检查)
# ---------------------------------------------------------------------------
check_headings() {
  file="$1"; shift
  [ -f "$file" ] || return 0
  for heading in "$@"; do
    if grep -qF -- "$heading" "$file"; then
      pass "heading present in $file: $heading"
    else
      fail "heading missing in $file: $heading"
    fi
  done
}

check_headings AGENTS.md \
  "# Project Agent Instructions" \
  "## 1. Project Overview" \
  "## 2. Sources of Truth" \
  "## 3. Required Reading" \
  "## 5. Development Commands" \
  "## 7. Scope and Change Rules" \
  "## 8. Verification Requirements" \
  "## 9. Git Safety Rules" \
  "## 10. Task State Protocol" \
  "## 11. Handoff Protocol" \
  "## 12. Security and Data Handling" \
  "## 13. Agent-Specific Boundaries"

check_headings CLAUDE.md "AGENTS.md"
check_headings PROJECT_CONTEXT.md "# Kids Visual Learning Pack Project Context" "## Required Read Order"
check_headings docs/README.md "# Project Documentation Map" "## Canonical Current Docs" "## Archive"
check_headings docs/ai/CURRENT_TASK.md "## Objective" "## Acceptance Criteria" "## In Scope" "## Out of Scope" "## Verification Plan"
check_headings docs/ai/HANDOFF.md "## Summary" "## Changed Files" "## Verification Results" "## Known Failures" "## Exact Next Action"
check_headings docs/ai/BACKLOG.md "# Backlog"
check_headings docs/ai/LOCAL_CONFIG.md "# Local Private Configuration" "## Prohibited"
check_headings docs/ai/START_PROMPTS.md "## 1. 恢复当前任务" "## 4. 任务交接" "## 5. 基础设施自检"
check_headings docs/archive/README.md "# Project Documentation Archive" "## Archive Manifest"
check_headings docs/knowledge/codex-memory/README.md "# Codex Memory Snapshot" "## Priority and Freshness"
check_headings docs/decisions/ADR-TEMPLATE.md "## Context" "## Decision" "## Alternatives Considered" "## Consequences" "## Verification"

# ---------------------------------------------------------------------------
# 3. 未处理占位内容(仅限基础设施文件)
#    docs/ai/START_PROMPTS.md 按设计包含字面 TBD/TODO 字样(自检提示词),豁免。
#    本脚本自身包含匹配模式,豁免。
# ---------------------------------------------------------------------------
INFRA_FILES="AGENTS.md CLAUDE.md PROJECT_CONTEXT.md README.md docs/README.md docs/ai/README.md docs/ai/CURRENT_TASK.md docs/ai/HANDOFF.md docs/ai/BACKLOG.md docs/ai/LOCAL_CONFIG.md docs/archive/README.md docs/knowledge/codex-memory/README.md docs/knowledge/codex-memory/memory_summary.md docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md docs/decisions/ADR-TEMPLATE.md scripts/ai/test-pre-commit.sh"
PLACEHOLDER_HITS=""
for f in $INFRA_FILES; do
  [ -f "$f" ] || continue
  hit="$(grep -nE 'TBD|TODO|FIXME|YOUR_REAL_API_KEY|sk-[A-Za-z0-9]{20,}|真实 Token 示例' "$f" || true)"
  if [ -n "$hit" ]; then
    PLACEHOLDER_HITS="$PLACEHOLDER_HITS$f: $hit
"
  fi
done
if [ -n "$PLACEHOLDER_HITS" ]; then
  fail "placeholder residue found:
$PLACEHOLDER_HITS"
else
  pass "no placeholder residue in infra files"
fi

# ---------------------------------------------------------------------------
# 4. 已跟踪文件中的密钥痕迹(只输出路径+字段名,不输出值)
#    FAIL 级:高置信密钥形态(私钥头、OpenAI 风格 key、赋值形态的长密钥)。
#    WARN 级:仅提及常见密钥字段名。
#    豁免(仅 WARN 级):按设计讨论密钥边界的文件。
# ---------------------------------------------------------------------------
TRACKED="$(git ls-files)"
SECRET_VALUE_HITS=""
SECRET_MENTION_FILES=""

# WARN 级豁免:这些文件按设计讨论密钥边界,不出现真实值。
WARN_ALLOWLIST="docs/ai/LOCAL_CONFIG.md AGENTS.md docs/ai/START_PROMPTS.md docs/knowledge/codex-memory/README.md docs/knowledge/codex-memory/memory_summary.md docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md scripts/ai/check-agent-infra.sh scripts/ai/check-doc-governance.sh scripts/ai/test-doc-governance.sh scripts/ai/test-pre-commit.sh scripts/ai/check-task-state.sh scripts/ai/check-handoff.sh scripts/ai/check-agent-state.sh scripts/ai/install-hooks.sh .githooks/pre-commit"

for f in $TRACKED; do
  [ -f "$f" ] || continue
  case "$f" in
    *.png|*.webp|*.jpg|*.jpeg|*.gif|*.ico|*.woff|*.woff2|*.lock) continue ;;
  esac

  # FAIL 级:私钥头
  if grep -qE -- '-----BEGIN [A-Z ]*PRIVATE KEY-----' "$f" 2>/dev/null; then
    SECRET_VALUE_HITS="$SECRET_VALUE_HITS  $f (field: private-key-block)
"
  fi
  # FAIL 级:OpenAI 风格 key(sk- 后接 20+ 位)
  if grep -qE 'sk-[A-Za-z0-9]{20,}' "$f" 2>/dev/null; then
    SECRET_VALUE_HITS="$SECRET_VALUE_HITS  $f (field: sk-api-key)
"
  fi
  # FAIL 级:赋值形态长密钥(排除明显占位符行)
  assign_hit="$(grep -inE '(api[_-]?key|secret|token|password|passwd)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_.=-]{16,}' "$f" 2>/dev/null \
    | grep -ivE 'YOUR|EXAMPLE|placeholder|dummy|example\.invalid' \
    | sed -E 's/^([0-9]+):.*/line \1/' || true)"
  if [ -n "$assign_hit" ]; then
    field_names="$(grep -ioE '(api[_-]?key|secret|token|password|passwd)' "$f" 2>/dev/null | tr '[:upper:]' '[:lower:]' | sort -u | tr '\n' ',' | sed 's/,$//')"
    SECRET_VALUE_HITS="$SECRET_VALUE_HITS  $f (field: $field_names)
"
  fi

  # WARN 级:仅提及字段名
  case " $WARN_ALLOWLIST " in
    *" $f "*) continue ;;
  esac
  mention_fields="$(grep -ioE '(api[_-]?key|secret[_-]?key|access[_-]?key|password|passwd|oauth|bearer)' "$f" 2>/dev/null | tr '[:upper:]' '[:lower:]' | sort -u | tr '\n' ',' | sed 's/,$//' || true)"
  if [ -n "$mention_fields" ]; then
    SECRET_MENTION_FILES="$SECRET_MENTION_FILES  $f (fields: $mention_fields)
"
  fi
done

if [ -n "$SECRET_VALUE_HITS" ]; then
  fail "possible secret values in tracked files (path + field only):
$SECRET_VALUE_HITS"
else
  pass "no high-confidence secret values in tracked files"
fi

if [ -n "$SECRET_MENTION_FILES" ]; then
  warn "secret-related field names mentioned in tracked files (review only, values not shown):
$SECRET_MENTION_FILES"
else
  pass "no secret field mentions outside allowlist"
fi

# ---------------------------------------------------------------------------
# 5. AGENTS.md 与 CLAUDE.md 重复度(CLAUDE.md 应只做适配)
# ---------------------------------------------------------------------------
if [ -f AGENTS.md ] && [ -f CLAUDE.md ]; then
  norm() {
    grep -vE '^\s*(#|```|@|-|\*|\||>|\s*$)' "$1" | sed 's/[[:space:]]\+/ /g' | grep -E '.{20,}' | sort -u
  }
  claude_lines="$(norm CLAUDE.md)"
  agents_lines="$(norm AGENTS.md)"
  if [ -n "$claude_lines" ]; then
    dup="$(comm -12 <(printf '%s\n' "$claude_lines") <(printf '%s\n' "$agents_lines") | wc -l | tr -d ' ')"
    total="$(printf '%s\n' "$claude_lines" | wc -l | tr -d ' ')"
    if [ "$dup" -gt 0 ]; then
      warn "CLAUDE.md shares $dup/$total long content lines with AGENTS.md (adapter should reference, not copy)"
    else
      pass "CLAUDE.md does not duplicate AGENTS.md content"
    fi
  else
    pass "CLAUDE.md has no long content lines to compare"
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
