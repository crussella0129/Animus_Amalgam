# Test Critique — Sprint 0

This review was run inline by the primary agent, reading only, against
`prompts/test-critic.md`. It was not run in an independent subagent, because
the owner limited Sprint 0's usage budget. One concern was fixed and verified;
two are deferred with rationale.

## Concerns

### C-001: The upstream-boundary assertion checked names, not what they mean
- **Where:** `unit-tests.md` T-001 `test_readme_upstream_boundary` / INT-0001 AC3
- **Quote:** "that section's body contains `website/`, `README.md` and `AGENTS.md`"
- **Failure mode:** weak-assertion
- **Why it matters:** AC3 requires the README to state *where the Book ends*. A section that listed those names while saying they belong in the Book would still have passed.
- **Suggested response:** tighten-assertion. **Resolved** in `8827c4e6f4`. The test now also requires that the section says `website/` is where "Fork records do not go", and that the root files including `AGENTS.md` "are owned by upstream and are outside the Book". Two mutated READMEs, one with "are owned" changed and one with "Fork records do" changed, each made the test fail. The unchanged README passes.

### C-002: Only the link checker has a negative-path test
- **Where:** `unit-tests.md` `test_intent_index_complete`, `test_backlog_format`, `test_backlog_intent_linkage`
- **Quote:** "every `INT-*.md` link target exists" / "no `(backlog)` line fails the locked regex"
- **Failure mode:** negative-path
- **Why it matters:** The logic that detects a dangling index link, a malformed backlog line, or a missing Work-evidence link runs only on data that passes. A bug that always passed would go unnoticed.
- **Suggested response:** defer-with-rationale. Each detector is a single `grep` or file-existence check whose failure branch is a plain `return 1`, and the one EARS clause about an error path (AC2 link resolution) has an executed negative test. Sprint 1 adds the lineage chapters and many new links, so a reusable Book test harness with mutation cases fits there. It is recorded under backlog [T-106](../../../work/tasks.md) (CI and checkpoint expectations for [INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md)).

### C-003: The E2E setup differs from the locked plan's wording
- **Where:** `e2e-tests.md` `test_cold_clone_orientation` / `test-plan.md` End-to-End Tests
- **Quote:** "`git clone --branch dev` the local repository into the scratchpad"
- **Failure mode:** evidence-drift
- **Why it matters:** The run that passed also creates a local `main` from `origin/main` and uses a sparse checkout. A reader might suspect the setup was changed just to make it pass.
- **Suggested response:** reject (the critique is wrong because all four locked assertions are unchanged, and only the setup was corrected to match how a newcomer actually arrives). A GitHub clone checks out `main`, then `git checkout dev`, which leaves both profile branches local. `e2e-tests.md` records the failed first run, its root cause (`substrate-partial:branch:main` with no local `main`), and the separate Git Bash path-conversion problem, so the evidence is complete.

## Confidence
proceed-with-caveats
