# Plan Critique — Sprint 0

This review was run inline by the primary agent, reading only, against
`prompts/plan-critic.md`. It was not run in an independent subagent, because
the owner limited Sprint 0's usage budget. Two concerns were fixed in the plan
before locking, and one is deferred.

## Concerns

### C-001: The upstream-boundary clause could not be tested precisely
- **Where:** `build-plan.md` T-001, fourth EARS clause / `test-plan.md` `test_readme_upstream_boundary`
- **Quote:** "each in a sentence that marks them as outside the Book"
- **Failure mode:** EARS-vague
- **Why it matters:** Whether a sentence "marks" something as outside the Book is a judgment call. Merely mentioning `README.md` anywhere in the file would pass a grep across the whole file.
- **Suggested response:** fix-in-plan. **Resolved:** the clause and the test now require a single `## Where the Book ends` section and check its body only.

### C-002: The risk of publishing to a public repository has no verification
- **Where:** `research-report.md` §4, "the repository is public"
- **Quote:** "Book content becomes public once the checkpoint branch is pushed"
- **Failure mode:** missing-risk
- **Why it matters:** The checkpoint pushes `dev` to a public GitHub repository, and no planned test screens the Book for sensitive content.
- **Suggested response:** defer-with-rationale. This sprint's Book content is project-intent prose, written and reviewed in the sprint itself, with no configuration, credentials or machine-local paths. The inherited upstream CI (including `osv-scanner.yml` and the supply-chain lanes) runs on the checkpoint pull request. A standing content-screening policy belongs with upstream sync and CI expectations under backlog T-106 ([INT-0001](../../../intents/INT-0001-project-book-and-sprint-substrate.md)).

### C-003: T-001's touched paths omitted INT-0001's lifecycle edit
- **Where:** `build-plan.md` T-001 **Touches**
- **Quote:** "**Touches:** `docs/README.md`, `docs/intents/README.md`"
- **Failure mode:** hidden-dep
- **Why it matters:** Build moves INT-0001 from `planned` to `active` before T-001 starts. `commit-task.sh` commits only the paths it is given, so that edit would have been left uncommitted outside the task boundary, and later check-tracked gates would fail.
- **Suggested response:** fix-in-plan. **Resolved:** T-001 **Touches** now lists the INT-0001 chapter.

## Confidence
proceed-with-caveats
