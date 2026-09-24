# Sprint 2 End-to-End Results (live operation, run first)

- **Scope:** real Hermes CLI and compression entry points, the installed
  llama.cpp b10964 CUDA backend and the owner's Qwen3.8-27B artifact, in a
  disposable home and fixture. No mocks, no live-profile change.
- **Evidence:** [operational ledger](operational-ledger.md),
  [sanitized receipts](qualification/attempts.json),
  [frozen manifests](qualification/manifests/).
- **Order:** operational confidence was declared after attempt 11
  (2026-09-24, about 16:18Z). The first formal suite ran afterwards, on
  harness revision `c42152ca0b`. Attempts 12–13 are a later live replay of
  the refactored harness.

| Test | EARS | Attempts | Result | Evidence |
|---|---|---|---|---|
| `live_admission_receipt` | R1, M2 | 03, 04, 12 | pass | Each refusal recorded the exact RAM shortfall, zero launches and zero inference. Attempt 12 missed by 148,172,800 bytes, and no automatic retry followed. |
| `live_smoke` | R2 | 07, 08, 09, 10, 13 | pass | Each returned exact `AMALGAM_OK`, checked independently by the driver. Attempt 10: 1169 input tokens, 12.0 s. Attempt 13 (refactored harness): 10.5 s. Timings and resource extrema are in the receipts. |
| `live_main_cancel` | R3, S1 | 10 | pass | The trigger fired with the slot processing request 15. Owned cleanup took 2.08 s, the listener closed at 2.63 s, and all roots exited 0. |
| `live_auxiliary_cancel` | R3, D2 | 11 | pass | The real `compress_now` request (1875 tokens, no production output cap) was active at the trigger. Hermes's interrupt closed the connection at 0.61 s; cleanup took 1.22 s and the listener closed at 1.78 s. |
| `operational_repair_replay` | R4, AC7 | 01–11 | pass | The real terminal toolset read, edited and checked the fixture, failed on a missing script and recovered, and reported truthfully. The independent checker returned exit 0 and `CHECK_OK`. Repairs replayed in fresh and continued sessions: GPU telemetry env (01→02), load mode (02→05), paging policy (05/09→10), 64K floor (06→07), title inference (07→08), tool surface (08→09), input ceiling (09→10). |
| `owned_job_cleanup_windows_live` (live half) | S1 | 08, 09 | pass | An independently launched sentinel process survived owned cleanup in both attempts. |

## Observed characteristics (not qualification claims)

- Continued-session prefix reuse was exact with thinking disabled. Uncached
  prompt tokens per continued turn were 40, 70, 47, 37, 93, 124 and 37, on
  the hybrid model with zero checkpoints.
- Cold prefill ran at 111–128 tokens/s and decode at 3.31–3.69 tokens/s.
  Decode dominated every warm step.
- Across attempts 10–13, minimum sampled RAM was 5.73 GiB, minimum free VRAM
  3.02 GiB and maximum page-out 0.2 MiB/s. The GPU peaked at 61 °C.

## Not run / deferred

The native/static paired comparison (AC3), context-policy trials (AC5) and
advancement (AC6) remain T-202. Thinking-enabled operation, contexts above
8192 and long sessions were not exercised. The direction review routes them
to [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md).
