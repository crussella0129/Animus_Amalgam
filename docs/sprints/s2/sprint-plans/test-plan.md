Finalized - DO NOT EDIT

# Sprint 2 Test Plan

## Execution order: operate, repair, replay, then formal verification

All work advances [INT-0004](../../../intents/INT-0004-bounded-local-model-qualification.md).
Its AC7 captures the owner's reverse-E2E direction. During Build, use actual
Hermes in a disposable environment, encounter failures, inspect them, repair
the implementation and replay failed operations. Do not make an offline
test matrix a prerequisite to operating the application.

Only the minimum practical bring-up checks precede live use: the isolated
endpoint is correct, request limits actually apply, and the independent stop
control works. Compile/format/lint as needed to get runnable code. These are
not permission to run the official unit/integration suites early.

Official unit and integration verification starts only after the operational
confidence criteria below are met. Prefer existing relevant tests; add focused
regressions for actual defects and essential new contracts. Do not create
exhaustive fixtures for speculative failures or rerun green suites without a
code change, a failure or another concrete reason.

## Intent Traceability

AC3, comparative context-policy AC5 and advancement AC6 remain T-202. The real
tasks here provide development evidence, not a native/static comparison.

| Intent | Acceptance criterion | Build task / EARS clause | Verification |
|---|---|---|---|
| INT-0004 | AC1 | T-201 / M1 | manifest_identity_contract, qualification_receipt_audit |
| INT-0004 | AC1 / AC2 | T-201 / M2 | admission_stop_contract, live_admission_receipt |
| INT-0004 | AC2 / AC4 | T-206 / S1 | owned_job_cleanup_windows_live, live_main_cancel |
| INT-0004 | AC2 / AC4 | T-206 / S2 | admission_stop_contract, owned_job_cleanup_windows_live |
| INT-0004 | AC1 / AC2 / AC4 | T-207 / D1 | test_hermes_wire_and_isolation_contract |
| INT-0004 | AC1 / AC2 | T-207 / D2 | test_hermes_wire_and_isolation_contract, live_auxiliary_cancel |
| INT-0004 | AC2 / AC4 | T-208 / R1 | live_admission_receipt |
| INT-0004 | AC2 / AC4 | T-208 / R2 | live_smoke |
| INT-0004 | AC2 / AC4 | T-208 / R3 | live_main_cancel, live_auxiliary_cancel |
| INT-0004 | AC4 / AC7 | T-208 / R4 | operational_repair_replay |
| INT-0004 | AC1 / AC4 | T-209 / P1 | qualification_receipt_audit |
| INT-0004 | AC7 and deferred AC3 / AC5 / AC6 | T-209 / P2 | book_scope_review |

## End-to-End Development — first

- **Status:** possible, conditional on resource admission. Use the real
  Hermes entry point, installed 27B backend and disposable task files; do not
  substitute a local HTTP fixture or generic SDK demo for operation.
- **Intent:** INT-0004; R1–R4, S1, D2.
- **live_admission_receipt:** record current host conditions and admission.
  Rejection records zero inference for that attempt and becomes a blocker to
  diagnose. If unresolved, leave operational confidence pending; this is not
  successful reverse-E2E or permission to replace operation with mocks.
- **live_smoke:** verify one tiny response and observe the actual endpoint,
  request budget, timings and resources. It confirms bring-up only.
- **live_main_cancel / live_auxiliary_cancel:** practically interrupt active
  main and actual compression requests. Verify owned cleanup within five
  seconds and no unrelated process termination. Completed-before-trigger
  means inconclusive cancellation evidence, not pass. Diagnose and replay
  within the same aggregate budget.
- **operational_repair_replay:** drive Hermes to read a fixture, edit it, run
  its real checker, encounter a deliberately failing command and recover.
  Continue the conversation to observe tool-result accumulation and bounded
  context pressure. Check resulting files/exit results independently. Record
  each failure, diagnostic evidence, root cause, repair revision and replay.
  Repairs may touch the real Hermes path; no substitute agent loop.

Operational confidence requires verified useful-task completion, successful
replay of repaired paths in fresh and continued sessions, working main and
auxiliary cancellation, and no unresolved blocking defect. Do not invent a
defect to fill the ledger if an operation succeeds initially. Do not call a
one-word smoke a useful task.

Development has a proposed aggregate budget of eighteen inference requests,
six launches and 60 minutes including startup/cleanup across all revisions.
Each request/load remains capped at 300 seconds; memory/stop gates remain
fixed. A failure stops its attempt, not the entire repair loop. Changing a
manifest never resets counters. At an unresolved blocker or exhausted budget,
report the evidence and keep confidence pending rather than silently enlarging
the run or reporting a pass.

## Unit Tests — after operational confidence

- **Intent:** INT-0004; M1/M2/S2.
- **manifest_identity_contract:** changing a real fixture artifact or an
  execution parameter invalidates the previous identity; observations and
  pre-admission unknowns remain distinct. Reuse existing hashing/parsing
  coverage; do not retest library internals.
- **admission_stop_contract:** missing identity/probes, insufficient per-device
  capacity or a breached/stale limit prevents launch or irreversibly stops
  the attempt. Use deterministic samples/clock inputs, not real memory stress.

These are focused new-envelope contracts. Additional regressions must point
to an observed defect; never test implementation source text or freeze values
that are expected to change.

## Integration Tests — after operational confidence

- **Intent:** INT-0004; S1/S2/D1/D2.
- **owned_job_cleanup_windows_live:** a real Windows parent/child/grandchild
  chain is owned before execution; cancellation, owner loss and a stalled
  collector leave no owned child/listener and retain an unrelated sentinel.
  Extend the operational reproducer into this regression, rather than build
  an independent supervision simulator. Use event synchronization and the
  actual host OS.
- **test_hermes_wire_and_isolation_contract:** actual Hermes main/compression
  imports and temporary homes A→B→A preserve route, bounded physical attempts,
  128-token cap, stable equivalent request bytes and profile separation.
  A mismatched server/context/rendered-input contract blocks generation.
  Use a local capture endpoint for this later regression only; its success
  is not live inference evidence. Reuse affected existing coverage where it
  already proves the contract.

Run Python checks through scripts/run_tests.sh; never bare pytest. Use the
repository Windows marker only for OS-dependent cases. Run the affected Rust
crate checks, formatting and clippy; run Ruff for new Python. Expand official
testing only for affected boundaries or new failures. If formal verification
finds a defect, reproduce/repair/replay the operation before rerunning the
affected check; do not blindly repeat the entire suite.

## Evidence and scope checks

- **Intent:** INT-0004; M1/P1/P2.
- **qualification_receipt_audit:** retain every attempt and revision, manifest
  identity, failure, exclusion and unavailable metric. Distinguish exploration
  from later frozen qualification. Screen publishable artifacts for private
  paths/configuration, credentials and unrelated content; preserve raw evidence
  locally with fingerprints. Do not build a general publication framework.
- **book_scope_review:** verify the operational-confidence record predates
  official suite runs, trace claims to actual evidence, retain INT-0004 as
  unfinished and T-202 as queued, resolve Book links and use official Book
  helpers. Missing operational evidence cannot be promoted to confidence
  by passing unit/integration tests.

Record unit/integration checks as pending/not run while the operational loop
is unresolved. After confidence, preserve the tested revision, commands,
results and focused coverage. The Test Phase critic reviews both the
operation/repair ledger and subsequent formal results before any success
report. This plan is a bounded development loop, not a promise to grind
through tests until a dashboard turns green.
