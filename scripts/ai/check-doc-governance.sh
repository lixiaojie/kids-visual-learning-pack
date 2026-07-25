#!/usr/bin/env bash
set -u

ROOT="${DOC_GOVERNANCE_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
TODAY="${DOC_GOVERNANCE_TODAY:-$(date +%F)}"
cd "$ROOT" || exit 2

fail_count=0
warn_count=0

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; warn_count=$((warn_count + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; fail_count=$((fail_count + 1)); }

valid_iso_date() {
  value="$1"
  if ! printf '%s\n' "$value" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    return 1
  fi

  if normalized="$(date -j -f "%Y-%m-%d" "$value" "+%Y-%m-%d" 2>/dev/null)" \
    && [ "$normalized" = "$value" ]; then
    return 0
  fi

  if normalized="$(date -d "$value" "+%Y-%m-%d" 2>/dev/null)" \
    && [ "$normalized" = "$value" ]; then
    return 0
  fi

  return 1
}

if ! valid_iso_date "$TODAY"; then
  fail "invalid DOC_GOVERNANCE_TODAY: $TODAY"
  echo "------------------------------------------------------------"
  printf 'RESULT: FAIL (%d failure(s), %d warning(s))\n' "$fail_count" "$warn_count"
  exit 1
fi

REQUIRED_FILES="
AGENTS.md
README.md
PROJECT_CONTEXT.md
docs/README.md
docs/ai/CURRENT_TASK.md
docs/ai/HANDOFF.md
docs/archive/README.md
docs/archive/2026-07-24-doc-governance/spec-v1.md
docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md
docs/spec-v2.md
docs/architecture-iteration-v1.3.md
docs/knowledge/codex-memory/README.md
docs/knowledge/codex-memory/memory_summary.md
docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md
docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md
"

for file in $REQUIRED_FILES; do
  if [ -f "$file" ]; then
    pass "required file exists: $file"
  else
    fail "missing required file: $file"
  fi
done

for superseded_path in \
  docs/spec-v1.md \
  docs/architecture-iteration-v1.2.md; do
  if [ -e "$superseded_path" ]; then
    fail "superseded document remains active: $superseded_path"
  else
    pass "superseded active path absent: $superseded_path"
  fi
done

check_links() {
  source="$1"
  [ -f "$source" ] || return 0
  base="$(dirname "$source")"

  while IFS= read -r match; do
    link="${match#](}"
    link="${link%%#*}"
    case "$link" in
      ""|\#*|//*) continue ;;
    esac
    if printf '%s\n' "$link" | grep -Eq '^[A-Za-z][A-Za-z0-9+.-]*:'; then
      continue
    fi
    target="$base/$link"
    if [ -e "$target" ]; then
      pass "Markdown link exists: $source -> $link"
    else
      fail "broken Markdown link: $source -> $link"
    fi
  done < <(grep -oE '\]\([^)]+' "$source" || true)
}

for source in \
  README.md \
  PROJECT_CONTEXT.md \
  docs/README.md \
  docs/archive/README.md \
  docs/knowledge/codex-memory/README.md; do
  check_links "$source"
done

check_review_dates() {
  review_file="$1"
  [ -f "$review_file" ] || return 0

  last_reviewed="$(sed -n 's/^- Last Reviewed:[[:space:]]*//p' "$review_file" | head -1)"
  next_review_due="$(sed -n 's/^- Next Review Due:[[:space:]]*//p' "$review_file" | head -1)"

  last_reviewed_valid=0
  if ! valid_iso_date "$last_reviewed"; then
    fail "invalid Last Reviewed date in $review_file: $last_reviewed"
  elif [ "$last_reviewed" \> "$TODAY" ]; then
    fail "Last Reviewed is in the future in $review_file: $last_reviewed"
    last_reviewed_valid=1
  else
    pass "Last Reviewed date is valid in $review_file: $last_reviewed"
    last_reviewed_valid=1
  fi

  if ! valid_iso_date "$next_review_due"; then
    fail "invalid Next Review Due date in $review_file: $next_review_due"
  elif [ "$last_reviewed_valid" -eq 0 ]; then
    pass "Next Review Due date is valid in $review_file: $next_review_due"
  elif [ "$next_review_due" \< "$last_reviewed" ] || [ "$next_review_due" = "$last_reviewed" ]; then
    fail "Next Review Due must be after Last Reviewed in $review_file"
  elif [ "$TODAY" \> "$next_review_due" ]; then
    warn "documentation review overdue for $review_file since $next_review_due"
  else
    pass "documentation review current for $review_file through $next_review_due"
  fi
}

for review_file in \
  PROJECT_CONTEXT.md \
  docs/README.md \
  docs/knowledge/codex-memory/README.md; do
  check_review_dates "$review_file"
done

echo "------------------------------------------------------------"
if [ "$fail_count" -gt 0 ]; then
  printf 'RESULT: FAIL (%d failure(s), %d warning(s))\n' "$fail_count" "$warn_count"
  exit 1
elif [ "$warn_count" -gt 0 ]; then
  printf 'RESULT: WARN (0 failures, %d warning(s))\n' "$warn_count"
  exit 0
else
  echo "RESULT: PASS"
  exit 0
fi
