#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CHECKER="$ROOT/scripts/ai/check-doc-governance.sh"
TMP_ROOT="$(mktemp -d)"
tmp_rc=$?
if [ "$tmp_rc" -ne 0 ] || [ -z "$TMP_ROOT" ] || [ ! -d "$TMP_ROOT" ]; then
  printf 'FAIL: mktemp -d did not create a usable temporary directory\n' >&2
  exit 2
fi
trap 'rm -rf "$TMP_ROOT"' EXIT

pass_count=0
fail_count=0

pass() {
  printf 'PASS: %s\n' "$1"
  pass_count=$((pass_count + 1))
}

fail() {
  printf 'FAIL: %s\n' "$1"
  fail_count=$((fail_count + 1))
}

make_fixture() {
  fixture="$1"
  mkdir -p \
    "$fixture/docs/ai" \
    "$fixture/docs/archive/2026-07-24-doc-governance" \
    "$fixture/docs/knowledge/codex-memory/rollout-summaries"

  printf '# Agents\n' > "$fixture/AGENTS.md"
  printf '# Readme\n' > "$fixture/README.md"
  printf '%s\n' \
    '# Context' \
    '' \
    '- Last Reviewed: 2026-07-24' \
    '- Next Review Due: 2026-08-24' \
    '' \
    '[Docs](docs/README.md)' \
    > "$fixture/PROJECT_CONTEXT.md"
  printf '%s\n' \
    '# Docs' \
    '' \
    '- Last Reviewed: 2026-07-24' \
    '- Next Review Due: 2026-08-24' \
    '' \
    '[Task](ai/CURRENT_TASK.md)' \
    > "$fixture/docs/README.md"
  printf '# Task\n' > "$fixture/docs/ai/CURRENT_TASK.md"
  printf '# Handoff\n' > "$fixture/docs/ai/HANDOFF.md"
  printf '# Archive\n\n[Replacement](../spec-v2.md)\n' > "$fixture/docs/archive/README.md"
  printf '# Archived\n' > "$fixture/docs/archive/2026-07-24-doc-governance/spec-v1.md"
  printf '# Archived\n' > "$fixture/docs/archive/2026-07-24-doc-governance/architecture-iteration-v1.2.md"
  printf '# Spec v2\n' > "$fixture/docs/spec-v2.md"
  printf '# Architecture v1.3\n' > "$fixture/docs/architecture-iteration-v1.3.md"
  printf '%s\n' \
    '# Memory' \
    '' \
    '- Last Reviewed: 2026-07-24' \
    '- Next Review Due: 2026-08-24' \
    '' \
    '[Summary](memory_summary.md)' \
    > "$fixture/docs/knowledge/codex-memory/README.md"
  printf '# Summary\n' > "$fixture/docs/knowledge/codex-memory/memory_summary.md"
  printf '# Deployment\n' > "$fixture/docs/knowledge/codex-memory/rollout-summaries/2026-07-11-card-os-deployment-ops.md"
  printf '# Skill Install\n' > "$fixture/docs/knowledge/codex-memory/rollout-summaries/2026-07-07-local-cognitive-card-os-skill-install.md"
}

run_checker() {
  run_checker_with_today "$1" "2026-07-24"
}

run_checker_with_today() {
  fixture="$1"
  today="$2"
  DOC_GOVERNANCE_ROOT="$fixture" \
    DOC_GOVERNANCE_TODAY="$today" \
    bash "$CHECKER" 2>&1
}

expect_single_failure() {
  description="$1"
  fixture="$2"
  today="$3"
  expected="$4"
  out="$(run_checker_with_today "$fixture" "$today")"
  rc=$?
  failure_count="$(printf '%s\n' "$out" | grep -c '^FAIL:' || true)"
  if [ "$rc" -ne 0 ] \
    && printf '%s\n' "$out" | grep -F "$expected" >/dev/null \
    && [ "$failure_count" -eq 1 ]; then
    pass "$description"
  else
    fail "$description should produce one expected failure"
  fi
}

write_memory_review() {
  fixture="$1"
  last_reviewed="$2"
  next_review_due="$3"
  printf '%s\n' \
    '# Memory' \
    '' \
    "- Last Reviewed: $last_reviewed" \
    "- Next Review Due: $next_review_due" \
    '' \
    '[Summary](memory_summary.md)' \
    > "$fixture/docs/knowledge/codex-memory/README.md"
}

make_fixture "$TMP_ROOT/pass"
out="$(run_checker "$TMP_ROOT/pass")"
rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -F 'RESULT: PASS' >/dev/null; then
  pass "current fixture passes"
else
  fail "current fixture should pass"
fi

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/missing"
rm "$TMP_ROOT/missing/docs/README.md"
printf '%s\n' \
  '# Context' \
  '' \
  '- Last Reviewed: 2026-07-24' \
  '- Next Review Due: 2026-08-24' \
  > "$TMP_ROOT/missing/PROJECT_CONTEXT.md"
expect_single_failure \
  "missing required file fails without extra route failures" \
  "$TMP_ROOT/missing" \
  "2026-07-24" \
  "missing required file: docs/README.md"

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/broken"
printf '%s\n' \
  '# Context' \
  '' \
  '- Last Reviewed: 2026-07-24' \
  '- Next Review Due: 2026-08-24' \
  '' \
  '[Missing](docs/missing.md)' \
  > "$TMP_ROOT/broken/PROJECT_CONTEXT.md"
expect_single_failure \
  "broken link fails without date failures" \
  "$TMP_ROOT/broken" \
  "2026-07-24" \
  "broken Markdown link: PROJECT_CONTEXT.md -> docs/missing.md"

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/overdue"
write_memory_review "$TMP_ROOT/overdue" "2026-06-01" "2026-07-02"
out="$(run_checker "$TMP_ROOT/overdue")"
rc=$?
if [ "$rc" -eq 0 ] \
  && printf '%s\n' "$out" | grep -F 'RESULT: WARN' >/dev/null \
  && ! printf '%s\n' "$out" | grep -q '^FAIL:'; then
  pass "overdue review warns"
else
  fail "overdue review should warn without failing"
fi

for date_case in \
  "empty||2026-08-24|invalid Last Reviewed date" \
  "non-zero-padded|2026-7-2|2026-08-24|invalid Last Reviewed date" \
  "invalid-calendar-date|2026-02-30|2026-08-24|invalid Last Reviewed date" \
  "future|2026-07-25|2026-08-24|Last Reviewed is in the future" \
  "due-equals-last-reviewed|2026-07-24|2026-07-24|Next Review Due must be after Last Reviewed"; do
  IFS='|' read -r case_name last_reviewed next_review_due expected <<< "$date_case"
  fixture="$TMP_ROOT/date-$case_name"
  cp -R "$TMP_ROOT/pass" "$fixture"
  write_memory_review "$fixture" "$last_reviewed" "$next_review_due"
  expect_single_failure \
    "date case $case_name fails strictly" \
    "$fixture" \
    "2026-07-24" \
    "$expected"
done

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/today-due"
write_memory_review "$TMP_ROOT/today-due" "2026-07-01" "2026-07-24"
out="$(run_checker "$TMP_ROOT/today-due")"
rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -F 'RESULT: PASS' >/dev/null; then
  pass "review due today remains current"
else
  fail "review due today should pass"
fi

expect_single_failure \
  "invalid DOC_GOVERNANCE_TODAY fails strictly" \
  "$TMP_ROOT/pass" \
  "2026-7-2" \
  "invalid DOC_GOVERNANCE_TODAY"

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/external-links"
printf '%s\n' \
  '' \
  '[Telephone](tel:+8612345678)' \
  '[FTP](ftp://example.test/file)' \
  '[Custom](custom+scheme:opaque)' \
  '[Protocol Relative](//example.test/path)' \
  >> "$TMP_ROOT/external-links/PROJECT_CONTEXT.md"
out="$(run_checker "$TMP_ROOT/external-links")"
rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -F 'RESULT: PASS' >/dev/null; then
  pass "all URI schemes and protocol-relative links are external"
else
  fail "external URI links should not be checked as project paths"
fi

mkdir -p "$TMP_ROOT/mock-bin"
printf '%s\n' '#!/usr/bin/env bash' 'exit 1' > "$TMP_ROOT/mock-bin/mktemp"
chmod +x "$TMP_ROOT/mock-bin/mktemp"
out="$(PATH="$TMP_ROOT/mock-bin:$PATH" bash "$ROOT/scripts/ai/test-doc-governance.sh" 2>&1)"
rc=$?
if [ "$rc" -eq 2 ] && printf '%s\n' "$out" | grep -F 'mktemp -d did not create a usable temporary directory' >/dev/null; then
  pass "mktemp failure exits before fixture paths are used"
else
  fail "mktemp failure should fail closed with exit 2"
fi

printf '%s\n' "RESULT: pass=$pass_count fail=$fail_count"
[ "$fail_count" -eq 0 ]
