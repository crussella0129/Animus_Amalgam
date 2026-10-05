# Test Critique — Sprint 3

Round 4, an independent read-only critic run at head `3396f33a8e`, after
the round-3 response. Each concern is addressed in the round-4 response
commits. The dispositions are in the [test report](test-report.md), and the
re-review is in [critique](critique.md).

## Concerns

### C-001: In the repaired lab, a request stopped by a stall or backstop is published as a cancel with no cause; the round-3 cause fix only covers the old `wire_failure` shape
- **Where:**
  - `run.run_session`, after `stop` is set: `interrupt_file.touch(); wire.cancel_active()`;
  - the except branch of `wire._handle`;
  - the relabel loop in `publish.receipts`;
  - the tests `test_an_aborted_request_takes_its_own_sessions_stop_as_its_cause` and `test_stopped_requests_keep_their_own_cause_and_elapsed_time`;
  - the test report's C-001 disposition;
  - build-plan H2 and INT-0007 AC7.
- **Quote:** `if r.get("outcome") == "wire_failure" and "stop_reason" not in r:` (publish.py). The integration row says the cancel "is recorded as `response_cancelled`, not as a wire failure".
- **Failure mode:** negative-path
- **Why it matters:**
  - With the repaired wire, a session-level stall or backstop calls `cancel_active()`, so the wire records `response_cancelled`.
  - `publish` then labels the request `response_cancelled` with no `stop_reason`, the same as the deliberate C4 cancel.
  - The round-3 tests feed only `wire_failure` sequences, so the mapping from `run_session` to the receipt for a stall or backstop is never exercised.
- **Suggested response:** add-test. Record `request_stopped` with the session's stop before `cancel_active()`, or map the cancel. Test both a stall-stopped request and a main-cancel.

### C-002: AC4/M3 "missing metrics are explicit" fails for meaningful first token on every stopped request
- **Where:**
  - `publish.REQUEST_FIELDS` and `run.stopped_request`;
  - the published stopped requests: request 1 (attempt 02), 10 (05), 91 (07), 145 (11) and 156 (12);
  - `test_every_request_names_its_missing_fields`;
  - the test report's INT-0004 row.
- **Quote:** M3: "meaningful first token … Any field the backend does not provide **SHALL** be named missing."
- **Failure mode:** weak-assertion
- **Why it matters:** In all 5 published stopped requests, `meaningful_first_token_seconds` is absent and not named missing. The per-request `tool_calls` count is absent in the same way. The four cut-short sessions carry no tool-call validity and do not name it missing.
- **Suggested response:** tighten-assertion. Carry the first token in `stopped_request`, name the fields missing, republish, and assert presence-or-named across the M3 fields.

### C-003: A cut-short session's L4 screen can still be empty and pass as clean, and the published evidence does not show what was screened
- **Where:**
  - `run.run_session`: `wire.end_session()`, then the verification wait, then `interrupt_file_holder.pop(...)`;
  - `run.stopped_session` and `publish._screen`;
  - `test_attempt_stopped_long_sessions_are_scored`.
- **Quote:** `conversation = (session or {}).get("last_messages") or []`
- **Failure mode:** weak-assertion
- **Why it matters:**
  - A guard can stop the attempt during a session's own verification wait. By then `wire.end_session()` has already cleared `wire.session`.
  - The stop path then screens an empty conversation and records `requests: None`, giving the session a clean verdict.
  - The receipts carry only `contamination: []`, and their test passes the same way on an empty screen.
- **Suggested response:** tighten-assertion. Keep the conversation past `end_session`, publish the screened message and tool-call counts, and assert that they are non-zero for a session with requests.

### C-004: The calibration-attempt gap window differs from the locked plan, with no recorded deviation and no assertion
- **Where:** the build-plan time model, "Gap between requests"; the uncalibrated branch of `run.session_windows`; `test_uncalibrated_windows_come_from_the_measured_load`
- **Quote:** the plan says "During calibration it is `k ×` that session's measured `T_cli`." The code has `"gap": uncalibrated_stall_window(params.stall_multiple * t_load, …)`.
- **Failure mode:** EARS-coverage
- **Why it matters:** This is a T1 window, about 908 s live instead of about 61 s. No deviation is recorded, and the test does not assert the gap.
- **Suggested response:** tighten-assertion. Record the deviation with its reason and assert the uncalibrated gap, or derive it from T_cli as planned.

### C-005: P1 and P2 have no named, executed check result
- **Where:** test-plan `policy_evidence_review` (P1) and `live_profile_untouched` (P2); the e2e-tests table; the test-report Summary; `local-operating-policy.md` "Recommended defaults"
- **Quote:** the report says "`config.yaml` `a48b4add…` and `presets.ini` `bb35c72d…` match the Sprint 3 baseline." It gives no date or head.
- **Failure mode:** EARS-coverage
- **Why it matters:** P2 applies when the sprint closes, but the only dated record is T-213's. P1's review is never recorded. The policy recommends `reasoning_echo: true` for thinking-on use, yet it ranks R1 (echo off) above R2.
- **Suggested response:** add-test. Record both checks with their time and head. State the echo-on recommendation as outside the ranking, or align it with the ranking.

## Confidence
block
