# Sprint 3 Integration Test Results (after operational confidence)

- **Tested head:** `a80294f17a` (after critique round 9). These results are
  part of the final formal run recorded in [unit-tests](unit-tests.md) (318
  passed, 0 failed; runner log sha256 `e9081c78…`).
- **Runner:** `scripts/run_tests.sh` on the owner's Windows 11 host.
- **Ordering:** written and first run after the confidence record
  (2026-10-04T01:58Z).

## Lab wire

The real `Wire` runs over loopback HTTP against a capture backend shaped
like the pinned b10964. It renders, tokenizes and streams a progress chunk,
reasoning and content or tool-call deltas, and a final timings chunk with
**no `id_slot`**. Its `/slots` names the working slot, as the real server
does: a slot is processing only during a request. The Sprint 2 wire tests
were ported to the Sprint 3 Wire API (T-211 changed its constructor),
keeping their invariants. Waits are event-based: the backend signals its
first chunk, and holds its final chunk until the test has seen the wire
record the working slot (`slot_seen`). Wall-clock bounds are at least 2 s.

| Test | EARS | Result | Assertion |
|---|---|---|---|
| `test_admitted_request_is_bounded_once_and_original_is_preserved` | M1 | pass | A thinking arm forwards its cap, `enable_thinking`, `reasoning_budget_tokens`, the full greedy sampler set and seed, with `stream` and `return_progress` on and `reasoning_effort` dropped. It does so exactly once, and the original body is kept. |
| `test_oversized_or_misrouted_request_never_reaches_generation` (3) | M1 | pass | Over the ceiling (through messages or tools), or a wrong model, the request is refused before generation. No request is consumed. |
| `test_exhausted_request_budget_refuses_before_generation` | T2 | pass | The aggregate budget refuses before generation. |
| `test_session_request_limit` | per-session limit | pass | A request past the session limit is refused, and the refusal is a `wire_failure` receipt (round 5). |
| `test_wire_streams_and_reassembles` | T4 | pass | Progress chunks never reach the client. A non-streaming client gets one reassembled response with reasoning, content and finish reason. Both went upstream streaming. |
| `test_streamed_tool_call_is_reassembled_and_counted` | M3, T4, L1 | pass | **Regression (round 5).** A streamed tool call is reassembled with its name and parsed arguments, counted, and recorded valid and known. Its output is counted as tool-call tokens. The capture backend decodes 2 tokens of template markup around its output, as a real template does: reasoning, visible and tool-call tokens stay within the decoded count, and the published remainder equals the markup (round 6). |
| `test_a_tool_call_cut_at_the_output_cap_is_recorded_invalid` | M3 | pass | **Regression (round 5, attempt 10).** A tool call delivered with `finish_reason: length` and cut arguments is recorded invalid on the response and in the session's validity. |
| `test_length_finish_marks_the_next_request_a_continuation` | M3 | pass | After a `length` finish, the next request is recorded as a truncation continuation. |
| `test_slot_counters_are_progress_while_deltas_are_withheld` | T4 | pass | While SSE deltas are withheld for seconds, rising `/slots` counters register as progress. |
| `test_receipt_fields_complete_or_named_missing` | M3, L1 | pass | The final chunk is released only after the wire has recorded `slot_seen`. The prediction is recorded at send. The response receipt carries timings, finish reason, the reasoning/visible/tool-call split (no tool call: 0 tool-call tokens and an empty validity list), first token and both predictions. The slot comes from `/slots` (`id_slot_source: "slots"`), because the stream carries none. `kernel_compiled` is present even when no cache is wired. |
| `test_cancel_returns_promptly_and_is_recorded_as_a_cancel` | C4, INT-0004 AC2 | pass | **Regression (attempt 02).** The cancel returns in under 2 s against a 6 s batch. It is recorded as `response_cancelled`, not as a wire failure, and keeps its elapsed time and prediction (AC7). |
| `test_sequential_request_after_done_is_accepted_and_concurrent_is_refused` | M1 | pass | **Regressions (attempt 10 and T-214).** A retry sent at `[DONE]` during the previous request's accounting is accepted. A request arriving mid-stream is refused as concurrent, including after a finishing handler's cleanup. **Round 9:** the refusal is a `wire_failure` receipt naming the session and whether it follows a `length` finish. |
| `test_a_failing_request_keeps_its_timing_and_predictions` | AC7, M3 | pass | **Regression (round 1).** A malformed stream fails the request, and its `wire_failure` keeps the elapsed time and both predictions. |
| `test_an_attempt_stop_receipts_the_live_in_flight_request` | AC7, L4 | pass | **Regression (round 3).** `run.stopped_request` on the live `Wire.active` mid-stream gives the request id, the cause, an elapsed time within the observed window and both predictions. The wire session keeps the conversation it forwarded. |
| `test_a_stall_stop_is_published_with_its_cause_and_a_cancel_is_not` | AC7, H2, M3 | pass | **Regression (round 4).** From the live wire's own receipts: a request stopped mid-stream through `run.stop_active_request` is published as `stopped` with the stall cause and its prediction. The stop comes after the first token, and the published first token equals the wire's (round 5). Its decode count never arrived, so `decoded_tokens` is named missing, with the `/slots` count the wire last saw as a lower bound (round 6). A deliberate cancel stays `response_cancelled`, with no cause. |
| `test_a_stop_during_verification_still_screens_the_ended_session` | L4, L2 | pass | **Regression (round 4).** After the wire has ended the session, the stop path still finds it by id. It screens the forwarded history plus the delivered response, flags `../../secret`, and records the request count. Validity covers the call the wire delivered (round 5), and AC1 coverage is recorded. |
| `test_the_screened_conversation_includes_tool_calls_already_delivered` | L4 | pass | **Regression (round 3).** After a delivered tool-call response, the screened conversation is the forwarded history plus that response's tool calls, which Hermes may run before another request. |

**Found by these tests:** a race in the attempt-10 repair. A finishing
handler's `finally` cleared the in-flight flag the next request had
already claimed. The flag now holds the owning handler's token, and only
that owner releases it (`0cd28ab8cc`).

## Published receipts and manifests

Since round 7 these tests read every sprint's published `attempt-*.json`, so
the repaired lab's first schema-3 receipts (backlog T-224) meet the stricter
rules. Test IDs carry the sprint, for example `s3-attempt-06-screen`.

| Test | EARS | Result | Assertion |
|---|---|---|---|
| `test_every_attempt_is_published` | V3 | pass | Attempt indices 1–13, taken from the final budget counter, each have a published receipt. |
| `test_published_evidence_excludes_private_paths_and_credentials` (25) | V3 | pass | No user path, `Bearer` value or 48-hex token appears in any published receipt or manifest. |
| `test_every_published_attempt_resolves_to_its_manifest` (13) | V3, M4, INT-0004 AC1 | pass | Each receipt resolves to its manifest by id. **Round 8:** the manifest pins INT-0004 AC1's identity: SHA-256 hashes of the model, tokenizer, template, backend build and task corpus, plus the 40-hex Hermes commit. **Round 9:** every backend library hash, a clean source tree, an integer seed and the interpreter. The public copy's digest is valid. The owner's time-model decision, Hermes timeouts (including the terminal timeout), the allowlist and the time parameters are present. The rendered prefix is measured, or not-measured with a reason. Post-calibration plans carry the full calibration record (rates, checkpoint size, frozen count, budget). Every session has an arm, a stop cause is kept, and cleanup took at most 5 s with the listener closed. |
| `test_launched_attempts_record_the_launch_and_admission` (13) | M1, M4 | pass | Every launched attempt's command has `--slot-save-path` and no `--predict`, and records its admission host condition. |
| `test_sessions_record_their_first_rendered_prefix` (13) | M4 | pass | Each session records its first rendered prefix (tokens and hash). |
| `test_every_request_names_its_missing_fields` (13) | L1, M3 | pass | **Regression (round 4).** Every request, completed, cancelled or stopped, carries each of the 18 L1/M3 request fields or names it missing. Meaningful first token and the tool-call count (round 4) and decoded tokens (round 6) were silently absent before. Tool-call tokens are named missing in every receipt before round 5. |
| `test_stopped_requests_keep_their_own_cause_and_elapsed_time` (13) | AC7 | pass | **Regression (round 3).** Each stopped request's cause equals its own session's recorded stop, or the attempt's reason when its session was still running, and it keeps its elapsed time. |
| `test_completed_calibrated_requests_carry_every_l1_and_m3_field` (13) | AC7, L1, M3 | pass | Every request completed after calibration carries every L1 and M3 request field, present and not merely named. The exceptions are fields the live runs' wire could not record, which must be named missing: `id_slot`, which b10964's stream does not return and the `/slots` correlation postdates, and tool-call tokens (round 5). Only receipts from schema-2 manifests (the live runs) may use the exceptions; the repaired lab writes schema 3 (round 6). |
| `test_machine_time_is_recomputable_from_the_receipt` (13) | O1 | pass | Each session's published machine time equals the span of its requests' published start and end times. |
| `test_attempt_stopped_long_sessions_are_scored` (13) | L2, L4 | pass | A long session cut short by an attempt stop has a score and an L4 screen that flagged nothing: attempts 05, 07, 11 and 12. **Round 4:** the screen must have seen the session (messages and tool calls non-zero for a session with requests). **Round 6:** validity covers every screened call, and the screened history may lack only calls cut at the output cap. A session screened at publish ends in a stopped request, so its last forwarded conversation holds every tool call Hermes ran. |
| `test_long_sessions_validate_every_delivered_tool_call` (13) | M3 | pass | **Regression (round 5).** Every long session, finished or cut short, has a validity entry for each delivered tool call, or names the shortfall, which can only be calls cut at the output cap. Attempt 10 names 1 of 8 (request 142). A schema-3 receipt may leave none unvalidated (round 6). |
| `test_the_token_split_accounts_for_decoded_output` (13) | L1 | pass | **Round 5.** Reasoning, visible and tool-call tokens never exceed the decoded count, and the published remainder makes up the difference. |
| `test_supervisor_lag_is_recorded_and_stops_only_past_two_periods` (13) | M3 | pass | **Round 5.** Every outcome records its maximum supervisor lag. It exceeds two telemetry periods exactly when the attempt stopped on lag (attempt 02, 14.9 s); the others peaked at 0.63 s. |
| `test_long_all_sessions_record_ac1_coverage` (13) | L2 | pass | **Regression (round 5).** Every long:all session, completed or stopped, records AC1 coverage, true exactly at 20 requests or more. |
| `test_published_screen_reproduces_the_recorded_winners` (13) | S2, L4 | pass | **Regression (round 7).** A screen attempt's receipt publishes each session's verdict under the current scan beside the live one. Re-ranking the published sessions under L4's pick gives the published ranking and the recorded `screen_winners`, and each session's score and live verdict match the receipt's session record. **Round 9:** the ranking inputs are tied to the receipt: exactly the ended long sessions, their arms and re-run links, their published machine time and their decoded tokens. |
| `test_a_stopped_requests_unreturned_decode_can_be_estimated_from_the_receipt` (13) | O1 | pass | **Round 7.** Where a stopped request publishes its seconds after prefill, it names `decoded_tokens` missing, and the time lies within its elapsed time; the missing decode is estimated from it. |
| `test_hermes_timers_hold_at_or_above_each_sessions_backstop` (13) | M2 | pass | **Round 5.** After calibration, every session's applied Hermes timer, and the manifest's declared timers, are at or above the request backstop recomputed from the calibration record, the time parameters and that session's output cap. |

## Windows file behaviour (`windows_only`)

| Test | Result | Assertion |
|---|---|---|
| `test_refused_telemetry_read_keeps_the_last_sample` | pass | **Regression (attempt 05).** While another handle denies sharing, the read keeps the last sample. |
| `test_telemetry_publish_survives_a_held_destination` | pass | **Regression (attempt 07).** With an injected bound, the writer retries until the reader closes. If the reader holds on, the sample is skipped without raising. |
| `test_lab_writers_emit_lf` | pass | Receipts and manifests are written with LF, so the published bytes and digests are host-independent. |

## Affected-suite regression check

The same file set ran with the same settings on base `5f6a0c7b60` (the
Sprint 2 checkpoint merge) and on head: `tests/hermes_cli/test_local_*.py`,
`tests/evals/`, and the four junk-fix files.

| Tree | Files | Passed | Failed | Skipped | Runner log sha256 |
|---|---|---|---|---|---|
| Base `5f6a0c7b60` | 30 | 345 | 7 | 2 | — |
| Head `1fca1a3095` | 34 | 548 | 1 | 2 | `f8b8b33e…` |
| Head `4f323770ee` | 34 | 554 | 1 | 2 | `c883ad77…` |
| Head `663bac6a2a` | 34 | 569 | 1 | 2 | `7848fb9f…` |
| Head `9c373121cd` | 34 | 622 | 1 | 2 | `99a776a6…` |
| Head `a730a0a39e` | 34 | 622 | 1 | 2 | `d10f32f0…` |
| Head `47522c6a2d` | 34 | 649 | 1 | 2 | `20559fd5…` |
| Head `32b8e50eaf` | 34 | 649 | 1 | 2 | `7722d7f4…` |
| Head `a80294f17a` | 34 | 649 | 1 | 2 | `28c8adad…` |

- **New failures on head:** none.
- **Fixed on head (6):** the shell-hook, hooks-CLI, cron catch-up and
  gitspawn baseline tests (fix `4532740520`). The Windows paths they put in
  bash bodies were mangled.
- **Inherited (1):** `test_local_runtime_child_env.py::test_spawn_server_keeps_the_callers_environment`
  fails identically on base. Neither it nor `processes.py` changed.
