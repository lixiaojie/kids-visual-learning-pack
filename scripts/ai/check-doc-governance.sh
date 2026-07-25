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

iso_date_to_epoch_day() {
  value="$1"
  if ! printf '%s\n' "$value" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    return 1
  fi

  parsed=""
  if parsed="$(TZ=UTC0 date -j -f "%Y-%m-%d %H:%M:%S" \
      "$value 00:00:00" "+%Y-%m-%d|%s" 2>/dev/null)"; then
    :
  elif parsed="$(TZ=UTC0 date -d "$value 00:00:00" \
      "+%Y-%m-%d|%s" 2>/dev/null)"; then
    :
  else
    return 1
  fi

  normalized="${parsed%%|*}"
  epoch="${parsed#*|}"
  if [ "$normalized" != "$value" ] \
    || ! printf '%s\n' "$epoch" | grep -Eq '^[0-9]+$'; then
    return 1
  fi

  printf '%s\n' "$((epoch / 86400))"
}

if ! TODAY_DAY="$(iso_date_to_epoch_day "$TODAY")"; then
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

check_archive_mapping() {
  original_path="$1"
  expected_row="$2"
  if [ -f docs/archive/README.md ] \
    && grep -Fx -- "$expected_row" docs/archive/README.md >/dev/null; then
    pass "archive manifest mapping valid for $original_path"
  else
    fail "archive manifest mapping missing or mismatched for $original_path"
  fi
}

check_archive_mapping \
  "docs/spec-v1.md" \
  '| `docs/spec-v1.md` | [spec-v1.md](2026-07-24-doc-governance/spec-v1.md) | 2026-07-24 | Superseded project specification | [spec-v2.md](../spec-v2.md) |'
check_archive_mapping \
  "docs/architecture-iteration-v1.2.md" \
  '| `docs/architecture-iteration-v1.2.md` | [architecture-iteration-v1.2.md](2026-07-24-doc-governance/architecture-iteration-v1.2.md) | 2026-07-24 | Superseded architecture iteration | [architecture-iteration-v1.3.md](../architecture-iteration-v1.3.md) |'

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
  last_reviewed_day=""
  if ! last_reviewed_day="$(iso_date_to_epoch_day "$last_reviewed")"; then
    fail "invalid Last Reviewed date in $review_file: $last_reviewed"
  elif [ "$last_reviewed_day" -gt "$TODAY_DAY" ]; then
    fail "Last Reviewed is in the future in $review_file: $last_reviewed"
    last_reviewed_valid=1
  else
    pass "Last Reviewed date is valid in $review_file: $last_reviewed"
    last_reviewed_valid=1
  fi

  next_review_due_day=""
  if ! next_review_due_day="$(iso_date_to_epoch_day "$next_review_due")"; then
    fail "invalid Next Review Due date in $review_file: $next_review_due"
  elif [ "$last_reviewed_valid" -eq 0 ]; then
    pass "Next Review Due date is valid in $review_file: $next_review_due"
  elif [ "$next_review_due_day" -le "$last_reviewed_day" ]; then
    fail "Next Review Due must be after Last Reviewed in $review_file"
  elif [ "$((next_review_due_day - last_reviewed_day))" -gt 31 ]; then
    fail "Next Review Due must be no more than 31 days after Last Reviewed in $review_file"
  else
    pass "review interval is within 31 days in $review_file"
  fi

  if [ "$last_reviewed_valid" -eq 1 ] \
    && [ "$last_reviewed_day" -le "$TODAY_DAY" ]; then
    if [ "$((TODAY_DAY - last_reviewed_day))" -gt 31 ]; then
      warn "documentation review overdue for $review_file; Last Reviewed was $last_reviewed"
    else
      pass "documentation review age is within 31 days in $review_file"
    fi
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
