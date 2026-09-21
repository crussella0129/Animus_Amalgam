# Sprint 0 Test Report

## Intent Verification
| Intent | Acceptance criterion | EARS / tests | Result | Intent evidence update |
|--------|----------------------|---------------|--------|------------------------|
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC1: substrate complete, contract 4, profile github main ← dev human-approve | met at init / `test_substrate_complete` | pass | Test evidence links this report |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC2: `check-book.sh`, SUMMARY reachability, relative links resolve | `test_check_book_passes`, `test_summary_reaches_every_intent`, `test_all_relative_links_resolve`, `test_link_checker_detects_broken_link`, `test_intent_index_complete` | pass | Test evidence links this report |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC3: README states the fork's identity, purpose, authority order and upstream boundary | T-001, four README clauses / `test_readme_fork_identity`, `test_readme_fork_purpose`, `test_readme_authority_order`, `test_readme_upstream_boundary` | pass | Documentation evidence: `docs/README.md` and `docs/intents/README.md` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC4: backlog queued and linked from intents | T-002, three clauses / `test_backlog_format`, `test_backlog_intent_linkage`, `test_no_sprint0_tasks_remain` | pass | Work evidence links T-106; INT-0002 and INT-0003 link T-101 to T-105 |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC5: diff limited to `docs/**` and the sprint-loops `.gitignore` block | `test_diff_scope_docs_only` | pass | eligible for `realized` once completion evidence is attached in Loop |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | Intent: someone new can orient and resume from the tracked Book | `test_cold_clone_orientation` | pass | none |

## Summary
- Unit tests: 9 passed / 0 failed / 9 total ([unit-tests.md](unit-tests.md))
- Integration tests: 5 passed / 0 failed / 5 total ([integration-tests.md](integration-tests.md))
- E2E tests: 1 passed / 0 failed / 1 total ([e2e-tests.md](e2e-tests.md))
- CI status: not configured for the work branch

## CI Confirmation
- **Head SHA:** `8827c4e6f4b910ff481e62092679bd59c3a2dff1` (`dev`)
- **CI run:** none. The inherited `ci.yaml` runs on `pull_request` and on pushes to `main` only, so pushes to `dev` trigger nothing.
- **Conclusion:** CI not configured, so these are local confirmations only.
- **Confirmations:** `SPRINT_LOOP_SKILL_DIR=<installed 0.22.0 skill dir> bash docs/sprints/s0/sprint-tests/run-tests.sh all` printed 15 `PASS` lines and `failures=0`. The per-suite records are linked above. The checkpoint pull request's CI is observed after the Loop phase opens it.

## Failures
None at the final head. The first E2E run failed because of how the test was
set up: it had no local `main` branch. See [e2e-tests.md](e2e-tests.md) and
[critique C-003](critique.md).

## Technical Debt Identified
- [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md): the Book has no reusable test harness with negative (mutation) cases for index, backlog and evidence linkage, and no CI job runs the Book checks. Both are deferred to backlog T-106 (critique C-002).

## Coverage Observations
- Every INT-0001 acceptance criterion and all 8 EARS clauses map to at least one executed test.
- INT-0002 and INT-0003 are not advanced this sprint. They are covered only structurally, by `test_check_book_passes`, and for backlog linkage, by `test_backlog_intent_linkage`.
- `check-substrate.sh` requires local branches for both profile branches. A clone made with `--branch dev` alone reports `substrate-partial:branch:main`. A normal GitHub clone followed by `git checkout dev` does not have this problem.
