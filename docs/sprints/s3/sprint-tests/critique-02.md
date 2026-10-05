# Test Critique — Sprint 3

Round 2, an independent read-only critic run at head `eae8756e6c`, after
the round-1 response. Each concern is addressed in the round-2 response
commits. The dispositions are in the [test report](test-report.md), and the
re-review is in [critique-03](critique-03.md).

## Concerns

### C-001: Nothing tests the attempt-stop timing path, yet AC7 is marked "Met" on the strength of it
- **Where:** `run.py` main `finally` (`request_stopped`); `wire.py` `_handle` except branch; `publish.py` `request_stopped` and `wire_failure` branches; the test-report AC7 row and its C-003 disposition
- **Quote:** "the repaired wire keeps them on every stop path"
- **Failure mode:** negative-path
- **Why it matters:**
  - No test feeds `publish.receipts` an event sequence, and no wire test makes a request fail.
  - The 4 published stopped requests went through the relabel heuristic, not the new path.
  - `publish.py`'s `response_cancelled` branch would overwrite a `stopped` outcome.
- **Suggested response:** add-test. Run `publish.receipts` on synthetic stop sequences, make the wire fail mid-stream, and extract the `request_stopped` emission into a seam.

### C-002: The field-completeness check cannot fail, and stopped requests still lose their resource extrema
- **Where:** `test_every_request_names_its_missing_fields`; `publish.py`; `run.py` `run_session` (`close_extrema()` is skipped when `observe()` raises)
- **Quote:** `assert set(absent) <= set(request["missing"])`, against a publisher that builds `missing` from the same 14-field tuple.
- **Failure mode:** weak-assertion
- **Why it matters:** The check is true by construction. The lab-owned resource extrema are lost on a guard stop, yet L1 requires them.
- **Suggested response:** tighten-assertion. Assert real presence on completed post-calibration requests, and record the extrema on the stop path.

### C-003: The V2 disposition claims behavioral reds that the unit results contradict
- **Where:** `test-report.md` C-008 disposition and V2 row; `unit-tests.md` rows and the V2 footnote
- **Quote:** "Behavioral regressions were added for the observing waits and the per-session erase (red on base)", against "their reds on older bases are missing attributes, not defects."
- **Failure mode:** evidence-drift
- **Why it matters:** The observing-waits V2 row is missing. The erase red is a missing schema field. The erase test never touches `run_session`'s decision.
- **Suggested response:** tighten-assertion. Restate both as API or schema reds, or route the erase decision through a seam and test that.

### C-004: The T1/T3 coverage gap remains: the wire's probe timeout is untested, and the retained list was changed outside the locked plan
- **Where:** `run.py` `probe_timeout`; build-plan "Constants classification"; the README retained list; `verify_long.score` (60 s), `prepare.py` (600 s), `telemetry.py` (`nvidia-smi` 2 s)
- **Quote:** "Only the constants on the 'retained' list **SHALL** remain fixed."
- **Failure mode:** EARS-coverage
- **Why it matters:** `probe_timeout` re-implements a stall window inline and is untested. The retained-list additions were made outside the plan, and other fixed seconds appear on no list.
- **Suggested response:** add-test (derive the probe timeout through `session_windows`) and record the retained-list additions as a plan deviation with reasons.

### C-005: L2's "being stopped" branch is never exercised; attempt-stopped sessions are neither scored nor recorded
- **Where:** receipts for attempts 07, 11 and 12 (`"sessions": []`); `run.py`; build-plan L2
- **Quote:** "**WHEN** a session ends by completing, failing or being stopped, **THEN** the hidden verifier **SHALL** score …"
- **Failure mode:** negative-path
- **Why it matters:** Attempt-level stops have no score and no session record, though O1 now charges their cost.
- **Suggested response:** defer-with-rationale, or score the fixture through a seam in the `finally` block.

### C-006: New tests still use a sub-2 s wall-clock bound and sleep-based synchronization
- **Where:** `test_every_supervisor_wait_keeps_observing`; `test_receipt_fields_complete_or_named_missing`
- **Quote:** `wait_while(lambda: True, 0.05, …)`; `backend.chunk_delay = 0.3  # long enough for the /slots poll to see the slot`
- **Failure mode:** flake-risk
- **Why it matters:** The 0.05 s timeout can expire before the first observe. The slot attribution depends on a poll landing in a timing window.
- **Suggested response:** tighten-assertion. Use a bound of at least 2 s with an event-driven condition, and gate the stream on a served `/slots` poll.

### C-007: Completion records and the O1 figures disagree, and the corrected figures cannot be recomputed from the receipts
- **Where:** `completed-tasks.md` entries T-214, T-216 and T-221; the R1 rows; `publish.py` (request timestamps stripped)
- **Quote:** T-214 says "112 passed … all 11 regressions". The policy's R1 row reads "**345 s** … | 346 s".
- **Failure mode:** evidence-drift
- **Why it matters:** The completion log holds superseded results, R1 is rounded two ways, and the machine-time inputs are not published.
- **Suggested response:** tighten-assertion. Annotate the completion entries, fix the rounding, and publish the machine-time inputs.

## Confidence
block
