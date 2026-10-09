Finalized - DO NOT EDIT

# Sprint 3 Test Plan

## Execution order: operate, repair, replay, then formal verification

This follows the owner's reverse-E2E rule (INT-0004 AC7, lesson L-18). Before
live operation, the only checks are:

- compile, format and lint checks;
- `bringup_stop_control_check` (T5), which loads no model.

Live operation of real Hermes on the real 27B follows. Formal unit and
integration suites run only after the operational-confidence record is
written to the ledger; V1 requires the record and its anchoring receipt to
predate the first formal run.

## Intent Traceability

| Intent | Acceptance criterion | Build task / EARS clause | Verification |
|--------|----------------------|--------------------------|--------------|
| [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md) | AC7: host-derived stall and backstops, no fixed seconds (module) | T-215 / H1, H2, H3 | `test_rates_use_only_qualifying_samples`, `test_stall_and_backstop_semantics`, `test_windows_scale_inversely_with_host_rate` |
| INT-0007 | AC7 (lab route): applied rules, predictions recorded, calibration, accuracy | T-221 / T1, T3; T-222 / C2; T-216 / O5 | `test_lab_rules_come_from_throughput_model`, `live_calibration_record`, `live_deadline_accuracy` |
| [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md) | AC1: manifest/launch configuration, rendered prefix, host condition, owner time-model choice | T-211 / M1, M4; T-214 / V3 | `test_arm_manifest_drives_server_flags`, `live_arm_replay`, `test_published_receipts_resolve_and_are_private` |
| INT-0004 | AC2: stop gates, main cancellation, one-request ownership | T-221 / T2, T4, T5; T-222 / C1, C4 | `test_stop_predicates_fire_at_boundary`, `test_wire_streams_and_reassembles`, `bringup_stop_control_check`, `live_arm_replay`, `live_main_cancel` |
| INT-0004 | AC4: correlated receipts with named missing fields | T-211 / M3; T-210 / L1 | `test_receipt_fields_complete_or_named_missing`, `live_full_run_R0` |
| INT-0004 | Fresh state, clean environment, probe off | T-211 / M2 | `test_fresh_session_state_and_clean_env` |
| INT-0007 | AC1: long task, ≥ 20 requests, per-turn receipts | T-210 / L1, L2, L3, L4 | `task_precheck`, `test_verify_scores_fixture_state`, `test_contamination_flag`, `live_full_run_R0` |
| INT-0007 | AC2: off vs bounded at the best-screened sampling, per verified item (unbounded is T-218) | T-212 / S1, S2, S3; T-216 / O1 | `live_sampling_screen`, `test_screen_ranking_rule`, `live_full_run_R0`, `live_full_run_R1` |
| INT-0007 | AC3: cross-session identity and reuse; thinking-on append-only; repair or density | T-222 / C3; T-216 / O2, O3 | `live_cross_session_prefix`, `live_full_run_R1`, `live_full_run_R2`, `live_checkpoint_density_R3` (conditional) |
| INT-0007 | AC6 (partial): policy ranked by verified throughput | T-213 / P1, P2 | `policy_evidence_review`, `live_profile_untouched` |
| INT-0004, INT-0007 | Repair provenance, formal order, regressions | T-216 / O4; T-214 / V1, V2 | `operational_repair_replay`, `formal_order_review`, `regression_red_on_base` |
| INT-0004, INT-0007 | Arm forwarding (cap, ceiling, thinking, budget, sampling, echo) | T-211 / M1 | `test_wire_applies_arm_bounds`, `test_fresh_session_state_and_clean_env` |

## End-to-End Tests (live, first)

- **Status:** possible, conditional on per-device admission. The real
  Hermes CLI runs against the installed b10964 backend and the owner's 27B,
  with a fresh home and fixture outside the repository for every session. A
  refusal is recorded and the owner is asked to free memory. Mocks never
  replace operation.
- **Intents:** INT-0004, INT-0007.
- **`bringup_stop_control_check`** (T5, pre-live):
  - Explicit synthetic rates.
  - A child that emits no events under the owned job is stopped by the
    stall rule.
  - The tree is cleaned up within 5 s.
  - An unrelated sentinel survives.
  - No model is loaded.
- **`live_arm_replay`** (C1, M1, M4):
  - The untracked-file refusal consumes zero launches.
  - After it is removed, launch succeeds with `/props` context and argv
    matching the arm.
  - The explicit-pin check admits the pin.
  - The receipt carries the rendered prefix, the host condition, the time
    parameters and Hermes's effective timeouts.
- **`live_calibration_record`** (C2): the record holds `P`, `D`, `O`,
  `T_load`, `T_cli`, the checkpoint size and the frozen count.
  - `D` comes from a checked decode sample of at least 16 tokens.
  - A missing field fails closed.
  - The sprint budget and the owner's time-model decision are in the ledger
    and manifest before the screen starts.
- **`live_cross_session_prefix`** (C3): the rendered system-prompt hashes are
  byte-identical, and reuse is recorded as pass or not-met, with the cause.
- **`live_main_cancel`** (C4): cancel at the first decoded token. Pass
  requires the slot idle and owned cleanup within 5 s.
- **`live_sampling_screen`** (S1–S3): six configurations, each with a fresh
  home, fixture and slot. The receipt records verified items, machine time
  and decoded tokens, and the selection follows S2, labeled as screening.
- **`live_full_run_R0`, `live_full_run_R1`, `live_full_run_R2`** (L1, L2,
  L4, O1, O2):
  - Every L1 field is present on every request.
  - The verifier scores 4 items.
  - The request count is recorded; below 20 means AC1 coverage not met.
  - Contamination handling follows L4.
  - Per-turn uncached tokens decide O2.
- **`live_checkpoint_density_R3`** (O3): runs only if R1's median uncached
  tokens per continued turn exceed 2,000 and the frozen count is at least 2.
  Otherwise the ledger records which condition was not met.
- **`live_deadline_accuracy`** (O5): across every request, the ledger
  reports predicted (initial and rearmed) versus actual seconds and their
  error distribution. Every stall, backstop or resource stop is listed with
  its cause, and a backstop stop is a recorded AC7 failure.
- **`operational_repair_replay`** (O4): each failure in T-222, T-212 or
  T-216 is linked to its diagnosis, repair revision and replay.
- **`live_profile_untouched`** (P2): the live fingerprints at close equal the
  plan baseline.

Operational confidence requires all of the following:

- the bring-up check, replay, calibration and main-cancel pass;
- the cross-session result is recorded;
- the screen is complete;
- R0, R1 and R2 have run through with verifier scores (AC3 needs both R1 and
  R2);
- every repair is replayed;
- no unresolved blocking defect remains;
- the sprint budget is intact.

The confidence record is written before any formal run.

## Unit Tests (after operational confidence)

### T-215 throughput module
- **Intent:** [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- `test_rates_use_only_qualifying_samples` (H1):
  - Samples below the minimum batch or token count leave `P` and `D`
    unchanged; a 1-token prefill leaves `P` unchanged.
  - The floors stay fixed from calibration.
  - The prediction is non-decreasing in uncached and output tokens.
- `test_stall_and_backstop_semantics` (H2):
  - A stream with events inside the window runs to the backstop without
    being stopped.
  - A silent stream past the window is stopped by the stall rule.
  - A progressing stream that reaches the backstop is stopped and reported
    as a failure.
  - The window from send to the first event is `k × max(O_cal, n_batch/P_min)`;
    after that, it comes from the floor intervals.
  - No window is shorter than 4 observation periods, even on a fast host.
  - The load backstop is `m × T_load / f`.
  - Gaps slower than the floors, or a large observed p99, **never** widen
    the stall or gap windows.
  - During calibration, only the stall rule (window `T_load`) and the
    resource stops apply.
- `test_windows_scale_inversely_with_host_rate` (H3): rates scaled by `s`
  scale every token-work window, backstop and budget by `1/s`, apart from
  the measured overhead terms, checked by computation. The retained
  cadence-based guards (stale, lag, load stall) are excluded.

### T-211 / T-221 / T-210 lab
- **Intents:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md), [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- `test_arm_manifest_drives_server_flags` (M1): an arm → the exact argv
  (context, checkpoints and min-step, verbosity, spec none,
  `--slot-save-path` present, `--predict` absent). Changing a field changes
  the manifest identity.
- `test_fresh_session_state_and_clean_env` (M2, M1):
  - Two sessions get distinct homes and fixtures outside the repository.
  - The config has `environment_probe: false` and the arm's
    `reasoning_echo`.
  - The CLI and tool environment has no repository path, does have
    `SYSTEMDRIVE`, and puts the task interpreter first on `PATH`.
  - Hermes's stream-stale and request timeouts are at or above the lab's
    request backstop.
  - Nothing from the first session is visible to the second.
- `test_stop_predicates_fire_at_boundary` (T2): stale, lag, launch-count,
  request-count and sprint-budget predicates each fire exactly at their
  boundary.
- `test_lab_rules_come_from_throughput_model` (T1, T3): each replaced
  decision is exercised on synthetic streams and follows T-215's output.
  Doubling the calibrated rates halves the windows, and only the listed
  retained constants stay fixed. The check is behavioral.
- `test_verify_scores_fixture_state` (L2): the 4 items, fixed or not → the
  per-item score. The transcript is ignored.
- `test_contamination_flag` (L4):
  - Absolute paths, `..` traversal and environment-variable paths that
    resolve outside the fixture are flagged.
  - Fixture-local paths, the allowlisted task venv, the system binaries and
    the terminal's resolved `bash` and its bin directories are not.
  - A session that exceeds its request limit is recorded as an arm failure
    (`test_session_request_limit`).
  - A flagged session is excluded and re-run once.
- `test_session_request_limit` (per-session limit): the wire refuses a
  session's request beyond 3 × its planned count, and the receipt records
  an arm failure that counts in the denominators.
- `test_screen_ranking_rule` (S2): the ranking follows the declared order,
  including the all-zero inconclusive case. The mid probe is never
  selected, even when it scores best.
- Regressions for defects repaired in T-222, T-212 or T-216, each proven red
  on the pre-repair revision (V2). They are named when reproduced; no
  speculative tests.

## Integration Tests (after operational confidence)

### Lab wire and receipts
- **Intents:** [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md), [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md)
- `test_wire_applies_arm_bounds` (M1): the real `Wire` against a loopback
  capture backend. It forwards the arm's cap, input ceiling (overflow →
  refusal), `enable_thinking`, `reasoning_budget_tokens` and full sampler
  set exactly once, and records the original body.
- `test_wire_streams_and_reassembles` (T4):
  - Streaming and non-streaming client requests both go upstream streaming,
    with `return_progress: true`.
  - Progress chunks never reach either client, and the non-streaming client
    receives one reassembled response.
  - A backend that withholds SSE deltas while its `/slots` `n_decoded`
    rises is not stalled.
- `test_receipt_fields_complete_or_named_missing` (M3, L1): the capture
  backend streams progress, reasoning and content deltas, a tool call, and a
  final `timings` chunk with `id_slot`.
  - Every L1 field is present.
  - M3 fields are present or named missing.
  - Reasoning and visible tokens are split.
- `test_published_receipts_resolve_and_are_private` (V3, M4):
  - Every published Sprint 3 attempt resolves to a digest-valid manifest
    with its arm.
  - Each manifest carries the owner's time-model decision, the calibration
    record, Hermes's effective timeouts (including the terminal command
    timeout) and the L4 allowlist.
  - No user path, credential or 48-hex token appears in any published
    JSON.

## Evidence and scope checks

- `task_precheck` (L3): shows three things:
  - the largest reference edit fits the smallest cap;
  - the reference path has at least 20 requests;
  - the peak rendered prompt plus worst-case echoed reasoning fits the
    smallest sprint context's input ceiling.
- `formal_order_review` (V1): the confidence record and anchoring receipt
  predate the first formal run, and the runner log fingerprint is recorded.
- `regression_red_on_base` (V2): each regression is shown failing on the
  pre-repair revision.
- `policy_evidence_review` (P1): the varied settings are ranked by machine
  time per verified item and linked to receipts. Fixed choices carry their
  rationale. Sprint 4 items and single-run status are marked. If no arm
  verified anything, the negative result and its limiting resource are
  documented instead.
- **Affected-suite regression:** a base-vs-head failing-ID diff for the
  affected `tests/hermes_cli/test_local_*.py` and `tests/agent/` files, with
  the same settings on both trees. The Windows baseline has 120 inherited
  failures.

Tests may strengthen, never weaken, an acceptance criterion. Green suites are
not repeated without a new reason.
