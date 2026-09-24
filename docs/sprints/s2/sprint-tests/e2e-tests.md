# Sprint 2 End-to-End Results (live operation, run first)

- **Scope:** the real Hermes CLI and compression entry points, the installed
  llama.cpp b10964 CUDA backend and the owner's Qwen3.8-27B artifact. One
  disposable lab home and fixture directory (`.hermes-sandbox/s2`, ignored)
  were reused across all thirteen attempts; they were not fresh per attempt.
  No mocks, and no change to the live profile.
- **Evidence:** [operational ledger](operational-ledger.md),
  [sanitized receipts](qualification/attempts.json) and
  [frozen manifests](qualification/manifests/). The receipts carry explicit
  `independent_verification`, the sanitized `backend_launch_command` (slot,
  KV type, flash attention, batch/ubatch, threads, checkpoints, cache RAM,
  sampling) and a `not_measured_per_request` list.
- **Timeline (confidence before formal suites):**
  - Attempt 11 ended at 16:19:33Z, per its outcome-receipt mtime. This
    completed the operational-confidence criteria.
  - The first formal test invocation followed at about 16:21Z (session
    record).
  - The confidence text was written into the ledger at about 16:28Z, but
    committed only at 16:59:32Z (`d5b94380bd`). That is after the test files'
    commit at 16:54:17Z (`501ff12df5`). The commit order therefore does not
    show the precedence; the receipt times and the session record do.
  - Formal results are recorded against head `4bc4f5ea89` and later.
    `c42152ca0b` was the harness revision of attempts 10–11, not a tested
    head.

| Test | EARS | Attempts | Result | Evidence |
|---|---|---|---|---|
| `live_admission_receipt` | R1, M2 | 03, 04, 12 | pass | Each refusal recorded the exact RAM shortfall, zero launches and zero inference. Attempt 12 missed by 148,172,800 bytes, and no automatic retry followed. |
| `live_smoke` | R2 | 07, 08, 09, 10, 13 | pass | Exact `AMALGAM_OK` each time. The driver checked attempts 10 and 13 at run time. Attempts 07–09 predate that check (added in `a85c947692`) and were verified afterwards from private results; the receipts label each case. |
| `live_main_cancel` | R3, S1 | 10 | pass | The trigger fired with the slot processing request 15. Owned cleanup took 2.08 s, the listener closed at 2.63 s, and all roots exited 0. No sentinel was running in this attempt. |
| `live_auxiliary_cancel` | R3, D2 | 11 | pass | The real `compress_now` request (1875 tokens, no production output cap) was active at the trigger. Hermes's interrupt closed the connection at 0.61 s; cleanup took 1.22 s and the listener closed at 1.78 s. |
| `operational_repair_replay` | R4, AC7 | 01–11 | pass, under the amended envelope | The real terminal toolset read, edited and checked the fixture, failed on a missing script and recovered, and reported truthfully. The independent checker returned exit 0 and `CHECK_OK`. |
| `owned_job_cleanup_windows_live` (live half) | S1 | 08, 09 | pass | An independently launched sentinel survived owned cleanup in both attempts. Every published attempt's cleanup took at most 5 s, as audited by `test_every_published_attempt_resolves_to_a_valid_frozen_manifest`. |

**Defect repairs replayed** (fresh and continued sessions):

- GPU telemetry environment (01→02)
- mapped CPU tensors / load mode (02→05)
- 64K context floor (06→07)
- background title inference (07→08)
- tool surface (08→09)
- driver completion check (09→10)

**Refactor replayed** (not a defect repair): the T-206 policy extraction was
replayed live in attempts 12–13. Later extractions made in response to the
critique are replayed by T-211.

**Envelope amendments, which are not defect repairs** (owner-approved
continuations):

- Load-phase page-in allowance (after 05).
- RAM-conditional post-load page-in stop (after 09).
- Rendered-input ceiling raised from 4096 to 6144 (after 09).
- Launch allowance raised from six to nine (after 09).

The useful task peaked at 4543 rendered input tokens (attempt 10, request
14). The locked 4096 ceiling would therefore not have admitted it. The
**attempt-scoped time charging** used from attempt 10 was introduced by the
agent and is **unratified**. Under the originally approved rule (wall clock,
repairs charged), attempts 10–13 all exceed the 60-minute allowance. If the
handoff and review interval is instead treated as idle, attempts 10–11 fit
(3,104 s and 3,208 s) and 12–13 exceed it. The ledger's
[time-accounting correction](operational-ledger.md#time-accounting-correction-test-critique-c-020)
has the computation. Owner ratification is requested at the checkpoint.

## D1 prompt stability — within a session only

Within one conversation, the serialized prompt stayed append-only. The
uncached suffixes in attempt 10 were 40, 70, 47, 37, 93, 124 and 37 tokens.
**Across sessions it did not stay stable, so D1's stable-bytes clause fails
across sessions.** The same no-tool smoke rendered
to 1169 tokens in attempts 07 and 10 and to 1127 in 08, 09 and 13, although
configuration and effective code were unchanged. A diff of the private
prompts finds exactly one differing line in the system prompt:
`Python toolchain: python3=3.13.14 (no pip module), python=3.11.16, pip→python3.13, uv=installed.`

`tools/env_probe.py::get_environment_probe_line` waits up to 10 s for this
probe and then fails open by omitting the line. On a host busy loading or
hashing a 16 GB model, the probe sometimes misses the deadline. Hermes keeps
the system prompt fixed within a session, so no in-session cache contract is
broken. Across sessions, though, the line defeats cross-session prefix reuse
and invalidates byte-identical paired arms. Set `agent.environment_probe:
false` in lab profiles before T-202 and T-210 (lesson L-19).

## AC4 metrics — partially met

| Available in published receipts | Private log only | Not measured |
|---|---|---|
| Request identity; input tokens; uncached prompt tokens (attempts 10–13); decoded tokens (where parsed); total and meaningful-first-token seconds; RAM/VRAM/page-in/page-out extrema; stop cause; cleanup time | Slot id; per-request prompt and decode milliseconds for earlier attempts | Action/argument validity scoring; retry count (none by design); host UI responsiveness |

## Not run / deferred

The native/static paired comparison (AC3), context-policy trials (AC5) and
advancement (AC6) remain T-202. Thinking-enabled operation, contexts above
8192 and long sessions were not exercised. The direction review routes them
to [INT-0007](../../../intents/INT-0007-decode-budget-long-session.md) (T-210).
Lab-hardening gaps are carried by T-211.
