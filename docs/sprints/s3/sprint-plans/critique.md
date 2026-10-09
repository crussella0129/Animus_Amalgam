# Plan Critique — Sprint 3

Round 4 (final), an independent read-only re-review. Earlier rounds:

- [01](critique-01.md): block;
- [02](critique-02.md): block;
- [03](critique-03.md): block on two text fixes only.

All round-3 concerns were verified resolved. The caveats below were then
addressed by tightening the plans, without changing any outcome, intent or
acceptance criterion.

## Concerns

### C-001: The planned calibration requests could not produce the decode rate `D`
- **Where:** time model Rates; Planned attempts; T-222 C2 and C4.
- **Failure mode:** hidden-dep
- **Response:** a checked decode-sample request (thinking off, at least 16 tokens) was added to calibration. C2 now requires a full-batch prefill sample and a created checkpoint, and fails closed with a stop-and-report if any field is missing.

### C-002: Overhead-scaled windows missed prompt-proportional pre-event work, and no window had a floor at the polling cadence
- **Failure mode:** missing-risk
- **Response:**
  - The pre-first-event window and the probe timeout use `k × max(O_cal, n_batch/P_min)`.
  - No window is shorter than 4 × the `/slots` observation period, which is now on the retained list.
  - Test cases were added.

### C-003: The L4 allowlist omitted the terminal's bash tools, and the allowlisted interpreter lived in the live install
- **Failure mode:** hidden-dep
- **Response:** the task interpreter is now a disposable standard-library venv outside the repo, built from the managed runtime's base with no download. The allowlist adds the resolved `bash` and its `usr/bin` and `mingw64/bin`, recorded in the manifest, with test cases.

### C-004: No per-session request limit; `max_turns` applied per user turn
- **Failure mode:** missing-risk
- **Response:** the wire enforces a per-session limit of 3 × the planned requests. An over-limit session is a recorded arm failure that counts in the denominators. `max_turns` is 30 per user turn. Test added.

### C-005: The load backstop did not use the floor rate
- **Failure mode:** intent-drift
- **Response:** the load backstop is now `m × T_load / f`.

### C-006: The owner's time-model decision and the calibration record had no named check
- **Failure mode:** plan-test-mismatch
- **Response:** both were added to `live_calibration_record` and `test_published_receipts_resolve_and_are_private`.

### C-007: The backlog T-210 and T-211 entries still carried their scope from before the split
- **Failure mode:** intent-drift
- **Response:** both entries were rewritten to their Sprint 3 scope, with pointers to T-217 to T-221 and T-222.

### C-008: Smaller gaps
- **Failure mode:** EARS-vague
- **Response:**
  - C4 now says "the lab SHALL cancel".
  - Floors are fixed from calibration for the whole sprint.
  - The request backstop uses `O_cal`.
  - P2 is unconditional.
  - `publish.py` is marked new.
  - A busy tool gap is bounded by Hermes's terminal timeout, recorded in the manifest and moving with T-219.

## Confidence
proceed-with-caveats
