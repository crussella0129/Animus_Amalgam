# Sprint 2 Test Plan — draft for owner approval

## Intent Traceability

All tests below advance [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md).
AC3, AC5, AC6 and useful-task AC4 are deferred to T-202 under that same intent;
they are not silently dropped or represented as satisfied by a tiny smoke.

| Intent | Acceptance criterion | Build task / EARS clause | Verification |
|---|---|---|---|
| INT-0004 | AC1 | T-201 / M1 | `manifest_identity_roundtrip`, `qualification_receipt_audit` |
| INT-0004 | AC1 / AC2 | T-201 / M2 | `admission_rejects_unverifiable_candidate` |
| INT-0004 | AC2 / AC4 | T-206 / S1 | `owned_job_cancellation_windows_live` |
| INT-0004 | AC2 / AC4 | T-206 / S2 | `gate_breach_classification`, `stalled_probe_windows_live` |
| INT-0004 | AC1 / AC2 / AC4 | T-207 / D1 | `test_main_and_compression_wire_contract` |
| INT-0004 | AC1 / AC2 | T-207 / D2 | `test_manifest_mismatch_blocks_generation`, `live_auxiliary_cancel` |
| INT-0004 | AC2 / AC4 | T-208 / R1 | `live_admission_receipt` |
| INT-0004 | AC2 / AC4 | T-208 / R2 | `live_smoke` |
| INT-0004 | AC2 / AC4 | T-208 / R3 | `live_main_cancel`, `live_auxiliary_cancel` |
| INT-0004 | AC1 / AC4 | T-209 / P1 | `qualification_receipt_audit` |
| INT-0004 | deferred AC3 / AC5 / AC6 and AC4 scope | T-209 / P2 | `book_scope_review` |

## Unit Tests

### T-201 manifest and admission
- **Intent:** INT-0004; clauses M1/M2.
- `manifest_identity_roundtrip`: real small fixture files and normalized
  tokenizer/template data produce a reproducible manifest identity; modifying
  any tested artifact or resource parameter invalidates the old identity.
  Required run observations are distinguished from pre-admission unknowns.
- `admission_rejects_unverifiable_candidate`: missing required probe/identity,
  unknown placement, insufficient CPU/GPU allowance, changed digest or input
  ceiling violation fails without invoking the supplied launch callback.
  Cover an aggregate-capacity failure and a separate per-device failure.
- Use temporary files and synthetic resource values, never real memory stress.

### T-206 stop policy
- **Intent:** INT-0004; S2.
- `gate_breach_classification`: deterministic clock/sample inputs prove exact
  RAM/VRAM floors, three-sample hard-paging threshold, sample staleness,
  scheduler lag, request/launch/total budgets and first-stop-cause retention.
  Model responses cannot clear a stop decision. These are behavior contracts,
  not snapshots of constants or source text.

## Integration Tests

### T-206 real Windows process ownership
- **Intent:** INT-0004; S1/S2.
- `owned_job_cancellation_windows_live`: spawn an owned synthetic server with
  a grandchild plus an unrelated sentinel; prove normal cancellation,
  deadline and supervisor-loss paths remove only the owned tree, close its
  listener and retain the stop receipt within five seconds. Use native Windows
  execution, event synchronization and no OS impersonation.
- `stalled_probe_windows_live`: a collector and driver that never answer
  cannot block the independent deadline; an injected resource-breach sample
  triggers cleanup. No real GPU load or memory exhaustion is involved.

### T-207 real Hermes imports and local HTTP fixtures
- **Intent:** INT-0004; D1/D2.
- `test_main_and_compression_wire_contract`: run actual AIAgent/custom-provider
  and compressor/auxiliary seams against an owned local capture server with
  temporary homes A→B→A. Assert body/model/endpoint, explicit 128-token limit,
  stable bytes across equivalent requests, one physical request per attempt,
  no cross-home state and no unrelated provider/network route. Include a
  failing/stalled response and verify bounded physical attempts. A generic
  SDK request used in place of the compressor is not sufficient evidence.
- `test_manifest_mismatch_blocks_generation`: local server fixtures report
  wrong model/context/slot count, oversized rendered input or missing cap
  capability; each prevents inference. The valid fixture allows exactly the
  planned request, and the real auxiliary attempt is observable to the owner.
- Python tests live at `tests/evals/test_local_qualification_driver.py` and
  use `scripts/run_tests.sh`, not bare pytest. Apply the native Windows marker
  only if a case depends on Windows process topology; host-independent
  request contracts remain unmarked. No test reads implementation source text.

## End-to-End Tests

- **Status:** possible, conditional on measured resource admission. The real
  host is available; do not substitute a mock run for live evidence.
- **Intent:** INT-0004; R1/R2/R3 plus D2.
- `live_admission_receipt`: freeze the actual candidate/environment and
  ten-second baseline. Pass the admission-check test only if its verdict and
  recorded evidence agree. If rejected, record all inference/cancellation
  subchecks as `not-run`, zero model requests, and the exact reason. This is
  not a pass of live cancellation or model qualification.
- `live_smoke`: admitted 27B must produce the independently checked short
  answer while server identity/context, input/output ceilings, 300-second
  request limit and resource gates hold. Record total/prefill/decode time and
  meaningful first token separately where observable; explicit unavailable
  metrics stay unavailable. Timeout, wrong answer, resource breach or cap
  mismatch fails and stops the run.
- `live_main_cancel`: after successful smoke, trigger at five seconds after
  acceptance while a synthetic main request is active. Verify no owned
  request/process/listener within five seconds of cancellation. Completed
  before the trigger is inconclusive coverage and stops later trials.
- `live_auxiliary_cancel`: same contract through the real compression path,
  using an explicitly correlated physical auxiliary attempt and synthetic
  input. Test no useful compression claim; this is stop behavior only.
- Maximum three launches/three inference requests/30 minutes total; no rerun
  to hide a failure. A fresh approved scope is needed to enlarge those limits.

## Evidence and scope checks

- **Intent:** INT-0004; M1/P1/P2.
- `qualification_receipt_audit`: validate all attempt IDs and manifest links,
  full denominators, not-run/failure reasons, metric units and explicit
  missingness. Confirm raw evidence hashes/retention location without
  publishing private paths, credentials or unrelated content. Exercise the
  receipt validator against a synthetic missing-attempt ledger and dummy
  secret fixture to show that incomplete/unsafe publication is rejected.
- `book_scope_review`: manually trace plan → artifacts → intent/work state;
  preserve INT-0004 as unfinished and T-202 as queued. Verify narrative claims
  match actual receipts, all Book links resolve, and the official Book helpers
  pass. Record reviewer and exact checked revision; a helper exit code alone
  does not establish experimental validity.

## Execution and reporting

Run Rust formatting, clippy with warnings fixed, and affected crate tests.
Run Ruff format/check on new Python glue and the affected Python tests through
the repository runner. Use a separate, pinned evaluation environment and
actual Windows for native process tests. Keep outputs with command, revision,
host, exit code and concise result; do not mark unavailable tests passed.

Offline checks precede every live action. Unit/integration receipts go in
their standard sprint reports; live metrics and the manifest go under
`sprint-tests/qualification/`. An independent Test Phase critic reviews the
actual receipts and distinctions between passed, failed, inconclusive and
not-run checks. The Test/Loop contracts determine sprint status; a useful
negative report cannot turn a failed gate into successful qualification.
