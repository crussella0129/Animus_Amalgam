# Sprint 3 Test Report

Sprint 3 operated the real Hermes CLI on the owner's Windows host
(Qwen3.8-27B on an RTX 2080 Ti) through a long multi-file task. It
repaired what broke at the source and replayed every repair, and it wrote
the formal tests only after the
[operational confidence record](operational-ledger.md#operational-confidence-record)
(2026-10-04T01:58Z). The final formal run is at head `32b8e50eaf`, after
eight critique rounds.

## Intent Verification

### INT-0007 — decode budget for long local sessions

| AC | Status | Evidence |
|---|---|---|
| AC1 — at least 20 requests on a multi-file task with per-turn receipts | **Partly met.** Receipts are complete; the 20-request count was reached by R1 only. | R1 made 20 requests. R0 and R2 made 18 each, recorded as coverage not met, separately from completion (L2). All three verified 4/4. Every request carries every L1 field or names it missing (`test_every_request_names_its_missing_fields`). The fix is owned by backlog **T-223**. |
| AC2 — off vs bounded vs unbounded at the best-screened sampling, per verified completion, including failures | **Met for off and bounded**; unbounded is T-218. | The screen selected greedy in both modes. Per verified item, across every attempt of a run, failed and stopped ones included (O1): R0 205.3 s and 557.5 decoded tokens, and R1 345.4 s and 1,058.3 tokens. The completed runs alone: 180.2 s and 345.4 s. R0's token figure is a lower bound: one stopped request's decode was never returned. From its published seconds after prefill, at the fastest decode rate any receipt shows, an estimate is about 586.1. The screen's greedy selection is the completed screen's (attempt 06). Counting the earlier stopped screen (attempt 05) as O1 counts stops, thinking-off model default would lead, at 318.5 s against greedy's 375.4 s; the full-length comparison is backlog T-225. The inputs are published per session in the receipts. |
| AC3 — byte-identical cross-session prefix, and append-only history with thinking on | **Met.** | C3: byte-identical prompts, 1147 of 1151 tokens reused. Thinking on, echo off: every turn rolls back the previous turn (median uncached 161). The replayed repair, `model.reasoning_echo: true`, makes history append-only (median 60), except after a budget-truncated think block. |
| AC4 — MTP | Deferred to T-217. | — |
| AC5 — compression | Deferred to T-219. | — |
| AC6 — default local policy with evidence | **Met for the settings measured.** | [`local-operating-policy.md`](../../../lineage/local-operating-policy.md) ranks by machine time per verified item, with failures in the denominators and receipt links. The live profile is unchanged (P2). |
| AC7 — host-derived deadlines, stall rule, backstop, predicted vs actual, stops recorded as failures | **Met on the lab route.** The Hermes-side deadlines are T-219. | The T-215 unit tests (H1–H3), including `step_stop`'s backstop and stall decisions. Live, only stalls and resource guards stopped work, and no backstop was reached. All 165 completed post-calibration requests carry every L1 and M3 request field, asserted by presence. The exceptions are `id_slot`, which b10964 does not stream, and tool-call tokens, which the live runs' wire did not count; both are named missing. The 4 attempt-stopped requests after calibration (attempts 05, 07, 11 and 12) keep their own stop cause and elapsed time, but the pre-repair lab recorded neither their predictions nor their extrema. Attempt 02's stall-stopped calibration request also lacks extrema. The repaired lab keeps both on every stop path (`stopped_request`, `RequestExtrema`), and both paths are tested. |

### INT-0004 — bounded local-model qualification

| Gap carried into Sprint 3 | Status | Evidence |
|---|---|---|
| AC1 and AC4 (identity, correlated receipts) | **Closed.** | All 13 attempts are published, each resolving to a digest-checked manifest with its arms (V3, M4 tests) and pinning the AC1 identity: model, tokenizer, template, backend build, Hermes commit and task corpus (asserted since round 8). Every request carries each of its 18 L1/M3 fields or names them missing. Since round 4 this includes meaningful first token and the tool-call count. Every long session has validity for each delivered tool call or names the shortfall: attempt 10's one call cut at the output cap, which Hermes dropped from its history, is named. The wire now records validity for every delivered call. The pinned llama.cpp's OpenAI stream carries no `id_slot`, so the slot is correlated from `/slots` (`id_slot_source: "slots"`). Receipts published before that repair name `id_slot` missing. |
| AC2 time gate (host-derived) | **Met.** | 10,788.8 s charged against the 81,365 s host-derived backstop budget. Calibration was in the ledger before the screen. |
| AC2 main-cancel replay and OS kill safety | **Met.** | C4: the slot was idle in 0.84 s and cleanup took 0.88 s. The T5 bring-up replay: the silent tree was stopped by the stall rule and gone in 0.047 s, a chatty child survived, and the sentinel survived. |

## Summary

| Layer | Result |
|---|---|
| Live (E2E) | Calibration, C1–C4, T5, the screen and R0–R2 all completed; R3 was not triggered. See [e2e-tests](e2e-tests.md). |
| Formal unit and integration | **318 passed, 0 failed** across six files at `32b8e50eaf`. Runner log sha256 `0cd5001f…`, started 2026-10-06T04:26:14Z; it passed twice in a row with retries off. See [unit-tests](unit-tests.md) and [integration-tests](integration-tests.md). |
| Regressions red on base (V2) | All 45 failed on their repair's parent revision. 25 failed on the behavior assertion itself and 20 because the repair introduced the API. The 7 API reds of rounds 1 and 2 are evidenced live by the attempt that found each defect. The 11 API reds of rounds 3 to 5 are the new fields and seams that those rounds' behavior reds depend on. |
| Affected-suite diff | Base: 7 failed. Head: 1 failed, inherited and unchanged. **0 new failures.** |
| Live-profile fingerprints (P2) | At 2026-10-05T21:38:24Z, head `663bac6a2a`, and 2026-10-06T04:11:27Z, head `47522c6a2d`, `config.yaml` `a48b4add…` (6,700 bytes) and `presets.ini` `bb35c72d…` (580 bytes) equal the plan baseline (`live_profile_untouched`). They are re-checked at sprint close. |
| Policy review (P1) | **Pass** (`policy_evidence_review`, re-reviewed 2026-10-06T04:11Z after round 7 corrected two policy figures). See [e2e-tests](e2e-tests.md). |

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
5. **An aborted request took the attempt's later, unrelated cause; cut-short
   sessions were never L4-screened; stop-path scoring could raise past the
   ledger charge; and the probe timeout had no floor before calibration**
   (`4f323770ee`): critique-03 C-001, C-002, C-003 and C-005.
6. **A session's stall or backstop stop would be published as a deliberate
   cancel; stopped requests dropped their first token silently; an attempt
   stop during a session's verification would screen nothing**
   (`663bac6a2a`): critique-04 C-001, C-002 and C-003.
7. **Tool-call validity came from Hermes's history, which drops a call cut
   at the output cap; tool-call output was in neither half of the token
   split; cut-short long sessions had no AC1 coverage** (`9c373121cd`):
   critique-05 C-001, C-002 and C-003.
8. **Requests that never completed left their decode count silently
   absent, so token figures read as exact** (`a730a0a39e`): critique-06
   C-001.
9. **Two policy figures contradicted the receipts, and the screen ranking
   rested on an unpublished re-scan** (`47522c6a2d`): critique-07 C-001 and
   C-002. Echo's prefill saving was the median, not the total, and the peak
   input was 9,935 tokens, not 7,867.

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

## Concern dispositions (critique round 3)

[critique-03](critique-03.md) returned `block` with 6 concerns:

| Concern | Response |
|---|---|
| C-001: attempt 02's stall-stopped request published with the attempt's later cause | **Fixed.** An aborted request takes its own session's recorded stop as its cause. Only a request in flight at the attempt stop takes the attempt's reason. Attempt 02's request 1 now reads `stall in prefill (window 47.0s)`. The receipt test asserts the cause equals the session's stop or the attempt's reason (red on base), and a publish test covers all three cases. |
| C-002: cut-short sessions never L4-screened, yet counted in O1 | **Fixed.** The wire keeps the conversation it last forwarded plus the response it last delivered, and the stop path screens it. Publish screened attempts 05, 07, 11 and 12 from their last request's conversation, each stopped in flight: none was flagged. Tests flag a contaminated cut-short session on both paths. O1 is reported under every reading: R2 is 384.3 s with attempt 12's screened items, 494.0 s without them and 864.6 s divided by one run's 4 items. R0 < R1 < R2 under each. |
| C-003: stop-path seams tested on hand-built inputs; scoring unguarded in `finally` | **Fixed.** A wire test feeds the live `Wire.active` into `stopped_request` mid-stream. Stop-path scoring is bounded by `VERIFY_S` and never raises: an error or overrun is recorded as the session's verification, and the ledger charge and outcome follow. |
| C-004: L1 presence covered only part of L1 | **Fixed.** Every L1 field is asserted present on completed calibrated requests. `id_slot` must be named missing, since these receipts predate the `/slots` correlation. |
| C-005: records misstated the evidence and the plan | **Fixed.** Extrema are missing in attempts 02, 05, 07, 11 and 12. The request counts are 3 (attempt 05) and 11 (attempt 12). The erase red is restated as API, making V2 16 behavioral and 11 API. The plan already retained the `git` timeouts and the 1 s lock handoff; the deviation is restated below with the 0.2 s listener check added. The uncalibrated probe window is asserted, and now keeps the observation floor. |
| C-006: the capture backend released its final chunk before the wire had necessarily seen the slot | **Fixed.** The final chunk is released only after the test observes `slot_seen`. The wire file passed 4 runs in a row with retries off. |

## Concern dispositions (critique round 4)

[critique-04](critique-04.md) returned `block` with 5 concerns:

| Concern | Response |
|---|---|
| C-001: a stall- or backstop-stopped request would be published as a cancel with no cause | **Fixed.** `run.stop_active_request` records the in-flight request's `request_stopped` with the session's stop before the wire cancels it, and `run_session` stops through it. A wire test publishes the live wire's own receipts. The stall-stopped request comes out `stopped` with its cause, and the deliberate cancel stays `response_cancelled`. |
| C-002: meaningful first token silently absent on stopped requests | **Fixed.** `stopped_request` carries the first token. Publish names it, and the tool-call count, missing when absent, which applies to all 5 stopped requests, and attempt 04's cancelled request names its tool-call count missing (it carries its first token; corrected in round 5). Cut-short sessions record tool-call validity from their last conversation: attempts 05, 07, 11 and 12 had 2, 2, 2 and 6 calls, all valid and known. The receipt tests check 16 fields per request and validity on every long session. |
| C-003: a cut-short screen could be empty and pass as clean | **Fixed.** The wire keeps an ended session readable until the next begins, and `stopped_session` finds the session by id. A wire test ends the session first, as a stop during verification would. Every L4 screen publishes what it saw, and the receipt test requires non-zero messages and tool calls for a session with requests. |
| C-004: calibration gap window differs from the plan | **Deviation recorded and asserted.** The driver reports the session's T_cli only in its result, after the session ends. During calibration the gap is therefore k × the attempt's own load time, the more permissive window. The README and the deviation list below record it, and the uncalibrated test asserts it. |
| C-005: no P1/P2 check results | **Fixed.** Both checks are recorded with time and head in [e2e-tests](e2e-tests.md); P2 is re-checked at close. The policy now says the echo-on recommendation is outside the time ranking, where echo ranks third. It is chosen for AC3's append-only history, and its throughput benefit on longer sessions is unmeasured. |

## Concern dispositions (critique round 5)

[critique-05](critique-05.md) returned `block` with 5 concerns:

| Concern | Response |
|---|---|
| C-001: validity left out the sprint's only malformed call | **Fixed.** The wire records validity for every delivered call, so a call cut at the cap is recorded invalid (tested), and sessions take their validity from it. For the published attempts, recorded before this, each long session shows its delivered count and names any call missing from Hermes's history. Attempt 10 names 1 of 8, request 142, cut at the output cap. The receipt test asserts that validity plus the named shortfall equals the delivered calls, and that the shortfall never exceeds the calls cut at the cap (red on base). |
| C-002: the visible count excluded tool-call output | **Fixed.** Tool-call output has its own count (name and arguments), and publish names the remainder of the decoded count (`unsplit_decoded_tokens`: template markup, plus the tool-call output in receipts before round 5). The README defines each part. A wire test checks that the parts add up to the decoded count on a tool-call response, and a receipt test checks that the remainder is never negative. |
| C-003: four planned checks unasserted | **Fixed.** Maximum supervisor lag is asserted on every outcome: over two periods exactly when the attempt stopped on lag. AC1 coverage is recorded and asserted on every long:all session, cut-short ones included; 07, 11 and 12 are not met. The Hermes timers are asserted at or above the backstop, through `session_windows` and against every published session's applied timer. The request-limit refusal's `wire_failure` receipt is asserted. |
| C-004: round-4 records misstated attempt 04; an assertion could not fail | **Fixed.** Attempt 04's cancelled request carries its first token (12.344 s) and names only its tool-call count missing; the ledger, this report and the V2 row are corrected. The live-wire test stops after the first token and asserts that the published value equals the wire's. |
| C-005: no named live replay of the post-confidence stop paths | **Deferred with rationale** to backlog **T-224**: Sprint 4's first lab attempt replays them, with the receipt checks listed there. The launch envelope is spent, and a replay needs the owner's approval. |

## Concern dispositions (critique round 6)

[critique-06](critique-06.md) returned `proceed-with-caveats` with 4 concerns. Each was addressed, and the critic was re-run:

| Concern | Response |
|---|---|
| C-001: stopped requests' decoded tokens counted as zero | **Fixed.** `decoded_tokens` is a named-missing field. The 6 requests that never completed name it (red on base). A stop receipt now carries the last `/slots` decode count as an observed lower bound, tested from the live wire. The ledger and policy label their token figures. Token figures are lower bounds. Three stopped requests (attempt 07's request 91, attempt 11's 145 and attempt 12's 156) never returned a decode count, so their receipts name it missing and the sums count them as 0. Each receipt publishes how long the request ran after its prompt was fully processed: 30.5, 89.1 and 16.7 s. At the fastest decode rate any receipt shows (3.743 tok/s), that time allows about 114 more tokens in R0 and 396 in R2, or about 586.1 and 1,215.6 tokens per verified item. This is an estimate from the receipts, not a strict bound. (Restated in round 7.) The time ranking is unaffected. |
| C-002: the split test matched the double by construction | **Fixed.** The capture backend decodes 2 tokens of template markup. The test asserts that the parts stay within the decode, and that the published remainder equals the markup. |
| C-003: receipt checks could not hold the replay to the new behavior | **Fixed.** The repaired lab writes schema-3 manifests, and only schema-2 receipts (the live runs) may name the later fields missing or leave cap-cut calls unvalidated. A cut-short session's screened history may lack only cap-cut calls. |
| C-004: small record drifts | **Fixed.** Per-request validity is published only where the wire recorded it. The AC7 row names both missing fields. T-210 and T-211 carry round-5 corrections. INT-0004 links the Sprint 3 ledger. |

## Concern dispositions (critique round 7)

[critique-07](critique-07.md) returned `proceed-with-caveats` with 4 concerns. Each was addressed, and the critic was re-run:

| Concern | Response |
|---|---|
| C-001: echo saving and peak input contradicted by the receipts | **Fixed.** The policy states the median saving (161 to 60 uncached tokens per continued request) beside the totals, which did not fall (R2 8,259 tokens in 90.3 s, R1 7,943 in 93.7 s). It corrects the peak to 9,935 tokens. The echo recommendation rests on AC3's append-only history, with no throughput claim. P1 was re-reviewed. |
| C-002: screen ranking from an unpublished re-scan | **Fixed.** Attempt 06's receipt publishes the ranking under the current scan, beside every session's live verdict. A receipt test re-ranks the published sessions and gets the recorded `screen_winners` (red on base). The tool calls themselves stay in the lab for privacy. The policy names the live scan's false positives. |
| C-003: schema-3 rules could never run | **Addressed; the rules first run in T-224.** The receipt suite reads every sprint's published attempts, so the Sprint 4 replay's schema-3 receipts meet them. T-224 names the suite as its acceptance check and adds `id_slot` and `decoded_tokens_observed` to its checklist. No schema-3 receipt exists yet. |
| C-004: the decode "bound" used the calibrated rate, from unpublished inputs | **Fixed.** Each stopped request publishes its seconds after prefill. The estimate uses the fastest decode rate any receipt shows (3.743 tok/s), is labelled an estimate, and drops the context-slowdown claim. |

## Concern dispositions (critique round 8)

[critique-08](critique-08.md) returned `proceed-with-caveats` with 3 concerns. Each was addressed, and the critic was re-run:

| Concern | Response |
|---|---|
| C-001: attempt 05's cut-short off-greedy screen session uncounted | **Disclosed; deferred with rationale** to backlog **T-225**. As locked, S2 ranks the screen that completed (attempt 06), one session per configuration. Attempt 05 was stopped by a lab defect and replayed as attempt 06. The policy, the e2e row and this report now state the exclusion and give the alternative reading: counting attempt 05 as O1 counts stops, greedy costs 375.4 s per verified item and model default (318.5 s) would rank first. The full runs used greedy, so the full-length comparison is unmeasured, and T-225 runs it. |
| C-002: INT-0004 AC1 identity unasserted on Sprint 3 manifests | **Fixed.** Every published manifest must pin the model, tokenizer, template, backend and corpus SHA-256 hashes, the 40-hex Hermes commit, the interpreter and the seed. |
| C-003: record drifts | **Fixed.** The AC2 row calls the decode figure an estimate, and the test and publish comment say "estimated". INT-0007's work evidence links the completed tasks and backlog T-223, T-224 and T-225. |

## Plan deviation: retained fixed values

The build plan retained the observation cadences and the guards counted in
them, the 2 s grace and 5 s cleanup, the wire's 1 s lock handoff and the
`git` tool timeouts. The Test phase found and kept further fixed bounds:

- the telemetry writer retry (half a sample period);
- the `nvidia-smi` query (2 s);
- the hidden verifier's process and thread bounds (60 and 120 s);
- one-time venv creation (600 s);
- the backend listener check after cleanup (0.2 s).

One planned window also changed. During the calibration attempt, the gap
between requests is k × the attempt's own load time instead of k × that
session's T_cli. The driver reports T_cli only after the session ends.

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
  is spent). They are seams, receipt-completeness changes and fixes to the
  stop paths, each covered by formal tests and listed in the ledger. Their
  live replay is backlog **T-224**, the first lab attempt of Sprint 4.

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
