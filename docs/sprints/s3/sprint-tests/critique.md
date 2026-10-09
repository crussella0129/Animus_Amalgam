# Test Critique — Sprint 3

Round 11, the final independent read-only critic run, at head `183c8fe431`
after the round-10 response. Rounds 1 to 5 blocked. Rounds 6 to 11 passed
with caveats, and the caveats of rounds 6 to 10 were addressed in code,
tests and records (critique-01 to critique-10). This round's caveats are
dispositioned in the [test report](test-report.md). The scope and wording
corrections are recorded there, and the remaining work goes to backlog
T-224 and T-226.

## Concerns

### C-001: `retry_of` catches only byte-identical re-sends, so one Hermes retry class on this route still publishes as an ordinary request
- **Where:** `publish.receipts` (`retry_of`); Hermes's post-tool empty-response nudge (`agent/turn_empty_response.py`); the test report's INT-0004 AC4 row and round-10 C-002 disposition; T-224's checklist
- **Quote:** "Retries are published as truncation continuations, as refusals that name a preceding length finish, and, since round 10, as `retry_of` for any re-sent conversation"
- **Failure mode:** EARS-coverage
- **Why it matters:** Hermes's empty-response recovery re-requests after a `stop` finish, with an `(empty)` assistant row and a nudge appended. That request gets neither marker. No published request had an empty response, so no Sprint 3 figure is wrong, but "Fixed" and "Closed" claim more than the rule covers.
- **Suggested response:** tighten-assertion. Mark a request that follows an empty response, or defer it to T-224 and narrow the AC4 wording.

### C-002: The round-10 "applied backstop" is untested where it is written, and the receipt rule silently falls back, so T-224's named acceptance check cannot fail on it
- **Where:** `run.py` (`request_backstop_seconds=windows["request_backstop"]`); `test_hermes_timers_hold_at_or_above_each_sessions_backstop`; T-224
- **Quote:** `backstop = start.get("request_backstop_seconds") or request_backstop(...)`
- **Failure mode:** weak-assertion
- **Why it matters:** A schema-3 receipt without the field passes. The suite has no rule for T-224's retry item. The schema-2 recompute uses the current formula, which T-219 may change.
- **Suggested response:** tighten-assertion. Require the field for schema 3, test that it equals `session_windows`' backstop, add or name as manual T-224's other checks, and state that the recompute uses the current formula.

### C-003: The attempt-10 sequential-retry repair was never replayed live, and no backlog task commits to provoking it
- **Where:** the ledger's provenance row for `c783199787`; the e2e "Not run or deferred" section; T-224; `wire.bound_body`, which replaces Hermes's boosted retry `max_tokens` with the arm cap
- **Quote:** "The live sequential-retry path: not re-triggered, because attempts 11–13 produced no cap-truncated tool call. It is covered by the integration test."
- **Failure mode:** e2e-cop-out
- **Why it matters:**
  - INT-0004 AC7 asks for each repair's replay outcome, and this is the only pre-confidence repair never exercised live.
  - Live, an admitted retry runs under the same cap that cut the first call, so it can be cut again.
- **Suggested response:** defer-with-rationale. Have T-224 provoke a cap-cut tool call deliberately, with a cap below one call, and check the receipts.

### C-004: The round-10 wire change has no test that runs it, and one record credits it to a test that passes without it
- **Where:** `wire.py`, which sets `last_finish` before release; the integration row for `test_a_refusal_after_a_length_finish_says_so`; test-report "Failures found and fixed" item 11
- **Quote:** "The wire records each finish before admitting the next request."
- **Failure mode:** evidence-drift
- **Why it matters:** Both round-10 tests pass on base, so reverting the change leaves the suite green. Item 11 also omits C-001's code change. Impact is low.
- **Suggested response:** tighten-assertion (wording). Optionally add a lock-timeout refusal test that is red on base.

## Confidence
proceed-with-caveats
