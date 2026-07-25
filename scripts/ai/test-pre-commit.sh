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
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -u' \
    'ROOT="$(cd "$(dirname "$0")/../.." && pwd)"' \
    'cd "$ROOT" || exit 2' \
    'if ! grep -qF "## Required Heading" AGENTS.md; then' \
    '  echo "FAIL: missing required heading in AGENTS.md"' \
    '  exit 1' \
    'fi' \
    'if [ ! -f docs/README.md ]; then' \
    '  echo "FAIL: missing docs/README.md"' \
    '  exit 1' \
    'fi' \
    'if ! git ls-files --error-unmatch AGENTS.md >/dev/null 2>&1; then' \
    '  echo "FAIL: original index is unavailable"' \
    '  exit 1' \
    'fi' \
    'exit 0' \
    > "$repo/scripts/ai/check-agent-infra.sh"
  chmod +x "$repo/scripts/ai/check-agent-infra.sh"
  printf '%s\n' '# Agents' '## Required Heading' > "$repo/AGENTS.md"
  printf '# Context\n' > "$repo/PROJECT_CONTEXT.md"
  printf '# Docs\n' > "$repo/docs/README.md"
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

make_repo "$TMP_ROOT/broken-heading"
printf '%s\n' '# Agents' > "$TMP_ROOT/broken-heading/AGENTS.md"
git -C "$TMP_ROOT/broken-heading" add AGENTS.md
git -C "$TMP_ROOT/broken-heading" show HEAD:AGENTS.md \
  > "$TMP_ROOT/broken-heading/AGENTS.md"
out="$(run_hook "$TMP_ROOT/broken-heading")"
rc=$?
if [ "$rc" -ne 0 ] \
  && printf '%s\n' "$out" | grep -F 'missing required heading in AGENTS.md' >/dev/null; then
  pass "staged broken heading with restored clean worktree is rejected"
else
  fail "staged broken heading should fail against the index snapshot"
fi

make_repo "$TMP_ROOT/deleted-recreated-infra"
git -C "$TMP_ROOT/deleted-recreated-infra" rm --cached -q docs/README.md
out="$(run_hook "$TMP_ROOT/deleted-recreated-infra")"
rc=$?
if [ "$rc" -ne 0 ] \
  && printf '%s\n' "$out" | grep -F 'missing docs/README.md' >/dev/null; then
  pass "staged infra deletion with same-path untracked recreation is rejected"
else
  fail "staged deletion with same-path untracked recreation should fail against the index snapshot"
fi

make_repo "$TMP_ROOT/deleted-ignored-recreation"
git -C "$TMP_ROOT/deleted-ignored-recreation" rm --cached -q docs/README.md
printf 'docs/README.md\n' > "$TMP_ROOT/deleted-ignored-recreation/.gitignore"
git -C "$TMP_ROOT/deleted-ignored-recreation" add .gitignore
out="$(run_hook "$TMP_ROOT/deleted-ignored-recreation")"
rc=$?
if [ "$rc" -ne 0 ] \
  && printf '%s\n' "$out" | grep -F 'missing docs/README.md' >/dev/null; then
  pass "staged deletion with staged ignore and ignored same-path recreation is rejected"
else
  fail "ignored same-path recreation should fail against the index snapshot"
fi

make_repo "$TMP_ROOT/project-context-only"
printf '%s\n' '# Context' '' 'Updated index.' > "$TMP_ROOT/project-context-only/PROJECT_CONTEXT.md"
printf 'unrelated scratch\n' > "$TMP_ROOT/project-context-only/unrelated.tmp"
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
