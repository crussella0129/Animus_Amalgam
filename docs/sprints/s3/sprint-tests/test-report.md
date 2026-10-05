# Sprint 3 Test Report

Sprint 3 operated the real Hermes CLI on the owner's Windows host
(Qwen3.8-27B on an RTX 2080 Ti) through a long multi-file task. It
repaired what broke at the source and replayed every repair, and it wrote
the formal tests only after the
[operational confidence record](operational-ledger.md#operational-confidence-record)
(2026-10-04T01:58Z). The final formal run is at head `1fca1a3095`, after
two critique rounds.

## Intent Verification

### INT-0007 — decode budget for long local sessions

| AC | Status | Evidence |
|---|---|---|
| AC1 — at least 20 requests on a multi-file task with per-turn receipts | **Partly met.** Receipts are complete; the 20-request count was reached by R1 only. | R1 made 20 requests. R0 and R2 made 18 each, recorded as coverage not met, separately from completion (L2). All three verified 4/4. Every request carries every L1 field or names it missing (`test_every_request_names_its_missing_fields`). The fix is owned by backlog **T-223**. |
| AC2 — off vs bounded vs unbounded at the best-screened sampling, per verified completion, including failures | **Met for off and bounded**; unbounded is T-218. | The screen selected greedy in both modes. Per verified item, across every attempt of a run, failed and stopped ones included (O1): R0 205.3 s and R1 345.4 s. The completed runs alone: 180.2 s and 345.4 s. The inputs are published per session in the receipts. |
| AC3 — byte-identical cross-session prefix, and append-only history with thinking on | **Met.** | C3: byte-identical prompts, 1147 of 1151 tokens reused. Thinking on, echo off: every turn rolls back the previous turn (median uncached 161). The replayed repair, `model.reasoning_echo: true`, makes history append-only (median 60), except after a budget-truncated think block. |
| AC4 — MTP | Deferred to T-217. | — |
| AC5 — compression | Deferred to T-219. | — |
| AC6 — default local policy with evidence | **Met for the settings measured.** | [`local-operating-policy.md`](../../../lineage/local-operating-policy.md) ranks by machine time per verified item, with failures in the denominators and receipt links. The live profile is unchanged (P2). |
| AC7 — host-derived deadlines, stall rule, backstop, predicted vs actual, stops recorded as failures | **Met on the lab route.** The Hermes-side deadlines are T-219. | The T-215 unit tests (H1–H3), including `step_stop`'s backstop and stall decisions. Live, only stalls and resource guards stopped work, and no backstop was reached. All 165 completed post-calibration requests carry predicted and actual time and resource extrema, asserted by presence. The 4 attempt-stopped requests keep their stop cause and elapsed time, but their predictions (and, in attempts 11 and 12, their extrema) were not recorded by the pre-repair lab. The repaired lab keeps both on every stop path (`stopped_request`, `RequestExtrema`), and both paths are tested. |

### INT-0004 — bounded local-model qualification

| Gap carried into Sprint 3 | Status | Evidence |
|---|---|---|
| AC1 and AC4 (identity, correlated receipts) | **Closed.** | All 13 attempts are published, each resolving to a digest-checked manifest with its arms (V3, M4 tests). Every request carries its fields or names them missing. The pinned llama.cpp's OpenAI stream carries no `id_slot`, so the slot is correlated from `/slots` (`id_slot_source: "slots"`). Receipts published before that repair name `id_slot` missing. |
| AC2 time gate (host-derived) | **Met.** | 10,788.8 s charged against the 81,365 s host-derived backstop budget. Calibration was in the ledger before the screen. |
| AC2 main-cancel replay and OS kill safety | **Met.** | C4: the slot was idle in 0.84 s and cleanup took 0.88 s. The T5 bring-up replay: the silent tree was stopped by the stall rule and gone in 0.047 s, a chatty child survived, and the sentinel survived. |

## Summary

| Layer | Result |
|---|---|
| Live (E2E) | Calibration, C1–C4, T5, the screen and R0–R2 all completed; R3 was not triggered. See [e2e-tests](e2e-tests.md). |
| Formal unit and integration | **217 passed, 0 failed** across six files at `1fca1a3095`. Runner log sha256 `72fefa45…`, started 2026-10-05T20:35:10Z; it passed twice in a row with retries off. See [unit-tests](unit-tests.md) and [integration-tests](integration-tests.md). |
| Regressions red on base (V2) | All 18 failed on their repair's parent revision. 11 failed on the behavior assertion itself, 1 on a missing schema field, and 6 because the repair introduced the API. Each of the 7 non-behavioral defects is evidenced live by the attempt that found it. |
| Affected-suite diff | Base: 7 failed. Head: 1 failed, inherited and unchanged. **0 new failures.** |
| Live-profile fingerprints (P2) | `config.yaml` `a48b4add…` and `presets.ini` `bb35c72d…` match the Sprint 3 baseline. |

## Failures found and fixed

The operational defects and their replays are in the ledger's provenance
table. The formal phase found three more, each fixed and covered by a
regression:

1. **The wire's in-flight ownership race** (`0cd28ab8cc`).
2. **A repository path in the session `PATH`** (`e062f5ee9d`).
3. **Requests stopped by an attempt stop lost their predictions and cause**
   (`efeb4ef4c4`): critique-01 C-003.
4. **A later cancel record relabelled a stopped request; a guard stop
   dropped the in-flight request's resource extrema; and sessions cut short
   by an attempt stop were never scored** (`1fca1a3095`): critique-02
   C-001, C-002 and C-005.

## Concern dispositions (critique round 1)

[critique-01](critique-01.md) returned `block` with 13 concerns. Each one
was addressed:

| Concern | Response |
|---|---|
| C-001: H2 backstop tautology | **Fixed.** `throughput.step_stop` decides stall versus backstop for requests and the load. The test asserts no stop while progressing, `"backstop"` past it, and `"stall"` on a silent step. |
| C-002: T1, T2 and T3 untested; the 0.5 s constant | **Fixed.** Boundary tests for every stop predicate. `run.session_windows` with rate-doubling and load-scaling tests. The writer's retry bound is now half the telemetry period, and is listed as a retained cadence in the README. |
| C-003: stopped requests drop timing; skipped check | **Fixed.** The wire records predictions at send and on every stop path, and a `request_stopped` receipt carries the stop cause. The receipt tests check all 14 fields on every request and the cause on stopped ones. The O5 claim is corrected to 165 of 169. |
| C-004: the double leaked `id_slot`; no tool call | **Fixed.** The capture backend now matches b10964 (no `id_slot`, `/slots` names the slot, a streamed tool call, a `length` finish), and the lab correlates the slot from `/slots`. AC4 is restated above. |
| C-005: the denominator rule not applied | **Fixed.** The O1 figures now count every failed and stopped attempt, beside the completed-run figures. The ranking is unchanged; the ledger and policy state the rule. |
| C-006: attempts 01 and 03 unpublished | **Fixed.** Both are published, and the test checks every attempt index from the budget counter. |
| C-007: T5 a bare timer; C1 pin unreported | **Fixed.** The bring-up stall watches child output and a chatty child must survive; it was re-run at `efeb4ef4c4`. The cancel test is relabelled C4. The C1 pin evidence is recorded. |
| C-008: API-only reds; missing regressions | **Fixed in part.** Behavioral regressions were added for the observing waits and the per-session erase (red on base). The four API reds are recorded as such, with their live evidence. A shim replaying the pre-repair code paths would re-implement the defect rather than test it, so it is not built. |
| C-009: C2 fail-closed untested | **Fixed.** Calibration and `prepare` fail-closed tests. |
| C-010: sub-2 s bounds and sleep synchronization | **Fixed.** Event-based synchronization (the backend's first-chunk event), bounds of at least 2 s, and an injected retry bound. |
| C-011: no V1 fingerprint; no intent links | **Fixed.** Runner-log digests and the first-run window are recorded (`formal_order_review` in the unit results). Both intents link the Sprint 3 test evidence. |
| C-012: M1, M4 and L4 claims beyond the assertions | **Fixed.** M1 against the published argv, the identity change, launch and admission receipts, first-prefix records, the full calibration record and allowlisted L4 paths. |
| C-013: AC1 shortfall unowned | **Deferred with rationale** to backlog **T-223**: lengthen the task, or make L3 require headroom above 20. |

## Concern dispositions (critique round 2)

[critique-02](critique-02.md) returned `block` with 7 concerns:

| Concern | Response |
|---|---|
| C-001: the attempt-stop timing path was untested | **Fixed.** The `run.stopped_request` seam is tested. `publish.receipts` is tested on synthetic stop sequences: a later `wire_failure` or `response_cancelled` no longer overrides `stopped` (this was red on base). A malformed-stream wire test checks that a failing request keeps its timing and predictions. |
| C-002: the completeness check could not fail; extrema lost on a stop | **Fixed.** A new receipt test asserts that timing, predictions and resources are present on every completed calibrated request. `run.RequestExtrema` records them on every loop exit, and a test raises a guard inside the loop. |
| C-003: the V2 claims overstated | **Fixed.** The V2 table restates the observing waits as an API red and the erase as a schema red. The erase test now exercises `run.erases_slot`, the decision `run_session` makes. |
| C-004: the probe timeout was untested; the retained list changed outside the plan | **Fixed.** `run.probe_window` derives the probe timeout, and it joins the rate-doubling test. Every remaining fixed bound is listed in the README with its reason, as a recorded plan deviation (below). |
| C-005: attempt-stopped sessions were unscored | **Fixed.** `run.stopped_session` scores a cut-short session in the stop path. `publish.py` scored the preserved fixtures of attempts 05, 07, 11 and 12 (0, 0, 0 and 2 verified), and a receipt test requires the scores. |
| C-006: sub-2 s and sleep-based synchronization | **Fixed.** The `wait_while` timeout case uses 2 s. The capture backend reports a slot as processing only during a request and holds its final chunk until a poll is served, and the slots test waits until the wire has seen the working slot. |
| C-007: stale completion records; R1 rounding; unpublished inputs | **Fixed.** The completion entries for T-214, T-216 and T-221 carry corrections. Receipts publish per-request relative times and per-session machine time. The O1 figures are recomputed from them, divided by the items every attempt verified. R1 is 345.4 s under both readings. |

## Plan deviation: retained fixed values

The build plan retained only the observation cadences and the 2 s grace and
5 s cleanup. The Test phase found and kept further fixed bounds:

- the telemetry writer retry (half a sample period);
- the `nvidia-smi` query (2 s);
- the hidden verifier's process and thread bounds (60 and 120 s);
- the `git` identity probes (10 s);
- one-time venv creation (600 s);
- the wire-close settle (1 s).

Each bounds process start-up, I/O or polling, never token work. They are
listed with their reasons in the lab README. Every window that scales with
token work derives from the throughput model and is tested to scale with
the host's rates.

## Concerns and limits

- **Host headroom.** With the model loaded, this host keeps about 6 GiB free.
  Windows idle maintenance (attempt 11) and ordinary app use (attempt 12)
  each crossed a guard. The guards worked as designed, but long local runs on
  a 32 GiB machine need a quiet host.
- **The live retry path.** The sequential-retry repair was not re-triggered
  live; it is covered by the integration test.
- **Post-confidence lab changes** were not replayed live (the launch envelope
  is spent). They are behavior-preserving seams, receipt-completeness
  changes and fixes, each covered by formal tests. They are listed in the
  ledger.

## Technical Debt Identified

- The T-215 prediction ignores context-dependent decode: 3.27 tok/s at about
  8K context against 3.55 calibrated, which caused one 9% under-prediction.
  For T-219.
- A budget-truncated think block re-renders differently from what was
  generated (R2's only divergence). For T-218.
- The client first-launch kernel JIT cost (30× slower first prompt) must be
  handled in Hermes's own local-runtime deadlines. For T-219.
- AC1's request count on efficient models. For T-223.
- One inherited Windows failure: `test_spawn_server_keeps_the_callers_environment`.

## Coverage Observations

- No test reads source code. Each pure seam (`launch_flags`, `read_sample`,
  `session_windows`, `wait_while`, `step_stop`, and `write_calibration`
  reading its own receipt) was extracted, then tested by behavior.
- Host-specific behavior (Windows file sharing, text-mode newlines) is
  tested on Windows under `windows_only`, never by faking `sys.platform`.
