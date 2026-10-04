# Sprint 3 Test Report

Sprint 3 operated the real Hermes CLI on the owner's Windows host
(Qwen3.8-27B on an RTX 2080 Ti) through a long multi-file task. It
repaired what broke at the source and replayed every repair, and it wrote
the formal tests only after the
[operational confidence record](operational-ledger.md#operational-confidence-record)
(2026-10-04T01:58Z).

## Intent Verification

### INT-0007 — decode budget for long local sessions

| AC | Status | Evidence |
|---|---|---|
| AC1 — at least 20 requests on a multi-file task with per-turn receipts | **Partly met.** Receipts are complete in every run; the 20-request count was reached by R1 only. | R1 made 20 requests; R0 and R2 made 18 each, recorded as coverage not met, separately from completion (L2). All three verified 4/4. Every L1 field is present or named missing. |
| AC2 — off vs bounded vs unbounded at the best-screened sampling, per verified completion | **Met for off and bounded**; unbounded is T-218. | The screen selected greedy in both modes. Per verified item: R0 182 s and R1 347 s. Failures and stops are counted (attempts 10–12). |
| AC3 — byte-identical cross-session prefix, and append-only history with thinking on | **Met.** | C3: byte-identical prompts, 1147 of 1151 tokens reused. Thinking on, echo off: every turn rolls back the previous turn (median uncached 161). The replayed repair, `model.reasoning_echo: true`, makes history append-only (median 60), except after a budget-truncated think block. |
| AC4 — MTP | Deferred to T-217. | — |
| AC5 — compression | Deferred to T-219. | — |
| AC6 — default local policy with evidence | **Met for the settings measured.** | [`local-operating-policy.md`](../../../lineage/local-operating-policy.md) ranks by machine time per verified item, with receipt links. The live profile is unchanged (P2). |
| AC7 — host-derived deadlines, stall rule, backstop, predicted vs actual | **Met on the lab route.** The Hermes-side deadlines are T-219. | The T-215 unit tests (H1–H3). In the live runs, only stalls, backstops and resource guards stopped work, and no backstop was reached. All 165 requests record predicted and actual time. |

### INT-0004 — bounded local-model qualification

| Gap carried into Sprint 3 | Status | Evidence |
|---|---|---|
| AC1 and AC4 (identity, receipts) | **Closed.** | Published manifests with arms and identity; correlated receipts with named missing fields (V3, M4 tests). |
| AC2 time gate (host-derived) | **Met.** | 10,788.8 s charged against the 81,365 s host-derived backstop budget. Calibration is in the ledger before the screen. |
| AC2 main-cancel replay | **Met.** | C4: the slot was idle in 0.84 s and cleanup took 0.88 s. |

## Summary

| Layer | Result |
|---|---|
| Live (E2E) | Calibration, C1–C4, the screen and R0–R2 all completed; R3 was not triggered. See [e2e-tests](e2e-tests.md). |
| Formal unit and integration | **112 passed, 0 failed** across six files on head `0cd28ab8cc`: the throughput, lab, wire, Windows, receipts and Sprint 2 policy tests. See [unit-tests](unit-tests.md) and [integration-tests](integration-tests.md). |
| Regressions red on base (V2) | All 11 failed on their repair's parent revision. 7 failed on the behavior assertion itself; the rest because the repair introduced the API. |
| Affected-suite diff | Base: 7 failed. Head: 1 failed, inherited and unchanged. **0 new failures.** |
| Live-profile fingerprints (P2) | `config.yaml` `a48b4add…` and `presets.ini` `bb35c72d…` match the Sprint 3 baseline. |

## Failures found and fixed

The operational defects and their replays are in the ledger's provenance
table: the cold kernel cache, the blocking cancel, the admission-sample
calibration, the C3 paths and erase, both sides of the telemetry race, the
shared `TEMP`, the scan false positives and the wire's sequential-retry
refusal. The formal phase found two more:

1. **The wire's in-flight ownership race** (`0cd28ab8cc`). The attempt-10
   repair let a finishing handler clear the next request's claim. The
   concurrency test failed, and it now passes.
2. **A repository path in the session `PATH`** (`e062f5ee9d`). Under an
   activated repo venv, the operator's `PATH` carried a repository entry into
   the CLI's environment, breaching M2.

## Concerns and limits

- **Host headroom.** With the model loaded, this host keeps about 6 GiB free.
  Windows idle maintenance (attempt 11) and ordinary app use (attempt 12)
  each crossed a guard. The guards worked as designed, but long local runs on
  a 32 GiB machine need a quiet host.
- **AC1 coverage.** Greedy thinking-off and echo runs finished the task in 18
  requests. The task is too efficient for this model to reach 20 every time.
  Lengthening it is a Sprint 4 candidate.
- **The live retry path.** The sequential-retry repair was not re-triggered
  live; it is covered offline and by the integration test.

## Technical Debt Identified

- The T-215 prediction ignores context-dependent decode: 3.27 tok/s at about
  8K context against 3.55 calibrated, which caused one 9% under-prediction.
  For T-219.
- A budget-truncated think block re-renders differently from what was
  generated (R2's only divergence). For T-218.
- The client first-launch kernel JIT cost (30× slower first prompt) must be
  handled in Hermes's own local-runtime deadlines. For T-219.
- One inherited Windows failure: `test_spawn_server_keeps_the_callers_environment`.

## Coverage Observations

- No test reads source code. Each pure seam (`launch_flags`, `read_sample`,
  `write_calibration` reading its own receipt) was extracted, then tested by
  behavior.
- Host-specific behavior (Windows file sharing, text-mode newlines) is
  tested on Windows under `windows_only`, never by faking `sys.platform`.
