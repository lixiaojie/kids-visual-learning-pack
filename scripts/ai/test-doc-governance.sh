#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CHECKER="$ROOT/scripts/ai/check-doc-governance.sh"
TMP_ROOT="$(mktemp -d)"
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
  fixture="$1"
  DOC_GOVERNANCE_ROOT="$fixture" \
    DOC_GOVERNANCE_TODAY="2026-07-24" \
    bash "$CHECKER" 2>&1
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
out="$(run_checker "$TMP_ROOT/missing")"
rc=$?
if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -F 'missing required file' >/dev/null; then
  pass "missing required file fails"
else
  fail "missing required file should fail"
fi

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/broken"
printf '# Context\n\n[Missing](docs/missing.md)\n' > "$TMP_ROOT/broken/PROJECT_CONTEXT.md"
out="$(run_checker "$TMP_ROOT/broken")"
rc=$?
if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -F 'broken Markdown link' >/dev/null; then
  pass "broken link fails"
else
  fail "broken link should fail"
fi

cp -R "$TMP_ROOT/pass" "$TMP_ROOT/overdue"
printf '%s\n' \
  '# Memory' \
  '' \
  '- Last Reviewed: 2026-06-01' \
  '- Next Review Due: 2026-07-02' \
  '' \
  '[Summary](memory_summary.md)' \
  > "$TMP_ROOT/overdue/docs/knowledge/codex-memory/README.md"
out="$(run_checker "$TMP_ROOT/overdue")"
rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -F 'RESULT: WARN' >/dev/null; then
  pass "overdue review warns"
else
  fail "overdue review should warn without failing"
fi

printf '%s\n' "RESULT: pass=$pass_count fail=$fail_count"
[ "$fail_count" -eq 0 ]
