# Test Critique — Sprint 3

Round 1, an independent read-only critic run at head `cbfb0c3bf5`. Each
concern is addressed in the round-1 response commits. The dispositions are
in the [test report](test-report.md), and the re-review is in
[critique-02](critique-02.md).

## Concerns

### C-001: H2 backstop clause is asserted by a tautology and never exercised
- **Where:** `tests/hermes_cli/test_local_runtime_throughput.py` `test_stall_and_backstop_semantics`; `unit-tests.md` H2 row; build-plan T-215 H2; `evals/local_qualification/run.py` inline backstop checks; `INT-0007` AC7
- **Quote:** "assert now >= backstop  # only the backstop can end a progressing step". This follows `while now < backstop:` and is true by construction.
- **Failure mode:** weak-assertion
- **Why it matters:** H2's third SHALL and AC7's "A backstop stop is a recorded failure" have no executed evidence. Enforcement is inline in `run_session` and in the load loop, which no test reaches, and no live run hit a backstop.
- **Suggested response:** add-test. Extract the request and load backstop decisions into a pure seam, then assert that each fires at the backstop and is recorded as a failure.

### C-002: T1, T2 and T3 have no executed tests, and a new fixed-seconds constant breaks T3
- **Where:** test-plan `test_stop_predicates_fire_at_boundary` (T2) and `test_lab_rules_come_from_throughput_model` (T1, T3); `unit-tests.md`; `evals/local_qualification/policy.py`; `evals/local_qualification/telemetry.py`
- **Quote:** No test references `telemetry_stale`, `supervisor_lagged`, `launch_allowed`, `request_allowed`, `budget_exceeded` or `load_progressed`. telemetry.py has `deadline = time.monotonic() + 0.5`.
- **Failure mode:** EARS-coverage
- **Why it matters:** The T2 boundaries are unproved, and T1/T3 have no behavioral test. The attempt-07 repair added a fixed 0.5 s deadline that is not on the retained list.
- **Suggested response:** add-test (predicate boundaries and a lab-level rate-doubling check). Derive the 0.5 s from the telemetry period, or list it as retained.

### C-003: Stopped requests drop predicted and actual time, and the receipt check skips them
- **Where:** `test_local_qualification_receipts.py` `test_request_receipts_name_every_missing_field`; receipts for attempts 05, 07, 11 and 12; `test-report.md` AC7 row; `INT-0007` AC7; build-plan M3 and L1
- **Quote:** The test skips every request whose outcome is not `response_end` and checks only 3 fields. The report claims "All 165 requests record predicted and actual time", but 4 stopped requests list `seconds` and both predictions as missing.
- **Failure mode:** negative-path
- **Why it matters:** AC7 needs predicted and actual time on every request, and the guard-stopped requests are exactly the failure path. "165" counts only the requests that have a prediction, so the claim is circular.
- **Suggested response:** tighten-assertion. Check every L1/M3 field on every request, keep the predictions and elapsed time on stopped requests, and correct the claim.

### C-004: The capture backend gives `id_slot` that the real backend never sends, and streams no tool call
- **Where:** `test_local_qualification_wire.py` `CaptureBackend` and `test_receipt_fields_complete_or_named_missing`; published receipts; `test-report.md` INT-0004 AC4 row
- **Quote:** The test asserts `end["id_slot"] == 0`. Live, `id_slot` is missing on 174 of 174 requests.
- **Failure mode:** stub-leak
- **Why it matters:** The test double encodes what the wire hopes for, not how b10964 behaves. No tool call is streamed, so tool-call validity, truncation retries and lag are never asserted. AC4's slot correlation rests on "missing is explicit" without saying so.
- **Suggested response:** tighten-assertion. Make the double match b10964, assert the named-missing and validity fields, and correlate the slot from `/slots` or restate AC4.

### C-005: The "failures in the denominators" rule is stated but not applied
- **Where:** `docs/lineage/local-operating-policy.md`; ledger attempt 10; build-plan O1; `INT-0007` AC2
- **Quote:** "Failures and stops count in the denominators", next to "354 s … attempt 13 (attempts 10–12 stopped…)".
- **Failure mode:** intent-coverage
- **Why it matters:** 354 s and 182 s exclude the stopped attempts. The echo-neutral conclusion rests on those figures.
- **Suggested response:** tighten-assertion. Recompute with the stops included, or state an explicit exclusion rule and fix the wording.

### C-006: V3 "every attempt" is not met, and the test cannot detect a missing attempt
- **Where:** `qualification/` (11 receipts); ledger attempts 01 and 03; `RECEIPTS = sorted(QUALIFICATION.glob(...))`; build-plan V3
- **Quote:** "every attempt **SHALL** resolve to a digest-valid manifest with its arm."
- **Failure mode:** evidence-drift
- **Why it matters:** Attempts 01 and 03 have no receipt, and the test enumerates whatever files happen to exist.
- **Suggested response:** add-test (check attempt indices 1..N against the budget counter) and publish attempts 01 and 03.

### C-007: T5 bring-up is unrecorded and its stall is a bare timer; the C1 pin check is unreported
- **Where:** `e2e-tests.md`; `evals/local_qualification/bringup.py`; `integration-tests.md` cancel row; build-plan C1
- **Quote:** bringup.py runs `while not clock.stalled(time.monotonic())`, with `stalled_after >= window` in its pass condition.
- **Failure mode:** evidence-drift
- **Why it matters:** The clock never observes the child, so any child is "stalled". T5 has no recorded result. The cancel test is mislabelled T5. C1's explicit-pin check appears nowhere in the results.
- **Suggested response:** add-test (a chatty child must survive), record T5, relabel the cancel test, and record the pin evidence.

### C-008: V2 regressions: four are red only because the API was missing, and two repairs have no regression
- **Where:** `unit-tests.md` V2 table; `test-report.md` V2 row; ledger provenance table
- **Quote:** "No `KernelCache` (the repair is the class)"; "No `publish`".
- **Failure mode:** weak-assertion
- **Why it matters:** An API-only red does not show the test catches the defect. The observing waits and the per-session erase have no regressions.
- **Suggested response:** add-test (observing waits, per-session erase) and show behavioral reds where possible.

### C-009: The C2 fail-closed path is never executed
- **Where:** build-plan C2; test-plan `live_calibration_record`; `run.py` `write_calibration`; `prepare.py`
- **Quote:** `raise RuntimeError(f"calibration incomplete (fail closed): missing {missing}")`
- **Failure mode:** negative-path
- **Why it matters:** C2's error-path SHALL has no evidence, live or formal.
- **Suggested response:** add-test. Assert the raise and the `calibration_failed` event, and that prepare refuses a non-calibration plan with no record.

### C-010: Sub-2 s wall-clock bounds and sleep-based synchronization in the wire and Windows tests
- **Where:** the wire cancel and concurrency tests; the slots test; the Windows publish test
- **Quote:** "assert elapsed < 0.5"; "time.sleep(0.5)  # the first request is mid-stream"; "threading.Timer(0.2, held.close)"
- **Failure mode:** flake-risk
- **Why it matters:** The repo rule is wall-clock bounds of at least 2 s and event-based synchronization.
- **Suggested response:** tighten-assertion. Use events, bounds of at least 2 s, and an injected retry deadline.

### C-011: V1 runner-log fingerprint and intent evidence links are missing
- **Where:** build-plan V1; test-plan `formal_order_review`; result headers; the INT-0007 and INT-0004 headers
- **Quote:** V1: "the runner log fingerprint **SHALL** be recorded." INT-0007 still reads "**Test evidence:** none".
- **Failure mode:** evidence-drift
- **Why it matters:** The pass counts and the ordering claim cannot be tied to a runner log, and the intents link no Sprint 3 evidence.
- **Suggested response:** add-test. Record the runner-log digests and first-run times, add `formal_order_review`, and link the evidence from both intents.

### C-012: The M1, M4 and L4 result claims go beyond what the tests assert
- **Where:** `unit-tests.md` M1 row; the lab M1 test and L4 fixture; `test_local_qualification_receipts.py`; build-plan M1 and M4
- **Quote:** "reproduces the frozen R2 argv exactly". The test checks six values on a synthetic profile.
- **Failure mode:** weak-assertion
- **Why it matters:** There is no comparison with the published flags, no `--slot-save-path` check, no identity-change check, no M4 prefix or admission check, and no allowlisted L4 case.
- **Suggested response:** tighten-assertion.

### C-013: The AC1 shortfall is deferred to an unnamed "Sprint 4 candidate"
- **Where:** `test-report.md` "Concerns and limits"; `INT-0007` AC1; `docs/work/tasks.md`
- **Quote:** "Lengthening it is a Sprint 4 candidate."
- **Failure mode:** intent-coverage
- **Why it matters:** R0 and R2 made 18 requests, and no backlog task owns the fix.
- **Suggested response:** defer-with-rationale, with a named backlog task linked from the report.

## Confidence
block
