# Sprint 0 Test Plan

## Intent Traceability
| Intent | Acceptance criterion | Build task / EARS clause | Verification |
|--------|----------------------|--------------------------|--------------|
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC1: substrate complete; marker at schema 2 and substrate 4; profile is github, main ← dev, human-approve | met at init by `deploy-substrate.sh` in `84a5005b2c`, no build task | `test_substrate_complete` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC2: `check-book.sh` passes | T-001 and T-002 must keep the Book valid | `test_check_book_passes` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC2: every intent is linked from SUMMARY | T-001 and T-002 | `test_summary_reaches_every_intent` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC2: every relative link under `docs/` resolves | T-001 and T-002 | `test_all_relative_links_resolve`, `test_link_checker_detects_broken_link` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC3: README states the fork identity | T-001 / WHEN README is read THEN SHALL name Hermes Agent and link upstream | `test_readme_fork_identity` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC3: README states the fork's purpose | T-001 / WHEN README is read THEN SHALL name AACD, Animus_Ferric and Kinesin and link INT-0002 and INT-0003 | `test_readme_fork_purpose` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC3: README states the authority order | T-001 / WHEN README is read THEN SHALL state intents → work → sprints → SUMMARY | `test_readme_authority_order` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC3: README states the upstream boundary | T-001 / WHEN README is read THEN SHALL name `website/` and the upstream root files | `test_readme_upstream_boundary` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC2 and AC3: the intent index is complete | T-001 / WHEN the intent index is read THEN SHALL link every chapter and no missing path | `test_intent_index_complete` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC4: backlog queued | T-002 / WHEN `tasks.md` is parsed THEN backlog lines SHALL be well formed and exactly T-101 to T-106 | `test_backlog_format` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC4: each backlog task is linked from its intent | T-002 / WHEN a backlog task names INT-X THEN INT-X's Work evidence SHALL link it | `test_backlog_intent_linkage` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC4: execution state is consistent | T-002 / WHEN Build completes THEN `tasks.md` SHALL contain no `(sprint 0)` entry | `test_no_sprint0_tasks_remain` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | AC5: the diff touches only `docs/**` and the sprint-loops `.gitignore` block | all tasks | `test_diff_scope_docs_only` |
| [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md) | Intent: an arrival with no prior context can orient and resume from the tracked Book alone | all tasks | `test_cold_clone_orientation` |

## Unit Tests
### T-001 unit tests
- **Intent:** [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md)
- `test_readme_fork_identity`: `docs/README.md` contains "Hermes Agent" and `https://github.com/NousResearch/hermes-agent`.
- `test_readme_fork_purpose`: `docs/README.md` contains "Adaptive Constrained Decoding", "Animus_Ferric" and "Kinesin", plus links whose targets contain `intents/INT-0002-` and `intents/INT-0003-`.
- `test_readme_authority_order`: `docs/README.md` has an authority list in which intents, work, sprints and SUMMARY appear in that order. The test checks the order by comparing line numbers, not just that each word is present.
- `test_readme_upstream_boundary`: `docs/README.md` has exactly one `## Where the Book ends` section, and that section's body contains `website/`, `README.md` and `AGENTS.md`. The test extracts the section with awk and does not match against the whole file.
- `test_intent_index_complete`: for every `docs/intents/INT-*.md` file, `docs/intents/README.md` contains a link to its basename. Every `INT-*.md` link target in the index exists.
- Stubs: none. Every assertion runs against the committed files.

### T-002 unit tests
- **Intent:** [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md)
- `test_backlog_format`: every `(backlog)` line in `docs/work/tasks.md` matches the EARS regex, and the sorted set of backlog task IDs is exactly `T-101 T-102 T-103 T-104 T-105 T-106`.
- `test_backlog_intent_linkage`: for each backlog line and each `INT-X` it names, the `- **Work evidence:**` line of `docs/intents/INT-X-*.md` contains `[…T-NNN…](`.
- `test_no_sprint0_tasks_remain`: `grep -c '(sprint 0)' docs/work/tasks.md` returns 0.
- `test_link_checker_detects_broken_link` is the negative path. The test copies `docs/` into a temporary directory, appends `[x](does-not-exist.md)` to the copied README, runs `check-links.sh` on the copy, and asserts a non-zero exit and that the missing target is named in the output.

## Integration Tests
### Book integrity
- **Intents:** [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md)
- `test_check_book_passes`: the installed `check-book.sh` exits 0 and reports 3 intent chapters.
- `test_summary_reaches_every_intent`: every `docs/intents/INT-*.md` basename appears as a link target in `docs/SUMMARY.md`.
- `test_all_relative_links_resolve`: `docs/sprints/s0/sprint-tests/check-links.sh docs` exits 0. The checker follows every relative Markdown link target under `docs/`, stripping any `#fragment`, and treats `http(s)` and `mailto` links as out of scope.
- `test_substrate_complete`: the installed `check-substrate.sh` prints `substrate-complete`; `docs/.sprint-loop-book` contains `schema-version: 2` and `substrate-version: 4`; the installed `remote-profile.sh` resolves provider `github`, base `main`, work `dev` and mergePolicy `human-approve`.
- `test_diff_scope_docs_only`: every path in `git diff --name-only main..dev` is under `docs/` or is `.gitignore`. Every line `git diff main..dev -- .gitignore` adds lies between `# >>> sprint-loops >>>` and `# <<< sprint-loops <<<` inclusive, and no line is removed.

## End-to-End Tests
- **Status:** possible
- `test_cold_clone_orientation`: `git clone --branch dev` the local repository into the scratchpad. In the clone:
  - `current-phase.sh` prints the same phase as the working repository;
  - `check-book.sh` exits 0;
  - `check-substrate.sh` prints `substrate-complete`;
  - `docs/README.md` exists.

  The test passes only if all four hold. This shows the Book is fully tracked and works without any local state.
- **CI:** `ci.yaml` runs on `pull_request` and on pushes to `main` only, so pushing to `dev` triggers nothing. The Test phase records local confirmations, and the checkpoint pull request's CI is observed after the Loop phase opens it.
