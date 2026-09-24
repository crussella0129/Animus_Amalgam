# Sprint 2 Meta

- **Sprint number:** 2
- **Book schema version:** 2
- **Start timestamp:** 2026-09-24T03:27:07Z
- **End timestamp:** (filled at Loop Phase)
- **Model:** GPT-6
- **Bundle version:** 0.22.0
- **Exit status:** in-progress
- **Token count:** (filled at Loop Phase if observable)
- **Summary:** Operate isolated 27B Hermes, repair encountered failures, then verify the bounded runtime formally.
- **Intents:** [INT-0004](../../intents/INT-0004-bounded-local-model-qualification.md)
- **Completion evidence:** (filled at Loop Phase)

## Blockages

- 2026-09-24: the owner authorized prioritizing Amalgam and stopping the
  restarted CubiKan WSL build. RAM admission subsequently passed. The corrected
  loader then hit the global page-in threshold while still loading; this
  measurement does not identify pagefile versus model-file reads. See the
  [operational ledger and proposed bounded amendment](sprint-tests/operational-ledger.md).
  Keep T-208 and T-209 pending; no inference or formal suite has yet run.
- 2026-09-24 continuation: owner approved the bounded loader amendment. The
  load-phase blocker is ready for replay; stopped overnight approval time is
  recorded separately without resetting consumed work or launch/request counts.
- 2026-09-24 after attempt 09: six launches exhausted, five inference requests
  consumed. Real startup succeeds; a valid terminal action was generated but
  stopped before execution by the global page-in guard. Useful-task completion
  and dedicated main/auxiliary cancellation remain unresolved. The operational
  ledger contains a concrete next-step proposal; official suites remain not run.
- 2026-09-24 resolved: the owner answered “continue” and asked for the
  direction to be checked. The session moved from GPT-6 (Codex) to Claude
  Opus 5.5 (Claude Code). The approved continuation (6144-token input, nine
  launches, RAM-conditional page-in stop), plus attempt-scoped time charging,
  unblocked the loop. Attempts 10–11 completed the useful task, the
  continued session and both cancellations. Attempt 13 replayed the
  refactored harness after the owner freed memory. See the
  [direction review](../../lineage/direction-review.md).
