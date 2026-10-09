# Test Critique — Sprint 3

Round 10, an independent read-only critic run at head `230d451b60`, after
the round-9 response. It passed with caveats. Each caveat is addressed in
the round-10 response commits. The dispositions are in the
[test report](test-report.md), and the re-review is in
[critique](critique.md).

## Concerns

### C-001: The round-9 refusal field is only ever asserted false, and attempt 10's exact retry is never run as one scenario
- **Where:** the refusal branch of `wire._handle`, which reads `session["last_finish"]`, a value set only after the accounting tail; `test_sequential_request_after_done_is_accepted_and_concurrent_is_refused`; `test_length_finish_marks_the_next_request_a_continuation`
- **Quote:** `assert refusal["follows_length_finish"] is False`
- **Failure mode:** weak-assertion
- **Why it matters:** The true case never runs. A refusal on the lock-timeout path reads the previous request's finish. A length finish followed by a retry at `[DONE]` is never tested as one scenario.
- **Suggested response:** tighten-assertion. Test both true cases, and set the finish before the in-flight claim is released.

### C-002: M3's "retries" is implemented only as "follows a `length` finish", but INT-0004 AC4 is reported Closed
- **Where:** INT-0004 AC4; build-plan M3; `continuation_of_length_finish`; Hermes's empty-response retry
- **Quote:** M3: "truncation continuations and retries"
- **Failure mode:** EARS-coverage
- **Why it matters:** A retry after a non-length finish re-sends the same conversation and would be published as an ordinary request. No published session repeats a prompt hash, so Sprint 3 missed no retry.
- **Suggested response:** publish `retry_of` from a repeated `prompt_sha256` within a session, or defer it to T-224.

### C-003: The cross-sprint receipt suite checks historical evidence against mutable lab config, not the frozen manifests
- **Where:**
  - `test_published_screen_reproduces_the_recorded_winners`, which reads the current `arms.json`;
  - `test_hermes_timers_hold_at_or_above_each_sessions_backstop`, which recomputes the backstop with the current code.
- **Quote:** `assert winners == arms["screen_winners"]`
- **Failure mode:** flake-risk
- **Why it matters:** A new screen, or T-225, would turn Sprint 3's check red with no change to its evidence.
- **Suggested response:** tighten-assertion. Use the frozen manifests as the oracle, and record the applied backstop.

### C-004: The M4 first-prefix check skips every cut-short session, under a rationale that is false for them
- **Where:** `test_sessions_record_their_first_rendered_prefix`; publish's at-publish session record; `run.stopped_session`
- **Quote:** `if first is None:  # stopped before any request reached the wire`
- **Failure mode:** weak-assertion
- **Why it matters:** The cut-short sessions of attempts 05, 07, 11 and 12 made 3, 3, 3 and 11 requests, yet carry no `first_request`.
- **Suggested response:** tighten-assertion. Skip only sessions with zero requests.

### C-005: Two record statements do not match the ledger and V2 table
- **Where:** the test report's AC7 row and V2 row; `unit-tests.md`
- **Quote:** "Live, only stalls and resource guards stopped work"; "The 13 API reds of rounds 3 to 7 are the new fields and seams that those rounds' behavior reds depend on."
- **Failure mode:** evidence-drift
- **Why it matters:** Lab-defect stops (02, 05, 07, 10) also stopped work. Round 7's API reds underlie no behavior red.
- **Suggested response:** tighten-assertion (wording only).

## Confidence
proceed-with-caveats
