#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK="$ROOT/.githooks/pre-commit"
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

make_repo() {
  repo="$1"
  mkdir -p "$repo/.githooks" "$repo/scripts/ai" "$repo/docs/ai"
  cp "$HOOK" "$repo/.githooks/pre-commit"
  chmod +x "$repo/.githooks/pre-commit"
  printf '%s\n' '#!/usr/bin/env bash' 'exit 0' > "$repo/scripts/ai/check-agent-infra.sh"
  chmod +x "$repo/scripts/ai/check-agent-infra.sh"
  printf '# Context\n' > "$repo/PROJECT_CONTEXT.md"
  printf '# Handoff\n' > "$repo/docs/ai/HANDOFF.md"

  git -C "$repo" init -q
  git -C "$repo" config user.name "Pre-commit Fixture"
  git -C "$repo" config user.email "fixture@example.invalid"
  git -C "$repo" add .
  git -C "$repo" commit -q -m "fixture baseline"
}

run_hook() {
  repo="$1"
  (
    cd "$repo" || exit 2
    GIT_CONFIG_GLOBAL=/dev/null bash .githooks/pre-commit
  ) 2>&1
}

make_repo "$TMP_ROOT/partial-infra"
printf '%s\n' '#!/usr/bin/env bash' 'exit 1' > "$TMP_ROOT/partial-infra/scripts/ai/check-agent-infra.sh"
git -C "$TMP_ROOT/partial-infra" add scripts/ai/check-agent-infra.sh
git -C "$TMP_ROOT/partial-infra" show HEAD:scripts/ai/check-agent-infra.sh \
  > "$TMP_ROOT/partial-infra/scripts/ai/check-agent-infra.sh"
out="$(run_hook "$TMP_ROOT/partial-infra")"
rc=$?
if [ "$rc" -ne 0 ] \
  && printf '%s\n' "$out" | grep -F '同时存在 staged 和 unstaged 差异' >/dev/null \
  && printf '%s\n' "$out" | grep -F 'scripts/ai/check-agent-infra.sh' >/dev/null; then
  pass "staged broken infra with clean worktree is rejected"
else
  fail "partial-staged infra should fail closed"
fi

make_repo "$TMP_ROOT/project-context-only"
printf '%s\n' '# Context' '' 'Updated index.' > "$TMP_ROOT/project-context-only/PROJECT_CONTEXT.md"
git -C "$TMP_ROOT/project-context-only" add PROJECT_CONTEXT.md
out="$(run_hook "$TMP_ROOT/project-context-only")"
rc=$?
if [ "$rc" -eq 0 ]; then
  pass "PROJECT_CONTEXT-only staged change is exempt from HANDOFF requirement"
else
  fail "PROJECT_CONTEXT-only staged change should pass"
fi

printf '%s\n' "RESULT: pass=$pass_count fail=$fail_count"
[ "$fail_count" -eq 0 ]
