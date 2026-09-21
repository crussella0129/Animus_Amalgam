#!/usr/bin/env bash
# Sprint 0 test suite: runs every named test in the locked test plan
# (sprint-plans/test-plan.md) against the committed Book, and prints one
# PASS/FAIL line per test.
# Usage (from the project root):
#   SPRINT_LOOP_SKILL_DIR=<installed skill dir> bash docs/sprints/s0/sprint-tests/run-tests.sh [unit|integration|e2e|all]
set -uo pipefail

SK="${SPRINT_LOOP_SKILL_DIR:?set SPRINT_LOOP_SKILL_DIR to the installed sprint-loop skill directory}"
SUITE="${1:-all}"
HERE="docs/sprints/s0/sprint-tests"
README=docs/README.md
INDEX=docs/intents/README.md
TASKS=docs/work/tasks.md
fails=0

report() { # name, status(0=pass)
  if [ "$2" -eq 0 ]; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi
}

# ---------- unit: T-001 ----------
test_readme_fork_identity() {
  grep -q 'Hermes Agent' "$README" &&
    grep -qF 'https://github.com/NousResearch/hermes-agent' "$README"
}
test_readme_fork_purpose() {
  grep -q 'Adaptive Constrained Decoding' "$README" &&
    grep -q 'Animus_Ferric' "$README" && grep -q 'Kinesin' "$README" &&
    grep -qE '\]\(intents/INT-0002-[^)]+\.md\)' "$README" &&
    grep -qE '\]\(intents/INT-0003-[^)]+\.md\)' "$README"
}
test_readme_authority_order() {
  local a b c d
  a=$(grep -nE '^1\. \*\*Intents\*\*' "$README" | cut -d: -f1)
  b=$(grep -nE '^2\. \*\*Work ledgers\*\*' "$README" | cut -d: -f1)
  c=$(grep -nE '^3\. \*\*Sprint records\*\*' "$README" | cut -d: -f1)
  d=$(grep -nE '^4\. \*\*\[SUMMARY\.md\]' "$README" | cut -d: -f1)
  [ -n "$a" ] && [ -n "$b" ] && [ -n "$c" ] && [ -n "$d" ] &&
    [ "$a" -lt "$b" ] && [ "$b" -lt "$c" ] && [ "$c" -lt "$d" ]
}
test_readme_upstream_boundary() {
  local section
  [ "$(grep -c '^## Where the Book ends$' "$README")" -eq 1 ] || return 1
  section=$(awk '/^## Where the Book ends$/ { f = 1; next } f && /^## / { f = 0 } f' "$README")
  printf '%s\n' "$section" | grep -qF 'website/' &&
    printf '%s\n' "$section" | grep -qF 'README.md' &&
    printf '%s\n' "$section" | grep -qF 'AGENTS.md' &&
    printf '%s\n' "$section" | tr '\n' ' ' |
      grep -qE '`website/`[^.]*upstream[^.]*\.[[:space:]]+Fork records[[:space:]]+do[[:space:]]+not go there' &&
    printf '%s\n' "$section" | tr '\n' ' ' |
      grep -qE '`AGENTS\.md`.{0,40}are owned[[:space:]]+by upstream[[:space:]]+and are outside the Book'
}
test_intent_index_complete() {
  local f t
  for f in docs/intents/INT-*.md; do
    grep -qF "($(basename "$f"))" "$INDEX" || { echo "  index misses $f"; return 1; }
  done
  for t in $(grep -oE '\(INT-[0-9]{4}-[^)]+\.md\)' "$INDEX" | tr -d '()'); do
    [ -f "docs/intents/$t" ] || { echo "  index links missing $t"; return 1; }
  done
}

# ---------- unit: T-002 ----------
BACKLOG_RE='^- \[ \] T-[0-9]+ \(backlog\) \[intent: INT-[0-9]{4}(, INT-[0-9]{4})*\]: .+ — touches: .+$'
test_backlog_format() {
  local malformed ids
  malformed=$(grep -F '(backlog)' "$TASKS" | grep -cvE "$BACKLOG_RE")
  ids=$(grep -F '(backlog)' "$TASKS" | grep -oE '^- \[ \] T-[0-9]+' | grep -oE 'T-[0-9]+' | sort | tr '\n' ' ')
  [ "$malformed" -eq 0 ] && [ "$ids" = "T-101 T-102 T-103 T-104 T-105 T-106 " ]
}
test_backlog_intent_linkage() {
  local line task intent file rc=0
  while IFS= read -r line; do
    task=$(printf '%s\n' "$line" | grep -oE 'T-[0-9]+' | head -1)
    for intent in $(printf '%s\n' "$line" | grep -oE '\[intent: [^]]*\]' | grep -oE 'INT-[0-9]{4}'); do
      file=$(ls docs/intents/"$intent"-*.md 2>/dev/null | head -1)
      if [ -z "$file" ] || ! grep -F -- '- **Work evidence:** ' "$file" | grep -qE "\[[^]]*$task[^]]*\]\("; then
        echo "  $task not linked from $intent Work evidence"; rc=1
      fi
    done
  done < <(grep -F '(backlog)' "$TASKS")
  return $rc
}
test_no_sprint0_tasks_remain() {
  [ "$(grep -c '(sprint 0)' "$TASKS")" -eq 0 ]
}
test_link_checker_detects_broken_link() {
  local tmp out rc
  tmp=$(mktemp -d)
  cp -R docs "$tmp/docs"
  printf '\n[x](does-not-exist.md)\n' >> "$tmp/docs/README.md"
  out=$(bash "$HERE/check-links.sh" "$tmp/docs" 2>&1); rc=$?
  rm -rf "$tmp"
  [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'BROKEN .*README.md: does-not-exist.md'
}

# ---------- integration ----------
test_check_book_passes() {
  bash "$SK/scripts/check-book.sh" | grep -qx 'check-book: valid v2 Book (3 intent chapters)'
}
test_summary_reaches_every_intent() {
  local f
  for f in docs/intents/INT-*.md; do
    grep -qF "(intents/$(basename "$f"))" docs/SUMMARY.md || { echo "  SUMMARY misses $f"; return 1; }
  done
}
test_all_relative_links_resolve() {
  bash "$HERE/check-links.sh" docs
}
test_substrate_complete() {
  [ "$(bash "$SK/scripts/check-substrate.sh")" = substrate-complete ] &&
    grep -qx 'schema-version: 2' docs/.sprint-loop-book &&
    grep -qx 'substrate-version: 4' docs/.sprint-loop-book &&
    [ "$(bash "$SK/scripts/remote-profile.sh" provider)" = github ] &&
    [ "$(bash "$SK/scripts/remote-profile.sh" base)" = main ] &&
    [ "$(bash "$SK/scripts/remote-profile.sh" work)" = dev ] &&
    [ "$(bash "$SK/scripts/remote-profile.sh" mergePolicy)" = human-approve ]
}
test_diff_scope_docs_only() {
  local outside removed state=before line
  outside=$(git diff --name-only main..dev | grep -vE '^docs/' | grep -vx '.gitignore')
  [ -z "$outside" ] || { echo "  outside scope: $outside"; return 1; }
  removed=$(git diff main..dev -- .gitignore | grep -E '^-' | grep -vcE '^---')
  [ "$removed" -eq 0 ] || { echo "  .gitignore lines removed: $removed"; return 1; }
  while IFS= read -r line; do
    case "$state:$line" in
      "before:# >>> sprint-loops >>>") state=inside ;;
      "inside:# <<< sprint-loops <<<") state=after ;;
      inside:*) ;;
      *) echo "  .gitignore addition outside the sprint-loops block: $line"; return 1 ;;
    esac
  done < <(git diff main..dev -- .gitignore | grep -E '^\+' | grep -vE '^\+\+\+' | cut -c2-)
  [ "$state" = after ]
}

# ---------- e2e ----------
test_cold_clone_orientation() {
  local tmp here_phase clone_phase rc=0
  tmp=$(mktemp -d)
  # Sparse: the Book plus .gitignore is all the helpers read, and a full
  # checkout of this repository is slow and trips Windows file locks on cleanup.
  git clone --quiet --no-checkout --branch dev "$(pwd)" "$tmp/clone" || { rm -rf "$tmp"; return 1; }
  MSYS_NO_PATHCONV=1 git -C "$tmp/clone" sparse-checkout set --no-cone '/docs/' '/.gitignore' &&
    git -C "$tmp/clone" checkout --quiet dev || { rm -rf "$tmp"; return 1; }
  # A newcomer's GitHub clone checks out the default branch (main) and then
  # `git checkout dev`, which leaves both profile branches local. `--branch dev`
  # alone leaves no local main, and check-substrate reports
  # substrate-partial:branch:main. Recreate the newcomer's state.
  git -C "$tmp/clone" branch --quiet main origin/main || { rm -rf "$tmp"; return 1; }
  here_phase=$(bash "$SK/scripts/current-phase.sh")
  clone_phase=$(cd "$tmp/clone" && bash "$SK/scripts/current-phase.sh")
  [ "$here_phase" = "$clone_phase" ] || { echo "  phase differs: here=$here_phase clone=$clone_phase"; rc=1; }
  (cd "$tmp/clone" && bash "$SK/scripts/check-book.sh" >/dev/null) || { echo "  check-book failed in clone"; rc=1; }
  [ "$(cd "$tmp/clone" && bash "$SK/scripts/check-substrate.sh")" = substrate-complete ] || { echo "  substrate not complete in clone"; rc=1; }
  [ -f "$tmp/clone/docs/README.md" ] || { echo "  README missing in clone"; rc=1; }
  echo "  clone head=$(git -C "$tmp/clone" rev-parse --short HEAD) phase=$clone_phase"
  rm -rf "$tmp" 2>/dev/null || true
  return $rc
}

run() { local t; for t in "$@"; do "$t"; report "$t" $?; done; }
UNIT=(test_readme_fork_identity test_readme_fork_purpose test_readme_authority_order
      test_readme_upstream_boundary test_intent_index_complete test_backlog_format
      test_backlog_intent_linkage test_no_sprint0_tasks_remain test_link_checker_detects_broken_link)
INTEGRATION=(test_check_book_passes test_summary_reaches_every_intent test_all_relative_links_resolve
             test_substrate_complete test_diff_scope_docs_only)
E2E=(test_cold_clone_orientation)

echo "head=$(git rev-parse HEAD) branch=$(git rev-parse --abbrev-ref HEAD) suite=$SUITE"
case "$SUITE" in
  unit) run "${UNIT[@]}" ;;
  integration) run "${INTEGRATION[@]}" ;;
  e2e) run "${E2E[@]}" ;;
  all) run "${UNIT[@]}" "${INTEGRATION[@]}" "${E2E[@]}" ;;
  *) echo "unknown suite $SUITE" >&2; exit 2 ;;
esac
echo "failures=$fails"
[ "$fails" -eq 0 ]
