# Plan Critique — Sprint 3

Round 3, an independent read-only re-review of the second rewrite. The
verdict was `block`, resting only on C-001 and C-002 (narrow text fixes);
C-003 to C-008 were caveats. All were addressed, and [critique.md](critique.md)
holds the re-review.

## Concerns

### C-001: Stall and gap windows could still widen within an attempt through the p99 term
- **Failure mode:** intent-drift
- **Response:** the p99 term was dropped from enforcement and is recorded only as a degradation metric. The gap window is `k × T_cli_cal`. A test was added so that slower-than-floor gaps never widen a window.

### C-002: The screen could select the unsourced mid probe, which AC2 does not allow
- **Failure mode:** intent-drift
- **Response:** the mid probe is reported only and not selectable. S2 ranks AC2-admissible candidates only, and the test asserts the probe is never selected.

### C-003: Pre-rate window ambiguity, which could cause false stalls on the first request of each fresh session; no calibration backstop; the load stall does not scale
- **Failure mode:** EARS-vague
- **Response:** the window is `k × O_cal` only from send to the first event, and floor intervals apply after that. During calibration, the stall rule (window `T_load`) and the resource stops apply, with no request backstop. The load stall is cadence-based and excluded from H3.

### C-004: The streaming-client path and Hermes timer settings were untested
- **Failure mode:** plan-test-mismatch
- **Response:** T4 now covers streaming and non-streaming clients. M2 sets Hermes's stream-stale and request timeouts at or above the backstop, and the tests assert both.

### C-005: The stall rule assumed per-token SSE emission
- **Failure mode:** missing-risk
- **Response:** the `/slots` counters `n_prompt_tokens_processed` and `n_decoded`, confirmed in the pinned source, count as progress. A test covers withheld deltas.

### C-006: Slot erase needs a server flag; the `--predict` decision was open
- **Failure mode:** hidden-dep
- **Response:** the pinned source confirms slot actions need `--slot-save-path`, which is now in the argv. `--predict` is removed, a decision recorded in the build plan. The M1 test asserts both.

### C-007: Contamination had no allowlist, so the task interpreter would flag every session
- **Failure mode:** hidden-dep
- **Response:** the task interpreter is the managed-runtime Python outside the repo, first on `PATH`. It and the system binaries are allowlisted in the manifest, with test cases.

### C-008: Smaller gaps
- **Where:** P1 negative branch, ranking unvaried settings, the budget comparator, stale Work evidence, "dimensionless" wording.
- **Failure mode:** plan-test-mismatch
- **Response:**
  - P1 gained a negative-result branch.
  - Only varied settings are ranked; fixed ones are stated with a rationale.
  - The budget includes calibrated hashing, load and start-up, compared against attempt-scoped charged time.
  - Work evidence was updated in INT-0004 and INT-0007.
  - The wording was corrected.

## Confidence
block
