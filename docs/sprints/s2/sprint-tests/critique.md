# Test Critique — Sprint 2

Round 4 (final), an independent read-only re-review at code head
`f8379f93ba`. The Sprint 2 test set passed 48/48 there. Earlier rounds:
[01](critique-01.md) (block), [02](critique-02.md) (block) and
[03](critique-03.md) (proceed-with-caveats). Round 3 concerns C-024 to C-030
were verified resolved, except that C-027's replay owner remained split.

The concerns below were addressed after this verdict, by wording and backlog
tightening only, with no code change:

- C-031: T-211 owns the replay, host condition and A→B→A; T-210 lists T-211
  as a prerequisite.
- C-032: EARS status added to the report Summary.
- C-033: T-207 correction appended.
- C-034: † added to AC2 cancellation, the ledger header and the E2E timeline.
- C-035: six repairs; page-in relabeled as an amendment; Ruff claim scoped.
- C-036: session-record anchor marked unpublished; helper results recorded at
  their actual run points; critique-03 added to SUMMARY.
- C-037: the report is linked from INT-0004's Test evidence.

## Concerns

### C-031: Deferred items and replay duties are missing from the backlog text of the tasks meant to carry them
- **Where:** test-report AC1 row and C-003 disposition; integration "Post-replay lab changes"; tasks T-210 and T-211.
- **Quote:** "The **next lab launch**, whichever of T-210 or T-211 runs first, replays all of these."
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion.

### C-032: The Summary shows no failures, and the report never gives each EARS clause's status
- **Where:** test-report Summary.
- **Quote:** "Integration tests: 13 passed / 0 failed / 13 total"
- **Failure mode:** EARS-coverage
- **Suggested response:** tighten-assertion (EARS status table).

### C-033: Completed-task T-207 still reads as a full D1/D2 pass
- **Where:** completed-tasks T-207.
- **Quote:** "a 128-token backend cap (attempts 06-11)"
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion (append a correction).

### C-034: Three places still state confidence or cancellation without the † condition
- **Where:** report AC2 result cell; ledger opening; E2E timeline bullet.
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion.

### C-035: Report statements disagree with their sources
- **Where:** AC7 "Seven defect repairs"; ledger criterion 2 page-in; Ruff sentence.
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion.

### C-036: Two `book_scope_review` rows need fixing
- **Where:** report scope-review rows 1 and 5; SUMMARY.
- **Quote:** "`check-book.sh` and `check-tracked.sh` run at the Loop boundary."
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion (run and record helper results or mark them pending; add critique-03 to SUMMARY; state that the anchor is unpublished).

### C-037: INT-0004 does not yet list the report as Test evidence
- **Where:** INT-0004 Test evidence field.
- **Failure mode:** evidence-drift
- **Suggested response:** tighten-assertion.

## Confidence
proceed-with-caveats
