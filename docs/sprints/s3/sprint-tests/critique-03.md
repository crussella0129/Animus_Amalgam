# Test Critique — Sprint 3

Round 3, an independent read-only critic run at head `4a039353ac`, after
the round-2 response. Each concern is addressed in the round-3 response
commits. The dispositions are in the [test report](test-report.md), and the
re-review is in [critique](critique.md).

## Concerns

### C-001: Attempt 02's stall-stopped request is published with the wrong stop cause, and the cause test can't detect it
- **Where:** the relabel loop in `publish.py` `receipts()`; `qualification/attempt-02-calibration.json` request 1; `test_stopped_requests_keep_their_cause_and_elapsed_time`
- **Quote:** `"stop_reason": "stopped: RuntimeError: supervisor scheduler lag exceeded two telemetry periods"`, while the same receipt's session 1 records `"stop": "stall in prefill (window 47.0s)"`.
- **Failure mode:** weak-assertion
- **Why it matters:** The sprint's only stall-stopped request carries an unrelated later cause. The heuristic relabels any `wire_failure` in a stopped attempt, and the test checks only that a cause is present.
- **Suggested response:** tighten-assertion. Relabel only a request in flight at the attempt stop, otherwise keep its session's recorded stop, and assert that the cause matches.

### C-002: Cut-short sessions are never L4-screened, yet round 2 began counting their items in O1 denominators, and the repaired stop path records them as clean
- **Where:** `run.stopped_session` (verifies with `result=None`); the at-publish scoring in `publish.receipts`; the ledger's round-2 O1 table; the policy's R2 row; build-plan L4
- **Quote:** L4: "A flagged session is excluded from selection and denominators". R2 went from "865 s" to "384.3 s".
- **Failure mode:** EARS-coverage
- **Why it matters:** A cut-short session gets a clean contamination verdict that nobody examined, and its items entered the O1 denominator without screening.
- **Suggested response:** tighten-assertion. Screen cut-short sessions from the conversation the wire last forwarded, test a flagged one, and report O1 under each reading.

### C-003: The stop-path seams are tested on hand-built inputs; their wiring in `main`'s `finally` is not exercised and not guarded
- **Where:** `test_stopped_request_keeps_its_cause_timing_and_predictions`; `run.main`'s `finally`
- **Quote:** `active = {"request_id": 7, "started": 100.0, ...}`
- **Failure mode:** stub-leak
- **Why it matters:** A key drift, or an exception from scoring inside `finally`, would skip the budget charge and the outcome record. Stop-path scoring also runs without the `VERIFY_S` bound.
- **Suggested response:** add-test. Feed a real `Wire.active` into `stopped_request`, and guard stop-path scoring so the ledger and outcome are always written.

### C-004: The L1 presence check still covers only part of L1
- **Where:** `test_completed_calibrated_requests_carry_timing_predictions_and_resources`; build-plan L1
- **Quote:** `for field in ("seconds", "predicted_initial_seconds", "predicted_rearmed_seconds", "resources"):`
- **Failure mode:** weak-assertion
- **Why it matters:** The token and timing fields L1 lists are still covered only by the named-missing test, which is true by construction.
- **Suggested response:** tighten-assertion. Assert every L1 field on completed calibrated requests.

### C-005: The round-2 records misstate the published evidence and the plan
- **Where:** the test-report AC7 row; the ledger's round-2 section; the unit-tests V2 table; the README and test-report "Plan deviation"; `test_uncalibrated_windows_come_from_the_measured_load`
- **Quote:** "(and, in attempts 11 and 12, their extrema)"; "| 12 | R2 | 10 | **2** |"; "**Schema:** … (`KeyError: 'erase_slot'`)"; "The locked plan retained only the cadences and the 2 s grace and 5 s cleanup"
- **Failure mode:** evidence-drift
- **Why it matters:**
  - Attempts 05 and 07 also lack extrema on their stopped requests.
  - The request counts are 11 (attempt 12) and 3 (attempt 05).
  - The committed erase test is an API red at its base.
  - The plan retained the `git` timeouts and the 1 s lock handoff, while the 0.2 s listener probe is on no list.
  - The uncalibrated `probe_window` branches are unasserted.
- **Suggested response:** tighten-assertion. Correct the records, list the 0.2 s probe, and assert `probe` in the uncalibrated test.

### C-006: The capture backend releases its final chunk before the wire has necessarily seen the slot
- **Where:** `CaptureBackend.do_GET`; `test_receipt_fields_complete_or_named_missing`
- **Quote:** `if owner.request_active: owner.polled_during_request.set()`
- **Failure mode:** flake-risk
- **Why it matters:** The gate is "a poll was received", not "the wire recorded `slot_seen`", so a loaded runner can invert the ordering.
- **Suggested response:** tighten-assertion. Release the final chunk only after the test observes `slot_seen`.

## Confidence
block
